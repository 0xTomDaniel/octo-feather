#!/usr/bin/env python3
"""Stand-in for a model provider at Pi's provider boundary: an OpenAI-compatible chat completions
server on 127.0.0.1 (Pi's `openai-completions` api, a models.json provider whose baseUrl is
http://127.0.0.1:PORT/v1), the kit tests' one (tests/gate/kit, tests/lib/spend-ledger.sh).

  provider.py [--log FILE] [--answer TEXT]

Prints its port and a newline on stdout once it listens (the caller's readiness: read that line
off the pipe, or wait for the file it is sent to), then serves until killed. Each request body is
appended to FILE as one JSON line. Every answer streams (text/event-stream) one delta, then the
finish with its usage, then [DONE]:
  a request whose messages ask to "use the tool" and hold no tool result yet: a nested_work tool
      call, usage 100 in, 20 out
  a qc brief (scripts/octo-feather-qc BRIEF: "Repo: ..., head SHA."): every criterion it names
      passes, as the judge's JSON, usage 150 in, 10 out
  else TEXT (default fake-answer-ok), usage 150 in, 10 out
"""

from __future__ import annotations

import argparse
import http.server
import json
import re
import sys
from typing import Any


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--log")
    ap.add_argument("--answer", default="fake-answer-ok")
    a = ap.parse_args()

    class H(http.server.BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: Any) -> None:  # noqa: A002, ANN401
            pass

        def do_POST(self) -> None:
            body = json.loads(self.rfile.read(int(self.headers.get("content-length", 0))))
            if a.log:
                with open(a.log, "a") as f:  # noqa: PTH123
                    f.write(json.dumps(body) + "\n")
            msgs = json.dumps(body.get("messages", []))
            tool = "use the tool" in msgs and not any(
                m.get("role") == "tool" for m in body.get("messages", [])
            )
            qc = re.search(r"Repo: .*, head ([0-9a-f]{40})\.", msgs)
            usage = {"prompt_tokens": 150, "completion_tokens": 10, "total_tokens": 160}
            end = "stop"
            delta: dict[str, Any]
            if tool:
                call = {"name": "nested_work", "arguments": "{}"}
                delta = {
                    "role": "assistant",
                    "tool_calls": [
                        {"index": 0, "id": "call_1", "type": "function", "function": call}
                    ],
                }
                end = "tool_calls"
                usage = {"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120}
            elif qc:
                ids = re.findall(r"\\n- (acceptance-[a-z0-9-]+): ", msgs)
                crit = [
                    {"id": i, "verdict": "pass", "command": "demo", "output": "ok", "why": "shown"}
                    for i in ids
                ]
                judged = json.dumps({"head": qc.group(1), "criteria": crit})
                delta = {"role": "assistant", "content": f"```json\n{judged}\n```"}
            else:
                delta = {"role": "assistant", "content": a.answer}
            self.send_response(200)
            self.send_header("content-type", "text/event-stream")
            self.end_headers()
            base = {"id": "x", "object": "chat.completion.chunk", "created": 0, "model": "fake"}
            chunks: list[dict[str, Any]] = [
                {**base, "choices": [{"index": 0, "delta": delta, "finish_reason": None}]},
                {
                    **base,
                    "choices": [{"index": 0, "delta": {}, "finish_reason": end}],
                    "usage": usage,
                },
            ]
            for d in chunks:
                self.wfile.write(b"data: " + json.dumps(d).encode() + b"\n\n")
            self.wfile.write(b"data: [DONE]\n\n")

    s = http.server.HTTPServer(("127.0.0.1", 0), H)
    sys.stdout.write(f"{s.server_address[1]}\n")
    sys.stdout.flush()
    s.serve_forever()


if __name__ == "__main__":
    main()
