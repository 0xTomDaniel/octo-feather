#!/usr/bin/env -S python3 -I -S
"""Fake `herdr` (the testkit's stand-in for Herdr, which the kit does not own), as
tests/lib/qa.sh's: a session's socket is a file under the config dir naming the session.

`server` writes it and sleeps; `session stop S` removes S's socket, `session delete S` its dir;
with no socket a call fails `server_not_running`; `agent list` prints no agent in Herdr's envelope
(as tests/fixtures/lane-report/herdr); one pane per workspace (as tests/lib/qc.sh's): `workspace
create` answers root pane w1:p1, `pane run P CMD...` starts CMD detached (as the server would) and
logs {"pane_id": P} beside the socket, which `pane list` prints (nothing before a run); any other
call prints {"session": S}.

Started light (-I -S, only os and sys imported up front): a qc run calls it dozens of times, and
each start is CPU the item pays (#672): pathlib's import alone costs more than the rest of a call.
"""
# ruff: noqa: PTH103, PTH108, PTH111, PTH113, PTH118, PTH120, PTH123  # os.path, not pathlib: above

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
    stale = os.path.join(home, "sessions", a[2], "herdr.sock")
    if os.path.lexists(stale):
        os.unlink(stale)
    sys.exit(0)
if a[:2] == ["session", "delete"] and len(a) == 3:
    import shutil

    shutil.rmtree(os.path.join(home, "sessions", a[2]), ignore_errors=True)
    sys.exit(0)
if not os.path.isfile(sock):
    sys.exit("server_not_running")
panes = os.path.join(os.path.dirname(sock), "panes")
if a[:2] == ["workspace", "create"]:
    sys.stdout.write('{"result":{"root_pane":{"pane_id":"w1:p1"}}}\n')
    sys.exit(0)
if a[:2] == ["pane", "run"] and len(a) > 3:
    with open(panes, "a") as f:
        f.write(f'{{"pane_id":"{a[2]}"}}\n')
    import subprocess

    subprocess.Popen(
        ["setsid", "sh", "-c", " ".join(a[3:])],  # noqa: S607
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    sys.exit(0)
if a == ["pane", "list"]:
    if os.path.isfile(panes):
        with open(panes) as f:
            sys.stdout.write(f.read())
elif a == ["agent", "list"]:
    sys.stdout.write('{"id": "1", "result": {"agents": []}}\n')
else:
    with open(sock) as f:
        name = f.read().strip()
    if '"' in name or "\\" in name or not (name.isascii() and name.isprintable()):
        import json

        sys.stdout.write(json.dumps({"session": name}) + "\n")
    else:  # as json.dumps writes it, without its import
        sys.stdout.write(f'{{"session": "{name}"}}\n')
