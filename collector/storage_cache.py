"""Disk scan result cache — fast repeat loads, optional refresh."""

from __future__ import annotations

import json
import time
from typing import Any

from collector.paths import get_app_support_dir

DEFAULT_TTL_SECONDS = 3600


def _cache_path(key: str):
    cache_dir = get_app_support_dir() / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / f"{key}.json"


def read_cache(key: str) -> dict[str, Any] | None:
    path = _cache_path(key)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def write_cache(key: str, data: list[dict], *, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> dict[str, Any]:
    cached_at = int(time.time())
    payload = {
        "cached_at": cached_at,
        "expires_at": cached_at + ttl_seconds,
        "data": data,
    }
    path = _cache_path(key)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return payload


def get_cached_or_compute(
    key: str,
    compute_fn,
    *,
    refresh: bool = False,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
) -> dict[str, Any]:
    """
    Return cached scan data when fresh, otherwise compute and store.

    When refresh=False and cache exists (even if stale), returns stale data
    with from_cache=True so the UI can show results immediately while the
    caller may optionally trigger a background refresh.
    """
    cached = None if refresh else read_cache(key)
    now = int(time.time())

    if cached and cached.get("expires_at", 0) > now:
        return {
            "data": cached["data"],
            "cached_at": cached["cached_at"],
            "from_cache": True,
            "stale": False,
        }

    if cached and not refresh:
        return {
            "data": cached["data"],
            "cached_at": cached["cached_at"],
            "from_cache": True,
            "stale": True,
        }

    data = compute_fn()
    saved = write_cache(key, data, ttl_seconds=ttl_seconds)
    return {
        "data": saved["data"],
        "cached_at": saved["cached_at"],
        "from_cache": False,
        "stale": False,
    }
