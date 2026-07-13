"""Reveal files in the system file manager (macOS Finder)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def reveal_in_file_manager(path: str) -> dict:
    """Open the parent folder and highlight a file/folder in Finder."""
    target = Path(path).expanduser().resolve()
    home = Path.home().resolve()

    if not str(target).startswith(str(home)):
        return {"ok": False, "message": "Path must be inside your home directory"}

    if not target.exists():
        return {"ok": False, "message": "Path does not exist"}

    if sys.platform == "darwin":
        try:
            subprocess.run(["open", "-R", str(target)], check=True, capture_output=True)
            return {"ok": True, "message": "Revealed in Finder"}
        except subprocess.CalledProcessError as exc:
            return {"ok": False, "message": exc.stderr.decode() if exc.stderr else str(exc)}

    return {"ok": False, "message": "Reveal is only supported on macOS"}
