"""Offline configuration and source-data diagnostics."""

import argparse
import sqlite3
from collections.abc import Sequence

from pydantic import ValidationError

from warhammer_rag.config import Settings
from warhammer_rag.retrieval.sqlite import readonly_connection


def doctor(settings: Settings, *, require_api_key: bool = False) -> int:
    """Check local inputs; report credential presence without exposing it."""
    print(f"Project: {settings.project_root}")
    failures = 0
    for label, path in (("Rulebook", settings.rulebook_path), ("SQLite", settings.database_path)):
        exists = path.is_file()
        print(f"{'OK' if exists else 'MISSING'} {label}: {path}")
        failures += int(not exists)
    if settings.database_path.is_file():
        try:
            with readonly_connection(settings.database_path) as connection:
                count = connection.execute(
                    "SELECT COUNT(*) FROM sqlite_schema WHERE type = 'table'"
                ).fetchone()[0]
            print(f"OK read-only database connection ({count} tables)")
        except (OSError, sqlite3.Error):
            print("ERROR database could not be read as SQLite")
            failures += 1
    print(f"GOOGLE_API_KEY: {'configured' if settings.has_api_key else 'not configured'}")
    print(f"GOOGLE_MODEL: {'configured' if settings.google_model else 'not configured'}")
    if require_api_key and not settings.has_api_key:
        print("ERROR configure GOOGLE_API_KEY locally in .env")
        failures += 1
    print("No API call was made.")
    return int(failures > 0)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="warhammer-rag",
        description="Warhammer RAG command-line utilities.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser(
        "doctor", help="Check local inputs and configuration without API calls"
    )
    check.add_argument(
        "--require-api-key", action="store_true", help="Fail if GOOGLE_API_KEY is missing"
    )
    args = parser.parse_args(argv)
    try:
        settings = Settings()
    except ValidationError:
        # Do not print validation details, which may contain raw environment values.
        parser.exit(2, "Invalid configuration. Check the paths and values in .env.\n")
    return doctor(settings, require_api_key=args.require_api_key)
