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
           `key=gh905 pane=<pane> issue=905`; Herdr names the supervisor's working directory
           that worktree. Each observation printed, for the qc demo.
  unicode_title  options before the ticket and in `--opt=value` form (argparse's grammar), a title
           with an emoji, a quote and a backslash: the record parses (tomllib) and its goal is the
           title exactly.
  refused  each exits 1 naming what it rejects and makes nothing (no worktree, branch, workspace,
           record or prompt): a missing --brief-file (argparse's usage error); `gh repo view`
           printing nameWithOwner null and an unknown field; issue-view printing a title that is no
           string (each edge validated before anything is made).

Seams (ticket #1157, recorded before any test): issue-lifecycle#acceptance-lane-start-exists and
#acceptance-lane-start-rerun, `octo-feather-lane start` run as a command, the same stand-ins.

  exists   each of a lane record lanes/gh905.toml, a worktree <checkout>-gh905 (on branch gh905),
           a branch gh905 alone, and a Herdr workspace labelled gh905, there before a start: it
           exits 1 naming that one, leaves it as it was and starts no supervisor (no workspace,
           tab or agent started, no prompt, no record, no worktree it did not find).
  rerun    the stand-in failing the goal's delivery once (its file prompt-down): the first run
           exits 1 naming step goal; the same start run again prints the first run's pane, and
           the lane has one worktree, one supervisor gh905 (one workspace create), one record,
           the goal then the brief once each, one spawn line and one prod line in the director
           log, and nothing kept of the start; a third run exits 1 naming the record.
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
    wt = checkout.with_name("target-gh905")
    got_agent = json.loads(s.run(["herdr", "agent", "get", "gh905"]).out)["result"]["agent"]
    assert (got_agent["pane_id"], got_agent["cwd"]) == (pane, str(wt)), got_agent
    show(f"herdr agent get gh905: pane {pane}, cwd {got_agent['cwd']}")
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


def unicode_title(s: Scratch) -> None:
    _, checkout, _ = world(s)
    brief = s.root / "brief.md"
    brief.write_text(BRIEF)
    title = 'Ship \U0001f680 "quoted" back\\slash'
    cmd = [kit("octo-feather-lane"), "start", f"--goal={title}", f"--brief-file={brief}"]
    s.run([*cmd, "--outcome", OUTCOME, "905"], cwd=checkout, env=DIRECTOR)
    state = s.home / ".local" / "state" / "octo-feather"
    rec = tomllib.loads((state / "lanes" / "gh905.toml").read_text(encoding="utf-8"))
    assert rec["goal"] == title, rec
    show(f"lanes/gh905.toml goal reads back {rec['goal']!r}")


def nothing_made(s: Scratch, d: Path, checkout: Path) -> None:
    """No worktree, branch, workspace, record or prompt for gh905."""
    assert not checkout.with_name("target-gh905").exists()
    assert s.git(checkout, "branch", "--list", "gh905") == ""
    calls = (d / "log").read_text().splitlines() if (d / "log").exists() else []
    assert not [c for c in calls if c.startswith(("workspace create", "tab create"))], calls
    assert not (d / "prompts").exists()
    assert not (s.home / ".local" / "state" / "octo-feather" / "lanes" / "gh905.toml").exists()


def refused(s: Scratch) -> None:
    d, checkout, _ = world(s)
    brief = s.root / "brief.md"
    brief.write_text(BRIEF)
    cmd = [kit("octo-feather-lane"), "start", "905", "--goal", TITLE, "--outcome", OUTCOME]
    err = s.run(cmd, cwd=checkout, env=DIRECTOR, want=1).err
    assert "the following arguments are required: --brief-file" in err, err
    nothing_made(s, d, checkout)
    show(f"no --brief-file: exit 1, {err}")

    cmd += ["--brief-file", str(brief)]
    s.gh.store("repo.json", {"nameWithOwner": None, "unexpected": True})
    err = s.run(cmd, cwd=checkout, env=DIRECTOR, want=1).err
    assert "gh repo view printed" in err, err
    assert "want exactly nameWithOwner" in err, err
    nothing_made(s, d, checkout)
    show(f"gh repo view malformed: exit 1, {err}")

    s.gh.store("repo.json", {"nameWithOwner": "o/r"})
    issue = json.loads((s.gh.dir / "issue" / "905.json").read_text()) | {"title": 7}
    s.gh.store("issue/905.json", issue)
    err = s.run(cmd, cwd=checkout, env=DIRECTOR, want=1).err
    assert "issue-view 905 printed title is no string" in err, err
    nothing_made(s, d, checkout)
    show(f"issue-view malformed: exit 1, {err}")


def no_supervisor(d: Path) -> None:
    """No workspace, tab or agent started, no prompt sent."""
    calls = (d / "log").read_text().splitlines() if (d / "log").exists() else []
    made = ("workspace create", "tab create", "agent start")
    assert not [c for c in calls if c.startswith(made)], calls
    assert not (d / "prompts").exists()


def exists(s: Scratch) -> None:
    d, checkout, main_ = world(s)
    brief = s.root / "brief.md"
    brief.write_text(BRIEF)
    cmd = [kit("octo-feather-lane"), "start", "905", "--goal", TITLE, "--outcome", OUTCOME]
    cmd += ["--brief-file", str(brief)]
    lanes = s.home / ".local" / "state" / "octo-feather" / "lanes"
    wt = checkout.with_name("target-gh905")

    lanes.mkdir()
    record = lanes / "gh905.toml"
    record.write_text('supervisor = "w7:p7"\nissue = "gh905"\n')
    err = s.run(cmd, cwd=checkout, env=DIRECTOR, want=1).err
    assert f"lane gh905 exists: lane record {record};" in err, err
    assert record.read_text() == 'supervisor = "w7:p7"\nissue = "gh905"\n'
    assert not wt.exists()
    assert s.git(checkout, "branch", "--list", "gh905") == ""
    no_supervisor(d)
    show(f"record there: exit 1, {err}")
    record.unlink()

    s.git(checkout, "worktree", "add", "-q", "-b", "gh905", str(wt))
    head = s.git(wt, "rev-parse", "HEAD")
    err = s.run(cmd, cwd=checkout, env=DIRECTOR, want=1).err
    assert f"lane gh905 exists: worktree {wt}, branch gh905;" in err, err
    assert s.git(wt, "rev-parse", "--abbrev-ref", "HEAD") == "gh905"
    assert s.git(wt, "rev-parse", "HEAD") == head != main_
    assert not record.exists()
    no_supervisor(d)
    show(f"worktree there: exit 1, {err}")
    s.git(checkout, "worktree", "remove", str(wt))

    err = s.run(cmd, cwd=checkout, env=DIRECTOR, want=1).err
    assert "lane gh905 exists: branch gh905;" in err, err
    assert s.git(checkout, "rev-parse", "gh905") == head
    assert not wt.exists()
    no_supervisor(d)
    show(f"branch there: exit 1, {err}")
    s.git(checkout, "branch", "-q", "-D", "gh905")

    agents = json.loads((d / "agents.json").read_text())
    other = {"name": "gh905", "pane_id": "w5:p9", "workspace_id": "w5", "tab_id": "w5:t9"}
    agents["w5:p9"] = other | {"agent_status": "working"}
    (d / "agents.json").write_text(json.dumps(agents))
    (d / "workspaces.json").write_text(json.dumps({"w5": "gh905"}))
    err = s.run(cmd, cwd=checkout, env=DIRECTOR, want=1).err
    assert "lane gh905 exists: Herdr workspace gh905 (w5);" in err, err
    assert json.loads((d / "agents.json").read_text()) == agents
    assert not wt.exists()
    assert s.git(checkout, "branch", "--list", "gh905") == ""
    assert not record.exists()
    no_supervisor(d)
    show(f"workspace there: exit 1, {err}")


def rerun(s: Scratch) -> None:
    d, checkout, main_ = world(s)
    brief = s.root / "brief.md"
    brief.write_text(BRIEF)
    cmd = [kit("octo-feather-lane"), "start", "905", "--goal", TITLE, "--outcome", OUTCOME]
    cmd += ["--brief-file", str(brief)]
    state = s.home / ".local" / "state" / "octo-feather"
    wt = checkout.with_name("target-gh905")

    (d / "prompt-down").write_text("")
    err = s.run(cmd, cwd=checkout, env=DIRECTOR, want=1).err
    assert "step goal (made so far: " in err, err
    assert "herdr: server not reachable" in err, err
    assert not (d / "prompts").exists()
    show(f"first run: exit 1, {err}")

    out = s.run(cmd, cwd=checkout, env=DIRECTOR).out
    m = re.fullmatch(r"key=gh905 pane=(\S+) issue=905", out)
    assert m, out
    pane = m.group(1)
    show(f"second run: {out}")

    trees = s.git(checkout, "worktree", "list", "--porcelain").splitlines()
    assert [x for x in trees if x.startswith("worktree ")] == [
        f"worktree {checkout}",
        f"worktree {wt}",
    ], trees
    assert s.git(wt, "rev-parse", "HEAD") == main_
    agents = json.loads((d / "agents.json").read_text())
    assert [p for p, g in agents.items() if g["name"] == "gh905"] == [pane], agents
    calls = (d / "log").read_text().splitlines()
    assert len([c for c in calls if c.startswith("workspace create ")]) == 1, calls
    assert len([c for c in calls if c.startswith("agent start ")]) == 1, calls
    lanes = state / "lanes"
    assert sorted(p.name for p in lanes.iterdir()) == ["gh905.toml"], list(lanes.iterdir())
    rec = tomllib.loads((lanes / "gh905.toml").read_text())
    assert (rec["supervisor"], rec["goal"]) == (pane, TITLE), rec
    show(f"one worktree {wt.name}, one supervisor gh905 at {pane}, one record {rec}")

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
    show(f"{pane} received the goal, then the brief, once each")
    log = [json.loads(x) for x in (state / "director.handoffs.jsonl").read_text().splitlines()]
    assert [(x["kind"], x.get("name") or x.get("issue")) for x in log] == [
        ("spawn", "gh905"),
        ("prod", "gh905"),
    ], log
    show("director log: one spawn line, one prod line")

    err = s.run(cmd, cwd=checkout, env=DIRECTOR, want=1).err
    assert f"lane gh905 exists: lane record {lanes / 'gh905.toml'}, " in err, err
    assert (d / "prompts").read_text() == got
    show(f"third run: exit 1, {err}")


if __name__ == "__main__":
    main(started, unicode_title, refused, exists, rerun)
