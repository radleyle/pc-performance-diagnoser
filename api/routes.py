"""HTTP route handlers for the PC Performance Diagnoser API."""

import json
import time
from fastapi import APIRouter, HTTPException, Query
from collector.db import (
    get_latest_process_snapshots,       
    get_metrics_since,
    insert_diagnosis,
)
from engine.detect import run_diagnosis
from engine.llm import OllamaError, explain_diagnosis

router = APIRouter()

@router.get("/health")
def health():
    return {"status": "ok", "service": "pc-performance-diagnoser"}


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
            }
            for row in rows
        ],
    }


@router.get("/processes")
def get_processes():
    rows = get_latest_process_snapshots()
    return {
        "count": len(rows),
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