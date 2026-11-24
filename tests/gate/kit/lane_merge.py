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

H = "1234567890abcdef1234567890abcdef12345678"  # PR #7's head, the approved one
STEPS = (
    "merged",
    "main CI",
    "kit refresh",
    "checkout",
    "stale agents",
    "tell supervisors",
    "teardown",
)
MERGE = f"pr merge 7 --merge --match-head-commit {H}"
DIRECTOR = "w9:p99"
# gh7's supervisor's environment in its own pane, as octo-feather-start and Herdr give it
SUPERVISOR = {
    "OCTO_FEATHER_ROLE": "supervisor",
    "OCTO_FEATHER_PARENT": DIRECTOR,
    "HERDR_PANE_ID": "zt1:p1",
    "HERDR_WORKSPACE_ID": "zt1",
}


class World:
    """Lane's world in S with PR #7 open, issues 70 and 71, lanes gh7 and gh8, Herdr's two
    supervisors; `merge` and `post_merge` run the command from the target clone."""

    def __init__(self, s: Scratch) -> None:
        self.lane = lane = Lane(s)
        self.s = s
        lane.install(lane.b)  # the install of o/r, the PR's repo: step 3 moves it
        lane.checkout(lane.b)
        lane.store([run1("check", "completed", "success", 11, lane.m)])
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

    def pr(self, state: str = "OPEN", head: str = H) -> None:
        """PR #7 STATE at HEAD, merging as M; the gh call log emptied."""
        self.s.gh.put(
            7,
            {
                "state": state,
                "headRefOid": head,
                "mergeCommit": None,
                "merges_as": self.lane.m,
                "baseRefName": "main",
                "headRefName": "gh7",
                "title": "Add foo",
                "url": "https://github.com/o/r/pull/7",
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
    """issue-lifecycle#acceptance-merge-starts-routine: `merge 7 H --repo o/r` (the ticket's
    demo, its commands and output printed) merges pinned to H (the fake
    gh logs the pinned merge, after the PR read), runs done on parent 70, the tracker key of the
    record's lane key gh70 (71 then 70 closed), leaves the kit install and the director's checkout
    at the merge commit, tells lane gh8's supervisor main moved (not gh7's own) through the
    guard of the supervisor's environment, that line and its prod line in the director log naming
    the post-merge routine of lane gh7 as sender, and prints steps 1-6 ok and step 7 pending;
    exit 0. The only gh writes: the merge and the two closes. `post-merge --lane gh7` then prints
    the record: PR, head and merge commit, steps 1-6 ok and step 7 pending. The guard still holds
    for the supervisor's own send: its `herdr-say zt2:p1 ...` exits 77, nothing delivered."""
    w = World(s)
    lane = w.lane
    m, m12 = lane.m, lane.m[:12]
    r = w.run(0, "merge", "7", H, "--repo", "o/r")
    log, merge = s.gh.log(), f"{MERGE} -R o/r"
    assert merge in log, f"no pinned merge: {log}"
    assert log.index("pr view 7 --json state,headRefOid -R o/r") < log.index(merge), log
    writes = [x for x in log if x.startswith(("pr merge", "issue close", "pr edit", "api -X"))]
    assert writes == [merge, "issue close 71", "issue close 70"], f"gh writes: {log}"
    out = r.out.split("\n")
    assert out[0] == "merged: PR #7 at head 1234567890ab (lane gh7)", r.out
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
    sender = "from the post-merge routine of lane gh7"
    assert sender in told[0], told
    prods = [
        json.loads(x)["note"]
        for x in lines(w.st / "director.handoffs.jsonl")
        if json.loads(x)["kind"] == "prod"
    ]
    assert len(prods) == 1, prods
    assert prods[0].startswith(f"post-merge {m} #7: main moved, told gh8 to re-read "), prods
    assert sender in prods[0], prods
    own = s.run([str(ASSETS / "herdr-say"), "zt2:p1", "mine"], want=77, env={"PATH": w.path})
    assert "supervisor may message only up its chain" in own.err, own.err
    assert w.told() == told, "the supervisor's own send delivered"
    shown = w.shown()
    head = w.run(0, "post-merge", "--lane", "gh7").out.split("\n")[0]
    record = w.st / "post-merge" / "gh7.json"
    want = f"post-merge record gh7: PR #7, head {H}, merge commit {m} ({record})"
    assert head == want, head
    ok = [f"{n} {name} ok" for n, name in enumerate(STEPS[:6], 1)]
    assert outcomes(shown) == [*ok, "7 teardown pending"], shown


def resume(s: Scratch) -> None:
    """`merge 7 H` with the director's checkout dirty and lane gh7's record holding issue `gh70-x`,
    a lane key the tracker skill does not round-trip (key-from-branch gives 70, whose lane-key is
    gh70): merged, its done step refuses naming both keys, closing nothing, and step 3 stops before
    the install moves, exit 1. Cleaned, `post-merge 7 H --lane gh7` resumes at step 3: steps 1 and 2
    print their recorded lines, not rerun (no PR read for step 1, no run list for step 2 in the
    fake gh's log), steps 3-6 run, step 7 pending, exit 3; the record shows 1-6 ok, 7 pending."""
    w = World(s)
    lane = w.lane
    t = lane.target
    (t / "a").write_text("mine\n")
    w.record("gh7", "zt1:p1", "gh70-x", 7)
    r = w.run(1, "merge", "7", H)
    assert MERGE in s.gh.log(), s.gh.log()
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
    r = w.run(3, "post-merge", "7", H, "--lane", "gh7")
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
    other = "abcdef0" + H[7:]
    cases = (
        ("head", lambda: w.pr(head=other), "PR #7's head is abcdef0890ab, not the approved head"),
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
        r = w.run(1, "merge", "7", H)
        assert want in r.err, f"{what}: {r.err}"
        assert not [x for x in s.gh.log() if x.startswith("pr merge")], f"{what}: {s.gh.log()}"
        assert s.gh.pr(7) == before, f"{what}: PR #7 changed"
        assert not (w.st / "post-merge").exists(), f"{what}: recorded"
        assert w.lane.head() == w.lane.b, f"{what}: install moved"


if __name__ == "__main__":
    main(merge_starts_routine, resume, refused)
