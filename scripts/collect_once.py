"""Run one real collection cycle and print what was saved."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from datetime import datetime

import psutil

from collector.collect import collect_snapshot, collect_system_metrics, collect_top_processes
from collector.db import count_rows, get_recent_metrics, init_db


def main() -> None:
    print("=== Step 4: One real snapshot ===\n")

    init_db()

    # Preview what we read (before saving)
    metrics = collect_system_metrics()
    print("System metrics:")
    print(f"  CPU:          {metrics['cpu_percent']}%")
    print(f"  RAM avail:    {metrics['ram_available_mb']:.0f} MB")
    print(f"  RAM used:     {metrics['ram_used_percent']}%")

    print("\nTop 5 processes by memory:")
    for i, proc in enumerate(collect_top_processes(limit=5), start=1):
        print(
            f"  {i}. {proc['process_name']}: "
            f"{proc['memory_mb']:.0f} MB"
        )

    # Save to SQLite
    print("\nSaving to database...")
    timestamp = collect_snapshot()
    ts = datetime.fromtimestamp(timestamp / 1000)

    print(f"Saved snapshot at: {ts}")
    print(f"Total metrics rows:   {count_rows('metrics')}")
    print(f"Total process rows:   {count_rows('process_snapshots')}")

    recent = get_recent_metrics(limit=1)[0]
    print("\nLatest row in DB:")
    print(f"  cpu_percent:  {recent['cpu_percent']}%")
    print(f"  ram_avail:    {recent['ram_available_mb']:.0f} MB")

    print("\nDone! Real OS data is now in SQLite.")


if __name__ == "__main__":
    main()