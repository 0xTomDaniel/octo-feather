"""The director relaunch's refusals (comms spec #director-relaunch; #1310), through
`octo-feather-start` with the testkit's Herdr stand-in (testkit/herdr.py, its FAKE_HERDR world)
and real processes standing in for the director's shell and Pi.

A director at w0:p1 in workspace `director`, its Pi a herdr-spawn one on session D1, named by
director.toml. relaunch_busy: its turn outlasts `--relaunch --wait 1`: refused, exit 75, naming
the busy director; relaunch_short_wait: idle, but --wait 31 leaves no full gap for the fourth
read: refused, exit 75. relaunch_own_scope: run by a detached job inside the director pane's agent
scope with no HERDR_PANE_ID, then with HERDR_PANE_ID that pane from outside: refused, exit 64,
naming it (end to end: a real scope, its two paths in its docstring).
resume_same_session: `--director --resume D1` beside it: refused, exit 73, naming w0:p1. Each
leaves Herdr's world, director.toml and the director's Pi as they were: nothing parked, closed or
spawned.
replace_outgoing (comms #acceptance-director-replace-outgoing): `--replace` with HERDR_PANE_ID the
director's pane refused, exit 64, nothing changed; then from outside it: exit 0, a fresh director
at a new pane in workspace `director` that Herdr and director.toml name, the old one's tab still
open under `director-outgoing-<UTC>` with its Pi live, told it is no longer the director; the new
pane told once what it replaced; the kickoff line printed. replace_none: director.toml naming a
pane Herdr no longer knows: `--replace` just spawns (no wait, nothing renamed)."""

from __future__ import annotations

import json
import os
import re
import secrets
import subprocess
import sys
import time
from pathlib import Path
from typing import cast

from testkit import Scratch, kit, main

PI = ["python3", "-c", "import time; time.sleep(300)", "--session-id", "D1"]  # a stand-in Pi


def show(line: str) -> None:
    """One observation on stdout, for the qc demo's output."""
    sys.stdout.write(line + "\n")


def director(
    s: Scratch, status: str, pane: str = "w0:p1"
) -> tuple[Path, list[subprocess.Popen[bytes]]]:
    """S's world: a target repo, director.toml naming PANE (w0:p1), its workspace labelled
    `director`, the director there in STATUS, its shell and its Pi (on session D1) live stand-in
    processes.
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
    (state / "director.toml").write_text(f'pane = "{pane}"\n')
    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with (state / "director.handoffs.jsonl").open("a") as f:  # a reflection just ran: none due
        f.write(json.dumps({"at": stamp, "kind": "reflection"}) + "\n")
    env = s.env | {"OCTO_FEATHER_SESSION_ID": "D1", "OCTO_FEATHER_ROLE": "director"}
    pi = subprocess.Popen(PI, cwd=s.root / "target", env=env, start_new_session=True)
    shell = subprocess.Popen(["sleep", "300"], start_new_session=True)  # noqa: S607
    w, n = pane.split(":p")
    me = {"name": "director", "pane_id": pane, "workspace_id": w, "tab_id": f"{w}:t{n}"}
    me |= {"agent_status": status, "shell_pid": shell.pid, "pi_pid": pi.pid, "label": "director"}
    (d / "agents.json").write_text(json.dumps({pane: me}))
    (d / "workspaces.json").write_text(json.dumps({w: "director"}))
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


def relaunch_short_wait(s: Scratch) -> None:
    """comms #acceptance-director-relaunch-busy, the wait's bound: an idle director and --wait 31,
    room for reads at 0, 15 and 30 s but not the fourth, 15 s after the third: refused, exit 75,
    nothing changed (#1141 design: 4 reads 15 s apart; a shortened last gap never counts)."""
    d, procs = director(s, "idle")
    pi = procs[0]
    before = snapshot(s, d)
    try:
        t0 = time.monotonic()
        cmd = start("--relaunch", "--wait", "31", "--cwd", str(s.root / "target"))
        ran = s.run(cmd, want=75)
        took = time.monotonic() - t0
        assert "w0:p1 is not settled" in ran.err, ran.err
        assert took < 45, took  # the fourth read's earliest time
        unchanged(s, d, before, pi)
        show(f"--relaunch --wait 31, director idle: exit 75 after {took:.0f} s: {ran.err.strip()}")
    finally:
        for p in procs:
            p.kill()


AGENT_SCOPE = re.compile(
    r"/user@\d+\.service/(?:.*/)?octo-feather-agent-(w[^/]*:p[^/]*)-[0-9a-f]{8}\.scope$"
)


def bus() -> bool:
    """The box's systemd user manager starts a scope for this process."""
    probe = ["systemd-run", "--user", "--scope", "--quiet", "--collect", "true"]
    return subprocess.run(probe, capture_output=True, check=False).returncode == 0


def own_agent_scope() -> str:
    """The pane whose kit agent scope this process already runs in, from /proc/self/cgroup;
    '' when none."""
    cg = next(x[3:] for x in Path("/proc/self/cgroup").read_text().splitlines() if x[:3] == "0::")
    m = AGENT_SCOPE.search(cg)
    return m.group(1) if m else ""


def relaunch_own_scope(s: Scratch) -> None:
    """comms #acceptance-director-relaunch-own-scope: the director's shell in its own agent
    scope, and from it a detached job, with no HERDR_PANE_ID of its own, running the relaunch;
    then the relaunch from outside with HERDR_PANE_ID the director's pane. The scope is real, by
    the first path the box gives: (1) a reachable user manager: a new scope for director w0:p1,
    made by systemd-run as herdr-spawn's adopt names one; (2) else the kit agent scope this
    process already runs in (the qc sandbox reaches no manager; a claimed run starts in its
    caller's agent scope): its pane is the director's, the shell and the job inherit it. Neither:
    the scenario fails, naming why."""
    reachable = bus()
    pane = "w0:p1" if reachable else own_agent_scope()
    if not pane:
        msg = "no real agent scope: no user manager answers, and this process sits in no kit"
        msg += f" agent scope ({Path('/proc/self/cgroup').read_text().strip()})"
        raise AssertionError(msg)
    unit = f"octo-feather-agent-{pane}-{secrets.token_hex(4)}.scope"  # as adopt names it
    out, rc, go = s.root / "job.out", s.root / "job.rc", s.root / "go"
    d, procs = director(s, "idle", pane)
    pi = procs[0]
    cmd = start("--relaunch", "--wait", "1", "--cwd", str(s.root / "target"))
    # The shell detaches the job (its own session, reparented, in the scope), which starts once
    # Herdr's world names the shell as the director pane's.
    job = f'while [ ! -e "{go}" ]; do sleep 0.05; done; "$@" >"{out}" 2>&1; echo $? >"{rc}"'
    script = f"(setsid sh -c '{job}' _ \"$@\" </dev/null &); exec sleep 300"
    run = ["systemd-run", "--user", "--scope", "--quiet", "--collect", "--unit", unit]
    shell = subprocess.Popen(
        [*(run if reachable else []), "sh", "-c", script, "_", *cmd], env=s.env
    )
    procs.append(shell)
    try:
        agents = json.loads((d / "agents.json").read_text())
        agents[pane]["shell_pid"] = shell.pid
        (d / "agents.json").write_text(json.dumps(agents))
        before = snapshot(s, d)
        go.touch()
        for _ in range(600):
            if rc.is_file() and rc.read_text().strip():
                break
            time.sleep(0.05)
        said = out.read_text() if out.is_file() else f"(no job output: {out})"
        assert rc.is_file(), said
        assert rc.read_text().strip() == "64", (rc.read_text(), said)
        assert f"director pane {pane}'s agent scope octo-feather-agent-{pane}-" in said, said
        unchanged(s, d, before, pi)
        how = f"new scope {unit}" if reachable else f"its own agent scope (pane {pane})"
        show(f"--relaunch from a detached job in {how}: exit 64: {said.strip()}")
        ran = s.run(cmd, env={"HERDR_PANE_ID": pane}, want=64)
        assert f"HERDR_PANE_ID is the director's pane {pane}" in ran.err, ran.err
        unchanged(s, d, before, pi)
        show(f"--relaunch with HERDR_PANE_ID={pane}: exit 64: {ran.err.strip()}")
    finally:
        for p in procs:
            p.kill()
        if reachable:
            stop = ["systemctl", "--user", "stop", unit]
            subprocess.run(stop, check=False, capture_output=True)


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


def prompts(d: Path) -> list[tuple[str, str]]:
    """Each message Herdr's world delivered: (pane, text)."""
    f = d / "prompts"
    lines = f.read_text().splitlines() if f.exists() else []
    return [cast("tuple[str, str]", tuple(x.split("\t", 1))) for x in lines]


def new_pane(out: str) -> str:
    """The pane= of the start's line, '' with none."""
    return next((x[5:] for x in out.split() if x.startswith("pane=")), "")


def replace_outgoing(s: Scratch) -> None:
    """comms #acceptance-director-replace-outgoing (module docstring)."""
    d, procs = director(s, "idle")
    pi = procs[0]
    before = snapshot(s, d)
    state = s.home / ".local" / "state" / "octo-feather" / "sessions" / s.env["HERDR_SESSION"]
    cmd = start("--replace", "--wait", "60", "--cwd", str(s.root / "target"))
    try:
        ran = s.run(cmd, env={"HERDR_PANE_ID": "w0:p1"}, want=64)
        assert "HERDR_PANE_ID is the director's pane w0:p1" in ran.err, ran.err
        unchanged(s, d, before, pi)
        show(f"--replace with HERDR_PANE_ID=w0:p1: exit 64: {ran.err.strip()}")
        t0 = time.monotonic()
        ran = s.run(cmd)
        took = time.monotonic() - t0
        new = new_pane(ran.out)
        agents = json.loads((d / "agents.json").read_text())
        old = agents["w0:p1"]
        assert took >= 45, took  # 4 idle reads 15 s apart
        assert new not in ("", "w0:p1"), ran.out
        assert agents[new]["name"] == "director", agents
        assert agents[new]["workspace_id"] == "w0", agents  # beside the old tab
        assert re.fullmatch(r"director-outgoing-\d{8}t\d{4}z", str(old["name"])), old
        assert old["tab_id"] == "w0:t1", old
        assert pi.poll() is None, "the old director's Pi ended"
        toml = (state / "director.toml").read_text()
        assert toml == f'pane = "{new}"\n', toml
        told = prompts(d)
        bye = [t for p, t in told if p == "w0:p1"]
        assert len(bye) == 1, told
        assert "you are no longer the director" in bye[0], bye
        assert "no writes to director.toml or the director log" in bye[0], bye
        hello = [t for p, t in told if p == new]
        assert len(hello) == 1, told
        assert "replacing pane w0:p1, session D1" in hello[0], hello
        assert str(state / "director.handoffs.jsonl") in hello[0], hello
        assert "send the director its /goal" in ran.err, ran.err
        calls = (d / "log").read_text().splitlines()
        assert not [x for x in calls if x.startswith(("tab close", "workspace close"))], calls
        show(f"--replace after {took:.0f} s: {ran.out}; old w0:p1 now {old['name']}")
        show(f"w0:p1 told: {bye[0]}")
        show(f"{new} told: {hello[0]}")
    finally:
        for p in procs:
            p.kill()


def replace_none(s: Scratch) -> None:
    """comms #acceptance-director-replace-outgoing, no live director (module docstring)."""
    d, procs = director(s, "idle")
    for p in procs:
        p.kill()
    (d / "agents.json").write_text("{}")
    state = s.home / ".local" / "state" / "octo-feather" / "sessions" / s.env["HERDR_SESSION"]
    t0 = time.monotonic()
    ran = s.run(start("--replace", "--wait", "60", "--cwd", str(s.root / "target")))
    took = time.monotonic() - t0
    new = new_pane(ran.out)
    assert took < 15, took  # no wait
    assert new, ran.out
    toml = (state / "director.toml").read_text()
    assert toml == f'pane = "{new}"\n', toml
    calls = (d / "log").read_text().splitlines()
    assert not [x for x in calls if x.startswith("agent rename")], calls
    hello = [t for p, t in prompts(d) if p == new]
    assert len(hello) == 1, prompts(d)
    assert "the previous director already gone" in hello[0], hello
    show(f"--replace with no live director: {ran.out}; {new} told: {hello[0]}")


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))
    main(
        relaunch_busy,
        relaunch_short_wait,
        relaunch_own_scope,
        resume_same_session,
        replace_outgoing,
        replace_none,
    )
