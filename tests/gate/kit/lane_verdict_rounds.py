"""The scenarios of tests/gate/kit/test_lane_verdict_rounds.py (its items), this file their command
(testkit.main): the review verdict covers the whole lane (issue-lifecycle #lanes-one-head,
#acceptance-verdict-covers-lane; #1220): `octo-feather-lane verdict` keeps every posted round in
the PR's one verdict comment and checks each report's Range against git; `merge-ask` refuses
rounds that do not chain from main to the reviewed head.

The recorded case, PR #1216 (lane gh1121), offline: its commits are the kit repo's own (main
6eaf8c7b; round 1 reviewed 6eaf8c7b..6f00d950, round 2 6eaf8c7b..ffba6ee7, round 3 the delta
ffba6ee7..2dc6f718; all on main since #1216 merged as 30086cb1), read through a scratch repo
whose object store borrows the kit's (git alternates), origin/main at 6eaf8c7b; the PR in the
fake gh (testkit/gh.py) at head 2dc6f718, its body the lane's merge ask (it builds no
criterion), its checks passing, the full gate pass recorded at 2dc6f718 by octo-feather-gate.
The three code-reviewer reports are the lane's result files verbatim
(tests/fixtures/verdict-rounds/round{1,2,3}.md); each scenario adds the `Range:` line its
reviewer would write. round3-alone.md is the verdict comment holding round 3 alone, as verdict
writes rounds; verdict itself refuses to post it there. The legacy comment is the one the old
verdict posted for round 3 (comment 7062437841 at 2026-11-21T12:15:27Z: its header and report).
The parent #1121 stands in the fake gh's store with no correction-lane marker in its title, a
non-correction lane's (#1222); tests/gate/kit/lane_correction_replay.py replays it as recorded.

A declaration-only check (issue-lifecycle #acceptance-declaration-check-shown; #1221): round 2's
trailer line as it should have read, `class: declaration` (DECLARED), swapped into round 2's
recorded report; nothing else in it changes but, where a scenario says so, its verdict.
"""

from __future__ import annotations

import subprocess
from typing import Any

from testkit import ROOT, Ran, Scratch, fixture, kit, main

L = kit("octo-feather-lane")
G = kit("octo-feather-gate")
PR = 1216
MAIN = "6eaf8c7b98f3c06ef088842dff6ca09043464682"
R1 = "6f00d9509ea815c03c64401579b386ad239d8f4c"
R2 = "ffba6ee7e78f9972957996e92622e2608cdb2d55"
R3 = "2dc6f718805b11b8995c1acdb3739f1b07ab8dc0"
LATER = "d186f2e5"  # the lane's next commit after 2dc6f718 (revert of #1215), one parent
CHECK_OK = [
    {"__typename": "CheckRun", "name": "check", "status": "COMPLETED", "conclusion": "SUCCESS"}
]
URL = f"https://github.com/o/r/pull/{PR}#issuecomment-"
ROUND2_CHECKS = [  # round 2's report's two Check lines, as recorded
    (
        "Check: scripts/octo-feather-lane: rule-only seam record and timing (ADR 0002; #1214) | "
        "reads: ticket acceptance items, notes, Git author time | class: exact"
    ),
    (
        "Check: scripts/octo-feather-lane: test-commit trailer declarations recorded before "
        "commit (#1215 declaration stopgap) | reads: worker commits, paths, interpret-trailers, "
        "ticket notes, handoff log | class: exact"
    ),
]
EXACT, TRAILER = ROUND2_CHECKS
DECLARED = TRAILER.replace("| class: exact", "| class: declaration")
DECLARATION_HEAD = "Declaration checks (stopgaps; owner rules at merge): 1"


class Lane:
    """The scratch repo R at PR #1216's recorded head, and the PR in the fake gh."""

    def __init__(self, s: Scratch) -> None:
        self.s, self.r = s, s.root / "repo"
        s.env.pop("HERDR_SESSION", None)
        s.env["XDG_STATE_HOME"] = str(s.root / "xdg")
        s.env["OCTO_FEATHER_QC_DIR"] = str(s.root / "qc")
        s.prepare("lane-verdict-rounds", Lane.build)
        url = "https://github.com/o/r/issues/1121"
        s.gh.store("issue/1121.json", {"number": 1121, "title": "a lane", "body": "", "url": url})

    @staticmethod
    def build(s: Scratch) -> None:
        r = s.root / "repo"
        r.mkdir()
        objects = (
            s.run(
                ["git", "-C", str(ROOT), "rev-parse", "--path-format=absolute", "--git-common-dir"]
            ).out
            + "/objects"
        )
        s.run(["git", "init", "-q", "-b", "lane", str(r)])
        (r / ".git" / "objects" / "info" / "alternates").write_text(objects + "\n")
        for k, v in (
            ("user.email", "t@example.com"),
            ("user.name", "t"),
            ("commit.gpgsign", "false"),
        ):
            s.run(["git", "-C", str(r), "config", k, v])
        has = subprocess.run(  # git from PATH
            ["git", "-C", str(r), "cat-file", "-e", f"{LATER}^{{commit}}"],  # noqa: S607
            check=False,
        )
        assert has.returncode == 0, f"the kit repo lacks PR #{PR}'s commits: git fetch origin main"
        s.run(["git", "-C", str(r), "update-ref", "refs/remotes/origin/main", MAIN])
        s.run(["git", "-C", str(r), "reset", "-q", "--hard", R3])
        s.run([G, "record", "--reason", "lane final head", "--seconds", "1"], cwd=r)

    def pr(
        self,
        head: str = R3,
        comments: list[dict[str, str]] | None = None,
        url: str = "",
        more: str = "",
    ) -> None:
        """PR #1216 at HEAD with COMMENTS, its merge ask naming the verdict comment URL, MORE
        after it."""
        body = (
            f"Closes #1121\n\n## Merge ask\n\nHead: {head[:12]}\n"
            f"Checks: check pass on {head[:12]}\nReview verdict: {url}\nBuilt: none\nFailed: none\n"
            + more
        )
        self.s.gh.put(
            PR,
            {
                "number": PR,
                "baseRefName": "main",
                "headRefName": "gh1121",
                "headRefOid": head,
                "body": body,
                "statusCheckRollup": CHECK_OK,
                "comments": comments or [],
            },
        )

    def keep_body(self, url: str, more: str = "") -> None:
        """The PR as the fake gh holds it, its merge ask naming URL, MORE after it."""
        d: dict[str, Any] = self.s.gh.pr(PR)
        comments = d["comments"]
        self.pr(d["headRefOid"], comments, url, more)

    def report(self, name: str, rng: str = "") -> str:
        """The recorded report NAME, with the line `Range: RNG` when given."""
        p = self.s.root / f"{name}-{rng.replace('.', '_')}.md"
        p.write_text(fixture(f"verdict-rounds/{name}.md") + (f"Range: {rng}\n" if rng else ""))
        return str(p)

    def lane(self, *args: str, want: int = 0) -> Ran:
        return self.s.run([L, *args], want=want, cwd=self.r)

    def verdict(self, head: str, name: str, rng: str = "", want: int = 0) -> Ran:
        return self.lane("verdict", str(PR), head[:12], self.report(name, rng), want=want)

    def ask(self, want: int = 0) -> Ran:
        return self.lane("merge-ask", str(PR), "--base", "origin/main", want=want)

    def body(self) -> str:
        return str(self.s.gh.pr(PR)["comments"][0]["body"])  # type: ignore[index]


def covers_lane(s: Scratch) -> None:
    """issue-lifecycle#acceptance-verdict-covers-lane, the recorded PR #1216: merge-ask refuses a
    verdict comment holding round 3 alone (the delta ffba6ee7..2dc6f718), naming the range it
    covers and 6eaf8c7b..ffba6ee7, which no posted round covers; verdict refuses round 3 before
    round 2 is posted, naming both ways out; rounds 2 and 3 posted, chained, merge-ask passes, the
    header and the rounds listing round 2's two Check lines."""
    ln = Lane(s)
    alone = {"url": URL + "7062437841", "body": fixture("verdict-rounds/round3-alone.md")}
    ln.pr(comments=[alone], url=alone["url"])
    r = ln.ask(want=1)
    want = (
        "Review verdict: the review rounds cover ffba6ee7e78f..2dc6f718805b only: no posted round "
        "covers 6eaf8c7b98f3..ffba6ee7e78f, the lane before them; post the round that reviewed up "
        "to ffba6ee7e78f with `octo-feather-lane verdict`, or review the lane from 6eaf8c7b98f3 "
        "and post that round"
    )
    assert want in r.err, f"round 3 alone: not refused naming the uncovered range: {r.err}"
    ln.pr()
    r = ln.verdict(R3, "round3", "ffba6ee7..2dc6f718", want=1)
    want = (
        "Range ffba6ee7..2dc6f718 starts neither on origin/main (a full round: the lane from main) "
        "nor at the head of a posted round (none is posted) (a delta round): post the round that "
        "reviewed up to ffba6ee7e78f first, or review the lane from 6eaf8c7b98f3 (origin/main) and "
        "post that report"
    )
    assert want in r.err, f"round 3 first: {r.err}"
    assert s.gh.writes() == 0, "a refused verdict wrote"
    url = ln.verdict(R2, "round2", "6eaf8c7b..ffba6ee7").out
    ln.verdict(R3, "round3", "ffba6ee7..2dc6f718")
    b = ln.body()
    head = f"Head: {R3}\nPR head: {R3}\nVerdict: clear\n" + "".join(f"{c}\n" for c in ROUND2_CHECKS)
    assert head + "\n### Rounds\n" in b, f"the comment's header: {b}"
    rounds = (
        f"- Round 1: {MAIN}..{R2}, full, verdict blocking\n"
        + "".join(f"  - {c}\n" for c in ROUND2_CHECKS)
        + f"- Round 2: {R2}..{R3}, delta, verdict clear\n  - Checks: none\n"
    )
    assert f"### Rounds\n\n{rounds}\n### Findings\n" in b, f"the comment's rounds: {b}"
    ln.keep_body(url)
    out = ln.ask().out.split("\n")
    classes = out.index("Review check classes (from the verdict comment, docs/adr/0008):")
    assert out[classes + 1 : classes + 3] == [f"- {c}" for c in ROUND2_CHECKS], out
    i = out.index("Review rounds (from the verdict comment, issue-lifecycle #lanes-one-head):")
    assert out[i + 1 : i + 6] == [
        "- Round 1: 6eaf8c7b98f3..ffba6ee7e78f full, verdict blocking",
        *(f"  - {c}" for c in ROUND2_CHECKS),
        "- Round 2: ffba6ee7e78f..2dc6f718805b delta, verdict clear",
        "  - Checks: none",
    ], out


def range_refusals(s: Scratch) -> None:
    """verdict refuses, writing nothing: a report with no Range (round 3's, as recorded); a Range
    whose `to` is not HEAD; one whose `from` is not an ancestor of `to`; a delta whose `from` is
    not the head the last posted round ended on (round 1 posted, then round 3), naming that head.
    A rerun of the last round's review replaces it."""
    ln = Lane(s)
    ln.pr()
    for args, want in (
        ((R3, "round3"), "report names no Range: add `Range: <from>..<to>`"),
        (
            (R2, "round3", "ffba6ee7..2dc6f718"),
            "Range ffba6ee7..2dc6f718 ends at 2dc6f718805b, not HEAD ffba6ee7e78f",
        ),
        (
            (R2, "round2", "2dc6f718..ffba6ee7"),
            "Range 2dc6f718..ffba6ee7: 2dc6f718805b is not an ancestor of ffba6ee7e78f",
        ),
        (
            (R3, "round3", "ffba6ee7..2dc6f718 6eaf8c7b..2dc6f718"),
            "`Range: ffba6ee7..2dc6f718 6eaf8c7b..2dc6f718` is not `Range: <from>..<to>`",
        ),
    ):
        r = ln.verdict(*args, want=1)
        assert want in r.err, f"{args}: want {want!r}: {r.err}"
    assert s.gh.writes() == 0, "a refused verdict wrote"
    ln.verdict(R1, "round1", "6eaf8c7b..6f00d950")
    ln.verdict(R1, "round1", "6eaf8c7b..6f00d950")
    assert ln.body().count("- Round ") == 1, f"a rerun of round 1 added a round: {ln.body()}"
    r = ln.verdict(R3, "round3", "ffba6ee7..2dc6f718", want=1)
    want = (
        "Range ffba6ee7..2dc6f718 starts neither on origin/main (a full round: the lane from main) "
        "nor at 6f00d9509ea8, the head the last posted round ended on (a delta round): post the "
        "round that reviewed up to ffba6ee7e78f first, or review the lane from 6eaf8c7b98f3 "
        "(origin/main) and post that report"
    )
    assert want in r.err, f"a delta off the last posted head: {r.err}"
    assert s.gh.writes() == 1, "a refused verdict wrote"


def legacy(s: Scratch) -> None:
    """A verdict comment posted before rounds (the old verdict's, round 3's report) still passes
    merge-ask, counted as one whole-lane round ending at its Head; the next verdict post chains a
    delta from that Head."""
    ln = Lane(s)
    old = (
        f"<!-- octo-feather-review-verdict -->\n## Code review verdict\n\nHead: {R3}\nPR head: "
        f"{R3}\nVerdict: clear\nChecks: none\n\n### Findings\n\n"
        + fixture("verdict-rounds/round3.md").strip()
        + "\n"
    )
    c = {"url": URL + "7062437841", "body": old}
    ln.pr(comments=[c], url=c["url"])
    out = ln.ask().out.split("\n")
    i = out.index("Review rounds (from the verdict comment, issue-lifecycle #lanes-one-head):")
    assert out[i + 1 : i + 3] == [
        "- Round 1: the lane to 2dc6f718805b, posted before rounds (counted whole), verdict clear",
        "  - Checks: none",
    ], out
    later = s.run(["git", "-C", str(ln.r), "rev-parse", LATER]).out
    ln.pr(later, [c], c["url"])
    ln.verdict(later, "round3", f"2dc6f718..{LATER}")
    b = ln.body()
    rounds = (
        f"- Round 1: lane..{R3}, legacy (posted before rounds), verdict clear\n  - Checks: none\n"
        f"- Round 2: {R3}..{later}, delta, verdict clear\n  - Checks: none\n"
    )
    assert f"### Rounds\n\n{rounds}\n### Findings\n" in b, f"the delta after a legacy comment: {b}"


def reclassed(ln: Lane, cls: str, rng: str, verdict: str = "blocking") -> str:
    """Round 2's recorded report, its trailer line classed CLS and its verdict VERDICT, with
    `Range: RNG`."""
    text = fixture("verdict-rounds/round2.md")
    assert TRAILER in text, "round2.md is not as recorded"
    assert "\nVerdict: blocking\n" in text, "round2.md is not as recorded"
    text = text.replace(TRAILER, TRAILER.replace("| class: exact", f"| class: {cls}"))
    p = ln.s.root / f"round2-{cls}-{verdict}.md"
    p.write_text(
        text.replace("\nVerdict: blocking\n", f"\nVerdict: {verdict}\n") + f"Range: {rng}\n"
    )
    return str(p)


def declaration_shown(s: Scratch) -> None:
    """issue-lifecycle#acceptance-declaration-check-shown, merge-ask: the recorded PR #1216, round 2
    posted with its trailer line classed declaration, round 3 (clear) chained after it; merge-ask
    passes, the exact line alone under `Review check classes`, the declaration line under its own
    heading, and the rounds keep it under round 1."""
    ln = Lane(s)
    ln.pr()
    url = ln.lane(
        "verdict", str(PR), R2[:12], reclassed(ln, "declaration", "6eaf8c7b..ffba6ee7")
    ).out
    ln.verdict(R3, "round3", "ffba6ee7..2dc6f718")
    assert f"Verdict: clear\n{EXACT}\n{DECLARED}\n\n### Rounds\n" in ln.body(), ln.body()
    ln.keep_body(url)
    out = ln.ask().out.split("\n")
    classes = out.index("Review check classes (from the verdict comment, docs/adr/0008):")
    assert out[classes + 1 : classes + 3] == [f"- {EXACT}", ""], out
    i = out.index(DECLARATION_HEAD)
    assert out[i + 1 : i + 3] == [f"- {DECLARED}", ""], out
    i = out.index("Review rounds (from the verdict comment, issue-lifecycle #lanes-one-head):")
    assert out[i + 2 : i + 4] == [f"  - {EXACT}", f"  - {DECLARED}"], out


def declaration_verdict(s: Scratch) -> None:
    """issue-lifecycle#acceptance-declaration-check-shown, verdict: round 2's report, clear, its
    trailer line classed proxy or another class (`stopgap`), is refused, writing nothing; classed
    declaration, it is posted, a full round over the lane; merge-ask passes and shows it apart."""
    ln = Lane(s)
    ln.pr()
    for cls, want in (
        ("proxy", "report says `Verdict: clear` with a proxy check"),
        (
            "stopgap",
            "has class 'stopgap'; write `class: exact`, `class: proxy` or `class: declaration`",
        ),
    ):
        r = ln.lane(
            "verdict", str(PR), R3[:12], reclassed(ln, cls, "6eaf8c7b..2dc6f718", "clear"), want=1
        )
        assert want in r.err, f"{cls}: want {want!r}: {r.err}"
    assert s.gh.writes() == 0, "a refused verdict wrote"
    report = reclassed(ln, "declaration", "6eaf8c7b..2dc6f718", "clear")
    url = ln.lane("verdict", str(PR), R3[:12], report).out
    assert (
        f"- Round 1: {MAIN}..{R3}, full, verdict clear\n  - {EXACT}\n  - {DECLARED}\n" in ln.body()
    )
    ln.keep_body(url)
    out = ln.ask().out.split("\n")
    assert out[out.index(DECLARATION_HEAD) + 1] == f"- {DECLARED}", out


if __name__ == "__main__":
    main(covers_lane, range_refusals, legacy, declaration_shown, declaration_verdict)
