"""The scenarios of tests/gate/kit/test_lane_correction.py (its items), this file their command
(testkit.main): the correction lanes the reflection files and comments on (the rule: spec comms
#reflection-correction, issue-lifecycle #lanes-correction; criteria comms
#acceptance-reflect-files-correction, #acceptance-reflect-recurrence-comments, issue-lifecycle
#acceptance-reflection-missed-lane, #acceptance-writer-route-lane) through `octo-feather-lane
archive` and `reflect --director`, in testkit.reflector's world: what counts, when a class is due,
refiling, recurrence, reflection-missed, owner-caught, where each files and what it quotes.

Seams (ticket #937, agreed before any test): (1) the CLI, `octo-feather-lane archive NAME` and
`octo-feather-lane reflect --director` run as commands over a scratch state dir, the real
scripts/pi-role starting agents/reflector.md and the real github-issues scripts; (2) the Pi model
boundary: the testkit's Pi in print mode (testkit/pi_agent.py, its Herdr the testkit's); (3) the
GitHub boundary: the testkit's gh (testkit/gh.py), nothing else standing in. Seam 3 has two forms.
The taped scenarios (lifecycle, other_lane, routed, counts) replay only real gh's recorded answers
(testkit/recordings/lane-correction.json, one tape per scenario; a request with no recording
fails), a filed issue read off the gh request that filed it (sent): its repo (GH_REPO, as
issue-create names the lane's target), title and body. The others run on the gh's store, each
tracker its repository's issues and comments. Amendment (director ruling, round 3): a
reflection-missed finding this run's reflector gives is dated by the run's clock, and the issue it
files quotes that date in its body, so no recorded request matches a later run; that scenario
(missed_at_once) and #962's own run on the store.

Deviations of the taped scenarios from tests/lane-correction.sh, each forced by real GitHub (the
facts kept): the lanes' target o/t is 0xTomDaniel/spec-chat; the keys filed are the real ones
(FILED); an issue is closed once, at its real closedAt (gh5's finding dated after it, gh4's before
it, where the old test closed it twice at chosen dates); the classes are fresh names (dup-rule
restated-rule, other lane's restated-rule-other, stale-check stale-doc, judged judged-qc), as
every scenario files in one real tracker that keeps earlier recordings' closed issues of the old
names, their closedAt after these findings. Rerecording needs fresh class names again."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import NamedTuple, cast

from testkit import Scratch, kit, main, reflector, reply

L = kit("octo-feather-lane")
TARGET, KIT = "0xTomDaniel/spec-chat", "0xTomDaniel/octo-feather"
HERE = "o/r"  # the tracker of a lane record naming no repository: the current directory's
# gh 2.102.0, 2026-11-17 (each recording's source): one run of each taped scenario against
# TARGET, every issue it filed closed after it; the lifecycle's first closed by hand between gh2's
# and gh4's archives (its closedAt in the tape).
TAPE = Path(__file__).parent / "testkit" / "recordings" / "lane-correction.json"
# The keys each taped scenario's run filed, in order.
FILED = {
    "lifecycle": ["12", "13"],
    "other_lane": ["14"],
    "routed": ["15"],
    "counts": ["16"],
}
GH5_AT = "2026-11-20T00:00:00Z"  # after the lifecycle's first issue closed
DUP = "[correction-lane duplicated-rule] repeated finding class: duplicated-rule"
MISSED = "[correction-lane reflection-missed] change the question list: reflection-missed"
LEGACY = (
    "[correction-lane reflection-missed 2026-11-05T01:02:03Z abcd1234] change the question list:"
    " reflection-missed"
)
OLD = "- director 2026-11-05T01:02:03Z director (director-reflection-missed), route r: old gap"
NONE = "correction lanes: none filed or commented"
CHANGES = "Changes: the question list, reflection/questions.json"
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


def gap(day: int, summary: str) -> str:
    """A lane reflection's reflection-missed finding, on 2026-11-0DAY."""
    at = f"2026-11-0{day}T00:00:00Z"
    return rf(at, "reflection-missed", summary, question="reflection-missed", route="r")


def lane(top: Path, name: str, *findings: str, repo: str = "", archived: bool = False) -> None:
    """Lane NAME on REPO (none: the current directory's), its log FINDINGS; ARCHIVED: archived."""
    d = top / "lanes" / ("archive" if archived else "")
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{name}.toml").write_text(
        f'issue = "{name}"\nsupervisor = "w9:p2"\ngoal = "scratch"\n'
        + (f'repository = "{repo}"\n' if repo else "")
    )
    (d / f"{name}.handoffs.jsonl").write_text("".join(f"{x}\n" for x in findings))


def director(top: Path, *findings: str) -> None:
    """FINDINGS appended to the director log."""
    with (top / "director.handoffs.jsonl").open("a") as f:
        f.write("".join(f"{x}\n" for x in findings))


def run(s: Scratch, *args: str, want: int = 0) -> str:
    """`octo-feather-lane ARGS`'s output, also printed: the scenario's demo for qc."""
    r = s.run([L, *args], want=want)
    out = f"{r.out}\n{r.err}"
    print(f"$ octo-feather-lane {' '.join(args)}\n{out.strip()}\n", flush=True)  # noqa: T201
    return out


# The store form: each tracker the gh's store of that repository's issues and comments.
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


# The taped form: real gh's recorded answers, the issues filed read off their requests.
class Sent(NamedTuple):
    repo: str
    title: str
    body: str


def taped(s: Scratch, scenario: str) -> Path:
    """S's reflection world, the gh replaying SCENARIO's tape; its state dir's octo-feather dir."""
    s.gh.store("tape.json", json.loads(TAPE.read_text())[scenario])
    return reflector(s)


def sent(s: Scratch) -> list[Sent]:
    """Every issue filed so far, read off its gh request."""
    got = [CREATE.fullmatch(x) for x in s.gh.log()]
    return [Sent(m[1], m[2], json.loads(m[3])) for m in got if m]


def quotes(i: Sent, repo: str, marker: str, *want: str) -> None:
    """I filed in REPO, its title holding MARKER, its body WANT."""
    assert i.repo == repo, i
    assert f"[correction-lane {marker}]" in i.title, i
    for q in want:
        assert q in i.body, (q, i.body)


def filed(key: str, repo: str, cls: str, rest: str = "") -> str:
    """The line (its start, without REST) printing KEY filed."""
    return f"correction lane: filed {key} in github-issues {repo} for {cls} {rest}"


def two(route: str) -> str:
    return f"(2 findings; route: {route})"


def lifecycle(s: Scratch) -> None:
    """#acceptance-reflect-files-correction, #acceptance-writer-route-lane: archived gh1 logged one
    restated-rule finding, gh2's review the second, the director reflection routes the class:
    archive gh2 files it in gh2's target, quoting both and the route, the key printed. Its issue
    closed after the class's latest finding: nothing; closed before a newer one: files again (an
    open one, a new finding: recurrence)."""
    top, keys = taped(s, "lifecycle"), FILED["lifecycle"]
    cls, route = "restated-rule", "agents/implementer.md Rules"
    gh12 = ("gh1 restated the merge rule", "gh2 restated the gate rule")
    (top / "lanes" / "archive").mkdir(parents=True)
    (top / "lanes" / "archive" / "gh1.handoffs.jsonl").write_text(
        cr("2026-10-20T00:00:00Z", cls, gh12[0]) + "\n"
    )
    lane(top, "gh2", cr("2026-10-21T00:00:00Z", cls, gh12[1]), repo=TARGET)
    why = "summary: 2 code-review findings in gh1, gh2"
    reply(s, "director", f"class: {cls} | question: writer-route | route: {route} | {why}")
    out = run(s, "archive", "gh2").splitlines()
    assert filed(keys[0], TARGET, cls, two(route)) in out, f"archive gh2: {out}"
    assert (top / "lanes" / "archive" / "gh2.toml").is_file(), f"gh2 not archived: {out}"
    (i,) = sent(s)
    quotes(i, TARGET, cls, f"Class: {cls}", f"Route: {route}", *gh12)
    assert "question list" not in i.body, i.body

    reply(s, "director")
    # Recorded: the issue closed here, after gh4's finding and before gh5's.
    lane(top, "gh4", cr("2026-10-23T00:00:00Z", cls, "gh4 again"), repo=TARGET)
    out = run(s, "archive", "gh4").splitlines()
    assert len(sent(s)) == 1, f"closed after the latest finding: filed again: {out}"
    lane(top, "gh5", cr(GH5_AT, cls, "gh5 after the close"), repo=TARGET)
    out = run(s, "archive", "gh5").splitlines()
    want = filed(keys[1], TARGET, cls)
    assert any(x.startswith(want) for x in out), f"closed before the latest finding: {out}"


def other_lane(s: Scratch) -> None:
    """Every due class files, whichever lane's reflection runs: archived gh1 and gh2 hold one
    restated-rule-other finding each, the archive of unrelated gh3 files the class in gh1/gh2's
    target quoting both; a further archive files nothing."""
    top, (key,) = taped(s, "other_lane"), FILED["other_lane"]
    cls = "restated-rule-other"
    gh12 = ("gh1 restated the merge rule", "gh2 restated the gate rule")
    for n, (name, summary) in enumerate(zip(("gh1", "gh2"), gh12, strict=True)):
        at = f"2026-10-2{n}T00:00:00Z"
        lane(top, name, cr(at, cls, summary), repo=TARGET, archived=True)
    lane(top, "gh3", repo=TARGET)
    out = run(s, "archive", "gh3").splitlines()
    want = filed(key, TARGET, cls, two("none given by a reflection"))
    assert want in out, f"other lane: due class not filed: {out}"
    assert (top / "lanes" / "archive" / "gh3.toml").is_file(), (
        f"other lane: gh3 not archived: {out}"
    )
    (i,) = sent(s)
    quotes(i, TARGET, cls, *gh12)
    lane(top, "gh4", repo=TARGET)
    out = run(s, "archive", "gh4").splitlines()
    assert NONE in out, f"other lane: refiled: {out}"
    assert len(sent(s)) == 1, f"other lane: refiled: {sent(s)}"


def routed(s: Scratch) -> None:
    """#acceptance-writer-route-lane through reflect --director: the class's findings in lanes,
    the director routes it: filed in their target naming the route."""
    top, (key,) = taped(s, "routed"), FILED["routed"]
    cls, route = "stale-doc", "agents/code-reviewer.md Rules"
    for n, name in enumerate(("gh1", "gh2")):
        at, summary = f"2026-10-2{n}T00:00:00Z", f"{name} check missed a stale doc"
        lane(top, name, cr(at, cls, summary), repo=TARGET, archived=True)
    why = "summary: 2 code-review findings in gh1, gh2"
    reply(s, "director", f"class: {cls} | question: writer-route | route: {route} | {why}")
    out = run(s, "reflect", "--director").splitlines()
    assert filed(key, TARGET, cls, two(route)) in out, f"routed: {out}"
    (i,) = sent(s)
    quotes(i, TARGET, cls, f"Route: {route}")


def counts(s: Scratch) -> None:
    """What counts: two reflection findings of a class in two lanes, two blocking ones in one
    lane, a non-blocking review finding beside a blocking one, or the director log's: none due; a
    blocking product-judge (qc) finding counts."""
    top, (key,) = taped(s, "counts"), FILED["counts"]
    q = {"blocking": False, "question": "undetected-rule", "route": "r"}
    lane(
        top,
        "gh1",
        rf("2026-10-20T00:00:00Z", "refl-only", "gh1 reflection", **q),
        cr("2026-10-20T00:00:00Z", "one-lane", "gh1 a"),
        cr("2026-10-20T01:00:00Z", "one-lane", "gh1 b"),
        cr("2026-10-20T02:00:00Z", "judged-qc", "gh1 review"),
        repo=TARGET,
        archived=True,
    )
    lane(
        top,
        "gh2",
        rf("2026-10-21T00:00:00Z", "refl-only", "gh2 reflection", **q),
        cr("2026-10-21T01:00:00Z", "one-lane", "gh2 note", blocking=False),
        cr("2026-10-21T02:00:00Z", "judged-qc", "gh2 judge", "qc"),
        repo=TARGET,
        archived=True,
    )
    director(top, finding("2026-10-22T00:00:00Z", "one-lane", "director saw it"))
    lane(top, "gh3", repo=TARGET)
    out = run(s, "archive", "gh3").splitlines()
    want = filed(key, TARGET, "judged-qc", "(2 findings; ")
    assert any(x.startswith(want) for x in out), f"counts: want judged-qc filed: {out}"
    assert len(sent(s)) == 1, f"counts: want only judged-qc filed: {sent(s)}"


def missed_at_once(s: Scratch) -> None:
    """#acceptance-reflection-missed-lane, on the store (the docstring's amendment): archiving gh6,
    this run's lane reflector and director reflector each give a reflection-missed finding; the
    lane's files at once in gh6's target, the director's in the kit's tracker, each titled
    MISSED, naming the question list and quoting its own finding, not the other's; owner-caught
    findings twice in the director log file nothing. The director reflection again, no new
    finding: nothing filed or commented."""
    top = reflector(s)
    caught = "owner-caught-stale-pr"
    director(
        top,
        finding("2026-10-25T00:00:00Z", caught, "a"),
        finding("2026-10-25T01:00:00Z", caught, "b"),
    )
    lane(top, "gh6", repo=TARGET)
    mine = "gh1 reflection found no gap; gh6 review found the rule broken; reword undetected-rule"
    theirs = "owner caught a stale PR after the last reflection; add a stale-PR question"
    reply(s, "lane", "class: reflection-missed | question: reflection-missed | route: "
          f"reflection/questions.json undetected-rule | summary: {mine}")  # fmt: skip
    reply(s, "director", "class: reflection-missed | question: director-reflection-missed | "
          f"route: reflection/questions.json owner-asked | summary: {theirs}")  # fmt: skip
    out = run(s, "archive", "gh6").splitlines()
    for repo, own, other in ((TARGET, mine, theirs), (KIT, theirs, mine)):
        want = filed("1", repo, "reflection-missed", "(1 finding; ")
        assert any(x.startswith(want) for x in out), f"not filed in {repo}: {out}"
        assert issues(s, repo) == [1], (repo, issues(s, repo))
        d = issue(s, 1, repo)
        assert d["title"] == MISSED, d
        for q in (CHANGES, own):
            assert q in str(d["body"]), (repo, q, d)
        assert other not in str(d["body"]), (repo, d)
    assert issues(s) == [], "wrote to the current directory's tracker"
    reply(s, "lane")
    reply(s, "director")
    out = run(s, "reflect", "--director").splitlines()
    assert NONE in out, f"refiled: {out}"
    for repo in (TARGET, KIT):
        assert (issues(s, repo), comments(s, 1, repo)) == ([1], []), f"wrote again: {out}"


def recurrence(s: Scratch) -> None:
    """Archived gh1, gh2 each logged a duplicated-rule finding its open issue #7 quotes (#9 open
    too, newer); gh3's review logs a third, then gh4 archives with none: the criterion's outcome,
    on #7, the oldest open; the running count 3."""
    top = reflector(s)
    for n, at in (("gh1", "2026-10-20"), ("gh2", "2026-10-21")):
        summary = f"{n} restated a rule"
        lane(top, n, cr(f"{at}T00:00:00Z", "duplicated-rule", summary), archived=True)
    body = (
        "Findings (2):\n- gh1 2026-10-20T00:00:00Z code-review: gh1 restated a rule\n"
        "- gh2 2026-10-21T00:00:00Z code-review: gh2 restated a rule\n"
    )
    for n in (9, 7):
        put(s, HERE, gh_issue(n, DUP, body))
    lane(top, "gh3", cr("2026-10-22T00:00:00Z", "duplicated-rule", "gh3 restated it again"))
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
    assert CHANGES in str(new["body"]), new
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
    lane(top, "gh1", gap(1, "gap in target A"), repo="owner/target-a", archived=True)
    lane(top, "gh2", gap(2, "gap in target B"), repo="owner/target-b")
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
    lane(top, "gh1", gap(1, "first new gap"), repo="owner/target", archived=True)
    lane(top, "gh2", gap(2, "second new gap"), repo="owner/target")
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
    main(
        lifecycle,
        other_lane,
        routed,
        counts,
        missed_at_once,
        recurrence,
        reflection_missed,
        malformed,
        two_targets,
        one_target,
        kit_lane,
    )
