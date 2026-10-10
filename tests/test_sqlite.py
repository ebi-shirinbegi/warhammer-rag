import sqlite3

import pytest

from warhammer_rag.retrieval.sqlite import readonly_connection


@pytest.fixture
def database(tmp_path):
    path = tmp_path / "units ? #.sqlite"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE units (id TEXT, toughness TEXT)")
        connection.execute("INSERT INTO units VALUES ('000001', '4')")
    return path


def test_select_preserves_exact_ids_and_handles_uri_characters(database):
    with readonly_connection(database) as connection:
        row = connection.execute(
            "SELECT id, toughness FROM units WHERE id = ?", ("000001",)
        ).fetchone()
        assert dict(row) == {"id": "000001", "toughness": "4"}
    with pytest.raises(sqlite3.ProgrammingError):
        connection.execute("SELECT 1")


@pytest.mark.parametrize(
    "query",
    [
        "UPDATE units SET toughness = '99'",
        "CREATE TABLE corrupted (id TEXT)",
        "PRAGMA query_only = OFF",
    ],
)
def test_writes_and_changing_protection_are_denied(database, query):
    original = database.read_bytes()
    with readonly_connection(database) as connection, pytest.raises(sqlite3.DatabaseError):
        connection.execute(query)
    assert database.read_bytes() == original


def test_attaching_another_database_is_denied(database, tmp_path):
    extra = tmp_path / "extra.sqlite"
    with readonly_connection(database) as connection, pytest.raises(sqlite3.DatabaseError):
        connection.execute("ATTACH DATABASE ? AS extra", (str(extra),))
    assert not extra.exists()


def test_missing_database_is_not_created(tmp_path):
    missing = tmp_path / "missing.sqlite"
    with pytest.raises(FileNotFoundError), readonly_connection(missing):
        pass
    assert not missing.exists()
