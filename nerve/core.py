"""Local database, source index and evidence-based target resolution.

NERVE is NOT a system-memory hook: the host must connect it and supply observations.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
import os
import re
import sqlite3
from typing import Any

MAX_TEXT = 3000
MAX_SCAN_FILES = 2500
MAX_FILE_SIZE = 250_000
SUPPORTED = {".py", ".js", ".mjs", ".cjs", ".jsx", ".ts", ".mts", ".cts", ".tsx", ".go", ".rs", ".vue", ".svelte", ".html", ".css", ".md"}
EXCLUDED_DIRS = {
    ".nerve", ".git", ".svn", "node_modules", "vendor", "dist", "build",
    "coverage", ".next", ".venv", "venv", "__pycache__", ".expo", ".idea",
    ".gradle", "Pods", ".cache", "target",
}
EXCLUDED_NAMES = {".env", ".env.local", ".env.production", ".env.development", ".npmrc", ".pypirc", "id_rsa", "id_ed25519"}
EXCLUDED_SUFFIXES = {".pem", ".key", ".p12", ".pfx", ".keystore", ".jks", ".mobileprovision", ".db", ".sqlite", ".sqlite3"}
SENSITIVE_KEY = re.compile(r"(^|[_\-.])(password|passwd|secret|token|authorization|cookie|api[_-]?key|private[_-]?key|credential|session[_-]?id)($|[_\-.])", re.I)
SENSITIVE_INLINE = re.compile(r"(?i)(\b(?:password|passwd|secret|token|api[_-]?key|authorization)\b\s*[:=]\s*)([^\s,;]+)")
TOKEN_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]{1,}")
# Retrieval stopwords remove accidental hits on short symbols (e.g. `to`, `pieces`).
# No language model is involved; these are plain heuristic signals.
QUERY_STOP = set("the a an and or of to for from at on in with by where what which why how who when did was were is are does do has have had this that those these its it my your our their not as get fix function file code project thing stuff new old after before while across through about into using uses used again more less same".split())

def retrieval_tokens(value: str) -> set[str]:
    expanded = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", value).replace("_", " ").replace("-", " ")
    return {t for t in tokens(expanded) if t not in QUERY_STOP and len(t) > 2}

SYMBOL = re.compile(
    r"^\s*(?:export\s+(?:default\s+)?)?(?:async\s+)?(?:function|class|interface|type|enum|def|struct)\s+([A-Za-z_][A-Za-z0-9_]*)\b|"
    r"^\s*(?:export\s+)?(?:const|let)\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:[:=])",
    re.M,
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def clean_text(value: object) -> str:
    txt = str(value)[:MAX_TEXT]
    return SENSITIVE_INLINE.sub(r"\1[REDACTED]", txt)


def redact(value: Any) -> Any:
    """Best-effort sanitization, not a guarantee against arbitrary secrets/PII."""
    if isinstance(value, dict):
        return {str(k)[:100]: "[REDACTED]" if SENSITIVE_KEY.search(str(k)) else redact(v)
                for k, v in list(value.items())[:80]}
    if isinstance(value, list):
        return [redact(x) for x in value[:50]]
    if isinstance(value, str):
        return clean_text(value)
    return value if value is None or isinstance(value, (int, float, bool)) else clean_text(value)


def tokens(text: str) -> set[str]:
    return {t.lower() for t in TOKEN_PATTERN.findall(text) if len(t) > 1}


def _allowed_relative_path(root: Path, rel: str) -> Path:
    if not rel or Path(rel).is_absolute() or '\\' in rel:
        raise ValueError("source_path must be relative to the project")
    candidate = (root / rel).resolve()
    if not candidate.is_relative_to(root):
        raise ValueError("source_path escapes the project")
    parts = Path(rel).parts
    if any(p in EXCLUDED_DIRS or p.startswith(".env") for p in parts) or candidate.suffix in EXCLUDED_SUFFIXES:
        raise ValueError("source_path is excluded from observation")
    return candidate


class Nerve:
    """Each instance is sandboxed to one explicitly selected project root."""

    def __init__(self, project_root: str | Path):
        self.root = Path(project_root).expanduser().resolve(strict=True)
        if not self.root.is_dir():
            raise ValueError("project_root must be a directory")
        self.db_path = self.root / ".nerve" / "memory.sqlite3"
        if self.db_path.parent.is_symlink() or self.db_path.is_symlink():
            raise ValueError("Refusing symlinked project memory path")
        self.db_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        if not self.db_path.parent.resolve().is_relative_to(self.root):
            raise ValueError("Memory directory escapes selected project")
        self.conn = sqlite3.connect(self.db_path, timeout=10)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS targets (
                target_id TEXT PRIMARY KEY,
                label TEXT NOT NULL,
                kind TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                aliases TEXT NOT NULL DEFAULT '[]',
                source_path TEXT NOT NULL DEFAULT '',
                locator TEXT NOT NULL DEFAULT '',
                state TEXT NOT NULL DEFAULT '{}',
                origin TEXT NOT NULL DEFAULT 'manual',
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                message TEXT NOT NULL,
                payload TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS ix_events_target ON events(target_id, id DESC);
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_id TEXT NOT NULL,
                category TEXT NOT NULL,
                text TEXT NOT NULL,
                author TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS ix_memories_target ON memories(target_id, id DESC);
        """)
        # Upgrade pre-0.6 projects in place without dropping memories or events.
        for table in ("events", "memories"):
            cols = {row[1] for row in self.conn.execute(f"PRAGMA table_info({table})")}
            if "source_digest" not in cols:
                self.conn.execute(f"ALTER TABLE {table} ADD COLUMN source_digest TEXT NOT NULL DEFAULT ''")
        self.conn.commit()
        # Optional FTS5 indexes cover historical evidence across the *entire*
        # project rather than only the most recent 300 global writes.
        # SQLite builds without FTS5 use the slower full-history fallback.
        self._fts_ready = False
        try:
            has_event_index = self.conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='nerve_events_fts'").fetchone() is not None
            has_memory_index = self.conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='nerve_memories_fts'").fetchone() is not None
            self.conn.executescript("""
                CREATE VIRTUAL TABLE IF NOT EXISTS nerve_events_fts USING fts5(
                    message, target_id UNINDEXED, content='events', content_rowid='id');
                CREATE VIRTUAL TABLE IF NOT EXISTS nerve_memories_fts USING fts5(
                    text, target_id UNINDEXED, content='memories', content_rowid='id');
                CREATE TRIGGER IF NOT EXISTS nerve_events_fts_ins AFTER INSERT ON events BEGIN
                    INSERT INTO nerve_events_fts(rowid,message,target_id) VALUES (new.id,new.message,new.target_id);
                END;
                CREATE TRIGGER IF NOT EXISTS nerve_events_fts_del AFTER DELETE ON events BEGIN
                    INSERT INTO nerve_events_fts(nerve_events_fts,rowid,message,target_id)
                    VALUES ('delete',old.id,old.message,old.target_id);
                END;
                CREATE TRIGGER IF NOT EXISTS nerve_memories_fts_ins AFTER INSERT ON memories BEGIN
                    INSERT INTO nerve_memories_fts(rowid,text,target_id) VALUES (new.id,new.text,new.target_id);
                END;
                CREATE TRIGGER IF NOT EXISTS nerve_memories_fts_del AFTER DELETE ON memories BEGIN
                    INSERT INTO nerve_memories_fts(nerve_memories_fts,rowid,text,target_id)
                    VALUES ('delete',old.id,old.text,old.target_id);
                END;
            """)
            if not has_event_index:
                self.conn.execute("INSERT INTO nerve_events_fts(nerve_events_fts) VALUES('rebuild')")
            if not has_memory_index:
                self.conn.execute("INSERT INTO nerve_memories_fts(nerve_memories_fts) VALUES('rebuild')")
            self.conn.commit()
            self._fts_ready = True
        except sqlite3.OperationalError:
            self.conn.rollback()

    def _source_digest(self, target_id: str) -> str:
        """Bind evidence to a source revision, without persisting source contents.

        An empty digest means no source revision could be anchored. In particular,
        it does NOT mean verified evidence: manually observed targets may not have
        a file and some permitted source paths may no longer exist.
        """
        row = self.conn.execute("SELECT source_path FROM targets WHERE target_id=?", (target_id,)).fetchone()
        if not row or not row["source_path"]:
            return ""
        try:
            src = _allowed_relative_path(self.root, row["source_path"])
            if not src.is_file() or src.stat().st_size > MAX_FILE_SIZE:
                return ""
            return sha256(src.read_bytes()).hexdigest()
        except (OSError, ValueError):
            return ""

    def _evidence_freshness(self, target_id: str, anchor: str) -> str:
        if not anchor:
            return "unanchored"
        row = self.conn.execute("SELECT source_path FROM targets WHERE target_id=?", (target_id,)).fetchone()
        if not row or not row["source_path"]:
            return "source_missing"
        try:
            src = _allowed_relative_path(self.root, row["source_path"])
            if not src.is_file():
                return "source_missing"
            if src.stat().st_size > MAX_FILE_SIZE:
                return "source_unavailable"
            current = sha256(src.read_bytes()).hexdigest()
        except (OSError, ValueError):
            return "source_unavailable"
        return "source_unchanged" if current == anchor else "source_changed"

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> Nerve:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def observe(self, target_id: str, label: str, kind: str = "object", description: str = "",
                aliases: list[str] | None = None, source_path: str = "", locator: str = "",
                state: dict[str, Any] | None = None, origin: str = "adapter") -> dict[str, Any]:
        """Register a stable observable identity. Updated state replaces prior state."""
        if not target_id.strip() or not label.strip():
            raise ValueError("target_id and label are required")
        if len(target_id) > 250:
            raise ValueError("target_id is too long (250-character maximum)")
        if source_path:
            _allowed_relative_path(self.root, source_path)
        existing = self.conn.execute("SELECT * FROM targets WHERE target_id=?", (target_id,)).fetchone()
        item = {
            "target_id": target_id[:250], "label": clean_text(label)[:200],
            "kind": clean_text(kind)[:80], "description": clean_text(description),
            "aliases": json.dumps([clean_text(a)[:200] for a in (aliases or [])[:20]]),
            "source_path": source_path, "locator": clean_text(locator)[:250],
            "state": json.dumps(redact(state if state is not None else (json.loads(existing["state"]) if existing else {}))),
            "origin": origin, "updated_at": utc_now(),
        }
        self.conn.execute("""INSERT INTO targets(target_id,label,kind,description,aliases,source_path,locator,state,origin,updated_at)
            VALUES (:target_id,:label,:kind,:description,:aliases,:source_path,:locator,:state,:origin,:updated_at)
            ON CONFLICT(target_id) DO UPDATE SET
            label=excluded.label,kind=excluded.kind,description=excluded.description,
            aliases=excluded.aliases,source_path=excluded.source_path,locator=excluded.locator,
            state=excluded.state,origin=excluded.origin,updated_at=excluded.updated_at""", item)
        self.conn.commit()
        return self.context(target_id, include_history=False)

    def event(self, target_id: str, event_type: str, message: str, payload: dict[str, Any] | None = None) -> int:
        if not self.conn.execute("SELECT 1 FROM targets WHERE target_id=?", (target_id,)).fetchone():
            raise ValueError("Unknown target; observe it first")
        digest = self._source_digest(target_id)
        with self.conn:
            cursor = self.conn.execute(
                "INSERT INTO events(target_id,event_type,message,payload,created_at,source_digest) VALUES (?,?,?,?,?,?)",
                (target_id, clean_text(event_type)[:100], clean_text(message), json.dumps(redact(payload or {})), utc_now(), digest))
        return int(cursor.lastrowid)

    def remember(self, text: str, target_id: str = "project", category: str = "decision", author: str = "user") -> int:
        if not text.strip():
            raise ValueError("Memory text must not be empty")
        if target_id != "project" and not self.conn.execute("SELECT 1 FROM targets WHERE target_id=?", (target_id,)).fetchone():
            raise ValueError("Unknown target; observe it first or use project scope")
        digest = self._source_digest(target_id)
        with self.conn:
            cursor = self.conn.execute(
                "INSERT INTO memories(target_id,category,text,author,created_at,source_digest) VALUES (?,?,?,?,?,?)",
                (target_id, clean_text(category)[:80], clean_text(text), clean_text(author)[:80], utc_now(), digest))
        return int(cursor.lastrowid)

    def context(self, target_id: str, include_history: bool = True, limit: int = 12) -> dict[str, Any]:
        row = self.conn.execute("SELECT * FROM targets WHERE target_id=?", (target_id,)).fetchone()
        if not row:
            return {"found": False, "target_id": target_id}
        info = dict(row)
        for key in ("aliases", "state"):
            info[key] = json.loads(info[key])
        info["found"] = True
        if include_history:
            info["events"] = [dict(x) for x in self.conn.execute(
                "SELECT * FROM events WHERE target_id=? ORDER BY id DESC LIMIT ?", (target_id, min(limit, 50)))]
            for e in info["events"]:
                e["payload"] = json.loads(e["payload"])
                e["freshness"] = self._evidence_freshness(e["target_id"], e["source_digest"])
            # Reserve space for target-scoped facts first: recent project-wide
            # notes must never evict a target's relevant evidence from context.
            cap = max(1, min(limit, 50))
            scoped = [dict(x) for x in self.conn.execute(
                "SELECT * FROM memories WHERE target_id=? ORDER BY id DESC LIMIT ?", (target_id, cap))]
            global_notes = []
            if target_id != "project" and len(scoped) < cap:
                global_notes = [dict(x) for x in self.conn.execute(
                    "SELECT * FROM memories WHERE target_id='project' ORDER BY id DESC LIMIT ?",
                    (cap-len(scoped),))]
            info["memories"] = sorted(scoped + global_notes, key=lambda x:x["id"], reverse=True)
            for m in info["memories"]:
                m["freshness"] = self._evidence_freshness(m["target_id"], m["source_digest"])
            info["evidence_notice"] = "File revision comparison is a staleness indicator, not proof that a memory is true. Agent-supplied text is untrusted."
        return info

    def resolve(self, query: str, limit: int = 5) -> dict[str, Any]:
        """Evidence-ranked candidates, not semantic understanding or certainty.

        Short exact identifiers and aliases dominate short requests; historical
        evidence matters more in descriptive requests. Common incidental words
        in one-symbol names do not win just because a long query contains them.
        """
        q = retrieval_tokens(query)
        if not q:
            return {"query": query, "candidates": [], "decision": "no_match",
                    "may_act_without_verification": False,
                    "message": "Add a more specific target description"}
        rows = self.conn.execute("SELECT * FROM targets").fetchall()
        history: dict[str, list[str]] = {}
        if self._fts_ready:
            # Treat each token as a phrase; avoid injecting caller-controlled
            # FTS syntax. FTS5's native tokenizer performs case folding.
            terms = sorted(q, key=lambda t:(-len(t),t))[:16]
            sources = (
                ("SELECT target_id, message AS content FROM nerve_events_fts WHERE nerve_events_fts MATCH ? LIMIT 500", 8),
                ("SELECT target_id, text AS content FROM nerve_memories_fts WHERE nerve_memories_fts MATCH ? LIMIT 500", 12),
            )
            # Search each term independently: a broad term like "castle" may
            # have thousands of matches. A single combined OR query with a
            # global LIMIT would crowd out an older *distinctive* incident.
            # Try longer (usually more discriminative) terms first.
            for statement, max_per_target in sources:
                for term in terms:
                    for item in self.conn.execute(statement, ('"' + term + '"',)):
                        bucket = history.setdefault(item["target_id"], [])
                        if len(bucket) < max_per_target and q & retrieval_tokens(item["content"]):
                            bucket.append(item["content"])
        else:
            # Feature fallback for SQLite builds without FTS5. Correctness is
            # favored over speed: scan all evidence, never silently discard old
            # incidents because another target received newer events.
            for statement, max_per_target in (
                ("SELECT target_id,message AS content FROM events ORDER BY id DESC", 8),
                ("SELECT target_id,text AS content FROM memories WHERE target_id != 'project' ORDER BY id DESC", 12),
            ):
                for item in self.conn.execute(statement):
                    bucket = history.setdefault(item["target_id"], [])
                    if len(bucket) < max_per_target and q & retrieval_tokens(item["content"]):
                        bucket.append(item["content"])
        scored: list[tuple[int, sqlite3.Row, list[str], int, bool]] = []
        normalized = " ".join(query.casefold().split())
        for row in rows:
            alias_strings = json.loads(row["aliases"])
            exact = (normalized == " ".join(row["label"].casefold().split()) or
                     normalized == row["target_id"].casefold() or
                     any(normalized == " ".join(a.casefold().split()) for a in alias_strings))
            label = retrieval_tokens(row["label"])
            path = retrieval_tokens(row["source_path"])
            aliases = retrieval_tokens(" ".join(alias_strings))
            desc = retrieval_tokens(row["description"])
            past = retrieval_tokens(" ".join(history.get(row["target_id"], [])))
            overlap = len(q & (label | path | aliases | desc | past))
            if not overlap and not exact: continue
            # Historical incident terms carry more weight in descriptive questions.
            # Exact label and alias matches are never penalized by text length.
            if len(q) <= 2:
                score = (8 * len(q & label) + 6 * len(q & aliases) + 3 * len(q & path)
                         + len(q & desc) + 2 * len(q & past))
            else:
                score = (2 * len(q & label) + 2 * len(q & aliases) + len(q & path)
                         + len(q & desc) + 5 * len(q & past))
            if exact: score += 100
            evidence = []
            for key, values in (("label",label),( "aliases",aliases), ("path",path),
                                ("description",desc),("history",past)):
                if q & values: evidence.append(key+":"+",".join(sorted(q & values)))
            scored.append((score,row,evidence,overlap,exact))
        scored.sort(key=lambda item:(-item[0],item[1]["target_id"]))
        candidates = []
        for score,r,evidence,_,_ in scored[:max(1,min(limit,20))]:
            source_path = r["source_path"]
            source_status = "not_file_backed"
            if source_path:
                try:
                    source_status = "present" if _allowed_relative_path(self.root, source_path).is_file() else "missing"
                except (ValueError, OSError):
                    source_status = "unavailable"
            candidates.append({"target_id":r["target_id"],"label":r["label"],"kind":r["kind"],
                               "source_path":source_path,"source_status":source_status,
                               "score":score,"evidence":evidence,
                               "last_observed":r["updated_at"],"origin":r["origin"]})
        decision = "no_match"
        if scored:
            first_score,_,_,overlap,exact = scored[0]
            ties = len(scored)>1 and scored[1][0] == first_score
            # A missing file invalidates a 'supported' match, even if the name is exact.
            # This is a safety gate, not a calibrated probability estimate.
            top_missing = bool(candidates and candidates[0]["source_status"] in ("missing", "unavailable"))
            decision = ("supported_candidate" if (exact or overlap>=2) and not ties and not top_missing
                        else "needs_confirmation")
        return {"query":query,"candidates":candidates,"decision":decision,
                "may_act_without_verification":False,
                "message":"Candidate only; confirm object identity and freshness."
                          if candidates else "No indexed or observed object matches."}

    def search_evidence(self, query: str, target_id: str | None = None,
                        limit: int = 12) -> dict[str, Any]:
        """Search older events and memories, beyond bounded recent context.

        A lexical evidence search, not semantic fact verification. The caller
        must confirm the returned content and source revision before using it.
        """
        wanted = retrieval_tokens(query)
        cap = max(1, min(limit, 50))
        if not wanted:
            return {"query": query, "target_id": target_id, "results": [],
                    "notice": "Use distinctive keywords; this is lexical retrieval, not semantic matching."}
        if target_id not in (None, "project") and not self.conn.execute(
                "SELECT 1 FROM targets WHERE target_id=?", (target_id,)).fetchone():
            return {"query": query, "target_id": target_id, "results": [], "unknown_target": True}
        matches: dict[tuple[str, int], dict[str, Any]] = {}
        specs = [("event", "events", "message", "nerve_events_fts"),
                 ("memory", "memories", "text", "nerve_memories_fts")]
        for kind, table, field, fts in specs:
            if self._fts_ready:
                for term in sorted(wanted, key=lambda t: (-len(t), t))[:16]:
                    # The term is double-quoted before being bound as SQL data,
                    # so user text cannot become an FTS5 expression.
                    qry = (f"SELECT t.* FROM {fts} f JOIN {table} t ON t.id=f.rowid "
                           f"WHERE {fts} MATCH ?")
                    params: list[Any] = ['"' + term.replace('"', '') + '"']
                    if target_id is not None:
                        qry += " AND t.target_id=?"
                        params.append(target_id)
                    qry += " ORDER BY t.id DESC LIMIT 500"
                    rows = self.conn.execute(qry, params)
                    for row in rows:
                        matches[(kind,row["id"])] = dict(row)
            else:
                qry = f"SELECT * FROM {table}"
                params = []
                if target_id is not None:
                    qry += " WHERE target_id=?"
                    params.append(target_id)
                for row in self.conn.execute(qry, params):
                    matches[(kind,row["id"])] = dict(row)
        ranked = []
        for (kind,ident), row in matches.items():
            content = row["message"] if kind == "event" else row["text"]
            overlap = wanted & retrieval_tokens(content)
            if not overlap: continue
            ranked.append((len(overlap),ident,kind,row,sorted(overlap)))
        ranked.sort(key=lambda t: (-t[0],-t[1],t[2]))
        output = []
        for score,ident,kind,row,terms in ranked[:cap]:
            obj = {"id":ident,"type":kind,"target_id":row["target_id"],
                   "text":row["message"] if kind == "event" else row["text"],
                   "matched_terms":terms,"created_at":row["created_at"],
                   "freshness":self._evidence_freshness(row["target_id"],row["source_digest"])}
            output.append(obj)
        return {"query":query,"target_id":target_id,"results":output,
                "notice":"Lexical match only; source freshness is not proof of factual accuracy."}

    def recent(self, limit: int = 20) -> dict[str, Any]:
        limit = max(1, min(limit, 100))
        events = [dict(r) for r in self.conn.execute("SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,))]
        for item in events:
            item["payload"] = json.loads(item["payload"])
            item["freshness"] = self._evidence_freshness(item["target_id"], item["source_digest"])
        memories = [dict(r) for r in self.conn.execute("SELECT * FROM memories ORDER BY id DESC LIMIT ?", (limit,))]
        for item in memories:
            item["freshness"] = self._evidence_freshness(item["target_id"], item["source_digest"])
        return {"project": str(self.root), "events": events, "memories": memories}

    def forget(self, target_id: str) -> dict[str, int]:
        """Explicit deletion of one target and its associated history."""
        with self.conn:
            a = self.conn.execute("DELETE FROM targets WHERE target_id=?", (target_id,)).rowcount
            b = self.conn.execute("DELETE FROM events WHERE target_id=?", (target_id,)).rowcount
            c = self.conn.execute("DELETE FROM memories WHERE target_id=?", (target_id,)).rowcount
        return {"targets": a, "events": b, "memories": c}

    def scan(self) -> dict[str, Any]:
        """Read safe source metadata. Never store full source or secrets from files."""
        found = 0
        indexed_symbols = 0
        skipped = 0
        # Prune excluded directories BEFORE walking their contents. A naive
        # rglob still enumerated massive node_modules/.git/build trees, even
        # though files inside them were later skipped. Do not follow symlinked
        # folders, and resolve each candidate before reading it.
        for directory, child_dirs, filenames in os.walk(self.root, followlinks=False):
            child_dirs[:] = sorted(
                name for name in child_dirs
                if name not in EXCLUDED_DIRS and not name.startswith(".env")
                and not (Path(directory) / name).is_symlink()
            )
            if found >= MAX_SCAN_FILES:
                break
            for filename in sorted(filenames):
                p = Path(directory) / filename
                if p.suffix not in SUPPORTED or p.name in EXCLUDED_NAMES or p.suffix in EXCLUDED_SUFFIXES:
                    continue
                rel = p.relative_to(self.root)
                if any(part in EXCLUDED_DIRS or part.startswith(".env") for part in rel.parts):
                    continue
                if found >= MAX_SCAN_FILES:
                    break
                try:
                    resolved = p.resolve()
                    if not p.is_file() or not resolved.is_relative_to(self.root) or p.stat().st_size > MAX_FILE_SIZE:
                        skipped += 1
                        continue
                    content = p.read_text(encoding="utf-8")
                except (OSError, UnicodeError):
                    skipped += 1
                    continue
                path = rel.as_posix()
                found += 1
                names = []
                for m in SYMBOL.finditer(content):
                    name = m.group(1) or m.group(2)
                    # Limit symbol fan-out to keep indexes bounded.
                    if name in names or len(names) >= 75:
                        continue
                    names.append(name)
                    target_id = f"symbol:{path}:{name}"
                    previous = self.conn.execute("SELECT origin FROM targets WHERE target_id=?", (target_id,)).fetchone()
                    if previous is None or previous["origin"] == "source-index":
                        self.observe(target_id, name, "source-symbol",
                                     "Declared symbol in indexed source file (static index; not a live object)",
                                     [name], path, origin="source-index")
                    indexed_symbols += 1
                # Derive searchable hints from filename, no full source text retained.
                target_id = f"file:{path}"
                previous = self.conn.execute("SELECT origin FROM targets WHERE target_id=?", (target_id,)).fetchone()
                if previous is None or previous["origin"] == "source-index":
                    self.observe(target_id, p.stem, "source-file",
                                 "Contains declared symbols: " + ", ".join(names[:50]),
                                 [path], path, origin="source-index")
        return {"files_indexed": found, "symbols_indexed": indexed_symbols,
                "files_skipped": skipped, "scope": str(self.root),
                "note": "Static index only; application state requires an observation adapter."}
