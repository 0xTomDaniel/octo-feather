#!/usr/bin/env python3
"""Fake `herdr` (the testkit's stand-in for Herdr, which the kit does not own), as
tests/lib/qa.sh's: a session's socket is a file under the config dir naming the session.

`server` writes it and sleeps; `session stop S` removes S's socket, `session delete S` its dir;
with no socket a call fails `server_not_running`; `pane list` prints nothing; any other call
prints {"session": S}.
"""

import json
import os
import shutil
import sys
from pathlib import Path

home = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "herdr"
session, a = "default", list[str]()
it = iter(sys.argv[1:])
for x in it:
    if x == "--session":
        session = next(it, "default")
    elif x in ("--remote", "--machine"):
        next(it, None)
    else:
        a.append(x)
sock = home / "herdr.sock" if session == "default" else home / "sessions" / session / "herdr.sock"
if a == ["server"]:
    sock.parent.mkdir(parents=True, exist_ok=True)
    sock.write_text(session + "\n")
    os.execvp("sleep", ["sleep", "600"])  # noqa: S606, S607
if a[:2] == ["session", "stop"] and len(a) == 3:
    (home / "sessions" / a[2] / "herdr.sock").unlink(missing_ok=True)
    sys.exit(0)
if a[:2] == ["session", "delete"] and len(a) == 3:
    shutil.rmtree(home / "sessions" / a[2], ignore_errors=True)
    sys.exit(0)
if not sock.is_file():
    sys.exit("server_not_running")
if a != ["pane", "list"]:
    sys.stdout.write(json.dumps({"session": sock.read_text().strip()}) + "\n")
