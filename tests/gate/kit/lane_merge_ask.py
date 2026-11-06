"""The scenarios of tests/gate/kit/test_lane_merge_ask.py (its items), this file their command
(testkit.main): scripts/octo-feather-lane verdict, fields and merge-ask (spec issue-lifecycle
#acceptance-merge-ask-evidence, issue #48), no network: the testkit's fake gh holds PR #7 of o/r
and logs every call. `verdict` creates the one marker comment, updates it in place on rerun, and
refuses a wrong head, a report with no verdict or no check classes (docs/adr/0008), a proxy check
with a clear verdict and a failed write, leaving no comment behind. `merge-ask` passes a complete
section and prints it, then labels each row with its latest qc result's decision source at the
judged head (quality#acceptance-qc-fallback) (also through the qc judge's offline gh,
github-pr/scripts/gh), fails PR #16's real body (fixture) naming each missing item, and fails each
single gap: no parent line (the tracker skill's pr-line for the PR branch: Closes #6 on GitHub; a
Linear target's lane passes with Tracks ENG-123 and no Closes line, and fails with one, spec
#acceptance-pr-tracks), stale head, failing or pending check, no check reported (rule: --help,
merge-ask Checks line), missing row, Built unequal to the status file or to the qc commits,
verdict link to another head or a blocking verdict, untriaged failed criterion. One judged head
(spec #acceptance-one-head), on a real git lane: review on J plus qc's status commit H passes with
the check's proof line; a non-status file after J fails naming it; a clean main merge keeps the qc
verdict and prints its proof; a main merge touching a lane file or resolving a conflict fails.
Full pass (#acceptance-merge-ask-full-proof): every merge ask needs a current recorded full gate
pass. Gate time (#acceptance-merge-ask-gate-budget): the final head's full run against the
budget, shown, never decided on. Skipped checks: #acceptance-ci-status-only (the rule:
#lanes-one-head). A lane building no criterion: PR #8.

Lane gh6's worktree with PR #7 and the review's clear verdict posted (`build`), and the same with
PR #8 of a lane building no criterion beside it (`build_pr8`), are each prepared once per gate run
(testkit Scratch.prepare) and copied into each item. Only the kit's own commands run
(octo-feather-lane, octo-feather-gate, the offline gh); GitHub is the fake gh's store.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from testkit import ROOT, Ran, Scratch, fixture, kit, main

if TYPE_CHECKING:
    from collections.abc import Callable

    Edit = Callable[[dict[str, Any]], object]

OFFLINE_GH = ROOT / ".agents" / "skills" / "github-pr" / "scripts"  # its gh
OTHER = "ffee" * 10  # a sha of no commit here
STATUS = "docs/specs/demo.status.json"
ST = ("--status", STATUS)
CHECK_OK = [
    {"__typename": "CheckRun", "name": "check", "status": "COMPLETED", "conclusion": "SUCCESS"},
    {"__typename": "StatusContext", "context": "ci/x", "state": "SUCCESS"},
]
REPORT = "Findings: none blocking.\nChecks: none\nVerdict: clear\n"
REPORT2 = "Note: a nit.\nChecks: none\nVerdict: blocking\n"
MARK = "<!-- octo-feather-review-verdict -->"
HDR = "| criterion | qc verdict | judged | evidence |\n|---|---|---|---|"
E502 = "gh: Server Error (HTTP 502)"
# GitHub's 403 on rules/branches on a plan without rulesets, as gh prints it.
E403 = "gh: Upgrade to GitHub Pro or make this repository public to enable this feature. (HTTP 403)"
TREES = "api/repos/o/r/git/trees"
BRANCH = "api/repos/o/r/branches/main"
RULES = "api/repos/o/r/rules/branches/main"
UNPROTECTED: dict[str, object] = {
    "name": "main",
    "protected": False,
    "protection": {
        "enabled": False,
        "required_status_checks": {"enforcement_level": "off", "contexts": [], "checks": []},
    },
}
GATE_TITLE = (
    "Gate time (the full gate on the final head against gate-budget.toml at {}; the code reviewer "
    "judges it, no gate reads it: issue-lifecycle #lanes-checkpoints):"
)
FULL = "has no current recorded full gate pass for that head and its gate configuration"


def status_text(st: str, pr: str) -> str:
    """demo.status.json with acceptance-a and -b at ST, PR."""
    return (
        '{"spec": "demo.spec.html", "accepted_commit": "0123abc", "criteria": {\n'
        f'  "acceptance-a": {{"status": "{st}", "pr": {pr}}}, '
        f'"acceptance-b": {{"status": "{st}", "pr": {pr}}},\n'
        '  "acceptance-c": {"status": "planned", "pr": null}, '
        '"acceptance-d": {"status": "built", "pr": 3}}}\n'
    )


def row(cid: str, judged: str, verdict: str = "pass", ev: str = "r") -> str:
    return f"| {cid} | {verdict} | {judged} | {ev} |"


def commit_entry(sha: str, subject: str) -> dict[str, str]:
    return {"oid": sha, "messageHeadline": subject, "messageBody": ""}


def pr_head(sha: str, subject: str) -> Edit:
    """SHA the PR head, a commit of the PR."""

    def f(d: dict[str, Any]) -> None:
        d["headRefOid"] = sha
        d["commits"].append(commit_entry(sha, subject))

    return f


def verdict_says(old: str, new: str) -> Edit:
    """The verdict comment's body with OLD replaced by NEW."""

    def f(d: dict[str, Any]) -> None:
        c = d["comments"][0]
        c["body"] = c["body"].replace(old, new)

    return f


def check(**kv: str) -> Edit:
    """The first reported check's fields set to KV."""
    return lambda d: d["statusCheckRollup"][0].update(kv)


def none_reported(d: dict[str, Any]) -> None:
    d.update(statusCheckRollup=[], baseRefName="main")


def lines_from(text: str, start: str, *, within: bool = False) -> list[str]:
    """TEXT's lines from the first starting with START (holding it, when WITHIN) on."""
    ls = text.split("\n")
    return ls[
        next(i for i, ln in enumerate(ls) if (start in ln if within else ln.startswith(start))) :
    ]


def before_gate_time(out: str) -> str:
    """OUT without its gate time block, which comes last."""
    ls = out.split("\n")
    end = next((i for i, ln in enumerate(ls) if ln.startswith("Gate time (")), len(ls))
    return "\n".join(ls[:end]).rstrip("\n")


def gate_block(out: str) -> str:
    """The gate time block of OUT, through its blank line, each age as AGE."""
    ls = lines_from(out, "Gate time (")
    end = next((i for i, ln in enumerate(ls) if ln == ""), len(ls))
    block = "\n".join(ls[:end])
    return re.sub(r"\((\d+d)?(\d+h)?\d+m ago\)", "(AGE ago)", block)


def without_gate_time(out: str) -> str:
    ls = out.split("\n")
    if not any(ln.startswith("Gate time (") for ln in ls):
        return out
    start = next(i for i, ln in enumerate(ls) if ln.startswith("Gate time ("))
    end = next((i for i in range(start, len(ls)) if ls[i] == ""), len(ls) - 1)
    return "\n".join(ls[:start] + ls[end + 1 :])


def proof_asked(err: str) -> str:
    """The proof line a refusal asks for."""
    m = re.search(r"add the check.s proof line `Judged: (.*)`$", err, re.MULTILINE)
    assert m, f"no proof line asked: {err}"
    return m.group(1)


class Lane:
    """Lane gh6's worktree: origin/main B, the judged head J (its full gate pass recorded) and
    qc's status commit H (the PR head); PR #7 in the fake gh with the review's clear verdict on J
    (comment URL `url`), kept as pr7.json. With PR #8 (build_pr8): commit N off B (its full pass
    recorded), PR #8 with its clear verdict (url8), kept as pr8.json."""

    def __init__(self, s: Scratch, *, new: bool = False) -> None:
        self.s = s
        self.repo = s.root / "repo"
        s.env["OCTO_FEATHER_QC_DIR"] = str(s.root / "qc")
        if new:  # being built: no heads yet
            (s.root / "lane.json").write_text(json.dumps({"b": "", "j": "", "h": "", "url": ""}))
        d: dict[str, str] = json.loads((s.root / "lane.json").read_text())
        self.b, self.j, self.h, self.url = d["b"], d["j"], d["h"], d["url"]
        self.n, self.url8 = d.get("n", ""), d.get("url8", "")
        self.j12, self.h12, self.js = self.j[:12], self.h[:12], self.j[:7]
        self.proof = f"{self.j12} to {self.h12}: qc status commits {self.h12} change only {STATUS}"

    def save(self, **kv: str) -> None:
        p = self.s.root / "lane.json"
        p.write_text(json.dumps(json.loads(p.read_text()) | kv))

    # --- the worktree ---

    def git(self, *args: str, want: int = 0) -> str:
        ident = [
            "-c",
            "user.email=t@example.com",
            "-c",
            "user.name=t",
            "-c",
            "commit.gpgsign=false",
        ]
        return self.s.run(["git", "-C", str(self.repo), *ident, *args], want=want).out

    def write(self, rel: str, text: str) -> None:
        (self.repo / rel).write_text(text)

    def append(self, rel: str, text: str) -> None:
        with (self.repo / rel).open("a") as f:
            f.write(text)

    def set_line(self, rel: str, n: int, text: str) -> None:
        ls = (self.repo / rel).read_text().split("\n")
        ls[n - 1] = text
        self.write(rel, "\n".join(ls))

    def commit(self, msg: str, *flags: str) -> str:
        self.git("add", "-A")
        self.git("commit", "-q", *flags, "-m", msg)
        return self.git("rev-parse", "HEAD")

    def on(self, parent: str, *steps: Callable[[], object]) -> str:
        """STEPS run on a detached checkout of PARENT; the new HEAD, back on the lane."""
        self.git("checkout", "-q", "--detach", parent)
        for step in steps:
            step()
        sha = self.git("rev-parse", "HEAD")
        self.git("checkout", "-q", "-f", "lane")
        return sha

    def main_at(self, sha: str) -> None:
        self.git("update-ref", "refs/remotes/origin/main", sha)

    def record(self, reason: str = "lane final head") -> None:
        """A full gate pass recorded at the checked-out commit."""
        self.s.run(
            [kit("octo-feather-gate"), "record", "--reason", reason, "--seconds", "1"],
            cwd=self.repo,
        )

    def merge(self, onto: str, other: str) -> str:
        return self.on(onto, lambda: self.git("merge", "-q", "--no-edit", other))

    def main_commit(self) -> str:
        """M1: origin/main one commit past B (notes.txt), set as origin/main."""
        m1 = self.on(
            self.b,
            lambda: self.append("notes.txt", "main\n"),
            lambda: self.git("commit", "-qam", "main: notes"),
        )
        self.main_at(m1)
        return m1

    # --- the commands and the PRs ---

    def lane(
        self, *args: str, want: int = 0, stdin: str | None = None, env: dict[str, str] | None = None
    ) -> Ran:
        return self.s.run(
            [kit("octo-feather-lane"), *args], want=want, cwd=self.repo, env=env, stdin=stdin
        )

    def file(self, name: str, text: str) -> str:
        p = self.s.root / name
        p.write_text(text)
        return str(p)

    def verdict(self, pr: str, head: str, report: str, want: int = 0) -> Ran:
        return self.lane("verdict", pr, head, self.file("report", report), want=want)

    def ask(self, *extra: str, want: int = 0) -> Ran:
        return self.lane("merge-ask", "7", *ST, *extra, want=want)

    def pr7(self) -> dict[str, Any]:
        return cast("dict[str, Any]", self.s.gh.pr(7))

    def kept(self, n: int = 7) -> dict[str, Any]:
        return cast("dict[str, Any]", json.loads((self.s.root / f"pr{n}.json").read_text()))

    def comments(self) -> int:
        return len(self.pr7()["comments"])

    def body(self, **kw: str) -> str:
        """PR #7's body with a complete merge ask section; KW overrides an item (parent, head,
        judged, rows, review, built, failed)."""
        js = self.js
        v = {
            "parent": "Closes #6",
            "head": self.h12,
            "judged": self.proof,
            "rows": f"| demo#acceptance-a | pass | judged {js} | qc report a1b2.json, cmd ok |\n"
            f"| acceptance-b | pass | judged {js} | qc report a1b2.json, cmd ok |",
            "review": self.url,
            "built": "demo#acceptance-a acceptance-b",
            "failed": "Failed: none",
        } | kw
        return (
            f"{v['parent']}\n\n## Summary\n\nLane work.\n\n## Merge ask\n\n"
            f"Head: {v['head']}\nChecks: check, ci/x pass on {self.h12}\nJudged: {v['judged']}\n"
            f"{HDR}\n{v['rows']}\nReview verdict: {v['review']}\nBuilt: {v['built']}\n"
            f"{v['failed']}\n\n## Notes\n\nafter the section"
        )

    def rows(self, *extra: str, judged: str = "") -> str:
        """Rows a and b passing, judged JUDGED (J's 7), then EXTRA."""
        j = judged or f"judged {self.js}"
        return "\n".join([row("demo#acceptance-a", j), row("demo#acceptance-b", j), *extra])

    def pr(self, *edits: Edit, **kw: str) -> None:
        """PR #7 as kept, its body from body(KW), then EDITS."""
        d = self.kept()
        d["body"] = self.body(**kw)
        for e in edits:
            e(d)
        self.s.gh.put(7, d)

    def bad(self, want: str, *edits: Edit, rx: bool = False, **kw: str) -> str:
        """merge-ask on PR #7 (pr(EDITS, KW)) exits 1 naming WANT (a regex when RX), printing
        nothing on stdout; its stderr."""
        self.pr(*edits, **kw)
        r = self.ask(want=1)
        found = re.search(want, r.err, re.MULTILINE) if rx else want in r.err
        assert found, f"merge-ask did not say {want!r}: {r.err}"
        assert r.out == "", f"a failing merge ask printed to stdout: {r.out}"
        return r.err

    def qc_report(self, name: str, results: list[dict[str, Any]]) -> None:
        q = self.s.root / "qc"
        q.mkdir(exist_ok=True)
        (q / name).write_text(json.dumps({"head": self.j, "spec": "demo", "results": results}))

    def runs(self, sha: str, runs: list[dict[str, object]]) -> None:
        """SHA's check runs on GitHub (REST check-runs)."""
        self.s.gh.store(
            f"api/repos/o/r/commits/{sha}/check-runs?per_page=100.json",
            {"total_count": len(runs), "check_runs": runs},
        )

    def log_from(self, k: int) -> list[str]:
        return self.s.gh.log()[k:]

    # --- PR #8, a lane building no criterion ---

    def nbody(self, **kw: str) -> str:
        """PR #8's merge ask section; KW overrides head, judged, table, built, failed."""
        v = {
            "head": self.n[:12],
            "judged": "",
            "table": "",
            "review": self.url8,
            "built": "none",
            "failed": "Failed: none",
        } | kw
        return (
            f"Closes #6\n\n## Merge ask\n\nHead: {v['head']}\nChecks: check, ci/x pass\n"
            f"{v['judged']}\n{v['table']}\nReview verdict: {v['review']}\nBuilt: {v['built']}\n"
            f"{v['failed']}"
        )

    def pr8(self, head: str, body: str, *edits: Edit, extra: tuple[str, str] | None = None) -> None:
        """PR #8 as kept, at HEAD with BODY, its commits N and EXTRA (sha, subject), then EDITS."""
        p = self.s.root / "pr8.json"
        d: dict[str, Any] = json.loads(p.read_text()) if p.exists() else {"comments": []}
        d.update(
            number=8,
            baseRefName="main",
            headRefName="gh6",
            headRefOid=head,
            body=body,
            statusCheckRollup=json.loads(json.dumps(CHECK_OK)),
            commits=[commit_entry(self.n, "fix: a rule")]
            + ([commit_entry(*extra)] if extra else []),
        )
        for e in edits:
            e(d)
        self.s.gh.put(8, d)


def build(p: Scratch) -> None:
    """The lane: B on main, J, its full pass, H; PR #7, the review's clear verdict on J."""
    lane = Lane(p, new=True)
    r = lane.repo
    (r / "docs" / "specs").mkdir(parents=True)
    p.git(r, "init", "-q", "-b", "main")
    for k, v in (("user.email", "t@example.com"), ("user.name", "t"), ("commit.gpgsign", "false")):
        p.git(r, "config", k, v)
    lane.write(STATUS, status_text("planned", "null"))
    lane.write("app.py", "".join(f"{i}\n" for i in range(1, 21)))
    lane.write("notes.txt", "notes\n")
    lane.write("gate-budget.toml", "budget_seconds = 150\ngrowth_share = 0.25\ntrend_runs = 3\n")
    lane.write("qc.toml", '[demo."demo#acceptance-a"]\ncommand = "true"\n')  # a demo for a only
    lane.write(
        "docs/specs/other.status.json",
        '{"spec": "other.spec.html", "accepted_commit": "0123abc", "criteria": '
        '{"acceptance-x": {"status": "built", "pr": 7}}}\n',
    )
    b = lane.commit("base")
    lane.main_at(b)
    lane.git("checkout", "-q", "-b", "lane")
    lane.set_line("app.py", 1, "one")
    j = lane.commit("feat: x")
    lane.record()
    lane.write(STATUS, status_text("built", "7"))
    h = lane.commit(f"qc: built acceptance-a acceptance-b (judged {j[:12]})")
    p.gh.put(
        7,
        {
            "number": 7,
            "baseRefName": "main",
            "headRefName": "gh6",
            "headRefOid": h,
            "body": "",
            "statusCheckRollup": CHECK_OK,
            "comments": [],
            "commits": [
                commit_entry(j, "feat: x"),
                commit_entry(h, f"qc: built acceptance-a acceptance-b (judged {j[:12]})"),
            ],
        },
    )
    url = lane.verdict("7", j[:7], REPORT).out
    assert url == "https://github.com/o/r/pull/7#issuecomment-1001", url
    (p.root / "pr7.json").write_text(json.dumps(p.gh.pr(7)))
    lane.save(b=b, j=j, h=h, url=url)


def build_pr8(p: Scratch) -> None:
    """The lane (build), and PR #8: commit N off main, its full pass, no qc commit, its review's
    clear verdict."""
    p.prepare("lane-merge-ask", build)
    lane = Lane(p)
    n = lane.on(
        lane.b,
        lambda: lane.set_line("app.py", 2, "two"),
        lambda: lane.git("commit", "-qam", "fix: a rule"),
    )
    lane.on(n, lane.record)
    lane.n = n
    lane.pr8(n, lane.nbody())
    lane.url8 = lane.verdict("8", n, REPORT).out
    (p.root / "pr8.json").write_text(json.dumps(p.gh.pr(8)))
    lane.save(n=n, url8=lane.url8)


def world(s: Scratch, *, pr8: bool = False) -> Lane:
    """S holding the prepared lane (with PR #8 when PR8), the fake gh's log empty."""
    if pr8:
        s.prepare("lane-merge-ask-pr8", build_pr8)
    else:
        s.prepare("lane-merge-ask", build)
    (s.gh.dir / "log").write_text("")
    return Lane(s)


# --- verdict ---


def verdict_posts(s: Scratch) -> None:
    """verdict creates the one marker comment, updates it in place on rerun (also from stdin),
    and an unchanged rerun writes nothing, saying so. The review judged J, while qc made H."""
    lane = world(s)
    lane.s.gh.put(7, {**lane.kept(), "comments": []})
    url = lane.verdict("7", lane.js, REPORT).out
    assert url == "https://github.com/o/r/pull/7#issuecomment-1001", f"verdict printed {url}"
    log = s.gh.log()
    assert any(
        ln.startswith("api -X POST repos/{owner}/{repo}/issues/7/comments ") for ln in log
    ), log
    assert lane.comments() == 1, f"create made {lane.comments()} comments"
    r = lane.verdict("7", lane.j, REPORT2)
    assert r.out == url, f"rerun printed {r.out}"
    assert lane.comments() == 1, f"rerun not in place: {lane.comments()} comments"
    patch = "api -X PATCH repos/{owner}/{repo}/issues/comments/1001 "
    assert any(ln.startswith(patch) for ln in s.gh.log()), s.gh.log()
    b = lane.pr7()["comments"][0]["body"]
    assert b.startswith(MARK), b
    assert f"Head: {lane.j}\nPR head: {lane.h}\n" in b, b
    assert "Verdict: blocking\n" in b, b
    assert "a nit" in b, b
    lane.lane("verdict", "7", lane.j, "-", stdin=REPORT)  # stdin, back to clear
    assert s.gh.writes() == 3, f"third run: {s.gh.log()}"
    assert lane.comments() == 1, f"third run: {lane.comments()} comments"
    r = lane.verdict("7", lane.j, REPORT)
    assert s.gh.writes() == 3, f"unchanged rerun wrote: {s.gh.log()}"
    assert "unchanged" in r.err, f"unchanged rerun not said: {r.err}"


def verdict_reader_scope(s: Scratch) -> None:
    """The verdict is the last line in the reader scope (.agents/skills/code-review/SKILL.md step
    4 Report fields; review of 39515df, class verdict-parsing): fenced and quoted lines are not
    read (#144, #121 D10), while an indented fence or quote that is no fence or quote is."""
    lane = world(s)
    fenced = (
        "Ran the gate:\n```\nVerdict: clear\n```\n> Verdict: clear\n\n"
        "The quoted run predates the fix commit.\nChecks: none\nVerdict: blocking\n"
    )
    r = lane.verdict("7", lane.j, fenced)
    assert "(blocking, head" in r.err, f"fenced Verdict: clear was taken: {r.err}"
    b = lane.pr7()["comments"][0]["body"]
    assert "\nVerdict: blocking\nChecks: none\n\n### Findings" in b, b
    # a blank line after a quote ends it; a fence interrupts a quote, ~~~ fences
    r = lane.verdict("7", lane.j, "> the implementer wrote:\n\nVerdict: blocking\nChecks: none\n")
    assert "(blocking, head" in r.err, f"Verdict after a blank line ending the quote: {r.err}"
    r = lane.verdict(
        "7", lane.j, "> > nested:\n~~~\nVerdict: clear\n~~~\nChecks: none\nVerdict: blocking\n"
    )
    assert "(blocking, head" in r.err, f"~~~ fence after a quote: {r.err}"
    # PR #140 review rounds 2 and 3 (owner: markdown()'s scope, #144): the literal reports post.
    for report, what in (
        ("    ```\n\nVerdict: clear\nChecks: none\n", "4-space indented backticks read as a fence"),
        (
            "- item\n  > quote\n    ```\nVerdict: clear\nChecks: none\n",
            "indented quote and backticks in a list item hid the verdict",
        ),
    ):
        k = len(s.gh.log())
        r = lane.verdict("7", lane.j, report)
        posted = any(ln.startswith("api -X PATCH") for ln in lane.log_from(k))
        assert "(clear, head" in r.err, f"{what}: {r.err}"
        assert posted, f"{what}: not posted: {s.gh.log()}"


def verdict_check_classes(s: Scratch) -> None:
    """Check classes (docs/adr/0008, issue #118): a proxy check posts only with a blocking
    verdict, in the header."""
    lane = world(s)
    lane.verdict(
        "7",
        lane.j,
        "Check: `scripts/check-x`: tests reach no internals (docs/adr/0002) | reads: code tokens "
        "in tests/*.sh | class: Proxy\nVerdict: blocking\n",
    )
    b = lane.pr7()["comments"][0]["body"]
    header = (
        "\nVerdict: blocking\nCheck: scripts/check-x: tests reach no internals (docs/adr/0002) | "
        "reads: code tokens in tests/*.sh | class: proxy\n\n### Findings"
    )
    assert header in b, f"proxy check not in the verdict header: {b}"


def verdict_refusals(s: Scratch) -> None:
    """Each refusal exits non-zero naming the fix and writes nothing: a wrong head, no verdict
    (also a lazy continuation line after a quote, D10), disagreeing verdicts, no check classes
    (a fenced one ignored), a proxy check with a clear verdict, another class, a malformed check
    line, a rule naming no owner (review of 2e1a0da, class unvalidated-input), `Checks:` other
    than none, none beside check lines, a missing or empty report, a bad head, no report, an
    unknown PR."""
    lane = world(s)

    def refused(
        report: str | None, want: str, head: str = "", pr: str = "7", *, rx: bool = False
    ) -> None:
        if report is None:
            r = lane.lane("verdict", pr, head or lane.j, want=1)
        else:
            r = lane.verdict(pr, head or lane.j, report, want=1)
        found = re.search(want, r.err) if rx else want in r.err
        assert found, f"verdict did not say {want!r}: {r.err}"

    refused(REPORT, f"is not a commit of PR #7 (head {lane.h12}): push the reviewed head", OTHER)
    refused("looks fine\n", "add a line `Verdict: clear`")
    for q in (
        "> the implementer wrote:",
        "> > nested, quoted:",
        "> - a quoted item",
        ">     quoted code\n> the reply",
    ):
        refused(f"{q}\nVerdict: clear\nChecks: none\n", "report names no verdict")
    refused("Verdict: clear\n> quoted:\nChecks: none\n", "report classifies no check")
    refused(
        "Verdict: clear\nmore\nVerdict: blocking\n",
        "verdicts that disagree (clear, blocking): keep one",
    )
    refused(
        "Verdict: clear\n```\nChecks: none\n```\n",
        "report classifies no check: add `Checks: none` when",
    )
    refused(
        "Check: scripts/check-x: tests reach no internals (docs/adr/0002) | reads: code tokens | "
        "class: proxy\nVerdict: clear\n",
        r"with a proxy check \(Check: scripts/check-x: .*\): "
        r"a proxy check blocks \(docs/adr/0008\)",
        rx=True,
    )
    refused(
        "Check: scripts/check-x: r (ADR 1) | reads: y | class: meaning\nVerdict: blocking\n",
        r"has class 'meaning'; write .class: exact. or .class: proxy.",
        rx=True,
    )
    refused(
        "Check: scripts/check-x is a fact\nVerdict: clear\n",
        "check line `Check: scripts/check-x is a fact` is not `Check: <path>",
    )
    for rule in ("r", "r ()", "r (  )", "(ADR 1)"):
        refused(
            f"Check: scripts/x: {rule} | reads: y | class: exact\nVerdict: clear\n",
            "check line for scripts/x names no owner: write its rule as stated where it is owned",
        )
    refused("Checks: fine\nVerdict: clear\n", "`Checks: fine`; `Checks:` takes only `none`")
    refused(
        "Checks: none\nCheck: scripts/check-x: r (ADR 1) | reads: y | class: exact\n"
        "Verdict: clear\n",
        "has `Checks: none` and `Check:` lines",
    )
    r = lane.lane("verdict", "7", lane.j, str(s.root / "missing"), want=1)
    assert "cannot read report" in r.err, f"missing report: {r.err}"
    refused("", "is empty")
    refused(REPORT, "commit sha", "xyz")
    refused(None, "usage")
    refused(REPORT, "check PR #9 exists", pr="9")
    assert s.gh.writes() == 0, f"a refusal wrote: {s.gh.log()}"


def verdict_write_fails(s: Scratch) -> None:
    """Execution failures: a failed create leaves no comment, a failed update leaves the comment,
    a failed read names the fix; two marker comments are refused, nothing written."""
    lane = world(s)
    s.gh.put(7, {**lane.kept(), "comments": []})
    s.gh.store("api/repos/o/r/issues/7/comments.error", E502)
    r = lane.verdict("7", lane.j, REPORT, want=1)
    assert re.search("was not created; fix the cause.*then rerun", r.err), f"failed write: {r.err}"
    assert lane.comments() == 0, "failed create left a comment"
    s.gh.put(7, lane.kept())
    s.gh.store("api/repos/o/r/issues/comments/1001.error", E502)
    r = lane.verdict("7", lane.j, REPORT2, want=1)
    assert "was not updated" in r.err, f"failed update: {r.err}"
    assert "Verdict: clear" in json.dumps(lane.pr7()), "failed update changed the comment"
    (s.gh.dir / "down").touch()
    r = lane.verdict("7", lane.j, REPORT, want=1)
    assert re.search("error connecting.*gh auth status", r.err), f"failed read: {r.err}"
    (s.gh.dir / "down").unlink()
    d = lane.kept()
    c = dict(d["comments"][0])
    c["url"] = c["url"][:-4] + "1099"
    d["comments"].append(c)
    s.gh.put(7, d)
    n = s.gh.writes()
    r = lane.verdict("7", lane.h, REPORT, want=1)
    assert re.search("has 2 verdict comments.*delete all but one", r.err), (
        f"two marker comments: {r.err}"
    )
    assert s.gh.writes() == n, f"a refused verdict wrote: {s.gh.log()}"


def offline_gh(s: Scratch) -> None:
    """The same PR through the qc judge's offline gh (snapshot layout of octo-feather-qc-ghsnap):
    merge-ask passes; verdict's write is refused naming the read-only snapshot."""
    lane = world(s)
    lane.pr()
    snap = s.root / "snap"
    (snap / "pr").mkdir(parents=True)
    (snap / "meta.json").write_text('{"repo": "o/r", "counts": {}, "capped": []}')
    (snap / "fetched_at").write_text("x\n")
    (snap / "pr" / "7.json").write_text(json.dumps(lane.pr7()))
    env = {"OCTO_FEATHER_GHSNAP": str(snap), "PATH": f"{OFFLINE_GH}:{s.env['PATH']}"}
    out = lane.lane("merge-ask", "7", *ST, env=env).out
    assert out.split("\n")[0] == "## Merge ask", f"offline gh pass: {out}"
    r = lane.lane("verdict", "7", lane.h, lane.file("report2", REPORT2), want=1, env=env)
    said = r.out + r.err
    assert re.search(
        "was not updated.*offline read-only snapshot|offline read-only snapshot.*was not updated",
        said,
    ), f"verdict under the offline gh: {said}"


# --- merge-ask ---


def merge_ask_passes(s: Scratch) -> None:
    """A complete section passes and prints only the section, then the review's check classes;
    each row labelled with the decision source of its latest qc result at the judged head
    (quality#acceptance-qc-fallback), never from qc.toml (which declares a demo for
    acceptance-a): none yet, then a report's tagged test and agent fallback. Nothing written."""
    lane = world(s)
    lane.pr()
    out = lane.ask().out
    ls = out.split("\n")
    assert ls[0] == "## Merge ask", f"pass did not print the section: {out}"
    assert "Failed: none" in ls, f"pass did not print the section: {out}"
    w = before_gate_time(out)
    assert w.split("\n")[-2:] == [
        "Review check classes (from the verdict comment, docs/adr/0008):",
        "- Checks: none",
    ], f"pass did not list the check classes: {out}"
    assert f"Review verdict: {lane.url}" in out, out
    assert "Notes" not in out, f"printed more than the section: {out}"
    assert "Summary" not in out, f"printed more than the section: {out}"
    src = (
        f"Decision sources (the latest qc result at the judged head {lane.j12}; quality spec "
        "#qc-results):"
    )
    i = ls.index(src)
    assert ls[i : i + 3] == [
        src,
        "- demo#acceptance-a: no qc result at the judged head",
        "- demo#acceptance-b: no qc result at the judged head",
    ], f"pass without a qc report did not say each row has no qc result: {out}"

    def res(cid: str, decision: str) -> dict[str, Any]:
        return {
            "id": cid,
            "verdict": "pass",
            "evidence": "complete",
            "decision": decision,
            "record": "r",
            "head": lane.j,
        }

    lane.qc_report(
        f"{lane.j}-20261029T090000Z-src123.json",
        [res("acceptance-a", "tagged test assertions"), res("acceptance-b", "agent fallback")],
    )
    ls = lane.ask().out.split("\n")
    i = ls.index(src)
    assert ls[i : i + 3] == [
        src,
        "- demo#acceptance-a: tagged test assertions",
        "- demo#acceptance-b: agent fallback",
    ], f"pass did not label each row's decision source from the qc report: {ls}"
    assert s.gh.writes() == 0, f"merge-ask wrote: {s.gh.log()}"


def gate_time(s: Scratch) -> None:
    """issue-lifecycle#acceptance-merge-ask-gate-budget: the full gate's wall time on the final
    head (J's full run: H adds only qc's status commit) against gate-budget.toml at the head,
    flagged over the budget and grown past the share, beside the trend (passed full runs on the
    head's history: B's three; a subset run on H and a red full run on J stay out) and the
    slowest items. No gate on timing: the ask passes, or fails with the same items, as with no
    run recorded."""
    lane = world(s)
    lane.pr()
    none_out = lane.ask().out
    trend = Path(s.run([kit("octo-feather-state")]).out) / "check-runs.jsonl"
    title = GATE_TITLE.format(lane.h12)
    assert gate_block(none_out) == f"{title}\n  no gate run recorded ({trend}: none)", (
        f"no trend file: {gate_block(none_out)}"
    )
    trend.parent.mkdir(parents=True, exist_ok=True)

    def run_line(start: str, head: str, total: str, rc: int, tier: str) -> str:
        steps = [
            {
                "name": "tests/a.sh",
                "seconds": int(total.split(".", maxsplit=1)[0]) - 30,
                "result": "ok",
            },
            {"name": "tests/b.sh", "seconds": 20.5, "result": "ok"},
            {"name": "check-lint", "seconds": 1.0, "result": "ok"},
        ]
        d = {"start": start, "repo": str(lane.repo), "head": head, "total_s": json.loads(total)}
        return json.dumps(d | {"exit": rc, "tier": tier, "steps": steps}) + "\n"

    b, j = lane.b, lane.j
    trend.write_text(
        run_line("2026-10-01T10:00:00Z", b, "100", 0, "full")
        + run_line("2026-10-02T10:00:00Z", b, "120", 0, "full")
        + run_line("2026-10-03T10:00:00Z", b, "110", 0, "full")
        + run_line("2026-10-04T10:00:00Z", j, "90", 1, "full")
        + run_line("2026-10-04T11:00:00Z", j, "200.5", 0, "full")
        + run_line("2026-10-04T12:00:00Z", lane.h, "5", 0, "subset")
    )
    out = lane.ask().out
    b12, j12 = b[:12], lane.j12
    want = (
        f"{title}\n"
        f"  full gate: 200.5s, head {j12}, started 2026-10-04T11:00:00Z (AGE ago): OVER BUDGET by "
        "50.5s (budget 150s)\n"
        "  growth: +82.3% over the trend's median 110s (the 3 passed full runs before it); set "
        "share 25%: GROWN\n"
        f"  trend: 100s {b12} 2026-10-01T10:00:00Z, 120s {b12} 2026-10-02T10:00:00Z, 110s {b12} "
        f"2026-10-03T10:00:00Z, 200.5s {j12} 2026-10-04T11:00:00Z (passed full runs, oldest "
        "first)\n"
        "  slowest: tests/a.sh 170s, tests/b.sh 20.5s, check-lint 1s"
    )
    assert gate_block(out) == want, f"over budget: {gate_block(out)}"
    assert without_gate_time(out) == without_gate_time(none_out), (
        f"the gate time changed the merge ask: {out}"
    )
    # a refusal: the same items with or without the run, the gate time on stderr only
    lane.pr(check(conclusion="FAILURE"))
    r = lane.ask(want=1)
    assert r.out == "", f"refusal over budget printed: {r.out}"
    assert f"  full gate: 200.5s, head {j12}" in r.err, f"refusal over budget: {r.err}"
    over = "\n".join(lines_from(r.err, "merge ask incomplete", within=True))
    trend.rename(trend.with_suffix(".keep"))
    r = lane.ask(want=1)
    assert "\n".join(lines_from(r.err, "merge ask incomplete", within=True)) == over, (
        f"the gate time changed the refusal: {r.err}"
    )


def failed_triage(s: Scratch) -> None:
    """A failed criterion with triage passes (a Failed bullet); insufficient evidence (quality
    spec #qc-results, #acceptance-qc-insufficient) is never triaged: merge-ask fails naming it,
    from its row or from the latest qc report at the judged head, until a rerun gives it pass or
    fail."""
    lane = world(s)
    js = f"judged {lane.js}"
    lane.pr(
        failed="Failed:\n- acceptance-c: outside the lane, the spec behaviour is untouched "
        "(reason)",
        rows=lane.rows(row("demo#acceptance-c", js, "fail", "r, output x")),
    )
    out = lane.ask().out
    assert re.search(r"^- acceptance-c: outside", out, re.MULTILINE), f"triaged fail: {out}"
    lane.bad(
        "criterion row demo#acceptance-b: insufficient evidence is never triaged; rerun just qc "
        "on it until it gives pass or fail",
        rows=row("demo#acceptance-a", js)
        + "\n"
        + row("demo#acceptance-b", js, "insufficient evidence"),
    )

    def report(stamp: str, vb: str) -> None:
        short = vb == "insufficient evidence"
        why = "demo did not run to its end (exit 77, a step it needs could not run here): "
        miss = {"missing": [why + "needs GitHub"]}

        def res(cid: str, v: str) -> dict[str, Any]:
            d = {
                "id": cid,
                "verdict": v,
                "evidence": "incomplete" if v == vb and short else "complete",
            }
            d |= {"decision": "demo checks", "record": "r", "head": lane.j}
            return d | (miss if v == vb and short else {})

        lane.qc_report(
            f"{lane.j}-{stamp}-abc123.json", [res("acceptance-a", "pass"), res("acceptance-b", vb)]
        )

    report("20261029T100000Z", "insufficient evidence")
    lane.bad(
        f"criterion demo#acceptance-b: insufficient evidence at the judged head {lane.j12} (demo "
        "did not run to its end (exit 77, a step it needs could not run here): needs GitHub; qc "
        f"report {lane.j}-20261029T100000Z-abc123.json): never triaged"
    )
    report("20261029T110000Z", "pass")  # the rerun at that head gave it pass
    lane.pr()
    lane.ask()


def parent_line(s: Scratch) -> None:
    """The parent line (spec #gates-pr-line): the tracker skill's pr-line for the key the PR
    branch names: Closes #6 on GitHub; only the parent's own closing link is exempt, never the
    rest of its line, and an issue URL closes too. A Linear target's lane (its
    .octo-feather.toml): Tracks ENG-123 for branch eng-123, no Closes line, passes."""
    lane = world(s)
    lane.bad(
        "parent line: missing; add the line `Closes #6` (the tracker skill's pr-line 6)", parent=""
    )
    lane.bad("parent line: missing; add the line `Closes #6`", parent="Closes #60")
    closes9 = "closes GitHub issue #9, not the lane's parent line `Closes #6`"
    lane.bad(f"parent line: `Also fixes #9` {closes9}", parent="Closes #6\nAlso fixes #9")
    lane.bad(f"parent line: `Closes #6, fixes #9` {closes9}", parent="Closes #6, fixes #9")
    lane.bad(
        "parent line: `Closes #6 closes o/r#6` closes GitHub issue #6",
        parent="Closes #6 closes o/r#6",
    )
    lane.bad(
        "parent line: `Resolves https://github.com/o/r/issues/9` closes GitHub issue #9",
        parent="Closes #6\nResolves https://github.com/o/r/issues/9",
    )
    lane.bad(
        "parent line: cannot name it for branch 'main'", lambda d: d.update(headRefName="main")
    )
    lane.write(".octo-feather.toml", 'tracker = "linear"\n')

    def eng(d: dict[str, Any]) -> None:
        d["headRefName"] = "eng-123"

    lane.pr(eng, parent="Tracks ENG-123")
    out = lane.ask().out
    assert out.split("\n")[0] == "## Merge ask", (
        f"Linear lane with Tracks ENG-123 did not pass: {out}"
    )
    lane.bad(
        "parent line: missing; add the line `Tracks ENG-123` (the tracker skill's pr-line ENG-123)",
        eng,
    )
    not_tracks = "closes GitHub issue #6, not the lane's parent line `Tracks ENG-123`"
    lane.bad(f"parent line: `Closes #6` {not_tracks}", eng, parent="Tracks ENG-123\nCloses #6")
    lane.bad(
        f"parent line: `Tracks ENG-123; Closes #6` {not_tracks}",
        eng,
        parent="Tracks ENG-123; Closes #6",
    )
    lane.bad("parent line: missing; add the line `Tracks ENG-123`", eng, parent="Tracks ENG-1234")


def pr16_body(s: Scratch) -> None:
    """PR #16's real body (fixture): no section, each item named."""
    lane = world(s)
    s.gh.put(16, json.loads(fixture("lane-merge-ask/pr16.json")))
    err = lane.lane(
        "merge-ask", "16", "--status", str(ROOT / "docs" / "specs" / "overview.status.json"), want=1
    ).err
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
        assert f"  - {item}" in err, f"PR #16: {item!r} not named: {err}"


def single_gaps(s: Scratch) -> None:
    """Each single gap fails, naming it: a stale or missing head, a failing or pending check
    (check run or status context), no check reported on a head whose tree holds a workflow."""
    lane = world(s)
    lane.bad(f"Head: names {OTHER[:12]}, the PR's head is {lane.h12} (stale)", head=OTHER[:12])
    lane.bad("Head: missing", head="")
    lane.bad("Checks: failing on head .*: check failure", check(conclusion="FAILURE"), rx=True)
    lane.bad(
        "Checks: pending on head .*: check in_progress",
        check(status="IN_PROGRESS", conclusion=""),
        rx=True,
    )
    lane.bad(
        "Checks: pending on head .*: ci/x pending",
        lambda d: d["statusCheckRollup"][1].update(state="PENDING"),
        rx=True,
    )
    lane.bad(
        "Checks: failing on head .*: ci/x error",
        lambda d: d["statusCheckRollup"][1].update(state="ERROR"),
        rx=True,
    )
    tree(s, lane.h, ci=True)
    lane.bad(
        f"Checks: none reported on head {lane.h12}, its workflows .github/workflows/check.yml; "
        "push the head",
        lambda d: d.update(statusCheckRollup=[]),
    )


def tree(s: Scratch, sha: str, *, ci: bool) -> None:
    """Commit SHA's tree on GitHub: app.py, and with CI .github/workflows/check.yml."""
    entries = [{"path": "app.py", "type": "blob", "sha": "x"}]
    entries += [{"path": ".github", "type": "tree", "sha": "g"}] if ci else []
    s.gh.store(f"{TREES}/{sha}.json", {"sha": sha, "tree": entries})
    s.gh.store(
        f"{TREES}/g.json", {"sha": "g", "tree": [{"path": "workflows", "type": "tree", "sha": "w"}]}
    )
    s.gh.store(
        f"{TREES}/w.json", {"sha": "w", "tree": [{"path": "check.yml", "type": "blob", "sha": "b"}]}
    )


def no_ci(s: Scratch) -> None:
    """No check reported and no workflow file at the head (rule: --help, merge-ask Checks line):
    the base's policy decides, read only then; it passes naming both facts when the base requires
    no check (by protection or ruleset, a plan without rulesets counting as none); required checks
    or an unreadable policy fail naming it; an unreadable tree fails that one item closed, the ask
    still listing every item."""
    lane = world(s)
    tree(s, lane.h, ci=False)
    s.gh.store(f"{BRANCH}.json", UNPROTECTED)
    s.gh.store(f"{RULES}.json", [])
    k = len(s.gh.log())
    lane.bad("Checks: failing on head .*: check failure", check(conclusion="FAILURE"), rx=True)
    assert not [ln for ln in lane.log_from(k) if ln.startswith("api ")], (
        f"a reported check still read the tree: {lane.log_from(k)}"
    )
    h12 = lane.h12
    t = (
        f"no workflow file under .github/workflows at head {h12} (gh api repos/<this "
        f"repo>/git/trees/{h12})"
    )
    lane.pr(none_reported)
    k = len(s.gh.log())
    out = lane.ask().out
    nocheck = (
        f"Checks: no CI: {t}; base main requires no check (gh api repos/<this repo>/branches/main: "
        "no required status check; gh api repos/<this repo>/rules/branches/main: {}), so required "
        "checks are none"
    )
    assert nocheck.format("no required_status_checks rule") in out.split("\n"), (
        f"no-CI head did not pass naming both facts: {out}"
    )
    assert [ln for ln in lane.log_from(k) if ln.startswith("api ")] == [
        f"api repos/{{owner}}/{{repo}}/git/trees/{lane.h}",
        "api repos/{owner}/{repo}/branches/main",
        "api repos/{owner}/{repo}/rules/branches/main",
    ], f"no-CI facts not read at the head and the base: {lane.log_from(k)}"
    s.gh.store(f"{RULES}.error", E403)
    out = lane.ask().out
    assert nocheck.format("rulesets unavailable on this plan, none in force") in out.split("\n"), (
        f"no-ruleset plan did not pass naming it: {out}"
    )
    (s.gh.dir / f"{RULES}.error").unlink()
    prot = {
        "protected": True,
        "protection": {
            "enabled": True,
            "required_status_checks": {
                "enforcement_level": "everyone",
                "contexts": ["ci/legacy"],
                "checks": [{"context": "build", "app_id": 1}],
            },
        },
    }
    s.gh.store(f"{BRANCH}.json", prot)
    lane.bad(
        f"  - Checks: none reported on head {h12}, no workflow file there (gh api repos/<this "
        f"repo>/git/trees/{h12}), but base main requires checks build, ci/legacy (gh api "
        "repos/<this repo>/branches/main, repos/<this repo>/rules/branches/main): push the head "
        "and wait for them",
        none_reported,
    )
    s.gh.store(f"{BRANCH}.json", UNPROTECTED)
    s.gh.store(
        f"{RULES}.json",
        [
            {"type": "deletion"},
            {
                "type": "required_status_checks",
                "parameters": {"required_status_checks": [{"context": "vercel"}]},
            },
        ],
    )
    lane.bad("but base main requires checks vercel (gh api", none_reported)
    s.gh.store(f"{RULES}.json", [])
    s.gh.store(f"{BRANCH}.error", E502)
    lane.bad(
        "but the required checks of base main could not be read (gh api repos/<this "
        f"repo>/branches/main: {E502}): fix gh auth status or read access, then rerun",
        none_reported,
    )
    (s.gh.dir / f"{BRANCH}.error").unlink()
    s.gh.store(f"{BRANCH}.json", {"protected": True})
    lane.bad(
        "but the required checks of base main could not be read (gh api repos/<this "
        "repo>/branches/main: no protection.required_status_checks)",
        none_reported,
    )
    s.gh.store(f"{BRANCH}.json", UNPROTECTED)
    s.gh.store(f"{RULES}.error", E502)
    lane.bad(
        "but the rulesets of base main could not be read (gh api repos/<this "
        f"repo>/rules/branches/main: {E502}): fix gh auth status or read access, then rerun",
        none_reported,
    )
    (s.gh.dir / f"{RULES}.error").unlink()
    # the head's tree unreadable: that one Checks item fails closed naming the read
    s.gh.store(f"{TREES}/{lane.h}.error", E502)
    err = lane.bad(
        "^"
        + re.escape(
            f"  - Checks: none reported on head {h12}, and the no-CI fact could not be read "
            f"(gh api repos/{{owner}}/{{repo}}/git/trees/{lane.h} failed ({E502})"
        ),
        none_reported,
        rx=True,
    )
    assert "merge ask incomplete" in err, f"an unreadable tree aborted the ask: {err}"
    assert re.search("^Gate time", err, re.MULTILINE), f"an unreadable tree aborted the ask: {err}"


def ci_status_only(s: Scratch) -> None:
    """issue-lifecycle#acceptance-ci-status-only (the rule: #lanes-one-head): check SKIPPED on
    qc's commit H; J's CI carried by the Judged proof, or refused: missing, pending, skipped or
    red on J, no proof (a code commit between J and the status-only head), or H the judged head
    itself (a draft's run, PR #608 at d0e4381)."""
    lane = world(s)
    skipped = check(conclusion="SKIPPED")
    j12, h12 = lane.j12, lane.h12
    skip = (
        f"Checks: check skipped on head {h12}, carried from the judged head {j12} by the Judged "
        "proof,"
    )
    lane.runs(lane.j, [])
    lane.bad(f"{skip} and {j12} has no check run", skipped)

    def run(i: int, status: str, conclusion: str | None) -> dict[str, object]:
        return {"id": i, "name": "check", "status": status, "conclusion": conclusion}

    lane.runs(lane.j, [run(2, "in_progress", None)])
    lane.bad(f"{skip} and pending on {j12}: check in_progress", skipped)
    lane.runs(lane.j, [run(2, "completed", "failure")])
    lane.bad(f"{skip} and failing on {j12}: check failure", skipped)
    lane.runs(lane.j, [run(2, "completed", "skipped")])  # J's own run skipped (a draft PR)
    lane.bad(f"{skip} and skipped on {j12} too: CI never ran there", skipped)
    # the demo: J's latest check run passed (an earlier one skipped while the PR was a draft)
    lane.runs(lane.j, [run(3, "completed", "success"), run(1, "completed", "skipped")])
    lane.pr(skipped)
    out = lane.ask().out
    assert f"- check: skipped on {h12}; success on {j12}, the judged head" in out.split("\n"), (
        f"a status-only head did not pass on the judged head's CI, naming it: {out}"
    )
    assert any(
        f"api repos/{{owner}}/{{repo}}/commits/{lane.j}/check-runs" in ln for ln in s.gh.log()
    ), f"J's check runs not read from GitHub: {s.gh.log()}"
    c = lane.on(
        lane.h, lambda: lane.append("app.py", "fix\n"), lambda: lane.git("commit", "-qam", "fix: y")
    )
    st = lane.on(
        c,
        lambda: lane.git(
            "commit",
            "-q",
            "--allow-empty",
            "-m",
            f"qc: built acceptance-a acceptance-b (judged {j12})",
        ),
    )
    err = lane.bad(
        f"Checks: skipped on head {st[:12]}: check; a skipped check is no pass and no Judged "
        "proof carries",
        skipped,
        pr_head(c, "fix: y"),
        pr_head(st, "x"),
        head=st[:12],
    )
    assert f"Judged: commit {c[:12]} 'fix: y' after the judged head {j12} changes app.py" in err, (
        f"a code commit before the status-only head: {err}"
    )
    lane.bad(
        f"Checks: skipped on head {j12}: check; a skipped check is no pass",
        skipped,
        lambda d: d.update(headRefOid=lane.j),
        head=j12,
        judged=f"{j12} is the PR head",
    )


def rows_and_built(s: Scratch) -> None:
    """Rows and Built: a missing row, no evidence, a verdict not pass or fail, a row of no
    criterion, Built unequal to the status files; the PR's commits and subjects read from git
    (BASE..head), so each case is a real lane head: a Built id no `qc: built` commit names fails,
    one built by an earlier qc run and reset to planned by a later (PR #49: ac060f9, a56de61) is
    not demanded, and a lane with no `qc: built` commit fails."""
    lane = world(s)
    js = f"judged {lane.js}"
    lane.bad(
        "criterion row demo#acceptance-b: missing (it is in Built)",
        rows=row("demo#acceptance-a", js),
    )
    lane.bad(
        "criterion row demo#acceptance-b: no evidence",
        rows=row("demo#acceptance-a", js) + f"\n| demo#acceptance-b | pass | {js} | |",
    )
    lane.bad(
        "qc verdict 'ok'; write pass or fail",
        rows=row("demo#acceptance-a", js) + "\n" + row("demo#acceptance-b", js, "ok"),
    )
    lane.bad("acceptance-zz: no criterion", rows=lane.rows(row("demo#acceptance-zz", js)))
    lane.bad(
        "Built: lists demo#acceptance-a, the status files hold built with PR #7: demo#acceptance-a "
        "demo#acceptance-b",
        built="demo#acceptance-a",
    )
    j12 = lane.j12
    qa = lane.on(
        lane.h,
        lambda: lane.git("commit", "-q", "--amend", "-m", f"qc: built acceptance-a (judged {j12})"),
    )
    lane.bad(
        r"Built: demo#acceptance-b in no .qc: built. commit of PR #7 \(they passed acceptance-a\); "
        "built only by just qc",
        pr_head(qa, "x"),
        rx=True,
        head=qa[:12],
        judged=f"{j12} to {qa[:12]}: qc status commits {qa[:12]} change only {STATUS}",
    )
    q1 = lane.on(
        lane.j,
        lambda: lane.git(
            "commit",
            "-q",
            "--allow-empty",
            "-m",
            "qc: built acceptance-a acceptance-c (judged 0123456789ab)",
        ),
    )

    def q2_steps() -> None:
        lane.git("checkout", "-q", lane.h, "--", STATUS)
        lane.git("commit", "-qm", f"qc: built acceptance-a acceptance-b (judged {j12})")

    q2 = lane.on(q1, q2_steps)
    lane.pr(
        pr_head(q2, "x"),
        head=q2[:12],
        judged=f"{j12} to {q2[:12]}: qc status commits {q1[:12]} {q2[:12]} change only {STATUS}",
    )
    lane.ask()
    qn = lane.on(lane.h, lambda: lane.git("commit", "-q", "--amend", "-m", "chore: status"))
    lane.bad("no .qc: built. commit on PR #7", pr_head(qn, "x"), rx=True, head=qn[:12])


def review_link(s: Scratch) -> None:
    """The review verdict link: empty, on another PR, a comment not on the PR, naming another
    head, blocking, with no check classification, clear with a proxy check, no marker, each
    refused; an exact check listed. A failed criterion: untriaged, a bullet with no triage, a
    triaged id with no row, a Failed line other than none or bullets."""
    lane = world(s)
    lane.bad("Review verdict: empty is not a comment on PR #7", review="")
    lane.bad("is not a comment on PR #7", review="https://github.com/o/r/pull/8#issuecomment-1001")
    lane.bad("comment 4242 not on PR #7", review=lane.url.removesuffix("1001") + "4242")
    lane.bad(
        f"the comment names head {OTHER}, not the judged head {lane.j12}",
        verdict_says(f"Head: {lane.j}", f"Head: {OTHER}"),
    )
    lane.bad(
        "Review verdict: blocking, not clear", verdict_says("Verdict: clear", "Verdict: blocking")
    )
    lane.bad(
        "Review verdict: the comment carries no usable check classification (report "
        "classifies no check",
        verdict_says("\nChecks: none\n", "\n"),
    )
    lane.bad(
        "Review verdict: clear with a proxy check (Check: scripts/x: r (ADR 1) | reads: y | class: "
        "proxy): a proxy check blocks",
        verdict_says("Checks: none", "Check: scripts/x: r (ADR 1) | reads: y | class: proxy"),
    )
    exact = "Check: scripts/x: r (ADR 1) | reads: y | class: exact"
    lane.pr(verdict_says("Checks: none", exact))
    w = before_gate_time(lane.ask().out)
    assert w.split("\n")[-1] == f"- {exact}", f"exact check not listed: {w}"
    lane.bad(
        "is not a verdict comment (no marker)",
        lambda d: d["comments"][0].update(body="Verdict: clear"),
    )
    c_fail = row("demo#acceptance-c", f"judged {lane.js}", "fail")
    lane.bad("criterion row demo#acceptance-c: fail with no triage", rows=lane.rows(c_fail))
    lane.bad(
        "Failed: demo#acceptance-c has no triage",
        rows=lane.rows(c_fail),
        failed="Failed:\n- acceptance-c:",
    )
    lane.bad(
        "criterion row demo#acceptance-c: missing (it is in Failed)",
        failed="Failed:\n- acceptance-c: repair ticket #9",
    )
    lane.bad("Failed: 'some'; write", failed="Failed: some")


def one_judged_head(s: Scratch) -> None:
    """One judged head (spec #acceptance-one-head): review and qc judged J; the PR head may add
    only qc's status commit, with the check's proof line. Refused: no proof line, rows on two
    heads, a code commit after qc, qc's own commit carrying a non-status file, a hand status
    edit. qc rerun at the exact head, nothing to flip, no status commit: passes."""
    lane = world(s)
    lane.pr()
    out = lane.ask().out
    assert f"Judged: {lane.proof}" in out, f"pass did not print the proof: {out}"
    lane.bad(f"Judged: names ''; add the check's proof line `Judged: {lane.proof}`", judged="")
    js = f"judged {lane.js}"
    lane.bad(
        "rows name 2 judged heads",
        rows=row("demo#acceptance-a", js) + "\n" + row("demo#acceptance-b", f"judged {lane.h[:7]}"),
    )
    j12 = lane.j12
    f = lane.on(
        lane.h,
        lambda: lane.append("app.py", "two\n"),
        lambda: lane.git("commit", "-qam", "feat: after qc"),
    )
    lane.on(f, lane.record)
    lane.bad(
        f"Judged: commit {f[:12]} 'feat: after qc' after the judged head {j12} changes app.py, not "
        f"only the status file qc writes ({STATUS}): run just qc and the review again, in "
        f"parallel, on {f[:12]}",
        pr_head(f, "feat: after qc"),
        head=f[:12],
    )

    def stray() -> None:
        text = (lane.repo / STATUS).read_text()
        lane.write(
            STATUS,
            text.replace(
                '"planned", "pr": null}, "acceptance-b', '"built", "pr": 7}, "acceptance-b', 1
            ),
        )
        lane.write("stray.txt", "x\n")
        lane.commit(f"qc: built acceptance-a (judged {j12})")

    q = lane.on(lane.j, stray)
    lane.bad(
        f"commit {q[:12]} 'qc: built acceptance-a (judged {j12})' after the judged head {j12} "
        "changes stray.txt, not only",
        pr_head(q, f"qc: built acceptance-a (judged {j12})"),
        head=q[:12],
    )
    st = lane.on(
        lane.h, lambda: lane.append(STATUS, " \n"), lambda: lane.git("commit", "-qam", "fix status")
    )
    lane.bad(
        f"commit {st[:12]} 'fix status' after the judged head {j12} is not a .qc: built",
        pr_head(st, "fix status"),
        rx=True,
        head=st[:12],
    )
    lane.pr(
        pr_head(f, "feat: after qc"),
        verdict_says(f"Head: {lane.j}", f"Head: {f}"),
        head=f[:12],
        judged=f"{f[:12]} is the PR head",
        rows=lane.rows(judged=f"judged {f[:9]}"),
    )
    lane.ask()


def main_merges(s: Scratch) -> None:
    """A clean main merge keeps the qc verdict: the check asks for its proof line, then passes
    printing it. A main merge touching a lane file, resolving a conflict, or merging another
    branch: qc reruns."""
    lane = world(s)
    j12, h12 = lane.j12, lane.h12
    m1 = lane.main_commit()
    r1 = lane.merge(lane.h, m1)
    err = lane.bad(
        r"add the check's proof line .Judged: "
        + re.escape(
            f"{j12} to {r1[:12]}: qc status commits {h12} change only {STATUS}; clean merge of "
            f"main {r1[:12]}: lane diff identical (1 file, sha256 "
        )
        + r"[0-9a-f]{12}\).",
        pr_head(r1, "Merge main"),
        rx=True,
        head=r1[:12],
    )
    proof = proof_asked(err)
    lane.pr(pr_head(r1, "Merge main"), head=r1[:12], judged=proof)
    out = lane.ask().out
    assert f"Judged: {proof}" in out, f"clean refresh: proof not in the section: {out}"
    m2 = lane.on(
        m1,
        lambda: lane.set_line("app.py", 20, "twenty"),
        lambda: lane.git("commit", "-qam", "main: app tail"),
    )
    lane.main_at(m2)
    r2 = lane.merge(lane.h, m2)
    lane.bad(
        "Judged: after merging origin/main, the lane's own diff changed in app.py (main touched a "
        "lane file, or the lane's diff moved): the qc verdict does not carry over; run just qc and "
        f"the review again, in parallel, on {r2[:12]}",
        pr_head(r2, "Merge main"),
        head=r2[:12],
    )
    m3 = lane.on(
        m1,
        lambda: lane.set_line("app.py", 1, "uno"),
        lambda: lane.git("commit", "-qam", "main: app head"),
    )
    lane.main_at(m3)

    def resolve() -> None:
        lane.git("merge", "-q", "--no-edit", m3, want=1)
        lane.git("checkout", "-q", "--ours", "app.py")
        lane.git("commit", "-qam", "Merge main, conflict resolved")

    r3 = lane.on(lane.h, resolve)
    lane.bad(
        f"Judged: merge {r3[:12]} 'Merge main, conflict resolved' resolved a conflict with "
        "origin/main: the qc verdict does not carry over",
        pr_head(r3, "Merge main, conflict resolved"),
        head=r3[:12],
    )
    lane.main_at(m1)
    x = lane.on(lane.b, lambda: lane.write("side.txt", "side\n"), lambda: lane.commit("side"))
    r4 = lane.merge(lane.h, x)
    lane.bad(
        f"Judged: merge {r4[:12]} .* brings in {x[:12]}, not origin/main: only a merge of main "
        "keeps the qc verdict",
        pr_head(r4, "Merge side"),
        rx=True,
        head=r4[:12],
    )


def full_pass(s: Scratch) -> None:
    """issue-lifecycle#acceptance-merge-ask-full-proof (rule: #lanes-checkpoints): the passes
    stand on J's recorded full pass (H adds only qc's status commit). A head with no recorded
    full pass refuses, naming it and the missing pass, the section otherwise complete; a pass
    whose gate configuration is not the head's (main brought a justfile, or changed the
    shared-machinery list) is stale; a pass recorded on a dirty tree (an untracked file beside
    the gate) proves nothing; a lane building no criterion is checked the same (PR #8)."""
    lane = world(s, pr8=True)
    j12 = lane.j12

    def own_head(c: str, subject: str) -> None:
        """PR #7 at C, a commit after H, with the review and qc on C, the section complete."""
        lane.pr(
            pr_head(c, subject),
            verdict_says(f"Head: {lane.j}", f"Head: {c}"),
            head=c[:12],
            judged=f"{c[:12]} is the PR head",
            rows=lane.rows(judged=f"judged {c[:9]}"),
        )

    e = lane.on(
        lane.h,
        lambda: lane.append("app.py", "e\n"),
        lambda: lane.git("commit", "-qam", "feat: no full pass"),
    )
    own_head(e, "feat: no full pass")
    err = lane.ask(want=1).err
    assert (
        f"(1 item), head {e[:12]}:\n  - Full pass: head {e[:12]} {FULL}; the full pass recorded "
        f"at {j12} does not carry over: commit {e[:12]} 'feat: no full pass' after the full pass "
        f"{j12} changes app.py"
    ) in err, f"a head with no full pass: {err}"
    m1 = lane.main_commit()
    for name, change, stale in (
        ("main: a gate", ("justfile", "check:\n    true\n"), "its gate_config [0-9a-f]{12}"),
        (
            "main: a shared-machinery list",
            ("shared-machinery.txt", "machinery\n"),
            "its list absent",  # a checkpoint: the list changed, J's pass was recorded against none
        ),
    ):
        m = lane.on(m1, lambda c=change: lane.write(*c), lambda n=name: lane.commit(n))
        lane.main_at(m)
        r = lane.merge(lane.h, m)
        lane.bad(
            re.escape(
                f"Full pass: head {r[:12]} {FULL}; the full pass recorded at {j12} does not carry "
                "over: "
            )
            + stale
            + re.escape(" is not the head's current ")
            + "[0-9a-f]{12}"
            + re.escape(f" (octo-feather-gate config {r[:12]}): stale"),
            pr_head(r, "Merge main"),
            rx=True,
            head=r[:12],
        )
    lane.main_at(m1)

    def dirty_pass() -> None:
        lane.append("app.py", "d\n")
        lane.git("commit", "-qam", "feat: dirty pass")
        lane.write("dirt", "x\n")
        lane.record("dirty")
        (lane.repo / "dirt").unlink()

    d = lane.on(lane.h, dirty_pass)
    own_head(d, "feat: dirty pass")
    err = lane.ask(want=1).err
    assert (
        f"(1 item), head {d[:12]}:\n  - Full pass: head {d[:12]} {FULL}; the full pass recorded at "
        f"{d[:12]} does not carry over: it was recorded on a dirty tree (clean false): it proves "
        "nothing"
    ) in err, f"a pass recorded on a dirty tree: {err}"
    # a lane building no criterion: its head without a recorded full pass refuses
    n2 = lane.on(
        lane.n,
        lambda: lane.append("app.py", "four\n"),
        lambda: lane.git("commit", "-qam", "fix: no full pass"),
    )
    lane.pr8(
        n2,
        lane.nbody(head=n2[:12]),
        verdict_says(f"Head: {lane.n}", f"Head: {n2}"),
        extra=(n2, "fix: no full pass"),
    )
    err = lane.lane("merge-ask", "8", want=1).err
    assert f"(1 item), head {n2[:12]}:\n  - Full pass: head {n2[:12]} {FULL}" in err, (
        f"no-criterion lane without a full pass: {err}"
    )


def judged_rows(s: Scratch) -> None:
    """A row's judged column names a commit of the PR, as `judged <sha>`; a table with no judged
    column is refused. Multi-spec lane: --status once per spec; a qc id outside the --status files
    is not demanded."""
    lane = world(s)
    js = f"judged {lane.js}"
    lane.bad(
        "criterion row demo#acceptance-a: judged deadbee is not a commit of PR #7; name the head "
        "qc and the review judged",
        rows=row("demo#acceptance-a", "judged deadbee") + "\n" + row("demo#acceptance-b", js),
    )
    lane.bad(
        "judged 'yesterday'; write .judged <sha>.",
        rows=row("demo#acceptance-a", "yesterday") + "\n" + row("demo#acceptance-b", js),
        rx=True,
    )
    old = lane.body().replace(
        HDR.split("\n", maxsplit=1)[0], "| criterion | qc verdict | evidence |"
    )
    lane.bad("criterion table: no judged column", lambda d: d.update(body=old))
    qx = lane.on(
        lane.h,
        lambda: lane.git(
            "commit", "-q", "--allow-empty", "-m", "qc: built acceptance-x (judged 0123456789ab)"
        ),
    )
    judged = f"{lane.j12} to {qx[:12]}: qc status commits {lane.h12} {qx[:12]} change only {STATUS}"
    lane.pr(pr_head(qx, "x"), head=qx[:12], judged=judged)
    lane.ask()
    lane.pr(
        pr_head(qx, "x"),
        head=qx[:12],
        judged=judged,
        rows=lane.rows(row("other#acceptance-x", js)),
        built="acceptance-a acceptance-b other#acceptance-x",
    )
    lane.ask("--status", "docs/specs/other.status.json")


def usage_failures(s: Scratch) -> None:
    """Usage and execution failures: no --status, an unreadable one, PR 0, a failed read, gh data
    lacking fields (an older gh's answer); nothing written."""
    lane = world(s)
    lane.pr()
    err = lane.lane("merge-ask", "7", want=1).err
    assert "name the lane's status file" in err, f"no --status: {err}"
    err = lane.lane("merge-ask", "7", "--status", str(s.root / "nope.json"), want=1).err
    assert "not a readable status file" in err, f"bad --status: {err}"
    err = lane.lane("merge-ask", "0", *ST, want=1).err
    assert "positive integer" in err, f"PR 0: {err}"
    (s.gh.dir / "down").touch()
    err = lane.ask(want=1).err
    assert re.search("error connecting.*gh auth status", err), f"failed read: {err}"
    (s.gh.dir / "down").unlink()
    s.gh.store("pr/7.out", '{"number": 7}\n')
    err = lane.ask(want=1).err
    assert "lacks fields" in err, f"short gh data: {err}"
    assert s.gh.writes() == 0, f"a merge-ask wrote: {s.gh.log()}"


def no_criterion_lane(s: Scratch) -> None:
    """A lane that builds no criterion (spec #lanes-one-head, #acceptance-merge-ask-no-criterion):
    PR #8, commit N off main, no qc commit; Built: none, Failed: none, no rows: passes on head,
    checks, parent line and the review verdict alone, --status optional, with no table or a
    header; each item still checked; the verdict names another head: a code commit after it has
    no proof, a clean main merge needs its proof line."""
    lane = world(s, pr8=True)
    n, n12 = lane.n, lane.n[:12]
    for tbl in ("", HDR):
        for st in ((), ST):
            lane.pr8(n, lane.nbody(table=tbl))
            out = lane.lane("merge-ask", "8", *st).out
            ls = out.split("\n")
            said = f"no-criterion lane (table {tbl[:5]!r}, status {st}) did not pass: {out}"
            assert ls[0] == "## Merge ask", said
            assert "Built: none" in ls, said

    def refused(want: str, *args: str, rx: bool = False) -> str:
        err = lane.lane("merge-ask", "8", *args, want=1).err
        assert re.search(want, err) if rx else want in err, f"PR #8 did not say {want!r}: {err}"
        return err

    lane.pr8(n, lane.nbody(head=OTHER[:12]))
    refused(f"Head: names {OTHER[:12]}")
    lane.pr8(n, lane.nbody(), check(conclusion="FAILURE"))
    refused("Checks: failing")
    lane.pr8(n, lane.nbody().split("\n", 1)[1])
    refused("parent line: missing")
    lane.pr8(n, lane.nbody(), verdict_says("Verdict: clear", "Verdict: blocking"))
    refused("Review verdict: blocking, not clear")
    lane.pr8(n, lane.nbody(), verdict_says("\nChecks: none\n", "\n"))
    err = refused("carries no usable check classification")
    assert "criterion table" not in err, f"no-criterion lane asked for a table: {err}"
    assert "qc: built" not in err, f"no-criterion lane asked for a qc commit: {err}"
    nf = lane.on(
        n, lambda: lane.append("app.py", "three\n"), lambda: lane.git("commit", "-qam", "fix: more")
    )
    lane.pr8(nf, lane.nbody(head=nf[:12]), extra=(nf, "fix: more"))
    refused(f"Judged: commit {nf[:12]} 'fix: more' after the judged head {n12} changes app.py")
    m1 = lane.main_commit()
    nm = lane.merge(n, m1)
    lane.pr8(nm, lane.nbody(head=nm[:12]), extra=(nm, "Merge main"))
    err = refused(
        rf"Judged: missing; add the check's proof line .Judged: {n12} to {nm[:12]}: no qc status "
        rf"commit; clean merge of main {nm[:12]}: lane diff identical",
        rx=True,
    )
    proof8 = proof_asked(err)
    lane.pr8(nm, lane.nbody(head=nm[:12], judged=f"Judged: {proof8}"), extra=(nm, "Merge main"))
    out = lane.lane("merge-ask", "8").out
    assert f"Judged: {proof8}" in out, f"no-criterion clean merge with proof: {out}"


def criterion_claimed(s: Scratch) -> None:
    """PR #8: a lane that claims a criterion with no rows (a qc commit, a Built or Failed id, a
    status entry built with the PR) is still refused naming the table
    (#acceptance-merge-ask-evidence); with a Built id and no --status, asked for it."""
    lane = world(s, pr8=True)
    n = lane.n
    lane.main_commit()

    def refused(want: str, *args: str) -> None:
        err = lane.lane("merge-ask", "8", *args, want=1).err
        assert want in err, f"PR #8 did not say {want!r}: {err}"

    nq = lane.on(
        n,
        lambda: lane.git(
            "commit", "-q", "--allow-empty", "-m", "qc: built acceptance-a (judged 0123456789ab)"
        ),
    )
    s8 = lane.file(
        "s8.json",
        "\n".join(
            ln.replace('"planned", "pr": null', '"built", "pr": 8', 1)
            for ln in (lane.repo / STATUS).read_text().split("\n")
        ),
    )
    for tbl in ("", HDR):
        want = "criterion table: " + ("missing" if not tbl else "no rows")
        lane.pr8(nq, lane.nbody(head=nq[:12], table=tbl))
        refused(want, *ST)
        lane.pr8(n, lane.nbody(table=tbl, built="demo#acceptance-a"))
        refused(want, *ST)
        lane.pr8(n, lane.nbody(table=tbl, failed="Failed:\n- acceptance-c: repair ticket #9"))
        refused(want, *ST)
        lane.pr8(n, lane.nbody(table=tbl))
        refused(want, "--status", s8)
    lane.pr8(n, lane.nbody(built="acceptance-a"))
    refused("name the lane's status file")


def many_commits(s: Scratch) -> None:
    """More than 100 commits: `gh pr view --json commits` lists at most 100, so the PR's commits
    are read from git (BASE..head). PR #8's head NL is the 101st commit off main; the fake gh
    lists only the first 100, as GitHub does. verdict accepts NL and merge-ask passes on it."""
    lane = world(s, pr8=True)
    stream = "".join(
        f"commit refs/heads/many\ncommitter t <t@example.com> {1_800_000_000 + i} +0000\n"
        f"data {len(f'chore: step {i}')}\nchore: step {i}\n"
        + (f"from {lane.b}\n" if i == 1 else "")
        + f"M 100644 inline many.txt\ndata {len(str(i)) + 1}\n{i}\n\n"
        for i in range(1, 102)
    )
    s.run(["git", "-C", str(lane.repo), "fast-import", "--quiet"], stdin=stream)
    nl = lane.git("rev-parse", "refs/heads/many")
    lane.on(nl, lane.record)
    first = lane.git("rev-list", "--reverse", f"{lane.b}..{nl}").split("\n")[:100]
    cap = [{"oid": c, "messageHeadline": "chore", "messageBody": ""} for c in first]
    lane.pr8(nl, lane.nbody(head=nl[:12]), lambda d: d.update(commits=cap))
    d = s.gh.pr(8)
    shas = {cast("dict[str, str]", c)["oid"] for c in cast("list[object]", d["commits"])}
    assert len(shas) == 100, "the 101-commit PR does not cap its commits at 100"
    assert nl not in shas, "the 101-commit PR lists its head"
    r = lane.verdict("8", nl, REPORT)
    assert f"(clear, head {nl[:12]})" in r.err, f"verdict on the 101st commit of a PR: {r.err}"
    out = lane.lane("merge-ask", "8").out
    assert out.split("\n")[0] == "## Merge ask", (
        f"merge-ask on a PR of 101 commits did not pass: {out}"
    )


def fields_label(s: Scratch) -> None:
    """fields: a label of words one space apart is a field (Prior art: code-review step 4, Report
    fields); two spaces is not."""
    f = s.root / "fields"
    f.write_text("Checks: none\nPrior art: PyYAML 6.0.2 | license: MIT\nPrior  art: x\n")
    out = s.run([kit("octo-feather-lane"), "fields", str(f)]).out
    got = json.loads(out)["fields"]
    assert got == {"Prior art": ["PyYAML 6.0.2 | license: MIT"]}, (
        f"fields: Prior art not read as one field: {out}"
    )


if __name__ == "__main__":
    main(
        verdict_posts,
        verdict_reader_scope,
        verdict_check_classes,
        verdict_refusals,
        verdict_write_fails,
        offline_gh,
        merge_ask_passes,
        gate_time,
        failed_triage,
        parent_line,
        pr16_body,
        single_gaps,
        no_ci,
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
        fields_label,
    )
