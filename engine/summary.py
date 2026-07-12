"""Build now-vs-then comparison summaries for the dashboard and report export."""

from __future__ import annotations

from collector.db import (
    get_latest_process_snapshots,
    get_metric_near,
    get_metrics_since,
    get_process_snapshots_near,
)
from collector.process_groups import group_process_rows


def _metric_snapshot(row) -> dict | None:
    if row is None:
        return None
    return {
        "timestamp": row["timestamp"],
        "cpu_percent": float(row["cpu_percent"]),
        "ram_available_mb": float(row["ram_available_mb"]),
        "ram_used_percent": float(row["ram_used_percent"]),
        "disk_free_gb": row["disk_free_gb"],
        "disk_used_percent": row["disk_used_percent"],
    }


def _top_process(rows) -> dict | None:
    if not rows:
        return None
    grouped = group_process_rows(rows)
    if not grouped:
        return None
    top = grouped[0]
    return {
        "app_name": top["app_name"],
        "memory_mb": top["memory_mb"],
        "cpu_percent": top["cpu_percent"],
    }


def _delta(current: float | None, past: float | None) -> float | None:
    if current is None or past is None:
        return None
    return round(current - past, 2)


def build_comparison(minutes_ago: int = 60) -> dict:
    """Compare the latest snapshot to the closest one from ~N minutes ago."""
    recent = get_metrics_since(minutes=5)
    current_metric_row = recent[-1] if recent else None
    past_metric_row = get_metric_near(minutes_ago=minutes_ago)

    current_metric = _metric_snapshot(current_metric_row)
    past_metric = _metric_snapshot(past_metric_row)

    current_processes = get_latest_process_snapshots()
    past_processes = get_process_snapshots_near(minutes_ago=minutes_ago)
    current_top = _top_process(current_processes)
    past_top = _top_process(past_processes)

    delta = None
    if current_metric and past_metric:
        delta = {
            "cpu_percent": _delta(
                current_metric["cpu_percent"], past_metric["cpu_percent"]
            ),
            "ram_available_mb": _delta(
                current_metric["ram_available_mb"],
                past_metric["ram_available_mb"],
            ),
            "ram_used_percent": _delta(
                current_metric["ram_used_percent"],
                past_metric["ram_used_percent"],
            ),
            "disk_free_gb": _delta(
                current_metric["disk_free_gb"], past_metric["disk_free_gb"]
            ),
            "disk_used_percent": _delta(
                current_metric["disk_used_percent"],
                past_metric["disk_used_percent"],
            ),
        }

    return {
        "minutes_ago": minutes_ago,
        "current": current_metric,
        "past": past_metric,
        "delta": delta,
        "current_top_process": current_top,
        "past_top_process": past_top,
    }
