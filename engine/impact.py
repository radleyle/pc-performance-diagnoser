"""Per-app impact scoring over a time window."""

from __future__ import annotations

from collections import defaultdict

from collector.db import get_process_history
from collector.process_groups import normalize_app_name


def compute_app_impact_scores(minutes: int = 60, limit: int = 15) -> list[dict]:
    """Score apps by memory footprint, CPU, and persistence."""
    rows = get_process_history(minutes=minutes)
    if not rows:
        return []

    by_app: dict[str, dict] = defaultdict(
        lambda: {
            "memory_samples": [],
            "cpu_samples": [],
            "snapshots": 0,
        }
    )

    for row in rows:
        app_name = normalize_app_name(row["process_name"])
        bucket = by_app[app_name]
        bucket["memory_samples"].append(float(row["memory_mb"]))
        bucket["cpu_samples"].append(float(row["cpu_percent"] or 0))
        bucket["snapshots"] += 1

    results = []
    for app_name, bucket in by_app.items():
        avg_memory = sum(bucket["memory_samples"]) / len(bucket["memory_samples"])
        avg_cpu = sum(bucket["cpu_samples"]) / len(bucket["cpu_samples"])
        peak_memory = max(bucket["memory_samples"])
        score = round((avg_memory * 0.7) + (avg_cpu * 10) + (bucket["snapshots"] * 0.5), 1)

        results.append(
            {
                "app_name": app_name,
                "impact_score": score,
                "avg_memory_mb": round(avg_memory, 1),
                "peak_memory_mb": round(peak_memory, 1),
                "avg_cpu_percent": round(avg_cpu, 1),
                "snapshot_count": bucket["snapshots"],
            }
        )

    results.sort(key=lambda row: row["impact_score"], reverse=True)
    return results[:limit]
