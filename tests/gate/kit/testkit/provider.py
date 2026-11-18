#!/usr/bin/env python3
"""Stand-in for a model provider at Pi's provider boundary (the kit tests' one, #973): an
OpenAI-compatible chat completions server on 127.0.0.1, for a models.json provider
{"baseUrl": "http://127.0.0.1:PORT/v1", "api": "openai-completions", "apiKey": "x",
"models": [{"id": "fake"}]} (a "cost" there prices its calls in Pi).

  provider.py [--log FILE] [--answer TEXT]

Prints its port and a newline on stdout once it listens (the caller's readiness: wait for that
line), then serves until killed. Each request body is appended to FILE as one JSON line. Every
answer streams (text/event-stream) one delta, then the finish with its usage, then [DONE]:
  a request whose messages ask to "use the tool" and hold no tool result yet: a nested_work tool
      call, usage 100 in, 20 out
  a qc brief (scripts/octo-feather-qc BRIEF: "Repo: ..., head SHA."): every criterion it names
      passes, as the judge's JSON, usage 150 in, 10 out
  else the answer TEXT (default fake-done), usage 150 in, 10 out
"""

from __future__ import annotations

import argparse
import http.server
import json
import re
import sys
from typing import Any


def reply(msgs: list[dict[str, Any]], answer: str) -> tuple[dict[str, Any], str, dict[str, int]]:
    """The delta, finish reason and usage answering a request's messages (the header's rules)."""
    text = json.dumps(msgs)
    usage = {"prompt_tokens": 150, "completion_tokens": 10, "total_tokens": 160}
    if "use the tool" in text and not any(m.get("role") == "tool" for m in msgs):
        call = {"name": "nested_work", "arguments": "{}"}
        tool = {"index": 0, "id": "call_1", "type": "function", "function": call}
        usage = {"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120}
        return {"role": "assistant", "tool_calls": [tool]}, "tool_calls", usage
    if qc := re.search(r"Repo: .*, head ([0-9a-f]{40})\.", text):
        ids = re.findall(r"\\n- (acceptance-[a-z0-9-]+): ", text)
        crit = [
            {"id": i, "verdict": "pass", "command": "demo", "output": "ok", "why": "shown"}
            for i in ids
        ]
        answer = "```json\n" + json.dumps({"head": qc.group(1), "criteria": crit}) + "\n```"
    return {"role": "assistant", "content": answer}, "stop", usage


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--log")
    ap.add_argument("--answer", default="fake-done")
    a = ap.parse_args()
    log: str | None = a.log

    class H(http.server.BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: Any) -> None:  # noqa: A002, ANN401
            pass

        def do_POST(self) -> None:
            body = self.rfile.read(int(self.headers.get("content-length", 0)))
            if log:
                with open(log, "a") as f:  # noqa: PTH123
                    f.write(json.dumps(json.loads(body)) + "\n")
            self.send_response(200)
            self.send_header("content-type", "text/event-stream")
            self.end_headers()
            base = {"id": "x", "object": "chat.completion.chunk", "created": 0, "model": "fake"}
            delta, stop, usage = reply(json.loads(body).get("messages", []), a.answer)
            for d, end in ((delta, None), ({}, stop)):
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
