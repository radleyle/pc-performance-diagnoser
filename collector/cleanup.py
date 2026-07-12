"""
Safe cleanup helpers — preview sizes, then delete only approved targets.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def _dir_size_shallow(path: Path) -> int:
    if not path.exists():
        return 0
    total = 0
    try:
        for entry in path.rglob("*"):
            if entry.is_file():
                try:
                    total += entry.stat().st_size
                except OSError:
                    continue
    except OSError:
        return 0
    return total


def _trash_size() -> int:
    trash = Path.home() / ".Trash"
    return _dir_size_shallow(trash)


def _cache_size() -> int:
    caches = Path.home() / "Library" / "Caches"
    return _dir_size_shallow(caches)


def get_cleanup_preview() -> dict:
    """Return reclaimable space for safe cleanup categories."""
    trash_bytes = _trash_size()
    cache_bytes = _cache_size()

    actions = [
        {
            "id": "empty_trash",
            "label": "Empty Trash",
            "description": "Permanently delete items in the Trash.",
            "size_bytes": trash_bytes,
            "size_mb": round(trash_bytes / (1024**2), 1),
            "available": trash_bytes > 0,
        },
        {
            "id": "clear_user_caches",
            "label": "Clear user caches",
            "description": "Remove ~/Library/Caches (apps will rebuild as needed).",
            "size_bytes": cache_bytes,
            "size_mb": round(cache_bytes / (1024**2), 1),
            "available": cache_bytes > 0,
        },
    ]

    total = sum(a["size_bytes"] for a in actions if a["available"])

    return {
        "actions": actions,
        "total_reclaimable_bytes": total,
        "total_reclaimable_mb": round(total / (1024**2), 1),
    }


def run_cleanup(action_ids: list[str]) -> dict:
    """Run only whitelisted cleanup actions."""
    allowed = {"empty_trash", "clear_user_caches"}
    results: list[dict] = []

    for action_id in action_ids:
        if action_id not in allowed:
            results.append({"id": action_id, "ok": False, "message": "Unknown action"})
            continue

        if action_id == "empty_trash":
            results.append(_empty_trash())
        elif action_id == "clear_user_caches":
            results.append(_clear_user_caches())

    return {"results": results}


def _empty_trash() -> dict:
    trash = Path.home() / ".Trash"
    if not trash.exists():
        return {"id": "empty_trash", "ok": True, "message": "Trash already empty"}

    if sys.platform == "darwin":
        try:
            subprocess.run(
                ["osascript", "-e", 'tell application "Finder" to empty trash'],
                check=True,
                capture_output=True,
                text=True,
            )
            return {"id": "empty_trash", "ok": True, "message": "Trash emptied"}
        except subprocess.CalledProcessError as exc:
            return {"id": "empty_trash", "ok": False, "message": exc.stderr or str(exc)}

    removed = 0
    try:
        for entry in trash.iterdir():
            if entry.is_dir():
                shutil.rmtree(entry, ignore_errors=True)
            else:
                entry.unlink(missing_ok=True)
            removed += 1
    except OSError as exc:
        return {"id": "empty_trash", "ok": False, "message": str(exc)}

    return {"id": "empty_trash", "ok": True, "message": f"Removed {removed} item(s)"}


def _clear_user_caches() -> dict:
    caches = Path.home() / "Library" / "Caches"
    if not caches.exists():
        return {"id": "clear_user_caches", "ok": True, "message": "No caches found"}

    removed = 0
    try:
        for entry in caches.iterdir():
            if entry.is_dir():
                shutil.rmtree(entry, ignore_errors=True)
            else:
                entry.unlink(missing_ok=True)
            removed += 1
    except OSError as exc:
        return {"id": "clear_user_caches", "ok": False, "message": str(exc)}

    return {
        "id": "clear_user_caches",
        "ok": True,
        "message": f"Cleared {removed} cache folder(s)",
    }
