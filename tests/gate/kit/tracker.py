"""The scenarios of tests/gate/kit/test_tracker.py (its items), this file their command
(testkit.main): the tracker per target (spec skills#tracker, docs/adr/0004), offline.

  skills    a target with no .octo-feather.toml, or tracker = "github", gets github-pr and
            github-issues from pi-role, not linear (asked from a subdirectory); the code reviewer
            lists no {tracker}; tracker = "linear" gives the supervisor github-pr and linear,
            never github-issues, and no role linear-cli or github-issues; tracker = "jira" makes
            pi-role and octo-feather-start --issue N exit non-zero naming jira and the kit's
            trackers, and no workspace, tab or agent starts (testkit's fake herdr logs every call)
  checked   check-skills (in `just check`) fails a tracker skill missing any tracker script, or
            holding one not executable, naming skill and script; each check-skills run starts the
            real Pi (its cost floor, #558), so every missing script is named by one run and both
            non-executable ones by a second (the clean copy's ok line naming both trackers:
            check_skills.py judged)
  github    each github-issues script against the offline gh (github-pr's scripts/gh) over a
            snapshot, whose refusal of writes passes through, and the writes against testkit's
            fake gh (the GitHub stand-in: each call logged, issues stored); issue-view lists
            sub-issue keys as children and refuses a partial list
  linear    each linear script reads and writes through the kit's offline fake linear (linear's
            scripts/linear, a JSON store), which refuses any other command; the same output
            shapes as github-issues; issue-done leaves an issue already done (Canceled) as it is;
            the fake's api answers a query under any operation name or none with only the
            selected fields (nested, aliased, paged by first) and refuses a field outside
            Linear's schema by name, so issue-view's JSON proves what its query selects

The target repo (a subdirectory in it) is prepared once per gate run (Scratch.prepare).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import TYPE_CHECKING

from testkit import ROOT, Ran, Scratch, kit, kit_repo, main, tool_homes

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


def build_target(p: Scratch) -> None:
    """P/target: an empty git repo, with a subdirectory sub."""
    p.run(["git", "init", "-q", str(p.root / "target")])
    (p.root / "target" / "sub").mkdir()


def target(s: Scratch, tracker: str | None = None) -> Path:
    """The prepared target in S, its .octo-feather.toml naming TRACKER (none: no file)."""
    s.prepare("tracker-target", build_target)
    t = s.root / "target"
    if tracker:
        (t / ".octo-feather.toml").write_text(f'tracker = "{tracker}"\n')
    return t


def names(s: Scratch, cwd: Path, role: str) -> list[str]:
    """The skill names pi-role --json passes ROLE's launch in CWD, in order."""
    a = json.loads(s.run([kit("pi-role"), "--json", str(AGENTS / f"{role}.md")], cwd=cwd).out)
    return [a["args"][i + 1].rsplit("/", 1)[1] for i, x in enumerate(a["args"]) if x == "--skill"]


def skills(s: Scratch) -> None:
    """No config and github: github-pr and github-issues, no linear, from a subdirectory; the code
    reviewer's exact list; linear: the supervisor gets github-pr and linear, never github-issues,
    no role linear-cli or github-issues; jira refused by pi-role and octo-feather-start, nothing
    started."""
    t = target(s)
    for case in ("none", "github"):
        if case == "github":
            (t / ".octo-feather.toml").write_text('tracker = "github"\n')
        got = names(s, t / "sub", "supervisor")
        assert "github-pr" in got, f"supervisor with tracker {case}: {got}"
        assert "github-issues" in got, f"supervisor with tracker {case}: {got}"
        assert "linear" not in got, f"supervisor with tracker {case}: {got}"
        assert not [n for n in got if "{tracker}" in n], f"supervisor with tracker {case}: {got}"
    got = names(s, t, "code-reviewer")
    assert got == ["code-review", "github-pr", "tdd", "codebase-design"], (
        f"code-reviewer lists no {{tracker}} but got: {got}"
    )
    (t / ".octo-feather.toml").write_text('tracker = "linear"\n')
    got = names(s, t / "sub", "supervisor")
    assert "github-pr" in got, f"supervisor with tracker linear: {got}"
    assert "linear" in got, f"supervisor with tracker linear: {got}"
    assert "github-issues" not in got, f"supervisor with tracker linear: {got}"
    assert "linear-cli" not in got, f"supervisor with tracker linear: {got}"
    roles = sorted(f.stem for f in AGENTS.glob("*.md"))
    assert "supervisor" in roles, roles
    for role in roles:
        got = names(s, t, role)
        assert "linear-cli" not in got, f"{role} with tracker linear: {got}"
        assert "github-issues" not in got, f"{role} with tracker linear: {got}"
    unknown(s, t)


def unknown(s: Scratch, t: Path) -> None:
    """tracker = "jira": pi-role refuses naming jira and github, printing no args; octo-feather-
    start --issue 5 refuses alike, and no workspace, tab or agent starts in the fake herdr."""
    (t / ".octo-feather.toml").write_text('tracker = "jira"\n')
    p = s.run([kit("pi-role"), "--json", str(AGENTS / "supervisor.md")], cwd=t, want=1)
    said = p.out + p.err
    assert "unknown tracker 'jira'" in said, said
    assert "the kit has: github" in said, said
    assert '"args"' not in said, said
    world = s.root / "herdr"
    world.mkdir()
    r = start(s, t, world)
    said = r.out + r.err
    assert r.rc != 0, f"octo-feather-start with tracker jira exited 0: {said}"
    assert "jira" in said, said
    assert "the kit has: github" in said, said
    log = world / "log"
    calls = log.read_text().splitlines() if log.exists() else []
    started = [c for c in calls if c.startswith(("workspace create", "tab create", "agent start"))]
    assert not started, f"a workspace or agent started: {calls}"


def start(s: Scratch, t: Path, world: Path) -> Ran:
    """octo-feather-start --issue 5 --cwd T outside any Herdr pane (testkit's fake herdr over
    WORLD), whatever it exits."""
    pane = ("HERDR_SESSION", "HERDR_PANE_ID")
    full = {k: v for k, v in s.env.items() if k not in pane} | {"FAKE_HERDR": str(world)}
    p = subprocess.run(
        [kit("octo-feather-start"), "--issue", "5", "--cwd", str(t)],
        cwd=s.root,
        env=full,
        capture_output=True,
        text=True,
        check=False,
    )
    assert "Traceback" not in p.stderr, p.stderr
    return Ran(p.returncode, p.stdout, p.stderr)


def checked(s: Scratch) -> None:
    """A kit copy whose tracker skills lack every tracker script: check-skills exits 1 naming each
    skill and script; then each script back, linear's issue-done and github-issues' pr-line not
    executable: exit 1 naming both."""
    k = kit_repo(s)
    env = {**tool_homes(), "PATH": os.environ["PATH"]}  # the real pi check-skills asks

    def check() -> str:
        r = s.run([sys.executable, str(k / "scripts" / "check-skills")], cwd=k, env=env, want=1)
        return r.out + r.err

    held = s.root / "held"
    for sk in ("github-issues", "linear"):
        (held / sk).mkdir(parents=True)
        for n in SCRIPTS:
            (k / ".agents" / "skills" / sk / "scripts" / n).rename(held / sk / n)
    out = check()
    for sk in ("github-issues", "linear"):
        for n in SCRIPTS:
            want = f"tracker skill {sk}: missing tracker script {n} "
            assert want in out, f"check-skills without {sk} {n}: {out}"
            (held / sk / n).rename(k / ".agents" / "skills" / sk / "scripts" / n)
    (k / ".agents/skills/linear/scripts/issue-done").chmod(0o644)
    (k / ".agents/skills/github-issues/scripts/pr-line").chmod(0o644)
    out = check()
    want = "tracker skill linear: tracker script issue-done is not executable"
    assert want in out, f"check-skills with linear issue-done not executable: {out}"
    want = "tracker skill github-issues: tracker script pr-line is not executable"
    assert want in out, f"check-skills with pr-line not executable: {out}"


def snapshot(s: Scratch) -> Path:
    """The offline gh's snapshot of o/r: issue 3 (sub-issues 7, 8), 7 (parent 3, blocked by 4 and
    5), 8 closed, and 9 whose sub-issue list gh pages (2 of 3 returned)."""
    sn = s.root / "snap"
    (sn / "issue").mkdir(parents=True)
    meta = {"repo": "o/r", "fetched_at": "2026-10-22T00:00:00Z", "counts": {}, "capped": []}
    (sn / "meta.json").write_text(json.dumps(meta))

    def issue(  # noqa: PLR0913 (one issue's fields)
        n: int,
        parent: object = None,
        blockers: tuple[int, ...] = (),
        state: str = "OPEN",
        children: tuple[int, ...] = (),
        total: int | None = None,
    ) -> None:
        sub = [{"number": c, "state": "OPEN", "title": "t", "url": "u"} for c in children]
        d = {
            "number": n,
            "title": f"Issue {n}",
            "body": f"body {n}",
            "state": state,
            "url": f"https://github.com/o/r/issues/{n}",
            "parent": parent,
            "blockedBy": {"nodes": [{"number": b} for b in blockers], "totalCount": len(blockers)},
            "subIssues": {"nodes": sub, "totalCount": len(children) if total is None else total},
        }
        (sn / "issue" / f"{n}.json").write_text(json.dumps(d))

    issue(3, children=(7, 8))
    issue(9, children=(7, 8), total=3)
    parent = {"number": 3, "title": "Parent", "url": "https://github.com/o/r/issues/3"}
    issue(7, parent=parent, blockers=(4, 5))
    issue(8, state="CLOSED")
    return sn


def github(s: Scratch) -> None:
    """github-issues against the offline gh: reads, keys, refused writes; the writes against
    testkit's fake gh: the one gh call each makes, what it prints, what GitHub then holds."""
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
    assert list(json.loads(r.out)) == [
        "key",
        "title",
        "body",
        "state",
        "url",
        "parent",
        "children",
        "blocked_by",
    ], r.out
    d = json.loads(gi(0, "issue-view", "#8").out)
    assert [d["key"], d["state"], d["parent"], d["blocked_by"]] == ["8", "done", None, []], d
    d = json.loads(gi(0, "issue-view", "3").out)
    assert d["children"] == ["7", "8"], f"issue-view 3 children: {d}"
    r = gi(1, "issue-view", "9")
    assert r.out == "", r.out
    assert "partial or unreadable sub-issue list" in r.err, f"issue-view 9, paged: {r.err}"
    r = gi(1, "issue-view", "10")
    assert r.out == "", r.out
    assert "not in snapshot" in r.err, f"issue-view 10 reason: {r.err}"
    assert "not a GitHub issue key" in gi(1, "issue-view", "ENG-1").err
    for k in ("82", "#82", "gh82", "https://github.com/o/r/issues/82"):
        assert gi(0, "lane-key", k).out == "gh82", f"lane-key {k}"
    r = gi(1, "lane-key", "ENG-123")
    assert r.out == "", r.out
    assert "not a GitHub issue number" in r.err, r.err
    for b in ("gh82", "lanes/gh82", "gh82-fix", "implementer-gh82", "gh82-gh97"):
        assert gi(0, "key-from-branch", b).out == "82", f"key-from-branch {b}"
    assert "names no GitHub issue" in gi(1, "key-from-branch", "main").err
    assert gi(0, "pr-line", "82").out == "Closes #82"
    # The offline gh is read-only: each write exits non-zero with its refusal, printing nothing.
    body = s.root / "body"
    body.write_text("hi\n")
    for a in (
        ("issue-create", "--title", "T", "--body-file", str(body)),
        ("issue-comment", "7", "--body-file", str(body)),
        ("issue-done", "7"),
    ):
        r = gi(1, *a)
        assert r.out == "", f"{a[0]} refusal printed: {r.out}"
        assert "read-only snapshot" in r.err, f"{a[0]} refusal: {r.err}"
    writes(s, t, body)


def writes(s: Scratch, t: Path, body: Path) -> None:
    """The writes against testkit's fake gh, holding issues 3 to 7 (6 closed) and 11, the last."""
    for n, state in ((3, "OPEN"), (4, "OPEN"), (5, "OPEN"), (6, "CLOSED"), (7, "OPEN"), (11, "OPEN")):
        s.gh.store(f"issue/{n}.json", {"number": n, "title": f"Issue {n}", "state": state})

    def gi(script: str, *a: str, stdin: str | None = None) -> Ran:
        return s.run([str(GI / script), *a], cwd=t, stdin=stdin)

    r = gi(
        "issue-create",
        *("--title", "New one", "--body-file", str(body), "--parent", "#3"),
        *("--blocked-by", "4", "--blocked-by", "5"),
    )
    assert r.out == "12", f"issue-create: {r.out}"
    want = f"issue create --title New one --body-file {body} --parent 3 --blocked-by 4,5"
    assert s.gh.log()[-1] == want, f"issue-create's gh call: {s.gh.log()}"
    new = json.loads((s.gh.dir / "issue" / "12.json").read_text())
    assert [new["title"], new["body"]] == ["New one", "hi\n"], f"issue 12 as filed: {new}"
    r = gi("issue-comment", "7", stdin="a note\n")
    assert r.out == "https://github.com/o/r/issues/7#issuecomment-1001", r.out
    assert s.gh.log()[-1] == "issue comment 7 --body-file -", s.gh.log()
    i7 = json.loads((s.gh.dir / "issue" / "7.json").read_text())
    assert [c["body"] for c in i7["comments"]] == ["a note\n"], f"issue 7's comments: {i7}"
    r = gi("issue-done", "7")
    assert (r.out, r.err) == ("", ""), f"issue-done 7 printed: {r}"
    assert s.gh.log()[-1] == "issue close 7", s.gh.log()
    i7 = json.loads((s.gh.dir / "issue" / "7.json").read_text())
    assert i7["state"] == "CLOSED", f"issue-done left 7 {i7['state']}"
    r = gi("issue-done", "6")
    assert (r.out, r.err) == ("", ""), f"issue-done on a closed issue printed: {r}"
    assert s.gh.log()[-1] == "issue close 6", s.gh.log()


STORE = {
    "workspace": "acme",
    "issues": {
        "ENG-3": {
            "title": "Parent",
            "description": "p",
            "state": "In Progress",
            "parent": None,
            "blocked_by": [],
        },
        "ENG-4": {"title": "B4", "description": "b", "state": "Todo", "parent": None, "blocked_by": []},
        "ENG-5": {"title": "B5", "description": "b", "state": "Todo", "parent": None, "blocked_by": []},
        "ENG-7": {
            "title": "Issue 7",
            "description": "body 7",
            "state": "Todo",
            "parent": "ENG-3",
            "blocked_by": ["ENG-4", "ENG-5"],
        },
        "ENG-8": {
            "title": "Issue 8",
            "description": None,
            "state": "Canceled",
            "parent": None,
            "blocked_by": [],
        },
    },
}


def linear(s: Scratch) -> None:
    """linear's scripts through the offline fake linear: a store with ENG-7 (parent ENG-3,
    blocked by ENG-4 and ENG-5) and ENG-8 canceled; then the fake's own api and refusals."""
    t = target(s)
    store = s.root / "store.json"
    store.write_text(json.dumps(STORE))
    env = {"PATH": f"{LI}:{s.env['PATH']}", "OCTO_FEATHER_LINEAR_STORE": str(store)}

    def li(want: int, script: str, *a: str, stdin: str | None = None) -> Ran:
        return s.run([str(LI / script), *a], want=want, cwd=t, env=env, stdin=stdin)

    def held() -> dict[str, dict[str, object]]:
        return json.loads(store.read_text())["issues"]

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
    assert [d["key"], d["body"], d["state"], d["parent"], d["blocked_by"]] == [
        "ENG-8",
        "",
        "done",
        None,
        [],
    ], f"linear issue-view eng-8: {d}"
    # The same shape as github-issues' issue-view: the same keys, keys as strings.
    assert sorted(d) == [
        "blocked_by",
        "body",
        "children",
        "key",
        "parent",
        "state",
        "title",
        "url",
    ], d
    r = li(1, "issue-view", "ENG-9")
    assert r.out == "", r.out
    assert "Entity not found" in r.err, r.err
    assert "not a Linear issue key" in li(1, "issue-view", "82").err
    for k in ("ENG-123", "eng-123", "https://linear.app/acme/issue/ENG-123/some-title"):
        assert li(0, "lane-key", k).out == "eng-123", f"lane-key {k}"
    r = li(1, "lane-key", "82")
    assert r.out == "", r.out
    assert "not a Linear issue key" in r.err, r.err
    for b in ("eng-123", "lanes/eng-123", "eng-123-fix", "implementer-eng-123", "code-reviewer-eng-123"):
        assert li(0, "key-from-branch", b).out == "ENG-123", f"linear key-from-branch {b}"
    assert "names no Linear issue" in li(1, "key-from-branch", "main").err
    assert li(0, "pr-line", "eng-123").out == "Tracks ENG-123"
    # Writes go to the fake's store and print what github-issues prints: the key, the url, nothing.
    body = s.root / "body"
    body.write_text("hi\n")
    new = ("--title", "New one", "--body-file", str(body), "--parent", "eng-3")
    assert li(0, "issue-create", *new, "--blocked-by", "ENG-4", "--blocked-by", "ENG-5").out == "ENG-9"
    d = json.loads(li(0, "issue-view", "ENG-9").out)
    assert [d["title"], d["body"], d["state"], d["parent"], d["blocked_by"]] == [
        "New one",
        "hi\n",
        "open",
        "ENG-3",
        ["ENG-4", "ENG-5"],
    ], f"linear new ENG-9: {d}"
    r = li(1, "issue-create", "--title", "T", "--body-file", str(body))
    assert r.out == "", r.out
    assert "No team given" in r.err, r.err
    r = li(1, "issue-create", "--title", "T", "--body-file", str(body), "--parent", "ENG-3", "--blocked-by", "ENG-99")
    assert r.out == "", r.out
    assert "filed ENG-10, but marking it blocked by ENG-99 failed" in r.err, r.err
    r = li(0, "issue-comment", "ENG-7", stdin="a note\n")
    assert r.out == "https://linear.app/acme/issue/ENG-7/issue-7#comment-c1", r.out
    assert held()["ENG-7"]["comments"] == [{"id": "c1", "body": "a note\n"}], held()["ENG-7"]
    assert li(0, "issue-comment", "ENG-7", "--body-file", str(body)).out.endswith("#comment-c2")
    for _ in range(2):  # the second on an issue already done
        r = li(0, "issue-done", "ENG-7")
        assert (r.out, r.err) == ("", ""), f"linear issue-done ENG-7 printed: {r}"
        assert held()["ENG-7"]["state"] == "Done", "issue-done did not move ENG-7 to Done"
        assert json.loads(li(0, "issue-view", "ENG-7").out)["state"] == "done"
    assert "not found" in li(1, "issue-done", "ENG-99").err
    # An issue already done stays as it is: Canceled is done, so issue-done leaves it Canceled.
    r = li(0, "issue-done", "ENG-8")
    assert (r.out, r.err) == ("", ""), f"linear issue-done ENG-8 printed: {r}"
    assert held()["ENG-8"]["state"] == "Canceled", f"issue-done moved canceled ENG-8: {held()}"
    api(s, env)


def api(s: Scratch, env: dict[str, str]) -> None:
    """The fake's api answers any query document as Linear's GraphQL API does: any operation name
    or none, only the fields selected (nested, aliased, connections paged by first), a field
    outside Linear's schema refused by name; every other command refused; no store, no answer."""

    def fapi(want: int, *a: str) -> str:
        r = s.run([str(LI / "linear"), "api", "--no-input", *a], want=want, env=env)
        return r.out + r.err

    for doc in (
        "query ReadTicket($id: String!) { issue(id: $id) { identifier title } }",
        "query($id: String!) { issue(id: $id) { identifier title } }",
        "{ issue(id: $id) { identifier title } }",
    ):
        got = json.loads(fapi(0, "--variable", "id=ENG-3", doc))
        assert got == {"data": {"issue": {"identifier": "ENG-3", "title": "Parent"}}}, (doc, got)
    got = json.loads(fapi(0, 'query Lean { issue(id: "ENG-9") { identifier } }'))
    assert got == {"data": {"issue": {"identifier": "ENG-9"}}}, f"only the selected fields: {got}"
    doc = (
        '{ issue(id: "ENG-9") { key: identifier state { type name } parent { identifier title }\n'
        "  children(first: 1) { nodes { identifier } pageInfo { hasNextPage } }"
        " inverseRelations { nodes { type issue { identifier } } } } }"
    )
    blocks = [{"type": "blocks", "issue": {"identifier": f"ENG-{n}"}} for n in (4, 5)]
    assert json.loads(fapi(0, doc)) == {
        "data": {
            "issue": {
                "key": "ENG-9",
                "state": {"type": "unstarted", "name": "Todo"},
                "parent": {"identifier": "ENG-3", "title": "Parent"},
                "children": {"nodes": [], "pageInfo": {"hasNextPage": False}},
                "inverseRelations": {"nodes": blocks},
            }
        }
    }, "fake linear api, nested and aliased selection"
    doc = '{ issue(id: "ENG-3") { children(first: 1) { nodes { identifier } pageInfo { hasNextPage } } } }'
    assert json.loads(fapi(0, doc))["data"]["issue"]["children"] == {
        "nodes": [{"identifier": "ENG-7"}],
        "pageInfo": {"hasNextPage": True},
    }, "fake linear api pages children by first"
    out = fapi(2, '{ issue(id: "ENG-3") { identifier bogus } }')
    assert 'linear (offline fake): api: Cannot query field "bogus" on type "Issue"' in out, out
    out = fapi(2, '{ issue(id: "ENG-3") { state { colour } } }')
    assert 'Cannot query field "colour" on type "WorkflowState"' in out, out
    out = fapi(2, '{ issue(id: "ENG-3") { state } }')
    assert 'Field "state" of type "WorkflowState!" must have a selection of subfields' in out, out
    for c in (
        "issue list",
        "issue view ENG-7",
        "issue delete ENG-7",
        "api query{viewer{id}}",
        "issue update ENG-7 --label x",
    ):
        r = s.run([str(LI / "linear"), *c.split()], want=2, env=env)
        assert "linear (offline fake)" in r.out + r.err, f"fake linear {c}: {r}"
    r = s.run([str(LI / "issue-view"), "ENG-7"], want=1, env={"PATH": env["PATH"]})
    assert "OCTO_FEATHER_LINEAR_STORE is unset" in r.out + r.err, r


if __name__ == "__main__":
    main(skills, checked, github, linear)
