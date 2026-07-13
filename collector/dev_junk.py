"""Developer cache and build artifact discovery."""

from __future__ import annotations

from pathlib import Path


def _dir_size_shallow(path: Path, max_entries: int = 500) -> int:
    if not path.exists():
        return 0
    total = 0
    count = 0
    try:
        for entry in path.rglob("*"):
            if entry.is_file():
                try:
                    total += entry.stat().st_size
                    count += 1
                    if count >= max_entries:
                        break
                except OSError:
                    continue
    except OSError:
        return 0
    return total


def _find_named_dirs(root: Path, names: set[str], max_depth: int = 5) -> list[Path]:
    matches: list[Path] = []

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
            if entry.is_dir():
                if entry.name in names:
                    matches.append(entry)
                elif entry.name not in {".git", "Library", "Applications"}:
                    walk(entry, depth + 1)

    walk(root, 0)
    return matches


def scan_dev_junk(limit: int = 15) -> list[dict]:
    """Find common developer artifacts and caches."""
    home = Path.home()
    targets: list[dict] = []

    named = {
        "node_modules",
        ".venv",
        "__pycache__",
        "DerivedData",
        ".gradle",
        "target",
        "dist",
        "build",
    }
    for folder in _find_named_dirs(home, named):
        size_bytes = _dir_size_shallow(folder)
        if size_bytes <= 0:
            continue
        targets.append(
            {
                "name": folder.name,
                "path": str(folder),
                "category": _category_for(folder.name),
                "size_bytes": size_bytes,
                "size_mb": round(size_bytes / (1024**2), 1),
            }
        )

    special = [
        ("Xcode DerivedData", home / "Library" / "Developer" / "Xcode" / "DerivedData"),
        ("Docker data", home / "Library" / "Containers" / "com.docker.docker"),
        ("npm cache", home / ".npm"),
        ("pip cache", home / "Library" / "Caches" / "pip"),
    ]
    for label, path in special:
        size_bytes = _dir_size_shallow(path)
        if size_bytes <= 0:
            continue
        targets.append(
            {
                "name": label,
                "path": str(path),
                "category": "developer",
                "size_bytes": size_bytes,
                "size_mb": round(size_bytes / (1024**2), 1),
            }
        )

    targets.sort(key=lambda row: row["size_bytes"], reverse=True)
    return targets[:limit]


def _category_for(name: str) -> str:
    if name in {"node_modules", ".gradle", "target", "dist", "build", "DerivedData"}:
        return "build"
    if name in {".venv", "__pycache__"}:
        return "python"
    return "developer"
