#!/usr/bin/env python3
"""Stand-in for the box's systemd user manager (which the kit does not own), answering as
`busctl`, `systemctl` or `systemd-run` by the name it runs under, for tests that spawn, close or
park an agent but do not prove its scope (that is end to end: tests/gate/kit/agent_scope.py, the
real manager), or start a transient unit.

busctl: a `--user call ... StartTransientUnit ...` is queued, as systemd answers it (the job's
object path). systemctl: `--user is-active [-q] UNIT` reads every unit active; `--user stop UNIT`
succeeds; `--user is-system-running` prints `running` (with FAKE_SYSTEMD_OFFLINE set, `offline`,
exit 1: no manager answers). Any other call fails (exit 1, naming it). With FAKE_SYSTEMD_LOG set,
each call is appended there first, one line of its name and args, so a test can assert one never
happened.

systemd-run (not in testkit FAKES: agent_scope.py runs the real one; a scenario links it itself):
`--user [--quiet] [--collect] --unit=U [--working-directory=D] [-p K=V]... [--setenv=K=V]... --
CMD...` returns at once, as systemd queues a transient service, and the unit runs detached (its
own session): CMD in D with only the --setenv environment (a unit never inherits its starter's),
its stdout and stderr appended to the file `-p StandardOutput=append:F` names, killed past `-p
RuntimeMaxSec=N`; then its `-p ExecStopPost=` command line, as systemd runs a stop hook after any
end, with SERVICE_RESULT (success, exit-code, timeout), EXIT_CODE (exited, killed) and EXIT_STATUS
(the exit status or the signal) set. FAKE_SYSTEMD_KILLED set in systemd-run's environment: CMD
outlives its runtime limit, so the unit is killed at its limit (the stand-in runs no CMD; result
timeout, killed TERM). With FAKE_SYSTEMD_LOG set, each unit's end is logged there too (`unit U
ended RESULT`), after its hook.
"""

import json
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import TypedDict, cast


class Spec(TypedDict):
    """One unit as systemd-run was asked for it."""

    unit: str
    cmd: list[str]
    cwd: str
    props: dict[str, str]
    env: dict[str, str]
    killed: bool
    log: str


name, a = Path(sys.argv[0]).name, sys.argv[1:]


def note(line: str) -> None:
    if log := os.environ.get("FAKE_SYSTEMD_LOG"):
        with Path(log).open("a") as f:
            f.write(line + "\n")


def start(a: list[str]) -> None:
    """systemd-run --user ... -- CMD: the unit, its spec to a detached runner (this file)."""
    cut = a.index("--")
    opts, cmd = a[:cut], a[cut + 1 :]
    unit, cwd = "", "/"
    props, env = dict[str, str](), dict[str, str]()
    it = iter(opts[1:])
    for x in it:
        if x == "-p":
            k, _, v = next(it).partition("=")
            props[k] = v
        elif x.startswith("--setenv="):
            k, _, v = x.removeprefix("--setenv=").partition("=")
            env[k] = v
        elif x.startswith("--unit="):
            unit = x.removeprefix("--unit=")
        elif x.startswith("--working-directory="):
            cwd = x.removeprefix("--working-directory=")
        elif x not in ("--quiet", "--collect"):
            sys.exit(f"systemd stand-in: unhandled: systemd-run option {x}")
    killed = bool(os.environ.get("FAKE_SYSTEMD_KILLED"))
    log = os.environ.get("FAKE_SYSTEMD_LOG", "")
    spec = Spec(unit=unit, cmd=cmd, cwd=cwd, props=props, env=env, killed=killed, log=log)
    io = subprocess.DEVNULL
    runner = [sys.executable, str(Path(__file__).resolve()), "--run-unit", json.dumps(spec)]
    subprocess.Popen(runner, stdin=io, stdout=io, stderr=io, start_new_session=True)


def run_unit(spec: Spec) -> None:
    """The detached unit (start's docstring)."""
    props, env, cwd = spec["props"], spec["env"], spec["cwd"]
    out_to = props.get("StandardOutput", "").removeprefix("append:")
    with Path(out_to or os.devnull).open("a") as out:
        if spec["killed"]:
            result, code, status = "timeout", "killed", "TERM"
        else:
            cmd = spec["cmd"]
            limit = float(props.get("RuntimeMaxSec", "0") or 0) or None
            io = subprocess.DEVNULL
            p = subprocess.Popen(cmd, cwd=cwd, env=env, stdin=io, stdout=out, stderr=out)
            try:
                rc = p.wait(limit)
                result, code, status = ("success" if rc == 0 else "exit-code"), "exited", str(rc)
            except subprocess.TimeoutExpired:
                p.terminate()
                p.wait()
                result, code, status = "timeout", "killed", "TERM"
        hook = props.get("ExecStopPost")
        if hook:
            ended = {"SERVICE_RESULT": result, "EXIT_CODE": code, "EXIT_STATUS": status}
            subprocess.run(
                shlex.split(hook),
                cwd=cwd,
                env=env | ended,
                stdin=subprocess.DEVNULL,
                stdout=out,
                stderr=out,
                check=False,
            )
    if spec["log"]:
        with Path(spec["log"]).open("a") as f:
            f.write(f"unit {spec['unit']} ended {result}\n")


if a[:1] == ["--run-unit"]:
    run_unit(cast("Spec", json.loads(a[1])))
    sys.exit(0)
note(" ".join([name, *a]))
if name == "busctl" and a[:2] == ["--user", "call"] and "StartTransientUnit" in a:
    sys.stdout.write('o "/org/freedesktop/systemd1/job/1"\n')
elif name == "systemctl" and a[:2] in (["--user", "is-active"], ["--user", "stop"]):
    pass
elif name == "systemctl" and a == ["--user", "is-system-running"]:
    offline = bool(os.environ.get("FAKE_SYSTEMD_OFFLINE"))
    sys.stdout.write("offline\n" if offline else "running\n")
    sys.exit(1 if offline else 0)
elif name == "systemd-run" and a[:1] == ["--user"] and "--" in a:
    start(a)
else:
    sys.exit(f"systemd stand-in: unhandled: {name} {' '.join(a)}")
