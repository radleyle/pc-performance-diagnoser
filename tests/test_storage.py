"""Tests for storage and cleanup helpers."""

from collector.cleanup import get_cleanup_preview, run_cleanup


def test_cleanup_preview_shape():
    preview = get_cleanup_preview()

    assert "actions" in preview
    assert "total_reclaimable_bytes" in preview
    assert "total_reclaimable_mb" in preview
    assert len(preview["actions"]) == 4

    for action in preview["actions"]:
        assert action["id"] in {
            "empty_trash",
            "clear_user_caches",
            "clear_pip_cache",
            "clear_npm_cache",
        }
        assert "label" in action
        assert "size_mb" in action
        assert "available" in action


def test_run_cleanup_rejects_unknown_action():
    result = run_cleanup(["not_a_real_action"])

    assert len(result["results"]) == 1
    assert result["results"][0]["ok"] is False
    assert "Unknown" in result["results"][0]["message"]


def test_run_cleanup_empty_list_returns_empty_results():
    result = run_cleanup([])

    assert result["results"] == []
