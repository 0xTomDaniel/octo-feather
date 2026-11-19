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
when it ends, pass or fail. A pane whose shell sits in a scope adopt did not name for that pane
(close_foreign, park_foreign: a probe scope octo-feather-agent-probe-<hex>.scope, a name no
agent has) is unowned: that scope is never stopped nor its members listed (#1070).

`herdr-close --park w1:p1` (#1001), the rule herdr-comms SKILL.md, Park an idle agent, states:
park_owned (the demo), park_unowned, park_refused and park_malformed drive it."""

from __future__ import annotations

import json
import os
import secrets
import subprocess
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING, cast

from testkit import ROOT, Scratch, main

if TYPE_CHECKING:
    from collections.abc import Mapping

ASSETS = ROOT / ".agents" / "skills" / "herdr-comms" / "assets"


def world(s: Scratch, agents: Mapping[str, Mapping[str, object]]) -> Path:
    """S's Herdr world holding AGENTS, the caller's Herdr and kit vars cleared, and the box's
    real busctl and systemctl first (not the testkit's systemd stand-ins)."""
    d = s.root / "herdr"
    d.mkdir(exist_ok=True)
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


def active(unit: str) -> bool:
    """UNIT is active under the user's manager."""
    is_active = ["systemctl", "--user", "is-active", "-q", unit]
    return subprocess.run(is_active, check=False).returncode == 0


def probe(s: Scratch) -> tuple[str, int, int]:
    """A probe scope (a unit name no agent has) holding a pane's shell and a detached job, as an
    agent's scope holds its shell and Pi: its unit, the shell's pid (systemd-run execs it) and
    the job's. The job keeps the scope active once the closed tab's shell is hung up."""
    unit = f"octo-feather-agent-probe-{secrets.token_hex(4)}.scope"
    job_file = s.root / "job"
    detach = '(setsid sleep 300 </dev/null >/dev/null 2>&1 & echo $! >"$0"); exec sleep 300'
    run = ["systemd-run", "--user", "--scope", "--quiet", "--collect", "--unit", unit]
    shell = subprocess.Popen([*run, "sh", "-c", detach, str(job_file)])
    job = read_pid(job_file)
    assert scope_of(job) == scope_of(shell.pid), (scope_of(job), scope_of(shell.pid))
    assert scope_of(job).endswith(f"/{unit}"), scope_of(job)
    return unit, shell.pid, job


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
    unit = f"octo-feather-agent-w1:p1-{secrets.token_hex(4)}.scope"  # as adopt names it
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


def close_foreign(s: Scratch) -> None:
    """`herdr-close w1:t1` over a pane whose shell sits in a probe scope (not w1:p1's own): the
    probe still runs, the pane named unowned= (#1070: an agent running the kit's tests)."""
    unit, shell, job = probe(s)
    try:
        pane = {"name": "", "pane_id": "w1:p1", "workspace_id": "w1", "tab_id": "w1:t1"}
        world(s, {"w1:p1": pane | {"agent_status": "none", "shell_pid": shell}})
        out = s.run([str(ASSETS / "herdr-close"), "w1:t1"]).out
        show(f"herdr-close w1:t1 over a pane in {unit}: {out}")
        assert out == "tab=w1:t1 tab_close_rc=0 killed=0 unowned=w1:p1", out
        assert active(unit), f"{unit} was stopped"
        assert alive(job), "close ended a job in a scope not the pane's own"
    finally:
        stop(f"/{unit}")


PI = ["python3", "-c", "import time; time.sleep(300)"]  # a stand-in Pi: argv as herdr-spawn's
PANE = {"name": "implementer-gh1", "pane_id": "w1:p1", "workspace_id": "w1", "tab_id": "w1:t1"}
PANE["label"] = "gh1"
PEER = {"name": "gh1", "pane_id": "w1:p9", "workspace_id": "w1", "tab_id": "w1:t9"}
TAB_ENV = {"OCTO_FEATHER_ROLE": "implementer", "OCTO_FEATHER_PARENT": "w1:p9"}


def read_pid(f: Path) -> int:
    for _ in range(100):
        if f.is_file() and f.read_text().strip():
            return int(f.read_text())
        time.sleep(0.05)
    msg = f"no pid in {f}"
    raise AssertionError(msg)


def foreign(s: Scratch) -> subprocess.Popen[bytes]:
    """A process outside any scope tagged as pane w1:p1's agent, with its own session."""
    tag = {"HERDR_TAB_ID": "w1:t1", "HERDR_WORKSPACE_ID": "w1", "HERDR_PANE_ID": "w1:p1"}
    tag |= {"OCTO_FEATHER_SESSION_ID": "foreign", "OCTO_FEATHER_ROLE": "foreign"}
    return subprocess.Popen(["sleep", "300"], env=s.env | tag, start_new_session=True)  # noqa: S607


def park(s: Scratch, want: int = 0) -> tuple[str, str]:
    ran = s.run([str(ASSETS / "herdr-close"), "--park", "w1:p1"], want=want)
    return ran.out, ran.err


def parked_ok(line: str, wt: Path) -> dict[str, str]:
    got = cast("dict[str, str]", json.loads(line))
    want = {"kind": "parked", "pane": "w1:p1", "name": "implementer-gh1", "role": "implementer"}
    want |= {"parent": "w1:p9", "cwd": str(wt.resolve()), "session": "S1", "label": "gh1"}
    assert {k: got.get(k) for k in want} == want, got
    return got


def park_owned(s: Scratch) -> None:
    """The demo: `herdr-close --park w1:p1` over an owned idle agent with a background job in
    its scope, then again once the job ended, then herdr-say to its name."""
    unit = f"octo-feather-agent-w1:p1-{secrets.token_hex(4)}.scope"  # as adopt names it
    wt = s.root / "wt"
    wt.mkdir()
    pi_file, job_file = s.root / "pi", s.root / "job"
    # The pane's shell in its scope, its Pi started in WT under the tab's env, and a detached job.
    script = 'cd "$0"; p=$1 j=$2; shift 2; "$@" & echo $! >"$p"'
    script += '; (setsid sleep 300 </dev/null >/dev/null 2>&1 & echo $! >"$j"); exec sleep 300'
    run = ["systemd-run", "--user", "--scope", "--quiet", "--collect", "--unit", unit]
    world(s, {})
    env = s.env | TAB_ENV | {"OCTO_FEATHER_SESSION_ID": "S1"}
    args = [*run, "sh", "-c", script, str(wt), str(pi_file), str(job_file)]
    shell = subprocess.Popen([*args, *PI, "--session-id", "S1"], env=env)
    other = foreign(s)
    cg = ""
    resumed = ""
    try:
        pi, job = read_pid(pi_file), read_pid(job_file)
        cg = scope_of(shell.pid)
        assert cg.endswith(f"/{unit}"), cg
        assert scope_of(job) == cg, (scope_of(job), cg)
        agents = {"w1:p1": PANE | {"agent_status": "idle", "shell_pid": shell.pid, "pi_pid": pi}}
        d = world(s, agents | {"w1:p9": PEER | {"agent_status": "idle"}})
        out, err = park(s, 75)
        show(f"herdr-close --park w1:p1 with a background job: exit 75: {err.strip()}")
        assert not out, out
        assert [x for x in err.splitlines() if x.startswith("  ")] == [f"  {job} sleep 300"], err
        assert not any("close" in x for x in (d / "log").read_text().splitlines()), "closed"
        assert alive(job), "the refused park ended the job"
        os.kill(job, 9)
        assert gone(job), job
        out, err = park(s)
        show(f"herdr-close --park w1:p1 once the job ended: {out}")
        show(f"close report: {err.strip()}")
        line = parked_ok(out, wt)
        assert "tab close w1:t1" in (d / "log").read_text().splitlines()
        assert err.startswith("tab=w1:t1 tab_close_rc=0 killed="), err
        assert gone(pi), "Pi still runs"
        assert gone(shell.pid), "its scope still runs"
        assert alive(other.pid), "the foreign tagged process was ended"
        resumed = resume(s, d, line)
    finally:
        other.kill()
        shell.kill()
        stop(cg or f"/{unit}")
        if resumed:
            g = json.loads((s.root / "herdr" / "agents.json").read_text())[resumed]
            stop(scope_of(int(g["shell_pid"])))


def resume(s: Scratch, d: Path, line: dict[str, str]) -> str:
    """LINE in the director log: herdr-say to its name resumes it with its session; its pane."""
    state = s.home / ".local" / "state" / "octo-feather"
    state.mkdir(parents=True)
    (state / "director.handoffs.jsonl").write_text(json.dumps(line) + "\n")
    s.identity()
    said = s.run([str(ASSETS / "herdr-say"), "implementer-gh1", "go on"]).out
    resumed = said.removeprefix("pane=").split()[0]
    g = json.loads((d / "agents.json").read_text())[resumed]
    assert g["env"]["OCTO_FEATHER_SESSION_ID"] == "S1", g
    prompts = (d / "prompts").read_text().splitlines()
    assert prompts == [f"{resumed}\tResumed from park as pane={resumed}. go on"], prompts
    show(f"herdr-say implementer-gh1 go on: {said} (session S1)")
    return resumed


def park_unowned(s: Scratch) -> None:
    """`herdr-close --park w1:p1` over an unowned pane, a job and a foreign process beside it."""
    wt = s.root / "wt"
    wt.mkdir()
    world(s, {})
    env = s.env | TAB_ENV | {"OCTO_FEATHER_SESSION_ID": "S1"}
    shell = subprocess.Popen(["sleep", "300"], start_new_session=True)  # noqa: S607
    pi = subprocess.Popen([*PI, "--session-id", "S1"], cwd=wt, env=env, start_new_session=True)
    job = subprocess.Popen(["sleep", "300"], env=env, start_new_session=True)  # noqa: S607
    other = foreign(s)
    try:
        agent = PANE | {"agent_status": "done", "shell_pid": shell.pid, "pi_pid": pi.pid}
        world(s, {"w1:p1": agent} | {"w1:p9": PEER | {"agent_status": "idle"}})
        out, err = park(s)
        parked_ok(out, wt)
        assert err.strip() == "tab=w1:t1 tab_close_rc=0 killed=0 unowned=w1:p1", err
        assert alive(job.pid), "park swept a job beside an unowned pane"
        assert alive(other.pid), "the foreign tagged process was ended"
        show(f"herdr-close --park w1:p1 unowned: {out}; {err.strip()}")
    finally:
        for p in (shell, pi, job, other):
            p.kill()


def park_foreign(s: Scratch) -> None:
    """`herdr-close --park w1:p1` over an idle agent whose shell sits, with a job, in a probe
    scope (not w1:p1's own): parked, not refused for the job, the pane unowned=, the probe and
    its job still run."""
    wt = s.root / "wt"
    wt.mkdir()
    world(s, {})
    env = s.env | TAB_ENV | {"OCTO_FEATHER_SESSION_ID": "S1"}
    unit, shell, job = probe(s)
    pi = subprocess.Popen([*PI, "--session-id", "S1"], cwd=wt, env=env, start_new_session=True)
    try:
        agent = PANE | {"agent_status": "idle", "shell_pid": shell, "pi_pid": pi.pid}
        world(s, {"w1:p1": agent} | {"w1:p9": PEER | {"agent_status": "idle"}})
        out, err = park(s)
        show(f"herdr-close --park w1:p1 in {unit}: {out}; {err.strip()}")
        parked_ok(out, wt)
        assert err.strip() == "tab=w1:t1 tab_close_rc=0 killed=0 unowned=w1:p1", err
        assert active(unit), f"{unit} was stopped"
        assert alive(job), "park ended a job in a scope not the pane's own"
    finally:
        pi.kill()
        stop(f"/{unit}")


def park_refused(s: Scratch) -> None:
    """`herdr-close --park w1:p1` over a working agent, and over a Pi without --session-id."""
    world(s, {})
    env = s.env | TAB_ENV | {"OCTO_FEATHER_SESSION_ID": "S1"}
    pi = subprocess.Popen([*PI, "--session-id", "S1"], env=env, start_new_session=True)
    bare = subprocess.Popen(PI, env=s.env | TAB_ENV, start_new_session=True)
    try:
        for status, proc, want, how in (("working", pi, 75, "S1"), ("idle", bare, 65, "none")):
            agent = PANE | {"agent_status": status, "pi_pid": proc.pid}
            (s.root / status).mkdir()
            d = world(sub := Scratch(s.root / status), {"w1:p1": agent})
            err = sub.run([str(ASSETS / "herdr-close"), "--park", "w1:p1"], want=want).err
            assert not any("close" in x for x in (d / "log").read_text().splitlines()), err
            show(f"herdr-close --park w1:p1 ({status}, session {how}): exit {want}: {err.strip()}")
    finally:
        pi.kill()
        bare.kill()


def park_malformed(s: Scratch) -> None:
    """`herdr-close --park w1:p1` with Herdr's foreground cwd false, then argv 0 (malformed,
    falsey, not null)."""
    world(s, {})
    env = s.env | TAB_ENV | {"OCTO_FEATHER_SESSION_ID": "S1"}
    pi = subprocess.Popen([*PI, "--session-id", "S1"], env=env, start_new_session=True)
    try:
        for field, bad in (("cwd", "false"), ("argv", "0")):
            (s.root / field).mkdir()
            sub = Scratch(s.root / field)
            agent = PANE | {"agent_status": "idle", "pi_pid": pi.pid}
            d = world(sub, {"w1:p1": agent})
            fake = (sub.bin / "herdr").resolve()
            (sub.bin / "herdr").unlink()
            patch = f".result.process_info.foreground_processes[0].{field} = {bad}"
            wrap = f'if [ "$1 $2" = "pane process-info" ]; then "{fake}" "$@" | jq -c \'{patch}\''
            wrap += f'; else exec "{fake}" "$@"; fi\n'
            (sub.bin / "herdr").write_text("#!/bin/sh\n" + wrap)
            (sub.bin / "herdr").chmod(0o755)
            ran = sub.run([str(ASSETS / "herdr-close"), "--park", "w1:p1"], want=76)
            assert f"].{field}: not " in ran.err, ran.err
            assert not ran.out, ran.out
            assert not any("close" in x for x in (d / "log").read_text().splitlines()), ran.err
            show(f"herdr-close --park w1:p1 ({field} {bad}): exit 76: {ran.err.strip()}")
    finally:
        pi.kill()


PARK = (park_owned, park_unowned, park_foreign, park_refused, park_malformed)

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))
    main(spawn_scoped, spawn_no_manager, close_owned, close_unowned, close_foreign, *PARK)
