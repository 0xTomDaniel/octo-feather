"""scripts/octo-feather-lane judge and its line in merge-ask (spec judgment
#acceptance-judge-advisory, #rule-advisory, #rule-one-model, #rule-calibration; issue #156),
no network, no model. Each item builds lane gh6's worktree and its PR #7 of o/r in the fake gh,
and runs the kit's own commands (octo-feather-lane, octo-feather-gate, check-evals); the judge's
classify runs for real in the qa sandbox (unprivileged user namespaces, Linux) against the stub
pi, which lists the kit's one judgment model (evals/judgment-model.json) beside three others and
fails the run when any other is asked.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import shutil
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import pytest
from testkit import FAKES, ROOT, Ran, Scratch, fixture, kit, main

Case = Callable[..., None]
PR = 7
OTHERS = "openrouter/respan/span-02 openrouter/nace-ai/drex-max stub/other"
MODEL = json.loads((ROOT / "evals" / "judgment-model.json").read_text())["model"]
MARK = "<!-- octo-feather-model-judgment: {} -->"
URL = "https://github.com/o/r/pull/7#issuecomment-1002"  # the first comment after the review's
BESIDE = (
    "Model judgments (advisory, spec judgment#rule-advisory: no gate reads them; this merge ask "
    "is ready or not without them):"
)
# A real suite's calibration may change with every rebench; what the rule fixes is its status: no
# accepted threshold (owner ruling 2026-10-23, #151). Exact numbers only in a copied kit's suite.
N = r"[0-9]\.[0-9]{3}"
CAL = (
    rf"no accepted threshold \(held-out accuracy {N}, Brier {N}; threshold held-out accuracy >= "
    rf"{N} and Brier <= {N}, proposed, not accepted\)"
)
PICK = {
    "call-evidence": "shows",
    "exact-or-proxy": "exact",
    "test-quality": "tautological",
    "ticket-slice": "slice",
}
pytestmark = pytest.mark.skipif(sys.platform == "darwin", reason="the qa sandbox needs Linux")
STATE = "Test:\ndef test_add():\n    assert add(1, 2) == add(1, 2)\n"


class Lane:
    """Lane gh6's worktree, origin/main B, the judged head J (its full gate pass recorded), qc's
    status commit H (the PR head) and that qc run's report at J; PR #7 in the fake gh."""

    def __init__(self, s: Scratch, kit_dir: Path = ROOT) -> None:
        self.s, self.kit = s, kit_dir
        r = self.repo = s.root / "repo"
        (r / "docs" / "specs").mkdir(parents=True)
        s.git(r, "init", "-q", "-b", "main")
        for k, v in (
            ("user.email", "t@example.com"),
            ("user.name", "t"),
            ("commit.gpgsign", "false"),
        ):
            s.git(r, "config", k, v)
        self.status("planned", "null")
        (r / "app.py").write_text("1\n2\n3\n4\n5\n")
        s.git(r, "update-ref", "refs/remotes/origin/main", self.commit("base"))
        s.git(r, "checkout", "-q", "-b", "lane")
        (r / "app.py").write_text("one\n2\n3\n4\n5\n")
        j = self.j = self.commit("feat: x")
        s.run(
            [kit("octo-feather-gate"), "record", "--reason", "lane final head", "--seconds", "1"],
            cwd=r,
        )
        self.status("built", "7")
        h = self.h = self.commit(f"qc: built acceptance-a (judged {j[:12]})")
        # The qc report at J, where octo-feather-qc writes it (octo-feather-qc --help, Report).
        q = Path(s.run([kit("octo-feather-state")]).out) / "qc"
        q.mkdir(parents=True)
        res = {
            "id": "acceptance-a",
            "verdict": "pass",
            "evidence": "complete",
            "decision": "agent fallback",
        }
        report = {"head": j, "spec": "demo", "results": [{**res, "record": "r", "head": j}]}
        (q / f"{j}-20261029T100000Z-abc123.json").write_text(json.dumps(report))
        commits = [
            {"oid": j, "messageHeadline": "feat: x", "messageBody": ""},
            {
                "oid": h,
                "messageHeadline": f"qc: built acceptance-a (judged {j[:12]})",
                "messageBody": "",
            },
        ]
        check = {
            "__typename": "CheckRun",
            "name": "check",
            "status": "COMPLETED",
            "conclusion": "SUCCESS",
        }
        s.gh.put(
            PR,
            {
                "number": PR,
                "baseRefName": "main",
                "headRefName": "gh6",
                "headRefOid": h,
                "body": "",
                "statusCheckRollup": [check],
                "comments": [],
                "commits": commits,
            },
        )
        s.env["STUB_ALSO"] = OTHERS
        self.state = self.file("state", STATE)

    def status(self, st: str, pr: str) -> None:
        crit = f'{{"acceptance-a": {{"status": "{st}", "pr": {pr}}}}}'
        (self.repo / "docs" / "specs" / "demo.status.json").write_text(
            f'{{"spec": "demo.spec.html", "accepted_commit": "0123abc", "criteria": {crit}}}\n'
        )

    def commit(self, msg: str) -> str:
        self.s.git(self.repo, "add", "-A")
        self.s.git(self.repo, "commit", "-q", "-m", msg)
        return self.s.git(self.repo, "rev-parse", "HEAD")

    def file(self, name: str, text: str) -> Path:
        p = self.s.root / name
        p.write_text(text)
        return p

    def lane(self, *args: str, want: int = 0, **env: str) -> Ran:
        return self.s.run(
            [str(self.kit / "scripts" / "octo-feather-lane"), *args],
            want=want,
            cwd=self.repo,
            env=env,
        )

    def verdict(self) -> str:
        """The code review's verdict comment, posted by `verdict`; the merge ask in the PR body."""
        url = self.lane(
            "verdict",
            str(PR),
            self.j[:7],
            str(self.file("report", "Checks: none\nVerdict: clear\n")),
        ).out
        body = fixture("lane-judge/merge-ask-body.md")
        self.edit(
            lambda d: d.update(
                body=body.format(h12=self.h[:12], j12=self.j[:12], j9=self.j[:9], url=url)
            )
        )
        return url

    def judge(self, q: str, state: Path, answer: str, want: int = 0) -> Ran:
        return self.lane(
            "judge",
            str(PR),
            q,
            "--state",
            str(state),
            want=want,
            STUB_ANSWER=answer,
            STUB_WANT=state.read_text(),
        )

    def merge_ask(self, want: int = 0) -> Ran:
        return self.lane("merge-ask", str(PR), "--status", "docs/specs/demo.status.json", want=want)

    def pr(self) -> dict[str, Any]:
        return cast("dict[str, Any]", self.s.gh.pr(PR))

    def edit(self, f: Callable[[dict[str, Any]], object]) -> None:
        d = self.pr()
        f(d)
        self.s.gh.put(PR, d)

    def comment(self, q: str) -> str:
        return next(
            c["body"] for c in self.pr()["comments"] if c["body"].startswith(MARK.format(q))
        )

    def judgments(self) -> int:
        return sum(c["body"].startswith(MARK.format("")[:-4]) for c in self.pr()["comments"])

    def ready(self) -> str:
        """merge-ask exits 0 with the judgments and without them, the same once their block goes;
        its output with them."""
        keep = self.pr()
        w = self.merge_ask().out
        self.edit(lambda d: d.update(comments=d["comments"][:1]))
        wo = self.merge_ask().out
        self.s.gh.put(PR, keep)
        ls = w.split("\n")
        r = next(i for i, ln in enumerate(ls) if ln.startswith("Model judgments (advisory"))
        e = next((i for i in range(r + 1, len(ls)) if not ls[i].startswith("- ")), len(ls))
        assert ls[r - 1] == "", w
        assert "\n".join(ls[: r - 1] + ls[e:]) == wo, (
            f"differs beyond the judgment block:\n{w}\n---\n{wo}"
        )
        return w


def judged_line(q: str, answer: str, cal: str, lane: Lane) -> str:
    """merge-ask's line for Q's judgment, a regex."""
    return (
        rf"- {q}: {answer}, confidence 0\.910 \(model judgment by {re.escape(MODEL)}, advisory: "
        rf"no gate "
        rf"reads it; calibration: {cal}; PR head {lane.h[:12]}, review head {lane.j[:12]}\): "
    )


def said(how: str, answer: str, cal: str) -> str:
    """The judge's line on stderr for test-quality, a regex."""
    return (
        rf"judge: {how} \(test-quality: {answer}, confidence 0\.910, model judgment by "
        rf"{re.escape(MODEL)}; calibration: {cal}\)"
    )


def spend_row(s: Scratch, spent: str, *row: str) -> None:
    s.run([str(ROOT / "tests" / "spend-out"), "row", *row], stdin=spent)


def refusals(s: Scratch) -> None:
    """Before the review's verdict comment, an unknown question, an unreadable or empty state, no
    usage, the kit's model unavailable: refused, nothing written."""
    lane = Lane(s)
    st = str(lane.state)
    err = lane.lane("judge", "7", "test-quality", "--state", st, want=1).err
    assert (
        "no code review verdict comment on PR #7: the judge answers beside the review; "
        "post it first "
        "with `octo-feather-lane verdict 7" in err
    ), err
    lane.verdict()
    n = s.gh.writes()
    err = lane.lane("judge", "7", "vibes", "--state", st, want=1).err
    assert (
        "no judgment question 'vibes': name one of call-evidence, criterion-evidence, "
        "exact-or-proxy, "
        "test-quality, ticket-slice (evals/judgment-<question>/)" in err
    ), err
    nope = str(s.root / "nope")
    err = lane.lane("judge", "7", "test-quality", "--state", nope, want=1).err
    assert f"cannot read state {nope}" in err, err
    empty = lane.file("empty", "")
    err = lane.lane("judge", "7", "test-quality", "--state", str(empty), want=1).err
    assert f"state {empty} is empty" in err, err
    err = lane.lane("judge", "7", "test-quality", want=1).err
    assert "usage: octo-feather-lane judge PR QUESTION --state FILE" in err, err
    err = lane.lane("judge", "7", "test-quality", "--state", st, want=1, STUB_KIT="stub/other").err
    unavailable = f"the kit's judgment model {MODEL} is not an available classifier (available: "
    assert unavailable in err, err
    assert f"available: {MODEL}" not in err, err
    assert s.gh.writes() == n, f"a refusal wrote: {s.gh.log()}"


def judge_posts(s: Scratch) -> None:
    """The kit's model alone answers the state file's text; one comment labelled a model judgment,
    its spend recorded under the lane; merge-ask shows it beside the review verdict, ready the
    same."""
    lane = Lane(s)
    lane.verdict()
    without = lane.merge_ask().out
    assert "model judgment" not in without.lower(), without
    n = s.gh.writes()
    # Lane gh5, its supervisor in Herdr workspace w5: the judge runs in its space
    # (spec spend#rule-lane).
    lanes = s.home / ".local" / "state" / "octo-feather" / "lanes"
    lanes.mkdir(parents=True)
    (lanes / "gh5.toml").write_text('supervisor = "w5:p2"\n')
    r = lane.lane(
        "judge",
        "7",
        "test-quality",
        "--state",
        str(lane.state),
        STUB_ANSWER="tautological",
        STUB_WANT=STATE,
        HERDR_WORKSPACE_ID="w5",
    )
    assert r.out == URL, r.out
    assert any(
        re.fullmatch(said("created", "tautological", CAL), ln) for ln in r.err.splitlines()
    ), r.err
    assert s.gh.writes() == n + 1, s.gh.log()
    # spec spend#acceptance-spend-judge: the stub reports 100 tokens in, 2 out, $0.0001.
    spent = lane.lane("spend").out
    assert f"Spend ledger: {s.home}/.local/state/octo-feather/spend.jsonl (1 calls)" in spent, spent
    day = dt.datetime.now(dt.UTC).strftime("%Y-%m-%d")
    for title, key in (("lane", "gh5"), ("purpose", "judge"), ("model", MODEL), ("day (UTC)", day)):
        spend_row(s, spent, title, key, "0.000100", "1", "0", "100", "2")
    b = lane.comment("test-quality")
    for want in (
        MARK.format("test-quality") + "\n",
        "\nJudgment: model judgment",
        "\nQuestion: test-quality\n",
        f"\nModel: {MODEL}\n",
        "\nAnswer: tautological\n",
        "\nConfidence: 0.910\n",
        f"\nPR head: {lane.h}\n",
        f"\nReview head: {lane.j}\n",
        "assert add(1, 2) == add(1, 2)",
    ):
        assert want in b, (want, b)
    assert re.search(f"^Calibration: {CAL}$", b, re.MULTILINE), b
    w = lane.merge_ask().out
    ls = w.split("\n")
    i = next(
        (
            i
            for i, ln in enumerate(ls)
            if re.fullmatch(
                judged_line("test-quality", "tautological", CAL, lane) + re.escape(URL), ln
            )
        ),
        None,
    )
    assert i is not None, f"merge-ask did not show the judgment: {w}"
    r0 = i - 1
    assert ls[r0] == BESIDE, ls[r0]
    assert ls[r0 - 1] == "", w
    assert ls[r0 - 2].endswith(": agent fallback"), w
    assert ls[r0 + 2] == "", w
    assert ls[r0 + 3].startswith("Review check classes"), w
    assert "\n".join(ls[: r0 - 1] + ls[r0 + 2 :]) == without, f"more changed:\n{w}\n---\n{without}"


def rerun_in_place(s: Scratch) -> None:
    """A rerun updates the one judgment comment in place (an earlier one on the PR, marker and an
    old answer); a state the model was not shown gives no answer and writes nothing; merge-ask
    shows the new answer."""
    lane = Lane(s)
    lane.verdict()
    old = {
        "author": {"login": "sup"},
        "body": MARK.format("test-quality") + "\nold answer",
        "url": URL,
    }
    lane.edit(lambda d: d["comments"].append(old))
    n = s.gh.writes()
    state2 = lane.file("state2", "Test:\ndef test_add():\n    assert add(1, 2) == 3\n")
    err = lane.lane(
        "judge",
        "7",
        "test-quality",
        "--state",
        str(lane.state),
        want=1,
        STUB_ANSWER="ok",
        STUB_WANT=state2.read_text(),
    ).err
    assert f"{MODEL} gave no answer (stub: state lacks " in err, err
    assert s.gh.writes() == n, f"no answer, yet a write: {s.gh.log()}"
    out = lane.judge("test-quality", state2, "ok").out
    assert out == URL, out
    assert lane.judgments() == 1, lane.pr()["comments"]
    patch = "api -X PATCH repos/{owner}/{repo}/issues/comments/1002 "
    assert any(ln.startswith(patch) for ln in s.gh.log()), s.gh.log()
    w = lane.merge_ask().out
    assert re.search(r"^- test-quality: ok, confidence 0\.910 \(model judgment", w, re.MULTILINE), w


def no_gate_reads_it(s: Scratch) -> None:
    """merge-ask passes or fails the same with and without a judgment, whatever it says; a
    malformed judgment comment changes nothing."""
    lane = Lane(s)
    lane.verdict()
    lane.judge("test-quality", lane.state, "tautological")

    def review(a: str, b: str) -> Callable[[dict[str, Any]], object]:
        return lambda d: d["comments"][0].update(body=d["comments"][0]["body"].replace(a, b))

    lane.edit(review("Verdict: clear", "Verdict: blocking"))
    with_err = lane.merge_ask(want=1).err
    keep = lane.pr()
    lane.edit(lambda d: d.update(comments=d["comments"][:1]))
    err = lane.merge_ask(want=1).err
    assert err == with_err, (
        f"a blocking review failed differently with the judgment:\n{with_err}\n---\n{err}"
    )
    s.gh.put(PR, keep)
    lane.edit(review("Verdict: blocking", "Verdict: clear"))
    lane.edit(lambda d: d["comments"][1].update(body=MARK.format("test-quality") + "\ngarbage"))
    w = lane.merge_ask().out
    assert re.search(r"^- test-quality: unreadable judgment comment", w, re.MULTILINE), w


def real_suite(s: Scratch, q: str) -> None:
    """Each of the kit's real suites but test-quality (test_judge_posts): no accepted threshold
    (owner ruling 2026-10-23, #151), said in the comment and beside the answer in merge-ask,
    ready the same."""
    lane = Lane(s)
    lane.verdict()
    st = lane.file(f"state-{q}", f"state for {q}\n")
    lane.judge(q, st, PICK[q])
    b = lane.comment(q)
    for want in ("\nJudgment: model judgment", f"\nModel: {MODEL}\n", f"\nAnswer: {PICK[q]}\n"):
        assert want in b, (want, b)
    assert re.search(f"^Calibration: {CAL}$", b, re.MULTILINE), b
    w = lane.ready()
    assert re.search("^" + judged_line(q, PICK[q], CAL, lane), w, re.MULTILINE), w


THRESHOLD = {"accuracy_min": 0.699, "brier_max": 0.39, "accepted": True}
HELD_OUT = {"below": {"accuracy": 0.571, "brier": 0.512}, "meets": {"accuracy": 0.8, "brier": 0.2}}
STATUS = {
    "below": "below accepted threshold (held-out accuracy 0.571, Brier 0.512; threshold held-out "
    "accuracy >= 0.699 and Brier <= 0.390, accepted)",
    "meets": "meets accepted threshold (held-out accuracy 0.800, Brier 0.200; threshold held-out "
    "accuracy >= 0.699 and Brier <= 0.390, accepted)",
}


def threshold(s: Scratch, which: str) -> None:
    """test-quality's threshold accepted, its held-out score below it or meeting it (a copy of the
    kit's scripts and evals, the suite edited): the answer still shown, labelled a model judgment,
    with the status; merge-ask ready with and without it (spec
    judgment#acceptance-judge-advisory)."""
    k = s.root / "kit"
    # The kit is where its scripts are; the qc sandbox binds the kit's own dirs, so those it
    # reads are copies (a link out of a kit under /tmp would dangle there); evidence is read
    # outside it.
    for d in ("scripts", "agents", ".agents"):
        shutil.copytree(ROOT / d, k / d, symlinks=True)
    (k / "evidence").symlink_to(ROOT / "evidence")
    for f in {src.relative_to(ROOT).parent for src in FAKES.values()}:
        shutil.copytree(ROOT / f, k / f, symlinks=True)
    s.link_fakes(k)
    (k / "evals").mkdir()
    for e in (ROOT / "evals").iterdir():
        (k / "evals" / e.name).symlink_to(e)
    (k / "evals" / "judgment-test-quality").unlink()
    shutil.copytree(ROOT / "evals" / "judgment-test-quality", k / "evals" / "judgment-test-quality")
    p = k / "evals" / "judgment-test-quality" / "suite.json"
    suite = json.loads(p.read_text())
    suite["calibration"].update(held_out=HELD_OUT[which], threshold=THRESHOLD)
    p.write_text(json.dumps(suite))
    s.run([str(k / "scripts" / "check-evals"), str(k / "evals")])
    lane = Lane(s, k)
    lane.verdict()
    err = lane.judge("test-quality", lane.state, "tautological").err
    line = said("created", "tautological", re.escape(STATUS[which]))
    assert any(re.fullmatch(line, ln) for ln in err.splitlines()), err
    b = lane.comment("test-quality")
    lines = b.splitlines()
    assert any(ln.startswith("Judgment: model judgment") for ln in lines), b
    assert "Answer: tautological" in lines, b
    assert f"Calibration: {STATUS[which]}" in lines, b
    w = lane.ready()
    assert re.search(
        "^" + judged_line("test-quality", "tautological", re.escape(STATUS[which]), lane),
        w,
        re.MULTILINE,
    ), w


def unwritable_ledger(s: Scratch) -> None:
    """spec spend#rule-write-fails: a directory in the ledger's place leaves the judge's output,
    line and exit as a writable one does (test_judge_posts), and says the spend went unrecorded."""
    lane = Lane(s)
    lane.verdict()
    (s.home / ".local" / "state" / "octo-feather" / "spend.jsonl").mkdir(parents=True)
    r = lane.judge("test-quality", lane.state, "tautological")
    assert r.out == URL, r.out
    assert any(
        re.fullmatch(said("created", "tautological", CAL), ln) for ln in r.err.splitlines()
    ), r.err
    unrecorded = (
        "octo-feather-lane spend record: spend unrecorded (1 call(s), $0.000100): cannot write "
    )
    assert unrecorded in r.err, r.err


def test_refusals(case: Case) -> None:
    case(refusals)


def test_judge_posts(case: Case) -> None:
    case(judge_posts)


def test_rerun_in_place(case: Case) -> None:
    case(rerun_in_place)


def test_no_gate_reads_it(case: Case) -> None:
    case(no_gate_reads_it)


@pytest.mark.parametrize("q", sorted(set(PICK) - {"test-quality"}))
def test_real_suite(case: Case, q: str) -> None:
    case(real_suite, q)


@pytest.mark.parametrize("which", ["below", "meets"])
def test_threshold(case: Case, which: str) -> None:
    case(threshold, which)


def test_unwritable_ledger(case: Case) -> None:
    case(unwritable_ledger)


if __name__ == "__main__":
    main(
        refusals,
        judge_posts,
        rerun_in_place,
        no_gate_reads_it,
        real_suite,
        threshold,
        unwritable_ledger,
    )
