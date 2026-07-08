"""Quick test: create tables and insert fake sample rows."""

import sys
from pathlib import Path
# Allow imports from project root (collector/, engine/, etc.)
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import time
from datetime import datetime

from collector.db import (
    count_rows,
    get_db_path,
    get_recent_metrics,
    init_db,
    insert_metric,
    insert_process_snapshot,
)


def main() -> None:
    print("=== : Database test ===\n")

    # 1. Show where the file will be created
    db_path = get_db_path()
    print(f"Database path: {db_path}")

    # 2. Create tables
    init_db()
    print("Tables created (or already existed).\n")

    # 3. Insert one fake metrics row
    now_ms = int(time.time() * 1000)  # Unix timestamp in milliseconds
    insert_metric(
        timestamp=now_ms,
        cpu_percent=23.5,
        ram_available_mb=8192.0,
        ram_used_percent=48.0,
    )

    # 4. Insert two fake process rows (same timestamp = same "snapshot moment")
    insert_process_snapshot(now_ms, "Safari", 450.0, 2.1)
    insert_process_snapshot(now_ms, "Cursor", 890.0, 5.3)

    # 5. Read back counts
    print(f"metrics rows:           {count_rows('metrics')}")
    print(f"process_snapshots rows: {count_rows('process_snapshots')}\n")

    # 6. Show latest metrics row
    recent = get_recent_metrics(limit=1)
    if recent:
        row = recent[0]
        ts = datetime.fromtimestamp(row["timestamp"] / 1000)
        print("Latest metrics row:")
        print(f"  time:         {ts}")
        print(f"  cpu_percent:  {row['cpu_percent']}%")
        print(f"  ram_avail:    {row['ram_available_mb']} MB")
        print(f"  ram_used:     {row['ram_used_percent']}%")

    print("\nDone! If you see row counts >= 1, Step 2 worked.")


if __name__ == "__main__":
    main()