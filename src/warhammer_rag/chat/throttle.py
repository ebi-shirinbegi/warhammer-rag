"""Coordinate Gemini call spacing across local chat and evaluation processes."""

import sqlite3
import time
from pathlib import Path


def wait_for_slot(path: Path, requests_per_minute: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=30)
    try:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS throttle (id INTEGER PRIMARY KEY, next REAL)"
        )
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute("SELECT next FROM throttle WHERE id=1").fetchone()
        now = time.time()
        slot = max(now, row[0] if row else now)
        connection.execute(
            "INSERT OR REPLACE INTO throttle VALUES (1, ?)",
            (slot + 60 / requests_per_minute,),
        )
        connection.commit()
    finally:
        connection.close()
    if slot > now:
        time.sleep(slot - now)
