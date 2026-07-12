"""
Read CPU, RAM, and top processes from the OS using psutil.

This module only *reads* data. Saving to SQLite happens in collect_snapshot().
"""

import sys
import time

import psutil


def now_ms() -> int:
    """Current time as Unix milliseconds (matches our DB schema)."""
    return int(time.time() * 1000)


def get_disk_path() -> str:
    """Main system drive: C:\\ on Windows, / on macOS and Linux."""
    if sys.platform == "win32":
        return "C:\\"
    return "/"


def collect_system_metrics() -> dict:
    """
    Read one system-wide snapshot: CPU %, RAM, and disk space.

    cpu_percent(interval=1) waits ~1 second to measure CPU accurately
    (same idea as Task Manager — you need a short window to measure usage).
    """
    cpu_percent = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage(get_disk_path())

    return {
        "cpu_percent": cpu_percent,
        "ram_available_mb": mem.available / (1024 ** 2),
        "ram_used_percent": mem.percent,
        "disk_free_gb": disk.free / (1024 ** 3),
        "disk_used_percent": disk.percent,
    }


def collect_top_processes(limit: int = 10) -> list[dict]:
    """
    Return the top `limit` processes sorted by memory (RSS), highest first.

    Some processes may disappear or deny access while we scan — we skip those.
    """
    processes: list[dict] = []

    for proc in psutil.process_iter(["name", "memory_info", "cpu_percent"]):
        try:
            info = proc.info
            memory_info = info.get("memory_info")
            if memory_info is None:
                continue

            memory_mb = memory_info.rss / (1024 ** 2)

            processes.append(
                {
                    "process_name": info.get("name") or "unknown",
                    "memory_mb": memory_mb,
                    "cpu_percent": info.get("cpu_percent"),
                }
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    processes.sort(key=lambda p: p["memory_mb"], reverse=True)
    return processes[:limit]


def collect_snapshot() -> int:
    """
    One full collection cycle:
      1. Read system metrics
      2. Read top 10 processes
      3. Save everything to SQLite

    Returns the timestamp (ms) used for this snapshot.
    """
    from collector.db import insert_metric, insert_process_snapshot

    timestamp = now_ms()

    metrics = collect_system_metrics()
    insert_metric(
        timestamp=timestamp,
        cpu_percent=metrics["cpu_percent"],
        ram_available_mb=metrics["ram_available_mb"],
        ram_used_percent=metrics["ram_used_percent"],
        disk_free_gb=metrics["disk_free_gb"],
        disk_used_percent=metrics["disk_used_percent"],
    )

    for proc in collect_top_processes(limit=10):
        insert_process_snapshot(
            timestamp=timestamp,
            process_name=proc["process_name"],
            memory_mb=proc["memory_mb"],
            cpu_percent=proc["cpu_percent"],
        )

    return timestamp