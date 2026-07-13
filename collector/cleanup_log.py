"""Cleanup action log for undo where possible."""

from __future__ import annotations

import time

from collector.db import get_cleanup_log, insert_cleanup_log_entry, mark_cleanup_restored


def log_cleanup_action(action_id: str, path: str, size_bytes: int) -> int:
    return insert_cleanup_log_entry(
        timestamp=int(time.time() * 1000),
        action_id=action_id,
        path=path,
        size_bytes=size_bytes,
    )


def list_recent_cleanup_actions(limit: int = 10) -> list[dict]:
    return get_cleanup_log(limit=limit)


def mark_action_restored(entry_id: int) -> None:
    mark_cleanup_restored(entry_id)
