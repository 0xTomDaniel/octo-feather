#!/usr/bin/env python3
"""Stand-in for a model provider at Pi's provider boundary (the kit tests' one, #973): an
OpenAI-compatible chat completions server on 127.0.0.1, for a models.json provider
{"baseUrl": "http://127.0.0.1:PORT/v1", "api": "openai-completions", "apiKey": "x",
"models": [{"id": "fake"}]}.

  provider.py [--log FILE] [--code CODE]

Prints its port and a newline on stdout once it listens (the caller's readiness: wait for that
line), then serves until killed. Each request body is appended to FILE as one JSON line. Every
request gets the answer fake-done, streamed (text/event-stream): one delta, then the finish with
usage 1 in, 1 out, then [DONE]. With --code, a request holding no tool result yet gets instead one
codemode tool call running CODE (what it returns reaches the log in the next request).
"""

from __future__ import annotations

import argparse
import http.server
import json
import sys
from typing import Any

ANSWER = "fake-done"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--log")
    ap.add_argument("--code")
    a = ap.parse_args()
    log: str | None = a.log

    class H(http.server.BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: Any) -> None:  # noqa: A002, ANN401
            pass

        def do_POST(self) -> None:
            body = json.loads(self.rfile.read(int(self.headers.get("content-length", 0))))
            if log:
                with open(log, "a") as f:  # noqa: PTH123
                    f.write(json.dumps(body) + "\n")
            self.send_response(200)
            self.send_header("content-type", "text/event-stream")
            self.end_headers()
            base = {"id": "x", "object": "chat.completion.chunk", "created": 0, "model": "fake"}
            delta: dict[str, Any] = {"role": "assistant", "content": ANSWER}
            finish = "stop"
            if a.code and not any(m.get("role") == "tool" for m in body["messages"]):
                fn = {"name": "codemode", "arguments": json.dumps({"code": a.code})}
                call = {"index": 0, "id": "call_1", "type": "function", "function": fn}
                delta = {"role": "assistant", "tool_calls": [call]}
                finish = "tool_calls"
            usage = {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}
            for d, end in ((delta, None), ({}, finish)):
                choice = {"index": 0, "delta": d, "finish_reason": end}
                c: dict[str, Any] = {**base, "choices": [choice]}
                if end:
                    c["usage"] = usage
                self.wfile.write(b"data: " + json.dumps(c).encode() + b"\n\n")
            self.wfile.write(b"data: [DONE]\n\n")

    s = http.server.HTTPServer(("127.0.0.1", 0), H)
    sys.stdout.write(f"{s.server_address[1]}\n")
    sys.stdout.flush()
    s.serve_forever()


if __name__ == "__main__":
    main()
