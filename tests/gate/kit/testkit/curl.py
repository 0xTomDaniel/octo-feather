#!/usr/bin/env -S python3 -S
"""Fake `curl` for OpenRouter (the testkit's stand-in for OpenRouter, which the kit does not
own), put first on PATH as `curl` by a scenario itself (testkit's docstring): a recording,
never a simulator (the tdd skill, mocking.md). It appends its argv, one line, to
$FAKE_CURL_DIR/argv, and reads the request from its argv and the --config on stdin: `GET URL
HEADER`, HEADER the config's one `header = "..."` line's value. $FAKE_CURL_DIR/tape.json maps
each request to its recorded answer:

  {"status": "200", "body": FILE}   FILE's bytes as OpenRouter sent them (tests/fixtures/
                                    openrouter-key/: 200.json and 401.json, recorded with real
                                    curl from GET https://openrouter.ai/api/v1/key, a real key
                                    and a wrong one, 2026-11-07; in 200.json the account's label,
                                    creator_user_id and workspace_id values replaced by REDACTED,
                                    nothing else), then what -w '\\n%{http_code}' prints;
  {"connect": "127.0.0.1:PORT"}     the real curl (the next on PATH) run with the same argv and
                                    stdin, connected to that local port instead (--connect-to):
                                    a port nothing listens on is a real refused connection.

A request no recording names, or a -w other than '\\n%{http_code}', exits 2 naming it.
"""

import json
import os
import subprocess
import sys

# ruff: noqa: PTH100, PTH118, PTH120, PTH123 (os.path, not pathlib: a light start)
d = os.environ.get("FAKE_CURL_DIR") or sys.exit("fake curl: FAKE_CURL_DIR unset")
a = sys.argv[1:]
with open(os.path.join(d, "argv"), "a") as f:
    f.write(" ".join(a) + "\n")
cfg = sys.stdin.read()
header = next((x.split('"')[1] for x in cfg.splitlines() if x.startswith("header = ")), "")
req = f"GET {a[-1]} {header}"
with open(os.path.join(d, "tape.json")) as f:
    tape: dict[str, dict[str, str]] = json.load(f)
ans = tape.get(req)
if ans is None:
    sys.exit(f"fake curl: no recording for {req.split(' Authorization', 1)[0]} (tape.json)")
if "connect" in ans:
    here = os.path.dirname(os.path.abspath(sys.argv[0]))
    path = [x for x in os.environ["PATH"].split(os.pathsep) if os.path.abspath(x) != here]
    real = next(
        (os.path.join(x, "curl") for x in path if os.access(os.path.join(x, "curl"), os.X_OK)), ""
    )
    if not real:
        sys.exit("fake curl: no real curl on PATH after the stand-in")
    host = a[-1].split("/")[2]
    to = ["--connect-to", f"{host}:443:{ans['connect']}"]
    sys.exit(subprocess.run([real, *to, *a], input=cfg, text=True, check=False).returncode)
if "-w" in a and a[a.index("-w") + 1] != "\n%{http_code}":
    sys.exit(f"fake curl: -w {a[a.index('-w') + 1]!r} is not the recorded form")
with open(ans["body"], "rb") as f:
    sys.stdout.buffer.write(f.read())
sys.stdout.write("\n" + ans["status"] if "-w" in a else "")
