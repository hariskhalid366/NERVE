"""Cloud REST gateway for one explicitly configured NERVE project.

Two distinct capabilities: AI agents read evidence and write *notes*; authorized
observers submit structured telemetry but cannot read existing data. This API
intentionally provides NO remote filesystem scan or arbitrary code execution.

Prototype: single tenant per deployment, single replica and durable SQLite disk.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import secrets
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from .collector import MAX_REQUEST_BYTES
from .core import Nerve

app = FastAPI(title="NERVE Cloud", version="0.5.0", docs_url=None, redoc_url=None, openapi_url=None)


def _keys() -> tuple[str, str]:
    agent = os.getenv("NERVE_AGENT_TOKEN", "")
    observer = os.getenv("NERVE_OBSERVER_TOKEN", "")
    if min(len(agent), len(observer)) < 32 or secrets.compare_digest(agent, observer):
        raise HTTPException(status_code=503, detail="Service credentials are not configured securely")
    return agent, observer


def _auth(request: Request, role: str) -> None:
    agent, observer = _keys()
    required = agent if role == "agent" else observer
    supplied = request.headers.get("authorization", "")
    # Require precise bearer format and compare constant-time.
    if not secrets.compare_digest(supplied, "Bearer " + required):
        raise HTTPException(status_code=401, detail="Unauthorized")


def _project_dir() -> Path:
    base = Path(os.getenv("NERVE_DATA_DIR", ".nerve-cloud-data")).expanduser().resolve()
    root = base / "project"
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    return root


async def _body(request: Request, allowed: set[str]) -> dict[str, Any]:
    if request.headers.get("content-type", "").split(";")[0].strip().lower() != "application/json":
        raise HTTPException(status_code=415, detail="Expected application/json")
    data = bytearray()
    async for chunk in request.stream():
        data.extend(chunk)
        if len(data) > MAX_REQUEST_BYTES:
            raise HTTPException(status_code=413, detail="Request exceeds 32 KiB")
    try:
        obj = json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise HTTPException(status_code=400, detail="Invalid JSON") from None
    if not isinstance(obj, dict):
        raise HTTPException(status_code=400, detail="JSON object required")
    unexpected = set(obj) - allowed
    if unexpected:
        raise HTTPException(status_code=400, detail="Unsupported fields: " + ", ".join(sorted(unexpected)[:5]))
    return obj


def _execute(handler):
    try:
        with Nerve(_project_dir()) as db:
            return handler(db)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)[:200]) from None


@app.middleware("http")
async def no_store(request: Request, call_next):
    try:
        response = await call_next(request)
    except Exception:
        raise
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.get("/healthz", include_in_schema=False)
def health():
    return {"status": "ok"}


@app.post("/v1/resolve")
async def resolve(request: Request):
    _auth(request, "agent")
    b = await _body(request, {"query", "limit"})
    if not isinstance(b.get("query"), str) or not b["query"].strip():
        raise HTTPException(status_code=400, detail="query must be a nonempty string")
    if len(b["query"]) > 1000:
        raise HTTPException(status_code=400, detail="query is too long")
    limit = b.get("limit", 5)
    if type(limit) is not int or not 1 <= limit <= 20:
        raise HTTPException(status_code=400, detail="limit must be 1..20")
    return _execute(lambda n: n.resolve(b["query"], limit))


@app.post("/v1/context")
async def context(request: Request):
    _auth(request, "agent")
    b = await _body(request, {"target_id", "limit"})
    if not isinstance(b.get("target_id"), str) or not 1 <= len(b["target_id"]) <= 250:
        raise HTTPException(status_code=400, detail="target_id must be a string of length 1..250")
    limit = b.get("limit", 12)
    if type(limit) is not int or not 1 <= limit <= 50:
        raise HTTPException(status_code=400, detail="limit must be 1..50")
    return _execute(lambda n: n.context(b["target_id"], limit=limit))


@app.post("/v1/recent")
async def recent(request: Request):
    _auth(request, "agent")
    b = await _body(request, {"limit"})
    limit = b.get("limit", 20)
    if type(limit) is not int or not 1 <= limit <= 50:
        raise HTTPException(status_code=400, detail="limit must be 1..50")
    return _execute(lambda n: n.recent(limit))


@app.post("/v1/remember")
async def remember(request: Request):
    _auth(request, "agent")
    b = await _body(request, {"text", "target_id", "category"})
    if not isinstance(b.get("text"), str) or not b["text"].strip():
        raise HTTPException(status_code=400, detail="text must be a nonempty string")
    return _execute(lambda n: {
        "memory_id": n.remember(b["text"], b.get("target_id", "project"), b.get("category", "note"), author="remote-agent")
    })


@app.post("/v1/observe")
async def observe(request: Request):
    _auth(request, "observer")
    b = await _body(request, {"target_id", "label", "kind", "description", "aliases", "source_path", "locator", "state"})
    if not isinstance(b.get("target_id"), str) or not isinstance(b.get("label"), str):
        raise HTTPException(status_code=400, detail="target_id and label must be strings")
    return _execute(lambda n: n.observe(**b, origin="remote-observer"))


@app.post("/v1/event")
async def event(request: Request):
    _auth(request, "observer")
    b = await _body(request, {"target_id", "event_type", "message", "payload"})
    if not all(isinstance(b.get(k), str) for k in ("target_id", "event_type", "message")):
        raise HTTPException(status_code=400, detail="target_id, event_type and message must be strings")
    return _execute(lambda n: {"event_id": n.event(**b)})
