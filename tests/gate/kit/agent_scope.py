"""Every agent runs in its own systemd user scope, and plain herdr-close ends only the closed
panes' scopes (#1000; owner ruling 2026-11-14, #739), end to end against the box's real systemd
user manager (the scope is what this proves), through the commands with the testkit's Herdr
stand-in (testkit/herdr.py, its FAKE_HERDR world) and real processes standing in for agents.

herdr-spawn adopts the new pane's shell into octo-feather-agent-PANE-N.scope before it starts
Pi; with no reachable user manager it refuses, exit 69, naming the need and busctl's own
failure, the tab closed. `herdr-close w1:t1` over an owned pane whose Pi already exited (its
shell and a detached, reparented job left in its scope) prints `tab=w1:t1 tab_close_rc=0
killed=N` and the job is gone, while a process outside any scope tagged HERDR_TAB_ID=w1:t1 of
the same session lives on: herdr-close reads no environ. Each scope a scenario makes is stopped
when it ends, pass or fail."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING

from testkit import ROOT, Scratch, main

if TYPE_CHECKING:
    from collections.abc import Mapping

ASSETS = ROOT / ".agents" / "skills" / "herdr-comms" / "assets"


def world(s: Scratch, agents: Mapping[str, Mapping[str, object]]) -> Path:
    """S's Herdr world holding AGENTS, the caller's Herdr and kit vars cleared, and the box's
    real busctl and systemctl first (not the testkit's systemd stand-ins)."""
    d = s.root / "herdr"
    d.mkdir()
    (d / "agents.json").write_text(json.dumps(agents))
    for k in [k for k in s.env if k.startswith(("HERDR_", "OCTO_FEATHER_"))]:
        del s.env[k]
    s.env["FAKE_HERDR"] = str(d)
    for name in ("busctl", "systemctl"):
        (s.bin / name).unlink(missing_ok=True)
    return d


def show(line: str) -> None:
    """One observation on stdout, for the qc demo's output."""
    sys.stdout.write(line + "\n")


def scope_of(pid: int) -> str:
    """PID's cgroup (its scope's path), or '' once it is gone."""
    try:
        return next(
            x[3:]
            for x in Path(f"/proc/{pid}/cgroup").read_text().splitlines()
            if x.startswith("0::")
        )
    except (OSError, StopIteration):
        return ""


def stop(*cgroups: str) -> None:
    """The scopes at CGROUPS stopped, any still there."""
    for cg in cgroups:
        if cg.endswith(".scope"):
            subprocess.run(
                ["systemctl", "--user", "stop", cg.rsplit("/", 1)[1]],  # noqa: S607
                check=False,
                capture_output=True,
            )


def alive(pid: int) -> bool:
    """PID runs (a zombie, ended but unreaped, does not)."""
    try:
        return Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[0] != "Z"
    except OSError:
        return False


def gone(pid: int) -> bool:
    for _ in range(100):
        if not alive(pid):
            return True
        time.sleep(0.05)
    return False


def spawn_scoped(s: Scratch) -> None:
    """herdr-spawn adopts the pane's shell into its own user scope before Pi starts."""
    d = world(s, {})
    s.identity()
    wt = s.root / "wt"
    wt.mkdir()
    spawn = [str(ASSETS / "herdr-spawn"), "--workspace", "w1", "--name", "implementer-gh1"]
    ran = s.run([*spawn, "--role", "implementer", "--cwd", str(wt)])
    got = dict(x.split("=", 1) for x in ran.out.split())
    shell = int(json.loads((d / "agents.json").read_text())[got["pane"]]["shell_pid"])
    cg = scope_of(shell)
    try:
        assert f"/octo-feather-agent-{got['pane']}-" in cg, cg
        assert cg.endswith(".scope"), cg
        log = (d / "log").read_text().splitlines()
        assert log.index(f"pane process-info --pane {got['pane']}") < next(
            i for i, x in enumerate(log) if x.startswith("agent start ")
        ), log
        show(f"herdr-spawn: pane {got['pane']} shell {shell} in {cg}")
    finally:
        stop(cg)


def spawn_no_manager(s: Scratch) -> None:
    """No reachable user manager: exit 69 naming the need and busctl's failure, tab closed."""
    d = world(s, {})
    s.identity()
    wt = s.root / "wt"
    wt.mkdir()
    s.env.pop("DBUS_SESSION_BUS_ADDRESS", None)
    s.env["XDG_RUNTIME_DIR"] = str(s.root / "no-runtime")
    spawn = [str(ASSETS / "herdr-spawn"), "--workspace", "w1", "--name", "implementer-gh1"]
    err = s.run([*spawn, "--role", "implementer", "--cwd", str(wt)], want=69).err
    for named in ("systemd user manager", "loginctl enable-linger", "busctl: "):
        assert named in err, err
    log = (d / "log").read_text().splitlines()
    assert "tab close w1:t1" in log, log
    assert not any(x.startswith("agent start ") for x in log), log
    assert json.loads((d / "agents.json").read_text()) == {}
    show(f"herdr-spawn with no user manager: exit 69: {err.splitlines()[-1]}")


def close_owned(s: Scratch) -> None:
    """The demo: `herdr-close w1:t1` over an owned pane whose Pi exited ends its detached job;
    a foreign process tagged with w1:t1 survives."""
    unit = f"octo-feather-agent-w1:p1-{os.getpid()}-{time.time_ns()}.scope"
    # The pane's shell in its scope; it detached a job (its own session, reparented), and its Pi
    # already exited. systemd-run execs the shell, so its pid is the shell's.
    job_file = s.root / "job"
    detach = '(setsid sleep 300 </dev/null >/dev/null 2>&1 & echo $! >"$0"); exec sleep 300'
    run = ["systemd-run", "--user", "--scope", "--quiet", "--collect", "--unit", unit]
    shell = subprocess.Popen([*run, "sh", "-c", detach, str(job_file)])
    tag = {"HERDR_TAB_ID": "w1:t1", "HERDR_WORKSPACE_ID": "w1", "HERDR_PANE_ID": "w1:p1"}
    foreign = subprocess.Popen(["sleep", "300"], env=s.env | tag, start_new_session=True)  # noqa: S607
    cg = ""
    try:
        for _ in range(100):
            if job_file.is_file() and job_file.read_text().strip():
                break
            time.sleep(0.05)
        job = int(job_file.read_text())
        cg = scope_of(shell.pid)
        assert cg.endswith(f"/{unit}"), cg
        assert scope_of(job) == cg, (scope_of(job), cg)
        pane = {"name": "", "pane_id": "w1:p1", "workspace_id": "w1", "tab_id": "w1:t1"}
        world(s, {"w1:p1": pane | {"agent_status": "none", "shell_pid": shell.pid}})
        out = s.run([str(ASSETS / "herdr-close"), "w1:t1"]).out
        show(f"herdr-close w1:t1: {out}")
        head, killed = out.rsplit(" killed=", 1)
        assert head == "tab=w1:t1 tab_close_rc=0", out
        assert killed.isdigit(), out
        assert int(killed) >= 1, out
        assert gone(job), f"the agent's detached job {job} still runs"
        assert alive(foreign.pid), "the foreign tagged process was ended"
    finally:
        foreign.kill()
        shell.kill()
        stop(cg or f"/{unit}")


def close_unowned(s: Scratch) -> None:
    """An unowned pane (its shell in no agent scope): closed, nothing swept, named unowned=."""
    tag = {"HERDR_TAB_ID": "w1:t1", "HERDR_WORKSPACE_ID": "w1", "HERDR_PANE_ID": "w1:p1"}
    shell = subprocess.Popen(["sleep", "300"], env=s.env | tag, start_new_session=True)  # noqa: S607
    try:
        pane = {"name": "", "pane_id": "w1:p1", "workspace_id": "w1", "tab_id": "w1:t1"}
        d = world(s, {"w1:p1": pane | {"agent_status": "none", "shell_pid": shell.pid}})
        out = s.run([str(ASSETS / "herdr-close"), "w1:t1"]).out
        assert out == "tab=w1:t1 tab_close_rc=0 killed=0 unowned=w1:p1", out
        assert "tab close w1:t1" in (d / "log").read_text().splitlines()
        show(f"herdr-close w1:t1 over an unowned pane: {out}")
    finally:
        shell.kill()


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))
    main(spawn_scoped, spawn_no_manager, close_owned, close_unowned)
