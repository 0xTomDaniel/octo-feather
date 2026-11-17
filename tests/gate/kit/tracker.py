"""The scenarios of tests/gate/kit/test_tracker.py (its items), this file their command
(testkit.main): the tracker per target (spec skills#tracker, docs/adr/0004), offline.

Seam (ticket #926, from its criteria, before any test; quality #acceptance-public-surfaces): the
CLIs of the tracker scripts (lane-key, key-from-branch, issue-view, issue-create, issue-comment,
issue-done, pr-line) of both tracker skills, `pi-role --json`, `octo-feather-start --issue`,
`check-skills`, and `octo-feather-lane tickets`. Stand-ins sit only at the CLI boundary of a
system the kit does not own: `linear` (testkit/linear.py, replaying the tape
tests/fixtures/linear-tracker/tape.json: not recorded, as LINEAR_API_KEY is not set in the
factory, but built from linear-cli v3.1.0's source and Linear's GraphQL schema, its `source`
says how), `gh` (testkit/gh.py), `herdr` (testkit/herdr.py). A call no tape records fails
naming it.

  skills    no .octo-feather.toml, or tracker = "github": the supervisor gets github-pr and
            github-issues from pi-role, not linear (asked from a subdirectory); the code reviewer
            lists no {tracker}; tracker = "linear": the supervisor gets github-pr and linear,
            never github-issues, no role linear-cli or github-issues; tracker = "jira": pi-role
            and octo-feather-start --issue exit non-zero naming jira and the kit's trackers, and
            the testkit herdr logs no workspace, tab or agent start
  checked   check-skills passes a clean kit copy and fails one holding a tracker script not
            executable, naming skill and script, each of two alone (each run starts the real Pi)
  missing   one item per tracker script: check-skills fails a kit copy whose github-issues, then
            whose linear, lacks it alone, naming skill and script
  github    each github-issues script against the offline gh (github-pr's scripts/gh) over a
            snapshot, whose refusal of writes passes through; issue-view lists sub-issue keys as
            children and refuses a partial list; the writes against the testkit gh: the gh call
            each makes, what it prints, what GitHub then holds
  linear    each linear script through the tape: the same output shapes as github-issues; each
            write's linear calls as the stand-in logged them, and what the script prints of
            Linear's answer; issue-done leaves an issue already done (Canceled) as it is
"""

from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

from testkit import FIXTURES, HERE, ROOT, Ran, Scratch, kit, main

if TYPE_CHECKING:
    from pathlib import Path

AGENTS = ROOT / "agents"
GI = ROOT / ".agents" / "skills" / "github-issues" / "scripts"
LI = ROOT / ".agents" / "skills" / "linear" / "scripts"
OFFLINE_GH = ROOT / ".agents" / "skills" / "github-pr" / "scripts" / "gh"
SCRIPTS = (
    "lane-key",
    "key-from-branch",
    "issue-view",
    "issue-create",
    "issue-comment",
    "issue-done",
    "pr-line",
)
VIEW_KEYS = ["key", "title", "body", "state", "url", "parent", "children", "blocked_by"]


def target(s: Scratch, tracker: str | None = None) -> Path:
    """S's target: a git repo with a subdirectory sub and a file body (hi), its
    .octo-feather.toml naming TRACKER (none: no file)."""
    t = s.root / "target"
    s.run(["git", "init", "-q", str(t)])
    (t / "sub").mkdir()
    (t / "body").write_text("hi\n")
    if tracker:
        (t / ".octo-feather.toml").write_text(f'tracker = "{tracker}"\n')
    return t


@dataclass(frozen=True)
class Launch:
    """`pi-role --json`'s output, the one field read: args, Pi's arguments."""

    args: list[str]


def launch(out: str) -> Launch:
    """OUT parsed and validated once; fails naming the field it rejects."""
    d: object = json.loads(out)
    args = cast("dict[str, object]", d).get("args") if isinstance(d, dict) else None
    ok = isinstance(args, list) and all(isinstance(a, str) for a in cast("list[object]", args))
    assert ok, f"pi-role --json: field args is not a list of text: {out}"
    return Launch(cast("list[str]", args))


def names(s: Scratch, cwd: Path, role: str) -> list[str]:
    """The skill names pi-role --json passes ROLE's launch in CWD, in order."""
    a = launch(s.run([kit("pi-role"), "--json", str(AGENTS / f"{role}.md")], cwd=cwd).out).args
    return [a[i + 1].rsplit("/", 1)[1] for i, x in enumerate(a[:-1]) if x == "--skill"]


def skills(s: Scratch) -> None:
    """The skills each tracker gives; jira refused (the module docstring)."""
    t = target(s)
    for case in ("none", "github"):
        if case == "github":
            (t / ".octo-feather.toml").write_text('tracker = "github"\n')
        got = names(s, t / "sub", "supervisor")
        assert {"github-pr", "github-issues"} <= set(got), f"supervisor, tracker {case}: {got}"
        assert "linear" not in got, f"supervisor, tracker {case}: {got}"
        assert not [n for n in got if "{tracker}" in n], f"supervisor, tracker {case}: {got}"
    assert names(s, t, "code-reviewer") == [
        "code-review",
        "github-pr",
        "refactoring",
        "principle-laziness-protocol",
        "principle-subtract-before-you-add",
        "principle-minimize-reader-load",
        "tdd",
        "codebase-design",
    ], "code-reviewer lists no {tracker}"
    (t / ".octo-feather.toml").write_text('tracker = "linear"\n')
    got = names(s, t / "sub", "supervisor")
    assert {"github-pr", "linear"} <= set(got), f"supervisor, tracker linear: {got}"
    assert not {"github-issues", "linear-cli"} & set(got), f"supervisor, tracker linear: {got}"
    for role in sorted(f.stem for f in AGENTS.glob("*.md")):
        got = names(s, t, role)
        assert not {"github-issues", "linear-cli"} & set(got), f"{role}, tracker linear: {got}"
    (t / ".octo-feather.toml").write_text('tracker = "jira"\n')
    r = s.run([kit("pi-role"), "--json", str(AGENTS / "supervisor.md")], cwd=t, want=1)
    said = r.out + r.err
    assert "unknown tracker 'jira'" in said, said
    assert "the kit has: github" in said, said
    assert '"args"' not in said, said
    for k in ("HERDR_SESSION", "HERDR_PANE_ID"):
        s.env.pop(k, None)
    world = s.root / "herdr"
    world.mkdir()
    s.env["FAKE_HERDR"] = str(world)
    r = s.run([kit("octo-feather-start"), "--issue", "5", "--cwd", str(t)], want=65)
    assert "jira" in r.err, r.err
    assert "the kit has: github" in r.err, r.err
    calls = (world / "log").read_text().splitlines() if (world / "log").exists() else []
    started = [c for c in calls if c.startswith(("workspace create", "tab create", "agent start"))]
    assert not started, f"a workspace or agent started: {calls}"


def kit_copy(s: Scratch) -> tuple[Path, list[str]]:
    """A kit copy check-skills reads (agents, skills, extensions, pi-role), and its command, run
    with the real Pi, which check-skills asks, not the testkit's."""
    k = s.root / "kit"
    for d in ("agents", ".agents", "extensions"):
        shutil.copytree(ROOT / d, k / d, symlinks=True)
    (k / "scripts").mkdir()
    for f in ("scripts/check-skills", "scripts/pi-role", "web-mcp.json"):
        shutil.copy2(ROOT / f, k / f)
    s.env["PATH"] = os.environ["PATH"]
    return k, [str(k / "scripts" / "check-skills")]


def checked(s: Scratch) -> None:
    """check-skills on a kit copy: clean, then each of two tracker scripts not executable alone."""
    k, check = kit_copy(s)
    out = s.run(check, cwd=k).out
    assert "trackers github, linear)" in out, f"check-skills covers both trackers: {out}"
    for sk, n in (("linear", "issue-done"), ("github-issues", "pr-line")):
        f = k / ".agents/skills" / sk / "scripts" / n
        f.chmod(0o644)
        err = s.run(check, cwd=k, want=1).err
        assert f"tracker skill {sk}: tracker script {n} is not executable" in err, err
        f.chmod(0o755)


def missing(s: Scratch, n: str) -> None:
    """check-skills on a kit copy without tracker script N, in each tracker skill alone."""
    k, check = kit_copy(s)
    for sk in ("github-issues", "linear"):
        f = k / ".agents/skills" / sk / "scripts" / n
        f.rename(s.root / n)
        err = s.run(check, cwd=k, want=1).err
        assert f"tracker skill {sk}: missing tracker script {n} " in err, f"{sk} {n}: {err}"
        (s.root / n).rename(f)


def snapshot(s: Scratch) -> Path:
    """The offline gh's snapshot of o/r: issue 3 (sub-issues 7, 8), 7 (parent 3, blocked by 4 and
    5), 8 closed, and 9 whose sub-issue list gh pages (2 of 3 returned)."""
    sn = s.root / "snap"
    (sn / "issue").mkdir(parents=True)
    meta: dict[str, object] = {
        "repo": "o/r",
        "fetched_at": "2026-10-22T00:00:00Z",
        "counts": {},
        "capped": [],
    }
    (sn / "meta.json").write_text(json.dumps(meta))

    def issue(  # noqa: PLR0913 (one issue's fields)
        n: int,
        *,
        parent: object = None,
        blockers: tuple[int, ...] = (),
        state: str = "OPEN",
        children: tuple[int, ...] = (),
        total: int | None = None,
    ) -> None:
        sub = [{"number": c, "state": "OPEN", "title": "t", "url": "u"} for c in children]
        total = len(children) if total is None else total
        d = {
            "number": n,
            "title": f"Issue {n}",
            "body": f"body {n}",
            "state": state,
            "url": f"https://github.com/o/r/issues/{n}",
            "parent": parent,
            "blockedBy": {"nodes": [{"number": b} for b in blockers], "totalCount": len(blockers)},
            "subIssues": {"nodes": sub, "totalCount": total},
        }
        (sn / "issue" / f"{n}.json").write_text(json.dumps(d))

    issue(3, children=(7, 8))
    issue(9, children=(7, 8), total=3)
    parent = {"number": 3, "title": "Parent", "url": "https://github.com/o/r/issues/3"}
    issue(7, parent=parent, blockers=(4, 5))
    issue(8, state="CLOSED")
    return sn


def github(s: Scratch) -> None:
    """github-issues against the offline gh, then its writes against the testkit gh."""
    t = target(s)
    off = s.root / "offline"
    off.mkdir()
    (off / "gh").symlink_to(OFFLINE_GH)
    env = {"PATH": f"{off}:{s.env['PATH']}", "OCTO_FEATHER_GHSNAP": str(snapshot(s))}

    def gi(want: int, script: str, *a: str) -> Ran:
        return s.run([str(GI / script), *a], want=want, cwd=t, env=env)

    r = gi(0, "issue-view", "7")
    assert json.loads(r.out) == {
        "key": "7",
        "title": "Issue 7",
        "body": "body 7",
        "state": "open",
        "url": "https://github.com/o/r/issues/7",
        "parent": "3",
        "children": [],
        "blocked_by": ["4", "5"],
    }, f"issue-view 7: {r.out}"
    d = json.loads(gi(0, "issue-view", "#8").out)
    assert [d["key"], d["state"], d["parent"], d["blocked_by"]] == ["8", "done", None, []], d
    assert json.loads(gi(0, "issue-view", "3").out)["children"] == ["7", "8"]
    r = gi(1, "issue-view", "9")
    assert (r.out, "partial or unreadable sub-issue list" in r.err) == ("", True), r
    r = gi(1, "issue-view", "10")
    assert (r.out, "not in snapshot" in r.err) == ("", True), r
    assert "not a GitHub issue key" in gi(1, "issue-view", "ENG-1").err
    for k in ("82", "#82", "gh82", "https://github.com/o/r/issues/82"):
        assert gi(0, "lane-key", k).out == "gh82", f"lane-key {k}"
    r = gi(1, "lane-key", "ENG-123")
    assert (r.out, "not a GitHub issue number" in r.err) == ("", True), r
    for b in ("gh82", "lanes/gh82", "gh82-fix", "implementer-gh82", "gh82-gh97"):
        assert gi(0, "key-from-branch", b).out == "82", f"key-from-branch {b}"
    assert "names no GitHub issue" in gi(1, "key-from-branch", "main").err
    assert gi(0, "pr-line", "82").out == "Closes #82"
    # The offline gh is read-only: each write exits non-zero with its refusal, printing nothing.
    for a in (
        ("issue-create", "--title", "T", "--body-file", "body"),
        ("issue-comment", "7", "--body-file", "body"),
        ("issue-done", "7"),
    ):
        r = gi(1, *a)
        assert (r.out, "read-only snapshot" in r.err) == ("", True), f"{a[0]} refusal: {r}"
    for n, state in (
        (3, "OPEN"),
        (4, "OPEN"),
        (5, "OPEN"),
        (6, "CLOSED"),
        (7, "OPEN"),
        (11, "OPEN"),
    ):
        s.gh.store(f"issue/{n}.json", {"number": n, "title": f"Issue {n}", "state": state})
    new = ("--title", "New one", "--body-file", "body", "--parent", "#3")
    r = s.run([str(GI / "issue-create"), *new, "--blocked-by", "4", "--blocked-by", "5"], cwd=t)
    assert r.out == "12", f"issue-create: {r.out}"
    want = "issue create --title New one --body-file body --parent 3 --blocked-by 4,5"
    assert s.gh.log()[-1] == want, s.gh.log()
    i12 = json.loads((s.gh.dir / "issue" / "12.json").read_text())
    assert [i12["title"], i12["body"]] == ["New one", "hi\n"], i12
    r = s.run([str(GI / "issue-comment"), "7"], cwd=t, stdin="a note\n")
    assert r.out == "https://github.com/o/r/issues/7#issuecomment-1001", r.out
    assert s.gh.log()[-1] == "issue comment 7 --body-file -", s.gh.log()
    i7 = json.loads((s.gh.dir / "issue" / "7.json").read_text())
    assert [c["body"] for c in i7["comments"]] == ["a note\n"], i7
    for n in ("7", "6"):  # 6 already closed
        r = s.run([str(GI / "issue-done"), n], cwd=t)
        assert (r.out, r.err) == ("", ""), f"issue-done {n} printed: {r}"
        assert s.gh.log()[-1] == f"issue close {n}", s.gh.log()
        assert json.loads((s.gh.dir / "issue" / f"{n}.json").read_text())["state"] == "CLOSED"


def linear(s: Scratch) -> None:  # noqa: PLR0915 (one tape session, its calls in order)
    """linear's scripts through the tape: ENG-7 (parent ENG-3, blocked by ENG-4 and ENG-5),
    ENG-8 canceled, ENG-9 not found until issue-create files it."""
    t = target(s)
    (s.root / "tape.json").symlink_to(FIXTURES / "linear-tracker" / "tape.json")
    env = {"PATH": f"{HERE / 'linear'}:{s.env['PATH']}", "FAKE_LINEAR": str(s.root)}

    def li(want: int, script: str, *a: str, stdin: str | None = None) -> Ran:
        return s.run([str(LI / script), *a], want=want, cwd=t, env=env, stdin=stdin)

    seen = [0]

    def writes() -> list[list[str | None]]:
        """The linear calls since the last asked, other than api reads, as [ARGV..., STDIN]."""
        calls = [json.loads(x) for x in (s.root / "log").read_text().splitlines()]
        new, seen[0] = calls[seen[0] :], len(calls)
        return [[*a, i] for a, i in new if a[0] != "api"]

    r = li(0, "issue-view", "ENG-7")
    assert json.loads(r.out) == {
        "key": "ENG-7",
        "title": "Issue 7",
        "body": "body 7",
        "state": "open",
        "url": "https://linear.app/acme/issue/ENG-7/issue-7",
        "parent": "ENG-3",
        "children": [],
        "blocked_by": ["ENG-4", "ENG-5"],
    }, f"linear issue-view ENG-7: {r.out}"
    assert json.loads(li(0, "issue-view", "ENG-3").out)["children"] == ["ENG-7"]
    d = json.loads(li(0, "issue-view", "eng-8").out)
    got = [d["key"], d["body"], d["state"], d["parent"], d["blocked_by"]]
    assert got == ["ENG-8", "", "done", None, []], f"linear issue-view eng-8: {d}"
    assert sorted(d) == sorted(VIEW_KEYS), f"the same keys as github-issues: {d}"
    r = li(1, "issue-view", "ENG-9")
    assert (r.out, "Entity not found" in r.err) == ("", True), r
    assert "not a Linear issue key" in li(1, "issue-view", "82").err
    for k in ("ENG-123", "eng-123", "https://linear.app/acme/issue/ENG-123/some-title"):
        assert li(0, "lane-key", k).out == "eng-123", f"lane-key {k}"
    r = li(1, "lane-key", "82")
    assert (r.out, "not a Linear issue key" in r.err) == ("", True), r
    for b in (
        "eng-123",
        "lanes/eng-123",
        "eng-123-fix",
        "implementer-eng-123",
        "code-reviewer-eng-123",
    ):
        assert li(0, "key-from-branch", b).out == "ENG-123", f"linear key-from-branch {b}"
    assert "names no Linear issue" in li(1, "key-from-branch", "main").err
    assert li(0, "pr-line", "eng-123").out == "Tracks ENG-123"
    assert writes() == [], "a read wrote"
    # Writes: the linear calls each makes, and what it prints of Linear's answer, as github-issues.
    new = ("--title", "New one", "--body-file", "body", "--parent", "eng-3")
    assert (
        li(0, "issue-create", *new, "--blocked-by", "ENG-4", "--blocked-by", "ENG-5").out == "ENG-9"
    )
    create = ["issue", "create", "--title", "New one", "--description-file", "body"]
    assert writes() == [
        [*create, "--parent", "ENG-3", "--team", "ENG", "--no-input", None],
        ["issue", "relation", "add", "ENG-9", "blocked-by", "ENG-4", "--no-input", None],
        ["issue", "relation", "add", "ENG-9", "blocked-by", "ENG-5", "--no-input", None],
    ]
    d = json.loads(li(0, "issue-view", "ENG-9").out)
    got = [d["title"], d["body"], d["state"], d["parent"], d["blocked_by"]]
    assert got == ["New one", "hi\n", "open", "ENG-3", ["ENG-4", "ENG-5"]], f"new ENG-9: {d}"
    r = li(1, "issue-create", "--title", "T", "--body-file", "body")
    assert (r.out, "No team given" in r.err) == ("", True), r
    r = li(
        1,
        "issue-create",
        "--title",
        "T",
        "--body-file",
        "body",
        "--parent",
        "ENG-3",
        "--blocked-by",
        "ENG-99",
    )
    assert r.out == "", r.out
    assert "filed ENG-10, but marking it blocked by ENG-99 failed" in r.err, r.err
    writes()
    r = li(0, "issue-comment", "ENG-7", stdin="a note\n")
    assert r.out == "https://linear.app/acme/issue/ENG-7/issue-7#comment-3f2a9c1e", r.out
    assert writes() == [
        ["issue", "comment", "add", "ENG-7", "--body-file", "-", "--no-input", "a note\n"]
    ]
    r = li(0, "issue-comment", "ENG-7", "--body-file", "body")
    assert r.out == "https://linear.app/acme/issue/ENG-7/issue-7#comment-8b41d7a0", r.out
    for done in ([["issue", "update", "ENG-7", "--state", "completed", "--no-input", None]], []):
        writes()
        r = li(0, "issue-done", "ENG-7")  # the second on an issue already done
        assert (r.out, r.err) == ("", ""), f"linear issue-done ENG-7 printed: {r}"
        assert writes() == done, "issue-done ENG-7 moved it to Done once"
        assert json.loads(li(0, "issue-view", "ENG-7").out)["state"] == "done"
    assert "not found" in li(1, "issue-done", "ENG-99").err
    # An issue already done stays as it is: Canceled is done, so issue-done leaves it Canceled.
    r = li(0, "issue-done", "ENG-8")
    assert (r.out, r.err) == ("", ""), f"linear issue-done ENG-8 printed: {r}"
    assert writes() == [], "issue-done moved canceled ENG-8"


if __name__ == "__main__":
    main(skills, checked, missing, github, linear)
