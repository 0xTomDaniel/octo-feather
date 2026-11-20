"""The scenarios of tests/gate/kit/test_lane_correction.py (its items), this file their command
(testkit.main): the wiring of the correction filer (scripts/correction_lanes.py) into
`octo-feather-lane archive`, `reflect NAME` and `reflect --director`, in testkit.reflector's
world: each reaches the filer after its reflections, prints its lines and refuses through it (the
rule: spec comms #reflection-correction, issue-lifecycle #lanes-correction). The filer's own rules,
what counts and files where, quoting what: test_lane_correction_filer.py, in-process at its
interface, on this file's helpers below.

Seams (ticket #937, agreed before any test): (1) the CLI, `octo-feather-lane archive NAME` and
`octo-feather-lane reflect` run as commands over a scratch state dir, the real scripts/pi-role
starting agents/reflector.md and the real github-issues scripts; (2) the Pi model boundary: the
testkit's Pi in print mode (testkit/pi_agent.py, its Herdr the testkit's); (3) the GitHub
boundary: the testkit's gh (testkit/gh.py), nothing else standing in: its store, each tracker its
repository's issues and comments, a filed issue also read off the gh request that filed it
(sent): its repo (GH_REPO, as issue-create names the route owner's tracker), title and body. A
target's `repo view` is its store answer, 0xTomDaniel/spec-chat's real gh's recorded one
(testkit/recordings/repo-view.json, read-only: re-created after its lanes started). The kit's
tracker in recorded_372 is real gh's recorded read-only answers loaded into the store
(testkit/recordings/reflection-missed-372.json)."""

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
# gh 2.102.0, 2026-11-19, read-only: comment 6997429551 on #372 and the reflection-missed issues
# quoting its findings, as before it (trimmed: the recording's source).
TAPE372 = Path(__file__).parent / "testkit" / "recordings" / "reflection-missed-372.json"
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


def archive(s: Scratch) -> None:
    """`archive` reaches the filer after both reflections: archived gh1 and target lane gh2 logged
    one restated-rule finding each, the director reflection routes the class: archive gh2 prints
    the filed line, the issue naming the director's route, then archives gh2. A `target:` route
    whose record names no repository: the filer's refusal refuses the archive, exit 1, naming the
    record, nothing filed, s2 not archived."""
    top = reflector(s)
    cls, route = "restated-rule", "agents/implementer.md Rules"
    lane(top, "gh1", cr("2026-10-20T00:00:00Z", cls, "gh1 restated"), repo=KIT, archived=True)
    lane(top, "gh2", cr("2026-10-21T00:00:00Z", cls, "gh2 restated"), repo=TARGET)
    why = "summary: 2 code-review findings in gh1, gh2"
    reply(s, "director", f"class: {cls} | question: writer-route | route: {route} | {why}")
    out = run(s, "archive", "gh2").splitlines()
    assert filed("1", KIT, cls, two(route)) in out, f"archive gh2: {out}"
    assert (top / "lanes" / "archive" / "gh2.toml").is_file(), f"gh2 not archived: {out}"
    (i,) = sent(s)
    quotes(i, KIT, cls, f"Route: {route}")
    reply(s, "director")
    target_lane(top, "s1", cr("2026-11-02T00:00:00Z", "own-rule", "s1 a"), archived=True)
    target_lane(top, "s2", cr("2026-11-03T00:00:00Z", "own-rule", "s2 b"), repo="")
    reply(s, "lane", "class: own-rule | question: undetected-rule | route: target: src/rule.py | "
          "summary: s2 own rule")  # fmt: skip
    out = run(s, "archive", "s2", want=1)
    assert str(top / "lanes" / "s2.toml") in out, out
    assert "names no repository" in out, out
    assert (top / "lanes" / "s2.toml").is_file(), out
    assert len(sent(s)) == 1, f"filed on a refusal: {sent(s)}"


def reflect(s: Scratch) -> None:
    """`reflect --director` and `reflect NAME` reach the filer after their reflection and print
    its lines: the director's new reflection-missed gap and then lane gh7's each a comment on the
    kit's open legacy issue #5, printed; with nothing new, `correction lanes: none filed or
    commented`. gh's issue list printing #5 out of its form: `reflect --director` refuses through
    the filer, exit 1, naming it, no traceback. A director reflection giving a `target:` route is
    refused, nothing appended."""
    top = reflector(s)
    dlog = top / "director.handoffs.jsonl"
    dlog.write_text(
        '{"at":"2026-11-05T01:02:03Z","kind":"finding","class":"reflection-missed",'
        '"question":"director-reflection-missed","route":"r","summary":"old gap"}\n'
    )
    put(s, KIT, gh_issue(5, LEGACY, OLD))
    new_gap = "owner caught a stale PR after the last reflection; add a stale-PR question"
    reply(s, "director", "class: reflection-missed | question: director-reflection-missed | "
          f"route: reflection/questions.json owner-asked | summary: {new_gap}")  # fmt: skip
    out = run(s, "reflect", "--director")
    (c,) = comments(s, 5, KIT)
    assert new_gap in c, c
    assert f"correction lane: commented https://github.com/{KIT}/issues/5" in out, out
    assert new_gap in out, f"comment not printed: {out}"
    reply(s, "director")
    lane(top, "gh7", repo=KIT)
    reply(s, "lane", "class: reflection-missed | question: reflection-missed | route: r | "
          "summary: gh7 new gap")  # fmt: skip
    out = run(s, "reflect", "gh7")
    assert len(comments(s, 5, KIT)) == 2, out
    assert "correction lane: commented " in out, out
    assert "gh7 new gap" in out, f"comment not printed: {out}"
    reply(s, "lane")
    out = run(s, "reflect", "gh7")
    assert NONE in out, out
    put(s, KIT, issue(s, 5, KIT) | {"title": 5})
    out = run(s, "reflect", "--director", want=1)
    assert "Traceback" not in out, out
    for want in ("item 1", "is not gh's issue JSON", "update gh, then rerun"):
        assert want in out, out
    before = dlog.read_text()
    reply(s, "director", "class: own-rule | question: writer-route | route: target: src/x.py | "
          "summary: director routes a target")  # fmt: skip
    out = run(s, "reflect", "--director", want=1)
    assert "a director reflection's route is never `target:`" in out, out
    assert dlog.read_text() == before, out


if __name__ == "__main__":
    main(archive, reflect)
