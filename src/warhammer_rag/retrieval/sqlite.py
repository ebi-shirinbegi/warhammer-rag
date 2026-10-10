"""Read-only access to the supplied SQLite snapshot.

This is a connection utility, not yet an LLM SQL tool. A future tool also needs
single-statement validation, result limits and an execution budget.
"""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


def _authorize(action: int, arg1: str | None, arg2: str | None, *_: object) -> int:
    # Read-only URI protects the main DB. These deny creation of attached DBs,
    # changing query_only, and invoking SQLite's extension-loading function.
    if action in (sqlite3.SQLITE_ATTACH, sqlite3.SQLITE_DETACH, sqlite3.SQLITE_PRAGMA):
        return sqlite3.SQLITE_DENY
    if action == sqlite3.SQLITE_FUNCTION and arg2 == "load_extension":
        return sqlite3.SQLITE_DENY
    return sqlite3.SQLITE_OK


@contextmanager
def readonly_connection(path: Path) -> Iterator[sqlite3.Connection]:
    """Open an existing DB without creating files; always close the connection."""
    path = path.expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Database file does not exist: {path}")
    connection = sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True, timeout=5)
    try:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only = ON")
        connection.set_authorizer(_authorize)
        yield connection
    finally:
        connection.close()
