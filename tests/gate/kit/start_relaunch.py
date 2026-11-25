"""The director relaunch's refusals (comms spec #director-relaunch; #1310), through
`octo-feather-start` with the testkit's Herdr stand-in (testkit/herdr.py, its FAKE_HERDR world)
and real processes standing in for the director's shell and Pi.

A director at w0:p1 in workspace `director`, its Pi a herdr-spawn one on session D1, named by
director.toml. relaunch_busy: its turn outlasts `--relaunch --wait 1`: refused, exit 75, naming
the busy director. relaunch_own_scope: run by a detached job inside the director pane's agent
scope with no HERDR_PANE_ID, then with HERDR_PANE_ID w0:p1 from outside: refused, exit 64,
naming w0:p1 (end to end: the scope is the box's real systemd user manager's).
resume_same_session: `--director --resume D1` beside it: refused, exit 73, naming w0:p1. Each
leaves Herdr's world, director.toml and the director's Pi as they were: nothing parked, closed or
spawned."""

from __future__ import annotations

import json
import os
import secrets
import subprocess
import sys
import time
from pathlib import Path

from testkit import Scratch, kit, main

PI = ["python3", "-c", "import time; time.sleep(300)", "--session-id", "D1"]  # a stand-in Pi
TOML = 'pane = "w0:p1"\n'


def show(line: str) -> None:
    """One observation on stdout, for the qc demo's output."""
    sys.stdout.write(line + "\n")


def director(s: Scratch, status: str) -> tuple[Path, list[subprocess.Popen[bytes]]]:
    """S's world: a target repo, director.toml naming w0:p1, workspace w0 labelled `director`,
    the director there in STATUS, its shell and its Pi (on session D1) live stand-in processes.
    The Herdr world's dir, and the Pi and the shell."""
    d = s.root / "herdr"
    d.mkdir()
    for k in [k for k in s.env if k.startswith(("HERDR_", "OCTO_FEATHER_"))]:
        del s.env[k]
    s.env |= {"FAKE_HERDR": str(d), "HERDR_SESSION": f"relaunch-{os.getpid()}"}
    s.identity()
    s.git(s.root, "init", "-q", "-b", "main", "target")
    state = s.home / ".local" / "state" / "octo-feather" / "sessions" / s.env["HERDR_SESSION"]
    state.mkdir(parents=True)
    (state / "director.toml").write_text(TOML)
    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with (state / "director.handoffs.jsonl").open("a") as f:  # a reflection just ran: none due
        f.write(json.dumps({"at": stamp, "kind": "reflection"}) + "\n")
    env = s.env | {"OCTO_FEATHER_SESSION_ID": "D1", "OCTO_FEATHER_ROLE": "director"}
    pi = subprocess.Popen(PI, cwd=s.root / "target", env=env, start_new_session=True)
    shell = subprocess.Popen(["sleep", "300"], start_new_session=True)  # noqa: S607
    me = {"name": "director", "pane_id": "w0:p1", "workspace_id": "w0", "tab_id": "w0:t1"}
    me |= {"agent_status": status, "shell_pid": shell.pid, "pi_pid": pi.pid, "label": "director"}
    (d / "agents.json").write_text(json.dumps({"w0:p1": me}))
    (d / "workspaces.json").write_text(json.dumps({"w0": "director"}))
    return d, [pi, shell]


def snapshot(s: Scratch, d: Path) -> tuple[str, str]:
    """Herdr's world and director.toml, as text."""
    state = s.home / ".local" / "state" / "octo-feather" / "sessions" / s.env["HERDR_SESSION"]
    return (d / "agents.json").read_text(), (state / "director.toml").read_text()


def unchanged(s: Scratch, d: Path, before: tuple[str, str], pi: subprocess.Popen[bytes]) -> None:
    """Nothing parked, closed or spawned; director.toml and the director's Pi as they were."""
    assert snapshot(s, d) == before, (snapshot(s, d), before)
    calls = (d / "log").read_text().splitlines() if (d / "log").exists() else []
    acts = ("tab close", "workspace close", "tab create", "workspace create", "agent start")
    assert not [x for x in calls if x.startswith(acts)], calls
    assert pi.poll() is None, "the director's Pi ended"


def start(*argv: str) -> list[str]:
    return [kit("octo-feather-start"), "--director", *argv]


def relaunch_busy(s: Scratch) -> None:
    """comms #acceptance-director-relaunch-busy."""
    d, procs = director(s, "working")
    pi = procs[0]
    before = snapshot(s, d)
    try:
        ran = s.run([*start("--relaunch", "--wait", "1", "--cwd", str(s.root / "target"))], want=75)
        assert "busy" in ran.err, ran.err
        assert "w0:p1" in ran.err, ran.err
        unchanged(s, d, before, pi)
        show(f"--relaunch --wait 1, director working: exit 75: {ran.err.strip()}")
    finally:
        for p in procs:
            p.kill()


def relaunch_own_scope(s: Scratch) -> None:
    """comms #acceptance-director-relaunch-own-scope: the director's shell in its own agent
    scope (as herdr-spawn adopts it), and from it a detached job, with no HERDR_PANE_ID of its
    own, running the relaunch; then the relaunch from outside with HERDR_PANE_ID w0:p1."""
    unit = f"octo-feather-agent-w0:p1-{secrets.token_hex(4)}.scope"  # as adopt names it
    out, rc, go = s.root / "job.out", s.root / "job.rc", s.root / "go"
    d, procs = director(s, "idle")
    pi = procs[0]
    cmd = start("--relaunch", "--wait", "1", "--cwd", str(s.root / "target"))
    # The shell detaches the job (its own session, reparented, in the scope), which starts once
    # Herdr's world names the shell as w0:p1's.
    job = f'while [ ! -e "{go}" ]; do sleep 0.05; done; "$@" >"{out}" 2>&1; echo $? >"{rc}"'
    script = f"(setsid sh -c '{job}' _ \"$@\" </dev/null &); exec sleep 300"
    run = ["systemd-run", "--user", "--scope", "--quiet", "--collect", "--unit", unit]
    shell = subprocess.Popen([*run, "sh", "-c", script, "_", *cmd], env=s.env)
    procs.append(shell)
    try:
        agents = json.loads((d / "agents.json").read_text())
        agents["w0:p1"]["shell_pid"] = shell.pid
        (d / "agents.json").write_text(json.dumps(agents))
        before = snapshot(s, d)
        go.touch()
        for _ in range(600):
            if rc.is_file() and rc.read_text().strip():
                break
            time.sleep(0.05)
        said = out.read_text()
        assert rc.read_text().strip() == "64", (rc.read_text(), said)
        assert "w0:p1" in said, said
        assert "scope" in said, said
        unchanged(s, d, before, pi)
        show(f"--relaunch from a detached job in {unit}: exit 64: {said.strip()}")
        ran = s.run(cmd, env={"HERDR_PANE_ID": "w0:p1"}, want=64)
        assert "w0:p1" in ran.err, ran.err
        unchanged(s, d, before, pi)
        show(f"--relaunch with HERDR_PANE_ID=w0:p1: exit 64: {ran.err.strip()}")
    finally:
        for p in procs:
            p.kill()
        subprocess.run(["systemctl", "--user", "stop", unit], check=False, capture_output=True)  # noqa: S607


def resume_same_session(s: Scratch) -> None:
    """comms #acceptance-director-relaunch-same-session."""
    d, procs = director(s, "idle")
    pi = procs[0]
    before = snapshot(s, d)
    try:
        ran = s.run([*start("--resume", "D1", "--cwd", str(s.root / "target"))], want=73)
        assert "w0:p1" in ran.err, ran.err
        assert "D1" in ran.err, ran.err
        unchanged(s, d, before, pi)
        show(f"--director --resume D1 beside the director on D1: exit 73: {ran.err.strip()}")
    finally:
        for p in procs:
            p.kill()


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))
    main(relaunch_busy, relaunch_own_scope, resume_same_session)
