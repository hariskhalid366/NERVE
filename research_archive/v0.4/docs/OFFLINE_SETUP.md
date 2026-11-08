# Offline / closed-network setup

NERVE's core, local CLI, SQLite storage and built-in stdio MCP tools subset require only Python 3.11+ and Python's standard library. This is designed for developers unable to send project source to external AI memory providers. **An AI host/model still needs to be available locally or through its permitted network; NERVE itself does not supply an LLM.**

## Steps

1. Transfer either the release ZIP or pre-built `nerve_agent_memory-0.4.0-py3-none-any.whl` to the approved development machine. For the wheel, install fully offline with:

   ```bash
   python -m pip install --no-index --no-deps /path/to/nerve_agent_memory-0.4.0-py3-none-any.whl
   ```

   This exact wheel-install flow was validated in a fresh isolated Python environment on Linux. Other operating systems remain untested.
2. With Python and setuptools already installed on the machine, from the extracted source directory:

   ```bash
   python -m pip install --no-build-isolation --no-deps -e .
   ```

   If `pip` or setuptools is not present, execute `python -m nerve` from inside the NERVE source folder with an appropriate `PYTHONPATH`, or provision approved Python packaging dependencies through your organization's internal package mirror.
3. Open an existing non-sensitive local project. Add `.nerve/` to its `.gitignore`.
4. Run:

   ```bash
   nerve --project /absolute/project/path init
   nerve --project /absolute/project/path scan
   nerve --project /absolute/project/path cursor-config --write
   nerve --project /absolute/project/path doctor
   ```

5. Reload Cursor or configure another MCP-capable host with the generated stdio config. Ask the host to list NERVE tools. Test `get_project_brief`; if that works, record a sample decision and test retrieval in a **new** agent session.

## No background capture

There is no always-on watcher, screen recording, clipboard collection or cloud upload. New context enters the database only when you call the CLI, an authorized agent uses the tools, or you explicitly enable an observer such as the safe Git metadata post-commit hook.

## Offline MCP wire format

When the official MCP SDK is absent, the fallback supports the common MCP `2025-06-18` stdio JSON-RPC tool subset: `initialize`, `ping`, `tools/list`, `tools/call` and notifications. It does not support prompts, resources, streaming, remote HTTP or OAuth. It is a compatibility layer; editor-host interoperability is not yet verified for each supported protocol revision.

## Troubleshooting

- **Can't import `nerve`:** verify the `pip install -e .` target and the Python interpreter configured in `.cursor/mcp.json` are the same.
- **No tools available:** restart your host, verify absolute project and Python paths and check the host's MCP logs.
- **Memory missing:** verify `--project` points to the exact same root, and check `.nerve/memory.sqlite3` exists.
- **Agent doesn't record decisions:** host tool use is discretionary; give the agent a clear project rule to record confirmed decisions, but verify which tool calls it actually makes.
- **Network restrictions:** NERVE local mode makes no outbound requests. Optional cloud mode should remain disabled.
