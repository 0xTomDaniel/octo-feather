"""The scenario of tests/gate/kit/test_lane_review_resolution.py (its item), this file its command
(testkit.main): the review of a main merge's resolution (the rule: issue-lifecycle
#lanes-one-head), offline: the testkit's gh answers only real gh's recorded answers
(testkit/recordings/lane-review-resolution.json), the scratch PR's views and its verdict
comments posted and edited. `octo-feather-lane resolution` prints a conflicted merge's remerge
diff and its files; `verdict --resolution` posts a verdict naming the merge and only those
files; merge-ask passes on the earlier review verdict with it and refuses without it, naming the
merge; a fix commit after the reviewed head needs a full review.

The lane rebuilds, byte for byte, the commits the recording pushed (lane_ci_start's identity and
dates, on its ROOT, the scratch base branch holding the recording's workflow): main B; the lane's
code J (reviewed, clear) and qc's status commit H. Main then changes the lane's line of app.py (a
conflict) and notes.txt (no lane file); the lane merges it as M, resolving the conflict by hand;
qc reruns on M (its status commit H2, the PR head). M's full gate pass is recorded. origin/main
of the old test is origin/BASE here, the PR's base branch.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, cast

from lane_ci_start import BASE, GIT_ENV, root
from testkit import Ran, Scratch, kit, main

if TYPE_CHECKING:
    from collections.abc import Callable

# gh 2.102.0 on 0xTomDaniel/octo-feather, 2026-11-17 (each recording's source): one real run of
# this scenario on scratch PR 946 (PR; lane_ci_start's, after its moments), head branch
# gh930-recording (its parent key 930), each head pushed and body edited as setpr names; then
# closed, both branches deleted.
TAPE = Path(__file__).parent / "testkit" / "recordings" / "lane-review-resolution.json"
PR = 946
STATUS = "docs/specs/demo.status.json"
ST = ("--status", STATUS)
CLEAR = "Findings: none blocking.\nChecks: none\nVerdict: clear\n"
BLOCKING = "Findings: the resolution drops main.\nChecks: none\nVerdict: blocking\n"
RESOLVED = "Merge main, conflict resolved"


class Lane:
    """The lane repo in S, its heads, and S's gh on the tape."""

    def __init__(self, s: Scratch) -> None:
        self.s, self.repo = s, s.root / "repo"
        s.env.pop("HERDR_SESSION", None)
        s.env |= {"XDG_STATE_HOME": str(s.root / "xdg"), "OCTO_FEATHER_QC_DIR": str(s.root / "qc")}
        (s.root / "clear").write_text(CLEAR)
        (s.root / "blocking").write_text(BLOCKING)
        self.h: dict[str, str] = {}
        self.tape = cast("list[dict[str, object]]", json.loads(TAPE.read_text()))
        s.gh.store("tape.json", self.tape)

    def git(self, *args: str, want: int = 0) -> str:
        return self.s.run(["git", "-C", str(self.repo), *args], want=want, env=GIT_ENV).out

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

    def main_at(self, sha: str) -> None:
        """origin's base branch at SHA (the old test's origin/main)."""
        self.git("update-ref", f"refs/remotes/origin/{BASE}", sha)

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
            f"Closes #930\n\n## Merge ask\n\nHead: {h}\nChecks: check pass\nJudged: {j} to {h}: "
            f"qc status commits {h} change only {STATUS}\n| criterion | qc verdict | judged | "
            f"evidence |\n|---|---|---|---|\n| demo#acceptance-a | pass | judged {j} | r |\n"
            f"Review verdict: {self.h['url']}\n{reviewed}Built: demo#acceptance-a\nFailed: none\n"
        )

    def setpr(self, head: str, body: str) -> None:
        """The PR from here on: its head HEAD (pushed) and BODY, as the recording set it. The
        tape's next PR view holds that head, and that body where it was asked."""
        views = [r for r in self.tape if str(r["request"]).startswith(f"pr view {PR} ")]
        seen = sum(x.startswith(f"pr view {PR} ") for x in self.s.gh.log())
        assert len(views) > seen, f"no recorded PR view at head {head[:12]}"
        d = json.loads(str(views[seen]["out"]))
        assert d["headRefOid"] == head, f"the tape's PR head {d['headRefOid']}, not {head}"
        assert d.get("body", body) == body, f"the tape's PR body: {d['body']!r}"


def build(lane: Lane) -> None:
    s, r, h = lane.s, lane.repo, lane.h
    root(s, r)
    (r / "docs" / "specs").mkdir(parents=True)
    (r / STATUS).write_text(
        '{"spec": "demo.spec.html", "accepted_commit": "0123abc", "criteria": {"acceptance-a": '
        '{"status": "planned", "pr": null}}}\n'
    )
    (r / "app.py").write_text("".join(f"{i}\n" for i in range(1, 21)))
    (r / "notes.txt").write_text("notes\n")
    h["b"] = lane.commit("base")
    lane.main_at(h["b"])
    lane.git("checkout", "-q", "-b", "lane")
    lane.set_app("one")
    h["j"] = lane.commit("feat: x")
    (r / STATUS).write_text(
        (r / STATUS).read_text().replace('"planned", "pr": null', f'"built", "pr": {PR}')
    )
    h["h"] = lane.commit(f"qc: built acceptance-a (judged {h['j'][:12]})")

    def main_two() -> None:
        lane.set_app("uno")
        with (r / "notes.txt").open("a") as f:
            f.write("main\n")
        lane.git("commit", "-qam", "main: two files")

    h["main"] = lane.on(h["b"], main_two)
    lane.main_at(h["main"])
    h["m"] = lane.on(h["h"], lane.resolved_merge)
    app = lane.git("show", f"{h['m']}:app.py").split("\n")[:2]
    assert app == ["one", "2"], f"fixture: the resolution kept {app}"
    h["h2"] = lane.on(h["m"], lambda: lane.qc(h["m"]))
    lane.on(h["m"], lane.record)


def resolution(s: Scratch) -> None:
    """issue-lifecycle#acceptance-review-resolution: without a resolution verdict merge-ask refuses
    naming the merge; `resolution` prints the remerge diff and only the files the resolution
    changed (notes.txt is main's own change), and refuses a non-merge; the resolution verdict names
    the merge and only its files (the body sent: its recording's request); merge-ask then asks for
    the Reviewed proof, then passes printing it; a blocking resolution verdict keeps nothing; a fix
    commit after the reviewed head still needs a full fresh review; --resolution on a merge with
    nothing beyond git's automatic merge is refused; a lane that builds no criterion: the same
    rule."""
    lane = Lane(s)
    build(lane)
    h, clear = lane.h, str(s.root / "clear")
    j12, m12 = h["j"][:12], h["m"][:12]
    lane.setpr(h["h2"], "")
    h["url"] = lane.lane(0, "verdict", str(PR), h["j"], clear).out  # the earlier review, of J
    lane.setpr(h["h2"], lane.body(h["h2"], h["m"]))
    r = lane.lane(1, "merge-ask", str(PR), *ST)
    want = (
        f"Review verdict: merge {m12} '{RESOLVED}' resolved a conflict with origin/{BASE}: the "
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
    rurl = lane.lane(0, "verdict", str(PR), m12, clear, "--resolution").out
    sent = [x for x in s.gh.log() if x.startswith("api -X POST ")][-1]  # the verdict's post
    body = json.loads(sent.split(" --input ", 1)[1].rsplit(" --jq ", 1)[0])["body"]
    assert f"\nMerge: {h['m']}\nFiles: app.py\n" in body, f"resolution verdict body: {body}"
    assert "\nVerdict: clear\n" in body, f"resolution verdict body: {body}"
    r = lane.lane(1, "merge-ask", str(PR), *ST)
    want = (
        f"Reviewed: {j12} to {m12}: qc status commits {h['h'][:12]} change only {STATUS}; "
        f"resolution of merge {m12} (app.py) reviewed clear: {rurl}"
    )
    assert f"Reviewed: missing; add the check's proof line `{want}`" in r.err, (
        f"no Reviewed line: {r.err}"
    )
    lane.setpr(h["h2"], lane.body(h["h2"], h["m"], want + "\n"))
    r = lane.lane(0, "merge-ask", str(PR), *ST)
    assert want in r.out.split("\n"), f"pass did not print the Reviewed proof: {r.out}"
    lane.lane(0, "verdict", str(PR), m12, str(s.root / "blocking"), "--resolution")
    r = lane.lane(1, "merge-ask", str(PR), *ST)
    assert f"Review verdict: merge {m12} '{RESOLVED}' resolved a conflict" in r.err, (
        f"blocking resolution verdict kept the review: {r.err}"
    )
    lane.lane(0, "verdict", str(PR), m12, clear, "--resolution")
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
    r = lane.lane(1, "merge-ask", str(PR), *ST)
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
    lane.main_at(c_main)
    cm = lane.on(h["h"], lambda: lane.git("merge", "-q", "--no-edit", c_main))
    lane.setpr(cm, lane.body(cm, h["j"]))
    r = lane.lane(1, "verdict", str(PR), cm[:12], clear, "--resolution")
    assert f"merge {cm[:12]} changes nothing beyond git's automatic merge" in r.err, (
        f"clean merge resolution: {r.err}"
    )


def no_criterion(lane: Lane) -> None:
    """A lane that builds no criterion: its review verdict on N, then a resolved merge NM, the PR
    head: the same rule."""
    h, clear, url = lane.h, str(lane.s.root / "clear"), lane.h["url"]
    n = lane.on(
        h["b"], lambda: lane.set_app("one"), lambda: lane.git("commit", "-qam", "fix: a rule")
    )
    lane.main_at(h["main"])
    nm = lane.on(n, lane.resolved_merge)
    assert lane.git("show", f"{nm}:app.py").split("\n")[:2] == ["one", "2"], (
        "fixture: NM's resolution"
    )
    lane.on(nm, lane.record)

    def nask(reviewed: str) -> None:
        lane.setpr(
            nm,
            f"Closes #930\n\n## Merge ask\n\nHead: {nm[:12]}\nChecks: check pass\nReview verdict: "
            f"{url}\n{reviewed}Built: none\nFailed: none\n",
        )

    nask("")
    lane.lane(0, "verdict", str(PR), n, clear)
    r = lane.lane(1, "merge-ask", str(PR))
    assert f"Judged: merge {nm[:12]} '{RESOLVED}' resolved a conflict" in r.err, (
        f"no-criterion lane without a resolution verdict: {r.err}"
    )
    nurl = lane.lane(0, "verdict", str(PR), nm[:12], clear, "--resolution").out
    nwant = (
        f"Reviewed: {n[:12]} to {nm[:12]}: no qc status commit; resolution of merge {nm[:12]} "
        f"(app.py) reviewed clear: {nurl}"
    )
    r = lane.lane(1, "merge-ask", str(PR))
    assert f"Reviewed: missing; add the check's proof line `{nwant}`" in r.err, (
        f"no-criterion lane, no Reviewed line: {r.err}"
    )
    nask(nwant + "\n")
    r = lane.lane(0, "merge-ask", str(PR))
    assert nwant in r.out.split("\n"), f"no-criterion lane with its resolution verdict: {r.out}"


if __name__ == "__main__":
    main(resolution)
