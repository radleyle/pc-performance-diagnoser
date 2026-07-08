"""
Unit tests for engine/detect.py detection rules.

Each test uses fake sample data — no SQLite, no real OS needed.
Run with: pytest tests/ -v
"""

import time

from engine.detect import (
    _check_high_cpu,
    _check_memory_overflow,
    _check_process_hogs,
    _check_ram_critical,
    _check_ram_warning,
    _compute_status,
)
from engine.schemas import Issue


# ---------------------------------------------------------------------------
# Helpers — fake data that looks like SQLite rows
# ---------------------------------------------------------------------------

def make_metric(
    *,
    offset_seconds: int = 0,
    cpu_percent: float = 10.0,
    ram_available_mb: float = 4000.0,
    ram_used_percent: float = 50.0,
) -> dict:
    """Build one fake metrics row with a timestamp relative to now."""
    return {
        "timestamp": int(time.time() * 1000) - (offset_seconds * 1000),
        "cpu_percent": cpu_percent,
        "ram_available_mb": ram_available_mb,
        "ram_used_percent": ram_used_percent,
    }


def make_process(name: str, memory_mb: float) -> dict:
    """Build one fake process snapshot row."""
    return {
        "process_name": name,
        "memory_mb": memory_mb,
    }


# ---------------------------------------------------------------------------
# RAM critical: available RAM < 500 MB
# ---------------------------------------------------------------------------

def test_ram_critical_fires_when_below_500mb():
    issue = _check_ram_critical(ram_available_mb=280, ram_used_percent=96.0)

    assert issue is not None
    assert issue.type == "ram_critical"
    assert issue.severity == "high"
    assert "280" in issue.message


def test_ram_critical_does_not_fire_when_enough_ram():
    issue = _check_ram_critical(ram_available_mb=800, ram_used_percent=96.0)

    assert issue is None


# ---------------------------------------------------------------------------
# RAM warning: available < 1 GB OR used > 90%
# ---------------------------------------------------------------------------

def test_ram_warning_fires_when_available_below_1gb():
    issue = _check_ram_warning(ram_available_mb=900, ram_used_percent=80.0)

    assert issue is not None
    assert issue.type == "ram_warning"
    assert issue.severity == "medium"


def test_ram_warning_fires_when_used_above_90_percent():
    issue = _check_ram_warning(ram_available_mb=5000, ram_used_percent=92.0)

    assert issue is not None
    assert issue.type == "ram_warning"


def test_ram_warning_does_not_fire_when_healthy():
    issue = _check_ram_warning(ram_available_mb=5000, ram_used_percent=70.0)

    assert issue is None


# ---------------------------------------------------------------------------
# Process memory hog: single process > 1 GB
# ---------------------------------------------------------------------------

def test_process_hog_fires_above_1gb():
    rows = [make_process("chrome.exe", 2100)]

    issues = _check_process_hogs(rows)

    assert len(issues) == 1
    assert issues[0].type == "process_memory_hog"
    assert issues[0].evidence["process_name"] == "chrome.exe"


def test_process_hog_ignores_small_processes():
    rows = [
        make_process("Cursor", 400),
        make_process("Safari", 600),
    ]

    issues = _check_process_hogs(rows)

    assert issues == []


# ---------------------------------------------------------------------------
# Memory overflow: RAM dropped > 50% in 60 seconds
# ---------------------------------------------------------------------------

def test_memory_overflow_fires_on_large_drop():
    # 60s ago: 4000 MB free → now: 1500 MB free (62.5% drop)
    rows = [
        make_metric(offset_seconds=60, ram_available_mb=4000.0),
        make_metric(offset_seconds=0, ram_available_mb=1500.0),
    ]

    issue = _check_memory_overflow(rows)

    assert issue is not None
    assert issue.type == "memory_overflow"
    assert issue.severity == "high"


def test_memory_overflow_does_not_fire_on_small_drop():
    # 4000 → 3000 is only 25% drop
    rows = [
        make_metric(offset_seconds=60, ram_available_mb=4000.0),
        make_metric(offset_seconds=0, ram_available_mb=3000.0),
    ]

    issue = _check_memory_overflow(rows)

    assert issue is None


def test_memory_overflow_needs_at_least_two_samples():
    rows = [make_metric(ram_available_mb=4000.0)]

    issue = _check_memory_overflow(rows)

    assert issue is None


# ---------------------------------------------------------------------------
# High CPU: > 90% for 3 consecutive samples
# ---------------------------------------------------------------------------

def test_high_cpu_fires_on_three_high_samples():
    rows = [
        make_metric(offset_seconds=10, cpu_percent=95.0),
        make_metric(offset_seconds=5, cpu_percent=92.0),
        make_metric(offset_seconds=0, cpu_percent=91.0),
    ]

    issue = _check_high_cpu(rows)

    assert issue is not None
    assert issue.type == "high_cpu"
    assert issue.severity == "medium"


def test_high_cpu_does_not_fire_if_one_sample_is_low():
    rows = [
        make_metric(offset_seconds=10, cpu_percent=95.0),
        make_metric(offset_seconds=5, cpu_percent=50.0),  # breaks the streak
        make_metric(offset_seconds=0, cpu_percent=91.0),
    ]

    issue = _check_high_cpu(rows)

    assert issue is None


def test_high_cpu_needs_three_samples():
    rows = [
        make_metric(cpu_percent=95.0),
        make_metric(cpu_percent=92.0),
    ]

    issue = _check_high_cpu(rows)

    assert issue is None


# ---------------------------------------------------------------------------
# Overall status: critical / warning / ok
# ---------------------------------------------------------------------------

def test_compute_status_critical_when_high_severity_present():
    issues = [
        Issue(
            type="ram_critical",
            severity="high",
            message="test",
        )
    ]

    assert _compute_status(issues) == "critical"


def test_compute_status_warning_when_only_medium_issues():
    issues = [
        Issue(
            type="ram_warning",
            severity="medium",
            message="test",
        )
    ]

    assert _compute_status(issues) == "warning"


def test_compute_status_ok_when_no_issues():
    assert _compute_status([]) == "ok"