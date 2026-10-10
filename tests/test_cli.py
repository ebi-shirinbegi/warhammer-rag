import sqlite3

from warhammer_rag.cli import main


def prepare_inputs(tmp_path, monkeypatch):
    raw = tmp_path / "data/raw"
    raw.mkdir(parents=True)
    (raw / "core_rules.pdf").write_bytes(b"%PDF-1.4\n")
    with sqlite3.connect(raw / "wahadb.sqlite") as connection:
        connection.execute("CREATE TABLE units (id TEXT)")
    monkeypatch.setenv("RAG_PROJECT_ROOT", str(tmp_path))


def test_doctor_allows_offline_work_but_strict_check_requires_key(tmp_path, monkeypatch):
    prepare_inputs(tmp_path, monkeypatch)
    assert main(["doctor"]) == 0
    assert main(["doctor", "--require-api-key"]) == 1


def test_doctor_never_prints_key(tmp_path, monkeypatch, capsys):
    prepare_inputs(tmp_path, monkeypatch)
    monkeypatch.setenv("GOOGLE_API_KEY", "private-test-key")
    assert main(["doctor", "--require-api-key"]) == 0
    captured = capsys.readouterr()
    assert "private-test-key" not in captured.out + captured.err
    assert "No API call was made" in captured.out


def test_doctor_fails_for_missing_inputs(tmp_path, monkeypatch):
    monkeypatch.setenv("RAG_PROJECT_ROOT", str(tmp_path))
    assert main(["doctor"]) == 1


def test_doctor_fails_for_invalid_sqlite(tmp_path, monkeypatch):
    prepare_inputs(tmp_path, monkeypatch)
    (tmp_path / "data/raw/wahadb.sqlite").write_bytes(b"not a database")
    assert main(["doctor"]) == 1
