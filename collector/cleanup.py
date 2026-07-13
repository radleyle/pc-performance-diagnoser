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
    pip_cache = _dir_size_shallow(Path.home() / "Library" / "Caches" / "pip")
    npm_cache = _dir_size_shallow(Path.home() / ".npm")

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
        {
            "id": "clear_pip_cache",
            "label": "Clear pip cache",
            "description": "Remove downloaded Python package wheels.",
            "size_bytes": pip_cache,
            "size_mb": round(pip_cache / (1024**2), 1),
            "available": pip_cache > 0,
        },
        {
            "id": "clear_npm_cache",
            "label": "Clear npm cache",
            "description": "Remove cached npm packages.",
            "size_bytes": npm_cache,
            "size_mb": round(npm_cache / (1024**2), 1),
            "available": npm_cache > 0,
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
    allowed = {
        "empty_trash",
        "clear_user_caches",
        "clear_pip_cache",
        "clear_npm_cache",
    }
    results: list[dict] = []

    for action_id in action_ids:
        if action_id not in allowed:
            results.append({"id": action_id, "ok": False, "message": "Unknown action"})
            continue

        if action_id == "empty_trash":
            results.append(_empty_trash())
        elif action_id == "clear_user_caches":
            results.append(_clear_user_caches())
        elif action_id == "clear_pip_cache":
            results.append(_clear_path_cache(Path.home() / "Library" / "Caches" / "pip", "clear_pip_cache"))
        elif action_id == "clear_npm_cache":
            results.append(_clear_path_cache(Path.home() / ".npm", "clear_npm_cache"))

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


def _clear_path_cache(path: Path, action_id: str) -> dict:
    if not path.exists():
        return {"id": action_id, "ok": True, "message": "Already empty"}

    size_bytes = _dir_size_shallow(path)
    try:
        shutil.rmtree(path, ignore_errors=True)
        path.mkdir(parents=True, exist_ok=True)
        return {
            "id": action_id,
            "ok": True,
            "message": f"Cleared {round(size_bytes / (1024**2), 1)} MB",
            "path": str(path),
            "size_bytes": size_bytes,
        }
    except OSError as exc:
        return {"id": action_id, "ok": False, "message": str(exc)}
