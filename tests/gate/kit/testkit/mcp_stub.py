#!/usr/bin/env -S python3 -I -S
"""Stub MCP server over stdio (the testkit's stand-in for a web MCP server, which the kit does
not own: a hosted search provider), newline-delimited JSON-RPC 2.0: argv[1] names it, each later
arg is one tool it lists. `initialize` answers with the client's protocol version, `tools/list`
the tools (each "NAME TOOL" its description, one string argument q), `tools/call` the text
NAME-TOOL-result, `ping` {}; any other request method-not-found; notifications go unanswered."""

import json
import sys
from typing import Any

name, tools = sys.argv[1], sys.argv[2:]


def send(o: object) -> None:
    sys.stdout.write(json.dumps(o) + "\n")
    sys.stdout.flush()


def answer(m: dict[str, Any]) -> dict[str, object]:
    meth, i = m.get("method"), m["id"]
    params: dict[str, Any] = m.get("params") or {}
    if meth == "initialize":
        result: object = {
            "protocolVersion": params.get("protocolVersion", "2025-06-18"),
            "capabilities": {"tools": {}},
            "serverInfo": {"name": name, "version": "1"},
        }
    elif meth == "tools/list":
        schema = {"type": "object", "properties": {"q": {"type": "string"}}}
        result = {
            "tools": [
                {"name": t, "description": f"{name} {t}", "inputSchema": schema} for t in tools
            ]
        }
    elif meth == "tools/call":
        result = {"content": [{"type": "text", "text": f"{name}-{params['name']}-result"}]}
    elif meth == "ping":
        result = {}
    else:
        return {"jsonrpc": "2.0", "id": i, "error": {"code": -32601, "message": "method not found"}}
    return {"jsonrpc": "2.0", "id": i, "result": result}


for line in sys.stdin:
    try:
        m: dict[str, Any] = json.loads(line)
    except ValueError:
        continue
    if "id" in m:
        send(answer(m))
