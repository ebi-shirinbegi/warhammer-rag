"""Keep tests independent of the developer's credentials and local paths."""

import pytest


@pytest.fixture(autouse=True)
def isolate_settings(monkeypatch, tmp_path):
    for key in (
        "GOOGLE_API_KEY",
        "GOOGLE_MODEL",
        "RAG_PROJECT_ROOT",
        "RAG_RAW_DIR",
        "RAG_PROCESSED_DIR",
        "RAG_INDEX_DIR",
        "RAG_EVAL_DIR",
        "RAG_REPORT_DIR",
    ):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.chdir(tmp_path)
