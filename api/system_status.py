"""
Check health of all services: API, collector, and Ollama.
"""

import time

import httpx

from collector.db import get_latest_metric_timestamp

COLLECTOR_STALE_SECONDS = 20
OLLAMA_URL = "http://127.0.0.1:11434/api/tags"
OLLAMA_TIMEOUT_SECONDS = 3.0


def check_collector() -> dict:
    """
    Collector is 'ok' if we received a metric within the last 20 seconds.
    'stale' if data exists but is old. 'down' if no data at all.
    """
    last_ts = get_latest_metric_timestamp()
    now_ms = int(time.time() * 1000)

    if last_ts is None:
        return {
            "status": "down",
            "last_snapshot_ms": None,
            "seconds_ago": None,
            "message": "No metrics collected yet",
        }

    seconds_ago = round((now_ms - last_ts) / 1000, 1)

    if seconds_ago <= COLLECTOR_STALE_SECONDS:
        status = "ok"
        message = "Collecting metrics"
    else:
        status = "stale"
        message = f"Last snapshot {seconds_ago}s ago — is collector running?"

    return {
        "status": status,
        "last_snapshot_ms": last_ts,
        "seconds_ago": seconds_ago,
        "message": message,
    }


def check_ollama() -> dict:
    """Ping Ollama's model list endpoint."""
    try:
        response = httpx.get(OLLAMA_URL, timeout=OLLAMA_TIMEOUT_SECONDS)
        response.raise_for_status()
        data = response.json()
        models = [m.get("name", "") for m in data.get("models", [])]
        return {
            "status": "ok",
            "message": "Ollama is running",
            "models_available": len(models),
        }
    except httpx.HTTPError:
        return {
            "status": "down",
            "message": "Cannot reach Ollama — run: ollama serve",
            "models_available": 0,
        }