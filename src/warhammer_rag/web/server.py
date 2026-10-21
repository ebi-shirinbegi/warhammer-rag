"""Loopback-only HTTP interface. Credentials never leave the Python backend."""

import errno
import hashlib
import http.client
import json
import secrets
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from google.genai.errors import APIError
from pydantic import ValidationError

from warhammer_rag.chat.history import Conversation, ConversationStore
from warhammer_rag.chat.service import ChatService, Question
from warhammer_rag.config import Settings

ASSETS = Path(__file__).parent
APP_ID = "warhammer-rag-chat"


def refresh_api_settings(settings: Settings) -> Settings:
    """Reload API credentials without changing the server's data paths."""
    current = Settings(_env_file=settings.project_root / ".env")
    return settings.model_copy(
        update={
            "google_api_key": current.google_api_key,
            "google_model": current.google_model,
            "google_requests_per_minute": current.google_requests_per_minute,
        }
    )


def workspace_id(settings: Settings) -> str:
    return hashlib.sha256(str(settings.project_root).encode()).hexdigest()


def existing_instance(settings: Settings, port: int) -> bool:
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
    try:
        connection.request("GET", "/api/status")
        response = connection.getresponse()
        if response.status != 200:
            return False
        status = json.loads(response.read(8192))
        return (
            isinstance(status, dict)
            and status.get("app") == APP_ID
            and status.get("workspace") == workspace_id(settings)
        )
    except (OSError, ValueError, http.client.HTTPException):
        return False
    finally:
        connection.close()


def open_browser(url: str) -> None:
    try:
        opened = webbrowser.open(url, new=2)
    except webbrowser.Error:
        opened = False
    if not opened:
        print(f"Could not open a browser automatically. Open {url} manually.", flush=True)


def create_server(settings: Settings, port: int = 8000, service=None) -> ThreadingHTTPServer:
    backend = service or ChatService(settings)
    token = secrets.token_urlsafe(32)
    busy = threading.Lock()
    store = ConversationStore(settings.project_root / "data/local/conversations.sqlite")

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def send(self, status, content, mime="application/json"):
            body = json.dumps(content).encode() if mime == "application/json" else content
            self.send_response(status)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "same-origin")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; style-src 'self'; script-src 'self'; "
                "object-src 'none'; frame-ancestors 'none'",
            )
            self.end_headers()
            self.wfile.write(body)

        def valid_host(self):
            port = self.server.server_port
            return self.headers.get("Host") in {f"127.0.0.1:{port}", f"localhost:{port}"}

        def do_GET(self):
            if not self.valid_host():
                return self.send(403, {"error": "Invalid host"})
            if self.path == "/api/status":
                return self.send(
                    200,
                    {
                        "app": APP_ID,
                        "workspace": workspace_id(settings),
                        "configured": settings.has_api_key and bool(settings.google_model),
                        "indexed": (settings.index_dir / "rules.sqlite").is_file(),
                        "token": token,
                    },
                )
            if self.path == "/api/conversations":
                return self.send(200, store.list())
            if self.path.startswith("/api/conversations/"):
                record = store.get(self.path.rsplit("/", 1)[-1])
                return (
                    self.send(200, record)
                    if record
                    else self.send(404, {"error": "Conversation not found"})
                )
            assets = {
                "/crest.svg": ("crest.svg", "image/svg+xml"),
                "/": ("index.html", "text/html; charset=utf-8"),
                "/style.css": ("style.css", "text/css; charset=utf-8"),
                "/app.js": ("app.js", "text/javascript; charset=utf-8"),
            }
            if self.path in assets:
                name, mime = assets[self.path]
                return self.send(200, (ASSETS / name).read_bytes(), mime)
            if self.path == "/sources/core-rules.pdf":
                return self.send(200, settings.rulebook_path.read_bytes(), "application/pdf")
            self.send(404, {"error": "Not found"})

        def do_POST(self):
            if not self.valid_host() or self.headers.get("X-Chat-Token") != token:
                return self.send(403, {"error": "Reload the page before sending a message."})
            if self.path == "/api/conversations":
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    if not 0 < length <= 4_000_000:
                        return self.send(413, {"error": "Conversation is too large to save."})
                    conversation = Conversation.model_validate_json(self.rfile.read(length))
                    store.save(conversation)
                    return self.send(200, {"id": conversation.id})
                except (ValueError, ValidationError):
                    return self.send(400, {"error": "Invalid conversation."})
                except Exception:
                    return self.send(500, {"error": "Could not save the conversation locally."})
            if self.path.startswith("/api/conversations/delete/"):
                store.delete(self.path.rsplit("/", 1)[-1])
                return self.send(200, {"deleted": True})
            if self.path != "/api/ask":
                return self.send(404, {"error": "Not found"})
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 80000:
                    return self.send(413, {"error": "Message is too large."})
                request = Question.model_validate_json(self.rfile.read(length))
                if not request.question.strip():
                    return self.send(400, {"error": "Enter a question."})
            except (ValueError, ValidationError):
                return self.send(400, {"error": "Invalid question or conversation history."})
            if not busy.acquire(blocking=False):
                return self.send(
                    429, {"error": "Another answer is in progress. Try again shortly."}
                )
            try:
                if service is None:
                    backend.settings = refresh_api_settings(settings)
                self.send(200, backend.ask(request))
            except APIError as exc:
                message = (
                    "Google returned a rate or quota limit (429). Your conversation is saved. "
                    "Try later or check this project’s limits in Google AI Studio."
                    if exc.code == 429
                    else (
                        f"Google could not complete the request (HTTP {exc.code}) after "
                        "three attempts. This is a timeout or service failure, not a quota "
                        "error. Your question is saved; please try again shortly."
                    )
                    if exc.code in {408, 500, 502, 503, 504}
                    else f"Gemini request failed (HTTP {exc.code}). Check API configuration."
                )
                self.send(502, {"error": message})
            except Exception:
                # SDK and transport exceptions may contain request credentials.
                self.send(
                    502,
                    {
                        "error": "The answer could not be completed. Check API configuration "
                        "and rebuild the index if needed, then retry."
                    },
                )
            finally:
                busy.release()

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def serve(settings: Settings, port: int = 8000, *, launch_browser: bool = True) -> int:
    if not 0 <= port <= 65535:
        print("Port must be between 0 and 65535.")
        return 1
    try:
        server = create_server(settings, port)
    except OSError as exc:
        if exc.errno == errno.EADDRINUSE:
            url = f"http://127.0.0.1:{port}"
            if existing_instance(settings, port):
                print(f"Warhammer archive is already running: {url}", flush=True)
                if launch_browser:
                    open_browser(url)
                return 0
            print(
                f"Port {port} is used by another service or an older app instance. "
                "Use --port 8001, or stop that instance first."
            )
        else:
            print(f"Could not start the local server on port {port} (OS error {exc.errno}).")
        return 1
    with server:
        url = f"http://127.0.0.1:{server.server_port}"
        print(f"Warhammer archive: {url}", flush=True)
        print("Press Ctrl+C to stop.", flush=True)
        if launch_browser:
            open_browser(url)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
    return 0
