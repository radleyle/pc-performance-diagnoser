"""Why-is-it-slow-now report builder."""

from __future__ import annotations

import time

from collector.db import get_latest_process_snapshots, get_metrics_since, get_process_snapshots_near
from collector.network import check_network_status
from collector.process_groups import group_process_rows
from collector.startup_items import list_startup_items
from engine.detect import run_diagnosis


def build_slow_now_report(minutes: int = 5) -> dict:
    """Bundle short-window signals into one actionable report."""
    diagnosis = run_diagnosis(minutes=minutes).model_dump()
    metrics = get_metrics_since(minutes=minutes)
    current_rows = get_latest_process_snapshots()
    past_rows = get_process_snapshots_near(minutes_ago=minutes)

    current_grouped = group_process_rows(current_rows)
    past_grouped = group_process_rows(past_rows)
    past_by_name = {row["app_name"]: row for row in past_grouped}

    movers = []
    for row in current_grouped[:8]:
        past = past_by_name.get(row["app_name"])
        delta_mb = row["memory_mb"] - (past["memory_mb"] if past else 0)
        movers.append(
            {
                "app_name": row["app_name"],
                "memory_mb": round(row["memory_mb"], 1),
                "cpu_percent": round(row["cpu_percent"], 1),
                "memory_delta_mb": round(delta_mb, 1),
            }
        )
    movers.sort(key=lambda row: abs(row["memory_delta_mb"]), reverse=True)

    cpu_now = float(metrics[-1]["cpu_percent"]) if metrics else 0.0
    ram_now = float(metrics[-1]["ram_used_percent"]) if metrics else 0.0
    cpu_start = float(metrics[0]["cpu_percent"]) if metrics else cpu_now

    network = check_network_status()
    startup_count = len(list_startup_items())

    likely_causes = []
    if diagnosis["status"] != "ok":
        likely_causes.append("Rule-based checks flagged performance issues")
    if cpu_now > 70 or (cpu_now - cpu_start) > 20:
        likely_causes.append("CPU spike in the last few minutes")
    if ram_now > 85:
        likely_causes.append("Memory pressure is high right now")
    if network["status"] != "ok":
        likely_causes.append(network["message"])
    if startup_count > 8:
        likely_causes.append(f"{startup_count} login items may slow startup")
    if not likely_causes:
        likely_causes.append("No major slowdown pattern detected in the last window")

    return {
        "generated_at": int(time.time() * 1000),
        "window_minutes": minutes,
        "status": diagnosis["status"],
        "headline": _headline(diagnosis["status"]),
        "likely_causes": likely_causes,
        "metrics": {
            "cpu_percent": round(cpu_now, 1),
            "cpu_delta": round(cpu_now - cpu_start, 1),
            "ram_used_percent": round(ram_now, 1),
        },
        "top_movers": movers[:5],
        "issues": diagnosis["issues"],
        "startup_item_count": startup_count,
        "network": network,
    }


def _headline(status: str) -> str:
    if status == "critical":
        return "Your Mac looks stressed right now"
    if status == "warning":
        return "Some slowdown patterns detected"
    return "No major slowdown detected in the last few minutes"
