"""Opt-in, loopback-only observation collector.

Runtime adapters can POST machine-readable observations without screenshots.
The collector accepts *data*, never commands or code execution.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from .core import Nerve

MAX_REQUEST_BYTES = 32_768


def collector_token(project: str | Path) -> str:
    """Read or generate a project-unique bearer token, never expose via MCP."""
    with Nerve(project) as nerve:
        f = nerve.db_path.parent / "collector-token"
        if f.is_symlink():
            raise ValueError("Refusing symlinked collector credential")
        if not f.exists():
            flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
            fd = os.open(f, flags, 0o600)
            with os.fdopen(fd, "w") as out:
                out.write(secrets.token_urlsafe(36))
        try:
            os.chmod(f, 0o600)
        except OSError:
            pass  # Windows: inherited local file permissions apply.
        return f.read_text(encoding="utf-8").strip()


def create_server(project: str | Path, port: int = 8765) -> ThreadingHTTPServer:
    root = Path(project).expanduser().resolve(strict=True)
    token = collector_token(root)

    class Handler(BaseHTTPRequestHandler):
        def _reply(self, code: int, data: dict):
            raw = json.dumps(data).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_POST(self):
            # Require capability token; browser simple CSRF cannot send it without CORS.
            if not secrets.compare_digest(self.headers.get("Authorization", ""), "Bearer " + token):
                return self._reply(401, {"error": "unauthorized"})
            if self.path not in ("/v1/observe", "/v1/event"):
                return self._reply(404, {"error": "unknown endpoint"})
            if self.headers.get("Content-Type", "").split(";")[0].strip() != "application/json":
                return self._reply(415, {"error": "Content-Type must be application/json"})
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if size < 2 or size > MAX_REQUEST_BYTES:
                    return self._reply(413, {"error": "invalid payload length"})
                data = json.loads(self.rfile.read(size))
                if not isinstance(data, dict):
                    raise ValueError("JSON payload must be an object")
                with Nerve(root) as nerve:
                    if self.path == "/v1/observe":
                        result = nerve.observe(**data)
                    else:
                        result = {"event_id": nerve.event(**data)}
                return self._reply(200, result)
            except (ValueError, TypeError, json.JSONDecodeError) as e:
                return self._reply(400, {"error": str(e)[:200]})
            except Exception:
                # Never leak filesystem paths or raw database errors.
                return self._reply(500, {"error": "collector internal error"})

        def log_message(self, format, *args):
            # Do not accidentally log client payload or auth headers.
            return

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.daemon_threads = True
    return server


def listen(project: str, port: int = 8765) -> None:
    srv = create_server(project, port)
    print(f"NERVE receiver on http://127.0.0.1:{srv.server_port} (Ctrl+C to stop)")
    print("This receives observations only; nothing is captured without an adapter.")
    try:
        srv.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
