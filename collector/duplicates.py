"""Conservative duplicate file finder — same name + size groups."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path


def find_duplicate_groups(
    min_mb: int = 10,
    limit: int = 20,
    max_depth: int = 4,
) -> list[dict]:
    """Find groups of files with the same name and size under home."""
    home = Path.home()
    min_bytes = min_mb * 1024 * 1024
    groups: dict[tuple[str, int], list[dict]] = defaultdict(list)

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
                        key = (entry.name.lower(), size)
                        groups[key].append(
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

    walk(home, 0)

    results = []
    for (_name, _size), files in groups.items():
        if len(files) < 2:
            continue
        total_waste = files[0]["size_bytes"] * (len(files) - 1)
        results.append(
            {
                "name": files[0]["name"],
                "size_mb": files[0]["size_mb"],
                "count": len(files),
                "waste_mb": round(total_waste / (1024**2), 1),
                "files": files,
            }
        )

    results.sort(key=lambda row: row["waste_mb"], reverse=True)
    return results[:limit]
