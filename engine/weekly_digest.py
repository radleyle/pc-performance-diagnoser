"""Weekly digest summary."""

from __future__ import annotations

import json
import time

from collector.db import get_metrics_since, get_recent_diagnoses
from engine.impact import compute_app_impact_scores


def build_weekly_digest() -> dict:
    """Summarize the last 7 days of activity."""
    minutes = 7 * 24 * 60
    metrics = get_metrics_since(minutes=minutes)
    diagnoses = get_recent_diagnoses(limit=50)

    warning_count = 0
    critical_count = 0
    for row in diagnoses:
        ts = int(row["timestamp"])
        if ts < int(time.time() * 1000) - minutes * 60 * 1000:
            continue
        try:
            parsed = json.loads(row["issues"])
            status = parsed.get("status", "ok")
        except json.JSONDecodeError:
            status = "unknown"
        if status == "warning":
            warning_count += 1
        elif status == "critical":
            critical_count += 1

    cpu_values = [float(row["cpu_percent"]) for row in metrics]
    ram_values = [float(row["ram_used_percent"]) for row in metrics]
    disk_values = [
        float(row["disk_free_gb"])
        for row in metrics
        if row["disk_free_gb"] is not None
    ]

    top_apps = compute_app_impact_scores(minutes=minutes, limit=5)

    return {
        "generated_at": int(time.time() * 1000),
        "days": 7,
        "diagnosis_counts": {
            "warning": warning_count,
            "critical": critical_count,
        },
        "averages": {
            "cpu_percent": round(sum(cpu_values) / len(cpu_values), 1) if cpu_values else None,
            "ram_used_percent": round(sum(ram_values) / len(ram_values), 1) if ram_values else None,
        },
        "disk_free_gb": {
            "start": round(disk_values[0], 1) if disk_values else None,
            "end": round(disk_values[-1], 1) if disk_values else None,
        },
        "top_apps": top_apps,
        "smart_scans": warning_count + critical_count,
    }
