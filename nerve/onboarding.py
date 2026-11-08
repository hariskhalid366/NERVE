"""Safe, opt-in host configuration helpers for local project mode."""
from __future__ import annotations
import json
from pathlib import Path
import sys


def cursor_config(project_root: Path, python_path: str | None = None) -> dict:
    """Generate config; never edit or replace a user's editor settings implicitly."""
    root = project_root.expanduser().resolve(strict=True)
    if not root.is_dir():
        raise ValueError('project must be a directory')
    command = str(Path(python_path or sys.executable).resolve())
    return {'mcpServers': {'nerve-local': {
        'type': 'stdio', 'command': command,
        'args': ['-m', 'nerve', '--project', str(root), 'mcp'],
    }}}


def save_cursor_config(project_root: Path, *, python_path: str | None = None) -> Path:
    """Merge a single key; refuse invalid configs and existing key collisions."""
    root = project_root.expanduser().resolve(strict=True)
    target = root / '.cursor' / 'mcp.json'
    target.parent.mkdir(exist_ok=True)
    existing = {}
    if target.exists():
        if target.is_symlink():
            raise ValueError('Refusing symlinked MCP config')
        try:
            existing = json.loads(target.read_text(encoding='utf-8'))
        except (OSError, ValueError) as exc:
            raise ValueError('Existing Cursor config is unreadable or invalid JSON; not modifying') from exc
        if not isinstance(existing, dict) or not isinstance(existing.get('mcpServers', {}), dict):
            raise ValueError('Existing Cursor config structure is invalid; not modifying')
        if 'nerve-local' in existing.get('mcpServers', {}):
            raise ValueError('nerve-local already exists; edit it manually if needed')
    existing.setdefault('mcpServers', {}).update(cursor_config(root, python_path)['mcpServers'])
    target.write_text(json.dumps(existing, indent=2) + '\n', encoding='utf-8')
    return target
