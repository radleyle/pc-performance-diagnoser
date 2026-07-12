"""
List startup / login items on macOS (read-only).
"""

from __future__ import annotations

import plistlib
import sys
from pathlib import Path


def _read_plist_name(path: Path) -> str | None:
    try:
        with path.open("rb") as handle:
            data = plistlib.load(handle)
        label = data.get("Label")
        if label:
            return str(label)
        return path.stem
    except Exception:
        return path.stem


def list_startup_items() -> list[dict]:
    """Return launch agents/daemons visible to the user (read-only)."""
    if sys.platform != "darwin":
        return []

    locations = [
        ("User Launch Agents", Path.home() / "Library" / "LaunchAgents"),
        ("System Launch Agents", Path("/Library/LaunchAgents")),
    ]

    items: list[dict] = []

    for location_name, folder in locations:
        if not folder.exists():
            continue
        try:
            for entry in sorted(folder.glob("*.plist")):
                items.append(
                    {
                        "name": _read_plist_name(entry) or entry.name,
                        "path": str(entry),
                        "location": location_name,
                        "enabled": True,
                    }
                )
        except OSError:
            continue

    return items
