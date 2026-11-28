"""The scenarios of tests/gate/kit/test_lane_merge.py (its items), this file their command
(testkit.main): scripts/octo-feather-lane merge, the supervisor's merge (issue 1133;
issue-lifecycle #gates-main-moved, #acceptance-merge-starts-routine), offline, in the world
tests/gate/kit/lane_post_merge.py prepares (Lane: origin, the kit install clone of o/r detached at
B, the director's checkout, the target clone, on main at B; the merge commit M). The testkit's fake
gh holds PR #7 open at head H, merging as M, with a green push run on M, and parent issue 70 with
sub-issue 71; the scratch state dir (XDG_STATE_HOME) holds lane gh7's record (`pr = 7`, issue
gh70, a lane key as every real record holds, comms #lane-record; supervisor zt1:p1) and one other
open lane, gh8 (issue gh80, supervisor zt2:p1); the testkit's Herdr stand-in (FAKE_HERDR) has both
supervisors and the director (w9:p99) live, idle, under the kit's own herdr-say. Every command runs
with gh7's supervisor's environment (SUPERVISOR: its role, the director pane its parent, its own
Herdr pane and workspace), so herdr-say's up-chain guard (docs/adr/0015) is active as in that
supervisor's pane (#1249). Space ids `zt*`, which no real Herdr gives.

merge_starts_routine runs instead in the gh1255 remerge's real case (testkit.realcase REMERGE):
gh answers only from its recorded tape (testkit/recordings/lane-merge-remerge.json), its git world
the realcase repo's bundle, every expected value the tape's recorded answer (#1267, #1266).
"""

from __future__ import annotations

import json
import os
import sys
from typing import TYPE_CHECKING

from herdr_messaging import ASSETS, agent, lines
from lane_post_merge import Lane, run1
from testkit import Scratch, kit, main
from testkit.realcase import REALCASE, REMERGE, RealCase, recorded, recordings

if TYPE_CHECKING:
    from testkit import Ran

STEPS = (
    "merged",
    "main CI",
    "kit refresh",
    "checkout",
    "coverage map",
    "stale agents",
    "tell supervisors",
    "teardown",
)
DIRECTOR = "w9:p99"
# gh7's supervisor's environment in its own pane, as octo-feather-start and Herdr give it
SUPERVISOR = {
    "OCTO_FEATHER_ROLE": "supervisor",
    "OCTO_FEATHER_PARENT": DIRECTOR,
    "HERDR_PANE_ID": "zt1:p1",
    "HERDR_WORKSPACE_ID": "zt1",
}
CASE = REMERGE  # lane A of lane key A, parent issue P, PR N; lane B of key B
TAPE, N, A, B, P = CASE.tape, CASE.pr, CASE.lane, CASE.other, int(CASE.lane[2:])


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
        self.record("gh7", "zt1:p1", "gh70", 7)
        self.record("gh8", "zt2:p1", "gh80", None)
        self.herdr = s.root / "herdr"
        self.herdr.mkdir()
        world = {
            p: agent(p, n, "idle")
            for p, n in (("zt1:p1", "gh7"), ("zt2:p1", "gh8"), (DIRECTOR, "director"))
        }
        (self.herdr / "agents.json").write_text(json.dumps(world))
        # the caller's Herdr pane and role replaced: the merge runs as gh7's supervisor in its pane
        for k in [k for k in s.env if k.startswith(("HERDR_", "OCTO_FEATHER_"))]:
            if k != "OCTO_FEATHER_KIT_INSTALL":
                del s.env[k]
        s.env |= SUPERVISOR
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

    def record(self, name: str, pane: str, issue: str, pr: int | None) -> None:
        (self.lanes / f"{name}.toml").write_text(
            f'supervisor = "{pane}"\nrepository = "o/r"\nissue = "{issue}"\n'
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
    """issue-lifecycle#acceptance-merge-starts-routine on the gh1255 remerge's real case
    (RealCase, testkit.realcase REMERGE, the merge tape; the ticket's demo, its commands and
    output printed): supervisor A's `merge N <head> --repo REALCASE` asks gh exactly the recorded
    run's calls, in its order, each answered by its recording: the PR read, the merge ask
    check's reads (octo-feather-lane --help, merge, allowed), the merge pinned to the PR's
    recorded head, done on parent P, the tracker key of the record's lane key A (its sub-issue
    closed, then P, each read back), then the routine's. It prints the merge, the
    recorded parent's sub-issues then the parent done, steps 1-7 ok and step 8 pending, exit 0;
    leaves the kit install (another repo's, as the recorded repo views name) unfetched and the
    director's checkout on the PR's base at the recorded merge commit; tells lane B's supervisor
    main moved (not A's own) through the guard of A's environment, naming the recorded PR title,
    its line and its prod line in the director log naming the post-merge routine of lane A as
    sender. `post-merge --lane A` then prints the record: PR, head and merge commit, steps
    1-7 ok and step 8 pending, no gh call. The guard still holds for the supervisor's own send:
    its `herdr-say zt2:p1 ...` exits 77, nothing delivered."""
    w = RealCase(s, TAPE, case=CASE)
    calls = [str(x["request"]) for x in recordings(TAPE)]
    head = json.loads(recorded(TAPE, f"pr view {N} --json state,headRefOid -R {REALCASE}"))
    h, m = head["headRefOid"], w.merge
    view = f"issue view {P} --json number,title,body,state,url,parent,subIssues,blockedBy"
    parent = json.loads(recorded(TAPE, view))  # done's first read of parent P, before its closes
    p, kids = parent["number"], [x["number"] for x in parent["subIssues"]["nodes"]]
    title = json.loads(recorded(TAPE, f"pr view {N} --json title,url -R {REALCASE}"))["title"]
    pr_repo, kit_repo = (
        json.loads(recorded(TAPE, f"repo view {x} --json nameWithOwner"))["nameWithOwner"]
        for x in (REALCASE, "https://github.com/0xTomDaniel/octo-feather")
    )
    r = w.lane("merge", str(N), h[:12], "--repo", REALCASE)
    assert s.gh.log() == calls, f"gh calls, want the recorded run's: {s.gh.log()}"
    out = r.out.split("\n")
    done = [f"{k}: done" for k in [*kids, p]] + [f"{p}: parent and {len(kids)} tickets done"]
    assert out[: 1 + len(done)] == [f"merged: PR #{N} at head {h[:12]} (lane {A})", *done], r.out
    for n, name in enumerate(STEPS[:7], 1):
        assert any(x.startswith(f"step {n} {name}: ok: ") for x in out), f"step {n}: {r.out}"
    kept = f"step 3 kit refresh: ok: kit install unchanged: PR in {pr_repo}, install is {kit_repo}"
    assert kept in out, r.out
    assert not s.git(w.kit, "for-each-ref"), "kit install fetched"
    pending = f"step 8 teardown: pending: lane {A} not archived; its archive starts this step"
    assert pending in out, r.out
    assert out[-1].endswith("step 7 tell supervisors ok; step 8 teardown pending"), r.out
    where = s.git(w.checkout, "rev-parse", "HEAD"), s.git(w.checkout, "branch", "--show-current")
    assert where == (m, w.base), f"checkout at {where}"
    sender = f"(from the post-merge routine of lane {A})"
    rules = "rule files changed: none; re-read the changed ones before your next step."
    told = w.told()
    assert told == [f"zt2:p1\tmain moved to {m[:12]} (#{N} {title}); {rules} {sender}"], told
    note = f"post-merge {m} #{N}: main moved, told {B} to re-read none {sender}"
    assert [(x["issue"], x["note"]) for x in w.prods()] == [(B, note)], w.prods()
    own = s.run([str(ASSETS / "herdr-say"), "zt2:p1", "mine"], want=77)
    assert "supervisor may message only up its chain" in own.err, own.err
    assert w.told() == told, "the supervisor's own send delivered"
    shown = w.lane("post-merge", "--lane", A).out.split("\n")
    record = w.top / "post-merge" / f"{A}.json"
    want = f"post-merge record {A}: PR #{N}, head {h[:12]}, merge commit {m} ({record})"
    assert shown[0] == want, shown[0]
    ok = [f"{n} {name} ok" for n, name in enumerate(STEPS[:7], 1)]
    assert outcomes(shown[1:]) == [*ok, "8 teardown pending"], shown
    assert s.gh.log() == calls, f"the record's read asked gh: {s.gh.log()}"


def resume(s: Scratch) -> None:
    """`merge 7 H` with the director's checkout dirty and lane gh7's record holding issue `gh70-x`,
    a lane key the tracker skill does not round-trip (key-from-branch gives 70, whose lane-key is
    gh70): merged, its done step refuses naming both keys, closing nothing, and step 3 stops before
    the install moves, exit 1. Cleaned, `post-merge 7 H --lane gh7` resumes at step 3: steps 1 and 2
    print their recorded lines, not rerun (no PR read for step 1, no run list for step 2 in the
    fake gh's log), steps 3-7 run, step 8 pending, exit 3; the record shows 1-7 ok, 8 pending."""
    w = World(s)
    lane = w.lane
    t = lane.target
    (t / "a").write_text("mine\n")
    w.record("gh7", "zt1:p1", "gh70-x", 7)
    r = w.run(1, "merge", "7", w.h)
    assert w.merge in s.gh.log(), s.gh.log()
    assert not [x for x in s.gh.log() if x.startswith("issue close")], s.gh.log()
    done = next((x for x in r.err.split("\n") if "done gh70-x" in x), "")
    assert "lane key gh70-x maps to tracker key 70" in done, r.err
    assert "whose lane key is gh70, not gh70-x" in done, r.err
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
    ok = [f"{n} {name} ok" for n, name in enumerate(STEPS[:7], 1)]
    assert outcomes(w.shown()) == [*ok, "8 teardown pending"], w.shown()


def refused(s: Scratch) -> None:
    """Refused before any merge, exit 1, nothing merged (no `pr merge` call, PR #7 as it was)
    and nothing recorded (no post-merge dir): PR #7 at another head; PR #7 closed; no open lane
    record with `pr = 7`; two of them. Each refusal names its fix."""
    w = World(s)
    other = "abcdef0" + w.h[7:]
    cases = (
        ("head", lambda: w.pr(head=other), f"PR #7's head is {other[:12]}, not the approved head"),
        ("closed", lambda: w.pr("CLOSED"), "PR #7 is CLOSED, not open: nothing merged"),
        ("no lane", lambda: w.record("gh7", "zt1:p1", "gh70", None), "no open lane record in "),
        (
            "two",
            lambda: w.record("gh8", "zt2:p1", "gh80", 7),
            "lane records gh7.toml, gh8.toml in ",
        ),
    )
    for what, setup, want in cases:
        w.pr()
        w.record("gh7", "zt1:p1", "gh70", 7)
        w.record("gh8", "zt2:p1", "gh80", None)
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
