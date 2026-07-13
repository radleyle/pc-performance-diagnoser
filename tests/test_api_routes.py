"""API route tests using FastAPI TestClient."""

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["api"] == "ok"
    assert "collector" in payload
    assert "ollama" in payload


def test_cleanup_preview_endpoint():
    response = client.get("/cleanup/preview")
    assert response.status_code == 200
    payload = response.json()
    assert "actions" in payload
    assert "total_reclaimable_mb" in payload


def test_storage_breakdown_returns_cache_metadata(monkeypatch):
    monkeypatch.setattr(
        "api.routes.get_cached_or_compute",
        lambda _key, _fn, refresh=False: {
            "data": [{"name": "Downloads", "path": "/tmp/Downloads", "size_bytes": 10, "size_gb": 0}],
            "cached_at": 1_700_000_000,
            "from_cache": True,
            "stale": False,
        },
    )

    response = client.get("/storage/breakdown")
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 1
    assert payload["from_cache"] is True
    assert payload["cached_at"] == 1_700_000_000


def test_reveal_rejects_paths_outside_home(monkeypatch):
    monkeypatch.setattr(
        "api.routes.reveal_in_file_manager",
        lambda _path: {"ok": False, "message": "Path must be inside your home directory"},
    )

    response = client.post("/storage/reveal", json={"path": "/etc/passwd"})
    assert response.status_code == 400


def test_kill_process_invalid_pid():
    response = client.post("/processes/0/kill")
    assert response.status_code == 400
