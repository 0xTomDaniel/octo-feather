"""Herdr messaging never fails silently or hangs (#666; #585, #619; owner rulings #585 and #619
2026-11-05), through the commands with the testkit's Herdr stand-in (testkit/herdr.py, its
FAKE_HERDR world): herdr-spawn returns only once its agent reads idle on `herdr agent wait`, so
an agent that turns ready late is not returned early, and a herdr-say right after it is
delivered; a herdr-say whose `herdr agent get` lookup fails names that lookup (not the up-chain
refusal, 77); a prompt Herdr reports stalled exits non-zero naming the pane and its state; and
`octo-feather-lane post-merge` step 4 to a busy (working) supervisor returns within its bound,
its step 4 line naming the supervisor NOT told (lane, pane, timeout, the re-send command) and going
on to tell the others (director rule #619). A general worker routes like every worker (roles
spec #acceptance-task-worker-route): its parent reached, a peer lane refused (77); and a worker
never messages the director: its parent proven gone, herdr-say itself sends the director one
fixed alert, a timeout or a stall none (comms spec #acceptance-parent-gone). The director parks
its own general worker into the director log and its next message resumes it, with its recorded
role, session and parent, in its parent's workspace (comms spec
#acceptance-director-worker-resume); a parked lane worker still resumes as before."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

from testkit import ROOT, Scratch, kit, main

ASSETS = ROOT / ".agents" / "skills" / "herdr-comms" / "assets"
TELL_BOUND = 20  # post-merge step 4's bound on one send, seconds (octo-feather-lane --help)


def herdr_world(s: Scratch, agents: dict[str, dict[str, object]] | None = None) -> Path:
    """S's Herdr: the stand-in's agents world, holding AGENTS, the caller's Herdr and kit
    variables cleared (a scenario's caller is no pane unless it sets one)."""
    d = s.root / "herdr"
    d.mkdir()
    (d / "agents.json").write_text(json.dumps(agents or {}))
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
    """An agent that turns idle 2 s after its start: herdr-spawn returns only once Herdr reads it
    idle (never while it still boots), and a herdr-say to its pane right after is delivered,
    nothing left typed and unsent."""
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
    """A process standing in for the agent at PANE: it runs in CWD under the env herdr-spawn gave
    PANE's tab, with Herdr's own ids, as herdr-close --park reads them from /proc."""
    g = json.loads((d / "agents.json").read_text())[pane]
    ids = {"HERDR_PANE_ID": pane, "HERDR_TAB_ID": g["tab_id"]}
    env = s.env | g["env"] | ids | {"HERDR_WORKSPACE_ID": g["workspace_id"]}
    p = subprocess.Popen(["sleep", "300"], cwd=cwd, env=env, start_new_session=True)  # noqa: S607
    for _ in range(100):  # until exec'd, so its environ is the tab's
        if Path(f"/proc/{p.pid}/environ").read_bytes().find(b"HERDR_TAB_ID=") >= 0:
            break
        time.sleep(0.02)
    return p


def resumed_as(d: Path, out: str, space: str, session: str) -> tuple[str, dict[str, str]]:
    """The pane herdr-say printed (pane=), asserted resumed in SPACE with SESSION; its tab env."""
    pane = next(x.removeprefix("pane=") for x in out.split() if x.startswith("pane="))
    g = json.loads((d / "agents.json").read_text())[pane]
    assert g["workspace_id"] == space, (space, g)
    assert g["env"]["OCTO_FEATHER_SESSION_ID"] == session, g
    starts = [x for x in lines(d / "log") if x.startswith(f"agent start {g['name']} ")]
    assert starts[-1].endswith(f"--session-id {session}"), starts
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
        assert worker.wait(timeout=10) is not None
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
    lane live2's w2:p1 idle: step 4 returns within its bound; live2 told (its prod line), live1
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
    tell = next((x for x in p.stdout.splitlines() if x.startswith("step 4 ")), "")
    assert tell.startswith("step 4 tell supervisors: stopped: NOT told: live1 w1:p1: "), said
    assert f"send timed out after {TELL_BOUND}s" in tell, said
    assert f"w1:p1 (pane w1:p1) still working after {TELL_BOUND}s" in tell, said
    assert "re-send by hand: herdr-say w1:p1 'main moved to " in tell, said
    assert "; NOT told: live1 w1:p1; told: live2 w2:p1;" in tell, said
    last = p.stdout.splitlines()[-1]
    want = "step 5 teardown not run; NOT told: live1 w1:p1 (step 4 names each re-send)"
    assert last.endswith(f"step 4 tell supervisors stopped; {want}"), said
    assert [x.split("\t")[0] for x in lines(d / "prompts")] == ["w1:p1", "w2:p1"], said
    prods = [json.loads(x) for x in lines(lanes.parent / "director.handoffs.jsonl")]
    assert [x["issue"] for x in prods] == [12], said


if __name__ == "__main__":
    main(
        spawn_ready_late,
        say_lookup_fails,
        say_stalled,
        post_merge_busy,
        worker_route,
        parent_gone,
        director_worker_resume,
    )
