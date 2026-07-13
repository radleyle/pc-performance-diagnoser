"""Folder size history and growth comparison."""

from __future__ import annotations

import time

from collector.db import get_folder_growth, insert_folder_snapshots
from collector.disk_scan import scan_home_folders


def save_folder_snapshot() -> int:
    """Store current top-level folder sizes."""
    folders = scan_home_folders(limit=20)
    timestamp = int(time.time() * 1000)
    rows = [
        {
            "folder_path": folder["path"],
            "folder_name": folder["name"],
            "size_bytes": folder["size_bytes"],
        }
        for folder in folders
    ]
    insert_folder_snapshots(timestamp, rows)
    return len(rows)


def get_folder_growth_report(days: int = 7) -> list[dict]:
    """Compare current folder sizes to the oldest snapshot within N days."""
    current = scan_home_folders(limit=20)
    past = get_folder_growth(days=days)
    past_by_path = {row["folder_path"]: row for row in past}

    results = []
    for folder in current:
        previous = past_by_path.get(folder["path"])
        delta_bytes = 0
        delta_gb = 0.0
        if previous:
            delta_bytes = folder["size_bytes"] - int(previous["size_bytes"])
            delta_gb = round(delta_bytes / (1024**3), 2)

        results.append(
            {
                "name": folder["name"],
                "path": folder["path"],
                "size_gb": folder["size_gb"],
                "delta_gb": delta_gb,
                "delta_bytes": delta_bytes,
                "has_history": previous is not None,
            }
        )

    results.sort(key=lambda row: abs(row["delta_bytes"]), reverse=True)
    return results
