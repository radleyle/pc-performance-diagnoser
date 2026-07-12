"""HTTP route handlers for the PC Performance Diagnoser API."""

import json
import time

from fastapi import APIRouter, HTTPException, Query

from api.system_status import check_collector, check_ollama
from collector.db import (
    get_latest_process_snapshots,
    get_metrics_since,
    get_recent_diagnoses,
    insert_diagnosis,
)
from collector.process_groups import group_process_rows
from engine.detect import run_diagnosis
from engine.llm import OllamaError, explain_diagnosis

router = APIRouter()

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