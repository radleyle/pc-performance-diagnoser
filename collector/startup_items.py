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
        disabled = folder / "disabled"
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
            if disabled.exists():
                for entry in sorted(disabled.glob("*.plist")):
                    items.append(
                        {
                            "name": _read_plist_name(entry) or entry.name,
                            "path": str(entry),
                            "location": f"{location_name} (disabled)",
                            "enabled": False,
                        }
                    )
        except OSError:
            continue

    return items


def set_startup_item_enabled(path: str, enabled: bool) -> dict:
    """Disable/enable a user LaunchAgent by moving it to a disabled folder."""
    import shutil
    import sys

    if sys.platform != "darwin":
        return {"ok": False, "message": "Startup control is macOS only"}

    plist = Path(path)
    agents_dir = Path.home() / "Library" / "LaunchAgents"
    disabled_dir = agents_dir / "disabled"
    disabled_dir.mkdir(parents=True, exist_ok=True)

    if not str(plist).startswith(str(agents_dir)):
        return {"ok": False, "message": "Only user LaunchAgents can be changed"}

    try:
        if enabled:
            if plist.parent == disabled_dir:
                target = agents_dir / plist.name
                shutil.move(str(plist), str(target))
                return {"ok": True, "message": f"Enabled {plist.name}", "enabled": True}
            return {"ok": True, "message": "Already enabled", "enabled": True}

        if plist.parent == agents_dir:
            target = disabled_dir / plist.name
            shutil.move(str(plist), str(target))
            return {"ok": True, "message": f"Disabled {plist.name}", "enabled": False}
        return {"ok": True, "message": "Already disabled", "enabled": False}
    except OSError as exc:
        return {"ok": False, "message": str(exc)}
