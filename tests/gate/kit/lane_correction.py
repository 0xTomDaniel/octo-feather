"""The scenarios of tests/gate/kit/test_lane_correction.py (its items), this file their command
(testkit.main): correction-lane filing over trackers that may already hold the class's issue (the
rule: spec comms #reflection-correction; criteria #acceptance-reflect-recurrence-comments,
issue-lifecycle #acceptance-reflection-missed-lane) through `octo-feather-lane archive` and
`reflect --director`, in testkit.reflector's world, each tracker the testkit gh's store of that
repository's issues and their comments (testkit/gh.py)."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, cast

from testkit import Scratch, kit, main, reflector, reply

if TYPE_CHECKING:
    from pathlib import Path

L = kit("octo-feather-lane")
DUP = "[correction-lane duplicated-rule] repeated finding class: duplicated-rule"
MISSED = "[correction-lane reflection-missed] change the question list: reflection-missed"
LEGACY = (
    "[correction-lane reflection-missed 2026-11-05T01:02:03Z abcd1234] change the question list:"
    " reflection-missed"
)
OLD = "- director 2026-11-05T01:02:03Z director (director-reflection-missed), route r: old gap"
NONE = "correction lanes: none filed or commented"
KIT = "0xTomDaniel/octo-feather"
HERE = "o/r"  # the tracker of a lane record naming no repository: the current directory's


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


def put(s: Scratch, repo: str, d: dict[str, object], n: int = 0) -> None:
    """Issue D stored in REPO's tracker as number N (default: its own)."""
    s.gh.store(f"{idir(repo)}/{n or d['number']}.json", d)


def idir(repo: str) -> str:
    return "issue" if repo == HERE else f"repos/{repo}/issue"


def issue(s: Scratch, n: int, repo: str = HERE) -> dict[str, object]:
    return json.loads((s.gh.dir / idir(repo) / f"{n}.json").read_text())


def issues(s: Scratch, repo: str = HERE) -> list[int]:
    return sorted(int(p.stem) for p in (s.gh.dir / idir(repo)).glob("*.json"))


def comments(s: Scratch, n: int, repo: str = HERE) -> list[str]:
    cs = cast("list[dict[str, object]]", issue(s, n, repo)["comments"])
    return [str(c["body"]) for c in cs]


def cr(at: str, summary: str) -> str:
    d = {"at": at, "kind": "finding", "source": "code-review", "class": "duplicated-rule"}
    return json.dumps(d | {"blocking": True, "summary": summary}) + "\n"


def gap(day: int, summary: str) -> str:
    """A lane reflection's reflection-missed finding line, on 2026-11-0DAY."""
    return json.dumps(
        {"at": f"2026-11-0{day}T00:00:00Z", "kind": "finding", "source": "reflection",
         "class": "reflection-missed", "question": "reflection-missed", "route": "r",
         "summary": summary}
    ) + "\n"  # fmt: skip


def lane(top: Path, name: str, log: str = "", repo: str = "", *, archived: bool = False) -> None:
    d = top / "lanes" / ("archive" if archived else "")
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{name}.toml").write_text(
        f'issue = "{name}"\nsupervisor = "w9:p2"\ngoal = "scratch"\n'
        + (f'repository = "{repo}"\n' if repo else "")
    )
    (d / f"{name}.handoffs.jsonl").write_text(log)


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
    for n, at in (("gh1", "2026-10-20"), ("gh2", "2026-10-21")):
        lane(top, n, cr(f"{at}T00:00:00Z", f"{n} restated a rule"), archived=True)
    body = (
        "Findings (2):\n- gh1 2026-10-20T00:00:00Z code-review: gh1 restated a rule\n"
        "- gh2 2026-10-21T00:00:00Z code-review: gh2 restated a rule\n"
    )
    for n in (9, 7):
        put(s, HERE, gh_issue(n, DUP, body))
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
    """The demo: an open legacy timestamped reflection-missed issue #5 in the kit's tracker quoting
    the director's old finding; `reflect --director` with a new one, then again with none; then #5
    closed before the next finding."""
    top = reflector(s)
    (top / "director.handoffs.jsonl").write_text(
        '{"at":"2026-11-05T01:02:03Z","kind":"finding","class":"reflection-missed",'
        '"question":"director-reflection-missed","route":"r","summary":"old gap"}\n'
    )
    put(s, KIT, gh_issue(5, LEGACY, OLD))
    new_gap = "owner caught a stale PR after the last reflection; add a stale-PR question"
    reply(
        s,
        "director",
        "class: reflection-missed | question: director-reflection-missed | route: "
        f"reflection/questions.json owner-asked | summary: {new_gap}",
    )
    out = run(s, "reflect", "--director")
    assert issues(s, KIT) == [5], f"filed a new issue: {issues(s, KIT)} {out}"
    (c,) = comments(s, 5, KIT)
    assert f"route reflection/questions.json owner-asked: {new_gap}" in c, c
    assert "- director " in c, c
    assert "running count 2" in c, c
    assert "old gap" not in c, c
    assert new_gap in out, f"comment not printed: {out}"
    reply(s, "director")
    out = run(s, "reflect", "--director")
    assert NONE in out, out
    assert (issues(s, KIT), len(comments(s, 5, KIT))) == ([5], 1), f"wrote again: {out}"
    put(s, KIT, issue(s, 5, KIT) | {"state": "CLOSED", "closedAt": "2026-11-06T00:00:00Z"})
    out = run(s, "reflect", "--director")
    assert issues(s, KIT) == [5, 6], out
    new = issue(s, 6, KIT)
    assert new["title"] == MISSED, new
    assert new_gap in str(new["body"]), new
    assert "Changes: the question list, reflection/questions.json" in str(new["body"]), new
    assert "old gap" in str(new["body"]), new
    assert len(comments(s, 5, KIT)) == 1, "commented on a closed issue"
    assert issues(s) == [], "wrote to another tracker than the kit's"


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
        put(s, KIT, good | bad, 1)
        out = run(s, "reflect", "--director", want=1)
        assert "Traceback" not in out, out
        for want in ("item 1", "is not gh's issue JSON", "update gh, then rerun"):
            assert want in out, (bad, out)
        assert issues(s, KIT) == [1], (bad, issues(s, KIT))
        assert issue(s, 1, KIT) == good | bad, (bad, out)


def two_targets(s: Scratch) -> None:
    """Archived gh1 (tracker owner/target-a) and gh2 (owner/target-b) each logged a
    reflection-missed gap: archiving gh2, each tracker holds one issue, quoting its own lane's."""
    top = reflector(s)
    lane(top, "gh1", gap(1, "gap in target A"), "owner/target-a", archived=True)
    lane(top, "gh2", gap(2, "gap in target B"), "owner/target-b")
    run(s, "archive", "gh2")
    for repo, mine, other in (
        ("owner/target-a", "gap in target A", "gap in target B"),
        ("owner/target-b", "gap in target B", "gap in target A"),
    ):
        assert issues(s, repo) == [1], (repo, issues(s, repo))
        body = str(issue(s, 1, repo)["body"])
        assert mine in body, (repo, body)
        assert other not in body, (repo, body)
    assert issues(s) == [], "wrote to the current directory's tracker"


def one_target(s: Scratch) -> None:
    """Archived gh1 and gh2, one tracker owner/target, each logged a reflection-missed gap no issue
    quotes; the tracker holds an open legacy issue #5: archiving gh2 adds exactly one comment on
    #5, quoting both, and files none."""
    top = reflector(s)
    put(s, "owner/target", gh_issue(5, LEGACY, OLD))
    lane(top, "gh1", gap(1, "first new gap"), "owner/target", archived=True)
    lane(top, "gh2", gap(2, "second new gap"), "owner/target")
    run(s, "archive", "gh2")
    assert issues(s, "owner/target") == [5], issues(s, "owner/target")
    (c,) = comments(s, 5, "owner/target")
    assert "first new gap" in c, c
    assert "second new gap" in c, c
    assert "running count 3" in c, c


def kit_lane(s: Scratch) -> None:
    """A lane of the kit itself (its tracker the director's), its lane and director reflections
    each finding a reflection-missed gap: the kit's tracker holds one issue, quoting both."""
    top = reflector(s)
    lane(top, "gh5", repo=KIT)
    reply(s, "lane", "class: reflection-missed | question: reflection-missed | route: r1 | "
          "summary: lane gap")  # fmt: skip
    reply(s, "director", "class: reflection-missed | question: director-reflection-missed | "
          "route: r2 | summary: director gap")  # fmt: skip
    run(s, "archive", "gh5")
    assert issues(s, KIT) == [1], issues(s, KIT)
    body = str(issue(s, 1, KIT)["body"])
    assert "route r1: lane gap" in body, body
    assert "route r2: director gap" in body, body
    assert comments(s, 1, KIT) == [], "commented on the issue it just filed"


if __name__ == "__main__":
    main(recurrence, reflection_missed, malformed, two_targets, one_target, kit_lane)
