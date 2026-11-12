"""The scenarios of tests/gate/kit/test_lane_merge_ask.py (its items), this file their command
(testkit.main): scripts/octo-feather-lane verdict, fields and merge-ask (spec issue-lifecycle
#acceptance-merge-ask-evidence, issue #48), no network. Each scenario builds its own lane: a real
git repo whose origin/main is B, the lane's code commit J (the judged head, its full gate pass
recorded by octo-feather-gate) and qc's status commit H (PR #7's head), and PR #7 of o/r in the
fake gh (testkit/gh.py), the only stand-in. `verdict` creates the one marker comment, updates it
in place, and refuses a wrong head, a report with no verdict or no check classes (docs/adr/0008),
a proxy check with a clear verdict and a failed write, leaving no comment behind. `merge-ask`
passes a complete section and prints it with each row's decision source (quality
#acceptance-qc-fallback), also through the qc judge's offline gh; fails PR #16's real body
(fixture) naming each missing item, and each single gap: the parent line (spec
#acceptance-pr-tracks), a stale head, a failing, pending or unreported check (rule: --help,
merge-ask Checks line), rows, Built against the status file and the qc commits, the verdict
link, an untriaged fail. One judged head (spec #acceptance-one-head): qc's status commit and a
clean main merge keep the verdict with the check's proof line; anything else fails naming it.
Full pass (#acceptance-merge-ask-full-proof), gate time (#acceptance-merge-ask-gate-budget,
shown only), skipped checks (#acceptance-ci-status-only, the rule: #lanes-one-head), a lane that
builds no criterion, and a PR of 101 commits.
"""

from __future__ import annotations

import copy
import json
import re
import shutil
from typing import TYPE_CHECKING, Any, cast

from testkit import ROOT, Ran, Scratch, fixture, kit, main

if TYPE_CHECKING:
    from collections.abc import Callable

    Edit = Callable[[dict[str, Any]], object]

L = kit("octo-feather-lane")
G = kit("octo-feather-gate")
OTHER = "ffee" * 10
# What the fake gh serves keeps GitHub's documented shapes, trimmed to the fields merge-ask reads:
# `gh pr view --json` statusCheckRollup (CheckRun and StatusContext nodes, GraphQL), comments,
# commits; REST: git/trees (docs.github.com/en/rest/git/trees#get-a-tree), branches/BRANCH
# (/rest/branches/branches#get-a-branch: protection.required_status_checks), rules/branches/BRANCH
# (/rest/repos/rules#get-rules-for-a-branch), commits/REF/check-runs
# (/rest/checks/runs#list-check-runs-for-a-git-reference). gh's errors: `gh: <message> (HTTP
# <status>)` on stderr, exit 1; the plan's 403 message as octo-feather-lane NO_RULESETS records it.
API = "api/repos/{owner}/{repo}"
CHECK_OK = [
    {"__typename": "CheckRun", "name": "check", "status": "COMPLETED", "conclusion": "SUCCESS"},
    {"__typename": "StatusContext", "context": "ci/x", "state": "SUCCESS"},
]
UNPROTECTED: dict[str, object] = {
    "name": "main",
    "protected": False,
    "protection": {
        "enabled": False,
        "required_status_checks": {"enforcement_level": "off", "contexts": [], "checks": []},
    },
}
REPORT = "Findings: none blocking.\nChecks: none\nVerdict: clear\n"
REPORT2 = "Note: a nit.\nChecks: none\nVerdict: blocking\n"
HDR = "| criterion | qc verdict | judged | evidence |\n|---|---|---|---|"
STATUS = "docs/specs/demo.status.json"
ONLY = f"change only {STATUS}"
AGE = re.compile(r"\(([0-9]+d)?([0-9]+h)?[0-9]+m ago\)")
GATE = re.compile(r"^Gate time \(.*?(?=^$|\Z)", re.MULTILINE | re.DOTALL)
ERR502 = "gh: Server Error (HTTP 502)"


# --- edits of a PR as the fake gh holds it ---


def check(i: int, **kv: str) -> Edit:
    """The rollup's check I updated with KV."""
    return lambda d: d["statusCheckRollup"][i].update(kv)


SKIPPED = check(0, conclusion="SKIPPED")
FAILURE = check(0, conclusion="FAILURE")


def no_checks(d: dict[str, Any]) -> None:
    d["statusCheckRollup"] = []


def branch(name: str) -> Edit:
    return lambda d: d.update(headRefName=name)


def pr_head(sha: str, subject: str) -> Edit:
    """SHA the PR head, a commit of the PR."""

    def edit(d: dict[str, Any]) -> None:
        d["headRefOid"] = sha
        d["commits"].append({"oid": sha, "messageHeadline": subject, "messageBody": ""})

    return edit


def verdict_says(old: str, new: str) -> Edit:
    """The verdict comment's body with OLD replaced by NEW."""

    def edit(d: dict[str, Any]) -> None:
        c = d["comments"][0]
        c["body"] = c["body"].replace(old, new)

    return edit


class Lane:
    """The lane worktree R (B, J, H; `on` adds a commit off any of them) and PR #7 in the fake
    gh, `keep` its state with the clear verdict comment at `url`, each case a copy of it. Built
    once per gate run (testkit Scratch.prepare) and copied into each item: `pr8` the variant
    whose PR #7 holds no comment and PR #8 its own (Pr8)."""

    def __init__(self, s: Scratch, *, pr8: bool = False) -> None:
        self.attach(s)
        name = "lane-merge-ask-pr8" if pr8 else "lane-merge-ask"
        s.prepare(name, lambda p: Lane.__new__(Lane).build(p, pr8=pr8))
        heads = json.loads((self.t / "lane.json").read_text())
        self.b, self.j, self.h, self.url = heads["b"], heads["j"], heads["h"], heads["url"]
        self.heads = heads
        self.keep: dict[str, Any] = self.pr(7)
        self.js = self.j[:7]
        self.proof = f"{self.j[:12]} to {self.h[:12]}: qc status commits {self.h[:12]} {ONLY}"
        self.report = str(self.t / "report")

    def attach(self, s: Scratch) -> None:
        self.s, self.t, self.r = s, s.root, s.root / "repo"
        s.env.pop("HERDR_SESSION", None)
        s.env["XDG_STATE_HOME"] = str(self.t / "xdg")  # the state dir's check-runs.jsonl
        s.env["OCTO_FEATHER_QC_DIR"] = str(self.t / "qc")  # qc reports (octo-feather-qc --help)

    def build(self, s: Scratch, *, pr8: bool) -> None:
        """The lane in S, its heads in lane.json: B, J (its full pass recorded), H, PR #7 with
        the clear verdict on J; with PR8, PR #7 with no comment and PR #8 at N with its own."""
        self.attach(s)
        (self.r / "docs" / "specs").mkdir(parents=True)
        self.git("init", "-q", "-b", "main", ".")
        self.status("planned", "null")
        self.write("app.py", "".join(f"{i}\n" for i in range(1, 21)))
        self.write("notes.txt", "notes\n")
        self.write(
            "gate-budget.toml", "budget_seconds = 150\ngrowth_share = 0.25\ntrend_runs = 3\n"
        )
        self.write("qc.toml", '[demo."demo#acceptance-a"]\ncommand = "true"\n')  # a demo for a only
        other = {"acceptance-x": {"status": "built", "pr": 7}}
        spec = {"spec": "other.spec.html", "accepted_commit": "0123abc", "criteria": other}
        self.write("docs/specs/other.status.json", json.dumps(spec) + "\n")
        b = self.commit("base")
        self.main(b)
        self.git("checkout", "-q", "-b", "lane")
        self.line(1, "one")
        j = self.commit("feat: x")
        self.record()
        self.status("built", "7")
        qc = f"qc: built acceptance-a acceptance-b (judged {j[:12]})"
        h = self.commit(qc)
        pr7 = {
            "number": 7,
            "baseRefName": "main",
            "headRefName": "gh6",
            "headRefOid": h,
            "body": "",
            "statusCheckRollup": CHECK_OK,
            "comments": [],
            "commits": [
                {"oid": j, "messageHeadline": "feat: x", "messageBody": ""},
                {"oid": h, "messageHeadline": qc, "messageBody": ""},
            ],
        }
        s.gh.put(7, pr7)
        self.ci(h, workflows=True)
        s.gh.store(f"{API}/branches/main.json", UNPROTECTED)
        s.gh.store(f"{API}/rules/branches/main.json", [])
        report = self.file("report", REPORT)
        heads = {"b": b, "j": j, "h": h, "url": ""}
        if pr8:
            heads |= Pr8.build(self, b, report)
        else:
            heads["url"] = self.lane("verdict", "7", j, report).out
        (self.t / "lane.json").write_text(json.dumps(heads))

    # --- the repo ---
    def git(self, *args: str, want: int = 0) -> str:
        ident = [
            "-c",
            "user.email=t@example.com",
            "-c",
            "user.name=t",
            "-c",
            "commit.gpgsign=false",
        ]
        return self.s.run(["git", *ident, *args], cwd=self.r, want=want).out

    def write(self, rel: str, text: str) -> None:
        (self.r / rel).write_text(text)

    def line(self, n: int, text: str) -> None:
        """app.py's line N set to TEXT."""
        p = self.r / "app.py"
        lines = p.read_text().splitlines()
        lines[n - 1] = text
        p.write_text("\n".join(lines) + "\n")

    def status(self, st: str, pr: str) -> None:
        self.write(
            STATUS,
            '{"spec": "demo.spec.html", "accepted_commit": "0123abc", "criteria": {\n'
            f'  "acceptance-a": {{"status": "{st}", "pr": {pr}}}, '
            f'"acceptance-b": {{"status": "{st}", "pr": {pr}}},\n'
            '  "acceptance-c": {"status": "planned", "pr": null}, '
            '"acceptance-d": {"status": "built", "pr": 3}}}\n',
        )

    def commit(self, msg: str, *, empty: bool = False) -> str:
        self.git("add", "-A")
        self.git("commit", "-q", *(["--allow-empty"] if empty else []), "-m", msg)
        return self.git("rev-parse", "HEAD")

    def main(self, sha: str) -> None:
        self.git("update-ref", "refs/remotes/origin/main", sha)

    def record(self) -> None:
        """The checkout's full gate pass, recorded."""
        self.s.run([G, "record", "--reason", "lane final head", "--seconds", "1"], cwd=self.r)

    def on(self, parent: str, make: Callable[[], object]) -> str:
        """MAKE run on a detached checkout of PARENT; the new HEAD, back on the lane."""
        self.git("checkout", "-q", "--detach", parent)
        make()
        sha = self.git("rev-parse", "HEAD")
        self.git("checkout", "-q", "-f", "lane")
        return sha

    def change(self, parent: str, msg: str, rel: str = "app.py", text: str = "two") -> str:
        """A commit MSG off PARENT appending the line TEXT to REL."""

        def make() -> None:
            with (self.r / rel).open("a") as f:
                f.write(text + "\n")
            self.commit(msg)

        return self.on(parent, make)

    def empty(self, parent: str, msg: str) -> str:
        return self.on(parent, lambda: self.commit(msg, empty=True))

    def merge(self, parent: str, other: str) -> str:
        return self.on(parent, lambda: self.git("merge", "-q", "--no-edit", other))

    # --- the fake gh and the commands ---
    def file(self, name: str, text: str) -> str:
        p = self.t / name
        p.write_text(text)
        return str(p)

    def ci(self, sha: str, *, workflows: bool) -> None:
        """The head SHA's tree in the fake gh: .github/workflows/check.yml, or no .github."""
        trees = {
            sha: [("app.py", "blob", "x")] + ([(".github", "tree", "g")] if workflows else []),
            "g": [("workflows", "tree", "w")],
            "w": [("check.yml", "blob", "b")],
        }
        for k, v in trees.items():
            entries = [{"path": p, "type": t, "sha": x} for p, t, x in v]
            self.s.gh.store(f"{API}/git/trees/{k}.json", {"sha": k, "tree": entries})

    def fail(self, path: str, err: str = ERR502) -> None:
        """gh failing on PATH (testkit/gh.py: api/PATH.err)."""
        self.s.gh.store(f"{API}/{path}.err", err)

    def heal(self, path: str) -> None:
        (self.s.gh.dir / f"{API}/{path}.err").unlink()

    def runs(self, sha: str, runs: list[dict[str, object]]) -> None:
        """SHA's check runs (REST check-runs API)."""
        page = {"total_count": len(runs), "check_runs": runs}
        self.s.gh.store(f"{API}/commits/{sha}/check-runs?per_page=100.json", page)

    def writes(self) -> int:
        """The fake gh's writes so far (a GET carries no -X)."""
        return sum(ln.startswith("api -X ") for ln in self.s.gh.log())

    def pr(self, n: int) -> dict[str, Any]:
        """PR N as the fake gh holds it."""
        return cast("dict[str, Any]", self.s.gh.pr(n))

    def comments(self, n: int = 7) -> list[dict[str, Any]]:
        return self.pr(n)["comments"]

    def lane(
        self, *args: str, want: int = 0, env: dict[str, str] | None = None, stdin: str | None = None
    ) -> Ran:
        return self.s.run([L, *args], want=want, cwd=self.r, env=env, stdin=stdin)

    def ask(self, *extra: str, want: int = 0, env: dict[str, str] | None = None) -> Ran:
        return self.lane("merge-ask", "7", "--status", STATUS, *extra, want=want, env=env)

    def rows(self, a: str, b: str = "", extra: str = "") -> str:
        """Rows a and b judged at A (b at B when given), evidence r, then EXTRA."""
        return (
            f"| demo#acceptance-a | pass | judged {a} | r |\n"
            f"| demo#acceptance-b | pass | judged {b or a} | r |{extra}"
        )

    def body(self, **o: str) -> str:
        """The complete section, a line overridden by each of O: parent head judged rows review
        built failed."""
        ev = "qc report a1b2.json, cmd ok"
        rows = (
            f"| demo#acceptance-a | pass | judged {self.js} | {ev} |\n"
            f"| acceptance-b | pass | judged {self.js} | {ev} |"
        )
        return (
            f"{o.get('parent', 'Closes #6')}\n\n## Summary\n\nLane work.\n\n## Merge ask\n\n"
            f"Head: {o.get('head', self.h[:12])}\n"
            f"Checks: check, ci/x pass on {self.h[:12]}\n"
            f"Judged: {o.get('judged', self.proof)}\n"
            f"{HDR}\n{o.get('rows', rows)}\n"
            f"Review verdict: {o.get('review', self.url)}\n"
            f"Built: {o.get('built', 'demo#acceptance-a acceptance-b')}\n"
            f"{o.get('failed', 'Failed: none')}\n\n## Notes\n\nafter the section\n"
        )

    def setpr(self, *edits: Edit, **o: str) -> None:
        """PR #7 as kept, its body body(**O), EDITS applied."""
        d = copy.deepcopy(self.keep)
        d["body"] = self.body(**o)
        for e in edits:
            e(d)
        self.s.gh.put(7, d)

    def bad(self, want: str, *edits: Edit, regex: bool = False, **o: str) -> Ran:
        """merge-ask exits 1 naming WANT (a regex with REGEX), nothing on stdout."""
        self.setpr(*edits, **o)
        r = self.ask(want=1)
        said = re.search(want, r.err, re.MULTILINE) if regex else want in r.err
        assert said, f"merge-ask did not say {want!r}: {r.err}"
        assert not r.out, f"a failing merge ask printed to stdout: {r.out}"
        return r

    def at(self, sha: str, subject: str) -> tuple[list[Edit], dict[str, str]]:
        """PR #7 at SHA, a commit SUBJECT the review and qc judged in its place: the edits and
        the body lines."""
        edits = [pr_head(sha, subject), verdict_says(f"Head: {self.j}", f"Head: {sha}")]
        lines = {
            "head": sha[:12],
            "judged": f"{sha[:12]} is the PR head",
            "rows": self.rows(sha[:9]),
        }
        return edits, lines


def first(r: Ran) -> str:
    return r.out.splitlines()[0]


def section(out: str) -> list[str]:
    """merge-ask's output before its gate time block (which comes last)."""
    return out.split("\nGate time (", 1)[0].splitlines()


def proof_line(err: str) -> str:
    m = re.search(r"add the check.s proof line `Judged: (.*)`$", err, re.MULTILINE)
    assert m, f"no proof line: {err}"
    return m.group(1)


# --- verdict ---


def verdict_posts(s: Scratch) -> None:
    """verdict creates the one marker comment, updates it in place, reads stdin, and an
    unchanged rerun writes nothing."""
    ln = Lane(s)
    j, h = ln.j, ln.h
    s.gh.put(7, {**ln.keep, "comments": []})
    (s.gh.dir / "log").write_text("")
    url = ln.lane("verdict", "7", ln.js, ln.report).out  # the review judged J, while qc made H
    assert url == "https://github.com/o/r/pull/7#issuecomment-1001", url
    post = "api -X POST repos/{owner}/{repo}/issues/7/comments "
    assert any(x.startswith(post) for x in s.gh.log()), s.gh.log()
    assert len(ln.comments()) == 1
    r = ln.lane("verdict", "7", j, ln.file("report2", REPORT2))
    assert r.out == url, r.out
    assert len(ln.comments()) == 1, "rerun did not update in place"
    patch = "api -X PATCH repos/{owner}/{repo}/issues/comments/1001 "
    assert any(x.startswith(patch) for x in s.gh.log()), s.gh.log()
    b = ln.comments()[0]["body"]
    assert b.startswith("<!-- octo-feather-review-verdict -->"), b
    assert f"Head: {j}\nPR head: {h}\n" in b, b
    assert "Verdict: blocking\n" in b, b
    assert "a nit" in b, b
    ln.lane("verdict", "7", j, "-", stdin=REPORT)  # stdin, back to clear
    assert ln.writes() == 3, s.gh.log()
    assert len(ln.comments()) == 1
    r = ln.lane("verdict", "7", j, ln.report)
    assert ln.writes() == 3, "unchanged rerun wrote"
    assert "unchanged" in r.err, r.err


def verdict_reader_scope(s: Scratch) -> None:
    """The verdict is the last line in the reader scope (.agents/skills/code-review/SKILL.md step
    4 Report fields): fenced and quoted lines aside (#144, #121 D10, PR #140); a proxy check posts
    only with a blocking verdict, in the header."""
    ln = Lane(s)

    def said(text: str, verdict: str) -> str:
        """The report TEXT posted (a write) with VERDICT: the comment's body."""
        log = len(s.gh.log())
        r = ln.lane("verdict", "7", ln.j, ln.file("r", text))
        assert f"({verdict}, head" in r.err, f"{text}: {r.err}"
        assert any(x.startswith("api -X PATCH") for x in s.gh.log()[log:]), f"{text}: not posted"
        return ln.comments()[0]["body"]

    fenced = (
        "Ran the gate:\n```\nVerdict: clear\n```\n> Verdict: clear\n\n"
        "The quoted run predates the fix commit.\nChecks: none\nVerdict: blocking\n"
    )
    b = said(fenced, "blocking")
    assert "\nVerdict: blocking\nChecks: none\n\n### Findings" in b, b
    said("> the implementer wrote:\n\nVerdict: blocking\nChecks: none\n", "blocking")
    said("> > nested:\n~~~\nVerdict: clear\n~~~\nChecks: none\nVerdict: blocking\n", "blocking")
    said("    ```\n\nVerdict: clear\nChecks: none\n", "clear")  # 4-space indented backticks
    said("- item\n  > quote\n    ```\nVerdict: clear\nChecks: none\n", "clear")
    rule = "tests reach no internals (docs/adr/0002)"
    reads = "reads: code tokens in tests/*.sh"
    b = said(
        f"Check: `scripts/check-x`: {rule} | {reads} | class: Proxy\nVerdict: blocking\n",
        "blocking",
    )
    want = f"Check: scripts/check-x: {rule} | {reads} | class: proxy\n\n### Findings"
    want = f"\nVerdict: blocking\n{want}"
    assert want in b, f"proxy check not in the verdict header: {b}"


def verdict_refusals(s: Scratch) -> None:
    """Each refusal exits 1 naming its fix and writes nothing."""
    ln = Lane(s)
    j, h = ln.j, ln.h
    n = ln.writes()

    def no(want: str, *args: str, regex: bool = False) -> None:
        r = ln.lane("verdict", "7", *args, want=1)
        said = re.search(want, r.err) if regex else want in r.err
        assert said, f"{args}: want {want!r}: {r.err}"

    def report(text: str, want: str, *, regex: bool = False) -> None:
        no(want, j, ln.file("r", text), regex=regex)

    no(f"is not a commit of PR #7 (head {h[:12]}): push the reviewed head", OTHER, ln.report)
    report("looks fine\n", "add a line `Verdict: clear`")
    lazy = ("> the implementer wrote:", "> > nested, quoted:", "> - a quoted item")
    for q in (*lazy, ">     quoted code\n> the reply"):  # D10: lazy continuation lines
        report(q + "\nVerdict: clear\nChecks: none\n", "report names no verdict")
    report("Verdict: clear\n> quoted:\nChecks: none\n", "report classifies no check")
    both = "verdicts that disagree (clear, blocking): keep one"
    report("Verdict: clear\nmore\nVerdict: blocking\n", both)
    nocls = "report classifies no check: add `Checks: none` when"
    report("Verdict: clear\n```\nChecks: none\n```\n", nocls)  # the fenced one ignored
    proxy = "Check: scripts/check-x: tests reach no internals (docs/adr/0002) | reads: code tokens"
    blocks = (
        r"with a proxy check \(Check: scripts/check-x: .*\): a proxy check blocks \(docs/adr/0008\)"
    )
    report(f"{proxy} | class: proxy\nVerdict: clear\n", blocks, regex=True)
    meaning = "Check: scripts/check-x: r (ADR 1) | reads: y | class: meaning\nVerdict: blocking\n"
    report(meaning, "has class 'meaning'; write `class: exact` or `class: proxy`")
    shape = "check line `Check: scripts/check-x is a fact` is not `Check: <path>"
    report("Check: scripts/check-x is a fact\nVerdict: clear\n", shape)
    owner = "check line for scripts/x names no owner: write its rule as stated where it is owned"
    for rule in ("r", "r ()", "r (  )", "(ADR 1)"):  # the rule names its owner (review of 2e1a0da)
        report(f"Check: scripts/x: {rule} | reads: y | class: exact\nVerdict: clear\n", owner)
    report("Checks: fine\nVerdict: clear\n", "`Checks: fine`; `Checks:` takes only `none`")
    exact = "Check: scripts/check-x: r (ADR 1) | reads: y | class: exact"
    report(f"Checks: none\n{exact}\nVerdict: clear\n", "has `Checks: none` and `Check:` lines")
    no("cannot read report", j, str(ln.t / "missing"))
    no("is empty", j, ln.file("empty", ""))
    no("commit sha", "xyz", ln.report)
    no("usage", j)
    r = ln.lane("verdict", "9", j, ln.report, want=1)
    assert "check PR #9 exists" in r.err, r.err
    assert ln.writes() == n, "a refusal wrote"


def verdict_write_fails(s: Scratch) -> None:
    """A failed create leaves no comment; a failed update changes nothing; a failed read names
    the fix; two marker comments are refused, nothing written."""
    ln = Lane(s)
    j, h = ln.j, ln.h
    d = copy.deepcopy(ln.keep)
    d["comments"] = []
    s.gh.put(7, d)
    ln.fail("issues/7/comments")
    r = ln.lane("verdict", "7", j, ln.report, want=1)
    assert re.search(r"was not created; fix the cause.*then rerun", r.err), r.err
    assert ln.comments() == [], "failed create left a comment"
    s.gh.put(7, ln.keep)
    ln.fail("issues/comments/1001")
    r = ln.lane("verdict", "7", j, ln.file("report2", REPORT2), want=1)
    assert "was not updated" in r.err, r.err
    assert "Verdict: clear" in ln.comments()[0]["body"], "failed update changed the comment"
    (s.gh.dir / "down").touch()
    r = ln.lane("verdict", "7", j, ln.report, want=1)
    assert re.search(r"error connecting.*gh auth status", r.err), r.err
    (s.gh.dir / "down").unlink()
    two = copy.deepcopy(ln.keep)
    c = dict(two["comments"][0])
    c["url"] = c["url"][:-4] + "1099"
    two["comments"].append(c)
    s.gh.put(7, two)
    n = ln.writes()
    r = ln.lane("verdict", "7", h, ln.report, want=1)
    assert re.search(r"has 2 verdict comments.*delete all but one", r.err), r.err
    assert ln.writes() == n


def offline_gh(s: Scratch) -> None:
    """The same PR through the qc judge's offline gh (snapshot layout of octo-feather-qc-ghsnap):
    merge-ask passes, verdict refuses to write."""
    ln = Lane(s)
    ln.setpr()
    snap = ln.t / "snap"
    (snap / "pr").mkdir(parents=True)
    (snap / "meta.json").write_text('{"repo": "o/r", "counts": {}, "capped": []}')
    (snap / "fetched_at").write_text("x\n")
    shutil.copy(s.gh.dir / "pr" / "7.json", snap / "pr" / "7.json")
    env = {
        "OCTO_FEATHER_GHSNAP": str(snap),
        "PATH": f"{ROOT / '.agents/skills/github-pr/scripts'}:{s.env['PATH']}",
    }
    assert first(ln.ask(env=env)) == "## Merge ask"
    r = ln.lane("verdict", "7", ln.h, ln.file("report2", REPORT2), want=1, env=env)
    assert "was not updated" in r.err, r.err
    assert "offline read-only snapshot" in r.err, r.err


# --- merge-ask ---


def qc_report(ln: Lane, stamp: str, results: list[tuple[str, str, str]]) -> None:
    """A qc report at J as octo-feather-qc writes it: (id, verdict, decision) per criterion."""
    q = ln.t / "qc"
    q.mkdir(exist_ok=True)
    short = (
        "demo did not run to its end (exit 77, a step it needs could not run here): needs GitHub"
    )

    def res(i: str, v: str, dec: str) -> dict[str, object]:
        r: dict[str, object] = {"id": i, "verdict": v, "evidence": "complete", "decision": dec}
        r |= {"record": "r", "head": ln.j}
        if v == "insufficient evidence":
            r |= {"evidence": "incomplete", "missing": [short]}
        return r

    rep = {"head": ln.j, "spec": "demo", "results": [res(*x) for x in results]}
    (q / f"{ln.j}-{stamp}.json").write_text(json.dumps(rep))


def merge_ask_passes(s: Scratch) -> None:
    """A complete section passes and prints exactly it, the check classes, and each row's
    decision source (quality#acceptance-qc-fallback): none yet, then from a qc report, never
    from qc.toml; merge-ask writes nothing."""
    ln = Lane(s)
    n = ln.writes()
    ln.setpr()
    out = ln.ask().out
    lines = section(out)
    assert lines[0] == "## Merge ask", out
    assert "Failed: none" in lines, out
    classes = "Review check classes (from the verdict comment, docs/adr/0008):"
    assert lines[-2:] == [classes, "- Checks: none"], out
    assert f"Review verdict: {ln.url}" in lines, out
    assert "Notes" not in out, out
    assert "Summary" not in out, out
    src = (
        f"Decision sources (the latest qc result at the judged head {ln.j[:12]}; "
        "quality spec #qc-results):"
    )

    def sources(out: str) -> list[str]:
        i = out.splitlines().index(src)
        return out.splitlines()[i + 1 : i + 3]

    none = "no qc result at the judged head"
    assert sources(out) == [f"- demo#acceptance-a: {none}", f"- demo#acceptance-b: {none}"], out
    tagged = "tagged test assertions"
    a, b = ("acceptance-a", "pass", tagged), ("acceptance-b", "pass", "agent fallback")
    qc_report(ln, "20261029T090000Z-src123", [a, b])
    out = ln.ask().out
    assert sources(out) == [f"- demo#acceptance-a: {tagged}", "- demo#acceptance-b: agent fallback"]
    assert ln.writes() == n, "merge-ask wrote"


def gate_time(s: Scratch) -> None:
    """issue-lifecycle#acceptance-merge-ask-gate-budget: the full gate's wall time on the final
    head (J's run: H adds only qc's status commit) against gate-budget.toml at the head, flagged
    over budget and grown past the share, beside the trend (passed full runs on the head's
    history: B's three; a subset run on H and a red full run on J stay out) and the slowest
    items; no gate on timing: the ask passes, or fails with the same items, as with none."""
    ln = Lane(s)
    j, h, b = ln.j[:12], ln.h[:12], ln.b[:12]
    trend = ln.t / "xdg" / "octo-feather" / "check-runs.jsonl"

    def block(out: str) -> str:
        m = GATE.search(out)
        assert m, out
        return AGE.sub("(AGE ago)", m.group(0).rstrip("\n"))

    head = (
        f"Gate time (the full gate on the final head against gate-budget.toml at {h}; the code "
        "reviewer judges it, no gate reads it: issue-lifecycle #lanes-checkpoints):"
    )
    ln.setpr()
    none_out = ln.ask().out
    assert block(none_out) == f"{head}\n  no gate run recorded ({trend}: none)", none_out
    trend.parent.mkdir(parents=True, exist_ok=True)

    def run(start: str, sha: str, total: float, rc: int = 0, tier: str = "full") -> str:
        steps = [
            {"name": "tests/a.sh", "seconds": int(total) - 30, "result": "ok"},
            {"name": "tests/b.sh", "seconds": 20.5, "result": "ok"},
            {"name": "check-lint", "seconds": 1.0, "result": "ok"},
        ]
        r = {"start": start, "repo": str(ln.r), "head": sha, "total_s": total, "exit": rc}
        return json.dumps(r | {"tier": tier, "steps": steps}) + "\n"

    day = "2026-10-0{}T{}:00:00Z".format
    trend.write_text(
        run(day(1, 10), ln.b, 100)
        + run(day(2, 10), ln.b, 120)
        + run(day(3, 10), ln.b, 110)
        + run(day(4, 10), ln.j, 90, 1)
        + run(day(4, 11), ln.j, 200.5)
        + run(day(4, 12), ln.h, 5, tier="subset")
    )
    out = ln.ask().out
    trend_line = (
        f"100s {b} {day(1, 10)}, 120s {b} {day(2, 10)}, 110s {b} {day(3, 10)}, "
        f"200.5s {j} {day(4, 11)} (passed full runs, oldest first)"
    )
    assert block(out) == (
        f"{head}\n"
        f"  full gate: 200.5s, head {j}, started {day(4, 11)} (AGE ago): "
        "OVER BUDGET by 50.5s (budget 150s)\n"
        "  growth: +82.3% over the trend's median 110s (the 3 passed full runs before it); "
        "set share 25%: GROWN\n"
        f"  trend: {trend_line}\n"
        "  slowest: tests/a.sh 170s, tests/b.sh 20.5s, check-lint 1s"
    ), block(out)
    assert GATE.sub("", out) == GATE.sub("", none_out), f"the gate time changed the ask: {out}"
    # a refusal: the same items with or without the run, the gate time on stderr only
    r = ln.bad(f"  full gate: 200.5s, head {j}", FAILURE)
    items = r.err[r.err.index("merge ask incomplete") :]
    trend.rename(trend.with_suffix(".keep"))
    r = ln.ask(want=1)
    assert r.err[r.err.index("merge ask incomplete") :] == items, (
        f"the gate time changed it: {r.err}"
    )


def failed_triage(s: Scratch) -> None:
    """A failed criterion with triage passes; insufficient evidence (quality spec #qc-results,
    #acceptance-qc-insufficient) is never triaged, from its row or from the latest qc report at
    the judged head, until a rerun gives pass or fail; an untriaged fail and Failed's malformed
    forms fail."""
    ln = Lane(s)
    js, j = ln.js, ln.j
    c_fail = f"\n| demo#acceptance-c | fail | judged {js} | r |"
    why = "Failed:\n- acceptance-c: outside the lane, the spec behaviour is untouched (reason)"
    ln.setpr(failed=why, rows=ln.rows(js, extra=c_fail.replace("| r |", "| r, output x |")))
    assert "- acceptance-c: outside the lane, the spec behaviour is untouched (reason)" in (
        ln.ask().out.splitlines()
    )
    never = (
        "insufficient evidence is never triaged; rerun just qc on it until it gives pass or fail"
    )
    rows = f"| demo#acceptance-a | pass | judged {js} | r |\n"
    rows += f"| demo#acceptance-b | insufficient evidence | judged {js} | r |"
    ln.bad(f"criterion row demo#acceptance-b: {never}", rows=rows)
    a = ("acceptance-a", "pass", "demo checks")
    qc_report(ln, "20261029T100000Z-abc123", [a, ("acceptance-b", "insufficient evidence", "x")])
    ln.bad(
        f"criterion demo#acceptance-b: insufficient evidence at the judged head {j[:12]} (demo did "
        "not run to its end (exit 77, a step it needs could not run here): needs GitHub; qc report "
        f"{j}-20261029T100000Z-abc123.json): never triaged"
    )
    qc_report(ln, "20261029T110000Z-abc123", [a, ("acceptance-b", "pass", "x")])
    ln.setpr()
    ln.ask()  # the rerun at that head gave it pass
    shutil.rmtree(ln.t / "qc")
    ln.bad("criterion row demo#acceptance-c: fail with no triage", rows=ln.rows(js, extra=c_fail))
    ln.bad(
        "Failed: demo#acceptance-c has no triage",
        failed="Failed:\n- acceptance-c:",
        rows=ln.rows(js, extra=c_fail),
    )
    ln.bad(
        "criterion row demo#acceptance-c: missing (it is in Failed)",
        failed="Failed:\n- acceptance-c: repair ticket #9",
    )
    ln.bad("Failed: 'some'; write", failed="Failed: some")


def parent_line(s: Scratch) -> None:
    """The parent line (spec #gates-pr-line): the tracker skill's pr-line for the key the PR
    branch names, and no other line closes an issue: only the parent's own closing link is
    exempt, never the rest of its line; an issue URL closes too. A Linear lane (spec
    #acceptance-pr-tracks): Tracks ENG-123 for branch eng-123, no Closes line."""
    ln = Lane(s)
    gh_parent = "not the lane's parent line `Closes #6`"
    missing = "parent line: missing; add the line"
    ln.bad(f"{missing} `Closes #6` (the tracker skill's pr-line 6)", parent="")
    ln.bad(f"{missing} `Closes #6`", parent="Closes #60")
    also = "parent line: `Also fixes #9` closes GitHub issue #9"
    ln.bad(f"{also}, {gh_parent}", parent="Closes #6\nAlso fixes #9")
    same = "parent line: `Closes #6, fixes #9` closes GitHub issue #9"
    ln.bad(f"{same}, {gh_parent}", parent="Closes #6, fixes #9")
    own = "parent line: `Closes #6 closes o/r#6` closes GitHub issue #6"
    ln.bad(own, parent="Closes #6 closes o/r#6")
    url = "https://github.com/o/r/issues/9"
    ln.bad(
        f"parent line: `Resolves {url}` closes GitHub issue #9", parent=f"Closes #6\nResolves {url}"
    )
    ln.bad("parent line: cannot name it for branch 'main'", branch("main"))
    ln.write(".octo-feather.toml", 'tracker = "linear"\n')
    eng = branch("eng-123")
    ln.setpr(eng, parent="Tracks ENG-123")
    assert first(ln.ask()) == "## Merge ask"
    ln.bad(f"{missing} `Tracks ENG-123` (the tracker skill's pr-line ENG-123)", eng)
    linear = "not the lane's parent line `Tracks ENG-123`"
    closes = "parent line: `Closes #6` closes GitHub issue #6"
    ln.bad(f"{closes}, {linear}", eng, parent="Tracks ENG-123\nCloses #6")
    on_line = "parent line: `Tracks ENG-123; Closes #6` closes GitHub issue #6"
    ln.bad(f"{on_line}, {linear}", eng, parent="Tracks ENG-123; Closes #6")
    ln.bad(f"{missing} `Tracks ENG-123`", eng, parent="Tracks ENG-1234")


def single_gaps(s: Scratch) -> None:
    """PR #16's real body names each missing item; a stale or missing head and each failing,
    pending or unreported check fail, naming it."""
    ln = Lane(s)
    h = ln.h[:12]
    (s.gh.dir / "pr" / "16.json").write_text(fixture("lane-merge-ask/pr16.json"))
    overview = str(ROOT / "docs/specs/overview.status.json")
    r = ln.lane("merge-ask", "16", "--status", overview, want=1)
    for item in (
        (
            "PR commits: PR #16's head f5f90b85a488 is not a commit in this repo: run it in the "
            "lane worktree after git fetch origin"
        ),
        "`## Merge ask` section",
        "Head: missing",
        "Checks: missing",
        "criterion table: missing",
        "Review verdict: missing",
        "Built: missing",
        "Failed: missing",
    ):
        assert f"  - {item}" in r.err, f"PR #16: {item!r} not named: {r.err}"
    ln.bad(f"Head: names {OTHER[:12]}, the PR's head is {h} (stale)", head=OTHER[:12])
    ln.bad("Head: missing", head="")
    ln.bad(f"Checks: failing on head {h}: check failure", FAILURE)
    pending = check(0, status="IN_PROGRESS", conclusion="")
    ln.bad(f"Checks: pending on head {h}: check in_progress", pending)
    ln.bad(f"Checks: pending on head {h}: ci/x pending", check(1, state="PENDING"))
    ln.bad(f"Checks: failing on head {h}: ci/x error", check(1, state="ERROR"))
    wf = "its workflows .github/workflows/check.yml; push the head"
    ln.bad(f"Checks: none reported on head {h}, {wf}", no_checks)


def no_ci(s: Scratch) -> None:
    """No check reported and no workflow file at the head (rule: --help, merge-ask Checks line):
    the base's required-check policy decides, read from GitHub: no check required passes,
    naming both facts; a required check fails naming it."""
    ln = Lane(s)
    h = ln.h
    ln.ci(h, workflows=False)
    k = len(s.gh.log())
    ln.bad(f"Checks: failing on head {h[:12]}: check failure", FAILURE)
    read = [x for x in s.gh.log()[k:] if x.startswith("api ")]
    assert not read, f"a reported check still read the tree: {read}"
    this = "gh api repos/<this repo>"
    tree = f"no workflow file under .github/workflows at head {h[:12]} ({this}/git/trees/{h[:12]})"
    rules = "rules/branches/main"

    def passes(rules_fact: str) -> None:
        out = ln.ask().out
        want = (
            f"Checks: no CI: {tree}; base main requires no check ({this}/branches/main: no "
            f"required status check; {this}/{rules}: {rules_fact}), so required checks are none"
        )
        assert want in out.splitlines(), f"no-CI head did not pass naming both facts: {out}"

    ln.setpr(no_checks)
    k = len(s.gh.log())
    passes("no required_status_checks rule")
    api = "api repos/{owner}/{repo}"
    read = [x for x in s.gh.log()[k:] if x.startswith("api ")]
    assert read == [f"{api}/git/trees/{h}", f"{api}/branches/main", f"{api}/{rules}"], read
    plan = "Upgrade to GitHub Pro or make this repository public to enable this feature."
    plan = f"gh: {plan} (HTTP 403)"
    ln.fail(rules, plan)
    passes("rulesets unavailable on this plan, none in force")
    ln.heal(rules)
    # required checks in branch protection or a ruleset fail naming them; a policy gh cannot read
    # fails closed naming it
    req = {
        "enforcement_level": "everyone",
        "contexts": ["ci/legacy"],
        "checks": [{"context": "build", "app_id": 1}],
    }
    prot = {"protected": True, "protection": {"enabled": True, "required_status_checks": req}}
    s.gh.store(f"{API}/branches/main.json", prot)
    ln.bad(
        f"  - Checks: none reported on head {h[:12]}, no workflow file there ({this}/git/trees/"
        f"{h[:12]}), but base main requires checks build, ci/legacy ({this}/branches/main, "
        f"repos/<this repo>/{rules}): push the head and wait for them",
        no_checks,
    )
    s.gh.store(f"{API}/branches/main.json", UNPROTECTED)
    vercel = {"required_status_checks": [{"context": "vercel"}]}
    ruleset = [{"type": "deletion"}, {"type": "required_status_checks", "parameters": vercel}]
    s.gh.store(f"{API}/{rules}.json", ruleset)
    ln.bad("but base main requires checks vercel (gh api", no_checks)


def no_ci_unread(s: Scratch) -> None:
    """A base policy or a head's tree gh cannot read fails closed, naming the read; the ask still
    lists every item (--help)."""
    ln = Lane(s)
    h = ln.h
    ln.ci(h, workflows=False)
    this = "gh api repos/<this repo>"
    rules = "rules/branches/main"
    fix = "fix gh auth status or read access, then rerun"
    unread = "but the required checks of base main could not be read"
    ln.fail("branches/main")
    ln.bad(f"{unread} ({this}/branches/main: {ERR502}): {fix}", no_checks)
    ln.heal("branches/main")
    s.gh.store(f"{API}/branches/main.json", {"protected": True})
    ln.bad(f"{unread} ({this}/branches/main: no protection.required_status_checks)", no_checks)
    s.gh.store(f"{API}/branches/main.json", UNPROTECTED)
    ln.fail(rules)
    unread = "but the rulesets of base main could not be read"
    ln.bad(f"{unread} ({this}/{rules}: {ERR502}): {fix}", no_checks)
    ln.heal(rules)
    # the head's tree unreadable: that one Checks item fails closed naming the read
    ln.ci(h, workflows=True)
    ln.fail(f"git/trees/{h}")
    r = ln.bad(
        f"\n  - Checks: none reported on head {h[:12]}, and the no-CI fact could not be read "
        f"(gh api repos/{{owner}}/{{repo}}/git/trees/{h} failed ({ERR502})",
        no_checks,
    )
    assert "merge ask incomplete" in r.err, f"an unreadable tree aborted the ask: {r.err}"
    assert r.err.startswith("Gate time"), f"an unreadable tree aborted the ask: {r.err}"


def ci_status_only(s: Scratch) -> None:
    """issue-lifecycle#acceptance-ci-status-only (the rule: #lanes-one-head): check SKIPPED on
    qc's commit H; J's CI carried by the Judged proof, or refused: missing, pending, skipped or
    red on J, no proof, or H the judged head itself (PR #608 at d0e4381)."""
    ln = Lane(s)
    j, h = ln.j, ln.h
    skip = (
        f"Checks: check skipped on head {h[:12]}, carried from the judged head {j[:12]} by the "
        "Judged proof,"
    )

    def run(state: str, conclusion: str | None, i: int = 2) -> dict[str, object]:
        return {"id": i, "name": "check", "status": state, "conclusion": conclusion}

    ln.runs(j, [])
    ln.bad(f"{skip} and {j[:12]} has no check run", SKIPPED)
    ln.runs(j, [run("in_progress", None)])
    ln.bad(f"{skip} and pending on {j[:12]}: check in_progress", SKIPPED)
    ln.runs(j, [run("completed", "failure")])
    ln.bad(f"{skip} and failing on {j[:12]}: check failure", SKIPPED)
    ln.runs(j, [run("completed", "skipped")])  # J's own run skipped (a draft PR)
    ln.bad(f"{skip} and skipped on {j[:12]} too: CI never ran there", SKIPPED)
    # the demo: J's latest check run passed (an earlier one skipped while the PR was a draft)
    ln.runs(j, [run("completed", "success", 3), run("completed", "skipped", 1)])
    ln.setpr(SKIPPED)
    out = ln.ask().out
    carried = f"- check: skipped on {h[:12]}; success on {j[:12]}, the judged head"
    assert carried in out.splitlines(), f"a status-only head did not pass on J's CI: {out}"
    read = f"api repos/{{owner}}/{{repo}}/commits/{j}/check-runs"
    assert any(read in x for x in s.gh.log()), f"J's check runs not read: {s.gh.log()}"
    # a code commit C between J and the status-only head S: no Judged proof, nothing carries
    c = ln.change(h, "fix: y", text="fix")
    sh = ln.empty(c, f"qc: built acceptance-a acceptance-b (judged {j[:12]})")
    r = ln.bad(
        f"Checks: skipped on head {sh[:12]}: check; a skipped check is no pass and no Judged "
        "proof carries",
        SKIPPED,
        pr_head(c, "fix: y"),
        pr_head(sh, "x"),
        head=sh[:12],
    )
    code = f"Judged: commit {c[:12]} 'fix: y' after the judged head {j[:12]} changes app.py"
    assert code in r.err, r.err
    # the judged head is the PR head and its check skipped (a draft's run): refused
    ln.bad(
        f"Checks: skipped on head {j[:12]}: check; a skipped check is no pass",
        SKIPPED,
        lambda d: d.update(headRefOid=j),
        head=j[:12],
        judged=f"{j[:12]} is the PR head",
    )


def rows_and_built(s: Scratch) -> None:
    """Rows against Built, Built against the status files and the PR's `qc: built` commits,
    read from git (BASE..head): each case a real lane head."""
    ln = Lane(s)
    js, j, h = ln.js, ln.j, ln.h
    a = f"| demo#acceptance-a | pass | judged {js} | r |"
    ln.bad("criterion row demo#acceptance-b: missing (it is in Built)", rows=a)
    rows = f"{a}\n| demo#acceptance-b | pass | judged {js} | |"
    ln.bad("criterion row demo#acceptance-b: no evidence", rows=rows)
    ln.bad(
        "qc verdict 'ok'; write pass or fail",
        rows=f"{a}\n| demo#acceptance-b | ok | judged {js} | r |",
    )
    zz = f"\n| demo#acceptance-zz | pass | judged {js} | r |"
    ln.bad("acceptance-zz: no criterion", rows=ln.rows(js, extra=zz))
    ln.bad(
        "Built: lists demo#acceptance-a, the status files hold built with PR #7: "
        "demo#acceptance-a demo#acceptance-b",
        built="demo#acceptance-a",
    )
    # a Built id the status file holds but no qc: built commit names: qc's commit, acceptance-a only
    qa = ln.on(
        h,
        lambda: ln.git(
            "commit", "-q", "--amend", "-m", f"qc: built acceptance-a (judged {j[:12]})"
        ),
    )
    ln.bad(
        "Built: demo#acceptance-b in no `qc: built` commit of PR #7 (they passed acceptance-a); "
        "built only by just qc",
        pr_head(qa, "x"),
        head=qa[:12],
        judged=f"{j[:12]} to {qa[:12]}: qc status commits {qa[:12]} {ONLY}",
    )
    # built by an earlier qc run, reset to planned by a later one (PR #49: ac060f9, a56de61): passes
    q1 = ln.empty(j, "qc: built acceptance-a acceptance-c (judged 0123456789ab)")

    def q2() -> None:
        ln.git("checkout", "-q", h, "--", STATUS)
        ln.commit(f"qc: built acceptance-a acceptance-b (judged {j[:12]})")

    q2_ = ln.on(q1, q2)
    proof = f"{j[:12]} to {q2_[:12]}: qc status commits {q1[:12]} {q2_[:12]} {ONLY}"
    ln.setpr(pr_head(q2_, "x"), head=q2_[:12], judged=proof)
    ln.ask()
    qn = ln.on(h, lambda: ln.git("commit", "-q", "--amend", "-m", "chore: status"))
    ln.bad("no `qc: built` commit on PR #7", pr_head(qn, "x"), head=qn[:12])


def review_link(s: Scratch) -> None:
    """Review verdict: this PR's marker comment, on the judged head, clear, with usable check
    classes (no proxy); its exact check lines listed."""
    ln = Lane(s)
    j = ln.j
    ln.bad("Review verdict: empty is not a comment on PR #7", review="")
    ln.bad("is not a comment on PR #7", review="https://github.com/o/r/pull/8#issuecomment-1001")
    ln.bad("comment 4242 not on PR #7", review=ln.url.removesuffix("1001") + "4242")
    other = verdict_says(f"Head: {j}", f"Head: {OTHER}")
    ln.bad(f"the comment names head {OTHER}, not the judged head {j[:12]}", other)
    ln.bad(
        "Review verdict: blocking, not clear", verdict_says("Verdict: clear", "Verdict: blocking")
    )
    ln.bad(
        "Review verdict: the comment carries no usable check classification (report classifies "
        "no check",
        verdict_says("\nChecks: none\n", "\n"),
    )
    proxy = "Check: scripts/x: r (ADR 1) | reads: y | class: proxy"
    blocks = f"Review verdict: clear with a proxy check ({proxy}): a proxy check blocks"
    ln.bad(blocks, verdict_says("Checks: none", proxy))
    exact = "Check: scripts/x: r (ADR 1) | reads: y | class: exact"
    ln.setpr(verdict_says("Checks: none", exact))
    out = ln.ask().out
    assert section(out)[-1] == f"- {exact}", f"exact check not listed: {out}"
    ln.bad(
        "is not a verdict comment (no marker)",
        lambda d: d["comments"][0].update(body="Verdict: clear"),
    )


def one_judged_head(s: Scratch) -> None:
    """One judged head (spec #acceptance-one-head): review and qc judged J; H may add only qc's
    status commit, with the check's proof; a code commit, a qc commit carrying another file or a
    hand status edit fails naming it; qc rerun at the exact head passes."""
    ln = Lane(s)
    j, h = ln.j, ln.h
    ln.setpr()
    assert f"Judged: {ln.proof}" in ln.ask().out.splitlines()
    ln.bad(f"Judged: names ''; add the check's proof line `Judged: {ln.proof}`", judged="")
    ln.bad("rows name 2 judged heads", rows=ln.rows(ln.js, h[:7]))
    f = ln.change(h, "feat: after qc")
    ln.on(f, ln.record)
    ln.bad(
        f"Judged: commit {f[:12]} 'feat: after qc' after the judged head {j[:12]} changes app.py, "
        f"not only the status file qc writes ({STATUS}): run just qc and the review again, in "
        f"parallel, on {f[:12]}",
        pr_head(f, "feat: after qc"),
        head=f[:12],
    )
    qc = f"qc: built acceptance-a (judged {j[:12]})"

    def stray() -> None:  # qc's own commit carrying a non-status file
        p = ln.r / STATUS
        pa = '"planned", "pr": null}, "acceptance-b'
        p.write_text(p.read_text().replace(pa, '"built", "pr": 7}, "acceptance-b'))
        ln.write("stray.txt", "x\n")
        ln.commit(qc)

    q = ln.on(j, stray)
    after = f"after the judged head {j[:12]}"
    ln.bad(
        f"commit {q[:12]} '{qc}' {after} changes stray.txt, not only", pr_head(q, qc), head=q[:12]
    )
    st = ln.change(h, "fix status", STATUS, " ")
    ln.bad(
        f"commit {st[:12]} 'fix status' {after} is not a `qc: built",
        pr_head(st, "fix status"),
        head=st[:12],
    )
    # qc reran at the exact head, nothing to flip: no status commit, passes
    edits, lines = ln.at(f, "feat: after qc")
    ln.setpr(*edits, **lines)
    ln.ask()


def main_merges(s: Scratch) -> None:
    """A clean main merge keeps the qc verdict, the check printing its proof line; a main merge
    touching a lane file, resolving a conflict, or merging another branch: qc reruns."""
    ln = Lane(s)
    j, h = ln.j, ln.h
    m1 = ln.change(ln.b, "main: notes", "notes.txt", "main")
    ln.main(m1)
    r1 = ln.merge(h, m1)
    r = ln.bad(
        rf"add the check's proof line .Judged: {j[:12]} to {r1[:12]}: qc status commits "
        rf"{h[:12]} {ONLY}; clean merge of main {r1[:12]}: lane diff identical "
        r"\(1 file, sha256 [0-9a-f]{12}\).",
        pr_head(r1, "Merge main"),
        regex=True,
        head=r1[:12],
    )
    proof = proof_line(r.err)
    ln.setpr(pr_head(r1, "Merge main"), head=r1[:12], judged=proof)
    assert f"Judged: {proof}" in ln.ask().out.splitlines()

    def line(n: int, text: str, msg: str) -> Callable[[], object]:
        return lambda: (ln.line(n, text), ln.commit(msg))

    m2 = ln.on(m1, line(20, "twenty", "main: app tail"))
    ln.main(m2)
    r2 = ln.merge(h, m2)
    ln.bad(
        "Judged: after merging origin/main, the lane's own diff changed in app.py (main touched a "
        "lane file, or the lane's diff moved): the qc verdict does not carry over; run just qc and "
        f"the review again, in parallel, on {r2[:12]}",
        pr_head(r2, "Merge main"),
        head=r2[:12],
    )
    m3 = ln.on(m1, line(1, "uno", "main: app head"))
    ln.main(m3)
    resolved = "Merge main, conflict resolved"

    def conflict() -> None:
        ln.git("merge", "-q", "--no-edit", m3, want=1)
        ln.git("checkout", "-q", "--ours", "app.py")
        ln.git("commit", "-qam", resolved)

    r3 = ln.on(h, conflict)
    ln.bad(
        f"Judged: merge {r3[:12]} '{resolved}' resolved a conflict with origin/main: the qc "
        "verdict does not carry over",
        pr_head(r3, resolved),
        head=r3[:12],
    )
    ln.main(m1)

    def side() -> None:
        ln.write("side.txt", "side\n")
        ln.commit("side")

    x = ln.on(ln.b, side)
    r4 = ln.merge(h, x)
    ln.bad(
        rf"Judged: merge {r4[:12]} .* brings in {x[:12]}, not origin/main: only a merge of main "
        "keeps the qc verdict",
        pr_head(r4, "Merge side"),
        regex=True,
        head=r4[:12],
    )


def full_pass(s: Scratch) -> None:
    """issue-lifecycle#acceptance-merge-ask-full-proof (rule: #lanes-checkpoints): the passes
    stand on J's recorded full pass (H adds only qc's status commit). A head with none refuses,
    naming it, the section otherwise complete; a pass whose gate configuration or shared-machinery
    list is not the head's (main brought it) is stale; one recorded on a dirty tree proves
    nothing."""
    ln = Lane(s)
    j, h = ln.j, ln.h

    def none(head: str, at: str) -> str:
        return (
            f"Full pass: head {head[:12]} has no current recorded full gate pass for that head and "
            f"its gate configuration; the full pass recorded at {at[:12]} does not carry over: "
        )

    e = ln.change(h, "feat: no full pass", text="e")
    edits, lines = ln.at(e, "feat: no full pass")
    ln.setpr(*edits, **lines)
    r = ln.ask(want=1)
    code = f"commit {e[:12]} 'feat: no full pass' after the full pass {j[:12]} changes app.py"
    want = f"(1 item), head {e[:12]}:\n  - {none(e, j)}{code}"
    assert want in r.err, f"a head with no full pass: {r.err}"
    m1 = ln.change(ln.b, "main: notes", "notes.txt", "main")

    def merged(rel: str, text: str, msg: str) -> str:
        """H merged with a main that adds REL, a commit MSG off M1."""

        def make() -> None:
            ln.write(rel, text)
            ln.commit(msg)

        m = ln.on(m1, make)
        ln.main(m)
        return ln.merge(h, m)

    r5 = merged("justfile", "check:\n    true\n", "main: a gate")
    stale = r"is not the head's current [0-9a-f]{12} \(octo-feather-gate config "
    ln.bad(
        re.escape(none(r5, j)) + rf"its gate_config [0-9a-f]{{12}} {stale}{r5[:12]}\): stale",
        pr_head(r5, "Merge main"),
        regex=True,
        head=r5[:12],
    )
    # a checkpoint: the list changed, J's pass was recorded against none
    r6 = merged("shared-machinery.txt", "machinery\n", "main: a shared-machinery list")
    ln.bad(
        re.escape(none(r6, j)) + rf"its list absent {stale}{r6[:12]}\): stale",
        pr_head(r6, "Merge main"),
        regex=True,
        head=r6[:12],
    )
    ln.main(m1)

    def dirty() -> None:  # a pass recorded on a dirty tree (an untracked file beside the gate)
        with (ln.r / "app.py").open("a") as f:
            f.write("d\n")
        ln.git("commit", "-qam", "feat: dirty pass")
        ln.write("dirt", "x\n")
        ln.record()
        (ln.r / "dirt").unlink()

    d = ln.on(h, dirty)
    edits, lines = ln.at(d, "feat: dirty pass")
    ln.setpr(*edits, **lines)
    r = ln.ask(want=1)
    dirt = "it was recorded on a dirty tree (clean false): it proves nothing"
    want = f"(1 item), head {d[:12]}:\n  - {none(d, d)}{dirt}"
    assert want in r.err, f"a pass recorded on a dirty tree: {r.err}"


def judged_rows(s: Scratch) -> None:
    """Each row's judged head is a commit of the PR, written `judged <sha>`, in a table with the
    judged column; a multi-spec lane passes --status once per spec, a qc id outside the --status
    files not demanded."""
    ln = Lane(s)
    js, j, h = ln.js, ln.j, ln.h
    b = f"\n| demo#acceptance-b | pass | judged {js} | r |"
    ln.bad(
        "criterion row demo#acceptance-a: judged deadbee is not a commit of PR #7; name the head "
        "qc and the review judged",
        rows=f"| demo#acceptance-a | pass | judged deadbee | r |{b}",
    )
    ln.bad(
        "judged 'yesterday'; write `judged <sha>`",
        rows=f"| demo#acceptance-a | pass | yesterday | r |{b}",
    )
    old = ln.body().replace(HDR.splitlines()[0], "| criterion | qc verdict | evidence |")
    ln.bad("criterion table: no judged column", lambda d: d.update(body=old))
    qx = ln.empty(h, "qc: built acceptance-x (judged 0123456789ab)")
    proof = f"{j[:12]} to {qx[:12]}: qc status commits {h[:12]} {qx[:12]} {ONLY}"
    ln.setpr(pr_head(qx, "x"), head=qx[:12], judged=proof)
    ln.ask()
    rows = ln.rows(js, extra=f"\n| other#acceptance-x | pass | judged {js} | r |")
    built = "acceptance-a acceptance-b other#acceptance-x"
    ln.setpr(pr_head(qx, "x"), head=qx[:12], judged=proof, rows=rows, built=built)
    ln.ask("--status", "docs/specs/other.status.json")


def usage_failures(s: Scratch) -> None:
    """Usage and execution failures name their fix."""
    ln = Lane(s)
    ln.setpr()
    for args, want in (
        (["7"], "name the lane's status file"),
        (["7", "--status", str(ln.t / "nope.json")], "not a readable status file"),
        (["0", "--status", STATUS], "positive integer"),
    ):
        r = ln.lane("merge-ask", *args, want=1)
        assert want in r.err, f"{args}: {r.err}"
    (s.gh.dir / "down").touch()
    r = ln.ask(want=1)
    assert re.search(r"error connecting.*gh auth status", r.err), r.err
    (s.gh.dir / "down").unlink()
    # a gh printing fewer fields than asked (the fake gh answers every field, as gh does)
    old = ln.t / "old-gh"
    old.mkdir()
    (old / "gh").write_text("#!/bin/sh\necho '{\"number\": 7}'\n")
    (old / "gh").chmod(0o755)
    r = ln.ask(want=1, env={"PATH": f"{old}:{s.env['PATH']}"})
    assert "lacks fields" in r.err, r.err


# --- a lane that builds no criterion (spec #lanes-one-head, #acceptance-merge-ask-no-criterion) ---


class Pr8:
    """PR #8: commit N off main, no qc commit, its full pass recorded and its clear verdict. Its
    lane's PR #7 holds no comment: PR #8's is the one a verdict updates."""

    def __init__(self, s: Scratch) -> None:
        ln = self.ln = Lane(s, pr8=True)
        self.n, self.url = ln.heads["n"], ln.heads["url8"]
        self.keep: dict[str, Any] = ln.pr(8)

    @staticmethod
    def build(ln: Lane, b: str, report: str) -> dict[str, str]:
        """PR #8 in the lane LN being built: N off B, its pass recorded, its verdict posted."""

        def fix() -> None:
            ln.line(2, "two")
            ln.git("commit", "-qam", "fix: a rule")
            ln.record()

        p = Pr8.__new__(Pr8)
        p.ln, p.n, p.url, p.keep = ln, ln.on(b, fix), "", {"comments": []}
        p.put(p.n, p.body())
        return {"n": p.n, "url8": ln.lane("verdict", "8", p.n, report).out}

    def body(self, **o: str) -> str:
        """Its section, a line overridden by each of O: parent head judged table built failed."""
        return (
            f"{o.get('parent', 'Closes #6')}\n\n## Merge ask\n\n"
            f"Head: {o.get('head', self.n[:12])}\nChecks: check, ci/x pass\n"
            f"{o.get('judged', '')}\n{o.get('table', '')}\n"
            f"Review verdict: {self.url}\nBuilt: {o.get('built', 'none')}\n"
            f"{o.get('failed', 'Failed: none')}\n"
        )

    def put(self, head: str, body: str, *edits: Edit, subject: str = "") -> None:
        """PR #8 at HEAD (with SUBJECT: a commit of it after N) with BODY, EDITS applied."""
        d = copy.deepcopy(self.keep)
        commits = [{"oid": self.n, "messageHeadline": "fix: a rule", "messageBody": ""}]
        if subject:
            commits.append({"oid": head, "messageHeadline": subject, "messageBody": ""})
        d.update(number=8, baseRefName="main", headRefName="gh6", headRefOid=head, body=body)
        d.update(statusCheckRollup=copy.deepcopy(CHECK_OK), commits=commits)
        for e in edits:
            e(d)
        self.ln.s.gh.put(8, d)

    def ask(self, *extra: str, want: int = 0) -> Ran:
        return self.ln.lane("merge-ask", "8", *extra, want=want)


def no_criterion_lane(s: Scratch) -> None:
    """A lane building no criterion passes on head, checks, parent line and the review verdict
    alone, with no table or its header, --status optional; each item still checked; the
    verdict's head is the judged head: a code commit after it fails, a clean main merge needs its
    proof line; a head with no recorded full pass refuses."""
    p = Pr8(s)
    ln, n = p.ln, p.n
    for tbl in ("", HDR):
        for args in ([], ["--status", STATUS]):
            p.put(n, p.body(table=tbl))
            out = p.ask(*args).out.splitlines()
            assert out[0] == "## Merge ask", (tbl, args, out)
            assert "Built: none" in out, (tbl, args, out)
    p.put(n, p.body(head=OTHER[:12]))
    assert f"Head: names {OTHER[:12]}" in p.ask(want=1).err
    p.put(n, p.body(), FAILURE)
    assert "Checks: failing" in p.ask(want=1).err
    p.put(n, p.body(parent=""))
    assert "parent line: missing" in p.ask(want=1).err
    p.put(n, p.body(), verdict_says("Verdict: clear", "Verdict: blocking"))
    assert "Review verdict: blocking, not clear" in p.ask(want=1).err
    p.put(n, p.body(), verdict_says("\nChecks: none\n", "\n"))
    err = p.ask(want=1).err
    assert "carries no usable check classification" in err, err
    assert "criterion table" not in err, f"no-criterion lane asked for a table: {err}"
    assert "qc: built" not in err, f"no-criterion lane asked for a qc commit: {err}"
    nf = ln.change(n, "fix: more", text="three")
    p.put(nf, p.body(head=nf[:12]), subject="fix: more")
    err = p.ask(want=1).err
    assert (
        f"Judged: commit {nf[:12]} 'fix: more' after the judged head {n[:12]} changes app.py" in err
    )
    m1 = ln.change(ln.b, "main: notes", "notes.txt", "main")
    ln.main(m1)
    nm = ln.merge(n, m1)
    p.put(nm, p.body(head=nm[:12]), subject="Merge main")
    err = p.ask(want=1).err
    want = (
        f"Judged: missing; add the check's proof line `Judged: {n[:12]} to {nm[:12]}: no qc status "
        f"commit; clean merge of main {nm[:12]}: lane diff identical"
    )
    assert want in err, err
    proof = proof_line(err)
    p.put(nm, p.body(head=nm[:12], judged=f"Judged: {proof}"), subject="Merge main")
    assert f"Judged: {proof}" in p.ask().out.splitlines()
    n2 = ln.change(n, "fix: no full pass", text="four")
    edit = verdict_says(f"Head: {n}", f"Head: {n2}")
    p.put(n2, p.body(head=n2[:12]), edit, subject="fix: no full pass")
    err = p.ask(want=1).err
    want = f"(1 item), head {n2[:12]}:\n  - Full pass: head {n2[:12]} has no current recorded full"
    assert want in err, err


def criterion_claimed(s: Scratch) -> None:
    """A lane that claims a criterion (a qc commit, a Built or Failed id, a status entry built
    with the PR) with no rows is refused naming the table (#acceptance-merge-ask-evidence); one
    with a Built id needs --status."""
    p = Pr8(s)
    ln, n = p.ln, p.n
    st = ["--status", STATUS]
    nq = ln.empty(n, "qc: built acceptance-a (judged 0123456789ab)")  # a qc commit on the lane
    built8 = (ln.r / STATUS).read_text().replace('"planned", "pr": null', '"built", "pr": 8')
    s8 = ["--status", ln.file("s8.json", built8)]
    for tbl in ("", HDR):
        want = "criterion table: " + ("no rows" if tbl else "missing")
        for head, body, args in (
            (nq, p.body(head=nq[:12], table=tbl), st),
            (n, p.body(table=tbl, built="demo#acceptance-a"), st),
            (n, p.body(table=tbl, failed="Failed:\n- acceptance-c: repair ticket #9"), st),
            (n, p.body(table=tbl), s8),
        ):
            p.put(head, body)
            err = p.ask(*args, want=1).err
            assert want in err, f"{want!r}: {err}"
    p.put(n, p.body(built="acceptance-a"))
    assert "name the lane's status file" in p.ask(want=1).err


def many_commits(s: Scratch) -> None:
    """More than 100 commits: `gh pr view --json commits` lists at most 100, so the PR's commits
    are read from git (BASE..head): PR #8's head NL, the 101st commit off main, listed only to 100
    as GitHub does; verdict accepts NL and merge-ask passes on it."""
    p = Pr8(s)
    ln = p.ln

    def many() -> None:
        for i in range(1, 102):
            ln.write("many.txt", f"{i}\n")
            ln.commit(f"chore: step {i}")
        ln.record()

    nl = ln.on(ln.b, many)
    cap = ln.git("rev-list", "--reverse", f"{ln.b}..{nl}").splitlines()[:100]
    listed = [{"oid": c, "messageHeadline": "chore", "messageBody": ""} for c in cap]
    p.put(nl, p.body(head=nl[:12]), lambda d: d.update(commits=listed))
    oids = [c["oid"] for c in ln.pr(8)["commits"]]
    assert len(oids) == 100, "the 101-commit PR does not list 100"
    assert nl not in oids, "the 101-commit PR lists its head"
    r = ln.lane("verdict", "8", nl, ln.report)
    assert f"(clear, head {nl[:12]})" in r.err, r.err
    assert first(p.ask()) == "## Merge ask"


def fields(s: Scratch) -> None:
    """fields: a label of words one space apart is a field (Prior art: code-review step 4,
    Report fields); two spaces is not."""
    p = s.root / "fields"
    p.write_text("Checks: none\nPrior art: PyYAML 6.0.2 | license: MIT\nPrior  art: x\n")
    f = json.loads(s.run([L, "fields", str(p)]).out)["fields"]
    assert f == {"Prior art": ["PyYAML 6.0.2 | license: MIT"]}, f


if __name__ == "__main__":
    main(
        verdict_posts,
        verdict_reader_scope,
        verdict_refusals,
        verdict_write_fails,
        offline_gh,
        merge_ask_passes,
        gate_time,
        failed_triage,
        parent_line,
        single_gaps,
        no_ci,
        no_ci_unread,
        ci_status_only,
        rows_and_built,
        review_link,
        one_judged_head,
        main_merges,
        full_pass,
        judged_rows,
        usage_failures,
        no_criterion_lane,
        criterion_claimed,
        many_commits,
        fields,
    )
