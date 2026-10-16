from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from warhammer_rag.chat.gemini import check_connection
from warhammer_rag.cli import main
from warhammer_rag.config import Settings


def test_connection_requires_model_and_key():
    with pytest.raises(ValueError, match="Configure"):
        check_connection(Settings(_env_file=None))


@pytest.mark.parametrize("text,expected", [("OK", True), (None, False), ("unexpected", False)])
def test_connection_checks_response_without_live_requests(monkeypatch, text, expected):
    client = MagicMock()
    client.models.generate_content.return_value = SimpleNamespace(text=text)
    factory = MagicMock()
    factory.return_value.__enter__.return_value = client
    monkeypatch.setattr("warhammer_rag.chat.gemini.genai.Client", factory)
    settings = Settings(_env_file=None, google_api_key="test-secret", google_model="test-model")
    assert check_connection(settings) is expected
    assert client.models.generate_content.call_args.kwargs["model"] == "test-model"
    factory.return_value.__exit__.assert_called_once()


def test_api_diagnostics_do_not_leak_transport_details(monkeypatch, capsys):
    def fail(_):
        raise RuntimeError("https://example.com?key=private-test-key")

    monkeypatch.setattr("warhammer_rag.chat.gemini.check_connection", fail)
    assert main(["check-api"]) == 1
    output = capsys.readouterr()
    assert "private-test-key" not in output.out + output.err
    assert "connection failed" in output.out
