"""Herdr messaging never fails silently or hangs (#666; #585, #619; owner rulings #585 and #619
2026-11-05), through the commands with the testkit's Herdr stand-in (testkit/herdr.py, its
FAKE_HERDR world): herdr-spawn returns only once its agent reads idle on `herdr agent wait`, so
an agent that turns ready late is not returned early, and a herdr-say right after it is
delivered; a herdr-say whose `herdr agent get` lookup fails names that lookup (not the up-chain
refusal, 77); a prompt Herdr reports stalled exits non-zero naming the pane and its state; and
`octo-feather-lane post-merge` step 4 to a busy (working) supervisor returns within its bound,
its step 4 line naming the supervisor NOT told (lane, pane, timeout, the re-send command) and going
on to tell the others (director rule #619)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from typing import TYPE_CHECKING

from testkit import ROOT, Scratch, kit, main

if TYPE_CHECKING:
    from pathlib import Path

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


if __name__ == "__main__":
    main(spawn_ready_late, say_lookup_fails, say_stalled, post_merge_busy, queued_completion)
