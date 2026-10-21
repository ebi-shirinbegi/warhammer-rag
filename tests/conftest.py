"""Keep tests independent of the developer's credentials and local paths."""

import pytest


@pytest.fixture(autouse=True)
def isolate_settings(monkeypatch, tmp_path):
    for key in (
        "GOOGLE_API_KEY",
        "GOOGLE_MODEL",
        "GOOGLE_REQUESTS_PER_MINUTE",
        "RAG_PROJECT_ROOT",
        "RAG_RAW_DIR",
        "RAG_PROCESSED_DIR",
        "RAG_INDEX_DIR",
        "RAG_EVAL_DIR",
        "RAG_REPORT_DIR",
    ):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.chdir(tmp_path)


@pytest.fixture(autouse=True)
def isolate_api_throttle(monkeypatch):
    monkeypatch.setattr("warhammer_rag.chat.service.wait_for_slot", lambda *args: None)
    monkeypatch.setattr("warhammer_rag.chat.gemini.wait_for_slot", lambda *args: None)
