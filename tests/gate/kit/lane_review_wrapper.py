"""The scenarios of tests/gate/kit/test_lane_review_wrapper.py (its items), this file their command
(testkit.main): `octo-feather-lane merge-ask` carries the review verdict across integrate's
`--no-ff` merge W of a worker branch whose tip is the worker's merge of main M, under the
conditions of issue-lifecycle #lanes-one-head (numbered as ticket #1332 numbers them); a failed
condition refuses, naming it and the commits. Offline: the
testkit's gh answers only real gh's recorded answers (testkit/recordings/review-wrapper-1332.json,
one tape per scenario), never its store.

The lane repo rebuilds, byte for byte, the commits the recording pushed (GIT_ENV): main B (app.py,
notes.txt); the lane's code J (app.py line 1, reviewed clear). Main adds c.txt (MA); the worker,
cut from J, merges it clean (M1); integrate lands it on the lane (W1). Main then sets app.py's line
1 and appends to notes.txt (MB); the worker, cut from W1, merges it resolving app.py's conflict by
hand (M2); integrate lands it (W2). The refusals: WB, a W of M1 adding a byte to notes.txt; WD, a
W of M1 on K (a lane commit after J M1 lacks) with M1's tree; W3, a W of M3, the worker's merge
of S, a side branch main merged as MD's second parent (on main, not its first-parent history).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import cast

from testkit import Ran, Scratch, kit, main

# gh 2.102.0 on 0xTomDaniel/octo-feather-realcase (the standing private test repo), 2026-11-28
# (each recording's source): one real run of these scenarios, in order, on PR PR, head branch
# gh1332-wrapper (its parent key 1332), base BASE (B); each head pushed and body edited as setpr
# names, the verdicts posted by the scenarios' own `octo-feather-lane verdict`; then closed, both
# branches deleted. Every answer as recorded.
TAPES = Path(__file__).parent / "testkit" / "recordings" / "review-wrapper-1332.json"
PR = 48
BASE = "gh1332-wrapper-base"
DATE = "2026-11-28T00:00:00Z"
GIT_ENV = {
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@example.com",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@example.com",
    "GIT_AUTHOR_DATE": DATE,
    "GIT_COMMITTER_DATE": DATE,
}
CLEAR = "Findings: none blocking.\nChecks: none\nVerdict: clear\n"
LANDS = "Merge branch 'worker' into lane"
RESOLVED = "Merge main, conflict resolved"


class Lane:
    """The lane repo in S, its commits H, and S's gh on SCENARIO's tape."""

    def __init__(self, s: Scratch, scenario: str) -> None:
        self.s, self.repo = s, s.root / "repo"
        s.env.pop("HERDR_SESSION", None)
        s.env |= {"XDG_STATE_HOME": str(s.root / "xdg"), "OCTO_FEATHER_QC_DIR": str(s.root / "qc")}
        tapes = cast("dict[str, list[dict[str, object]]]", json.loads(TAPES.read_text()))
        self.tape = tapes.get(scenario, [])
        s.gh.store("tape.json", self.tape)
        self.h: dict[str, str] = {}
        build(self)

    def git(self, *args: str, want: int = 0) -> str:
        return self.s.run(["git", "-C", str(self.repo), *args], want=want, env=GIT_ENV).out

    def on(self, parent: str, msg: str, files: dict[str, str]) -> str:
        """A commit on PARENT writing FILES (appending to one whose text starts with '+')."""
        self.git("checkout", "-q", "--detach", parent)
        for name, text in files.items():
            p = self.repo / name
            p.write_text(p.read_text() + text[1:] if text.startswith("+") else text)
        self.git("add", "-A")
        self.git("commit", "-q", "-m", msg)
        return self.git("rev-parse", "HEAD")

    def merge(self, ours: str, theirs: str, msg: str, *, ff: bool = True) -> str:
        """OURS merging THEIRS (--no-ff unless FF), git's automatic merge."""
        self.git("checkout", "-q", "--detach", ours)
        self.git("merge", "-q", *([] if ff else ["--no-ff"]), "-m", msg, theirs)
        return self.git("rev-parse", "HEAD")

    def main_at(self, sha: str) -> None:
        self.git("update-ref", f"refs/remotes/origin/{BASE}", sha)

    def record(self, sha: str) -> None:
        """A full gate pass recorded at SHA."""
        self.git("checkout", "-q", "--detach", sha)
        self.s.run(
            [kit("octo-feather-gate"), "record", "--reason", "lane final head", "--seconds", "1"],
            cwd=self.repo,
        )

    def lane(self, want: int, *args: str) -> Ran:
        return self.s.run([kit("octo-feather-lane"), *args], want=want, cwd=self.repo)

    def verdict(self) -> str:
        """The clear review verdict on J, from B (its Range); its comment URL."""
        report = self.s.root / "clear-j"
        report.write_text(f"{CLEAR}Range: {self.h['b']}..{self.h['j']}\n")
        return self.lane(0, "verdict", str(PR), self.h["j"], str(report)).out

    def ask(self, head: str, url: str, lines: str, want: int) -> Ran:
        """merge-ask on the PR at HEAD, its section naming the review verdict URL and LINES."""
        h = head[:12]
        body = (
            f"Closes #1332\n\n## Merge ask\n\nHead: {h}\nChecks: none reported on {h}\n{lines}"
            f"Review verdict: {url}\nBuilt: none\nFailed: none\n"
        )
        self.setpr(head, body)
        return self.lane(want, "merge-ask", str(PR))

    def setpr(self, head: str, body: str) -> None:
        """The PR from here on: its head HEAD (pushed) and BODY, as the recording set them. The
        tape's next PR view holds both."""
        views = [r for r in self.tape if str(r["request"]).startswith(f"pr view {PR} --json body")]
        seen = sum(x.startswith(f"pr view {PR} --json body") for x in self.s.gh.log())
        assert len(views) > seen, f"no recorded PR view at head {head[:12]}"
        d = json.loads(str(views[seen]["out"]))
        assert d["headRefOid"] == head, f"the tape's PR head {d['headRefOid']}, not {head}"
        assert d["body"] == body, f"the tape's PR body: {d['body']!r}"


def build(lane: Lane) -> None:
    r, h = lane.repo, lane.h
    lane.s.git(r.parent, "init", "-q", "-b", BASE, r.name)
    for k, v in (("user.email", "t@example.com"), ("user.name", "t"), ("commit.gpgsign", "false")):
        lane.s.git(r, "config", k, v)
    (r / "app.py").write_text("".join(f"{i}\n" for i in range(1, 21)))
    (r / "notes.txt").write_text("notes\n")
    lane.git("add", "-A")
    lane.git("commit", "-q", "-m", "base")
    h["b"] = lane.git("rev-parse", "HEAD")
    app = (r / "app.py").read_text().split("\n", 1)[1]
    h["j"] = lane.on(h["b"], "feat: x", {"app.py": "one\n" + app})
    h["ma"] = lane.on(h["b"], "main: c", {"c.txt": "c\n"})
    h["m1"] = lane.merge(h["j"], h["ma"], "Merge main into worker")
    h["w1"] = lane.merge(h["j"], h["m1"], LANDS, ff=False)
    h["mb"] = lane.on(h["ma"], "main: two files", {"app.py": "uno\n" + app, "notes.txt": "+main\n"})
    lane.git("checkout", "-q", "--detach", h["w1"])
    lane.git("merge", "-q", "-m", RESOLVED, h["mb"], want=1)
    (r / "app.py").write_text("one\n" + app)
    lane.git("commit", "-qam", RESOLVED)
    h["m2"] = lane.git("rev-parse", "HEAD")
    h["w2"] = lane.merge(h["w1"], h["m2"], LANDS, ff=False)
    lane.git("checkout", "-q", "--detach", h["j"])
    lane.git("merge", "-q", "--no-ff", "--no-commit", h["m1"])
    (r / "notes.txt").write_text("notes\nbeside\n")
    lane.git("commit", "-qam", LANDS)
    h["wb"] = lane.git("rev-parse", "HEAD")
    h["k"] = lane.on(h["j"], "feat: k", {"k.txt": "k\n"})
    h["wd"] = lane.git(
        "commit-tree", f"{h['m1']}^{{tree}}", "-p", h["k"], "-p", h["m1"], "-m", LANDS
    )
    h["s"] = lane.on(h["ma"], "side: s", {"s.txt": "s\n"})
    h["mc"] = lane.on(h["mb"], "main: d", {"d.txt": "d\n"})
    h["md"] = lane.merge(h["mc"], h["s"], "Merge branch 'side'", ff=False)
    h["m3"] = lane.merge(h["j"], h["s"], "Merge branch 'side' into worker")
    h["w3"] = lane.merge(h["j"], h["m3"], LANDS, ff=False)
    lane.git("checkout", "-q", "--detach", h["b"])


def proof_line(err: str, field: str) -> str:
    """The proof line ERR asks the section's FIELD to carry."""
    m = re.search(rf"{field}: missing; add the check's proof line `({field}: [^`]*)`", err)
    assert m, f"no {field} proof asked for: {err}"
    return m.group(1)


def wrapper_clean(s: Scratch) -> None:
    """issue-lifecycle#acceptance-review-wrapper-clean: W1 over the worker's clean main merge M1
    passes on the review verdict on J, no new review, its Judged proof naming M1's lane-hunks proof
    and W1 of M1; the full pass recorded at M1 carries to W1 as M1 would."""
    lane = Lane(s, "wrapper_clean")
    h = lane.h
    j, m1, w1 = h["j"][:12], h["m1"][:12], h["w1"][:12]
    lane.main_at(h["ma"])
    lane.record(h["m1"])
    url = lane.verdict()
    judged = proof_line(lane.ask(h["w1"], url, "", 1).err, "Judged")
    assert re.fullmatch(
        rf"Judged: {j} to {w1}: no qc status commit; clean merge of main {m1}: lane hunks "
        rf"identical \(1 file, sha256 [0-9a-f]{{12}}\); wrapper {w1} of {m1} carries it "
        r"\(tree equal\)",
        judged,
    ), judged
    r = lane.ask(h["w1"], url, judged + "\n", 0)
    assert judged in r.out.split("\n"), f"the pass did not print its Judged proof: {r.out}"


def wrapper_resolved(s: Scratch) -> None:
    """issue-lifecycle#acceptance-review-wrapper-resolved: W2 over the worker's hand-resolved main
    merge M2 refuses without a resolution verdict, naming M2; with a clear `verdict --resolution`
    naming M2 it passes on the review verdict on J, its proof naming M2's resolution and W2."""
    lane = Lane(s, "wrapper_resolved")
    h = lane.h
    m2, w1, w2 = h["m2"][:12], h["w1"][:12], h["w2"][:12]
    lane.main_at(h["mb"])
    lane.record(h["w2"])
    url = lane.verdict()
    r = lane.ask(h["w2"], url, "", 1)
    want = f"Judged: merge {m2} {RESOLVED!r} resolved a conflict with origin/{BASE}: "
    assert want in r.err, f"no resolution verdict: not refused naming M2: {r.err}"
    report = s.root / "clear-m2"
    report.write_text(CLEAR)
    rurl = lane.lane(0, "verdict", str(PR), m2, str(report), "--resolution").out
    reviewed = proof_line(lane.ask(h["w2"], url, "", 1).err, "Reviewed")
    assert reviewed.endswith(
        f"; resolution of merge {m2} (app.py) reviewed clear: {rurl}; wrapper {w1} of "
        f"{h['m1'][:12]} carries it (tree equal); wrapper {w2} of {m2} carries it (tree equal)"
    ), reviewed
    r = lane.ask(h["w2"], url, reviewed + "\n", 0)
    assert reviewed in r.out.split("\n"), f"the pass did not print its Reviewed proof: {r.out}"


def wrapper_refused(s: Scratch) -> None:
    """issue-lifecycle#acceptance-review-wrapper-refused: a W adding a byte beside M1 (WB), one
    dropping the lane commit K (WD), and one over the worker's merge of side branch S (W3) each
    refuse, the line naming the failed condition and the commits."""
    lane = Lane(s, "wrapper_refused")
    h = lane.h
    lane.main_at(h["md"])
    m1, m3 = h["m1"][:12], h["m3"][:12]
    url = lane.verdict()
    tail = ": only a merge of main, or integrate's merge of a worker's merge of main adding nothing"
    for w, failed in (
        ("wb", f"condition 1 fails: it changes notes.txt beside {m1} (adds to it)"),
        (
            "wd",
            (
                f"condition 2 fails: its first parent {h['k'][:12]} is not an ancestor of {m1} "
                "(drops lane commits)"
            ),
        ),
        (
            "w3",
            (
                f"condition 3 fails: {m3}'s second parent {h['s'][:12]} is not on "
                f"origin/{BASE}'s first-parent history (a merge of another branch, not of main)"
            ),
        ),
    ):
        lane.record(h[w])
        r = lane.ask(h[w], url, "", 1)
        mm = m3 if w == "w3" else m1
        want = f"Judged: merge {h[w][:12]} {LANDS!r} wraps merge {mm}, but {failed}{tail}"
        assert want in r.err, f"{w}: not refused naming its condition: {r.err}"


if __name__ == "__main__":
    main(wrapper_clean, wrapper_resolved, wrapper_refused)
