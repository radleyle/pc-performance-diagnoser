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
from collector.db import init_db


INTERVAL_SECONDS = 5


def main() -> None:
    init_db()
    print("PC Performance Diagnoser — collector started")
    print(f"Saving every {INTERVAL_SECONDS} seconds. Press Ctrl+C to stop.\n")

    while True:
        timestamp = collect_snapshot()
        ts = datetime.fromtimestamp(timestamp / 1000).strftime("%H:%M:%S")
        print(f"[{ts}] Snapshot saved")
        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCollector stopped.")