"""
Background collector: read OS metrics every 5 seconds and save to SQLite.

Run from project root:
    python -m collector.main
"""

import sys
import time
from datetime import datetime
from pathlib import Path

# When run as `python collector/main.py`, fix import path.
# When run as `python -m collector.main`, this is harmless.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from collector.collect import collect_snapshot
from collector.db import init_db, purge_old_data
from collector.folder_growth import save_folder_snapshot
from collector.scheduler import maybe_run_scheduled_scan
from engine.baseline import update_baselines
from engine.config import get_config


def main() -> None:
    config = get_config()
    interval = config.collector.interval_seconds
    cleanup_every = config.collector.cleanup_every_cycles
    folder_every = config.collector.folder_snapshot_every_cycles
    baseline_every = config.collector.baseline_every_cycles
    retention_days = config.collector.retention_days

    init_db()
    print("PC Performance Diagnoser — collector started")
    print(f"Saving every {interval} seconds. Press Ctrl+C to stop.")
    print(f"Data retention: {retention_days} days\n")

    cycle = 0

    while True:
        timestamp = collect_snapshot()
        ts = datetime.fromtimestamp(timestamp / 1000).strftime("%H:%M:%S")
        print(f"[{ts}] Snapshot saved")

        cycle += 1
        if cycle % cleanup_every == 0:
            deleted = purge_old_data(retention_days=retention_days)
            total = sum(deleted.values())
            if total > 0:
                print(f"[{ts}] Purged {total} old rows (>{retention_days} days)")

        if cycle % folder_every == 0:
            count = save_folder_snapshot()
            print(f"[{ts}] Saved folder snapshot ({count} folders)")

        if cycle % baseline_every == 0:
            updated = update_baselines(days=7)
            if updated:
                print(f"[{ts}] Updated {updated} baseline buckets")

        if cycle % max(1, int((config.scheduler.interval_hours * 3600) / interval)) == 0:
            scheduled = maybe_run_scheduled_scan()
            if scheduled:
                print(f"[{ts}] Scheduled scan: {scheduled['status']}")

        time.sleep(interval)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCollector stopped.")
