"""The scenarios of tests/gate/kit/test_lane_correction.py (its items), this file their command
(testkit.main): correction-lane filing over a tracker that may already hold the class's issue (the
rule: spec comms #reflection-correction; criteria #acceptance-reflect-recurrence-comments,
issue-lifecycle #acceptance-reflection-missed-lane) through `octo-feather-lane archive` and
`reflect --director`, in testkit.reflector's world, the tracker the testkit gh's store
(issue/N.json, its comments) or, where a tracker's search must lag a write or trackers differ,
its recorded answers (testkit/recordings/lane-correction-*.json)."""

from __future__ import annotations

import json
from pathlib import Path

from testkit import Scratch, kit, main, reflector, reply

TAPES = Path(__file__).parent / "testkit" / "recordings"
L = kit("octo-feather-lane")
DUP = "[correction-lane duplicated-rule] repeated finding class: duplicated-rule"
LEGACY = (
    "[correction-lane reflection-missed 2026-11-05T01:02:03Z abcd1234] change the question list:"
    " reflection-missed"
)
OLD = "- director 2026-11-05T01:02:03Z director (director-reflection-missed), route r: old gap"
NONE = "correction lanes: none filed or commented"
KIT = "0xTomDaniel/octo-feather"


def gh_issue(n: int, title: str, body: str) -> dict[str, object]:
    """Open issue N as gh's issue list prints it, no comment yet."""
    return {
        "number": n,
        "title": title,
        "state": "OPEN",
        "closedAt": None,
        "body": body,
        "comments": [],
    }


def cr(at: str, summary: str) -> str:
    d = {"at": at, "kind": "finding", "source": "code-review", "class": "duplicated-rule"}
    return json.dumps(d | {"blocking": True, "summary": summary}) + "\n"


def lane(top: Path, name: str, log: str = "", repo: str = "") -> None:
    (top / "lanes" / f"{name}.toml").write_text(
        f'issue = "{name}"\nsupervisor = "w9:p2"\ngoal = "scratch"\n'
        + (f'repository = "{repo}"\n' if repo else "")
    )
    (top / "lanes" / f"{name}.handoffs.jsonl").write_text(log)


def issue(s: Scratch, n: int) -> dict[str, object]:
    return json.loads((s.gh.dir / "issue" / f"{n}.json").read_text())


def issues(s: Scratch) -> list[int]:
    return sorted(int(p.stem) for p in (s.gh.dir / "issue").glob("*.json"))


def comments(s: Scratch, n: int) -> list[str]:
    return [str(c["body"]) for c in issue(s, n).get("comments") or []]  # type: ignore[union-attr]


def run(s: Scratch, *args: str, want: int = 0) -> str:
    """`octo-feather-lane ARGS`'s output, also printed: the scenario's demo for qc."""
    r = s.run([L, *args], want=want)
    out = f"{r.out}\n{r.err}"
    print(f"$ octo-feather-lane {' '.join(args)}\n{out.strip()}\n", flush=True)  # noqa: T201
    return out


def recurrence(s: Scratch) -> None:
    """Archived gh1, gh2 each logged a duplicated-rule finding its open issue #7 quotes (#9 open
    too, newer); gh3's review logs a third, then gh4 archives with none: the criterion's outcome,
    on #7, the oldest open; the running count 3."""
    top = reflector(s)
    (top / "lanes" / "archive").mkdir(parents=True)
    for n, at in (("gh1", "2026-10-20"), ("gh2", "2026-10-21")):
        (top / "lanes" / "archive" / f"{n}.handoffs.jsonl").write_text(
            cr(f"{at}T00:00:00Z", f"{n} restated a rule")
        )
    body = (
        "Findings (2):\n- gh1 2026-10-20T00:00:00Z code-review: gh1 restated a rule\n"
        "- gh2 2026-10-21T00:00:00Z code-review: gh2 restated a rule\n"
    )
    for n in (9, 7):
        s.gh.store(f"issue/{n}.json", gh_issue(n, DUP, body))
    lane(top, "gh3", cr("2026-10-22T00:00:00Z", "gh3 restated it again"))
    out = run(s, "archive", "gh3")
    assert issues(s) == [7, 9], f"filed a new issue: {issues(s)} {out}"
    assert comments(s, 9) == [], "commented on the newer open issue"
    (c,) = comments(s, 7)
    assert "- gh3 2026-10-22T00:00:00Z code-review: gh3 restated it again" in c, c
    assert "running count 3" in c, c
    assert "gh1 restated" not in c, f"quoted an old finding: {c}"
    assert "gh2 restated" not in c, f"quoted an old finding: {c}"
    assert "correction lane: commented https://github.com/o/r/issues/7#issuecomment-1001" in out
    assert "gh3 restated it again" in out, f"comment not printed: {out}"
    lane(top, "gh4")
    out = run(s, "archive", "gh4")
    assert NONE in out, out
    assert (issues(s), len(comments(s, 7))) == ([7, 9], 1), f"commented again: {out}"


def reflection_missed(s: Scratch) -> None:
    """The demo: an open legacy timestamped reflection-missed issue #5 quoting the director's old
    finding; `reflect --director` with a new one, then again with none; then #5 closed before the
    next finding: the outcomes the rule gives (the module docstring), in the kit's tracker."""
    top = reflector(s)
    (top / "director.handoffs.jsonl").write_text(
        '{"at":"2026-11-05T01:02:03Z","kind":"finding","class":"reflection-missed",'
        '"question":"director-reflection-missed","route":"r","summary":"old gap"}\n'
    )
    s.gh.store("issue/5.json", gh_issue(5, LEGACY, OLD))
    gap = "owner caught a stale PR after the last reflection; add a stale-PR question"
    reply(
        s,
        "director",
        "class: reflection-missed | question: director-reflection-missed | route: "
        f"reflection/questions.json owner-asked | summary: {gap}",
    )
    out = run(s, "reflect", "--director")
    assert issues(s) == [5], f"filed a new issue: {issues(s)} {out}"
    (c,) = comments(s, 5)
    assert f"route reflection/questions.json owner-asked: {gap}" in c, c
    assert "- director " in c, c
    assert "running count 2" in c, c
    assert "old gap" not in c, c
    assert "correction lane: commented https://github.com/o/r/issues/5#issuecomment-1001" in out
    assert gap in out, f"comment not printed: {out}"
    assert any("--repo 0xTomDaniel/octo-feather" in x for x in s.gh.log()), s.gh.log()
    reply(s, "director")
    out = run(s, "reflect", "--director")
    assert NONE in out, out
    assert (issues(s), len(comments(s, 5))) == ([5], 1), f"filed or commented again: {out}"
    closed = issue(s, 5) | {"state": "CLOSED", "closedAt": "2026-11-06T00:00:00Z"}
    s.gh.store("issue/5.json", closed)
    out = run(s, "reflect", "--director")
    assert "correction lane: filed 6 in github-issues 0xTomDaniel/octo-feather " in out, out
    new = issue(s, 6)
    title = "[correction-lane reflection-missed] change the question list: reflection-missed"
    assert new["title"] == title, new
    assert gap in str(new["body"]), new
    assert "Changes: the question list, reflection/questions.json" in str(new["body"]), new
    assert "old gap" in str(new["body"]), new
    assert len(comments(s, 5)) == 1, "commented on a closed issue"


def malformed(s: Scratch) -> None:
    """gh's issue list printing an issue not in its form (each field below wrong or missing):
    `reflect --director` refuses naming the issue and the fix, no traceback, nothing written."""
    top = reflector(s)
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
        s.gh.store("issue/1.json", good | bad)
        out = run(s, "reflect", "--director", want=1)
        assert "Traceback" not in out, out
        for want in ("item 1", "is not gh's issue JSON", "update gh, then rerun"):
            assert want in out, (bad, out)
        assert issues(s) == [1], (bad, issues(s))
        assert issue(s, 1) == good | bad, (bad, out)


def tape(s: Scratch, name: str) -> None:
    """The gh stand-in answering only testkit/recordings/lane-correction-NAME.json."""
    s.gh.store("tape.json", json.loads((TAPES / f"lane-correction-{name}.json").read_text()))


def calls(s: Scratch, kind: str) -> int:
    """How many `gh issue KIND` calls the stand-in answered."""
    return sum(x.startswith(f"issue {kind} ") for x in s.gh.log())


def two_targets(s: Scratch) -> None:
    """Archived gh1 (tracker owner/target-a) and gh2 (owner/target-b) each logged a
    reflection-missed gap: archiving gh2 files each in its own lane's tracker, one issue each."""
    top = reflector(s)
    (top / "lanes" / "archive").mkdir(parents=True)
    gap = (
        '{{"at":"2026-11-0{}T00:00:00Z","kind":"finding","source":"reflection","class":'
        '"reflection-missed","question":"reflection-missed","route":"{}","summary":"{}"}}\n'
    )
    lane(top, "gh1", gap.format(1, "ra", "gh1 gap"), repo="owner/target-a")
    for f in ("gh1.toml", "gh1.handoffs.jsonl"):
        (top / "lanes" / f).rename(top / "lanes" / "archive" / f)
    lane(top, "gh2", gap.format(2, "rb", "gh2 gap"), repo="owner/target-b")
    tape(s, "targets")
    out = run(s, "archive", "gh2")
    for repo, route in (("owner/target-a", "ra"), ("owner/target-b", "rb")):
        want = f"correction lane: filed 1 in github-issues {repo} for reflection-missed (1 finding;"
        assert f"{want} route: {route})" in out, out
    assert calls(s, "create") == 2, s.gh.log()


def kit_lane(s: Scratch) -> None:
    """A lane of the kit itself (its tracker the director's), its lane and director reflections
    each finding a reflection-missed gap, the tracker's search lagging this run's write (the
    recordings: a re-list misses the issue just filed): one issue, the lane's, and one comment on
    it, the director's."""
    top = reflector(s)
    (top / "lanes").mkdir()
    lane(top, "gh5", repo=KIT)
    reply(s, "lane", "class: reflection-missed | question: reflection-missed | route: r1 | "
          "summary: lane gap")  # fmt: skip
    reply(s, "director", "class: reflection-missed | question: director-reflection-missed | "
          "route: r2 | summary: director gap")  # fmt: skip
    tape(s, "stale")
    out = run(s, "archive", "gh5")
    filed = f"correction lane: filed 1 in github-issues {KIT} for reflection-missed (1 finding"
    assert filed in out, out
    said = f"correction lane: commented https://github.com/{KIT}/issues/1#issuecomment-1 on 1"
    assert said in out, out
    assert "route r2: director gap" in out.split(said)[1], f"comment not the director's: {out}"
    assert (calls(s, "create"), calls(s, "comment")) == (1, 1), s.gh.log()


if __name__ == "__main__":
    main(recurrence, reflection_missed, malformed, two_targets, kit_lane)
