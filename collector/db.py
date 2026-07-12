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
import time
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


def _add_disk_columns_if_missing(conn: sqlite3.Connection) -> None:
    """Add disk columns to existing databases created before Step 5."""
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(metrics)")}
    if "disk_free_gb" not in columns:
        conn.execute("ALTER TABLE metrics ADD COLUMN disk_free_gb REAL")
    if "disk_used_percent" not in columns:
        conn.execute("ALTER TABLE metrics ADD COLUMN disk_used_percent REAL")


def init_db() -> None:
    """
    Create all tables if they don't exist yet.
    Safe to call every time the collector starts.
    """
    conn = get_connection()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS metrics (
                id                 INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp          INTEGER NOT NULL,
                cpu_percent        REAL NOT NULL,
                ram_available_mb   REAL NOT NULL,
                ram_used_percent   REAL NOT NULL,
                disk_free_gb       REAL,
                disk_used_percent  REAL
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
        _add_disk_columns_if_missing(conn)
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
    disk_free_gb: float,
    disk_used_percent: float,
) -> None:
    """Insert one system metrics row."""
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO metrics (
                timestamp, cpu_percent, ram_available_mb, ram_used_percent,
                disk_free_gb, disk_used_percent
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                timestamp,
                cpu_percent,
                ram_available_mb,
                ram_used_percent,
                disk_free_gb,
                disk_used_percent,
            ),
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
        
def get_metrics_since(minutes: int = 60) -> list[sqlite3.Row]:
    """Return metrics rows from the last N minutes, oldest first."""
    cutoff_ms = int(time.time() * 1000) - (minutes * 60 * 1000)

    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT * FROM metrics
            WHERE timestamp >= ?
            ORDER BY timestamp ASC
            """,
            (cutoff_ms,),
        ).fetchall()
        return list(rows)
    finally:
        conn.close()


def get_latest_process_snapshots() -> list[sqlite3.Row]:
    """Return process rows from the most recent snapshot timestamp."""
    conn = get_connection()
    try:
        latest = conn.execute(
            "SELECT MAX(timestamp) AS ts FROM process_snapshots"
        ).fetchone()

        if latest is None or latest["ts"] is None:
            return []

        rows = conn.execute(
            """
            SELECT * FROM process_snapshots
            WHERE timestamp = ?
            ORDER BY memory_mb DESC
            """,
            (latest["ts"],),
        ).fetchall()
        return list(rows)
    finally:
        conn.close()
        
def insert_diagnosis(
    timestamp: int,
    issues_json: str,
    ai_explanation: str | None = None,
) -> None:
    """Save one diagnosis result to history."""
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO diagnoses (timestamp, issues, ai_explanation)
            VALUES (?, ?, ?)
            """,
            (timestamp, issues_json, ai_explanation),
        )
        conn.commit()
    finally:
        conn.close()
        
def get_latest_metric_timestamp() -> int | None:
    """Return the timestamp (ms) of the most recent metrics row, or None."""
    conn = get_connection()
    try:
        row = conn.execute("SELECT MAX(timestamp) AS ts FROM metrics").fetchone()
        if row is None or row["ts"] is None:
            return None
        return int(row["ts"])
    finally:
        conn.close()
        
def get_recent_diagnoses(limit: int = 20) -> list[sqlite3.Row]:
    """Return the most recent diagnosis rows, newest first."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT id, timestamp, issues, ai_explanation
            FROM diagnoses
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return list(rows)
    finally:
        conn.close()