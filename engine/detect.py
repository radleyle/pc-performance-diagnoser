"""
Rule-based detection engine.

Reads recent data from SQLite and returns structured issues.
No LLM here — just thresholds and simple pattern checks.
"""

import time

from collector.db import get_latest_process_snapshots, get_metrics_since
from engine.schemas import DiagnosisResult, Issue, ProcessSummary, Status


# --- Thresholds ---

RAM_CRITICAL_MB = 500
RAM_WARNING_MB = 1024
RAM_USED_WARNING_PERCENT = 90.0
PROCESS_HOG_MB = 1024
CPU_HIGH_PERCENT = 90.0
CPU_HIGH_CONSECUTIVE_SAMPLES = 3
OVERFLOW_WINDOW_SECONDS = 60
OVERFLOW_DROP_FRACTION = 0.50
DISK_CRITICAL_FREE_GB = 2.0
DISK_WARNING_FREE_GB = 10.0
DISK_WARNING_USED_PERCENT = 90.0


def _check_ram_critical(ram_available_mb: float, ram_used_percent: float) -> Issue | None:
    if ram_available_mb < RAM_CRITICAL_MB:
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
    if ram_available_mb < RAM_WARNING_MB or ram_used_percent > RAM_USED_WARNING_PERCENT:
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
    if disk_free_gb < DISK_CRITICAL_FREE_GB:
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
    if (
        disk_free_gb < DISK_WARNING_FREE_GB
        or disk_used_percent > DISK_WARNING_USED_PERCENT
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

    for row in process_rows:
        memory_mb = float(row["memory_mb"])
        if memory_mb > PROCESS_HOG_MB:
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
    Flag if available RAM dropped by more than 50% within ~60 seconds.

    We compare the oldest and newest samples in a 60s window.
    """
    if len(metrics_rows) < 2:
        return None

    now_ms = int(time.time() * 1000)
    window_start_ms = now_ms - (OVERFLOW_WINDOW_SECONDS * 1000)

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

    if drop_fraction > OVERFLOW_DROP_FRACTION:
        return Issue(
            type="memory_overflow",
            severity="high",
            message=(
                f"Available RAM dropped {drop_fraction * 100:.0f}% in "
                f"{OVERFLOW_WINDOW_SECONDS}s ({start_mb:.0f} MB → {end_mb:.0f} MB)"
            ),
            evidence={
                "start_ram_available_mb": start_mb,
                "end_ram_available_mb": end_mb,
                "drop_fraction": round(drop_fraction, 3),
                "window_seconds": OVERFLOW_WINDOW_SECONDS,
            },
        )

    return None


def _check_high_cpu(metrics_rows) -> Issue | None:
    """Flag if the last 3 samples all have CPU > 90%."""
    if len(metrics_rows) < CPU_HIGH_CONSECUTIVE_SAMPLES:
        return None

    recent = metrics_rows[-CPU_HIGH_CONSECUTIVE_SAMPLES:]
    cpu_values = [float(r["cpu_percent"]) for r in recent]

    if all(cpu > CPU_HIGH_PERCENT for cpu in cpu_values):
        return Issue(
            type="high_cpu",
            severity="medium",
            message=f"CPU above {CPU_HIGH_PERCENT}% for {CPU_HIGH_CONSECUTIVE_SAMPLES} consecutive samples",
            evidence={
                "cpu_samples": cpu_values,
                "threshold_percent": CPU_HIGH_PERCENT,
            },
        )

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

    top_processes = [
        ProcessSummary(name=row["process_name"], memory_mb=float(row["memory_mb"]))
        for row in process_rows[:10]
    ]

    return DiagnosisResult(
        status=_compute_status(issues),
        issues=issues,
        top_processes=top_processes,
    )