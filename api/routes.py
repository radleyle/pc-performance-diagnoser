"""HTTP route handlers for the PC Performance Diagnoser API."""

import json
import time

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from api.system_status import check_collector, check_ollama
from collector.cleanup import get_cleanup_preview, run_cleanup
from collector.db import (
    get_latest_process_snapshots,
    get_metrics_since,
    get_recent_diagnoses,
    insert_diagnosis,
)
from collector.process_groups import group_process_rows
from collector.disk_scan import find_large_files, scan_home_folders
from collector.process_control import kill_process, list_live_processes
from collector.startup_items import list_startup_items
from engine.detect import run_diagnosis
from engine.llm import OllamaError, explain_diagnosis
from engine.summary import build_comparison

router = APIRouter()


class CleanupRequest(BaseModel):
    action_ids: list[str]


@router.get("/health")
def health():
    collector = check_collector()
    ollama = check_ollama()

    return {
        "api": "ok",
        "collector": collector,
        "ollama": ollama,
    }


@router.get("/metrics")
def get_metrics(minutes: int = Query(default=60, ge=1, le=10080)):
    rows = get_metrics_since(minutes=minutes)
    return {
        "minutes": minutes,
        "count": len(rows),
        "data": [
            {
                "timestamp": row["timestamp"],
                "cpu_percent": row["cpu_percent"],
                "ram_available_mb": row["ram_available_mb"],
                "ram_used_percent": row["ram_used_percent"],
                "disk_free_gb": row["disk_free_gb"],
                "disk_used_percent": row["disk_used_percent"],
            }
            for row in rows
        ],
    }


@router.get("/processes")
def get_processes(grouped: bool = Query(default=True)):
    """
    Return top processes from the latest snapshot.

    ?grouped=true (default) combines helpers under parent app names.
    ?grouped=false returns raw per-process rows.
    """
    rows = get_latest_process_snapshots()

    if grouped:
        data = group_process_rows(rows)
        return {"count": len(data), "grouped": True, "data": data}

    return {
        "count": len(rows),
        "grouped": False,
        "data": [
            {
                "process_name": row["process_name"],
                "memory_mb": row["memory_mb"],
                "cpu_percent": row["cpu_percent"],
                "timestamp": row["timestamp"],
            }
            for row in rows
        ],
    }


@router.get("/storage/breakdown")
def storage_breakdown(limit: int = Query(default=10, ge=1, le=30)):
    """Top-level home folder sizes."""
    data = scan_home_folders(limit=limit)
    return {"count": len(data), "data": data}


@router.get("/storage/large-files")
def storage_large_files(
    min_mb: int = Query(default=500, ge=100, le=5000),
    limit: int = Query(default=15, ge=1, le=50),
):
    """Largest files in the home directory."""
    data = find_large_files(min_mb=min_mb, limit=limit)
    return {"min_mb": min_mb, "count": len(data), "data": data}


@router.get("/cleanup/preview")
def cleanup_preview():
    """Show safe cleanup options and reclaimable space."""
    return get_cleanup_preview()


@router.post("/cleanup/run")
def cleanup_run(body: CleanupRequest):
    """Run user-approved safe cleanup actions."""
    if not body.action_ids:
        raise HTTPException(status_code=400, detail="No actions selected")
    return run_cleanup(body.action_ids)


@router.get("/startup-items")
def startup_items():
    """Login / launch items (read-only, macOS)."""
    data = list_startup_items()
    return {"count": len(data), "data": data}


@router.get("/processes/live")
def get_live_processes(limit: int = Query(default=25, ge=1, le=50)):
    """Running processes with PID for management actions."""
    data = list_live_processes(limit=limit)
    return {"count": len(data), "data": data}


@router.post("/processes/{pid}/kill")
def terminate_process(pid: int):
    """Terminate a process by PID."""
    if pid <= 0:
        raise HTTPException(status_code=400, detail="Invalid PID")
    result = kill_process(pid)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("message", "Failed"))
    return result


@router.get("/diagnoses")
def get_diagnoses(limit: int = Query(default=20, ge=1, le=100)):
    """Return past AI analyses, newest first."""
    rows = get_recent_diagnoses(limit=limit)
    data = []

    for row in rows:
        try:
            parsed = json.loads(row["issues"])
            status = parsed.get("status", "ok")
            issue_count = len(parsed.get("issues", []))
        except json.JSONDecodeError:
            status = "unknown"
            issue_count = 0

        data.append(
            {
                "id": row["id"],
                "timestamp": row["timestamp"],
                "status": status,
                "issue_count": issue_count,
                "explanation": row["ai_explanation"],
            }
        )

    return {"count": len(data), "data": data}


@router.get("/summary")
def get_summary(minutes_ago: int = Query(default=60, ge=5, le=1440)):
    """Compare current metrics to the closest snapshot from N minutes ago."""
    return build_comparison(minutes_ago=minutes_ago)


@router.get("/report")
def get_report():
    """Export a full snapshot: diagnosis, comparison, and top processes."""
    diagnosis = run_diagnosis(minutes=60).model_dump()
    comparison = build_comparison(minutes_ago=60)
    rows = get_latest_process_snapshots()

    return {
        "generated_at": int(time.time() * 1000),
        "diagnosis": diagnosis,
        "comparison": comparison,
        "top_processes": group_process_rows(rows),
    }


@router.post("/diagnose")
def diagnose():
    result = run_diagnosis(minutes=60)
    return result.model_dump()

@router.post("/analyze")
def analyze():
    """
    Run detection, send JSON to Ollama, return explanation.
    This is the endpoint the dashboard Analyze button calls.
    """
    result = run_diagnosis(minutes=60)
    diagnosis = result.model_dump()
    try:
        explanation = explain_diagnosis(diagnosis)
    except OllamaError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    insert_diagnosis(
        timestamp=int(time.time() * 1000),
        issues_json=json.dumps(diagnosis),
        ai_explanation=explanation,
    )
    return {
        "status": diagnosis["status"],
        "issues": diagnosis["issues"],
        "top_processes": diagnosis["top_processes"],
        "explanation": explanation,
    }