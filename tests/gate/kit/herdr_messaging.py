"""Herdr messaging never fails silently or hangs (#666; #585, #619; owner rulings #585 and #619
2026-11-05), through the commands with the testkit's Herdr stand-in (testkit/herdr.py, its
FAKE_HERDR world): herdr-spawn returns only once its Pi takes input (#871: Herdr reads a booting
Pi idle before that), so an agent that turns ready late is not returned early, and a herdr-say
right after it is delivered, as is a herdr-say that resumes a parked agent; a spawn whose Pi
never reports, or whose integration install fails, fails closed naming it, within one readiness
bound for the report and the idle wait together; a herdr-say whose
`herdr agent get` lookup fails names that lookup (not the up-chain refusal, 77); a prompt Herdr
reports stalled exits non-zero naming the pane and its state; and `octo-feather-lane post-merge`
step 6 to a busy (working) supervisor returns within its bound, its step 6 line naming the
supervisor NOT told (lane, pane, timeout, the re-send command) and going on to tell the others
(director rule #619). A general worker routes like every worker (roles
spec #acceptance-task-worker-route): its parent reached, a peer lane refused (77); and a worker
never messages the director: its parent proven gone, herdr-say itself sends the director one
fixed alert, a timeout or a stall none (comms spec #acceptance-parent-gone). director_worker_resume
drives comms spec #acceptance-director-worker-resume (its docstring names each step).
fresh_worker_session drives the provider-session half of roles spec
#acceptance-fresh-independent-worker (its docstring names each step).

post-merge step 6 (owner ruling on issue 206; issues 398, 458): live supervisors of the PR's repo
(every lane on a kit PR) told once, by the kit's own herdr-say with its bound, with the merge, PR,
title and rule files, one prod line each, a rerun telling nothing new; parked and gone lanes
listed, never sent to; a failed send named, no prod line, exit 1; any other herdr failure stops
the step; step 7 reached, the kit's own herdr-close run and Herdr's workspace_not_found read as
already closed. Space ids `zt*`, which no real Herdr gives."""

from __future__ import annotations

import contextlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

import tomllib
from testkit import HERE, ROOT, Scratch, kit, main

ASSETS = ROOT / ".agents" / "skills" / "herdr-comms" / "assets"
TELL_BOUND = 20  # post-merge step 6's bound on one send, seconds (octo-feather-lane --help)


def herdr_world(s: Scratch, agents: dict[str, dict[str, object]] | None = None) -> Path:
    """S's Herdr: the stand-in's agents world, holding AGENTS, the caller's Herdr and kit
    variables cleared (a scenario's caller is no pane unless it sets one)."""
    d = s.root / "herdr"
    d.mkdir()
    (d / "agents.json").write_text(json.dumps(agents or {}))
    return herdr_env(s, d)


def herdr_env(s: Scratch, d: Path) -> Path:
    """S's env on the Herdr world in D (herdr_world): D."""
    for k in [k for k in s.env if k.startswith(("HERDR_", "OCTO_FEATHER_"))]:
        del s.env[k]
    s.env["FAKE_HERDR"] = str(d)
    return d


def agent(pane: str, name: str, status: str, ready_at: float = 0) -> dict[str, object]:
    w = pane.split(":", maxsplit=1)[0]
    return {
        "name": name,
        "pane_id": pane,
        "workspace_id": w,
        "tab_id": f"{w}:t{pane.split(':p')[1]}",
        "agent_status": status,
        "ready_at": ready_at,
    }


SUPERVISOR = {
    "OCTO_FEATHER_ROLE": "supervisor",
    "OCTO_FEATHER_PARENT": "w0:p1",
    "HERDR_PANE_ID": "w1:p0",
    "HERDR_WORKSPACE_ID": "w1",
}


def lines(p: Path) -> list[str]:
    return p.read_text().splitlines() if p.exists() else []


def spawn_ready_late(s: Scratch) -> None:
    """A Pi that takes input 2 s after its start, read idle by Herdr's fallback before that:
    herdr-spawn returns only once it takes input (never while it still boots), and a herdr-say to
    its pane right after is delivered, nothing left typed and unsent."""
    d = herdr_world(s)
    (d / "ready_after").write_text("2")
    s.identity()
    wt = s.root / "wt"
    wt.mkdir()
    spawn = [str(ASSETS / "herdr-spawn"), "--workspace", "w1", "--name", "implementer-gh1"]
    ran = s.run([*spawn, "--role", "implementer", "--cwd", str(wt)], env=SUPERVISOR)
    pane = next(x.removeprefix("pane=") for x in ran.out.split() if x.startswith("pane="))
    got = json.loads(s.run(["herdr", "agent", "get", pane]).out)["result"]["agent"]
    assert got["agent_status"] == "idle", f"spawn returned while the agent read {got}"
    s.run([str(ASSETS / "herdr-say"), pane, "the brief"], env=SUPERVISOR)
    assert lines(d / "prompts") == [f"{pane}\tthe brief"], lines(d / "prompts")
    assert lines(d / "typed") == [], lines(d / "typed")


def spawn_fails_closed(s: Scratch) -> None:
    """Herdr's Pi integration does not install, then Pi never reports through it (read idle by
    Herdr all along): each spawn exits 69 naming the cause, no tab left, never ready on the
    screen-idle read alone."""
    d = herdr_world(s)
    s.identity()
    wt = s.root / "wt"
    wt.mkdir()
    spawn = [str(ASSETS / "herdr-spawn"), "--workspace", "w1", "--name", "implementer-gh1"]
    spawn += ["--role", "implementer", "--cwd", str(wt)]
    (d / "install-down").touch()
    ran = s.run(spawn, want=69, env=SUPERVISOR)
    assert "herdr integration install pi failed" in ran.err, ran.err
    assert "integration install failed" in ran.err, ran.err
    assert not any(x.startswith("tab create") for x in lines(d / "log")), lines(d / "log")
    (d / "install-down").unlink()
    (d / "no-report").touch()
    ran = s.run(spawn, want=69, env=SUPERVISOR | {"HERDR_SPAWN_READY_TIMEOUT": "1"})
    assert "never reported to Herdr" in ran.err, ran.err
    assert json.loads((d / "agents.json").read_text()) == {}, "tab left open"


def spawn_one_bound(s: Scratch) -> None:
    """A Pi that reports at once and then stays working, through a Herdr whose `agent get` takes
    at least 1 s: herdr-spawn exits 69 naming it not idle within the 60 s
    HERDR_SPAWN_READY_TIMEOUT, no tab left, one bound for the report and the idle wait together,
    never a fresh bound for the idle wait after the report (owner ruling #941: judged by what
    herdr-spawn reports and passes Herdr, no stopwatch): the report poll spends at least that 1 s
    of the bound, so the one `agent wait` gets --timeout at most 59000 ms, under any load; the
    60 s only guards a hang."""
    d = herdr_world(s)
    (d / "get-delay").write_text("1")
    (d / "start-status").write_text("working")
    s.identity()
    wt = s.root / "wt"
    wt.mkdir()
    spawn = [str(ASSETS / "herdr-spawn"), "--workspace", "w1", "--name", "implementer-gh1"]
    spawn += ["--role", "implementer", "--cwd", str(wt)]
    ran = s.run(spawn, want=69, env=SUPERVISOR | {"HERDR_SPAWN_READY_TIMEOUT": "60"})
    assert "not idle within 60s" in ran.err, ran.err
    log = lines(d / "log")
    waits = [x.split() for x in log if x.startswith("agent wait ")]
    assert len(waits) == 1, log
    timeout_ms = int(waits[0][waits[0].index("--timeout") + 1])
    assert timeout_ms <= 59000, f"the idle wait got a {timeout_ms} ms bound past the report"
    assert json.loads((d / "agents.json").read_text()) == {}, "tab left open"


def say_resumes_parked(s: Scratch) -> None:
    """An owner shell's herdr-say to a parked worker (its parked line in a lane log), whose Pi
    takes input 2 s after its resume, read idle by Herdr before that: the first send resumes it
    and lands, exit 0, its new pane= printed, the message delivered with the resume notice, nothing
    left typed and unsent."""
    d = herdr_world(s)
    (d / "ready_after").write_text("2")
    s.identity()
    wt = s.root / "wt"
    wt.mkdir()
    lanes = s.home / ".local" / "state" / "octo-feather" / "lanes"
    lanes.mkdir(parents=True)
    line = {"at": "2026-11-13T00:00:00Z", "kind": "parked", "pane": "w1:p7", "name": "impl1"}
    line |= {"label": "worker-1", "role": "implementer", "parent": "w1:p0", "cwd": str(wt)}
    (lanes / "gh1.handoffs.jsonl").write_text(json.dumps(line | {"session": "S1"}) + "\n")
    ran = s.run([str(ASSETS / "herdr-say"), "w1:p7", "go on"], env={"HERDR_WORKSPACE_ID": "w1"})
    pane = ran.out.removeprefix("pane=")
    assert lines(d / "prompts") == [f"{pane}\tResumed from park as pane={pane}. go on"], ran
    assert lines(d / "typed") == [], lines(d / "typed")


def say_lookup_fails(s: Scratch) -> None:
    """A supervisor's herdr-say to its worker while `herdr agent get` fails: an error naming the
    lookup and what it printed, never the up-chain refusal (77); nothing prompted."""
    d = herdr_world(s, {"w1:p2": agent("w1:p2", "implementer-gh1", "idle")})
    (d / "get-down").touch()
    ran = s.run([str(ASSETS / "herdr-say"), "w1:p2", "hi"], want=69, env=SUPERVISOR)
    assert "herdr agent get w1:p2" in ran.err, ran.err
    assert "server not reachable" in ran.err, ran.err
    assert "up its chain" not in ran.err, ran.err
    assert not lines(d / "prompts"), lines(d / "prompts")


def say_stalled(s: Scratch) -> None:
    """A prompt Herdr reports stalled (typed, never seen to land): herdr-say exits non-zero, its
    last line naming the pane and the state Herdr reads it in, and Herdr's own error kept."""
    late = time.time() + 3600
    d = herdr_world(s, {"w1:p2": agent("w1:p2", "implementer-gh1", "idle", late)})
    ran = s.run([str(ASSETS / "herdr-say"), "implementer-gh1", "hi"], want=1)
    last = ran.err.splitlines()[-1]
    assert "agent_prompt_stalled" in ran.err, ran.err
    assert "w1:p2" in last, ran.err
    assert "unknown" in last, ran.err
    assert lines(d / "typed") == ["w1:p2\thi"], lines(d / "typed")


RESULT = "RESULT-TEXT commit abc123 done"


def worker_world(
    s: Scratch,
    parent: str = "idle",
    *,
    director: bool = True,
    resumed: str = "",
) -> tuple[Path, dict[str, str]]:
    """Director w0:p1 (live unless not DIRECTOR); lane gh7 (record lanes/gh7.toml) with
    supervisor w1:p1 (PARENT: its status, or gone; RESUMED: a pane where its parked agent gh7
    runs live again) and general worker w1:p2; peer lane gh8, supervisor w2:p1, worker w2:p2.
    The Herdr world and the general worker's env."""
    agents = {
        "w1:p2": agent("w1:p2", "general-worker-gh7", "idle"),
        "w2:p1": agent("w2:p1", "gh8", "idle"),
        "w2:p2": agent("w2:p2", "implementer-gh8", "idle"),
    }
    if director:
        agents["w0:p1"] = agent("w0:p1", "director", "idle")
    if resumed:
        agents[resumed] = agent(resumed, "gh7", "idle")
    if parent != "gone":
        late = time.time() + 3600 if parent == "booting" else 0
        agents["w1:p1"] = agent("w1:p1", "gh7", parent, late)
    d = herdr_world(s, agents)
    state = s.home / ".local" / "state" / "octo-feather"
    (state / "lanes").mkdir(parents=True)
    (state / "director.toml").write_text('pane = "w0:p1"\n')
    for lane, sup in (("gh7", "w1:p1"), ("gh8", "w2:p1")):
        (state / "lanes" / f"{lane}.toml").write_text(f'supervisor = "{sup}"\ngoal = "g"\n')
    env = {
        "OCTO_FEATHER_ROLE": "general-worker",
        "OCTO_FEATHER_PARENT": "w1:p1",
        "HERDR_PANE_ID": "w1:p2",
        "HERDR_WORKSPACE_ID": "w1",
    }
    return d, env


def to(d: Path, pane: str) -> list[str]:
    """What PANE received: each prompt submitted to it."""
    return [x.split("\t", 1)[1] for x in lines(d / "prompts") if x.split("\t")[0] == pane]


def show(line: str) -> None:
    """One observation on stdout, for the qc demo's output."""
    sys.stdout.write(line + "\n")


def sub(s: Scratch, name: str) -> Scratch:
    """A fresh Scratch NAME inside S, for one more world in the same scenario."""
    (s.root / name).mkdir()
    return Scratch(s.root / name)


def worker_route(s: Scratch) -> None:
    """A general worker (roles #acceptance-task-worker-route): a send to a peer lane's agent, by
    pane or name, exits 77 and the peer receives nothing; `--parent RESULT` is delivered to its
    parent. Each observation printed, for the qc demo."""
    d, env = worker_world(s)
    say = str(ASSETS / "herdr-say")
    for peer in ("w2:p2", "implementer-gh8", "gh8"):
        ran = s.run([say, peer, RESULT], want=77, env=env)
        assert "may message only up its chain" in ran.err, ran.err
        show(f"peer {peer}: exit 77: {ran.err.strip()}")
    assert to(d, "w2:p1") == [], lines(d / "prompts")
    assert to(d, "w2:p2") == [], lines(d / "prompts")
    show("peer lane gh8 received: nothing")
    s.run([say, "--parent", RESULT], env=env)
    assert lines(d / "prompts") == [f"w1:p1\t{RESULT}"], lines(d / "prompts")
    show(f"parent w1:p1: exit 0, received: {to(d, 'w1:p1')}")


def parent_gone(s: Scratch) -> None:
    """comms #acceptance-parent-gone: lane gh7's supervisor w1:p1 closed, no parked line: the
    general worker's `--parent RESULT` exits 68 and the director receives exactly one fixed alert
    naming lane, gone parent and worker, without RESULT; no other pane receives anything. A
    parked line naming the parent, a timeout and a stall raise no alert; an implementer may not
    reach the director; with no director reachable or no director.toml, the exit says the alert
    was not delivered; a parent no lane record names still alerts, naming no lane."""
    say = str(ASSETS / "herdr-say")
    d, env = worker_world(s, "gone")
    ran = s.run([say, "--parent", RESULT], want=68, env=env)
    alerts = to(d, "w0:p1")
    show(f"parent gone: exit 68: {ran.err.strip()}")
    show(f"director w0:p1 received: {alerts}")
    assert len(alerts) == 1, alerts
    for named in ("lane gh7", "parent w1:p1 is gone", "general-worker-gh7", "w1:p2"):
        assert named in alerts[0], alerts
    assert "RESULT-TEXT" not in alerts[0], alerts
    assert [x.split("\t")[0] for x in lines(d / "prompts")] == ["w0:p1"], lines(d / "prompts")
    assert "alert delivered to the director" in ran.err, ran.err

    for status, want, why in (("working", 124, "timeout"), ("booting", 1, "stalled")):
        s2 = sub(s, why)
        d, env = worker_world(s2, status)
        s2.run([say, "--timeout", "1", "--parent", RESULT], want=want, env=env)
        assert to(d, "w0:p1") == [], lines(d / "prompts")
        show(f"parent {why}: exit {want}, director received: nothing")

    s2 = sub(s, "parked")
    d, env = worker_world(s2, "gone", resumed="w1:p5")
    log = s2.home / ".local" / "state" / "octo-feather" / "lanes" / "gh7.handoffs.jsonl"
    log.write_text(
        json.dumps({"at": "2026-11-13T00:00:00Z", "kind": "parked", "pane": "w1:p1"}) + "\n"
    )
    s2.run([say, "--parent", RESULT], env=env)
    assert lines(d / "prompts") == [f"w1:p5\t{RESULT}"], lines(d / "prompts")
    show("parent parked: delivered to its live agent w1:p5, director received: nothing")

    s2 = sub(s, "implementer")
    d, env = worker_world(s2)
    ran = s2.run([say, "w0:p1", RESULT], want=77, env=env | {"OCTO_FEATHER_ROLE": "implementer"})
    assert to(d, "w0:p1") == [], lines(d / "prompts")
    show(f"implementer to the director w0:p1: exit 77: {ran.err.strip()}")

    no_director(s, say)


def no_director(s: Scratch, say: str) -> None:
    """parent_gone's cases with no director reachable (its pane gone, or no director.toml), and a
    gone parent no lane record names."""
    s2 = sub(s, "nodirector")
    d, env = worker_world(s2, "gone", director=False)
    ran = s2.run([say, "--parent", RESULT], want=68, env=env)
    assert "alert NOT delivered to the director (pane w0:p1" in ran.err, ran.err
    assert lines(d / "prompts") == [], lines(d / "prompts")
    show(f"no director reachable: exit 68: {ran.err.strip().splitlines()[-1]}")

    s2 = sub(s, "notoml")
    d, env = worker_world(s2, "gone")
    (s2.home / ".local" / "state" / "octo-feather" / "director.toml").unlink()
    ran = s2.run([say, "--parent", RESULT], want=68, env=env)
    assert "alert NOT delivered: no director reachable (no " in ran.err, ran.err
    assert "result stays retained" in ran.err, ran.err
    assert lines(d / "prompts") == [], lines(d / "prompts")
    show(f"no director.toml: exit 68: {ran.err.strip().splitlines()[-1]}")

    s2 = sub(s, "nolane")
    d, env = worker_world(s2, "gone")
    ran = s2.run([say, "--parent", RESULT], want=68, env=env | {"OCTO_FEATHER_PARENT": "w0:p9"})
    alerts = to(d, "w0:p1")
    assert len(alerts) == 1, alerts
    for named in ("no lane", "parent w0:p9 is gone", "general-worker-gh7"):
        assert named in alerts[0], alerts
    assert "RESULT-TEXT" not in alerts[0], alerts
    show(f"parent w0:p9 in no lane record: exit 68, director received: {alerts}")


def state_dir(s: Scratch) -> Path:
    """S's octo-feather state dir for its Herdr session (scripts/octo-feather-state)."""
    base = s.home / ".local" / "state" / "octo-feather"
    return base / "sessions" / s.env["HERDR_SESSION"] if "HERDR_SESSION" in s.env else base


def tab_process(s: Scratch, d: Path, pane: str, cwd: Path) -> subprocess.Popen[bytes]:
    """A process standing in for the Pi at PANE: it runs in CWD under the env herdr-spawn gave
    PANE's tab, with Herdr's own ids and its --session-id, and Herdr names it PANE's foreground
    process (`pi_pid`), where herdr-close --park reads it."""
    agents = json.loads((d / "agents.json").read_text())
    g = agents[pane]
    ids = {"HERDR_PANE_ID": pane, "HERDR_TAB_ID": g["tab_id"]}
    env = s.env | g["env"] | ids | {"HERDR_WORKSPACE_ID": g["workspace_id"]}
    pi = ["python3", "-c", "import time; time.sleep(300)"]
    pi += ["--session-id", g["env"]["OCTO_FEATHER_SESSION_ID"]]
    p = subprocess.Popen(pi, cwd=cwd, env=env, start_new_session=True)
    for _ in range(100):  # until exec'd, so its argv and environ are Pi's
        if Path(f"/proc/{p.pid}/environ").read_bytes().find(b"HERDR_TAB_ID=") >= 0:
            break
        time.sleep(0.02)
    g["pi_pid"] = p.pid
    (d / "agents.json").write_text(json.dumps(agents))
    return p


def resumed_as(d: Path, out: str, space: str, session: str) -> tuple[str, dict[str, str]]:
    """The pane herdr-say printed (pane=), asserted resumed in SPACE with SESSION; its tab env."""
    pane = next(x.removeprefix("pane=") for x in out.split() if x.startswith("pane="))
    g = json.loads((d / "agents.json").read_text())[pane]
    assert g["workspace_id"] == space, (space, g)
    assert g["env"]["OCTO_FEATHER_SESSION_ID"] == session, g
    starts = [x for x in lines(d / "log") if x.startswith(f"agent start {g['name']} ")]
    assert f" --session-id {session} " in f"{starts[-1]} ", starts
    return pane, g["env"]


DIRECTOR = {"OCTO_FEATHER_ROLE": "director", "HERDR_PANE_ID": "w0:p1", "HERDR_WORKSPACE_ID": "w0"}
SAY = str(ASSETS / "herdr-say")


def director_parks(s: Scratch, d: Path) -> dict[str, str]:
    """The director spawns general-worker-a1 in w0 (a process standing in for it), parks it with
    `herdr-close --park`, appending the line to the director log after a note line: that line."""
    state = state_dir(s)
    (state / "lanes").mkdir(parents=True)
    (state / "director.toml").write_text('pane = "w0:p1"\n')
    s.identity()
    wt = s.root / "wt"
    wt.mkdir()
    spawn = [str(ASSETS / "herdr-spawn"), "--workspace", "w0", "--name", "general-worker-a1"]
    spawn += ["--label", "a1", "--role", "general-worker", "--cwd", str(wt)]
    got = dict(x.split("=", 1) for x in s.run(spawn, env=DIRECTOR).out.split())
    worker = tab_process(s, d, got["pane"], wt)
    try:
        park = s.run([str(ASSETS / "herdr-close"), "--park", got["pane"]], env=DIRECTOR)
    finally:
        worker.kill()
    dlog = state / "director.handoffs.jsonl"
    note = {"at": "2026-11-13T00:00:00Z", "kind": "note", "text": "t"}
    dlog.write_text(json.dumps(note) + "\n" + park.out + "\n")
    show(f"herdr-close --park {got['pane']} >> director.handoffs.jsonl: {park.out}")
    line = json.loads(park.out)
    want = {"name": "general-worker-a1", "role": "general-worker", "parent": "w0:p1", "label": "a1"}
    assert {k: line[k] for k in want} == want, line
    assert line["session"] == got["provider_session_id"], (line, got)
    return line


def lane_worker_resumes(s: Scratch, caller: str, who: str) -> None:
    """Lane gh7's worker implementer-gh7 parked (parent its supervisor w1:p1, session S7):
    CALLER's herdr-say resumes it in w1 with its role, session and parent, as before."""
    d, _ = worker_world(s)
    s.identity()
    parked = {"at": "2026-11-13T00:00:00Z", "kind": "parked", "pane": "w1:p3"}
    parked |= {"name": "implementer-gh7", "label": "gh7", "role": "implementer"}
    parked |= {"parent": "w1:p1", "cwd": str(s.root), "session": "S7"}
    (state_dir(s) / "lanes" / "gh7.handoffs.jsonl").write_text(json.dumps(parked) + "\n")
    env = SUPERVISOR | {"HERDR_PANE_ID": "w1:p1"} if caller == "w1:p1" else DIRECTOR
    got = s.run([SAY, "implementer-gh7", "go on"], env=env)
    new, tab = resumed_as(d, got.out, "w1", "S7")
    assert (tab["OCTO_FEATHER_ROLE"], tab["OCTO_FEATHER_PARENT"]) == ("implementer", "w1:p1")
    assert to(d, new) == [f"Resumed from park as pane={new}. go on"], lines(d / "prompts")
    show(f"parked lane worker implementer-gh7, sent by {who}: {got.out}, in w1, session S7")


def director_worker_resume(s: Scratch) -> None:
    """comms #acceptance-director-worker-resume: the director w0:p1 parks its general worker
    general-worker-a1 into the director log (director_parks); `herdr-say --parked
    general-worker-a1` prints that line; the director's `herdr-say general-worker-a1 MSG` prints
    the resumed pane=, in w0, with the recorded role, session and parent, and the worker receives
    "Resumed from park as pane=..."; its `--parent RESULT` reaches the director. A parked lane
    worker still resumes in its supervisor's workspace w1, by its supervisor or by the director.
    Each observation printed, for the qc demo."""
    d, _ = worker_world(s)
    s.env["HERDR_SESSION"] = f"park-{os.getpid()}"  # only this scenario's processes count
    line = director_parks(s, d)
    got = s.run([SAY, "--parked", "general-worker-a1"], env=DIRECTOR)
    assert json.loads(got.out) == line, got.out
    show(f"herdr-say --parked general-worker-a1: {got.out}")
    got = s.run([SAY, "general-worker-a1", "continue a1"], env=DIRECTOR)
    new, env = resumed_as(d, got.out, "w0", line["session"])
    assert env["OCTO_FEATHER_ROLE"] == "general-worker", env
    assert env["OCTO_FEATHER_PARENT"] == "w0:p1", env
    assert to(d, new) == [f"Resumed from park as pane={new}. continue a1"], lines(d / "prompts")
    show(f"herdr-say general-worker-a1 from the director: {got.out}; {new} received: {to(d, new)}")
    back = {k: env[k] for k in ("OCTO_FEATHER_ROLE", "OCTO_FEATHER_PARENT")}
    s.run([SAY, "--parent", RESULT], env=back | {"HERDR_PANE_ID": new, "HERDR_WORKSPACE_ID": "w0"})
    assert to(d, "w0:p1") == [RESULT], lines(d / "prompts")
    show(f"resumed worker --parent: director w0:p1 received: {to(d, 'w0:p1')}")
    for caller, who in (("w1:p1", "its supervisor"), ("w0:p1", "the director")):
        lane_worker_resumes(sub(s, caller.replace(":", "-")), caller, who)


def tab_env(d: Path, pane: str) -> dict[str, str]:
    """The env of the agent at PANE as its tab gives it: herdr-spawn's, with Herdr's own ids."""
    g = json.loads((d / "agents.json").read_text())[pane]
    return g["env"] | {"HERDR_PANE_ID": pane, "HERDR_WORKSPACE_ID": g["workspace_id"]}


def start(s: Scratch, *argv: str) -> dict[str, str]:
    """octo-feather-start ARGV at the target repo, from an owner shell: what it printed."""
    out = s.run([kit("octo-feather-start"), "--cwd", str(s.root / "target"), *argv]).out
    return dict(x.split("=", 1) for x in out.split())


def drop(d: Path, pane: str) -> None:
    """The agent at PANE gone from Herdr's world, as after a restart."""
    agents = json.loads((d / "agents.json").read_text())
    del agents[pane]
    (d / "agents.json").write_text(json.dumps(agents))


def supervised(s: Scratch) -> tuple[Path, dict[str, str], dict[str, str]]:
    """Director w0:p1; lane gh7's supervisor started by octo-feather-start, its lane record
    naming it (with other keys and a comment), and its implementer spawned through herdr-spawn,
    the spawn line in the lane log. The Herdr world, the supervisor's start and the worker's env.
    Built once per gate run (build_supervised) and copied here, its paths moved to S's root (the
    tabs' env, the logs' cwd), as several items start from it."""
    s.prepare("herdr-supervised", build_supervised)
    got = json.loads((s.root / "supervised.json").read_text())
    if got["root"] != str(s.root):
        old, new = got["root"].encode(), str(s.root).encode()
        for f in s.root.rglob("*"):
            if f.is_file() and not f.is_symlink() and old in (b := f.read_bytes()):
                f.write_bytes(b.replace(old, new))
        got = json.loads((s.root / "supervised.json").read_text())
    d = herdr_env(s, s.root / "herdr")
    s.env["HERDR_SESSION"] = got["session"]
    return d, got["sup"], got["worker"]


def build_supervised(s: Scratch) -> None:
    """supervised's world in S, with supervised.json: S's root, its Herdr session, the
    supervisor's start and the worker's env. Its tabs' shells (each a process Herdr names for a
    pane, alive while S's Herdr dir is) ended and unnamed: a copy's own Herdr starts its own."""
    d = herdr_world(s, {"w0:p1": agent("w0:p1", "director", "idle")})
    s.env["HERDR_SESSION"] = f"parent-{os.getpid()}"  # only this scenario's processes count
    s.identity()
    s.git(s.root, "init", "-q", "-b", "main", "target")
    state = state_dir(s)
    (state / "lanes").mkdir(parents=True)
    (state / "director.toml").write_text('pane = "w0:p1"\n')
    sup = start(s, "--name", "gh7")
    record = f'# lane gh7\nissue = "7"\nsupervisor = "{sup["pane"]}"\ngoal = "g"\n'
    (state / "lanes" / "gh7.toml").write_text(record)
    spawn = [str(ASSETS / "herdr-spawn"), "--workspace", sup["workspace"], "--name"]
    spawn += ["implementer-gh7", "--label", "gh7", "--role", "implementer", "--cwd", str(s.root)]
    worker = dict(x.split("=", 1) for x in s.run(spawn, env=tab_env(d, sup["pane"])).out.split())
    got = {"root": str(s.root), "session": s.env["HERDR_SESSION"], "sup": sup}
    got["worker"] = tab_env(d, worker["pane"])
    agents = json.loads((d / "agents.json").read_text())
    for g in agents.values():
        if isinstance(pid := g.pop("shell_pid", None), int):
            with contextlib.suppress(ProcessLookupError):
                os.killpg(pid, signal.SIGKILL)
    (d / "agents.json").write_text(json.dumps(agents))
    (s.root / "supervised.json").write_text(json.dumps(got))


def parent_resumed(s: Scratch) -> None:
    """comms say-parent, the parent surviving restart and park (owner ruling 2026-11-18 #901):
    lane gh7's supervisor gone with no park (a Herdr restart), resumed by `octo-feather-start
    --name gh7 --resume S` on a new pane: the lane record's `supervisor` names it, every other key
    unchanged, and its implementer's `herdr-say --parent RESULT` (OCTO_FEATHER_PARENT still the old
    pane) lands there as the notice naming its result file, exit 0, the director receiving
    nothing; the director then edits the record
    by hand and the next send follows it; that pane gone with no parked line, the director gets the
    one parent-gone alert, exit 68. Parked with `herdr-close --park` and resumed the same way:
    the same. Each observation printed, for the qc demo."""
    d, sup, worker = supervised(s)
    record = state_dir(s) / "lanes" / "gh7.toml"
    before = record.read_text()
    drop(d, sup["pane"])
    show(f"supervisor gh7 {sup['pane']} gone without a park (Herdr restart)")
    new = start(s, "--name", "gh7", "--resume", sup["provider_session_id"])["pane"]
    assert new != sup["pane"], new
    want = tomllib.loads(before) | {"supervisor": new}
    assert tomllib.loads(record.read_text()) == want, record.read_text()
    show(f"octo-feather-start --resume: {record.name} supervisor = {new}, other keys unchanged")
    ran = s.run([SAY, "--parent", RESULT], env=worker)
    assert worker["OCTO_FEATHER_PARENT"] == sup["pane"], worker
    assert to(d, new) == [noted(s, worker)], lines(d / "prompts")
    assert to(d, "w0:p1") == [], lines(d / "prompts")
    show(f"implementer --parent: exit 0 {ran.err.strip()}; {new} received: {to(d, new)}")

    agents = json.loads((d / "agents.json").read_text())
    (d / "agents.json").write_text(json.dumps(agents | {"w9:p1": agent("w9:p1", "gh7b", "idle")}))
    record.write_text(record.read_text().replace(new, "w9:p1"))
    s.run([SAY, "--parent", RESULT], env=worker)
    assert to(d, "w9:p1") == [noted(s, worker)], lines(d / "prompts")
    assert to(d, new) == [noted(s, worker)], lines(d / "prompts")
    show(f"record hand-edited to w9:p1: the next --parent reached w9:p1: {to(d, 'w9:p1')}")
    drop(d, "w9:p1")
    ran = s.run([SAY, "--parent", RESULT], want=68, env=worker)
    alerts = to(d, "w0:p1")
    assert len(alerts) == 1, alerts
    assert "lane gh7" in alerts[0], alerts
    assert "parent w9:p1 is gone" in alerts[0], alerts
    show(f"record pane w9:p1 gone, no parked line: exit 68, director received: {alerts}")

    parked_resumed(sub(s, "parked"))


def parked_resumed(s: Scratch) -> None:
    """parent_resumed's park: the supervisor parked with herdr-close --park, its line in the lane
    log, resumed by octo-feather-start --resume; the implementer's --parent lands there."""
    d, sup, worker = supervised(s)
    record = state_dir(s) / "lanes" / "gh7.toml"
    p = tab_process(s, d, sup["pane"], s.root / "target")
    try:
        park = s.run([str(ASSETS / "herdr-close"), "--park", sup["pane"]])
    finally:
        p.kill()
    with (state_dir(s) / "lanes" / "gh7.handoffs.jsonl").open("a") as f:
        f.write(park.out + "\n")
    new = start(s, "--name", "gh7", "--resume", json.loads(park.out)["session"])["pane"]
    assert f'supervisor = "{new}"' in record.read_text(), record.read_text()
    s.run([SAY, "--parent", RESULT], env=worker)
    assert to(d, new) == [noted(s, worker)], lines(d / "prompts")
    assert to(d, "w0:p1") == [], lines(d / "prompts")
    show(f"supervisor parked, resumed as {new}: implementer --parent exit 0, {new} received it")


def director_moved(s: Scratch) -> None:
    """comms say-parent for a director's own general worker: a director started by hand (no kit
    env) at w0:p1 spawns general-worker-a1 (its spawn line in the director log); the director is
    resumed by `octo-feather-start --director --resume D` on a new pane, director.toml's `pane`
    then naming it; the worker's `herdr-say --parent RESULT` reaches it, exit 0."""
    d = herdr_world(s, {"w0:p1": agent("w0:p1", "director", "idle")})
    s.env["HERDR_SESSION"] = f"director-{os.getpid()}"
    s.identity()
    s.git(s.root, "init", "-q", "-b", "main", "target")
    state = state_dir(s)
    (state / "lanes").mkdir(parents=True)
    (state / "director.toml").write_text('# the director\npane = "w0:p1"\n')
    hand = {"HERDR_PANE_ID": "w0:p1", "HERDR_WORKSPACE_ID": "w0"}
    spawn = [str(ASSETS / "herdr-spawn"), "--workspace", "w0", "--name", "general-worker-a1"]
    spawn += ["--label", "a1", "--role", "general-worker", "--cwd", str(s.root)]
    worker = tab_env(d, dict(x.split("=", 1) for x in s.run(spawn, env=hand).out.split())["pane"])
    log = state / "director.handoffs.jsonl"
    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with log.open("a") as f:  # a reflection just ran: the start runs none in the background
        f.write(json.dumps({"at": stamp, "kind": "reflection"}) + "\n")
    drop(d, "w0:p1")
    new = start(s, "--director", "--resume", "D1")["pane"]
    toml = (state / "director.toml").read_text()
    assert toml == f'pane = "{new}"\n', toml
    ran = s.run([SAY, "--parent", RESULT], env=worker)
    assert worker["OCTO_FEATHER_PARENT"] == "w0:p1", worker
    assert to(d, new) == [noted(s, worker, "director", "general-worker-a1")], lines(d / "prompts")
    show(f"director resumed as {new}: general worker --parent exit 0 {ran.err.strip()}")


REPORT = "DONE commit abc123: the report\nevidence: just fast green\nnext: review"


def results_dir(s: Scratch, owner: str = "lanes/gh7") -> Path:
    """OWNER's results dir in S's state: a lane's, or `director` for the director's own."""
    return state_dir(s) / f"{owner}.results"


def reported(s: Scratch, worker: dict[str, str], owner: str = "lanes/gh7") -> Path:
    """The result file WORKER's report sits in, asserted holding REPORT whole."""
    f = results_dir(s, owner) / f"{worker['OCTO_FEATHER_SESSION_ID']}.md"
    assert REPORT in f.read_text(), f.read_text()
    return f


def notice(f: Path, first: str = REPORT.splitlines()[0], name: str = "implementer-gh7") -> str:
    """The notice herdr-say sends the parent for a report (FIRST its first line) by worker NAME
    (`<role>-<ticket>`) kept in result file F."""
    role = name.rpartition("-")[0]
    return f"{name} reported ({role}); read {f}. First line: {first}"


def noted(s: Scratch, worker: dict[str, str], owner: str = "lanes/gh7", name: str = "") -> str:
    """The notice for WORKER's one-line report RESULT (NAME, else implementer-gh7), its file
    in OWNER's results dir."""
    f = results_dir(s, owner) / f"{worker['OCTO_FEATHER_SESSION_ID']}.md"
    return notice(f, RESULT, name or "implementer-gh7")


def result_compacting(s: Scratch) -> None:
    """comms result file (owner ruling 2026-11-18 #954): lane gh7's implementer reports with
    `herdr-say --parent REPORT` while its supervisor compacts for 4 s: the result file
    lanes/gh7.results/<its session>.md holds REPORT before any prompt (there when the prompt is
    asked), with a heading naming it;
    the supervisor receives one notice naming the file and REPORT's first line, one prompt sent,
    no resend (#882's queued path kept), exit 0. Each observation printed, for the qc demo."""
    d, sup, worker = supervised(s)
    agents = json.loads((d / "agents.json").read_text())
    agents[sup["pane"]]["compacting_until"] = time.time() + 4
    (d / "agents.json").write_text(json.dumps(agents))
    path = results_dir(s) / f"{worker['OCTO_FEATHER_SESSION_ID']}.md"
    (d / "prompt-watch").write_text(str(path))
    ran = s.run([SAY, "--parent", REPORT], env=worker)
    f = reported(s, worker)
    assert lines(d / "watched") == ["yes"], (
        f"result file there at the prompt: {lines(d / 'watched')}"
    )
    heading = r"^## \S+Z implementer-gh7 \(implementer\)$"
    assert re.search(heading, f.read_text(), re.MULTILINE), f.read_text()
    sent = [x for x in lines(d / "log") if x.startswith("agent prompt ")]
    assert to(d, sup["pane"]) == [notice(f)], lines(d / "prompts")
    assert len(sent) == 1, sent
    assert "queued" in ran.err, ran.err
    show(f"result file {f.name}: {f.read_text().splitlines()[0]}")
    show(f"supervisor compacting: {len(sent)} prompt, received: {to(d, sup['pane'])}")


def result_resumed(s: Scratch) -> None:
    """comms result file: lane gh7's supervisor gone (a Herdr restart), resumed by
    `octo-feather-start --resume` on a new pane; its implementer's `herdr-say --parent REPORT`:
    the new pane receives the notice naming the result file, which holds REPORT; the old pane and
    the director nothing."""
    d, sup, worker = supervised(s)
    drop(d, sup["pane"])
    new = start(s, "--name", "gh7", "--resume", sup["provider_session_id"])["pane"]
    s.run([SAY, "--parent", REPORT], env=worker)
    f = reported(s, worker)
    assert to(d, new) == [notice(f)], lines(d / "prompts")
    assert [x.split("\t")[0] for x in lines(d / "prompts")] == [new], lines(d / "prompts")
    show(f"supervisor resumed as {new}: received {to(d, new)}")


def spawned(s: Scratch, d: Path, sup: dict[str, str], name: str, role: str) -> dict[str, str]:
    """Worker NAME (ROLE) spawned by lane gh7's supervisor through herdr-spawn: its tab env."""
    spawn = [str(ASSETS / "herdr-spawn"), "--workspace", sup["workspace"], "--name", name]
    spawn += ["--label", name, "--role", role, "--cwd", str(s.root)]
    got = dict(x.split("=", 1) for x in s.run(spawn, env=tab_env(d, sup["pane"])).out.split())
    return tab_env(d, got["pane"])


def results_listing(s: Scratch) -> None:
    """comms result file, the parent's listing: lane gh7's supervisor spawns implementer-gh7
    (reports with `herdr-say --parent`), general-worker-a (live, no report), corrector-gh7 (then
    gone from Herdr, no report, no parked line), code-reviewer-gh7 (parked) and general-worker-b
    (an attempt line closes it). `octo-feather-handoff results` run as the supervisor lists, one
    line each, name, pane, state and result: implementer-gh7 its result file, general-worker-a
    `none yet`, corrector-gh7 `ended, no result file`, code-reviewer-gh7 parked `none yet`, and
    not general-worker-b; the lane log unchanged. The demo: each line printed."""
    d, sup, impl = supervised(s)
    log = state_dir(s) / "lanes" / "gh7.handoffs.jsonl"
    live = spawned(s, d, sup, "general-worker-a", "general-worker")
    ended = spawned(s, d, sup, "corrector-gh7", "corrector")
    parked = spawned(s, d, sup, "code-reviewer-gh7", "code-reviewer")
    done = spawned(s, d, sup, "general-worker-b", "general-worker")
    drop(d, ended["HERDR_PANE_ID"])
    drop(d, parked["HERDR_PANE_ID"])
    line = {"at": "2026-11-18T00:00:00Z", "kind": "parked", "pane": parked["HERDR_PANE_ID"]}
    line |= {"name": "code-reviewer-gh7", "session": parked["OCTO_FEATHER_SESSION_ID"]}
    attempt = {"at": "2026-11-18T00:00:01Z", "kind": "attempt", "worker": "general-worker-b"}
    attempt |= {"session": done["OCTO_FEATHER_SESSION_ID"], "result": "done"}
    with log.open("a") as f:
        f.write(json.dumps(line) + "\n" + json.dumps(attempt) + "\n")
    s.run([SAY, "--parent", REPORT], env=impl)
    f = reported(s, impl)
    before = log.read_text()
    out = s.run([kit("octo-feather-handoff"), "results"], env=tab_env(d, sup["pane"])).out
    got = [x.split("\t") for x in out.splitlines()]
    for row in got:
        show("results: " + " | ".join(row))
    want = [
        ["implementer-gh7", impl["HERDR_PANE_ID"], "live idle", str(f)],
        ["general-worker-a", live["HERDR_PANE_ID"], "live idle", "none yet"],
        ["corrector-gh7", ended["HERDR_PANE_ID"], "ended", "ended, no result file"],
        ["code-reviewer-gh7", parked["HERDR_PANE_ID"], "parked", "none yet"],
    ]
    assert got == want, got
    assert log.read_text() == before, "results wrote the log"


def director_prune(s: Scratch) -> None:
    """comms result file, the director's remover (#notification-records: a week after the worker
    is gone): the director w0:p1 spawns general workers a1, a2 and a3, each reporting with
    `herdr-say --parent` into director.results/, every report 8 days old; a1 and a3 then gone
    from Herdr, a2 live. `octo-feather-start --director --resume` removes none: a1 and a3 just
    went (gone-since now, their `<session>.gone` beside the file), a2 is live. a1's gone-since
    backdated 8 days, a2's a stale one (live again): `octo-feather-handoff prune-results` as the
    director removes a1's file and marker only, clears a2's marker, keeps a3's (gone 0 days)."""
    d = herdr_world(s, {"w0:p1": agent("w0:p1", "director", "idle")})
    s.env["HERDR_SESSION"] = f"prune-{os.getpid()}"
    s.identity()
    s.git(s.root, "init", "-q", "-b", "main", "target")
    state = state_dir(s)
    (state / "lanes").mkdir(parents=True)
    (state / "director.toml").write_text('pane = "w0:p1"\n')
    hand = {"HERDR_PANE_ID": "w0:p1", "HERDR_WORKSPACE_ID": "w0"}
    files: dict[str, Path] = {}
    old = time.time() - 8 * 86400
    for n in ("a1", "a2", "a3"):
        spawn = [str(ASSETS / "herdr-spawn"), "--workspace", "w0", "--name", f"general-worker-{n}"]
        spawn += ["--label", n, "--role", "general-worker", "--cwd", str(s.root)]
        pane = dict(x.split("=", 1) for x in s.run(spawn, env=hand).out.split())["pane"]
        worker = tab_env(d, pane)
        s.run([SAY, "--parent", REPORT], env=worker)
        files[n] = reported(s, worker, "director")
        os.utime(files[n], (old, old))
        if n != "a2":
            drop(d, pane)
    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with (state / "director.handoffs.jsonl").open("a") as f:  # no background reflection
        f.write(json.dumps({"at": stamp, "kind": "reflection"}) + "\n")
    drop(d, "w0:p1")
    start(s, "--director", "--resume", "D1")
    gone = {n: f.with_suffix(".gone") for n, f in files.items()}
    assert all(f.is_file() for f in files.values()), "an old report of a just-gone worker removed"
    assert gone["a1"].is_file(), gone
    assert gone["a3"].is_file(), gone
    assert not gone["a2"].exists(), gone
    show("director start: kept every 8-day-old report (a1, a3 just gone, a2 live)")
    for n in ("a1", "a2"):
        gone[n].touch()
        os.utime(gone[n], (old, old))
    director = {"HERDR_PANE_ID": "w0:p9"}
    s.run([kit("octo-feather-handoff"), "prune-results"], env=director)
    assert not files["a1"].exists(), "a1 gone 8 days: its report kept"
    assert not gone["a1"].exists(), "a1 gone 8 days: its marker kept"
    assert files["a2"].is_file(), "a2 live: its report removed"
    assert not gone["a2"].exists(), "a2 live: its marker kept"
    assert files["a3"].is_file(), "a3 gone 0 days: its report removed"
    assert gone["a3"].is_file(), "a3 gone 0 days: its marker removed"
    left = sorted(p.name for p in results_dir(s, "director").iterdir())
    show(f"prune-results, a1 gone 8 days: removed {files['a1'].name}; left {left}")


RECORDS = {
    "indented": '# lane gh7\n  supervisor = "w1:p1"\nissue = 7\ngoal = "g # not a comment"\n',
    "odd": 'goal=\'g\'   # hand edit\n"supervisor"="w1:p1"\nissue=7\n',
    "absent": 'issue = 7\ngoal = "g"\n',
}


def repoint_record(s: Scratch) -> None:
    """`octo-feather-start --name gh7 --resume S` (a resume repoints the record: comms
    #octo-lane-record-key-supervisor) over lane records a hand edit shaped: an indented
    `supervisor` key with a comment, a quoted key and single-quoted strings with no spaces, and no
    `supervisor` key at all: each record parses after, every key equal but `supervisor`, now the
    resumed pane (comments are not kept). The records it refuses: repoint_refused."""
    d, state = repoint_world(s)
    record = state / "lanes" / "gh7.toml"
    for case, text in RECORDS.items():
        record.write_text(text)
        new = start(s, "--name", "gh7", "--resume", "S")["pane"]
        drop(d, new)  # gone again (a restart) before the next resume
        got = tomllib.loads(record.read_text())
        want = {k: v for k, v in tomllib.loads(text).items() if k != "supervisor"}
        assert got == {"supervisor": new, **want}, (case, record.read_text())
        show(f"resume over {case}: {record.read_text()!r}")


def repoint_refused(s: Scratch) -> None:
    """repoint_record's resume over a lane record holding a table or an array: the start still
    runs the agent, warns that the record was not repointed, naming the key, and the record is
    byte for byte unchanged; the director's hand-edited record (an indented `pane`) repointed
    through `--director --resume`, every other key equal."""
    d, state = repoint_world(s)
    record = state / "lanes" / "gh7.toml"
    for bad, key in (('supervisor = "w1:p1"\n[extra]\nx = 1\n', "extra"), ("ids = [1]\n", "ids")):
        record.write_text(bad)
        cmd = [kit("octo-feather-start"), "--cwd", str(s.root / "target")]
        ran = s.run([*cmd, "--name", "gh7", "--resume", "S"])
        drop(d, dict(x.split("=", 1) for x in ran.out.split())["pane"])
        assert "gh7's record not repointed to its new pane" in ran.err, ran.err
        assert f"key {key!r}" in ran.err, ran.err
        assert record.read_text() == bad, record.read_text()
        show(f"resume over a record holding {key}: record untouched, {ran.err.strip()}")
    director = state / "director.toml"
    director.write_text('    pane = "w0:p1"\nname = "d"\n')
    drop(d, "w0:p1")
    new = start(s, "--director", "--resume", "D")["pane"]
    assert tomllib.loads(director.read_text()) == {"pane": new, "name": "d"}, director.read_text()


def repoint_world(s: Scratch) -> tuple[Path, Path]:
    """The resumes' world: director w0:p1 live, a target repo, the state dir's lanes/ and a
    reflection just run (none in the background). The Herdr world and the state dir."""
    d = herdr_world(s, {"w0:p1": agent("w0:p1", "director", "idle")})
    s.env["HERDR_SESSION"] = f"repoint-{os.getpid()}"
    s.identity()
    s.git(s.root, "init", "-q", "-b", "main", "target")
    state = state_dir(s)
    (state / "lanes").mkdir(parents=True)
    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with (state / "director.handoffs.jsonl").open("a") as f:  # no background reflection
        f.write(json.dumps({"at": stamp, "kind": "reflection"}) + "\n")
    return d, state


ODD_ANSWERS = ('{"result": {"agent": null}}', '{"result": {"agent": {}}}', "not json", "{}")


def herdr_malformed(s: Scratch) -> None:
    """`herdr agent get` answering exit 0 with a shape that is no agent (agent null, an agent with
    no pane or status, not JSON, no result): `octo-feather-handoff results` shows that worker
    `unknown (...)` with `none yet`, never `ended` nor `live None`; a director result file 8 days
    old whose worker gets such an answer is kept by `prune-results`, its gone-since clock not
    started. Only Herdr's explicit agent_not_found is absence: it starts the clock, and the file
    goes once that is 8 days old."""
    d, sup, impl = supervised(s)
    for raw in ODD_ANSWERS:
        (d / "get-answer").write_text(json.dumps({"implementer-gh7": raw}))
        out = s.run([kit("octo-feather-handoff"), "results"], env=tab_env(d, sup["pane"])).out
        name, pane, state, result = out.splitlines()[0].split("\t")
        assert (name, pane, result) == ("implementer-gh7", impl["HERDR_PANE_ID"], "none yet"), out
        assert state.startswith("unknown ("), out
        show(f"agent get answered {raw}: {out.strip()}")
    files = results_dir(s, "director")
    files.mkdir()
    old = files / "S-old.md"
    old.write_text("## report\n")
    then = time.time() - 8 * 86400
    os.utime(old, (then, then))
    spawn = {
        "at": "2026-11-01T00:00:00Z",
        "kind": "spawn",
        "name": "general-worker-a9",
        "session": "S-old",
    }
    with (state_dir(s) / "director.handoffs.jsonl").open("a") as f:
        f.write(json.dumps(spawn) + "\n")
    marker = old.with_suffix(".gone")
    for raw in ODD_ANSWERS:
        (d / "get-answer").write_text(json.dumps({"general-worker-a9": raw}))
        s.run([kit("octo-feather-handoff"), "prune-results"])
        assert old.is_file(), f"pruned on {raw}"
        assert not marker.exists(), f"gone-since started on {raw}"
    (d / "get-answer").unlink()
    s.run([kit("octo-feather-handoff"), "prune-results"])
    assert old.is_file(), "agent_not_found: the report removed at once"
    assert marker.is_file(), "agent_not_found: gone-since not started"
    os.utime(marker, (then, then))
    s.run([kit("octo-feather-handoff"), "prune-results"])
    assert not old.is_file(), "a worker gone 8 days: its report kept"
    show("prune: no clock on an odd answer; agent_not_found starts it; removed 8 days on")


def merged_repo(s: Scratch) -> tuple[Path, str]:
    """A repo whose main merged PR 7 (head H, changing a role file): its dir and H."""
    r = s.root / "repo"
    s.run(["git", "init", "-q", "-b", "main", str(r)])
    (r / "agents").mkdir()
    (r / "agents" / "supervisor.md").write_text("a\n")
    s.git(r, "add", "-A")
    s.git(r, "commit", "-qm", "base")
    s.git(r, "checkout", "-qb", "gh7")
    (r / "agents" / "supervisor.md").write_text("b\n")
    s.git(r, "commit", "-qam", "change")
    head = s.git(r, "rev-parse", "HEAD")
    s.git(r, "checkout", "-q", "main")
    s.git(r, "merge", "-q", "--no-ff", "gh7", "-m", "Merge #7")
    return r, head


def post_merge_busy(s: Scratch) -> None:
    """post-merge after PR 7 merged, lane live1's supervisor w1:p1 busy (working the whole run),
    lane live2's w2:p1 idle: step 6 returns within its bound; live2 told (its prod line), live1
    NOT told, named with its pane, the timeout, its state and the herdr-say that re-sends it by
    hand, no prod line; the summary names live1 NOT told; exit 1."""
    busy = agent("w1:p1", "live1", "working")
    d = herdr_world(s, {"w1:p1": busy, "w2:p1": agent("w2:p1", "live2", "idle")})
    r, head = merged_repo(s)
    merge = s.git(r, "rev-parse", "HEAD")
    url = "https://github.com/o/r/pull/7"
    s.gh.put(
        7,
        {
            "state": "MERGED",
            "headRefOid": head,
            "mergeCommit": {"oid": merge},
            "baseRefName": "main",
            "headRefName": "gh7",
            "title": "Add foo",
            "url": url,
        },
    )
    run = {"databaseId": 1, "status": "completed", "conclusion": "success"}
    s.gh.store("run/1.json", run | {"workflowName": "check", "url": f"{url}/checks"})
    # Step 3 asks `gh repo view` for the PR's repo and the kit install's origin: the fake gh knows
    # only o/r, so a gh first on PATH names the install's origin o/kit (step 3 then leaves it).
    gh = s.root / "ghbin"
    gh.mkdir()
    (gh / "gh").write_text(
        '#!/bin/sh\n[ "$1 $2 $3" = "repo view https://github.com/o/kit.git" ] && '
        'exec echo \'{"nameWithOwner": "o/kit"}\'\n'
        '[ "$1 $2" = "repo view" ] && exec echo \'{"nameWithOwner": "o/r"}\'\n'
        f'exec {s.bin}/gh "$@"\n'
    )
    (gh / "gh").chmod(0o755)
    kit_clone = s.root / "kit"
    s.run(["git", "clone", "-q", str(r), str(kit_clone)])
    s.git(kit_clone, "remote", "set-url", "origin", "https://github.com/o/kit.git")
    lanes = s.home / ".local" / "state" / "octo-feather" / "lanes"
    lanes.mkdir(parents=True)
    for n, issue in ((1, 11), (2, 12)):
        (lanes / f"live{n}.toml").write_text(
            f'supervisor = "w{n}:p1"\nrepository = "o/r"\nissue = {issue}\ngoal = "g"\n'
            'started_at = "2026-11-06T00:00:00Z"\n'
        )
    env = s.env | {
        "PATH": f"{gh}{os.pathsep}{ASSETS}{os.pathsep}{s.env['PATH']}",
        "OCTO_FEATHER_KIT_INSTALL": str(kit_clone),
    }
    cmd = [kit("octo-feather-lane"), "post-merge", "7", head, "--lane", "gh7", "--repo", "o/r"]
    t0 = time.monotonic()
    p = subprocess.run(
        [*cmd, "--wait", "0"],
        cwd=r,
        env=env,
        capture_output=True,
        text=True,
        timeout=TELL_BOUND + 60,
        check=False,
    )
    took = time.monotonic() - t0
    said = f"exit {p.returncode} after {took:.0f}s\n{p.stdout}\n{p.stderr}"
    assert p.returncode == 1, said
    assert took < TELL_BOUND + 20, said
    tell = next((x for x in p.stdout.splitlines() if x.startswith("step 6 ")), "")
    assert tell.startswith("step 6 tell supervisors: stopped: NOT told: live1 w1:p1: "), said
    assert f"send timed out after {TELL_BOUND}s" in tell, said
    assert f"w1:p1 (pane w1:p1) still working after {TELL_BOUND}s" in tell, said
    assert "re-send by hand: herdr-say w1:p1 'main moved to " in tell, said
    assert "; NOT told: live1 w1:p1; told: live2 w2:p1;" in tell, said
    last = p.stdout.splitlines()[-1]
    want = "step 7 teardown not run; NOT told: live1 w1:p1 (step 6 names each re-send)"
    assert last.endswith(f"step 6 tell supervisors stopped; {want}"), said
    assert [x.split("\t")[0] for x in lines(d / "prompts")] == ["w1:p1", "w2:p1"], said
    prods = [json.loads(x) for x in lines(lanes.parent / "director.handoffs.jsonl")]
    assert [x["issue"] for x in prods] == [12], said


# A kit install's recipes step 3's refresh runs (by the real just): nothing to fetch or check.
TELL_JUSTFILE = "vendored-fetch:\n    @true\n\ninstall-check target:\n    @true\n"
RULED = ".agents/skills/foo/SKILL.md, agents/supervisor.md"
REREAD = "re-read the changed ones before your next step."


def build_tell(p: Scratch) -> None:
    """repo: main merged gh7 (two rule files and a product file changed) then gh8 (a file under
    no rule path); kit: a clone of it at main, its origin o/kit (Tell fetches it from repo);
    shas.json: each merge commit and the head it merged."""
    r = p.root / "repo"
    p.run(["git", "init", "-q", "-b", "main", str(r)])
    for f, text in (("agents/supervisor.md", "a"), ("src/app.py", "a"), ("docs/notes.md", "a")):
        (r / f).parent.mkdir(parents=True, exist_ok=True)
        (r / f).write_text(text + "\n")
    (r / "justfile").write_text(TELL_JUSTFILE)
    p.git(r, "add", "-A")
    p.git(r, "commit", "-qm", "base")
    for branch, files in (
        ("gh7", ("agents/supervisor.md", ".agents/skills/foo/SKILL.md", "src/app.py")),
        ("gh8", ("docs/notes.md",)),
    ):
        p.git(r, "checkout", "-qb", branch)
        for f in files:
            (r / f).parent.mkdir(parents=True, exist_ok=True)
            (r / f).write_text(f"{branch}\n")
        p.git(r, "add", "-A")
        p.git(r, "commit", "-qm", "change")
        p.git(r, "checkout", "-q", "main")
        p.git(r, "merge", "-q", "--no-ff", branch, "-m", f"Merge #{branch[2:]}")
    k = p.root / "kit"
    p.run(["git", "clone", "-q", str(r), str(k)])
    p.git(k, "remote", "set-url", "origin", "https://github.com/o/kit.git")
    log = p.git(r, "log", "--first-parent", "--format=%H %P", "main").splitlines()
    (m2, _, h2), (m, _, h) = (x.split() for x in log[:2])
    (p.root / "shas.json").write_text(json.dumps({"m": m, "h": h, "m2": m2, "h2": h2}))


class Tell:
    """The prepared repo and kit install in S, its lanes and director log, Herdr's world, the
    kit's herdr-say and herdr-close on PATH; `run` runs post-merge from the repo."""

    def __init__(self, s: Scratch) -> None:
        s.prepare("lane-post-merge-tell", build_tell)
        self.s, self.r = s, s.root / "repo"
        self.d = herdr_world(s)
        s.env.pop("GH_REPO", None)
        st = s.root / "state" / "octo-feather"
        self.lanes, self.dlog = st / "lanes", st / "director.handoffs.jsonl"
        self.lanes.mkdir(parents=True)
        rec = s.root / "rec"
        rec.mkdir()
        for n in ("uv", "pnpm"):  # step 3's refresh reaching the registries: argv_recorder.sh
            (rec / n).symlink_to(HERE / "argv_recorder.sh")
        s.env |= {
            "XDG_STATE_HOME": str(s.root / "state"),
            "OCTO_FEATHER_KIT_INSTALL": str(s.root / "kit"),
            "ARGV_LOG": str(s.root / "argv.log"),
            "PATH": os.pathsep.join([str(rec), str(ASSETS), s.env["PATH"]]),
            # The kit install's origin, o/kit, is this copy's repo: a url rewrite in git's env
            # (no git call; the prepared tree's path is not this copy's).
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": f"url.{self.r}.insteadOf",
            "GIT_CONFIG_VALUE_0": "https://github.com/o/kit.git",
        }
        shas = json.loads((s.root / "shas.json").read_text())
        self.m, self.h, self.m2, self.h2 = (shas[k] for k in ("m", "h", "m2", "h2"))
        s.gh.store("repo.json", {"nameWithOwner": "o/r"})
        s.gh.store("api/repos/o/kit.json", {"nameWithOwner": "o/kit"})
        run = {"databaseId": 1, "status": "completed", "conclusion": "success"}
        url = "https://github.com/o/r/actions/runs/1"
        s.gh.store("run/1.json", run | {"workflowName": "check", "url": url})
        self.store("o/r", "Add foo")

    def store(self, repo: str, title: str) -> None:
        """PRs 7 (TITLE, of REPO) and 8 (Notes, of o/r), merged."""
        for n, head, merge, t, at in (
            (7, self.h, self.m, title, repo),
            (8, self.h2, self.m2, "Notes", "o/r"),
        ):
            pr = {
                "state": "MERGED",
                "headRefOid": head,
                "mergeCommit": {"oid": merge},
                "baseRefName": "main",
                "headRefName": f"gh{n}",
                "title": t,
                "url": f"https://github.com/{at}/pull/{n}",
            }
            self.s.gh.put(n, pr)

    def lane(self, name: str, pane: str, repo: str, issue: int) -> None:
        (self.lanes / f"{name}.toml").write_text(
            f'supervisor = "{pane}"\nrepository = "{repo}"\nissue = {issue}\ngoal = "g"\n'
            'started_at = "2026-10-29T00:00:00Z"\n'
        )

    def parked(self, lane: str, pane: str, at: str) -> None:
        line = {"at": at, "kind": "parked", "pane": pane, "name": lane}
        with (self.lanes / f"{lane}.handoffs.jsonl").open("a") as f:
            f.write(json.dumps(line) + "\n")

    def live(self, *panes: str, blocked: str = "") -> None:
        """Herdr's agents: PANES live (idle), BLOCKED (one of them) on a dialog."""
        live = {p: agent(p, p, "blocked" if p == blocked else "idle") for p in panes}
        (self.d / "agents.json").write_text(json.dumps(live))

    def run(self, want: int, pr: int, *args: str) -> tuple[str, str]:
        """post-merge PR (its head) ARGS --wait 0, exit WANT, no traceback: its step 6 line and
        its last line. Each run a fresh routine: the post-merge records removed first (a rerun's
        resume: tests/gate/kit/lane_merge.py)."""
        shutil.rmtree(self.lanes.parent / "post-merge", ignore_errors=True)
        head = self.h if pr == 7 else self.h2
        cmd = [kit("octo-feather-lane"), "post-merge", str(pr), head, *args, "--wait", "0"]
        ran = self.s.run(cmd, want=want, cwd=self.r)
        tell = [x for x in ran.out.splitlines() if re.match(r"step [0-9]+ tell supervisors: ", x)]
        assert tell, f"no tell supervisors line: {ran.out}"
        self.out = ran.out
        return tell[0], ran.out.splitlines()[-1]

    def said(self) -> list[str]:
        """Each pane a send was tried to, sorted; each send bounded by post-merge's bound."""
        sends = [x for x in lines(self.d / "log") if x.startswith("agent prompt ")]
        bound = f" --timeout {TELL_BOUND * 1000}"
        assert all(x.endswith(bound) for x in sends), f"a send without{bound}: {sends}"
        return sorted(x.split()[2] for x in sends)

    def told(self) -> list[str]:
        return [x.split("\t", 1)[1] for x in lines(self.d / "prompts")]

    def prods(self) -> list[dict[str, object]]:
        return [json.loads(x) for x in lines(self.dlog)]

    def clear(self) -> None:
        """The sends, Herdr's call log and the director log emptied."""
        for f in (self.d / "log", self.d / "prompts", self.dlog):
            f.write_text("")


def told_live(t: Tell) -> None:
    """tell_supervisors' first phase: live, parked and another repo's lanes; a rerun; a merge
    with no rule file."""
    t.lane("gh7", "zt0:p1", "o/r", 7)
    t.lane("live1", "zt1:p1", "o/r", 11)
    t.lane("parked", "zt2:p1", "o/r", 12)
    t.lane("other", "zt3:p1", "x/y", 13)
    t.parked("parked", "zt2:p0", "2026-10-28T00:00:00Z")
    t.parked("parked", "zt2:p1", "2026-10-29T00:00:00Z")
    t.live("zt0:p1", "zt1:p1", "zt3:p1")
    earlier = '{"at": "2026-10-29T00:00:00+00:00", "kind": "prod", "issue": 11, "note": "earlier"}'
    t.dlog.write_text(earlier + "\n")
    tell, last = t.run(3, 7, "--lane", "gh7", "--repo", "o/r")
    assert t.said() == ["zt1:p1"], t.said()
    want = f"main moved to {t.m[:12]} (#7 Add foo); rule files changed: {RULED}; {REREAD}"
    assert t.told() == [want], t.told()
    assert "told: live1 zt1:p1" in tell, tell
    gone = "gone: director to resume or archive: none"
    assert tell.endswith(f"not woken: parked zt2:p1; {gone}"), tell
    assert last.endswith("tell supervisors ok; step 7 teardown pending"), last
    assert "agent get zt3:p1" not in lines(t.d / "log"), lines(t.d / "log")
    prods = t.prods()
    assert len(prods) == 2, prods
    note = f"post-merge {t.m} #7: main moved, told live1 to re-read {RULED}"
    p = prods[1]
    assert sorted(p) == ["at", "issue", "kind", "note"], p
    assert (p["kind"], p["issue"], p["note"]) == ("prod", 11, note), p
    assert re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9:.]+\+00:00", str(p["at"])), p
    tell, _ = t.run(3, 7, "--lane", "gh7", "--repo", "o/r")
    assert len(t.told()) == 1, f"rerun sent again: {t.told()}"
    assert len(t.prods()) == 2, f"rerun logged again: {t.prods()}"
    assert "already told: live1" in tell, tell
    assert "not woken: parked zt2:p1" in tell, tell
    t.run(3, 8, "--lane", "gh7", "--repo", "o/r")
    none = f"main moved to {t.m2[:12]} (#8 Notes); rule files changed: none; {REREAD}"
    assert t.told()[-1] == none, t.told()
    assert t.prods()[-1]["note"] == f"post-merge {t.m2} #8: main moved, told live1 to re-read none"


def told_kit(t: Tell) -> None:
    """tell_supervisors' kit PR phase: the sends and the director log emptied first."""
    t.store("o/kit", "Kit rule")
    t.clear()
    t.run(3, 7, "--lane", "gh7", "--repo", "o/kit")
    assert t.said() == ["zt1:p1", "zt3:p1"], f"{t.said()}: {t.out}"
    assert sorted(int(str(p["issue"])) for p in t.prods()) == [11, 13], t.prods()


def told_failed(t: Tell) -> None:
    """tell_supervisors' failed send phase, on the o/r PR again: live2 added, live1 blocked on
    a dialog (the kit's herdr-say exits 75)."""
    t.store("o/r", "Add foo")
    t.clear()
    t.lane("live2", "zt4:p1", "o/r", 14)
    t.live("zt0:p1", "zt1:p1", "zt3:p1", "zt4:p1", blocked="zt1:p1")
    tell, last = t.run(1, 7, "--lane", "gh7", "--repo", "o/r")
    assert t.said() == ["zt1:p1", "zt4:p1"], t.said()
    assert "stopped: " in tell, tell
    assert "herdr-say failed: live1 zt1:p1 exit 75" in tell, tell
    assert "told: live2 zt4:p1" in tell, tell
    assert [p["issue"] for p in t.prods()] == [14], t.prods()
    assert "tell supervisors stopped" in last, last
    t.live("zt0:p1", "zt1:p1", "zt3:p1", "zt4:p1")
    t.run(3, 7, "--lane", "gh7", "--repo", "o/r")
    assert t.said() == ["zt1:p1", "zt1:p1", "zt4:p1"], f"retry: {t.said()}"
    assert [p["issue"] for p in t.prods()] == [14, 11], t.prods()


def told_gone(t: Tell) -> None:
    """tell_supervisors' issue 458 phase: every lane record and hand-off log replaced first."""
    for f in t.lanes.iterdir():
        f.unlink()
    t.clear()
    t.lane("live1", "zt1:p1", "o/r", 11)
    t.lane("parked", "zt2:p1", "o/r", 12)
    t.lane("gone", "zt5:p1", "o/r", 15)
    t.lane("moved", "zt6:p1", "o/r", 16)
    t.parked("parked", "zt2:p1", "2026-10-29T00:00:00Z")
    t.parked("moved", "zt6:p1", "2026-10-28T00:00:00Z")
    t.parked("moved", "zt6:p0", "2026-10-29T00:00:00Z")
    t.live("zt1:p1")
    gone = "gone: director to resume or archive: gone zt5:p1, moved zt6:p1"
    tell, _ = t.run(3, 7, "--lane", "gh1", "--repo", "o/r")
    assert t.said() == ["zt1:p1"], t.said()
    want = "told: live1 zt1:p1; already told: none; not woken: parked zt2:p1; " + gone
    assert tell.startswith("step 6 tell supervisors: ok: "), tell
    assert tell.endswith(want), tell
    pending = "step 7 teardown: pending: lane gh1 not archived; rerun on its close report"
    assert pending in t.out.splitlines(), t.out
    # Archived: step 7 runs the kit's herdr-close on space zt9, which Herdr has not: its close
    # fails, and Herdr's workspace_not_found (stderr) reads as already closed.
    (t.lanes / "archive").mkdir()
    (t.lanes.parent / "director.toml").write_text('pane = "zt0:p9"\n')
    t.s.git(t.r, "remote", "add", "origin", str(t.r))
    (t.lanes / "archive" / "gh1.toml").write_text(
        'supervisor = "zt9:p1"\nrepository = "o/r"\nissue = 1\npr = 7\ngoal = "g"\n'
        'started_at = "2026-10-29T00:00:00Z"\n'
    )
    t.run(0, 7, "--lane", "gh1", "--repo", "o/r")
    down = (
        "step 7 teardown: ok: space zt9 already closed; worktree of gh1 already removed; no open "
        "PR based on gh1; local branch gh1 already deleted; remote branch gh1 already deleted "
        "from origin"
    )
    assert down in t.out.splitlines(), t.out
    log = lines(t.d / "log")
    assert "workspace close zt9" in log, f"herdr-close asked no close: {log}"
    assert "workspace get zt9" in log, f"teardown asked no workspace get: {log}"
    # Any other herdr failure still stops step 6, named; the other lanes are still handled.
    (t.lanes / "archive" / "gh1.toml").unlink()
    (t.d / "get-down").write_text("zt2:p1\n")
    tell, _ = t.run(1, 7, "--lane", "gh1", "--repo", "o/r")
    stop = (
        "step 6 tell supervisors: stopped: parked zt2:p1: herdr agent get zt2:p1 failed (herdr: "
        "server not reachable)"
    )
    assert tell.startswith(stop), tell
    assert tell.endswith(gone), tell


def tell_supervisors(s: Scratch) -> None:
    """Only a live supervisor of the PR's repo gets one message naming the merge commit, PR,
    title and changed rule files, by the kit's herdr-say bounded by post-merge's bound; the --lane
    lane, a parked one (its latest parked line names its pane) and another repo's lane (never
    looked up) none; one canonical prod line per lane told, after the director's own; step 6 ok,
    step 7 pending, exit 3. A rerun sends and logs nothing new (already told). A merge touching no
    rule file says none, and is told again. A kit PR (o/kit, the install's own repo): every lane
    runs kit roles, so another repo's live lane is told too, one prod line each (step 3 refreshes
    the install first: its recipes no-ops by the real just, uv and pnpm argv_recorder.sh). A send
    that fails (its supervisor blocked on a dialog, herdr-say's 75): named, no prod line for it,
    the others still tried and told, the step stopped, exit 1; a rerun tells only that one. Issue
    458: --lane gh1 with a live, a parked and two gone lanes (one never parked, one whose latest
    parked line names an older pane): only the live one told, the rest listed, step 6 ok, step 7
    pending (not archived). Archived: step 7 runs, the kit's herdr-close failing and Herdr's
    workspace_not_found read as already closed. Any other herdr failure (Herdr unreachable on the
    parked lane's lookup) stops step 6, named, the other lanes still handled. One
    world, the old test's order: each phase resets only what it names."""
    t = Tell(s)
    told_live(t)
    told_kit(t)
    told_failed(t)
    told_gone(t)


COMPLETION = "DONE commit abc123: the completion"
WORKER = {
    "OCTO_FEATHER_ROLE": "implementer",
    "OCTO_FEATHER_PARENT": "w1:p1",
    "HERDR_PANE_ID": "w1:p2",
    "HERDR_WORKSPACE_ID": "w1",
}


def queued_completion(s: Scratch) -> None:
    """comms #acceptance-queued-completion: an implementer's `herdr-say --parent COMPLETION`
    while its supervisor w1:p1 compacts for 2 s, Herdr confirming nothing (agent_prompt_stalled)
    and the supervisor's pane showing COMPLETION queued: herdr-say exits 0 only after compaction
    ended, the supervisor received COMPLETION once, one prompt was sent. Compaction outlasting
    the bound: no resend, a non-zero exit naming it queued, nothing received yet, no alert to the
    director w0:p1. Each observation printed, for the verify drive."""
    say = str(ASSETS / "herdr-say")
    compacting = agent("w1:p1", "gh7", "idle") | {"compacting_until": time.time() + 2}
    d = herdr_world(s, {"w1:p1": compacting, "w0:p1": agent("w0:p1", "director", "idle")})
    t0 = time.monotonic()
    ran = s.run([say, "--parent", COMPLETION], env=WORKER)
    took = time.monotonic() - t0
    got = [x for x in lines(d / "prompts") if x.startswith("w1:p1\t")]
    sent = [x for x in lines(d / "log") if x.startswith("agent prompt ")]
    sys.stdout.write(f"herdr-say exit 0 after {took:.1f}s: {ran.err}\n")
    sys.stdout.write(f"delivered {len(got)}, attempts {len(sent)}\n")
    assert got == [f"w1:p1\t{COMPLETION}"], lines(d / "prompts")
    assert len(sent) == 1, sent
    assert took >= 2, f"exit 0 before compaction ended, after {took:.1f}s"
    assert "queued" in ran.err, ran.err

    (s.root / "long").mkdir()
    s2 = Scratch(s.root / "long")
    long = agent("w1:p1", "gh7", "idle") | {"compacting_until": time.time() + 3600}
    d = herdr_world(s2, {"w1:p1": long, "w0:p1": agent("w0:p1", "director", "idle")})
    ran = s2.run([say, "--timeout", "1", "--parent", COMPLETION], want=1, env=WORKER)
    sent = [x for x in lines(d / "log") if x.startswith("agent prompt ")]
    sys.stdout.write(f"still compacting at the bound: exit 1: {ran.err.splitlines()[-1]}\n")
    sys.stdout.write(f"delivered {len(lines(d / 'prompts'))}, attempts {len(sent)}\n")
    assert lines(d / "prompts") == [], lines(d / "prompts")
    assert len(sent) == 1, sent
    assert "queued" in ran.err.splitlines()[-1], ran.err
    assert "not resent" in ran.err.splitlines()[-1], ran.err


def fresh_worker_session(s: Scratch) -> None:
    """roles #acceptance-fresh-independent-worker, its provider-session half, through the real
    herdr-spawn and herdr-close: supervisor zt1:p0 spawns implementer-gh13 for #13 and closes it
    (assignment done); its spawn for the independent #14, implementer-gh14, prints another
    provider_session_id, and Pi is started with that --session-id; a --resume of the closed session
    (the same unfinished assignment only) reuses it. Space zt1: no real Herdr gives it, so
    herdr-close's sweep reaches no box process. Each observation printed, for the qc demo."""
    d = herdr_world(s)
    s.identity()
    sup = SUPERVISOR | {"HERDR_PANE_ID": "zt1:p0", "HERDR_WORKSPACE_ID": "zt1"}

    def spawn(name: str, *more: str) -> dict[str, str]:
        wt = s.root / f"wt-{name}"
        wt.mkdir(exist_ok=True)
        argv = [str(ASSETS / "herdr-spawn"), "--workspace", "zt1", "--name", name, "--label", name]
        out = s.run([*argv, "--role", "implementer", "--cwd", str(wt), *more], env=sup).out
        got = dict(x.split("=", 1) for x in out.split())
        starts = [x for x in lines(d / "log") if x.startswith(f"agent start {name} ")]
        assert f" --session-id {got['provider_session_id']} " in f"{starts[-1]} ", starts
        show(f"herdr-spawn --name {name} {' '.join(more)}: {out}")
        return got

    closed = spawn("implementer-gh13")
    s.run([str(ASSETS / "herdr-close"), closed["tab"]], env=sup)
    show(f"herdr-close {closed['tab']}: implementer-gh13's assignment closed")
    fresh = spawn("implementer-gh14")
    assert fresh["provider_session_id"] != closed["provider_session_id"], (closed, fresh)
    resumed = spawn("implementer-gh13", "--resume", closed["provider_session_id"])
    assert resumed["provider_session_id"] == closed["provider_session_id"], (closed, resumed)


if __name__ == "__main__":
    main(
        spawn_ready_late,
        spawn_fails_closed,
        spawn_one_bound,
        say_resumes_parked,
        say_lookup_fails,
        say_stalled,
        post_merge_busy,
        tell_supervisors,
        worker_route,
        parent_gone,
        director_worker_resume,
        queued_completion,
        fresh_worker_session,
        parent_resumed,
        director_moved,
        result_compacting,
        result_resumed,
        results_listing,
        director_prune,
        repoint_record,
        repoint_refused,
        herdr_malformed,
    )
