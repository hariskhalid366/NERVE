"""Opt-in, metadata-only Git observation. NEVER reads commit content or diff."""
from __future__ import annotations
from pathlib import Path
import os
import shlex
import subprocess
import sys
from .core import Nerve, _allowed_relative_path, SUPPORTED


def _git(root: Path, *args: str) -> str:
    proc = subprocess.run(['git', '-C', str(root), *args], text=True, capture_output=True,
                          timeout=10, check=False)
    if proc.returncode:
        raise ValueError('Not a usable Git repository: ' + proc.stderr.strip()[:120])
    return proc.stdout.strip()


def capture_commit(project: str | Path) -> dict:
    root = Path(project).expanduser().resolve(strict=True)
    # Abort if selected project is a nested directory of a broader repo.
    actual = Path(_git(root, 'rev-parse', '--show-toplevel')).resolve()
    if actual != root:
        raise ValueError('Select the Git repository root before capturing commits')
    sha = _git(root, 'rev-parse', 'HEAD')
    # On root commits, --root includes the new files. Commit messages and diffs are never read.
    files = _git(root, 'diff-tree', '--root', '--no-commit-id', '--name-only', '-r', 'HEAD').splitlines()
    allowed: list[str] = []
    for name in files:
        try:
            candidate = _allowed_relative_path(root, name)
            if candidate.suffix in SUPPORTED and not name.startswith('.'):
                allowed.append(name[:250])
        except ValueError:
            pass
    allowed = allowed[:100]
    with Nerve(root) as n:
        n.observe('git:repository', 'Git repository', 'repository',
                  'Metadata-only snapshots of Git commits in this project.',
                  aliases=['recent changes', 'last commit', 'Git history'], origin='git-hook',
                  state={'head': sha, 'changed_source_files': allowed, 'changed_source_count': len(allowed)})
        event_id = n.event('git:repository', 'commit',
                           f'Git commit {sha[:12]} updated {len(allowed)} permitted source files.',
                           {'sha': sha, 'changed_source_files': allowed})
    return {'sha': sha, 'source_files': allowed, 'event_id': event_id,
            'note': 'Only commit SHA and permitted source paths recorded, no diff or commit message'}


def install_post_commit_hook(project: str | Path, python_path: str | None = None) -> Path:
    root = Path(project).expanduser().resolve(strict=True)
    actual = Path(_git(root, 'rev-parse', '--show-toplevel')).resolve()
    if root != actual:
        raise ValueError('Select Git repository root')
    hooks_setting = _git(root, 'config', '--get', 'core.hooksPath') if _has_hooks_path(root) else None
    if hooks_setting:
        raise ValueError('Custom Git hooksPath is configured; refusing to install automatically')
    hooks_dir = Path(_git(root, 'rev-parse', '--git-path', 'hooks'))
    if not hooks_dir.is_absolute():
        hooks_dir = root / hooks_dir
    hooks_dir = hooks_dir.resolve()
    hooks_dir.mkdir(parents=True, exist_ok=True)
    hook = hooks_dir / 'post-commit'
    if hook.exists() or hook.is_symlink():
        raise ValueError('Existing post-commit hook found; refusing to overwrite it')
    python = shlex.quote(str(Path(python_path or sys.executable).resolve()))
    project_arg = shlex.quote(str(root))
    # Hook executes from the Git repository, not necessarily where the source
    # package was installed. Include the existing NERVE package root so source
    # checkouts are usable offline as well as pip-installed environments.
    module_parent = shlex.quote(str(Path(__file__).resolve().parent.parent))
    script = '#!/bin/sh\n# NERVE opt-in: store safe metadata after commits.\n' + \
        f'PYTHONPATH={module_parent}${{PYTHONPATH:+:$PYTHONPATH}} {python} -m nerve --project {project_arg} git-capture >/dev/null 2>&1 || true\n'
    hook.write_text(script, encoding='utf-8')
    hook.chmod(0o700)
    return hook


def _has_hooks_path(root: Path) -> bool:
    proc = subprocess.run(['git', '-C', str(root), 'config', '--get', 'core.hooksPath'],
                          capture_output=True, text=True, timeout=10)
    return proc.returncode == 0 and bool(proc.stdout.strip())
