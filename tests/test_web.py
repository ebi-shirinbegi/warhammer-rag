import io
import json
from types import SimpleNamespace
from unittest.mock import Mock

from warhammer_rag.config import Settings
from warhammer_rag.web.server import create_server


def test_api_settings_reload_after_dotenv_changes(monkeypatch, tmp_path):
    from warhammer_rag.web.server import refresh_api_settings

    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_MODEL", raising=False)
    settings = Settings(
        _env_file=None, project_root=tmp_path, google_api_key="old", google_model="old-model"
    )
    env = tmp_path / ".env"
    env.write_text("GOOGLE_API_KEY=new-key\nGOOGLE_MODEL=new-model\nRAG_RAW_DIR=elsewhere\n")
    updated = refresh_api_settings(settings)
    assert updated.google_api_key.get_secret_value() == "new-key"
    assert updated.google_model == "new-model"
    assert updated.raw_dir == settings.raw_dir
    env.write_text("GOOGLE_API_KEY=another-key\nGOOGLE_MODEL=another-model\n")
    assert refresh_api_settings(settings).google_api_key.get_secret_value() == "another-key"


def client(monkeypatch, backend=None):
    state = {}

    def server(address, handler):
        state["handler"] = handler
        return SimpleNamespace(server_port=8000)

    monkeypatch.setattr("warhammer_rag.web.server.ThreadingHTTPServer", server)
    instance = create_server(Settings(_env_file=None), service=backend or Mock())

    def request(method="GET", path="/api/status", headers=None, body=b""):
        lines = [
            f"{method} {path} HTTP/1.1",
            "Host: 127.0.0.1:8000",
            f"Content-Length: {len(body)}",
        ]
        lines.extend(f"{k}: {v}" for k, v in (headers or {}).items())
        raw = ("\r\n".join(lines) + "\r\n\r\n").encode() + body
        socket = Mock()
        socket.makefile.return_value = io.BytesIO(raw)
        state["handler"](socket, ("127.0.0.1", 1234), instance)
        response = b"".join(call.args[0] for call in socket.sendall.call_args_list)
        head, data = response.split(b"\r\n\r\n", 1)
        return head.decode(), data

    return request


def test_only_fixed_assets_are_served(monkeypatch):
    request = client(monkeypatch)
    head, body = request(path="/")
    assert "200" in head and b"IMPERIAL" in body
    assert "Content-Security-Policy" in head
    for path in ("/.env", "/../.env", "/src/warhammer_rag/config.py"):
        assert "404" in request(path=path)[0]


def test_chat_requires_token_and_valid_body(monkeypatch):
    backend = Mock()
    request = client(monkeypatch, backend)
    token = json.loads(request()[1])["token"]
    assert "403" in request("POST", "/api/ask", body=b"{}")[0]
    assert "400" in request("POST", "/api/ask", {"X-Chat-Token": token}, b"{}")[0]
    backend.ask.assert_not_called()


def test_response_and_errors_never_expose_exception_secrets(monkeypatch):
    backend = Mock()
    backend.ask.side_effect = RuntimeError("secret-api-key")
    request = client(monkeypatch, backend)
    token = json.loads(request()[1])["token"]
    head, data = request("POST", "/api/ask", {"X-Chat-Token": token}, b'{"question":"grenades"}')
    assert "502" in head
    assert b"secret-api-key" not in data
    backend.ask.side_effect = None
    backend.ask.return_value = {"status": "answer", "paragraphs": [], "sources": []}
    assert (
        "200" in request("POST", "/api/ask", {"X-Chat-Token": token}, b'{"question":"grenades"}')[0]
    )


def test_occupied_app_port_opens_existing_instance(monkeypatch, capsys):
    import errno

    from warhammer_rag.web.server import serve

    monkeypatch.setattr(
        "warhammer_rag.web.server.create_server",
        Mock(side_effect=OSError(errno.EADDRINUSE, "busy")),
    )
    monkeypatch.setattr("warhammer_rag.web.server.existing_instance", lambda *_: True)
    browser = Mock()
    monkeypatch.setattr("warhammer_rag.web.server.open_browser", browser)
    assert serve(Settings(_env_file=None)) == 0
    browser.assert_called_once_with("http://127.0.0.1:8000")
    assert "already running" in capsys.readouterr().out


def test_unrelated_occupied_port_does_not_open_browser(monkeypatch, capsys):
    import errno

    from warhammer_rag.web.server import serve

    monkeypatch.setattr(
        "warhammer_rag.web.server.create_server",
        Mock(side_effect=OSError(errno.EADDRINUSE, "busy")),
    )
    monkeypatch.setattr("warhammer_rag.web.server.existing_instance", lambda *_: False)
    browser = Mock()
    monkeypatch.setattr("warhammer_rag.web.server.open_browser", browser)
    assert serve(Settings(_env_file=None)) == 1
    browser.assert_not_called()
    assert "--port" in capsys.readouterr().out


def test_new_server_can_suppress_browser_launch(monkeypatch):
    from unittest.mock import MagicMock

    from warhammer_rag.web.server import serve

    server = MagicMock(server_port=8123)
    server.serve_forever.side_effect = KeyboardInterrupt
    monkeypatch.setattr("warhammer_rag.web.server.create_server", lambda *_: server)
    browser = Mock()
    monkeypatch.setattr("warhammer_rag.web.server.open_browser", browser)
    assert serve(Settings(_env_file=None), 8123, launch_browser=False) == 0
    browser.assert_not_called()
    assert serve(Settings(_env_file=None), 8123) == 0
    browser.assert_called_once_with("http://127.0.0.1:8123")


def test_existing_server_must_identify_the_same_workspace(monkeypatch):
    from warhammer_rag.web.server import APP_ID, existing_instance, workspace_id

    settings = Settings(_env_file=None)
    connection = Mock()
    connection.getresponse.return_value.status = 200
    monkeypatch.setattr(
        "warhammer_rag.web.server.http.client.HTTPConnection", lambda *a, **k: connection
    )
    for payload, expected in [
        ({"app": APP_ID, "workspace": workspace_id(settings)}, True),
        ({"app": APP_ID, "workspace": "different"}, False),
        ({"app": "other"}, False),
        ([], False),
    ]:
        connection.getresponse.return_value.read.return_value = json.dumps(payload).encode()
        assert existing_instance(settings, 8000) is expected
    connection.close.assert_called()


def test_history_api_round_trip_and_delete(monkeypatch, tmp_path):
    monkeypatch.setenv("RAG_PROJECT_ROOT", str(tmp_path))
    request = client(monkeypatch)
    token = json.loads(request()[1])["token"]
    headers = {"X-Chat-Token": token}
    item = {"id": "b" * 32, "title": "Saved question", "messages": [], "draft": "Grenades?"}
    assert "403" in request("POST", "/api/conversations", body=json.dumps(item).encode())[0]
    assert "200" in request("POST", "/api/conversations", headers, json.dumps(item).encode())[0]
    assert json.loads(request(path="/api/conversations")[1])[0]["title"] == item["title"]
    assert json.loads(request(path=f"/api/conversations/{item['id']}")[1])["draft"] == "Grenades?"
    assert "200" in request("POST", f"/api/conversations/delete/{item['id']}", headers)[0]
    assert json.loads(request(path="/api/conversations")[1]) == []
