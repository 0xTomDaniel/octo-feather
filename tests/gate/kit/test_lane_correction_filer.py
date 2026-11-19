"""The correction filer's rules, in-process at its interface, `file_corrections` of
scripts/correction_lanes.py (its module docstring; ticket #1083, seams agreed on it before any
test): what counts, when a class is due, refiling, recurrence (legacy duplicate issues included,
#1068), reflection-missed, where each files (the tracker of the repository owning its route,
#1004) and what it quotes, and the `target:` records refused. The rule: spec comms
#reflection-correction, issue-lifecycle #lanes-correction.

Each test writes a scratch state dir's lanes/ (lane_correction.py's helpers) and calls
file_corrections on it: the real github-issues scripts and gh calls over the testkit's gh
(testkit/gh.py, its store: each tracker its repository's issues and comments, every request in
its log), the scratch's environment and directory the process's for the call. No reflector
runs: what the lane and director reflections append, the commands' part (octo-feather-lane
archive, reflect; their wiring: test_lane_correction.py), is written as their finding lines,
dated NOW, the run's clock. Each test is the command scenario of the same name it replaced
(parity: tests/parity/lane-correction-*/), its facts the filer's: the lines the command prints
are each Outcome's text.

Deviations: lifecycle, other_lane, routed and counts replayed real gh's recordings of filing in
0xTomDaniel/spec-chat (the lanes' target) until #1004; under the route-owner rule they file in the
kit's tracker, which no tape recorded, and a tape is never recorded by filing a real issue, so they
run on the store (the tape, testkit/recordings/lane-correction.json, gone with them): the keys are
the store's, the lifecycle's first issue closed by the test at the closedAt the tape held, the
classes the fresh names the recordings needed (restated-rule, restated-rule-other, stale-doc,
judged-qc). A reflection-missed finding a reflection gives is dated by the run's clock, so
missed_at_once always ran on the store (director ruling, round 3).
"""

from __future__ import annotations

import json
import os
import re
from typing import TYPE_CHECKING

import pytest
from correction_lanes import Outcome, Refused, file_corrections
from lane_correction import (
    CHANGES,
    CLOSED_AT,
    DUP,
    GH5_AT,
    HERE,
    KIT,
    LEGACY,
    MISSED,
    OLD,
    PRIV,
    TAPE372,
    TARGET,
    VIEW,
    comments,
    cr,
    created,
    director,
    filed,
    finding,
    gap,
    gh_issue,
    issue,
    issues,
    lane,
    put,
    quotes,
    rf,
    sent,
    target_lane,
    two,
)
from testkit import Scratch

if TYPE_CHECKING:
    from pathlib import Path

NOW = "2026-11-19T12:00:00Z"  # a reflection's findings' at: the run's clock in the commands


class World:
    """One test's scratch: S (its gh store), TOP its state dir."""

    def __init__(self, s: Scratch) -> None:
        self.s = s
        self.top = s.root / "state" / "octo-feather"
        self.top.mkdir(parents=True)

    def file(self) -> list[str]:
        """file_corrections on TOP's lanes/: the lines the command prints for its outcomes."""
        return said(file_corrections(self.top / "lanes"))

    def refused(self) -> str:
        """file_corrections refusing: its message."""
        with pytest.raises(Refused) as e:
            file_corrections(self.top / "lanes")
        return str(e.value)

    def reflected(self, who: str, *replies: str) -> None:
        """The finding lines WHO's reflection appends ("director": the director log's, no
        blocking; else lane WHO's, blocking false) for REPLIES, each `class: C | question: Q |
        route: R | summary: S` as the reflector's reply gives it."""
        lines: list[str] = []
        for r in replies:
            f = dict(x.split(": ", 1) for x in r.split(" | "))
            more: dict[str, object] = {} if who == "director" else {"blocking": False}
            more |= {"question": f["question"], "route": f["route"]}
            lines.append(rf(NOW, f["class"], f["summary"], **more))
        if who == "director":
            director(self.top, *lines)
            return
        with (self.top / "lanes" / f"{who}.handoffs.jsonl").open("a") as log:
            log.write("".join(f"{x}\n" for x in lines))


def said(outcomes: list[Outcome]) -> list[str]:
    return [x for o in outcomes for x in o.text.splitlines()]


@pytest.fixture
def world(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> World:
    """A World whose scratch environment (the testkit's gh first on PATH, its store) and
    directory are this process's while the test runs."""
    s = Scratch(tmp_path)
    for k in [k for k in os.environ if k not in s.env]:
        monkeypatch.delenv(k)
    for k, v in s.env.items():
        monkeypatch.setenv(k, v)
    monkeypatch.chdir(s.root)
    return World(s)


@pytest.mark.criterion("comms#acceptance-reflect-files-route-owner")
def test_lane_correction_route_owner(world: World) -> None:
    """#acceptance-reflect-files-route-owner, the #850 regression: blocking findings of kit-skill
    in kit lane gh1 and private target lane x1 (x1's reflection routing it, untagged, in its own
    words), the director routing it to a kit skill; of target-only in x1, x2 and kit lane gh1,
    x2's lane reflection routing it `target:`; of own-only in kit lanes gh0 and gh1 alone, x2's
    reflection routing it `target:` too. Filing files kit-skill only in the kit's tracker,
    quoting x1's finding by lane, date and class alone and naming only the director's route;
    target-only only in PRIV's, quoting only x1's, x2's and x2's routing reflection finding;
    own-only only in PRIV's, quoting x2's routing reflection finding (never zero findings);
    nothing in the current directory's tracker."""
    s, top = world.s, world.top
    created(s, PRIV, "2026-10-01T00:00:00Z")
    private = "PRIVATE exo internals"
    at = ("2026-11-02T00:00:00Z", "2026-11-03T00:00:00Z", "2026-11-04T00:00:00Z")
    q = {"blocking": False, "question": "undetected-rule", "route": f"{private} route"}
    lane(
        top,
        "gh1",
        cr(at[0], "kit-skill", "gh1 kit finding"),
        cr(at[0], "target-only", "gh1 kit finding of target-only"),
        cr(at[0], "own-only", "gh1 kit finding of own-only"),
        repo=KIT,
        archived=True,
    )
    lane(top, "gh0", cr(at[0], "own-only", "gh0 kit finding of own-only"), repo=KIT, archived=True)
    target_lane(
        top,
        "x1",
        cr(at[1], "kit-skill", f"{private} x1 kit-skill"),
        rf(at[1], "kit-skill", f"{private} x1 reflection", **q),
        cr(at[1], "target-only", "x1 target-only finding"),
        archived=True,
    )
    target_lane(top, "x2", cr(at[2], "target-only", "x2 target-only finding"))
    world.reflected("x2", "class: target-only | question: undetected-rule | "
                    "route: target: src/exo/rules.py | summary: x2 found its own rule unchecked",
                    "class: own-only | question: undetected-rule | "
                    "route: target: src/exo/own.py | summary: x2 own-only reflection")  # fmt: skip
    route = ".agents/skills/tdd/SKILL.md Seams"
    world.reflected("director", f"class: kit-skill | question: writer-route | route: {route} | "
                    "summary: 2 code-review findings in gh1, x1")  # fmt: skip
    out = world.file()
    assert filed("1", KIT, "kit-skill", two(route)) in out, out
    for cls, rest in (
        ("target-only", "(3 findings; route: target: src/exo/rules.py)"),
        ("own-only", "(1 finding; route: target: src/exo/own.py)"),
    ):
        assert any(x.endswith(f" in github-issues {PRIV} for {cls} {rest}") for x in out), out
    assert (issues(s, KIT), issues(s, PRIV), issues(s)) == ([1], [1, 2], []), out
    titled = {str(issue(s, n, PRIV)["title"]).split()[1].rstrip("]"): n for n in (1, 2)}
    kit_issue, priv_issue = issue(s, 1, KIT), issue(s, titled["target-only"], PRIV)
    assert "kit-skill" in str(kit_issue["title"]), kit_issue
    body = str(kit_issue["body"])
    assert f"Route: {route}\n" in body, body
    assert "- gh1 2026-11-02T00:00:00Z code-review: gh1 kit finding" in body, body
    assert "\n- x1 2026-11-03T00:00:00Z kit-skill\n" in body + "\n", body
    for leak in (private, "exo", "target-only"):
        assert leak not in body, (leak, body)
    assert "target-only" in str(priv_issue["title"]), priv_issue
    body = str(priv_issue["body"])
    for want in (
        "Route: target: src/exo/rules.py\n",
        "x1 target-only finding",
        "x2 target-only finding",
        "reflection (undetected-rule), route target: src/exo/rules.py: x2 found its own rule",
    ):
        assert want in body, (want, body)
    assert "gh1" not in body, body
    body = str(issue(s, titled["own-only"], PRIV)["body"])
    assert "Findings (1):\n- x2 " in body, body
    assert "route target: src/exo/own.py: x2 own-only reflection" in body, body
    assert "gh0" not in body, body
    assert "gh1" not in body, body


def test_lane_correction_refusal(world: World) -> None:
    """A `target:` route whose lane record's repository was re-created after the lane started
    (0xTomDaniel/spec-chat, gh's recorded answer), renamed, or not named: refused naming the
    record to fix, nothing filed in any tracker."""
    s, top = world.s, world.top
    (rec,) = json.loads(VIEW.read_text())
    s.gh.store(f"api/repos/{TARGET}.json", json.loads(rec["out"]))
    created(s, "owner/old", "2026-10-01T00:00:00Z", "owner/new")
    created(s, PRIV, "2026-10-01T00:00:00Z")
    target_lane(top, "s1", cr("2026-11-02T00:00:00Z", "own-rule", "s1 a"), archived=True)
    target_lane(top, "s2", cr("2026-11-03T00:00:00Z", "own-rule", "s2 b"))
    world.reflected("s2", "class: own-rule | question: undetected-rule | route: target: "
                    "src/rule.py | summary: s2 own rule")  # fmt: skip
    for repo, why in (
        (TARGET, "created 2026-11-13T03:20:54Z, after the lane started"),
        ("owner/old", "is now owner/new"),
        ("", "names no repository"),
    ):
        target_lane(top, "s2", cr("2026-11-03T00:00:00Z", "own-rule", "s2 b"), repo=repo)
        world.reflected("s2", "class: own-rule | question: undetected-rule | route: target: "
                        "src/rule.py | summary: s2 own rule")  # fmt: skip
        out = world.refused()
        assert str(top / "lanes" / "s2.toml") in out, (repo, out)
        assert why in out, (repo, out)
        for r in (KIT, PRIV, TARGET, "owner/old", "owner/new", HERE):
            assert issues(s, r) == [], (repo, r, out)


def test_lane_correction_lifecycle(world: World) -> None:
    """#acceptance-reflect-files-correction, #acceptance-writer-route-lane: archived gh1 logged one
    restated-rule finding, target lane gh2's review the second, the director reflection routes
    the class to a kit role: filing files it in the kit's tracker (the route's owner, never gh2's
    target), quoting gh1's finding, gh2's by lane, date and class, and the route, the key
    printed. Its issue closed after the class's latest finding: nothing; closed before a newer
    one: files again (an open one, a new finding: recurrence)."""
    s, top = world.s, world.top
    cls, route = "restated-rule", "agents/implementer.md Rules"
    gh12 = ("gh1 restated the merge rule", "gh2 restated the gate rule")
    lane(top, "gh1", cr("2026-10-20T00:00:00Z", cls, gh12[0]), repo=KIT, archived=True)
    lane(top, "gh2", cr("2026-10-21T00:00:00Z", cls, gh12[1]), repo=TARGET)
    why = "summary: 2 code-review findings in gh1, gh2"
    world.reflected("director", f"class: {cls} | question: writer-route | route: {route} | {why}")
    out = world.file()
    assert filed("1", KIT, cls, two(route)) in out, f"filing: {out}"
    (i,) = sent(s)
    gh2 = f"- gh2 2026-10-21T00:00:00Z {cls}"
    quotes(i, KIT, cls, f"Class: {cls}", f"Route: {route}", gh12[0], gh2)
    assert gh12[1] not in i.body, f"quoted a target lane's summary: {i.body}"
    assert "question list" not in i.body, i.body
    assert (issues(s, TARGET), issues(s)) == ([], []), "filed in a contributing lane's tracker"

    lane(top, "gh4", cr("2026-10-23T00:00:00Z", cls, "gh4 again"), repo=KIT)
    put(s, KIT, issue(s, 1, KIT) | {"state": "CLOSED", "closedAt": CLOSED_AT})
    out = world.file()
    assert len(sent(s)) == 1, f"closed after the latest finding: filed again: {out}"
    lane(top, "gh5", cr(GH5_AT, cls, "gh5 after the close"), repo=KIT)
    out = world.file()
    want = filed("2", KIT, cls)
    assert any(x.startswith(want) for x in out), f"closed before the latest finding: {out}"


def test_lane_correction_other_lane(world: World) -> None:
    """Every due class files, whichever lane's reflection runs: archived gh1 and gh2 hold one
    restated-rule-other finding each, filing beside unrelated gh3 files the class in the kit's
    tracker (no route: the kit's) quoting both; a further filing files nothing."""
    s, top = world.s, world.top
    cls = "restated-rule-other"
    gh12 = ("gh1 restated the merge rule", "gh2 restated the gate rule")
    for n, (name, summary) in enumerate(zip(("gh1", "gh2"), gh12, strict=True)):
        at = f"2026-10-2{n}T00:00:00Z"
        lane(top, name, cr(at, cls, summary), repo=KIT, archived=True)
    lane(top, "gh3", repo=KIT)
    out = world.file()
    want = filed("1", KIT, cls, two("none given by a reflection"))
    assert want in out, f"other lane: due class not filed: {out}"
    (i,) = sent(s)
    quotes(i, KIT, cls, *gh12)
    lane(top, "gh4", repo=KIT)
    out = world.file()
    assert out == [], f"other lane: refiled: {out}"
    assert len(sent(s)) == 1, f"other lane: refiled: {sent(s)}"


def test_lane_correction_routed(world: World) -> None:
    """#acceptance-writer-route-lane: the class's findings in lanes, the director routes it: filed
    in the kit's tracker naming the route."""
    s, top = world.s, world.top
    cls, route = "stale-doc", "agents/code-reviewer.md Rules"
    for n, name in enumerate(("gh1", "gh2")):
        at, summary = f"2026-10-2{n}T00:00:00Z", f"{name} check missed a stale doc"
        lane(top, name, cr(at, cls, summary), repo=KIT, archived=True)
    why = "summary: 2 code-review findings in gh1, gh2"
    world.reflected("director", f"class: {cls} | question: writer-route | route: {route} | {why}")
    out = world.file()
    assert filed("1", KIT, cls, two(route)) in out, f"routed: {out}"
    (i,) = sent(s)
    quotes(i, KIT, cls, f"Route: {route}")


def test_lane_correction_counts(world: World) -> None:
    """What counts: two reflection findings of a class in two lanes, two blocking ones in one
    lane, a non-blocking review finding beside a blocking one, or the director log's: none due; a
    blocking product-judge (qc) finding counts."""
    s, top = world.s, world.top
    q = {"blocking": False, "question": "undetected-rule", "route": "r"}
    lane(
        top,
        "gh1",
        rf("2026-10-20T00:00:00Z", "refl-only", "gh1 reflection", **q),
        cr("2026-10-20T00:00:00Z", "one-lane", "gh1 a"),
        cr("2026-10-20T01:00:00Z", "one-lane", "gh1 b"),
        cr("2026-10-20T02:00:00Z", "judged-qc", "gh1 review"),
        repo=KIT,
        archived=True,
    )
    lane(
        top,
        "gh2",
        rf("2026-10-21T00:00:00Z", "refl-only", "gh2 reflection", **q),
        cr("2026-10-21T01:00:00Z", "one-lane", "gh2 note", blocking=False),
        cr("2026-10-21T02:00:00Z", "judged-qc", "gh2 judge", "qc"),
        repo=KIT,
        archived=True,
    )
    director(top, finding("2026-10-22T00:00:00Z", "one-lane", "director saw it"))
    lane(top, "gh3", repo=KIT)
    out = world.file()
    want = filed("1", KIT, "judged-qc", "(2 findings; ")
    assert any(x.startswith(want) for x in out), f"counts: want judged-qc filed: {out}"
    assert len(sent(s)) == 1, f"counts: want only judged-qc filed: {sent(s)}"


def test_lane_correction_missed_at_once(world: World) -> None:
    """#acceptance-reflection-missed-lane: lane gh6's reflection and the director reflection each
    give a reflection-missed finding: both file at once in the kit's tracker (every
    reflection-missed finding's), not gh6's target, one issue titled MISSED naming the question
    list, quoting the director's finding and gh6's by lane, date and class only; owner-caught
    findings twice in the director log file nothing. Filing again, no new finding: nothing filed
    or commented."""
    s, top = world.s, world.top
    caught = "owner-caught-stale-pr"
    director(
        top,
        finding("2026-10-25T00:00:00Z", caught, "a"),
        finding("2026-10-25T01:00:00Z", caught, "b"),
    )
    lane(top, "gh6", repo=TARGET)
    mine = "gh1 reflection found no gap; gh6 review found the rule broken; reword undetected-rule"
    theirs = "owner caught a stale PR after the last reflection; add a stale-PR question"
    world.reflected("gh6", "class: reflection-missed | question: reflection-missed | route: "
                    f"reflection/questions.json undetected-rule | summary: {mine}")  # fmt: skip
    world.reflected("director", "class: reflection-missed | question: director-reflection-missed"
                    " | route: reflection/questions.json owner-asked | summary: "
                    f"{theirs}")  # fmt: skip
    out = world.file()
    want = filed(
        "1", KIT, "reflection-missed", "(2 findings; route: reflection/questions.json owner-asked)"
    )
    assert want in out, f"not filed in the kit: {out}"
    assert (issues(s, KIT), issues(s, TARGET), issues(s)) == ([1], [], []), out
    d = issue(s, 1, KIT)
    assert d["title"] == MISSED, d
    body = str(d["body"])
    for q in (CHANGES, theirs, "\n- gh6 "):
        assert q in body, (q, d)
    assert re.search(r"(?m)^- gh6 \S+ reflection-missed$", body), body
    for leak in (mine, "undetected-rule"):
        assert leak not in body, (leak, body)
    out = world.file()
    assert out == [], f"refiled: {out}"
    assert (issues(s, KIT), comments(s, 1, KIT)) == ([1], []), f"wrote again: {out}"


@pytest.mark.criterion("comms#acceptance-reflect-recurrence-comments")
def test_lane_correction_recurrence(world: World) -> None:
    """Kit lanes gh1, gh2 each logged a duplicated-rule finding its open issue #7 in the kit's
    tracker (the route owner: no route) quotes (#9 open too, newer); private target lane gh3's
    review logs a third: the criterion's outcome, on #7, the oldest open, gh3's finding by lane,
    date and class only; the running count 3; no other tracker. Filing again: nothing."""
    s, top = world.s, world.top
    for n, at in (("gh1", "2026-10-20"), ("gh2", "2026-10-21")):
        summary = f"{n} restated a rule"
        lane(top, n, cr(f"{at}T00:00:00Z", "duplicated-rule", summary), repo=KIT, archived=True)
    body = (
        "Findings (2):\n- gh1 2026-10-20T00:00:00Z code-review: gh1 restated a rule\n"
        "- gh2 2026-10-21T00:00:00Z code-review: gh2 restated a rule\n"
    )
    for n in (9, 7):
        put(s, KIT, gh_issue(n, DUP, body))
    target_lane(top, "gh3", cr("2026-10-22T00:00:00Z", "duplicated-rule", "gh3 restated it again"))
    out = "\n".join(world.file())
    assert issues(s, KIT) == [7, 9], f"filed a new issue: {issues(s, KIT)} {out}"
    assert (issues(s, PRIV), issues(s)) == ([], []), (
        f"wrote to a contributing lane's tracker: {out}"
    )
    assert comments(s, 9, KIT) == [], "commented on the newer open issue"
    (c,) = comments(s, 7, KIT)
    assert "\n- gh3 2026-10-22T00:00:00Z duplicated-rule" in f"{c}\n", c
    assert "restated it again" not in c, f"quoted a target lane's summary: {c}"
    assert "running count 3" in c, c
    assert "gh1 restated" not in c, f"quoted an old finding: {c}"
    assert "gh2 restated" not in c, f"quoted an old finding: {c}"
    assert f"correction lane: commented https://github.com/{KIT}/issues/7#issuecomment-1001" in out
    assert "- gh3 2026-10-22T00:00:00Z duplicated-rule" in out, f"comment not printed: {out}"
    lane(top, "gh4", repo=KIT)
    out = "\n".join(world.file())
    assert out == "", out
    assert (issues(s, KIT), len(comments(s, 7, KIT))) == ([7, 9], 1), f"commented again: {out}"


@pytest.mark.criterion("comms#acceptance-reflect-recurrence-comments")
def test_lane_correction_legacy_quote(world: World) -> None:
    """The kit's open test-is-check issue #4, filed before #1004 as #849 was, quotes kit lane
    gh586's finding and target lane specchat-gh221's in full. Filing beside gh5 (no finding) adds
    nothing: specchat-gh221's finding, now quoted minimally, is the one #4 already quotes. Then
    private lane x3's new finding: one comment, x3's alone, minimally, running count 3."""
    s, top = world.s, world.top
    cls = "test-is-check"
    old = ("2026-11-05T20:56:49Z", "2026-11-11T01:17:25Z")
    lane(top, "gh586", cr(old[0], cls, "ci_scope scans workflow text"), repo=KIT, archived=True)
    spec = "TIMING-QUALIFIED scan of the spec-chat gate"
    lane(top, "specchat-gh221", cr(old[1], cls, spec), repo=TARGET, archived=True)
    body = (
        f"Class: {cls}\nRoute: none given by a reflection\n\nFindings (2):\n"
        f"- gh586 {old[0]} code-review: ci_scope scans workflow text\n"
        f"- specchat-gh221 {old[1]} code-review: {spec}\n"
    )
    put(s, KIT, gh_issue(4, f"[correction-lane {cls}] repeated finding class: {cls}", body))
    lane(top, "gh5", repo=KIT)
    out = world.file()
    assert out == [], f"a finding #4 quotes in full counted as new: {out}"
    assert comments(s, 4, KIT) == [], out
    target_lane(top, "x3", cr("2026-11-12T00:00:00Z", cls, "x3 private text"))
    out = world.file()
    (c,) = comments(s, 4, KIT)
    assert "1 new finding; running count 3." in c, c
    assert c.endswith("\n\n- x3 2026-11-12T00:00:00Z test-is-check"), c
    assert issues(s, KIT) == [4], out


@pytest.mark.criterion("comms#acceptance-reflect-recurrence-comments")
def test_lane_correction_legacy_duplicates(world: World) -> None:
    """#acceptance-reflect-recurrence-comments, the #1068 regression: lane gh7's log holds three
    reflection-missed findings of one reflection run (one date), each quoted in full by its own
    legacy duplicate issue in the kit's tracker (#2 open, #3 closed, #4 open), #5 (closed)
    quoting the first again: filing comments nothing. Its reflection then finds a new gap: one
    comment, on #2, quoting it alone, running count 4 (each quoted finding once). Filing again
    adds nothing."""
    s, top = world.s, world.top
    at = "2026-11-06T00:00:00Z"
    old = [f"gh7 old gap {x}" for x in "abc"]
    q = {"question": "reflection-missed", "route": "r"}
    lane(top, "gh7", *(rf(at, "reflection-missed", x, **q) for x in old), repo=KIT)
    line = f"- gh7 {at} reflection (reflection-missed), route r: "
    for n, title, x, state in (
        (2, LEGACY, old[0], "OPEN"),
        (3, MISSED, old[1], "CLOSED"),
        (4, LEGACY, old[2], "OPEN"),
        (5, LEGACY, old[0], "CLOSED"),
    ):
        closed = None if state == "OPEN" else "2026-11-07T00:00:00Z"
        d = gh_issue(n, title, f"{CHANGES}\n\nFindings (1):\n{line}{x}")
        put(s, KIT, d | {"state": state, "closedAt": closed})
    out = world.file()
    assert out == [], f"re-quoted findings legacy duplicates quote: {out}"
    assert [comments(s, n, KIT) for n in (2, 3, 4, 5)] == [[]] * 4, out
    new = "gh7 new gap d"
    world.reflected("gh7", "class: reflection-missed | question: reflection-missed | route: r | "
                    f"summary: {new}")  # fmt: skip
    out = world.file()
    (c,) = comments(s, 2, KIT)
    assert "1 new finding; running count 4." in c, c
    assert c.endswith(f", route r: {new}"), c
    assert not any(x in c for x in old), f"re-quoted an old finding: {c}"
    assert [comments(s, n, KIT) for n in (3, 4, 5)] == [[]] * 3, out
    assert any(x.startswith("correction lane: commented ") for x in out), out
    out = world.file()
    assert out == [], out
    assert (issues(s, KIT), len(comments(s, 2, KIT))) == ([2, 3, 4, 5], 1), f"wrote again: {out}"


@pytest.mark.criterion("comms#acceptance-reflect-recurrence-comments")
def test_lane_correction_recorded_372(world: World) -> None:
    """#acceptance-reflect-recurrence-comments on the real case: the kit's tracker as real gh
    answered before comment 6997429551 (TAPE372: open #372 and the reflection-missed issues
    quoting that comment's findings, #375, #393, #418, #426, #384, #434 among them), the 44
    findings that comment quoted back in their logs (the director's, archived kit lanes gh261 and
    gh802): filing beside kit lane gh850 files and comments nothing."""
    s, top = world.s, world.top
    said_, listed = (json.loads(r["out"]) for r in json.loads(TAPE372.read_text()))
    for d in listed:
        put(s, KIT, d)
    form = re.compile(r"- (\S+) (\S+) reflection \(([^)]*)\), route (.*?): (.*)")
    logs: dict[str, list[str]] = {}
    for m in (form.fullmatch(x) for x in str(said_["body"]).splitlines() if x.startswith("- ")):
        assert m, said_
        found = rf(m[2], "reflection-missed", m[5], question=m[3], route=m[4])
        logs.setdefault(m[1], []).append(found)
    assert sorted((k, len(v)) for k, v in logs.items()) == [
        ("director", 42),
        ("gh261", 1),
        ("gh802", 1),
    ], logs.keys()
    director(top, *logs["director"])
    for name in ("gh261", "gh802"):
        lane(top, name, *logs[name], repo=KIT, archived=True)
    lane(top, "gh850", repo=KIT)
    before = comments(s, 372, KIT)
    out = world.file()
    assert out == [], f"re-quoted findings the class's issues quote: {out}"
    assert comments(s, 372, KIT) == before, out
    assert issues(s, KIT) == sorted(int(str(d["number"])) for d in listed), out


@pytest.mark.criterion("issue-lifecycle#acceptance-reflection-missed-lane")
def test_lane_correction_reflection_missed(world: World) -> None:
    """An open legacy timestamped reflection-missed issue #5 in the kit's tracker quoting the
    director's old finding; the director reflection gives a new one: a comment on #5, then
    filing again with none adds nothing; then #5 closed before the next finding: a new issue."""
    s, top = world.s, world.top
    (top / "director.handoffs.jsonl").write_text(
        '{"at":"2026-11-05T01:02:03Z","kind":"finding","class":"reflection-missed",'
        '"question":"director-reflection-missed","route":"r","summary":"old gap"}\n'
    )
    put(s, KIT, gh_issue(5, LEGACY, OLD))
    new_gap = "owner caught a stale PR after the last reflection; add a stale-PR question"
    world.reflected(
        "director",
        "class: reflection-missed | question: director-reflection-missed | route: "
        f"reflection/questions.json owner-asked | summary: {new_gap}",
    )
    out = "\n".join(world.file())
    assert issues(s, KIT) == [5], f"filed a new issue: {issues(s, KIT)} {out}"
    (c,) = comments(s, 5, KIT)
    assert f"route reflection/questions.json owner-asked: {new_gap}" in c, c
    assert "- director " in c, c
    assert "running count 2" in c, c
    assert "old gap" not in c, c
    assert new_gap in out, f"comment not printed: {out}"
    out = "\n".join(world.file())
    assert out == "", out
    assert (issues(s, KIT), len(comments(s, 5, KIT))) == ([5], 1), f"wrote again: {out}"
    put(s, KIT, issue(s, 5, KIT) | {"state": "CLOSED", "closedAt": "2026-11-06T00:00:00Z"})
    out = "\n".join(world.file())
    assert issues(s, KIT) == [5, 6], out
    new = issue(s, 6, KIT)
    assert new["title"] == MISSED, new
    assert new_gap in str(new["body"]), new
    assert CHANGES in str(new["body"]), new
    assert "old gap" in str(new["body"]), new
    assert len(comments(s, 5, KIT)) == 1, "commented on a closed issue"
    assert issues(s) == [], "wrote to another tracker than the kit's"


def test_lane_correction_malformed(world: World) -> None:
    """gh's issue list printing an issue not in its form (each field below wrong or missing):
    refused naming the issue and the fix, nothing written."""
    s, top = world.s, world.top
    (top / "director.handoffs.jsonl").write_text(
        '{"at":"2026-11-05T01:02:03Z","kind":"finding","class":"reflection-missed",'
        '"question":"director-reflection-missed","route":"r","summary":"old gap"}\n'
    )
    good = gh_issue(1, LEGACY, OLD)
    for bad in (
        {"comments": ""},
        {"comments": None},
        {"comments": [1]},
        {"comments": [{"body": 2}]},
        {"comments": [{"author": {"login": "x"}}]},
        {"body": None},
        {"title": 5},
        {"state": None},
        {"closedAt": 3},
        {"number": "1"},
        {"number": True},
    ):
        put(s, KIT, good | bad, 1)
        out = world.refused()
        for want in ("item 1", "is not gh's issue JSON", "update gh, then rerun"):
            assert want in out, (bad, out)
        assert issues(s, KIT) == [1], (bad, issues(s, KIT))
        assert issue(s, 1, KIT) == good | bad, (bad, out)


def test_lane_correction_two_targets(world: World) -> None:
    """Archived gh1 (owner/target-a) and gh2 (owner/target-b) each logged a reflection-missed
    gap: the kit's tracker (every reflection-missed finding's) holds one issue, quoting each by
    lane, date and class only; neither target's tracker holds one."""
    s, top = world.s, world.top
    lane(top, "gh1", gap(1, "gap in target A"), repo="owner/target-a", archived=True)
    lane(top, "gh2", gap(2, "gap in target B"), repo="owner/target-b")
    world.file()
    assert issues(s, KIT) == [1], issues(s, KIT)
    body = str(issue(s, 1, KIT)["body"])
    for want in (
        "- gh1 2026-11-01T00:00:00Z reflection-missed",
        "- gh2 2026-11-02T00:00:00Z reflection-missed",
    ):
        assert want in body, (want, body)
    for leak in ("gap in target", "target-a", "target-b"):
        assert leak not in body, (leak, body)
    for repo in ("owner/target-a", "owner/target-b", HERE):
        assert issues(s, repo) == [], (repo, issues(s, repo))


def test_lane_correction_one_target(world: World) -> None:
    """Archived gh1 and gh2, both of owner/target, each logged a reflection-missed gap no issue
    quotes; the kit's tracker holds an open legacy issue #5: filing adds exactly one comment on
    #5, quoting both by lane, date and class only, files none, and writes nothing in
    owner/target's tracker; filing beside gh3 then adds nothing."""
    s, top = world.s, world.top
    put(s, KIT, gh_issue(5, LEGACY, OLD))
    lane(top, "gh1", gap(1, "first new gap"), repo="owner/target", archived=True)
    lane(top, "gh2", gap(2, "second new gap"), repo="owner/target")
    world.file()
    assert (issues(s, KIT), issues(s, "owner/target")) == ([5], []), issues(s, KIT)
    (c,) = comments(s, 5, KIT)
    assert "- gh1 2026-11-01T00:00:00Z reflection-missed\n" in c, c
    assert c.endswith("- gh2 2026-11-02T00:00:00Z reflection-missed"), c
    assert "new gap" not in c, c
    assert "running count 3" in c, c
    lane(top, "gh3", repo="owner/target")
    world.file()
    assert len(comments(s, 5, KIT)) == 1, comments(s, 5, KIT)


def test_lane_correction_kit_lane(world: World) -> None:
    """A lane of the kit itself (its tracker the director's), its lane and director reflections
    each finding a reflection-missed gap: the kit's tracker holds one issue, quoting both."""
    s, top = world.s, world.top
    lane(top, "gh5", repo=KIT)
    world.reflected("gh5", "class: reflection-missed | question: reflection-missed | route: r1 | "
                    "summary: lane gap")  # fmt: skip
    world.reflected("director", "class: reflection-missed | question: director-reflection-missed"
                    " | route: r2 | summary: director gap")  # fmt: skip
    world.file()
    assert issues(s, KIT) == [1], issues(s, KIT)
    body = str(issue(s, 1, KIT)["body"])
    assert "route r1: lane gap" in body, body
    assert "route r2: director gap" in body, body
    assert comments(s, 1, KIT) == [], "commented on the issue it just filed"
