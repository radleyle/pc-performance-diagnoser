"""Scheduled diagnosis runs from the collector loop."""

from __future__ import annotations

import json
import time

from collector.db import get_last_scheduled_diagnosis_ms, insert_diagnosis
from engine.config import get_config
from engine.detect import run_diagnosis
from engine.llm import OllamaError, explain_diagnosis


def maybe_run_scheduled_scan() -> dict | None:
    """Run a scheduled diagnosis if the interval has elapsed."""
    config = get_config().scheduler
    if not config.enabled:
        return None

    now_ms = int(time.time() * 1000)
    interval_ms = config.interval_hours * 60 * 60 * 1000
    last_ms = get_last_scheduled_diagnosis_ms()

    if last_ms is not None and (now_ms - last_ms) < interval_ms:
        return None

    result = run_diagnosis(minutes=60)
    diagnosis = result.model_dump()
    explanation = None

    if config.run_ai:
        try:
            explanation = explain_diagnosis(diagnosis)
        except OllamaError:
            explanation = None

    insert_diagnosis(
        timestamp=now_ms,
        issues_json=json.dumps(diagnosis),
        ai_explanation=explanation,
        source="scheduled",
    )
    return {"timestamp": now_ms, "status": diagnosis["status"], "source": "scheduled"}
