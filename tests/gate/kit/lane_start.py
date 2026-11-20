"""The scenarios of tests/gate/kit/test_lane_start.py (its items), this file their command
(testkit.main): `octo-feather-lane start`, the director's lane start (issue-lifecycle spec
#acceptance-lane-start; issue 1155), offline.

Seam (ticket #1155, recorded before any test): `octo-feather-lane start` run as a command, the
testkit's herdr and gh stand-ins first on PATH (testkit/herdr.py's FAKE_HERDR world,
testkit/gh.py's store holding repo o/r and its open issue 905), the real octo-feather-start and
herdr-spawn behind it. The target is a scratch clone of a local origin whose main moved after the
clone, so the lane branch must come from origin's main as fetched, not the checkout's stale main.

  started  run from the director's pane w0:p1 in the checkout: the lane workspace labelled gh905
           holds the supervisor gh905 (tab supervisor); the worktree <checkout>-gh905 is on branch
           gh905 at origin's main; lanes/gh905.toml holds exactly comms #lane-record's keys at
           launch; the supervisor received the goal, then the brief (its generated header, then
           the file's text) and nothing else; the director log holds one prod line for the lane
           (beside the spawn line herdr-spawn writes for the director's spawn); it printed
           `key=gh905 pane=<pane> issue=905`. Each observation printed, for the qc demo.
"""

from __future__ import annotations

import json
import re
import sys
from typing import TYPE_CHECKING

import tomllib
from testkit import Scratch, kit, main

if TYPE_CHECKING:
    from pathlib import Path

TITLE = "Lane start as one command"
OUTCOME = "a scratch proof"
BRIEF = "Build the lane start.\nSpec: docs/specs/issue-lifecycle.spec.html\n"
DIRECTOR = {"OCTO_FEATHER_ROLE": "director", "HERDR_PANE_ID": "w0:p1", "HERDR_WORKSPACE_ID": "w0"}


def show(line: str) -> None:
    """One observation on stdout, for the qc demo's output."""
    sys.stdout.write(line + "\n")


def world(s: Scratch) -> tuple[Path, Path, str]:
    """S's Herdr (director w0:p1, idle), its state dir with director.toml, GitHub (repo o/r, open
    issue 905) and the target: origin with main moved past the director's clone. The Herdr world
    dir, the checkout and origin's main."""
    d = s.root / "herdr"
    d.mkdir()
    director = {"name": "director", "pane_id": "w0:p1", "workspace_id": "w0", "tab_id": "w0:t1"}
    (d / "agents.json").write_text(json.dumps({"w0:p1": director | {"agent_status": "idle"}}))
    for k in [k for k in s.env if k.startswith(("HERDR_", "OCTO_FEATHER_"))]:
        del s.env[k]
    s.env["FAKE_HERDR"] = str(d)
    state = s.home / ".local" / "state" / "octo-feather"
    state.mkdir(parents=True)
    (state / "director.toml").write_text('pane = "w0:p1"\n')
    s.identity()
    s.gh.store("repo.json", {"nameWithOwner": "o/r"})
    none: list[object] = []
    issue: dict[str, object] = {"number": 905, "title": TITLE, "body": "b", "state": "OPEN"}
    issue |= {"url": "https://github.com/o/r/issues/905", "parent": None}
    issue |= {"blockedBy": {"nodes": none}, "subIssues": {"totalCount": 0, "nodes": none}}
    s.gh.store("issue/905.json", issue)
    origin, seed = s.root / "origin.git", s.root / "seed"
    s.run(["git", "init", "-q", "--bare", "-b", "main", str(origin)])
    s.run(["git", "clone", "-q", str(origin), str(seed)])
    s.git(seed, "commit", "-q", "--allow-empty", "-m", "first")
    s.git(seed, "push", "-q", "origin", "main")
    checkout = s.root / "src" / "target"
    s.run(["git", "clone", "-q", str(origin), str(checkout)])
    s.git(seed, "commit", "-q", "--allow-empty", "-m", "main moved")
    s.git(seed, "push", "-q", "origin", "main")
    return d, checkout, s.git(seed, "rev-parse", "HEAD")


def started(s: Scratch) -> None:
    d, checkout, main_ = world(s)
    brief = s.root / "brief.md"
    brief.write_text(BRIEF)
    cmd = [kit("octo-feather-lane"), "start", "905", "--goal", TITLE, "--outcome", OUTCOME]
    out = s.run([*cmd, "--brief-file", str(brief)], cwd=checkout, env=DIRECTOR).out
    m = re.fullmatch(r"key=gh905 pane=(\S+) issue=905", out)
    assert m, out
    pane = m.group(1)
    show(f"printed: {out}")

    agents = json.loads((d / "agents.json").read_text())
    sup = agents[pane]
    calls = (d / "log").read_text().splitlines()
    assert [c for c in calls if c.startswith("workspace create ")] == [
        c for c in calls if c.startswith("workspace create --label gh905 ")
    ], calls
    assert len([c for c in calls if c.startswith("workspace create ")]) == 1, calls
    assert (sup["name"], sup["label"]) == ("gh905", "supervisor"), sup
    assert sup["env"]["OCTO_FEATHER_ROLE"] == "supervisor", sup
    assert [p for p, g in agents.items() if g["workspace_id"] == sup["workspace_id"]] == [pane]
    show(
        f"workspace gh905 ({sup['workspace_id']}) holds supervisor gh905 at {pane}, tab supervisor"
    )

    wt = checkout.with_name("target-gh905")
    assert s.git(wt, "rev-parse", "--abbrev-ref", "HEAD") == "gh905"
    assert s.git(wt, "rev-parse", "HEAD") == main_, "the branch is not at origin's main"
    show(f"worktree {wt.name} on branch gh905 at origin's main {main_[:12]}")

    state = s.home / ".local" / "state" / "octo-feather"
    rec = tomllib.loads((state / "lanes" / "gh905.toml").read_text())
    at = rec.pop("started_at")
    assert re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", at), at
    want = {"supervisor": pane, "repository": "o/r", "issue": "gh905", "goal": TITLE}
    assert rec == want | {"waiting_on": ""}, rec
    show(f"lanes/gh905.toml: {rec | {'started_at': at}}")

    goal = (
        f"/goal {OUTCOME} for gh905, delivered through implement-spec; done when an owner gate"
        " is pending (review link or merge ask sent) or PR merged and lane torn down"
    )
    head = (
        "Lane facts (octo-feather-lane start):\nLane key: gh905\n"
        f"Parent issue: 905 {TITLE} (https://github.com/o/r/issues/905)\n"
        f"Director pane: w0:p1\nWorktree: {wt}\nBranch: gh905\nMain commit: {main_}\n\n"
    )
    got = (d / "prompts").read_text()
    assert got == f"{pane}\t{goal}\n{pane}\t{head}{BRIEF}\n", got
    show(f"{pane} received the goal, then the brief: {got!r}")

    log = [json.loads(x) for x in (state / "director.handoffs.jsonl").read_text().splitlines()]
    prods = [x for x in log if x["kind"] == "prod"]
    assert [x for x in log if x not in prods] == [x for x in log if x["kind"] == "spawn"], log
    assert [(x["name"], x["pane"]) for x in log if x["kind"] == "spawn"] == [("gh905", pane)]
    assert len(prods) == 1, prods
    assert prods[0]["issue"] == "gh905", prods
    assert set(prods[0]) == {"at", "kind", "issue", "note"}, prods
    assert pane in prods[0]["note"], prods
    show(f"director log: one prod line {prods[0]}")


if __name__ == "__main__":
    main(started)
