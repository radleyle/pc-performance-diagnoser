"""Cross-platform application support paths."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def get_app_support_dir() -> Path:
    """Return PCDiagnoser config/cache directory, creating it if needed."""
    if sys.platform == "win32":
        base = Path(os.environ["LOCALAPPDATA"])
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path.home() / ".local" / "share"

    support_dir = base / "PCDiagnoser"
    support_dir.mkdir(parents=True, exist_ok=True)
    return support_dir
