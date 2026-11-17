"""The scenarios of tests/gate/kit/test_lane_correction.py (its items), this file their command
(testkit.main): the correction lanes the reflection files (spec comms #reflection-correction,
#acceptance-reflect-files-correction; issue-lifecycle #lanes-correction,
#acceptance-reflection-missed-lane, #acceptance-writer-route-lane), each case proved against the
rule as issue-lifecycle #lanes-correction owns it (what counts, when a class is due, refiling,
reflection-missed, owner-caught) and comms #reflection-correction (where it files, what it quotes).

Seams (ticket #937, agreed before any test): (1) the CLI, `octo-feather-lane archive NAME` and
`octo-feather-lane reflect --director` run as commands over a scratch state dir, the real
scripts/pi-role starting agents/reflector.md and the real github-issues scripts; (2) the Pi model
boundary: the testkit's Pi in print mode (testkit/pi_agent.py, testkit.reflector's world, its
Herdr the testkit's); (3) the GitHub boundary: the testkit's gh answering only real gh's recorded
answers (testkit/recordings/lane-correction.json, one tape per scenario; a request with no
recording fails). Nothing else stands in. A filed issue is read off the gh request that filed
it: its repo (GH_REPO, as issue-create names the lane's target), title and body (testkit/gh.py).

Deviations from tests/lane-correction.sh, each forced by real GitHub (the facts kept): the lanes'
target o/t is 0xTomDaniel/spec-chat, the kit's tracker 0xTomDaniel/octo-feather; the keys filed
are the real ones (FILED); an issue is closed once, at its real closedAt (gh5's finding dated
after it, gh4's before it, where the old test closed it twice at chosen dates); every scenario
files in one real tracker, so the other-lane scenario's class is dup-rule-other, not the
lifecycle's dup-rule; and a reflection-missed finding stands in its log from the start, dated, not
written by this run's reflector: the subject a reflection-missed lane files under holds its
finding's `at` (scripts/octo-feather-reflect corrections), which a reflector's run sets to its own
clock, so no recorded request could match it (a reflector's findings reaching the log: the lane
and director reflection tests). Rerecording needs fresh class names: each scenario's issues are
closed after their findings, so none would be due again."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import NamedTuple

from testkit import Scratch, kit, main, reflector, reply

L = kit("octo-feather-lane")
TARGET, KIT = "0xTomDaniel/spec-chat", "0xTomDaniel/octo-feather"
# gh 2.102.0, 2026-11-17 (each recording's source): one run of each scenario against TARGET and
# KIT, every issue it filed closed after it; the lifecycle's spec-chat#6 closed by hand between
# gh3's and gh4's archives, at 2026-11-17T18:45:02Z.
TAPE = Path(__file__).parent / "testkit" / "recordings" / "lane-correction.json"
# The keys each scenario's run filed, in order.
FILED = {
    "lifecycle": ["6", "7", "8", "964"],
    "other_lane": ["9"],
    "routed": ["10"],
    "counts": ["11"],
}
GH5_AT = "2026-11-20T00:00:00Z"  # after spec-chat#6 closed
CREATE = re.compile(r"GH_REPO=(\S+) issue create --title (.*) --body-file (\".*\")")


def finding(at: str, cls: str, summary: str, **more: object) -> str:
    """A finding line (spec comms #reflection-output); MORE: source, blocking, question, route."""
    return json.dumps({"at": at, "kind": "finding", "class": cls, **more, "summary": summary})


def cr(
    at: str, cls: str, summary: str, source: str = "code-review", *, blocking: bool = True
) -> str:
    """A review (or SOURCE's) finding."""
    return finding(at, cls, summary, source=source, blocking=blocking)


def rf(at: str, cls: str, summary: str, **more: object) -> str:
    """A reflection's finding, MORE its question and route (a lane's: blocking false)."""
    return finding(at, cls, summary, source="reflection", **more)


class Issue(NamedTuple):
    repo: str
    title: str
    body: str


class World:
    """S's reflection world (testkit.reflector), each reflector replying no gap; the testkit's
    gh replaying SCENARIO's tape."""

    def __init__(self, s: Scratch, scenario: str) -> None:
        self.s, self.top = s, reflector(s)
        self.lanes = self.top / "lanes"
        (self.lanes / "archive").mkdir(parents=True)
        self.dlog = self.top / "director.handoffs.jsonl"
        self.dlog.write_text("")
        s.gh.store("tape.json", json.loads(TAPE.read_text())[scenario])

    def lane(self, name: str, *findings: str, archived: bool = False) -> None:
        """Lane NAME on TARGET, its log FINDINGS; ARCHIVED: in archive/."""
        d = self.lanes / ("archive" if archived else "")
        (d / f"{name}.toml").write_text(
            f'issue = "{name}"\nrepository = "{TARGET}"\nsupervisor = "w9:p2"\ngoal = "scratch"\n'
        )
        (d / f"{name}.handoffs.jsonl").write_text("".join(f"{x}\n" for x in findings))

    def director(self, *findings: str) -> None:
        """FINDINGS appended to the director log."""
        with self.dlog.open("a") as f:
            f.write("".join(f"{x}\n" for x in findings))

    def run(self, *args: str) -> list[str]:
        """`octo-feather-lane ARGS`' stdout lines."""
        return self.s.run([L, *args]).out.splitlines()

    def filed(self) -> list[Issue]:
        """Every issue filed so far, read off its gh request."""
        got = [CREATE.fullmatch(x) for x in self.s.gh.log()]
        return [Issue(m[1], m[2], json.loads(m[3])) for m in got if m]

    def none_filed(self, out: list[str], n: int, what: str) -> None:
        """OUT says none filed, and N issues filed in all."""
        assert NONE in out, f"{what}: {out}"
        assert len(self.filed()) == n, f"{what}: {self.filed()}"


NONE = "correction lanes: none filed"


def filed(key: str, repo: str, cls: str, rest: str = "") -> str:
    """The line (its start, without REST) printing KEY filed."""
    return f"correction lane: filed {key} in github-issues {repo} for {cls} {rest}"


def two(route: str) -> str:
    return f"(2 findings; route: {route})"


def issue(i: Issue, repo: str, marker: str, *quotes: str) -> None:
    """I filed in REPO, its title holding MARKER, its body QUOTES."""
    assert i.repo == repo, i
    assert f"[correction-lane {marker}" in i.title, i
    for q in quotes:
        assert q in i.body, (q, i.body)


def lifecycle(s: Scratch) -> None:
    """#acceptance-reflect-files-correction, #acceptance-writer-route-lane: archived gh1 logged one
    dup-rule finding, gh2's review the second, the director reflection routes the class: archive
    gh2 files it in gh2's target, quoting both and the route, the key printed. Its issue open: a
    third finding files nothing; closed after the class's latest finding: nothing; closed before a
    newer one: files again. #acceptance-reflection-missed-lane: one lane reflection-missed finding
    files at once in the lane's target, a director one in the kit's repo, each naming the question
    list; owner-caught classes twice in the director log file nothing. Each reflection-missed
    finding files once: the director reflection alone, no new finding, files nothing."""
    w, keys = World(s, "lifecycle"), FILED["lifecycle"]
    (w.lanes / "archive" / "gh1.handoffs.jsonl").write_text(
        cr("2026-10-20T00:00:00Z", "dup-rule", "gh1 restated the merge rule") + "\n"
    )
    w.lane("gh2", cr("2026-10-21T00:00:00Z", "dup-rule", "gh2 restated the gate rule"))
    route = "agents/implementer.md Rules"
    why = "summary: 2 code-review findings in gh1, gh2"
    reply(s, "director", f"class: dup-rule | question: writer-route | route: {route} | {why}")
    out = w.run("archive", "gh2")
    assert filed(keys[0], TARGET, "dup-rule", two(route)) in out, f"archive gh2: {out}"
    assert (w.lanes / "archive" / "gh2.toml").is_file(), f"gh2 not archived: {out}"
    (i,) = w.filed()
    gh12 = ("gh1 restated the merge rule", "gh2 restated the gate rule")
    issue(i, TARGET, "dup-rule]", "Class: dup-rule", f"Route: {route}", *gh12)
    assert "question list" not in i.body, i.body

    reply(s, "director")
    w.lane("gh3", cr("2026-10-22T00:00:00Z", "dup-rule", "gh3 again"))
    w.none_filed(w.run("archive", "gh3"), 1, "open issue: filed again")
    # Recorded: the issue closed here, after gh4's finding and before gh5's.
    w.lane("gh4", cr("2026-10-23T00:00:00Z", "dup-rule", "gh4 again"))
    out = w.run("archive", "gh4")
    assert len(w.filed()) == 1, f"closed after the latest finding: filed again: {out}"
    w.lane("gh5", cr(GH5_AT, "dup-rule", "gh5 after the close"))
    out = w.run("archive", "gh5")
    want = filed(keys[1], TARGET, "dup-rule")
    assert any(x.startswith(want) for x in out), f"closed before the latest finding: {out}"

    caught = "owner-caught-stale-pr"
    w.director(
        finding("2026-10-25T00:00:00Z", caught, "a"),
        finding("2026-10-25T01:00:00Z", caught, "b"),
        rf("2026-10-25T02:00:00Z", "reflection-missed", "owner caught a stale PR after the last"
           " reflection; add a stale-PR question", question="director-reflection-missed",
           route="reflection/questions.json owner-asked"),
    )  # fmt: skip
    w.lane("gh6", rf("2026-10-25T00:00:00Z", "reflection-missed", "gh1 reflection found no gap;"
                     " gh6 review found the rule broken; reword undetected-rule", blocking=False,
                     question="reflection-missed",
                     route="reflection/questions.json undetected-rule"))  # fmt: skip
    out = w.run("archive", "gh6")
    for key, repo in ((keys[2], TARGET), (keys[3], KIT)):
        want = filed(key, repo, "reflection-missed")
        assert any(x.startswith(want) for x in out), f"not filed in {repo}: {out}"
    got = w.filed()
    assert len(got) == 4, got
    changes = "Changes: the question list, reflection/questions.json"
    issue(got[2], TARGET, "reflection-missed ", changes, "reword undetected-rule")
    issue(got[3], KIT, "reflection-missed ", changes, "add a stale-PR question")
    assert not any(caught in i.title for i in got), got

    w.none_filed(w.run("reflect", "--director"), 4, "refiled")


def other_lane(s: Scratch) -> None:
    """Every due subject files, whichever lane's reflection runs: archived gh1 and gh2 hold one
    dup-rule-other finding each, the archive of unrelated gh3 files the class in gh1/gh2's target
    quoting both; a further archive files nothing."""
    w, (key,) = World(s, "other_lane"), FILED["other_lane"]
    gh12 = ("gh1 restated the merge rule", "gh2 restated the gate rule")
    for n, (lane, summary) in enumerate(zip(("gh1", "gh2"), gh12, strict=True)):
        w.lane(lane, cr(f"2026-10-2{n}T00:00:00Z", "dup-rule-other", summary), archived=True)
    w.lane("gh3")
    out = w.run("archive", "gh3")
    want = filed(key, TARGET, "dup-rule-other", two("none given by a reflection"))
    assert want in out, f"other lane: due class not filed: {out}"
    assert (w.lanes / "archive" / "gh3.toml").is_file(), f"other lane: gh3 not archived: {out}"
    (i,) = w.filed()
    issue(i, TARGET, "dup-rule-other]", *gh12)
    w.lane("gh4")
    w.none_filed(w.run("archive", "gh4"), 1, "other lane: refiled")


def routed(s: Scratch) -> None:
    """#acceptance-writer-route-lane through reflect --director: the class's findings in lanes,
    the director routes it: filed in their target naming the route."""
    w, (key,) = World(s, "routed"), FILED["routed"]
    for n, lane in enumerate(("gh1", "gh2")):
        at, summary = f"2026-10-2{n}T00:00:00Z", f"{lane} check missed a stale doc"
        w.lane(lane, cr(at, "stale-check", summary), archived=True)
    route = "agents/code-reviewer.md Rules"
    why = "summary: 2 code-review findings in gh1, gh2"
    reply(s, "director", f"class: stale-check | question: writer-route | route: {route} | {why}")
    out = w.run("reflect", "--director")
    assert filed(key, TARGET, "stale-check", two(route)) in out, f"routed: {out}"
    (i,) = w.filed()
    issue(i, TARGET, "stale-check]", f"Route: {route}")


def counts(s: Scratch) -> None:
    """What counts: two reflection findings of a class in two lanes, two blocking ones in one
    lane, a non-blocking review finding beside a blocking one, or the director log's: none due; a
    blocking product-judge (qc) finding counts."""
    w, (key,) = World(s, "counts"), FILED["counts"]
    q = {"blocking": False, "question": "undetected-rule", "route": "r"}
    w.lane(
        "gh1",
        rf("2026-10-20T00:00:00Z", "refl-only", "gh1 reflection", **q),
        cr("2026-10-20T00:00:00Z", "one-lane", "gh1 a"),
        cr("2026-10-20T01:00:00Z", "one-lane", "gh1 b"),
        cr("2026-10-20T02:00:00Z", "judged", "gh1 review"),
        archived=True,
    )
    w.lane(
        "gh2",
        rf("2026-10-21T00:00:00Z", "refl-only", "gh2 reflection", **q),
        cr("2026-10-21T01:00:00Z", "one-lane", "gh2 note", blocking=False),
        cr("2026-10-21T02:00:00Z", "judged", "gh2 judge", "qc"),
        archived=True,
    )
    w.director(finding("2026-10-22T00:00:00Z", "one-lane", "director saw it"))
    w.lane("gh3")
    out = w.run("archive", "gh3")
    want = filed(key, TARGET, "judged", "(2 findings; ")
    assert any(x.startswith(want) for x in out), f"counts: want judged filed: {out}"
    assert len(w.filed()) == 1, f"counts: want only judged filed: {w.filed()}"


if __name__ == "__main__":
    main(lifecycle, other_lane, routed, counts)
