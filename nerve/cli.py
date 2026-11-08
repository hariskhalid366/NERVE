"""Dependency-free CLI; add the MCP extra to expose the same functionality to agents."""
import argparse
import json
from pathlib import Path
from .core import Nerve


def main() -> None:
    parser = argparse.ArgumentParser(prog="nerve", description="Local project memory for AI agents")
    parser.add_argument("--project", default=".", help="Project folder. Database lives under PROJECT/.nerve")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init", help="Create project-local database")
    sub.add_parser("doctor", help="Check NERVE database, MCP availability and Git integration")
    b = sub.add_parser("brief", help="Bounded project history summary for session start")
    b.add_argument("--limit", type=int, default=8)
    c = sub.add_parser("cursor-config", help="Print Cursor project MCP config without writing it")
    c.add_argument("--write", action="store_true", help="Merge into .cursor/mcp.json (opt-in)")
    gh = sub.add_parser("git-hook", help="Install Git post-commit metadata observer (opt-in)")
    gh.add_argument("action", choices=["install"])
    sub.add_parser("git-capture", help="Record latest Git commit metadata (no source/diff content)")
    sub.add_parser("scan", help="Index permitted source filenames and symbols")
    p = sub.add_parser("resolve", help="Find an object by natural language")
    p.add_argument("query")
    p = sub.add_parser("search-evidence", help="Search historical evidence beyond recent context")
    p.add_argument("query"); p.add_argument("--target", default=None)
    p = sub.add_parser("context", help="Retrieve evidence for an exact target ID")
    p.add_argument("target_id")
    p = sub.add_parser("observe", help="Ingest structured observation JSON")
    p.add_argument("json_path", help="Path to a JSON file with fields matching observe()")
    p = sub.add_parser("event", help="Record an event")
    p.add_argument("target_id"); p.add_argument("event_type"); p.add_argument("message")
    p = sub.add_parser("remember", help="Store an explicit project-scoped decision or fact")
    p.add_argument("text"); p.add_argument("--target", default="project")
    p = sub.add_parser("recent", help="Show recent evidence")
    p.add_argument("--limit", type=int, default=20)
    p = sub.add_parser("forget", help="Delete a target and its target-scoped history")
    p.add_argument("target_id")
    sub.add_parser("mcp", help="Run local MCP stdio server (built-in fallback, optional .[mcp])")
    p = sub.add_parser("listen", help="Receive authorized observations via localhost HTTP")
    p.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    if args.command == "mcp":
        import importlib.util
        import os
        selected = os.getenv("NERVE_MCP_BACKEND", "auto").lower()
        if selected not in ("auto", "builtin", "sdk"):
            raise SystemExit("NERVE_MCP_BACKEND must be auto, builtin or sdk")
        available = importlib.util.find_spec("mcp") is not None
        if selected == "sdk" and not available:
            raise SystemExit("MCP SDK unavailable; install .[mcp] or select builtin")
        if selected == "builtin" or (selected == "auto" and not available):
            # Dependency-free MCP tools subset for offline/air-gapped environments.
            from .mcp_stdio import serve
        else:
            from .mcp_server import serve
        serve(args.project)
        return
    if args.command == "listen":
        from .collector import listen
        listen(args.project, args.port)
        return
    if args.command == "cursor-config":
        from .onboarding import cursor_config, save_cursor_config
        if args.write:
            result = {"written": str(save_cursor_config(Path(args.project)))}
        else:
            result = cursor_config(Path(args.project))
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return
    if args.command in ("git-hook", "git-capture"):
        from .git_observer import capture_commit, install_post_commit_hook
        result = ({"installed": str(install_post_commit_hook(args.project))}
                  if args.command == "git-hook" else capture_commit(args.project))
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return
    with Nerve(args.project) as nerve:
        if args.command == "init": result = {"database": str(nerve.db_path), "status": "ready"}
        elif args.command == "brief":
            from .brief import project_brief
            result = project_brief(nerve, args.limit)
        elif args.command == "doctor":
            import importlib.util
            result = {"project": str(nerve.root), "database": str(nerve.db_path),
                      "mcp_installed": importlib.util.find_spec("mcp") is not None,
                      "mcp_backend": "SDK v2" if importlib.util.find_spec("mcp") is not None else "built-in stdio tool compatibility",
                      "cursor_project_config": (nerve.root / ".cursor" / "mcp.json").exists(),
                      "database_exists": nerve.db_path.is_file(),
                      "git_repo": (nerve.root / ".git").exists(),
                      "caution": "MCP package availability is not a confirmed host handshake"}
        elif args.command == "scan": result = nerve.scan()
        elif args.command == "resolve": result = nerve.resolve(args.query)
        elif args.command == "context": result = nerve.context(args.target_id)
        elif args.command == "search-evidence": result = nerve.search_evidence(args.query,args.target)
        elif args.command == "observe": result = nerve.observe(**json.loads(Path(args.json_path).read_text()))
        elif args.command == "event": result = {"event_id": nerve.event(args.target_id, args.event_type, args.message)}
        elif args.command == "remember": result = {"memory_id": nerve.remember(args.text, target_id=args.target)}
        elif args.command == "recent": result = nerve.recent(args.limit)
        elif args.command == "forget": result = nerve.forget(args.target_id)
        else: raise AssertionError("Unknown CLI command")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
