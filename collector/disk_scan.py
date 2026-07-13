"""
Disk usage analysis: folder breakdown and large file discovery.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _dir_size(path: Path, *, max_depth: int = 3, _depth: int = 0) -> int:
    """Return total bytes under path (bounded depth for speed)."""
    if not path.exists():
        return 0

    if path.is_file():
        try:
            return path.stat().st_size
        except OSError:
            return 0

    if _depth >= max_depth:
        return 0

    total = 0
    try:
        for entry in path.iterdir():
            if entry.is_symlink():
                continue
            try:
                if entry.is_file():
                    total += entry.stat().st_size
                elif entry.is_dir():
                    total += _dir_size(entry, max_depth=max_depth, _depth=_depth + 1)
            except OSError:
                continue
    except OSError:
        return 0

    return total


def _scan_home_folders_du(limit: int) -> list[dict] | None:
    """Fast top-level folder sizes on macOS using du."""
    if sys.platform != "darwin":
        return None

    home = Path.home()
    try:
        result = subprocess.run(
            ["du", "-sk", "-d", "1", str(home)],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None

    if result.returncode != 0 or not result.stdout.strip():
        return None

    results: list[dict] = []
    for line in result.stdout.splitlines():
        parts = line.split("\t", 1)
        if len(parts) != 2:
            continue
        try:
            size_kb = int(parts[0])
        except ValueError:
            continue

        folder = Path(parts[1])
        if folder == home:
            continue
        if not folder.is_dir():
            continue
        if folder.name.startswith(".") and folder.name not in {".Trash"}:
            continue

        size_bytes = size_kb * 1024
        if size_bytes <= 0:
            continue

        results.append(
            {
                "name": folder.name,
                "path": str(folder),
                "size_bytes": size_bytes,
                "size_gb": round(size_bytes / (1024**3), 2),
            }
        )

    results.sort(key=lambda row: row["size_bytes"], reverse=True)
    return results[:limit]


def scan_home_folders(limit: int = 12) -> list[dict]:
    """Size of each top-level folder in the user's home directory."""
    fast = _scan_home_folders_du(limit)
    if fast is not None:
        return fast

    home = Path.home()
    results: list[dict] = []

    try:
        entries = sorted(home.iterdir(), key=lambda p: p.name.lower())
    except OSError:
        return results

    for entry in entries:
        if not entry.is_dir() or entry.is_symlink():
            continue
        if entry.name.startswith(".") and entry.name not in {".Trash"}:
            continue

        size_bytes = _dir_size(entry, max_depth=2)
        if size_bytes <= 0:
            continue

        results.append(
            {
                "name": entry.name,
                "path": str(entry),
                "size_bytes": size_bytes,
                "size_gb": round(size_bytes / (1024**3), 2),
            }
        )

    results.sort(key=lambda row: row["size_bytes"], reverse=True)
    return results[:limit]


def find_large_files(
    min_mb: int = 500,
    limit: int = 20,
    max_depth: int = 4,
) -> list[dict]:
    """Find the largest files under the user's home directory."""
    home = Path.home()
    min_bytes = min_mb * 1024 * 1024
    matches: list[dict] = []

    def walk(path: Path, depth: int) -> None:
        if depth > max_depth:
            return
        try:
            entries = list(path.iterdir())
        except OSError:
            return

        for entry in entries:
            if entry.is_symlink():
                continue
            try:
                if entry.is_file():
                    size = entry.stat().st_size
                    if size >= min_bytes:
                        matches.append(
                            {
                                "name": entry.name,
                                "path": str(entry),
                                "size_bytes": size,
                                "size_mb": round(size / (1024**2), 1),
                            }
                        )
                elif entry.is_dir():
                    if entry.name in {".git", "node_modules", ".venv", "Library"}:
                        continue
                    walk(entry, depth + 1)
            except OSError:
                continue

    walk(home, depth=0)
    matches.sort(key=lambda row: row["size_bytes"], reverse=True)
    return matches[:limit]
