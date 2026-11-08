"""Small dependency-free MCP stdio compatibility adapter for offline local projects.

Implements the common 2025-06-18 JSON-RPC 2.0 tools subset. This is not a
replacement for the full MCP SDK; prefer the SDK when installed and available.
It is intentionally **local stdio only** and has no networking capability.
"""
from __future__ import annotations
import json
from pathlib import Path
import sys
from typing import Any
from .core import Nerve
from .brief import project_brief

MAX_LINE = 65536
PROTOCOL = '2025-06-18'


def tool_spec(name: str, description: str, properties: dict, required: list[str] | None = None) -> dict:
    return {'name': name, 'description': description, 'inputSchema': {
        'type': 'object', 'properties': properties, 'required': required or [],
        'additionalProperties': False,
    }}


def string(description: str) -> dict:
    return {'type': 'string', 'description': description}


def integer(description: str, *, minimum: int = 1, maximum: int = 50) -> dict:
    return {'type': 'integer', 'minimum': minimum, 'maximum': maximum, 'description': description}


TOOLS = [
    tool_spec('get_project_brief', 'Bounded recent project decisions and events.',
              {'limit': integer('How many recent entries to return.', maximum=25)}),
    tool_spec('scan_project', 'Index permitted local filenames and source symbols, not full source contents.', {}),
    tool_spec('resolve_target', 'Resolve reference to candidate object identities; results need verification.',
              {'query': string('Target description or user reference.'),
               'limit': integer('Maximum candidates.', maximum=20)}, ['query']),
    tool_spec('get_target_context', 'Read an exact object identity and its recorded history.',
              {'target_id': string('Target identifier.')}, ['target_id']),
    tool_spec('search_evidence', 'Search old stored project evidence by keywords beyond the recent-context limit.',
              {'query': string('Distinctive evidence keywords.'), 'target_id': string('Optional exact target ID.'),
               'limit': integer('Maximum matches.',maximum=50)}, ['query']),
    tool_spec('get_recent_activity', 'Read recent events and memories.',
              {'limit': integer('Maximum entries.', maximum=100)}),
    tool_spec('observe_target', 'Register an authorized observation of an object.',
              {'target_id': string('Stable target ID.'), 'label': string('Visible name.'),
               'kind': string('Object category.'), 'description': string('Short description.'),
               'aliases': {'type': 'array', 'items': {'type': 'string'}},
               'source_path': string('Project-relative source path.'),
               'locator': string('Optional stable locator.'),
               'state': {'type': 'object'}}, ['target_id', 'label']),
    tool_spec('record_event', 'Record an observed event about an existing target.',
              {'target_id': string('Existing target ID.'),
               'event_type': string('Event category.'),
               'message': string('Verified concise observation.'),
               'payload': {'type': 'object'}}, ['target_id', 'event_type', 'message']),
    tool_spec('remember_context', 'Persist an explicit decision or note; not automatic verification.',
              {'text': string('Decision, observation or fact.'),
               'target_id': string('Existing target ID or project.'),
               'category': string('Fact category.')}, ['text']),
]


def call_tool(root: Path, name: str, args: dict) -> dict:
    spec = next((t for t in TOOLS if t['name'] == name), None)
    if spec is None:
        raise ValueError('Unknown tool')
    if not isinstance(args, dict):
        raise ValueError('Tool arguments must be an object')
    fields = spec['inputSchema']['properties']
    if set(args) - set(fields):
        raise ValueError('Unexpected tool arguments')
    missing = set(spec['inputSchema']['required']) - set(args)
    if missing:
        raise ValueError('Missing required tool arguments: ' + ', '.join(sorted(missing)))
    for key, value in args.items():
        typ = fields[key]['type']
        if typ == 'integer' and (type(value) is not int or not fields[key]['minimum'] <= value <= fields[key]['maximum']):
            raise ValueError('Invalid integer value for ' + key)
        if typ == 'string' and (not isinstance(value, str) or len(value) > 3000):
            raise ValueError('Invalid string value for ' + key)
        if typ == 'object' and not isinstance(value, dict):
            raise ValueError('Invalid object value for ' + key)
        if typ == 'array' and (not isinstance(value, list) or not all(isinstance(v, str) for v in value)):
            raise ValueError('Invalid string array for ' + key)
    with Nerve(root) as n:
        if name == 'get_project_brief': return project_brief(n, args.get('limit', 8))
        if name == 'scan_project': return n.scan()
        if name == 'resolve_target': return n.resolve(args['query'], args.get('limit', 5))
        if name == 'get_target_context': return n.context(args['target_id'])
        if name == 'get_recent_activity': return n.recent(args.get('limit', 20))
        if name == 'search_evidence': return n.search_evidence(args['query'],args.get('target_id'),args.get('limit',12))
        if name == 'observe_target': return n.observe(**args)
        if name == 'record_event': return {'event_id': n.event(**args)}
        if name == 'remember_context':
            return {'memory_id': n.remember(args['text'], args.get('target_id', 'project'),
                                            args.get('category', 'decision'), author='agent')}
    raise AssertionError('Unknown tool')


def handle(root: Path, message: Any) -> dict | None:
    """Return one JSON-RPC response, or None for notifications."""
    if not isinstance(message, dict) or message.get('jsonrpc') != '2.0':
        return {'jsonrpc': '2.0', 'id': None, 'error': {'code': -32600, 'message': 'Invalid Request'}}
    method = message.get('method')
    ident = message.get('id')
    if 'id' not in message:  # JSON-RPC notification: never respond
        return None
    out: dict = {'jsonrpc': '2.0', 'id': ident}
    try:
        if method == 'initialize':
            params = message.get('params') or {}
            if not isinstance(params, dict): raise ValueError('Invalid parameters')
            # A common compatibility protocol, not pretending to support unknown revisions.
            out['result'] = {'protocolVersion': PROTOCOL,
                             'capabilities': {'tools': {'listChanged': False}},
                             'serverInfo': {'name': 'nerve-local', 'version': '0.8.0rc2'}}
        elif method == 'ping': out['result'] = {}
        elif method == 'tools/list': out['result'] = {'tools': TOOLS}
        elif method == 'tools/call':
            params = message.get('params')
            if not isinstance(params, dict) or not isinstance(params.get('name'), str):
                raise ValueError('Expected tool name and arguments')
            try:
                value = call_tool(root, params['name'], params.get('arguments', {}))
                out['result'] = {'content': [{'type': 'text', 'text': json.dumps(value, ensure_ascii=False)}],
                                 'isError': False}
            except (TypeError, ValueError, OSError) as exc:
                out['result'] = {'content': [{'type': 'text', 'text': str(exc)[:300]}],
                                 'isError': True}
        else:
            out['error'] = {'code': -32601, 'message': 'Method not found'}
    except (TypeError, ValueError) as exc:
        out['error'] = {'code': -32602, 'message': str(exc)[:300]}
    return out


def serve(project: str) -> None:
    root = Path(project).expanduser().resolve(strict=True)
    if not root.is_dir(): raise ValueError('project_root must be a directory')
    # No debug banners printed to stdout; only JSON-RPC frames.
    for line in sys.stdin.buffer:
        if len(line) > MAX_LINE:
            response = {'jsonrpc': '2.0', 'id': None,
                        'error': {'code': -32700, 'message': 'Message too large'}}
        else:
            try:
                response = handle(root, json.loads(line))
            except (UnicodeDecodeError, json.JSONDecodeError):
                response = {'jsonrpc': '2.0', 'id': None,
                            'error': {'code': -32700, 'message': 'Parse error'}}
        if response is not None:
            sys.stdout.write(json.dumps(response, ensure_ascii=False, separators=(',', ':')) + '\n')
            sys.stdout.flush()
