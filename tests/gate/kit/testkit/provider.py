#!/usr/bin/env -S python3 -I -S
"""Fake OpenAI-compatible model provider on 127.0.0.1 (the testkit's stand-in for a model
provider, which the kit does not own): `provider.py LOG CODE` serves chat completions as an SSE
stream, appending each request body as one JSON line to LOG; a request holding no tool result
gets one `codemode` tool call running CODE, the next the answer `fake-done`. Readiness, never a
delay: once listening it prints its port as one line on stdout, which the caller reads off the
pipe. Runs until killed."""

import http.server
import json
import sys

log, code = sys.argv[1], sys.argv[2]
BASE = {"id": "x", "object": "chat.completion.chunk", "created": 0, "model": "fake"}


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:  # noqa: A002 (the base's name)
        pass

    def do_POST(self) -> None:  # noqa: N802 (the base's name)
        body = json.loads(self.rfile.read(int(self.headers.get("content-length", 0))))
        with open(log, "a") as f:  # noqa: PTH123 (os-level start: -S)
            f.write(json.dumps(body) + "\n")
        self.send_response(200)
        self.send_header("content-type", "text/event-stream")
        self.end_headers()
        if any(m.get("role") == "tool" for m in body["messages"]):
            deltas = [({"role": "assistant", "content": "fake-done"}, None), ({}, "stop")]
        else:
            fn = {"name": "codemode", "arguments": json.dumps({"code": code})}
            call = {"index": 0, "id": "call_1", "type": "function", "function": fn}
            deltas = [({"role": "assistant", "tool_calls": [call]}, None), ({}, "tool_calls")]
        for d, fin in deltas:
            c: dict[str, object] = {**BASE, "choices": [{"index": 0, "delta": d, "finish_reason": fin}]}
            if fin:
                c["usage"] = {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}
            self.wfile.write(b"data: " + json.dumps(c).encode() + b"\n\n")
        self.wfile.write(b"data: [DONE]\n\n")


server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
sys.stdout.write(f"{server.server_address[1]}\n")
sys.stdout.flush()
server.serve_forever()
