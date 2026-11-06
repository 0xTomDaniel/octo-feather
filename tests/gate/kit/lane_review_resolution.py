"""The scenario of tests/gate/kit/test_lane_review_resolution.py (its item), this file its command
(testkit.main): the review of a main merge's resolution (the rule: issue-lifecycle
#lanes-one-head), no network: the testkit's fake gh holds PR #7 of o/r. `octo-feather-lane
resolution` prints a conflicted merge's remerge diff and its files; `verdict --resolution` posts a
verdict naming the merge and only those files; merge-ask passes on the earlier review verdict with
it and refuses without it, naming the merge; a fix commit after the reviewed head needs a full
review.

The lane, prepared once per gate run (testkit Scratch.prepare): main B; the lane's code J
(reviewed, clear) and qc's status commit H. Main then changes the lane's line of app.py (a
conflict) and notes.txt (no lane file); the lane merges it as M, resolving the conflict by hand;
qc reruns on M (its status commit H2, the PR head). M's full gate pass is recorded.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, cast

from testkit import Ran, Scratch, kit, main

if TYPE_CHECKING:
    from collections.abc import Callable

STATUS = "docs/specs/demo.status.json"
ST = ("--status", STATUS)
CLEAR = "Findings: none blocking.\nChecks: none\nVerdict: clear\n"
BLOCKING = "Findings: the resolution drops main.\nChecks: none\nVerdict: blocking\n"
CHECK_OK = [
    {"__typename": "CheckRun", "name": "check", "status": "COMPLETED", "conclusion": "SUCCESS"}
]
RESOLVED = "Merge main, conflict resolved"


class Lane:
    """The lane repo in S and its heads (saved beside it, heads.json)."""

    def __init__(self, s: Scratch) -> None:
        self.s, self.repo = s, s.root / "repo"
        s.env.pop("HERDR_SESSION", None)
        s.env |= {"XDG_STATE_HOME": str(s.root / "xdg"), "OCTO_FEATHER_QC_DIR": str(s.root / "qc")}
        (s.root / "clear").write_text(CLEAR)
        (s.root / "blocking").write_text(BLOCKING)
        heads = s.root / "heads.json"
        self.h: dict[str, str] = json.loads(heads.read_text()) if heads.exists() else {}

    def git(self, *args: str, want: int = 0) -> str:
        return self.s.run(["git", "-C", str(self.repo), *args], want=want).out

    def commit(self, msg: str) -> str:
        self.git("add", "-A")
        self.git("commit", "-q", "-m", msg)
        return self.git("rev-parse", "HEAD")

    def on(self, parent: str, *steps: Callable[[], object]) -> str:
        """STEPS run on a detached checkout of PARENT; the new HEAD, back on the lane."""
        self.git("checkout", "-q", "--detach", parent)
        for step in steps:
            step()
        sha = self.git("rev-parse", "HEAD")
        self.git("checkout", "-q", "-f", "lane")
        return sha

    def set_app(self, line1: str) -> None:
        p = self.repo / "app.py"
        p.write_text(line1 + "\n" + p.read_text().split("\n", 1)[1])

    def resolved_merge(self) -> None:
        """Merge main, resolving app.py's conflict by keeping the lane's line."""
        self.git("merge", "-q", "--no-edit", self.h["main"], want=1)
        p = self.repo / "app.py"
        conflict = ("<<<<<<<", "=======", ">>>>>>>")
        p.write_text(
            "".join(
                x
                for x in p.read_text().splitlines(keepends=True)
                if not x.startswith(conflict) and x != "uno\n"
            )
        )
        self.git("commit", "-qam", RESOLVED)

    def qc(self, judged: str) -> None:
        """qc's status-only commit, judged JUDGED."""
        with (self.repo / STATUS).open("a") as f:
            f.write("\n")
        self.git("commit", "-qam", f"qc: built acceptance-a (judged {judged[:12]})")

    def record(self) -> None:
        """A full gate pass recorded at the checked-out commit."""
        self.s.run(
            [kit("octo-feather-gate"), "record", "--reason", "lane final head", "--seconds", "1"],
            cwd=self.repo,
        )

    def lane(self, want: int, *args: str) -> Ran:
        return self.s.run([kit("octo-feather-lane"), *args], want=want, cwd=self.repo)

    def body(self, head: str, judged: str, reviewed: str = "") -> str:
        h, j = head[:12], judged[:12]
        return (
            f"Closes #6\n\n## Merge ask\n\nHead: {h}\nChecks: check pass\nJudged: {j} to {h}: qc "
            f"status commits {h} change only {STATUS}\n| criterion | qc verdict | judged | "
            f"evidence |\n|---|---|---|---|\n| demo#acceptance-a | pass | judged {j} | r |\n"
            f"Review verdict: {self.h['url']}\n{reviewed}Built: demo#acceptance-a\nFailed: none\n"
        )

    def setpr(self, head: str, body: str) -> None:
        self.s.gh.put(7, self.s.gh.pr(7) | {"headRefOid": head, "body": body})


def build(p: Scratch) -> None:
    lane = Lane(p)
    r = lane.repo
    (r / "docs" / "specs").mkdir(parents=True)
    p.git(r, "init", "-q", "-b", "main")
    for k, v in (("user.email", "t@example.com"), ("user.name", "t"), ("commit.gpgsign", "false")):
        lane.git("config", k, v)
    (r / STATUS).write_text(
        '{"spec": "demo.spec.html", "accepted_commit": "0123abc", "criteria": {"acceptance-a": '
        '{"status": "planned", "pr": null}}}\n'
    )
    (r / "app.py").write_text("".join(f"{i}\n" for i in range(1, 21)))
    (r / "notes.txt").write_text("notes\n")
    h = lane.h
    h["b"] = lane.commit("base")
    lane.git("update-ref", "refs/remotes/origin/main", h["b"])
    lane.git("checkout", "-q", "-b", "lane")
    lane.set_app("one")
    h["j"] = lane.commit("feat: x")
    (r / STATUS).write_text(
        (r / STATUS).read_text().replace('"planned", "pr": null', '"built", "pr": 7')
    )
    h["h"] = lane.commit(f"qc: built acceptance-a (judged {h['j'][:12]})")

    def main_two() -> None:
        lane.set_app("uno")
        with (r / "notes.txt").open("a") as f:
            f.write("main\n")
        lane.git("commit", "-qam", "main: two files")

    h["main"] = lane.on(h["b"], main_two)
    lane.git("update-ref", "refs/remotes/origin/main", h["main"])
    h["m"] = lane.on(h["h"], lane.resolved_merge)
    app = lane.git("show", f"{h['m']}:app.py").split("\n")[:2]
    assert app == ["one", "2"], f"fixture: the resolution kept {app}"
    h["h2"] = lane.on(h["m"], lambda: lane.qc(h["m"]))
    lane.on(h["m"], lane.record)
    p.gh.put(
        7,
        {
            "number": 7,
            "baseRefName": "main",
            "headRefName": "gh6",
            "headRefOid": h["h2"],
            "body": "",
            "statusCheckRollup": CHECK_OK,
            "comments": [],
        },
    )
    h["url"] = lane.lane(0, "verdict", "7", h["j"], str(p.root / "clear")).out  # J's review
    (p.root / "heads.json").write_text(json.dumps(h))


def resolution(s: Scratch) -> None:
    """issue-lifecycle#acceptance-review-resolution: without a resolution verdict merge-ask refuses
    naming the merge; `resolution` prints the remerge diff and only the files the resolution
    changed (notes.txt is main's own change), and refuses a non-merge; the resolution verdict names
    the merge and only its files; merge-ask then asks for the Reviewed proof, then passes printing
    it; a blocking resolution verdict keeps nothing; a fix commit after the reviewed head still
    needs a full fresh review; --resolution on a merge with nothing beyond git's automatic merge is
    refused; a lane that builds no criterion: the same rule. Nothing but the verdicts written."""
    s.prepare("lane-review-resolution", build)
    lane = Lane(s)
    h, clear = lane.h, str(s.root / "clear")
    j12, m12 = h["j"][:12], h["m"][:12]
    lane.setpr(h["h2"], lane.body(h["h2"], h["m"]))
    r = lane.lane(1, "merge-ask", "7", *ST)
    want = (
        f"Review verdict: merge {m12} '{RESOLVED}' resolved a conflict with origin/main: the "
        "review verdict does not carry over without a clear resolution verdict naming it"
    )
    assert want in r.err, f"no resolution verdict: not refused naming the merge: {r.err}"
    r = lane.lane(0, "resolution", m12)
    head = (
        f"Resolution of merge {h['m']} '{RESOLVED}' (git show --remerge-diff; issue-lifecycle "
        "#lanes-one-head):"
    )
    assert r.out.split("\n")[:2] == [head, "Files: app.py"], f"resolution header: {r.out}"
    assert "-uno" in r.out.split("\n"), f"resolution printed less than the remerge diff: {r.out}"
    assert "notes.txt" not in r.out, f"resolution printed more than the remerge diff: {r.out}"
    r = lane.lane(1, "resolution", j12)
    assert f"commit {j12} is not a merge" in r.err, f"resolution of a non-merge: {r.err}"
    rurl = lane.lane(0, "verdict", "7", m12, clear, "--resolution").out
    comments = cast("list[dict[str, str]]", s.gh.pr(7)["comments"])
    body = next(c["body"] for c in comments if c["url"] == rurl)
    assert f"\nMerge: {h['m']}\nFiles: app.py\n" in body, f"resolution verdict body: {body}"
    assert "\nVerdict: clear\n" in body, f"resolution verdict body: {body}"
    r = lane.lane(1, "merge-ask", "7", *ST)
    want = (
        f"Reviewed: {j12} to {m12}: qc status commits {h['h'][:12]} change only {STATUS}; "
        f"resolution of merge {m12} (app.py) reviewed clear: {rurl}"
    )
    assert f"Reviewed: missing; add the check's proof line `{want}`" in r.err, (
        f"no Reviewed line: {r.err}"
    )
    lane.setpr(h["h2"], lane.body(h["h2"], h["m"], want + "\n"))
    r = lane.lane(0, "merge-ask", "7", *ST)
    assert want in r.out.split("\n"), f"pass did not print the Reviewed proof: {r.out}"
    lane.lane(0, "verdict", "7", m12, str(s.root / "blocking"), "--resolution")
    r = lane.lane(1, "merge-ask", "7", *ST)
    assert f"Review verdict: merge {m12} '{RESOLVED}' resolved a conflict" in r.err, (
        f"blocking resolution verdict kept the review: {r.err}"
    )
    lane.lane(0, "verdict", "7", m12, clear, "--resolution")
    fix_commit(lane, want)
    clean_merge(lane)
    no_criterion(lane)


def fix_commit(lane: Lane, want: str) -> None:
    """A fix commit after the reviewed head still needs a full fresh review, the resolution
    verdict (its Reviewed line WANT) aside."""
    h, j12 = lane.h, lane.h["j"][:12]

    def fix() -> None:
        with (lane.repo / "app.py").open("a") as f:
            f.write("fix\n")
        lane.git("commit", "-qam", "fix: after merge")

    f = lane.on(h["h2"], fix)
    f2 = lane.on(f, lambda: lane.qc(f))
    lane.on(f, lane.record)
    lane.setpr(f2, lane.body(f2, f, want + "\n"))
    r = lane.lane(1, "merge-ask", "7", *ST)
    assert (
        f"Review verdict: commit {f[:12]} 'fix: after merge' after the reviewed head {j12} "
        "changes app.py" in r.err
    ), f"fix commit after the reviewed head: {r.err}"


def clean_merge(lane: Lane) -> None:
    """--resolution on a merge with nothing beyond git's automatic merge is refused."""
    h, clear = lane.h, str(lane.s.root / "clear")

    def main_c() -> None:
        (lane.repo / "c.txt").write_text("c\n")
        lane.git("add", "c.txt")
        lane.git("commit", "-qm", "main: c")

    c_main = lane.on(h["b"], main_c)
    lane.git("update-ref", "refs/remotes/origin/main", c_main)
    cm = lane.on(h["h"], lambda: lane.git("merge", "-q", "--no-edit", c_main))
    lane.setpr(cm, lane.body(cm, h["j"]))
    r = lane.lane(1, "verdict", "7", cm[:12], clear, "--resolution")
    assert f"merge {cm[:12]} changes nothing beyond git's automatic merge" in r.err, (
        f"clean merge resolution: {r.err}"
    )


def no_criterion(lane: Lane) -> None:
    """A lane that builds no criterion: its review verdict on N, then a resolved merge NM, the PR
    head: the same rule. Nothing but the verdicts written, all along."""
    h, clear, url, s = lane.h, str(lane.s.root / "clear"), lane.h["url"], lane.s
    n = lane.on(
        h["b"], lambda: lane.set_app("one"), lambda: lane.git("commit", "-qam", "fix: a rule")
    )
    lane.git("update-ref", "refs/remotes/origin/main", h["main"])
    nm = lane.on(n, lane.resolved_merge)
    assert lane.git("show", f"{nm}:app.py").split("\n")[:2] == ["one", "2"], (
        "fixture: NM's resolution"
    )
    lane.on(nm, lane.record)

    def nask(reviewed: str) -> None:
        lane.setpr(
            nm,
            f"Closes #6\n\n## Merge ask\n\nHead: {nm[:12]}\nChecks: check pass\nReview verdict: "
            f"{url}\n{reviewed}Built: none\nFailed: none\n",
        )

    nask("")
    lane.lane(0, "verdict", "7", n, clear)
    r = lane.lane(1, "merge-ask", "7")
    assert f"Judged: merge {nm[:12]} '{RESOLVED}' resolved a conflict" in r.err, (
        f"no-criterion lane without a resolution verdict: {r.err}"
    )
    nurl = lane.lane(0, "verdict", "7", nm[:12], clear, "--resolution").out
    nwant = (
        f"Reviewed: {n[:12]} to {nm[:12]}: no qc status commit; resolution of merge {nm[:12]} "
        f"(app.py) reviewed clear: {nurl}"
    )
    r = lane.lane(1, "merge-ask", "7")
    assert f"Reviewed: missing; add the check's proof line `{nwant}`" in r.err, (
        f"no-criterion lane, no Reviewed line: {r.err}"
    )
    nask(nwant + "\n")
    r = lane.lane(0, "merge-ask", "7")
    assert nwant in r.out.split("\n"), f"no-criterion lane with its resolution verdict: {r.out}"
    wrote = [x for x in s.gh.log() if x.startswith("api -X ")]
    assert all("/issues/7/comments" in x or "/issues/comments/" in x for x in wrote), (
        f"a write beside the verdicts: {wrote}"
    )


if __name__ == "__main__":
    main(resolution)
