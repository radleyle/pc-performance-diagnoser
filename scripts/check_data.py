"""Show how much data the collector has stored."""

import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from collector.db import count_rows, get_connection, get_db_path


def main() -> None:
    print("=== Collector data status ===\n")
    print(f"Database: {get_db_path()}\n")

    metrics_count = count_rows("metrics")
    process_count = count_rows("process_snapshots")

    print(f"metrics rows:           {metrics_count}")
    print(f"process_snapshots rows: {process_count}")

    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT MIN(timestamp) AS first_ts, MAX(timestamp) AS last_ts FROM metrics"
        ).fetchone()

        if row and row["first_ts"]:
            first = datetime.fromtimestamp(row["first_ts"] / 1000)
            last = datetime.fromtimestamp(row["last_ts"] / 1000)
            duration_min = (row["last_ts"] - row["first_ts"]) / 1000 / 60

            print(f"\nFirst snapshot:  {first}")
            print(f"Latest snapshot: {last}")
            print(f"Time span:       {duration_min:.1f} minutes")

            latest = conn.execute(
                """
                SELECT cpu_percent, ram_available_mb, ram_used_percent
                FROM metrics ORDER BY timestamp DESC LIMIT 1
                """
            ).fetchone()
            print(f"\nLatest reading:")
            print(f"  CPU:       {latest['cpu_percent']}%")
            print(f"  RAM free:  {latest['ram_available_mb']:.0f} MB")
            print(f"  RAM used:  {latest['ram_used_percent']}%")
        else:
            print("\nNo metrics yet — run the collector first.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()