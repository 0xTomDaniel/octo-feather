#!/usr/bin/env python3
"""Stand-in for the box's systemd user manager (which the kit does not own), answering as
`busctl` or `systemctl` by the name it runs under, for tests that spawn, close or park an agent
but do not prove its scope (that is end to end: tests/gate/kit/agent_scope.py, the real manager).

busctl: a `--user call ... StartTransientUnit ...` is queued, as systemd answers it (the job's
object path). systemctl: `--user is-active [-q] UNIT` reads every unit active; `--user stop UNIT`
succeeds. Any other call fails (exit 1, naming it). With FAKE_SYSTEMD_LOG set, each call is
appended there first, one line of its name and args, so a test can assert one never happened."""

import os
import sys
from pathlib import Path

name, a = Path(sys.argv[0]).name, sys.argv[1:]
if log := os.environ.get("FAKE_SYSTEMD_LOG"):
    with Path(log).open("a") as f:
        f.write(" ".join([name, *a]) + "\n")
if name == "busctl" and a[:2] == ["--user", "call"] and "StartTransientUnit" in a:
    sys.stdout.write('o "/org/freedesktop/systemd1/job/1"\n')
elif name == "systemctl" and a[:2] in (["--user", "is-active"], ["--user", "stop"]):
    pass
else:
    sys.exit(f"systemd stand-in: unhandled: {name} {' '.join(a)}")
