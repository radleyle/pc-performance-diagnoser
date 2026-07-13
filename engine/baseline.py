"""Learn typical CPU/RAM patterns and compare current values."""

from __future__ import annotations

import statistics
import time

from collector.db import get_metrics_since, upsert_baseline
from engine.config import get_config


def update_baselines(days: int = 7) -> int:
    """Recompute hourly baselines from recent metrics."""
    minutes = days * 24 * 60
    rows = get_metrics_since(minutes=minutes)
    if len(rows) < 20:
        return 0

    buckets: dict[tuple[str, int], list[float]] = {}
    for row in rows:
        hour = time.localtime(row["timestamp"] / 1000).tm_hour
        for metric_name, value in (
            ("cpu_percent", float(row["cpu_percent"])),
            ("ram_used_percent", float(row["ram_used_percent"])),
        ):
            buckets.setdefault((metric_name, hour), []).append(value)

    updated = 0
    now_ms = int(time.time() * 1000)
    for (metric_name, hour), values in buckets.items():
        if len(values) < 5:
            continue
        upsert_baseline(
            metric_name=metric_name,
            hour_of_day=hour,
            p50=statistics.median(values),
            p95=sorted(values)[int(len(values) * 0.95) - 1],
            sample_count=len(values),
            updated_at=now_ms,
        )
        updated += 1
    return updated


def compare_to_baseline() -> list[dict]:
    """Flag metrics that exceed learned p95 for the current hour."""
    from collector.db import get_baselines_for_hour

    rows = get_metrics_since(minutes=30)
    if not rows:
        return []

    latest = rows[-1]
    hour = time.localtime(latest["timestamp"] / 1000).tm_hour
    baselines = {row["metric_name"]: row for row in get_baselines_for_hour(hour)}
    deviation_pct = get_config().thresholds.baseline_deviation_percent

    comparisons = []
    for metric_name, label in (
        ("cpu_percent", "CPU"),
        ("ram_used_percent", "RAM used"),
    ):
        baseline = baselines.get(metric_name)
        if not baseline:
            continue
        current = float(latest[metric_name])
        p95 = float(baseline["p95"])
        delta = current - p95
        abnormal = current > p95 * (1 + deviation_pct / 100)
        comparisons.append(
            {
                "metric": label,
                "current": round(current, 1),
                "baseline_p95": round(p95, 1),
                "delta": round(delta, 1),
                "abnormal": abnormal,
            }
        )
    return comparisons
