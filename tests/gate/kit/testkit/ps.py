#!/usr/bin/env python3
"""Stand-in for macOS `ps` (the OS, which the kit does not own), put first on PATH by a scenario
itself (testkit's docstring) inside a mount namespace whose /proc is covered, as on macOS: `ps
-Aww -o pid=,uid=,args=` as macOS prints it, each process's args joined by spaces, read from the
real /proc bound aside at FAKE_PS_PROC (as macOS ps reads the kernel). It also prints the odd lines
a busy box yields: a blank line, and its own pid and uid with no args. Only an e2e scenario runs it
(tests/gate/kit/review_host.py: the no-/proc case), as the real process table is its input."""

import os
import sys
from pathlib import Path

proc = Path(os.environ["FAKE_PS_PROC"])
out = ["", f"{os.getpid()} {os.getuid()}"]
for d in proc.iterdir():
    if not d.name.isdigit():
        continue
    try:
        argv = (d / "cmdline").read_bytes().rstrip(b"\0").split(b"\0")
        uid = d.stat().st_uid
    except OSError:
        continue
    if argv != [b""]:
        out.append(f"{d.name} {uid} {b' '.join(argv).decode(errors='replace')}")
sys.stdout.write("\n".join(out) + "\n")
