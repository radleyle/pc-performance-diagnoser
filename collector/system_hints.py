"""macOS storage hints for Photos, iCloud, and local snapshots."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from collector.disk_scan import _dir_size


def get_system_storage_hints() -> list[dict]:
    """Read-only hints about large system-related storage."""
    if sys.platform != "darwin":
        return []

    hints: list[dict] = []
    home = Path.home()

    photos = home / "Pictures" / "Photos Library.photoslibrary"
    if photos.exists():
        size = _dir_size(photos, max_depth=1)
        if size > 0:
            hints.append(
                {
                    "name": "Photos Library",
                    "path": str(photos),
                    "size_gb": round(size / (1024**3), 2),
                    "hint": "Manage in Photos → Settings → Storage",
                }
            )

    mobile_backup = home / "Library" / "Application Support" / "MobileSync" / "Backup"
    if mobile_backup.exists():
        size = _dir_size(mobile_backup, max_depth=2)
        if size > 0:
            hints.append(
                {
                    "name": "iOS device backups",
                    "path": str(mobile_backup),
                    "size_gb": round(size / (1024**3), 2),
                    "hint": "Review old backups in Finder or iTunes/Finder device settings",
                }
            )

    icloud = home / "Library" / "Mobile Documents"
    if icloud.exists():
        size = _dir_size(icloud, max_depth=2)
        if size > 0:
            hints.append(
                {
                    "name": "iCloud Drive (local)",
                    "path": str(icloud),
                    "size_gb": round(size / (1024**3), 2),
                    "hint": "Files may also exist in iCloud — check System Settings → Apple ID",
                }
            )

    try:
        result = subprocess.run(
            ["tmutil", "listlocalsnapshots", "/"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            count = len([line for line in result.stdout.splitlines() if "com.apple" in line])
            if count > 0:
                hints.append(
                    {
                        "name": "Time Machine local snapshots",
                        "path": "/",
                        "size_gb": None,
                        "hint": f"{count} local snapshot(s) — macOS may reclaim space automatically",
                    }
                )
    except (OSError, subprocess.TimeoutExpired):
        pass

    return hints
