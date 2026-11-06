#!/usr/bin/env -S python3 -I -S
"""Fake `herdr` (the testkit's stand-in for Herdr, which the kit does not own), as
tests/lib/qa.sh's: a session's socket is a file under the config dir naming the session.

`server` writes it and sleeps; `session stop S` removes S's socket, `session delete S` its dir;
with no socket a call fails `server_not_running`; `pane list` prints nothing; `agent list` prints
no agent in Herdr's envelope (as tests/fixtures/lane-report/herdr); any other call prints
{"session": S}.

Started light (-I -S, only os and sys imported up front): a qc run calls it dozens of times, and
each start is CPU the item pays (#672).
"""

import os
import sys

home = os.path.join(
    os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config"), "herdr"
)
session, a = "default", list[str]()
it = iter(sys.argv[1:])
for x in it:
    if x == "--session":
        session = next(it, "default")
    elif x in ("--remote", "--machine"):
        next(it, None)
    else:
        a.append(x)
sock = (
    os.path.join(home, "herdr.sock")
    if session == "default"
    else os.path.join(home, "sessions", session, "herdr.sock")
)
if a == ["server"]:
    os.makedirs(os.path.dirname(sock), exist_ok=True)
    with open(sock, "w") as f:
        f.write(session + "\n")
    os.execvp("sleep", ["sleep", "600"])  # noqa: S606, S607
if a[:2] == ["session", "stop"] and len(a) == 3:
    try:
        os.unlink(os.path.join(home, "sessions", a[2], "herdr.sock"))
    except FileNotFoundError:
        pass
    sys.exit(0)
if a[:2] == ["session", "delete"] and len(a) == 3:
    import shutil

    shutil.rmtree(os.path.join(home, "sessions", a[2]), ignore_errors=True)
    sys.exit(0)
if not os.path.isfile(sock):
    sys.exit("server_not_running")
if a == ["agent", "list"]:
    sys.stdout.write('{"id": "1", "result": {"agents": []}}\n')
elif a != ["pane", "list"]:
    with open(sock) as f:
        name = f.read().strip()
    if '"' in name or "\\" in name or not (name.isascii() and name.isprintable()):
        import json

        sys.stdout.write(json.dumps({"session": name}) + "\n")
    else:  # as json.dumps writes it, without its import
        sys.stdout.write(f'{{"session": "{name}"}}\n')
