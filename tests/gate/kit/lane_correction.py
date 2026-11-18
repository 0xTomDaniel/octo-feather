"""The scenarios of tests/gate/kit/test_lane_correction.py (its items), this file their command
(testkit.main): the correction lanes the reflection files and comments on (the rule: spec comms
#reflection-correction, issue-lifecycle #lanes-correction; criteria comms
#acceptance-reflect-files-correction, #acceptance-reflect-files-route-owner,
#acceptance-reflect-recurrence-comments, issue-lifecycle #acceptance-reflection-missed-lane,
#acceptance-writer-route-lane) through `octo-feather-lane archive` and `reflect --director`, in
testkit.reflector's world: what counts, when a class is due, refiling, recurrence,
reflection-missed, owner-caught, where each files (the tracker of the repository owning its route,
#1004) and what it quotes, and the `target:` routes refused.

Seams (ticket #937, agreed before any test): (1) the CLI, `octo-feather-lane archive NAME` and
`octo-feather-lane reflect --director` run as commands over a scratch state dir, the real
scripts/pi-role starting agents/reflector.md and the real github-issues scripts; (2) the Pi model
boundary: the testkit's Pi in print mode (testkit/pi_agent.py, its Herdr the testkit's); (3) the
GitHub boundary: the testkit's gh (testkit/gh.py), nothing else standing in: its store, each
tracker its repository's issues and comments, a filed issue also read off the gh request that
filed it (sent): its repo (GH_REPO, as issue-create names the route owner's tracker), title and
body. A target's `repo view` is its store answer, 0xTomDaniel/spec-chat's real gh's recorded one
(testkit/recordings/repo-view.json, read-only: re-created after its lanes started).

Deviations: lifecycle, other_lane, routed and counts replayed real gh's recordings of filing in
0xTomDaniel/spec-chat (the lanes' target) until #1004; under the route-owner rule they file in the
kit's tracker, which no tape recorded, and a tape is never recorded by filing a real issue, so they
run on the store (the tape, testkit/recordings/lane-correction.json, gone with them): the keys are
the store's, the lifecycle's first issue closed by the scenario at the closedAt the tape held, the
classes the fresh names the recordings needed (restated-rule, restated-rule-other, stale-doc,
judged-qc). A reflection-missed finding this run's reflector gives is dated by the run's clock, so
missed_at_once always ran on the store (director ruling, round 3)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import NamedTuple, cast

from testkit import Scratch, kit, main, reflector, reply

L = kit("octo-feather-lane")
TARGET, KIT = "0xTomDaniel/spec-chat", "0xTomDaniel/octo-feather"
HERE = "o/r"  # the tracker of a lane record naming no repository: the current directory's
PRIV = "owner/exo"  # a private target (exosurface-like): none of its lanes' text may reach the kit
STARTED = "2026-11-01T00:00:00Z"  # each scratch lane record's started_at, after PRIV's creation
# gh 2.102.0, 2026-11-18: `gh repo view 0xTomDaniel/spec-chat --json nameWithOwner,createdAt`.
VIEW = Path(__file__).parent / "testkit" / "recordings" / "repo-view.json"
CLOSED_AT = "2026-11-17T21:17:06Z"  # the lifecycle's first issue closed: after gh4's, before gh5's
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


def target_lane(
    top: Path, name: str, *found: str, repo: str = PRIV, archived: bool = False
) -> None:
    """Lane NAME of target REPO started at STARTED, its log FOUND."""
    lane(top, name, *found, repo=repo, archived=archived)
    d = top / "lanes" / ("archive" if archived else "")
    with (d / f"{name}.toml").open("a") as f:
        f.write(f'started_at = "{STARTED}"\n')


def created(s: Scratch, repo: str, at: str, now: str = "") -> None:
    """REPO's `gh repo view --json nameWithOwner,createdAt`: created AT, named NOW (else REPO)."""
    s.gh.store(f"api/repos/{repo}.json", {"nameWithOwner": now or repo, "createdAt": at})


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


# The issues filed, read off the gh requests that filed them.
class Sent(NamedTuple):
    repo: str
    title: str
    body: str


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
    restated-rule finding, target lane gh2's review the second, the director reflection routes
    the class to a kit role: archive gh2 files it in the kit's tracker (the route's owner, never
    gh2's target), quoting gh1's finding, gh2's by lane, date and class, and the route, the key
    printed. Its issue closed after the class's latest finding: nothing; closed before a newer
    one: files again (an open one, a new finding: recurrence)."""
    top = reflector(s)
    cls, route = "restated-rule", "agents/implementer.md Rules"
    gh12 = ("gh1 restated the merge rule", "gh2 restated the gate rule")
    lane(top, "gh1", cr("2026-10-20T00:00:00Z", cls, gh12[0]), repo=KIT, archived=True)
    lane(top, "gh2", cr("2026-10-21T00:00:00Z", cls, gh12[1]), repo=TARGET)
    why = "summary: 2 code-review findings in gh1, gh2"
    reply(s, "director", f"class: {cls} | question: writer-route | route: {route} | {why}")
    out = run(s, "archive", "gh2").splitlines()
    assert filed("1", KIT, cls, two(route)) in out, f"archive gh2: {out}"
    assert (top / "lanes" / "archive" / "gh2.toml").is_file(), f"gh2 not archived: {out}"
    (i,) = sent(s)
    gh2 = f"- gh2 2026-10-21T00:00:00Z {cls}"
    quotes(i, KIT, cls, f"Class: {cls}", f"Route: {route}", gh12[0], gh2)
    assert gh12[1] not in i.body, f"quoted a target lane's summary: {i.body}"
    assert "question list" not in i.body, i.body
    assert (issues(s, TARGET), issues(s)) == ([], []), "filed in a contributing lane's tracker"

    reply(s, "director")
    lane(top, "gh4", cr("2026-10-23T00:00:00Z", cls, "gh4 again"), repo=KIT)
    put(s, KIT, issue(s, 1, KIT) | {"state": "CLOSED", "closedAt": CLOSED_AT})
    out = run(s, "archive", "gh4").splitlines()
    assert len(sent(s)) == 1, f"closed after the latest finding: filed again: {out}"
    lane(top, "gh5", cr(GH5_AT, cls, "gh5 after the close"), repo=KIT)
    out = run(s, "archive", "gh5").splitlines()
    want = filed("2", KIT, cls)
    assert any(x.startswith(want) for x in out), f"closed before the latest finding: {out}"


def other_lane(s: Scratch) -> None:
    """Every due class files, whichever lane's reflection runs: archived gh1 and gh2 hold one
    restated-rule-other finding each, the archive of unrelated gh3 files the class in the kit's
    tracker (no route: the kit's) quoting both; a further archive files nothing."""
    top = reflector(s)
    cls = "restated-rule-other"
    gh12 = ("gh1 restated the merge rule", "gh2 restated the gate rule")
    for n, (name, summary) in enumerate(zip(("gh1", "gh2"), gh12, strict=True)):
        at = f"2026-10-2{n}T00:00:00Z"
        lane(top, name, cr(at, cls, summary), repo=KIT, archived=True)
    lane(top, "gh3", repo=KIT)
    out = run(s, "archive", "gh3").splitlines()
    want = filed("1", KIT, cls, two("none given by a reflection"))
    assert want in out, f"other lane: due class not filed: {out}"
    assert (top / "lanes" / "archive" / "gh3.toml").is_file(), (
        f"other lane: gh3 not archived: {out}"
    )
    (i,) = sent(s)
    quotes(i, KIT, cls, *gh12)
    lane(top, "gh4", repo=KIT)
    out = run(s, "archive", "gh4").splitlines()
    assert NONE in out, f"other lane: refiled: {out}"
    assert len(sent(s)) == 1, f"other lane: refiled: {sent(s)}"


def routed(s: Scratch) -> None:
    """#acceptance-writer-route-lane through reflect --director: the class's findings in lanes,
    the director routes it: filed in the kit's tracker naming the route."""
    top = reflector(s)
    cls, route = "stale-doc", "agents/code-reviewer.md Rules"
    for n, name in enumerate(("gh1", "gh2")):
        at, summary = f"2026-10-2{n}T00:00:00Z", f"{name} check missed a stale doc"
        lane(top, name, cr(at, cls, summary), repo=KIT, archived=True)
    why = "summary: 2 code-review findings in gh1, gh2"
    reply(s, "director", f"class: {cls} | question: writer-route | route: {route} | {why}")
    out = run(s, "reflect", "--director").splitlines()
    assert filed("1", KIT, cls, two(route)) in out, f"routed: {out}"
    (i,) = sent(s)
    quotes(i, KIT, cls, f"Route: {route}")


def counts(s: Scratch) -> None:
    """What counts: two reflection findings of a class in two lanes, two blocking ones in one
    lane, a non-blocking review finding beside a blocking one, or the director log's: none due; a
    blocking product-judge (qc) finding counts."""
    top = reflector(s)
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
    out = run(s, "archive", "gh3").splitlines()
    want = filed("1", KIT, "judged-qc", "(2 findings; ")
    assert any(x.startswith(want) for x in out), f"counts: want judged-qc filed: {out}"
    assert len(sent(s)) == 1, f"counts: want only judged-qc filed: {sent(s)}"


def missed_at_once(s: Scratch) -> None:
    """#acceptance-reflection-missed-lane, on the store (the docstring's amendment): archiving gh6,
    this run's lane reflector and director reflector each give a reflection-missed finding: both
    file at once in the kit's tracker (every reflection-missed finding's), not gh6's target, one
    issue titled MISSED naming the question list, quoting the director's finding and gh6's by
    lane, date and class only; owner-caught findings twice in the director log file nothing. The
    director reflection again, no new finding: nothing filed or commented."""
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
    reply(s, "lane")
    reply(s, "director")
    out = run(s, "reflect", "--director").splitlines()
    assert NONE in out, f"refiled: {out}"
    assert (issues(s, KIT), comments(s, 1, KIT)) == ([1], []), f"wrote again: {out}"


def recurrence(s: Scratch) -> None:
    """Kit lanes gh1, gh2 each logged a duplicated-rule finding its open issue #7 in the kit's
    tracker (the route owner: no route) quotes (#9 open too, newer); private target lane gh3's
    review logs a third, then gh4 archives with none: the criterion's outcome, on #7, the oldest
    open, gh3's finding by lane, date and class only; the running count 3; no other tracker."""
    top = reflector(s)
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
    out = run(s, "archive", "gh3")
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
    out = run(s, "archive", "gh4")
    assert NONE in out, out
    assert (issues(s, KIT), len(comments(s, 7, KIT))) == ([7, 9], 1), f"commented again: {out}"


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
    """Archived gh1 (owner/target-a) and gh2 (owner/target-b) each logged a reflection-missed
    gap: archiving gh2, the kit's tracker (every reflection-missed finding's) holds one issue,
    quoting each by lane, date and class only; neither target's tracker holds one."""
    top = reflector(s)
    lane(top, "gh1", gap(1, "gap in target A"), repo="owner/target-a", archived=True)
    lane(top, "gh2", gap(2, "gap in target B"), repo="owner/target-b")
    run(s, "archive", "gh2")
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


def one_target(s: Scratch) -> None:
    """Archived gh1 and gh2, both of owner/target, each logged a reflection-missed gap no issue
    quotes; the kit's tracker holds an open legacy issue #5: archiving gh2 adds exactly one
    comment on #5, quoting both by lane, date and class only, files none, and writes nothing in
    owner/target's tracker; archiving gh3 then adds nothing."""
    top = reflector(s)
    put(s, KIT, gh_issue(5, LEGACY, OLD))
    lane(top, "gh1", gap(1, "first new gap"), repo="owner/target", archived=True)
    lane(top, "gh2", gap(2, "second new gap"), repo="owner/target")
    run(s, "archive", "gh2")
    assert (issues(s, KIT), issues(s, "owner/target")) == ([5], []), issues(s, KIT)
    (c,) = comments(s, 5, KIT)
    assert "- gh1 2026-11-01T00:00:00Z reflection-missed\n" in c, c
    assert c.endswith("- gh2 2026-11-02T00:00:00Z reflection-missed"), c
    assert "new gap" not in c, c
    assert "running count 3" in c, c
    lane(top, "gh3", repo="owner/target")
    run(s, "archive", "gh3")
    assert len(comments(s, 5, KIT)) == 1, comments(s, 5, KIT)


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


def route_owner(s: Scratch) -> None:
    """#acceptance-reflect-files-route-owner, the #850 regression: blocking findings of kit-skill
    in kit lane gh1 and private target lane x1 (x1's reflection routing it, untagged, in its own
    words), the director routing it to a kit skill; of target-only in x1, x2 and kit lane gh1,
    x2's lane reflection routing it `target:`; of own-only in kit lanes gh0 and gh1 alone, x2's
    reflection routing it `target:` too. Archiving x2 files kit-skill only in the kit's tracker,
    quoting x1's finding by lane, date and class alone and naming only the director's route;
    target-only only in PRIV's, quoting only x1's, x2's and x2's routing reflection finding;
    own-only only in PRIV's, quoting x2's routing reflection finding (never zero findings);
    nothing in the current directory's tracker. The demo: the `filed` lines."""
    top = reflector(s)
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
    reply(s, "lane", "class: target-only | question: undetected-rule | "
          "route: target: src/exo/rules.py | summary: x2 found its own rule unchecked",
          "class: own-only | question: undetected-rule | "
          "route: target: src/exo/own.py | summary: x2 own-only reflection")  # fmt: skip
    route = ".agents/skills/tdd/SKILL.md Seams"
    reply(s, "director", f"class: kit-skill | question: writer-route | route: {route} | "
          "summary: 2 code-review findings in gh1, x1")  # fmt: skip
    out = run(s, "archive", "x2").splitlines()
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


def refusal(s: Scratch) -> None:
    """A `target:` route whose lane record's repository was re-created after the lane started
    (0xTomDaniel/spec-chat, gh's recorded answer), renamed, or not named: archive refuses naming
    the record to fix, nothing filed in any tracker, the lane not archived. A director reflection
    giving a `target:` route is refused, nothing appended."""
    top = reflector(s)
    (rec,) = json.loads(VIEW.read_text())
    s.gh.store(f"api/repos/{TARGET}.json", json.loads(rec["out"]))
    created(s, "owner/old", "2026-10-01T00:00:00Z", "owner/new")
    created(s, PRIV, "2026-10-01T00:00:00Z")
    target_lane(top, "s1", cr("2026-11-02T00:00:00Z", "own-rule", "s1 a"), archived=True)
    target_lane(top, "s2", cr("2026-11-03T00:00:00Z", "own-rule", "s2 b"))
    reply(s, "lane", "class: own-rule | question: undetected-rule | route: target: src/rule.py | "
          "summary: s2 own rule")  # fmt: skip
    for name, repo, why in (
        ("s2", TARGET, "created 2026-11-13T03:20:54Z, after the lane started"),
        ("s2", "owner/old", "is now owner/new"),
        ("s2", "", "names no repository"),
    ):
        target_lane(top, name, cr("2026-11-03T00:00:00Z", "own-rule", "s2 b"), repo=repo)
        out = run(s, "archive", "s2", want=1)
        assert str(top / "lanes" / "s2.toml") in out, (repo, out)
        assert why in out, (repo, out)
        assert (top / "lanes" / "s2.toml").is_file(), (repo, out)
        for r in (KIT, PRIV, TARGET, "owner/old", "owner/new", HERE):
            assert issues(s, r) == [], (repo, r, out)
    reply(s, "lane")
    reply(s, "director", "class: own-rule | question: writer-route | route: target: src/x.py | "
          "summary: director routes a target")  # fmt: skip
    out = run(s, "reflect", "--director", want=1)
    assert "a director reflection's route is never `target:`" in out, out
    assert not (top / "director.handoffs.jsonl").exists(), out


if __name__ == "__main__":
    main(
        route_owner,
        refusal,
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
