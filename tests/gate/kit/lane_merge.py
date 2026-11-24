"""The scenarios of tests/gate/kit/test_lane_merge.py (its items), this file their command
(testkit.main): scripts/octo-feather-lane merge, the supervisor's merge (issue 1133;
issue-lifecycle #gates-main-moved, #acceptance-merge-starts-routine), offline, in the world
tests/gate/kit/lane_post_merge.py prepares (Lane: origin, the kit install clone of o/r detached at
B, the director's checkout, the target clone, on main at B; the merge commit M). The testkit's fake
gh holds PR #7 open at head H, merging as M, with a green push run on M, and parent issue 70 with
sub-issue 71; the scratch state dir (XDG_STATE_HOME) holds lane gh7's record (`pr = 7`, issue 70,
supervisor zt1:p1) and one other open lane, gh8 (supervisor zt2:p1); the testkit's Herdr stand-in
(FAKE_HERDR) has both supervisors live, idle, under the kit's own herdr-say. Space ids `zt*`, which
no real Herdr gives.
"""

from __future__ import annotations

import json
import os
import sys
from typing import TYPE_CHECKING

from herdr_messaging import ASSETS, agent, lines
from lane_post_merge import Lane, run1
from testkit import Scratch, kit, main

if TYPE_CHECKING:
    from testkit import Ran

STEPS = (
    "merged",
    "main CI",
    "kit refresh",
    "checkout",
    "stale agents",
    "tell supervisors",
    "teardown",
)


class World:
    """Lane's world in S with PR #7 open, issues 70 and 71, lanes gh7 and gh8, Herdr's two
    supervisors; `merge` and `post_merge` run the command from the target clone."""

    def __init__(self, s: Scratch) -> None:
        self.lane = lane = Lane(s)
        self.s = s
        lane.install(lane.b)  # the install of o/r, the PR's repo: step 3 moves it
        lane.checkout(lane.b)
        lane.store([run1("check", "completed", "success", 11, lane.m)])
        # PR #7's head H, a lane commit on B in the target (branch gh7): the merge's guard reads
        # the ask's spec calls from the lane diff, so the head is a commit here (#1266)
        t = lane.target
        tree = s.git(t, "rev-parse", f"{lane.b}^{{tree}}")
        ident = ["-c", "user.name=t", "-c", "user.email=t@t"]
        self.h = s.git(t, *ident, "commit-tree", tree, "-p", lane.b, "-m", "gh7")
        s.git(t, "update-ref", "refs/heads/gh7", self.h)
        self.merge = f"pr merge 7 --merge --match-head-commit {self.h}"
        self.pr()
        for n, kids in ((70, [71]), (71, [])):
            s.gh.store(
                f"issue/{n}.json",
                {
                    "number": n,
                    "title": f"t{n}",
                    "body": "",
                    "state": "OPEN",
                    "url": f"https://github.com/o/r/issues/{n}",
                    "parent": None,
                    "subIssues": {"totalCount": len(kids), "nodes": [{"number": k} for k in kids]},
                    "blockedBy": {"nodes": []},
                },
            )
        self.st = lane.state / "octo-feather"
        self.lanes = self.st / "lanes"
        self.lanes.mkdir(parents=True)
        self.record("gh7", "zt1:p1", 70, 7)
        self.record("gh8", "zt2:p1", 80, None)
        self.herdr = s.root / "herdr"
        self.herdr.mkdir()
        world = {p: agent(p, n, "idle") for p, n in (("zt1:p1", "gh7"), ("zt2:p1", "gh8"))}
        (self.herdr / "agents.json").write_text(json.dumps(world))
        # the caller's Herdr pane and role cleared: the merge runs as a supervisor shell would
        for k in [k for k in s.env if k.startswith(("HERDR_", "OCTO_FEATHER_"))]:
            if k != "OCTO_FEATHER_KIT_INSTALL":
                del s.env[k]
        s.env["FAKE_HERDR"] = str(self.herdr)
        self.path = lane.path["rec"] + str(ASSETS) + os.pathsep + s.env["PATH"]

    def pr(self, state: str = "OPEN", head: str = "") -> None:
        """PR #7 STATE at HEAD (H by default), merging as M; the gh call log emptied."""
        head = head or self.h
        self.s.gh.put(
            7,
            {
                "number": 7,
                "state": state,
                "headRefOid": head,
                "mergeCommit": None,
                "merges_as": self.lane.m,
                "baseRefName": "main",
                "headRefName": "gh7",
                "title": "Add foo",
                "url": "https://github.com/o/r/pull/7",
                # a merge ask building no criterion, tier 1: the merge's guard lets it go (#1266)
                "body": f"## Merge ask\n\nHead: {head[:12]}\nBuilt: none\nFailed: none\n",
            },
        )
        (self.s.gh.dir / "log").write_text("")

    def record(self, name: str, pane: str, issue: int, pr: int | None) -> None:
        (self.lanes / f"{name}.toml").write_text(
            f'supervisor = "{pane}"\nrepository = "o/r"\nissue = {issue}\n'
            + (f"pr = {pr}\n" if pr else "")
            + 'goal = "g"\nstarted_at = "2026-11-19T00:00:00Z"\n'
        )

    def run(self, want: int, *args: str) -> Ran:
        r = self.s.run(
            [kit("octo-feather-lane"), *args],
            want=want,
            cwd=self.lane.target,
            env={"PATH": self.path},
        )
        said = f"$ octo-feather-lane {' '.join(args)}  # exit {r.rc}\n{r.out}\n{r.err}"
        sys.stdout.write(said.rstrip() + "\n")  # each command and its output: the demo's
        return r

    def told(self) -> list[str]:
        """Each prompt Herdr delivered, `<pane>\\t<text>`."""
        return lines(self.herdr / "prompts")

    def shown(self) -> list[str]:
        """`post-merge --lane gh7`'s lines after its header."""
        return self.run(0, "post-merge", "--lane", "gh7").out.split("\n")[1:]


def outcomes(shown: list[str]) -> list[str]:
    """Each step's `<n> <name> <outcome>` from the record's lines."""
    out: list[str] = []
    for ln, (n, name) in zip(shown, enumerate(STEPS, 1), strict=True):
        head = f"step {n} {name}: "
        assert ln.startswith(head), f"record line {n}: {ln}"
        out.append(f"{n} {name} {ln.removeprefix(head).split(' ', 1)[0].rstrip(':')}")
    return out


def merge_starts_routine(s: Scratch) -> None:
    """issue-lifecycle#acceptance-merge-starts-routine: `merge 7 H --repo o/r` (the ticket's
    demo, its commands and output printed) merges pinned to H (the fake
    gh logs the pinned merge, after the PR read), runs done on parent 70 (71 then 70 closed),
    leaves the kit install and the director's checkout at the merge commit, tells lane gh8's
    supervisor main moved (not gh7's own), and prints steps 1-6 ok and step 7 pending; exit 0.
    The only gh writes: the merge and the two closes. `post-merge --lane gh7` then prints the
    record: PR, head and merge commit, steps 1-6 ok and step 7 pending."""
    w = World(s)
    lane = w.lane
    m, m12 = lane.m, lane.m[:12]
    r = w.run(0, "merge", "7", w.h, "--repo", "o/r")
    log, merge = s.gh.log(), f"{w.merge} -R o/r"
    assert merge in log, f"no pinned merge: {log}"
    assert log.index("pr view 7 --json state,headRefOid -R o/r") < log.index(merge), log
    writes = [x for x in log if x.startswith(("pr merge", "issue close", "pr edit", "api -X"))]
    assert writes == [merge, "issue close 71", "issue close 70"], f"gh writes: {log}"
    out = r.out.split("\n")
    assert out[0] == f"merged: PR #7 at head {w.h[:12]} (lane gh7)", r.out
    assert out[1:4] == ["71: done", "70: done", "70: parent and 1 tickets done"], r.out
    for n, name in enumerate(STEPS[:6], 1):
        assert any(x.startswith(f"step {n} {name}: ok: ") for x in out), f"step {n}: {r.out}"
    pending = "step 7 teardown: pending: lane gh7 not archived; its archive starts this step"
    assert pending in out, r.out
    assert out[-1].endswith("step 6 tell supervisors ok; step 7 teardown pending"), r.out
    assert lane.head() == m, f"kit install at {lane.head()}, not the merge commit"
    assert lane.where() == (m, "main"), f"checkout at {lane.where()}"
    told = w.told()
    assert [x.split("\t")[0] for x in told] == ["zt2:p1"], f"told: {told}"
    assert told[0].startswith(f"zt2:p1\tmain moved to {m12} (#7 Add foo); "), told
    shown = w.shown()
    head = w.run(0, "post-merge", "--lane", "gh7").out.split("\n")[0]
    record = w.st / "post-merge" / "gh7.json"
    want = f"post-merge record gh7: PR #7, head {w.h}, merge commit {m} ({record})"
    assert head == want, head
    ok = [f"{n} {name} ok" for n, name in enumerate(STEPS[:6], 1)]
    assert outcomes(shown) == [*ok, "7 teardown pending"], shown


def resume(s: Scratch) -> None:
    """`merge 7 H` with the director's checkout dirty: merged and done, step 3 stops before the
    install moves, exit 1. Cleaned, `post-merge 7 H --lane gh7` resumes at step 3: steps 1 and 2
    print their recorded lines, not rerun (no PR read for step 1, no run list for step 2 in the
    fake gh's log), steps 3-6 run, step 7 pending, exit 3; the record shows 1-6 ok, 7 pending."""
    w = World(s)
    lane = w.lane
    t = lane.target
    (t / "a").write_text("mine\n")
    r = w.run(1, "merge", "7", w.h)
    assert w.merge in s.gh.log(), s.gh.log()
    stop = f"step 3 kit refresh: stopped: checkout {t} is dirty (M a): commit"
    assert any(x.startswith(stop) for x in r.out.split("\n")), r.out
    assert lane.head() == lane.b, "install moved past a stop"
    assert outcomes(w.shown())[2:4] == ["3 kit refresh stopped", "4 checkout not"], w.shown()
    (t / "a").write_text("")
    (s.gh.dir / "log").write_text("")
    r = w.run(3, "post-merge", "7", w.h, "--lane", "gh7")
    out = r.out.split("\n")
    for n, name in ((1, "merged"), (2, "main CI")):
        line = next((x for x in out if x.startswith(f"step {n} {name}: ok: ")), "")
        assert line.endswith(", not rerun)"), f"step {n}: {r.out}"
        assert " (recorded 20" in line, f"step {n}: {r.out}"
    log = s.gh.log()
    assert not [x for x in log if x.startswith(("pr view 7 --json state,", "run "))], log
    assert any(x.startswith("step 3 kit refresh: ok: kit install ") for x in out), r.out
    assert lane.head() == lane.m, "install not moved on the resume"
    ok = [f"{n} {name} ok" for n, name in enumerate(STEPS[:6], 1)]
    assert outcomes(w.shown()) == [*ok, "7 teardown pending"], w.shown()


def refused(s: Scratch) -> None:
    """Refused before any merge, exit 1, nothing merged (no `pr merge` call, PR #7 as it was)
    and nothing recorded (no post-merge dir): PR #7 at another head; PR #7 closed; no open lane
    record with `pr = 7`; two of them. Each refusal names its fix."""
    w = World(s)
    other = "abcdef0" + w.h[7:]
    cases = (
        ("head", lambda: w.pr(head=other), f"PR #7's head is {other[:12]}, not the approved head"),
        ("closed", lambda: w.pr("CLOSED"), "PR #7 is CLOSED, not open: nothing merged"),
        ("no lane", lambda: w.record("gh7", "zt1:p1", 70, None), "no open lane record in "),
        ("two", lambda: w.record("gh8", "zt2:p1", 80, 7), "lane records gh7.toml, gh8.toml in "),
    )
    for what, setup, want in cases:
        w.pr()
        w.record("gh7", "zt1:p1", 70, 7)
        w.record("gh8", "zt2:p1", 80, None)
        setup()
        before = s.gh.pr(7)
        r = w.run(1, "merge", "7", w.h)
        assert want in r.err, f"{what}: {r.err}"
        assert not [x for x in s.gh.log() if x.startswith("pr merge")], f"{what}: {s.gh.log()}"
        assert s.gh.pr(7) == before, f"{what}: PR #7 changed"
        assert not (w.st / "post-merge").exists(), f"{what}: recorded"
        assert w.lane.head() == w.lane.b, f"{what}: install moved"


if __name__ == "__main__":
    main(merge_starts_routine, resume, refused)
