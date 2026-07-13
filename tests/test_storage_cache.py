"""Tests for storage cache helpers."""

import json
import time

from collector.storage_cache import get_cached_or_compute, read_cache, write_cache


def test_write_and_read_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "collector.storage_cache.get_app_support_dir",
        lambda: tmp_path,
    )

    write_cache("demo", [{"name": "Downloads", "size_bytes": 1000}])
    cached = read_cache("demo")

    assert cached is not None
    assert cached["data"][0]["name"] == "Downloads"


def test_get_cached_or_compute_uses_fresh_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "collector.storage_cache.get_app_support_dir",
        lambda: tmp_path,
    )

    calls = {"count": 0}

    def compute():
        calls["count"] += 1
        return [{"value": calls["count"]}]

    first = get_cached_or_compute("items", compute, ttl_seconds=3600)
    second = get_cached_or_compute("items", compute, ttl_seconds=3600)

    assert first["from_cache"] is False
    assert second["from_cache"] is True
    assert second["data"][0]["value"] == 1
    assert calls["count"] == 1


def test_get_cached_or_compute_refresh_recomputes(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "collector.storage_cache.get_app_support_dir",
        lambda: tmp_path,
    )

    write_cache("items", [{"value": 1}], ttl_seconds=3600)

    result = get_cached_or_compute(
        "items",
        lambda: [{"value": 2}],
        refresh=True,
        ttl_seconds=3600,
    )

    assert result["from_cache"] is False
    assert result["data"][0]["value"] == 2


def test_stale_cache_flagged_when_expired(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "collector.storage_cache.get_app_support_dir",
        lambda: tmp_path,
    )

    cache_file = tmp_path / "cache" / "items.json"
    cache_file.parent.mkdir(parents=True)
    cache_file.write_text(
        json.dumps(
            {
                "cached_at": int(time.time()) - 7200,
                "expires_at": int(time.time()) - 3600,
                "data": [{"value": 9}],
            }
        ),
        encoding="utf-8",
    )

    result = get_cached_or_compute("items", lambda: [{"value": 1}], refresh=False)

    assert result["from_cache"] is True
    assert result["stale"] is True
    assert result["data"][0]["value"] == 9
