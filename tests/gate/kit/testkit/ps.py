#!/usr/bin/env python3
"""Stand-in for macOS `ps` (the OS, which the kit does not own), put first on PATH by a scenario
itself (testkit's docstring) inside a mount namespace whose /proc is covered, as on macOS: `ps
-Aww -o pid=,uid=,args=` as macOS prints it, each process's args joined by spaces. Its rows are
the scenario's own processes only, planted in the file FAKE_PS_ROWS, one "PID ARGS" line each (a
process the scenario started, or a server its own register started, as its record names it), each
owned by the caller's user, as ps sees it (its own uid: inside a user namespace, the mapped one);
it never reads /proc or any other process. First it prints the odd lines a busy box yields: a
blank line, and its own pid and uid with no args. A missing FAKE_PS_ROWS fails naming it."""

import os
import sys
from pathlib import Path

rows = Path(os.environ["FAKE_PS_ROWS"])
if not rows.is_file():
    sys.exit(f"testkit ps: no planted rows: no file {rows} (FAKE_PS_ROWS)")
uid = os.getuid()
lines = [
    f"{pid} {uid} {args}"
    for pid, _, args in (r.partition(" ") for r in rows.read_text().splitlines())
]
sys.stdout.write("\n".join(["", f"{os.getpid()} {uid}", *lines]) + "\n")
