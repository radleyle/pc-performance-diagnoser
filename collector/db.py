"""
Database helpers for PC Performance Diagnoser.

This module:
  - picks a cross-platform path for data.db
  - creates tables if they don't exist yet
  - provides small functions to insert and read rows
"""

import os
import sqlite3
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Where does the database file live?
# ---------------------------------------------------------------------------

def get_db_path() -> Path:
    """
    Return the full path to data.db, creating the parent folder if needed.

    Windows:  %LOCALAPPDATA%/PCDiagnoser/data.db
    macOS:    ~/Library/Application Support/PCDiagnoser/data.db
    Linux:    ~/.local/share/PCDiagnoser/data.db
    """
    if sys.platform == "win32":
        base = Path(os.environ["LOCALAPPDATA"])
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path.home() / ".local" / "share"

    db_dir = base / "PCDiagnoser"
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir / "data.db"


# ---------------------------------------------------------------------------
# Connection + schema
# ---------------------------------------------------------------------------

def get_connection() -> sqlite3.Connection:
    """
    Open (or create) the SQLite file and return a connection.

    row_factory = sqlite3.Row lets us access columns by name:
      row["cpu_percent"] instead of row[1]
    """
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """
    Create all tables if they don't exist yet.
    Safe to call every time the collector starts.
    """
    conn = get_connection()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS metrics (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp        INTEGER NOT NULL,
                cpu_percent      REAL NOT NULL,
                ram_available_mb REAL NOT NULL,
                ram_used_percent REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS process_snapshots (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp     INTEGER NOT NULL,
                process_name  TEXT NOT NULL,
                memory_mb     REAL NOT NULL,
                cpu_percent   REAL
            );

            CREATE TABLE IF NOT EXISTS diagnoses (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp       INTEGER NOT NULL,
                issues          TEXT NOT NULL,
                ai_explanation  TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_metrics_timestamp
                ON metrics (timestamp);

            CREATE INDEX IF NOT EXISTS idx_process_snapshots_timestamp
                ON process_snapshots (timestamp);
        """)
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Write helpers (collector will use these in Step 4)
# ---------------------------------------------------------------------------

def insert_metric(
    timestamp: int,
    cpu_percent: float,
    ram_available_mb: float,
    ram_used_percent: float,
) -> None:
    """Insert one system metrics row."""
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO metrics (timestamp, cpu_percent, ram_available_mb, ram_used_percent)
            VALUES (?, ?, ?, ?)
            """,
            (timestamp, cpu_percent, ram_available_mb, ram_used_percent),
        )
        conn.commit()
    finally:
        conn.close()


def insert_process_snapshot(
    timestamp: int,
    process_name: str,
    memory_mb: float,
    cpu_percent: float | None = None,
) -> None:
    """Insert one process snapshot row."""
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO process_snapshots (timestamp, process_name, memory_mb, cpu_percent)
            VALUES (?, ?, ?, ?)
            """,
            (timestamp, process_name, memory_mb, cpu_percent),
        )
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Read helpers (useful for testing and later for the API)
# ---------------------------------------------------------------------------

def count_rows(table: str) -> int:
    """Return how many rows are in a table (for quick checks)."""
    allowed = {"metrics", "process_snapshots", "diagnoses"}
    if table not in allowed:
        raise ValueError(f"Unknown table: {table}")

    conn = get_connection()
    try:
        row = conn.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()
        return int(row["n"])
    finally:
        conn.close()


def get_recent_metrics(limit: int = 5) -> list[sqlite3.Row]:
    """Return the most recent metrics rows, newest first."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT * FROM metrics
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return list(rows)
    finally:
        conn.close()