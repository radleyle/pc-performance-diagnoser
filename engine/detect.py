"""
Rule-based detection engine.

Reads recent data from SQLite and returns structured issues.
No LLM here — just thresholds and simple pattern checks.
"""

import time

from collector.db import get_latest_process_snapshots, get_metrics_since, get_process_history
from collector.network import check_network_status
from engine.baseline import compare_to_baseline
from engine.config import get_config
from engine.schemas import DiagnosisResult, Issue, ProcessSummary, Status


def _thresholds():
    return get_config().thresholds


def _check_ram_critical(ram_available_mb: float, ram_used_percent: float) -> Issue | None:
    if ram_available_mb < _thresholds().ram_critical_mb:
        return Issue(
            type="ram_critical",
            severity="high",
            message=f"Only {ram_available_mb:.0f} MB RAM available",
            evidence={
                "ram_available_mb": ram_available_mb,
                "ram_used_percent": ram_used_percent,
            },
        )
    return None


def _check_ram_warning(ram_available_mb: float, ram_used_percent: float) -> Issue | None:
    thresholds = _thresholds()
    if (
        ram_available_mb < thresholds.ram_warning_mb
        or ram_used_percent > thresholds.ram_used_warning_percent
    ):
        return Issue(
            type="ram_warning",
            severity="medium",
            message=(
                f"Low memory: {ram_available_mb:.0f} MB available, "
                f"{ram_used_percent:.1f}% used"
            ),
            evidence={
                "ram_available_mb": ram_available_mb,
                "ram_used_percent": ram_used_percent,
            },
        )
    return None


def _check_disk_critical(disk_free_gb: float, disk_used_percent: float) -> Issue | None:
    if disk_free_gb < _thresholds().disk_critical_free_gb:
        return Issue(
            type="disk_critical",
            severity="high",
            message=f"Only {disk_free_gb:.1f} GB disk space free",
            evidence={
                "disk_free_gb": disk_free_gb,
                "disk_used_percent": disk_used_percent,
            },
        )
    return None


def _check_disk_warning(disk_free_gb: float, disk_used_percent: float) -> Issue | None:
    thresholds = _thresholds()
    if (
        disk_free_gb < thresholds.disk_warning_free_gb
        or disk_used_percent > thresholds.disk_warning_used_percent
    ):
        return Issue(
            type="disk_warning",
            severity="medium",
            message=(
                f"Low disk space: {disk_free_gb:.1f} GB free, "
                f"{disk_used_percent:.1f}% used"
            ),
            evidence={
                "disk_free_gb": disk_free_gb,
                "disk_used_percent": disk_used_percent,
            },
        )
    return None


def _check_process_hogs(process_rows) -> list[Issue]:
    issues: list[Issue] = []
    hog_mb = _thresholds().process_hog_mb

    for row in process_rows:
        memory_mb = float(row["memory_mb"])
        if memory_mb > hog_mb:
            name = row["process_name"]
            issues.append(
                Issue(
                    type="process_memory_hog",
                    severity="medium",
                    message=f"{name} using {memory_mb:.0f} MB",
                    evidence={
                        "process_name": name,
                        "memory_mb": memory_mb,
                    },
                )
            )

    return issues


def _check_memory_overflow(metrics_rows) -> Issue | None:
    """
    Flag if available RAM dropped by more than the configured fraction
    within the configured window.
    """
    if len(metrics_rows) < 2:
        return None

    thresholds = _thresholds()
    now_ms = int(time.time() * 1000)
    window_start_ms = now_ms - (thresholds.overflow_window_seconds * 1000)

    in_window = [r for r in metrics_rows if r["timestamp"] >= window_start_ms]
    if len(in_window) < 2:
        return None

    oldest = in_window[0]
    newest = in_window[-1]

    start_mb = float(oldest["ram_available_mb"])
    end_mb = float(newest["ram_available_mb"])

    if start_mb <= 0:
        return None

    drop_fraction = (start_mb - end_mb) / start_mb

    if drop_fraction > thresholds.overflow_drop_fraction:
        return Issue(
            type="memory_overflow",
            severity="high",
            message=(
                f"Available RAM dropped {drop_fraction * 100:.0f}% in "
                f"{thresholds.overflow_window_seconds}s "
                f"({start_mb:.0f} MB → {end_mb:.0f} MB)"
            ),
            evidence={
                "start_ram_available_mb": start_mb,
                "end_ram_available_mb": end_mb,
                "drop_fraction": round(drop_fraction, 3),
                "window_seconds": thresholds.overflow_window_seconds,
            },
        )

    return None


def _check_high_cpu(metrics_rows) -> Issue | None:
    """Flag if the last N samples all exceed the CPU threshold."""
    thresholds = _thresholds()
    sample_count = thresholds.cpu_high_consecutive_samples

    if len(metrics_rows) < sample_count:
        return None

    recent = metrics_rows[-sample_count:]
    cpu_values = [float(r["cpu_percent"]) for r in recent]

    if all(cpu > thresholds.cpu_high_percent for cpu in cpu_values):
        return Issue(
            type="high_cpu",
            severity="medium",
            message=(
                f"CPU above {thresholds.cpu_high_percent}% for "
                f"{sample_count} consecutive samples"
            ),
            evidence={
                "cpu_samples": cpu_values,
                "threshold_percent": thresholds.cpu_high_percent,
            },
        )

    return None


def _check_memory_leaks(minutes: int) -> list[Issue]:
    """Flag processes whose memory grew significantly over the window."""
    rows = get_process_history(minutes=minutes)
    if not rows:
        return []

    thresholds = _thresholds()
    growth_mb = thresholds.memory_leak_growth_mb
    by_process: dict[str, list[float]] = {}

    for row in rows:
        by_process.setdefault(row["process_name"], []).append(float(row["memory_mb"]))

    issues: list[Issue] = []
    for process_name, samples in by_process.items():
        if len(samples) < 3:
            continue
        delta = samples[-1] - samples[0]
        if delta >= growth_mb and samples[-1] > thresholds.process_hog_mb / 2:
            issues.append(
                Issue(
                    type="memory_leak",
                    severity="medium",
                    message=(
                        f"{process_name} grew {delta:.0f} MB in "
                        f"{thresholds.memory_leak_window_minutes} minutes"
                    ),
                    evidence={
                        "process_name": process_name,
                        "start_mb": round(samples[0], 1),
                        "end_mb": round(samples[-1], 1),
                        "growth_mb": round(delta, 1),
                    },
                )
            )
    return issues


def _check_baseline_anomalies() -> list[Issue]:
    issues: list[Issue] = []
    for row in compare_to_baseline():
        if row["abnormal"]:
            issues.append(
                Issue(
                    type="baseline_anomaly",
                    severity="medium",
                    message=(
                        f"{row['metric']} is {row['current']} — above your usual "
                        f"{row['baseline_p95']} (p95)"
                    ),
                    evidence=row,
                )
            )
    return issues


def _check_network_degraded() -> Issue | None:
    network = check_network_status()
    latency = network.get("ping_latency_ms") or network.get("dns_latency_ms")
    threshold = _thresholds().network_latency_warning_ms
    if latency is not None and latency > threshold:
        return Issue(
            type="network_latency",
            severity="medium",
            message=f"Network latency is high ({latency:.0f} ms)",
            evidence=network,
        )
    return None


def _check_power_state() -> Issue | None:
    try:
        import psutil

        battery = psutil.sensors_battery()
        if battery is None:
            return None
        if not battery.power_plugged and battery.percent < 20:
            return Issue(
                type="low_battery",
                severity="medium",
                message=f"Battery at {battery.percent:.0f}% while unplugged",
                evidence={"percent": battery.percent, "power_plugged": battery.power_plugged},
            )
    except Exception:
        return None
    return None


def _compute_status(issues: list[Issue]) -> Status:
    if any(issue.severity == "high" for issue in issues):
        return "critical"
    if issues:
        return "warning"
    return "ok"


def run_diagnosis(minutes: int = 60) -> DiagnosisResult:
    """
    Run all detection rules against recent SQLite data.

    Returns a DiagnosisResult ready for JSON / API / LLM.
    """
    metrics_rows = get_metrics_since(minutes=minutes)
    process_rows = get_latest_process_snapshots()

    issues: list[Issue] = []

    if metrics_rows:
        latest = metrics_rows[-1]
        ram_available_mb = float(latest["ram_available_mb"])
        ram_used_percent = float(latest["ram_used_percent"])
        disk_free_gb = latest["disk_free_gb"]
        disk_used_percent = latest["disk_used_percent"]

        for check in (
            _check_ram_critical(ram_available_mb, ram_used_percent),
            _check_ram_warning(ram_available_mb, ram_used_percent),
            _check_memory_overflow(metrics_rows),
            _check_high_cpu(metrics_rows),
            _check_disk_critical(disk_free_gb, disk_used_percent)
            if disk_free_gb is not None
            else None,
            _check_disk_warning(disk_free_gb, disk_used_percent)
            if disk_free_gb is not None
            else None,
        ):
            if check is not None:
                issues.append(check)

    issues.extend(_check_process_hogs(process_rows))
    issues.extend(_check_memory_leaks(_thresholds().memory_leak_window_minutes))
    issues.extend(_check_baseline_anomalies())

    for check in (_check_network_degraded(), _check_power_state()):
        if check is not None:
            issues.append(check)

    top_processes = [
        ProcessSummary(name=row["process_name"], memory_mb=float(row["memory_mb"]))
        for row in process_rows[:10]
    ]

    return DiagnosisResult(
        status=_compute_status(issues),
        issues=issues,
        top_processes=top_processes,
    )
