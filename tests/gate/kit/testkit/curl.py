#!/usr/bin/env -S python3 -S
"""Fake `curl` for OpenRouter's GET /api/v1/key (the testkit's stand-in for OpenRouter, which the
kit does not own), put first on PATH as `curl` by a scenario itself (testkit's docstring): it
appends its argv, one line, to $FAKE_CURL_DIR/argv, and reads the Bearer key from the --config
on stdin: sk-test-123 gets the usage windows (today 1.5, this week 2.5, this month 4.0), any other
key OpenRouter's 401, each body then the status, as `curl -w '\\n%{http_code}'` prints them. With
FAKE_CURL_EXIT set it fails as an unreachable host does, with that exit. Another URL exits 3.
"""

import os
import sys

URL = "https://openrouter.ai/api/v1/key"
d = os.environ.get("FAKE_CURL_DIR") or sys.exit("fake curl: FAKE_CURL_DIR unset")
with open(os.path.join(d, "argv"), "a") as f:  # noqa: PTH118, PTH123 (os.path: a light start)
    f.write(" ".join(sys.argv[1:]) + "\n")
cfg = sys.stdin.read().splitlines()
if os.environ.get("FAKE_CURL_EXIT"):
    sys.stderr.write("curl: (7) Failed to connect to openrouter.ai port 443\n")
    sys.exit(int(os.environ["FAKE_CURL_EXIT"]))
if sys.argv[-1] != URL:
    sys.stderr.write(f"fake curl: unexpected URL {sys.argv[-1]}\n")
    sys.exit(3)
if 'header = "Authorization: Bearer sk-test-123"' in cfg:
    usage = '"usage":9,"usage_daily":1.5,"usage_weekly":2.5,"usage_monthly":4.0'
    sys.stdout.write(f'{{"data":{{"label":"x",{usage}}}}}\n200')
else:
    sys.stdout.write('{"error":{"code":401}}\n401')
