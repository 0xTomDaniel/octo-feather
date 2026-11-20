"""The scenarios of tests/gate/kit/test_lane_seam.py (its items), this file their command
(testkit.main): scripts/octo-feather-lane seam, the `Seam:` record contract (rules:
octo-feather-lane --help (seam); correction lane #987, ticket #1009), and the tracker skills'
issue-view --notes it reads (skills spec #tracker-script-issue-view), offline.

GitHub answers only real gh's, unmodified (testkit/recordings/lane-seam.json): #876, lane gh840's
ticket, holds no `Seam:` record for the herdr-spawn seam its test (74f80a78) was written at; #1009
holds two `Seam:` lines, written 2026-11-18T20:29:48Z. A scratch commit carries 74f80a78's author
time (before the record: late) and another a later one (after it). No real ticket holds a `Seam:`
record in a comment or one edited after a test, so those cases are Linear's.

Linear: LINEAR_API_KEY is not set in the factory (director decision on #921); its answers are a
tape built here, its source saying so (testkit/linear.py replays it)."""

from __future__ import annotations

import json
import os
from pathlib import Path

from lane_tickets import NOTES, VIEW
from testkit import HERE, ROOT, Ran, Scratch, kit, main

# gh 2.102.0 on 0xTomDaniel/octo-feather, 2026-11-18 (each recording's source).
TAPE = Path(__file__).parent / "testkit" / "recordings" / "lane-seam.json"
GH_VIEW = ROOT / ".agents" / "skills" / "github-issues" / "scripts" / "issue-view"
LIN_VIEW = ROOT / ".agents" / "skills" / "linear" / "scripts" / "issue-view"
TEST_AT = "2026-11-18T03:24:33+00:00"  # 74f80a78's author time on origin/gh840
LATER_AT = "2026-11-18T21:00:00+00:00"  # a test commit after #1009's Seam: lines
PUBLIC = "quality#acceptance-public-surfaces"
TRACKER = "skills#acceptance-tracker-scripts"


def commit(s: Scratch, repo: str, at: str) -> str:
    """A commit in REPO authored at AT; its SHA from git rev-parse."""
    (s.root / repo / "f").write_text(at)
    s.git(s.root / repo, "add", ".")
    s.git(s.root / repo, "commit", "-q", "-m", "test", f"--date={at}")
    return s.git(s.root / repo, "rev-parse", "HEAD")


def seam(s: Scratch, repo: str, *args: str, want: int = 0) -> Ran:
    """`octo-feather-lane seam ARGS` in REPO, each call replaying its tracker's answers afresh."""
    for d in (s.gh.dir, Path(s.env.get("FAKE_LINEAR", s.gh.dir))):
        (d / "log").write_text("")
    return s.run([kit("octo-feather-lane"), "seam", *args], want=want, cwd=s.root / repo)


def github(s: Scratch) -> None:
    """#876: issue-view --notes prints the body and both real comments with GitHub's times; seam
    finds no record for herdr-spawn, exit 1. #1009: its Seam: lines are late for a commit at
    74f80a78's time (exit 1, naming both times) and recorded before a later commit (exit 0, that
    commit's own SHA), for both its criteria; a criterion it does not list, seam-off-criteria.
    gh asked only issue view and the graphql read."""
    s.gh.store("tape.json", json.loads(TAPE.read_text()))
    s.git(s.root, "init", "-q", "-b", "main", "t")
    early, late = commit(s, "t", TEST_AT), commit(s, "t", LATER_AT)
    v = json.loads(s.run([str(GH_VIEW), "876", "--notes"], cwd=s.root / "t").out)
    got = [(n["at"], n["edited_at"]) for n in v["notes"]]
    want = [("2026-11-13T05:37:26Z", None), ("2026-11-18T04:21:10Z", None)]
    assert got[:2] == want, f"#876 notes: {got}"
    assert v["key"] == "876", v["key"]
    crit = "roles#acceptance-fresh-independent-worker"
    r = seam(s, "t", "876", crit, "herdr-spawn", "--before", early, want=1)
    no = f"876: class: unlisted-test-seam: no `Seam:` record for {crit} `herdr-spawn` on 876"
    assert r.out.startswith(no), f"#876: {r.out}"
    r = seam(s, "t", "1009", PUBLIC, "octo-feather-lane seam", "--before", early, want=1)
    url = "https://github.com/0xTomDaniel/octo-feather/issues/1009"
    said = (
        f"written at 2026-11-18T20:29:48Z ({url}), after commit {early[:8]} at 2026-11-18T03:24:33Z"
    )
    assert "class: unlisted-test-seam" in r.out, f"#1009 late: {r.out}"
    assert said in r.out, f"#1009 late: {r.out}"
    for crit, sm in ((PUBLIC, "octo-feather-lane seam"), (TRACKER, "issue-view")):
        r = seam(s, "t", "1009", crit, sm, "--before", late)
        ok = f"1009: seam {crit} `{sm}` recorded at 2026-11-18T20:29:48Z"
        assert r.out.startswith(ok), f"#1009 {crit}: {r.out}"
        assert r.out.endswith(f", before commit {late[:8]}"), f"#1009 {crit}: {r.out}"
    r = seam(s, "t", "1009", "roles#acceptance-delegated-pr", "issue-view", want=1)
    assert "class: seam-off-criteria: roles#acceptance-delegated-pr" in r.out, r.out
    asked = {" ".join(x.split(" ", 2)[:2]) for x in s.gh.log()}
    assert asked == {"issue view", "api graphql"}, f"gh asked: {s.gh.log()}"


SOURCE = (
    "Not recorded: LINEAR_API_KEY is not set in the factory (director decision on #921). Built "
    "from schpet/linear-cli v3.1.0's source (the linear skill's cli-version: `api` prints Linear's "
    "response compact) and Linear's GraphQL schema (linear/linear packages/sdk/src/schema.graphql: "
    "Issue.history IssueHistory.updatedAt and updatedDescription, Comment.editedAt null until "
    "edited). Each call answered once, as Linear would for ENG-1 in that state."
)
URL = "https://linear.app/acme/issue/ENG-1/t"
CRIT = "roles#acceptance-fresh-independent-worker"
RECORD = f"Seam: {CRIT}: `herdr-spawn` kit integration test"
DESC = f"## Acceptance criteria\n\n- [ ] {CRIT}: x\n- [ ] demo: `x`\n"
W0, W1, W2 = "2026-11-18T03:00:00.000Z", "2026-11-18T03:22:00.000Z", "2026-11-18T04:21:10.000Z"


def linear_tape(
    d: Path,
    desc: str,
    comments: list[dict[str, object]],
    history: list[dict[str, object]],
    *,
    more: bool = False,
) -> None:
    """D's tape: ENG-1, created 2026-11-13, with DESC, COMMENTS and HISTORY (MORE: a further
    page)."""
    view: dict[str, object] = {
        "identifier": "ENG-1",
        "title": "t",
        "description": desc,
        "url": URL,
        "state": {"type": "started"},
        "parent": None,
        "children": {"nodes": [], "pageInfo": {"hasNextPage": False}},
        "inverseRelations": {"nodes": []},
    }
    notes: dict[str, object] = {
        "url": URL,
        "createdAt": "2026-11-13T05:37:26.000Z",
        "description": desc,
        "comments": {"nodes": comments, "pageInfo": {"hasNextPage": False}},
        "history": {"nodes": history, "pageInfo": {"hasNextPage": more}},
    }
    calls: list[dict[str, object]] = [
        {
            "argv": ["api", "--no-input", "--variable", "id=ENG-1", q],
            "stdin": None,
            "answers": [{"rc": 0, "err": "", "json": {"data": {"issue": i}}}],
        }
        for q, i in ((VIEW, view), (NOTES, notes))
    ]
    d.mkdir(exist_ok=True)
    (d / "tape.json").write_text(json.dumps({"source": SOURCE, "calls": calls}))
    (d / "log").write_text("")


def note(at: str, edited: str | None) -> dict[str, object]:
    return {"url": f"{URL}#comment-1", "createdAt": at, "editedAt": edited, "body": RECORD}


def linear(s: Scratch) -> None:
    """A comment record written before the test passes; written after it, late (exit 1); written
    before and edited after, unchecked (exit 2), never late. A description record: its edit time
    is its latest history entry with updatedDescription, so a later state move leaves it before
    (exit 0) and a later description edit makes it unchecked (exit 2); history past one page,
    issue-view exits 1 naming the time it cannot give and seam is unchecked (exit 2)."""
    fl = s.root / "fl"
    path = f"{s.bin}{os.pathsep}{HERE / 'linear'}{os.pathsep}{s.env['PATH']}"
    s.env |= {"FAKE_LINEAR": str(fl), "PATH": path}
    s.git(s.root, "init", "-q", "-b", "main", "t")
    (s.root / "t" / ".octo-feather.toml").write_text('tracker = "linear"\n')
    sha = commit(s, "t", TEST_AT)
    args = ("ENG-1", CRIT, "herdr-spawn", "--before", sha)
    edit: dict[str, object] = {"updatedAt": W2, "updatedDescription": True}
    move: dict[str, object] = {"updatedAt": W2, "updatedDescription": False}

    linear_tape(fl, DESC, [note(W1, None)], [])
    r = seam(s, "t", *args)
    ok = f"ENG-1: seam {CRIT} `herdr-spawn` recorded at 2026-11-18T03:22:00Z ({URL}#comment-1)"
    assert r.out == f"{ok}, before commit {sha[:8]}", r.out
    linear_tape(fl, DESC, [note(W2, None)], [])
    r = seam(s, "t", *args, want=1)
    assert f"written at 2026-11-18T04:21:10Z ({URL}#comment-1), after commit {sha[:8]}" in r.out, (
        r.out
    )
    linear_tape(fl, DESC, [note(W0, W2)], [])
    r = seam(s, "t", *args, want=2)
    assert r.out.startswith("ENG-1: unchecked: "), f"comment edited after: {r.out}"
    assert "changed at 2026-11-18T04:21:10Z" in r.out, f"comment edited after: {r.out}"
    linear_tape(fl, DESC + RECORD + "\n", [], [move])
    v = json.loads(s.run([str(LIN_VIEW), "ENG-1", "--notes"], cwd=s.root / "t").out)
    assert v["notes"] == [
        {
            "at": "2026-11-13T05:37:26.000Z",
            "edited_at": None,
            "url": URL,
            "body": DESC + RECORD + "\n",
        }
    ], v
    r = seam(s, "t", *args)
    assert r.out.endswith(f", before commit {sha[:8]}"), f"description, state moved after: {r.out}"
    linear_tape(fl, DESC + RECORD + "\n", [], [move, edit])
    r = seam(s, "t", *args, want=2)
    assert "unchecked:" in r.out, f"description edited after: {r.out}"
    assert "changed at 2026-11-18T04:21:10Z" in r.out, f"description edited after: {r.out}"
    linear_tape(fl, DESC + RECORD + "\n", [], [move], more=True)
    r = s.run([str(LIN_VIEW), "ENG-1", "--notes"], cwd=s.root / "t", want=1)
    assert "the description's last edit time cannot be given" in r.err, r.err
    r = seam(s, "t", *args, want=2)
    assert "the description's last edit time cannot be given" in r.err, r.err


if __name__ == "__main__":
    main(github, linear)
