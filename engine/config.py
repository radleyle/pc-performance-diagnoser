"""
Load settings from config.yaml at the project root.

Falls back to built-in defaults if the file is missing or a key is absent.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.yaml"


@dataclass(frozen=True)
class CollectorConfig:
    interval_seconds: int = 5
    retention_days: int = 7
    cleanup_every_cycles: int = 720


@dataclass(frozen=True)
class ThresholdConfig:
    ram_critical_mb: float = 500
    ram_warning_mb: float = 1024
    ram_used_warning_percent: float = 90.0
    process_hog_mb: float = 1024
    cpu_high_percent: float = 90.0
    cpu_high_consecutive_samples: int = 3
    overflow_window_seconds: int = 60
    overflow_drop_fraction: float = 0.50
    disk_critical_free_gb: float = 2.0
    disk_warning_free_gb: float = 10.0
    disk_warning_used_percent: float = 90.0


@dataclass(frozen=True)
class AppConfig:
    collector: CollectorConfig
    thresholds: ThresholdConfig


def _merge_dict(defaults: dict, overrides: dict) -> dict:
    merged = dict(defaults)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge_dict(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config(path: Path | None = None) -> AppConfig:
    """Load config.yaml, using defaults for any missing values."""
    defaults = {
        "collector": {
            "interval_seconds": 5,
            "retention_days": 7,
            "cleanup_every_cycles": 720,
        },
        "thresholds": {
            "ram_critical_mb": 500,
            "ram_warning_mb": 1024,
            "ram_used_warning_percent": 90.0,
            "process_hog_mb": 1024,
            "cpu_high_percent": 90.0,
            "cpu_high_consecutive_samples": 3,
            "overflow_window_seconds": 60,
            "overflow_drop_fraction": 0.50,
            "disk_critical_free_gb": 2.0,
            "disk_warning_free_gb": 10.0,
            "disk_warning_used_percent": 90.0,
        },
    }

    config_path = path or CONFIG_PATH
    if config_path.exists():
        with config_path.open(encoding="utf-8") as handle:
            loaded = yaml.safe_load(handle) or {}
        data = _merge_dict(defaults, loaded)
    else:
        data = defaults

    return AppConfig(
        collector=CollectorConfig(**data["collector"]),
        thresholds=ThresholdConfig(**data["thresholds"]),
    )


_config: AppConfig | None = None


def get_config() -> AppConfig:
    """Return cached config (loaded once per process)."""
    global _config
    if _config is None:
        _config = load_config()
    return _config
