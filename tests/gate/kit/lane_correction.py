"""The scenarios of tests/gate/kit/test_lane_correction.py (its items), this file their command
(testkit.main): a recurrence of a class whose correction-lane issue is open (spec comms
#reflection-correction, #acceptance-reflect-recurrence-comments; issue-lifecycle
#acceptance-reflection-missed-lane) through `octo-feather-lane archive` and `reflect --director`,
in testkit.reflector's world, the tracker the testkit gh's store (issue/N.json, its comments)."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from testkit import Scratch, kit, main, reflector, reply

if TYPE_CHECKING:
    from pathlib import Path

L = kit("octo-feather-lane")
DUP = "[correction-lane duplicated-rule] repeated finding class: duplicated-rule"
LEGACY = (
    "[correction-lane reflection-missed 2026-11-05T01:02:03Z abcd1234] change the question list:"
    " reflection-missed"
)
OLD = "- director 2026-11-05T01:02:03Z director (director-reflection-missed), route r: old gap"
NONE = "correction lanes: none filed or commented"


def cr(at: str, summary: str) -> str:
    d = {"at": at, "kind": "finding", "source": "code-review", "class": "duplicated-rule"}
    return json.dumps(d | {"blocking": True, "summary": summary}) + "\n"


def lane(top: Path, name: str, log: str = "") -> None:
    (top / "lanes" / f"{name}.toml").write_text(
        f'issue = "{name}"\nsupervisor = "w9:p2"\ngoal = "scratch"\n'
    )
    (top / "lanes" / f"{name}.handoffs.jsonl").write_text(log)


def issue(s: Scratch, n: int) -> dict[str, object]:
    return json.loads((s.gh.dir / "issue" / f"{n}.json").read_text())


def issues(s: Scratch) -> list[int]:
    return sorted(int(p.stem) for p in (s.gh.dir / "issue").glob("*.json"))


def comments(s: Scratch, n: int) -> list[str]:
    return [str(c["body"]) for c in issue(s, n).get("comments") or []]  # type: ignore[union-attr]


def run(s: Scratch, *args: str, want: int = 0) -> str:
    r = s.run([L, *args], want=want)
    return f"{r.out}\n{r.err}"


def recurrence(s: Scratch) -> None:
    """Archived gh1, gh2 each logged a duplicated-rule finding its open issue #7 quotes (#9 open
    too, newer): archiving gh3, whose review logged a third, files nothing and adds one comment to
    #7 quoting only gh3's, its date and the running count 3, printed; archiving gh4, no new
    finding, comments nothing."""
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
        s.gh.store(f"issue/{n}.json", {"number": n, "title": DUP, "state": "OPEN", "body": body})
    lane(top, "gh3", cr("2026-10-22T00:00:00Z", "gh3 restated it again"))
    out = run(s, "archive", "gh3")
    assert issues(s) == [7, 9], f"filed a new issue: {issues(s)} {out}"
    assert comments(s, 9) == [], "commented on the newer open issue"
    (c,) = comments(s, 7)
    assert "- gh3 2026-10-22T00:00:00Z code-review: gh3 restated it again" in c, c
    assert "running count 3" in c, c
    assert "gh1 restated" not in c and "gh2 restated" not in c, f"quoted an old finding: {c}"
    assert "correction lane: commented https://github.com/o/r/issues/7#issuecomment-1001" in out
    assert "gh3 restated it again" in out, f"comment not printed: {out}"
    lane(top, "gh4")
    out = run(s, "archive", "gh4")
    assert NONE in out, out
    assert (issues(s), len(comments(s, 7))) == ([7, 9], 1), f"commented again: {out}"


def reflection_missed(s: Scratch) -> None:
    """The demo: an open legacy timestamped reflection-missed issue #5 quoting the director's old
    finding; `reflect --director` finding a new one comments on #5 (the kit's tracker) and prints
    it; run again with no new finding, it prints none filed or commented. With #5 closed before
    the next finding, one files a new issue, never on a closed one; then malformed comments JSON
    refuses with a fix, no traceback."""
    top = reflector(s)
    (top / "director.handoffs.jsonl").write_text(
        '{"at":"2026-11-05T01:02:03Z","kind":"finding","class":"reflection-missed",'
        '"question":"director-reflection-missed","route":"r","summary":"old gap"}\n'
    )
    s.gh.store("issue/5.json", {"number": 5, "title": LEGACY, "state": "OPEN", "body": OLD})
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
    assert f"route reflection/questions.json owner-asked: {gap}" in c and "- director " in c, c
    assert "running count 2" in c and "old gap" not in c, c
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
    assert gap in str(new["body"]) and "old gap" in str(new["body"]), new
    assert len(comments(s, 5)) == 1, "commented on a closed issue"
    s.gh.store("issue/6.json", new | {"comments": "not a list"})
    out = run(s, "reflect", "--director", want=1)
    assert "Traceback" not in out, out
    assert "#6" in out and "comments" in out and "rerun" in out, out


if __name__ == "__main__":
    main(recurrence, reflection_missed)
