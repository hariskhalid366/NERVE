"""HTTP client for NERVE Cloud, used by the model-agnostic MCP stdio bridge."""
from __future__ import annotations
import json
import os
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


class NerveCloudClient:
    def __init__(self, url: str | None = None, token: str | None = None):
        self.url = (url or os.getenv("NERVE_CLOUD_URL", "")).rstrip("/")
        self.token = token or os.getenv("NERVE_AGENT_TOKEN", "")
        parsed = urlsplit(self.url)
        local = parsed.hostname in ("localhost", "127.0.0.1", "::1")
        if parsed.scheme != "https" and not (parsed.scheme == "http" and local):
            raise ValueError("NERVE_CLOUD_URL must use HTTPS (HTTP allowed only on localhost)")
        if not parsed.netloc or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in ("", "/"):
            raise ValueError("NERVE_CLOUD_URL must be an HTTPS origin without path, query or credentials")
        if len(self.token) < 32:
            raise ValueError("NERVE_AGENT_TOKEN is required and must contain at least 32 characters")

    def post(self, path: str, data: dict) -> dict:
        if path not in ("/v1/resolve", "/v1/context", "/v1/recent", "/v1/remember"):
            raise ValueError("Unsupported agent endpoint")
        request = Request(self.url + path, data=json.dumps(data).encode("utf-8"),
                          headers={"Authorization": "Bearer " + self.token,
                                   "Content-Type": "application/json", "Accept": "application/json"},
                          method="POST")
        try:
            with urlopen(request, timeout=12) as response:
                return json.load(response)
        except HTTPError as exc:
            raise RuntimeError(f"NERVE Cloud HTTP {exc.code}: request failed") from None
        except URLError:
            raise RuntimeError("Cannot reach NERVE Cloud") from None
