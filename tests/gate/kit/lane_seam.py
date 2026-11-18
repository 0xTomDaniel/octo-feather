"""The scenarios of tests/gate/kit/test_lane_seam.py (its items), this file their command
(testkit.main): scripts/octo-feather-lane seam, is a test's seam written down on its ticket from the
ticket's criteria before the test (AGENTS.md Rules, integration test seam; rules: octo-feather-lane
--help (seam); correction lane #987), offline. The ticket is real: lane gh840's #876, read through
the github-issues skill's issue-notes from real gh's recorded answers
(testkit/recordings/lane-seam.json: issue-view 876 --notes), and the test commit a scratch commit carrying the real test
commit's author time (74f80a78, fresh_worker_session at the herdr-spawn CLI, 2026-11-18T03:24:33Z).
As recorded #876 holds no seam record for herdr-spawn: refused. The same answers with a seam
record added before the test pass; added at the real late comment's time, or edited after the test,
refused. A Linear target reads the same through the linear skill's issue-view --notes, the testkit's
Linear stand-in (testkit/linear.py) replaying a tape built here: a description record counts by the
issue's last update (Linear keeps no description edit time), so one updated after the test is refused."""

from __future__ import annotations

import json
from pathlib import Path

import os

from lane_tickets import VIEW
from testkit import HERE, Ran, Scratch, kit, main

# gh 2.102.0 on 0xTomDaniel/octo-feather, 2026-11-18 (each recording's source): issue-notes 876.
TAPE = Path(__file__).parent / "testkit" / "recordings" / "lane-seam.json"
CRIT = "roles#acceptance-fresh-independent-worker"
TEST_AT = "2026-11-18T03:24:33+00:00"  # 74f80a78's author time on origin/gh840
RECORD = f"Seam: {CRIT}: `herdr-spawn` kit integration test, Herdr stood in"


def answers(*comments: tuple[str, str | None, str]) -> list[dict[str, object]]:
    """The recorded answers, #876 given COMMENTS (createdAt, lastEditedAt, body) after its real ones."""
    tape = json.loads(TAPE.read_text())
    for r in tape:
        if r["request"].startswith("api graphql"):
            d = json.loads(r["out"])
            nodes = d["data"]["repository"]["issue"]["comments"]["nodes"]
            for i, (at, edited, body) in enumerate(comments):
                url = f"https://github.com/0xTomDaniel/octo-feather/issues/876#issuecomment-{i + 1}"
                nodes.append({"url": url, "createdAt": at, "lastEditedAt": edited, "body": body})
            r["out"] = json.dumps(d)
    return tape


def seam(s: Scratch, tape: list[dict[str, object]], *args: str, want: int = 0) -> Ran:
    """`octo-feather-lane seam 876 ...` in the scratch repo, gh answering only TAPE."""
    s.gh.store("tape.json", tape)
    (s.gh.dir / "log").write_text("")  # each run replays the tape from its first answer
    return s.run([kit("octo-feather-lane"), "seam", "876", *args], want=want, cwd=s.root / "t")


def gh840(s: Scratch) -> None:
    """The real case: #876 as recorded names herdr-spawn only in prose and a table pointer, so
    fresh_worker_session's seam is refused, before the test and with no time; a `Seam:` record
    posted at the brief's time (03:22Z) passes; the same record at the real late comment's time
    (04:21:10Z), or one posted earlier but edited after the test, is refused naming both times; a
    criterion #876 does not list is refused; gh asked only repo view and the graphql read."""
    s.git(s.root, "init", "-q", "-b", "main", "t")
    (s.root / "t" / "test_herdr_messaging.py").write_text("def test_fresh_worker_session(): ...\n")
    s.git(s.root / "t", "add", ".")
    s.git(s.root / "t", "commit", "-q", "-m", "test", f"--date={TEST_AT}")
    before = (CRIT, "herdr-spawn", "--before", "HEAD")
    r = seam(s, answers(), *before, want=1)
    assert r.out.startswith(
        f"876: class: unlisted-test-seam: no seam record for {CRIT} `herdr-spawn` on 876"
    ), f"real #876: {r.out}"
    assert "tell your supervisor" in r.out, f"a test already written names the escalation: {r.out}"
    r = seam(s, answers(), CRIT, "herdr-spawn", want=1)
    assert "post `Seam: " in r.out and "tell your supervisor" not in r.out, f"no --before: {r.out}"
    r = seam(s, answers(("2026-11-18T03:22:00Z", None, RECORD)), *before)
    want = f"876: seam {CRIT} `herdr-spawn` recorded at 2026-11-18T03:22:00Z ("
    assert r.out.startswith(want) and r.out.endswith(", before commit " + r.out[-8:]), r.out
    for late in (("2026-11-18T04:21:10Z", None, RECORD), ("2026-11-18T03:00:00Z", "2026-11-18T04:21:10Z", RECORD)):
        r = seam(s, answers(late), *before, want=1)
        said = "recorded on 876 at 2026-11-18T04:21:10Z"
        assert said in r.out and "at 2026-11-18T03:24:33Z" in r.out, f"late {late[:2]}: {r.out}"
    fenced = f"```\n{RECORD}\n```"
    r = seam(s, answers(("2026-11-18T03:22:00Z", None, fenced)), *before, want=1)
    assert "no seam record" in r.out, f"a record in a fence: {r.out}"
    r = seam(s, answers(), "roles#acceptance-delegated-pr", "herdr-spawn", want=1)
    assert "class: seam-off-criteria: roles#acceptance-delegated-pr" in r.out, r.out
    asked = {x.split(" ", 2)[0] + " " + x.split(" ", 2)[1] for x in s.gh.log()}
    assert asked == {"issue view", "api graphql"}, f"gh asked: {s.gh.log()}"


# The linear skill's issue-view --notes second call: its GraphQL document, verbatim.
NOTES = (
    "query IssueNotes($id: String!) { issue(id: $id) { url createdAt updatedAt description\n  "
    "comments(first: 250) { nodes { url createdAt editedAt body } pageInfo { hasNextPage } } } }"
)
DESC = f"## Acceptance criteria\n\n- [ ] {CRIT}: x\n- [ ] demo: `x`\n"


def linear_tape(d: Path, updated: str, desc: str, comments: list[dict[str, object]]) -> None:
    """D's tape: ENG-1 (created 2026-11-13, last updated UPDATED, description DESC, COMMENTS) as
    linear-cli v3.1.0 prints Linear's answers. Built, not recorded: LINEAR_API_KEY is not set in
    the factory (director decision on #921)."""
    url = "https://linear.app/acme/issue/ENG-1/t"
    view = {"identifier": "ENG-1", "title": "t", "description": desc, "url": url,
            "state": {"type": "started"}, "parent": None,
            "children": {"nodes": [], "pageInfo": {"hasNextPage": False}},
            "inverseRelations": {"nodes": []}}
    notes = {"url": url, "createdAt": "2026-11-13T05:37:26.000Z", "updatedAt": updated,
             "description": desc, "comments": {"nodes": comments, "pageInfo": {"hasNextPage": False}}}
    calls = [{"argv": ["api", "--no-input", "--variable", "id=ENG-1", q], "stdin": None,
              "answers": [{"rc": 0, "err": "", "json": {"data": {"issue": i}}}]}
             for q, i in ((VIEW, view), (NOTES, notes))]
    d.mkdir(exist_ok=True)
    (d / "tape.json").write_text(json.dumps({"source": linear_tape.__doc__, "calls": calls}))
    (d / "log").write_text("")


def linear(s: Scratch) -> None:
    """A Linear target: a comment record before the test passes, edited after it is refused; a
    description record passes while the issue was last updated before the test, and is refused
    once it was updated after (a state move counts: Linear keeps no description edit time)."""
    fl = s.root / "fl"
    s.env |= {"FAKE_LINEAR": str(fl), "PATH": f"{s.bin}{os.pathsep}{HERE / 'linear'}{os.pathsep}{s.env['PATH']}"}
    s.git(s.root, "init", "-q", "-b", "main", "t")
    (s.root / "t" / ".octo-feather.toml").write_text('tracker = "linear"\n')
    s.git(s.root / "t", "add", ".")
    s.git(s.root / "t", "commit", "-q", "-m", "test", f"--date={TEST_AT}")

    def run(updated: str, desc: str, comments: list[dict[str, object]], want: int) -> str:
        linear_tape(fl, updated, desc, comments)
        cmd = [kit("octo-feather-lane"), "seam", "ENG-1", CRIT, "herdr-spawn", "--before", "HEAD"]
        return s.run(cmd, want=want, cwd=s.root / "t").out

    def note(at: str, edited: str | None) -> dict[str, object]:
        return {"url": "https://linear.app/acme/issue/ENG-1/t#comment-1", "createdAt": at, "editedAt": edited, "body": RECORD}

    early, late = "2026-11-18T03:22:00.000Z", "2026-11-18T04:21:10.000Z"
    out = run(early, DESC, [note(early, None)], 0)
    assert out.startswith(f"ENG-1: seam {CRIT} `herdr-spawn` recorded at 2026-11-18T03:22:00Z"), out
    out = run(late, DESC, [note(early, late)], 1)
    assert "class: unlisted-test-seam" in out and "at 2026-11-18T04:21:10Z" in out, f"edited after: {out}"
    out = run(early, DESC + RECORD + "\n", [], 0)
    assert "recorded at 2026-11-18T03:22:00Z" in out, f"description, updated before: {out}"
    out = run(late, DESC + RECORD + "\n", [], 1)
    assert "recorded on ENG-1 at 2026-11-18T04:21:10Z" in out, f"description, updated after: {out}"


if __name__ == "__main__":
    main(gh840, linear)
