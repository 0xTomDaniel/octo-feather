"""A case over its runs and kits, and a review case, in-process at the grading module's stored-run
interface: `record`, `combine`, `summarize` and `review` of scripts/eval_grading.py (its
docstring; ticket #1090, seams agreed on it before any test). Each test produces its runs as the
command does (testkit/qa_box.py, Qa.evaluation: the real watch runs scripts/pi-role on the case's
role, which launches the testkit's Pi stand-in in a scratch git repo, then grade), stores them
with the module's writers alone, and asserts through what those print and write, with the
literals the command items it replaced asserted (parity: tests/parity/<item>/). No qc sandbox
and no octo-feather-qa process per case: the command's wiring (its header, the sandbox, usage
exits, --help) stays in tests/qa-runs.sh, tests/qa-baseline.sh and tests/qa-review.sh."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from eval_grading import UsageError, review
from testkit import Scratch
from testkit import qa_box as data
from testkit.jsonwalk import at, keys, seq
from testkit.qa_box import Qa, Want, load, printed

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def q(tmp_path: Path) -> Qa:
    """One test's qa world (testkit/qa_box.py's Qa) in its own scratch."""
    return Qa(Scratch(tmp_path))


RUN_FILES = ("prompt.md", "input.json", "transcript.jsonl", "grading.json", "result.json")


@pytest.mark.criterion("quality#acceptance-qa-repeats")
def test_qa_runs(q: Qa) -> None:
    """--runs (octo-feather-qa --help): alt, whose stub reads tdd on odd runs only, 2/3 with pass
    rate and spread FAILS, each run's line first, the failing run's facts named; run-<k>
    artifacts, result.json and summary.json runs/pass_rate/stddev; every run passing, 2/2 PASSES;
    one run (the default): no run lines, artifacts in the case dir, result.json with one run."""
    want = data.runs(q)  # alt/ (the trig suite plus alt)
    ev = q.evaluation(q.t / "alt" / "trig", ["alt"], runs=3)
    printed("\n".join(ev.lines), [w for w in want["alt"] if not w.text.startswith("^qa: run ")])
    c = ev.run_dir / "trig" / "alt"
    for k in (1, 2, 3):
        for f in RUN_FILES:
            assert (c / f"run-{k}" / f).exists(), (k, f)
        r = load(c / f"run-{k}" / "result.json")
        assert (at(r, "run"), at(r, "of"), at(r, "verdict")) == (
            k,
            3,
            "FAIL" if k == 2 else "PASS",
        ), r
        assert at(load(c / f"run-{k}" / "input.json"), "run") == k
    r = load(c / "result.json")
    assert at(r, "verdict") == "FAIL", r
    assert (at(r, "runs_passed"), at(r, "pass_rate"), at(r, "stddev")) == (2, 0.6667, 0.5774), r
    rs = [(at(x, "run"), at(x, "dir"), at(x, "verdict")) for x in seq(at(r, "runs"))]
    assert rs == [(1, "run-1", "PASS"), (2, "run-2", "FAIL"), (3, "run-3", "PASS")], rs
    assert {
        "suite",
        "id",
        "verdict",
        "deciding",
        "model",
        "seconds",
        "stop",
        "tool_calls",
        "kit_sha",
    } <= keys(r), r
    sm = load(ev.run_dir / "summary.json")
    assert (at(sm, "passed"), at(sm, "total"), at(sm, "runs")) == (0, 1, 3), sm
    assert at(sm, "cases", 0, "pass_rate") == 0.6667, sm
    # Every run passes: PASS, 2/2.
    ev = q.evaluation(q.t / "alt" / "trig", ["reads"], runs=2)
    printed("\n".join(ev.lines), want["every"])
    # One run (default): no run lines, artifacts in the case dir, result.json with one run.
    ev = q.evaluation(q.t / "alt" / "trig", ["reads"])
    printed("\n".join(ev.lines), [*want["one"], Want("^PASS trig/reads: ", "one run: its line")])
    c = ev.run_dir / "trig" / "reads"
    r = load(c / "result.json")
    assert not (c / "run-1").exists(), r
    assert "run" not in keys(r), r
    assert (at(r, "verdict"), at(r, "runs_passed"), at(r, "pass_rate"), at(r, "stddev")) == (
        "PASS",
        1,
        1.0,
        0.0,
    ), r
    assert [at(x, "dir") for x in seq(at(r, "runs"))] == ["."], r


@pytest.mark.criterion("quality#acceptance-qa-cost", "quality#acceptance-qa-baseline")
def test_qa_baseline(q: Qa) -> None:
    """--runs and --baseline (octo-feather-qa --help): a case's time and tokens as mean and spread
    (the stub's runs 1 and 2 report 220 and 240 tokens); a baseline kit c1 (its implementer lists
    no tdd: the case fails) beside the current kit c2 (it passes), with the compare table and the
    difference, each run's result.json, the case's and summary.json's baseline fields."""
    k = q.kits()
    c1, c2 = k.c1.sha, k.c2.sha
    want = data.baseline(c1, c2)
    ev = q.evaluation(q.t / "evals" / "trig", ["reads"], runs=2, configs=[k.c2._replace(ref=None)])
    printed("\n".join(ev.lines), want["cost"])
    d = ev.run_dir
    r = load(d / "trig" / "reads" / "result.json")
    assert [at(x, "usage", "total") for x in seq(at(r, "runs"))] == [220, 240], r
    assert at(r, "tokens") == {"mean": 230, "stddev": 14.1421}, r
    assert at(r, "cost_usd") == {"mean": 0.002, "stddev": 0.0}, r
    assert keys(at(r, "time")) == {"mean", "stddev"}, r
    f0 = at(r, "runs", 0, "facts", 0)
    assert at(f0, "status") == "pass", at(r, "runs", 0)
    assert "evidence" not in keys(f0), at(r, "runs", 0)
    assert at(load(d / "summary.json"), "cases", 0, "tokens", "mean") == 230
    # Baseline c1 (fails: no tdd) beside the head c2 (passes), the table.
    configs = [k.c1._replace(name="baseline", ref=c1[:9]), k.c2._replace(name="current", ref=None)]
    ev = q.evaluation(q.t / "evals" / "trig", ["reads"], runs=2, configs=configs)
    header = ("^qa: run ", "; baseline kit ")  # the run header: tests/qa-baseline.sh
    printed("\n".join(ev.lines), [w for w in want["compared"] if not w.text.startswith(header)])
    c = ev.run_dir / "trig" / "reads"
    r = load(c / "result.json")
    for side, sha in (("baseline", c1), ("current", c2)):
        for n in (1, 2):
            x = load(c / side / f"run-{n}" / "result.json")
            assert (at(x, "config"), at(x, "run"), at(x, "kit_sha")) == (side, n, sha), x
    b = at(r, "baseline")
    got = (
        at(r, "verdict"),
        at(r, "kit_sha"),
        at(b, "verdict"),
        at(b, "kit_sha"),
        at(b, "pass_rate"),
    )
    assert got == ("PASS", c2, "FAIL", c1, 0.0), r
    assert [at(x, "dir") for x in seq(at(b, "runs"))] == ["baseline/run-1", "baseline/run-2"], b
    assert at(b, "runs", 0, "facts", 0, "status") == "fail", b
    assert at(r, "delta", "pass_rate") == 1.0, at(r, "delta")
    assert at(r, "delta", "tokens") == 0.0, at(r, "delta")
    sm = load(ev.run_dir / "summary.json")
    assert at(sm, "baseline", "kit_sha") == c1, sm
    assert at(sm, "kit_sha") == c2, sm
    assert (at(sm, "passed"), at(sm, "total")) == (1, 1), sm


@pytest.mark.criterion("quality#acceptance-qa-review")
def test_qa_review(q: Qa) -> None:
    """A review case (octo-feather-qa --help, Review): awaiting review, never a pass, its output
    shown and kept; shown awaiting review until a verdict is recorded, then the verdict and note;
    the next run shows the latest verdict and note beside its new output; a bad verdict, a blank
    note, a case that is no review case refused."""
    rv = q.t / "rv" / "rv"
    data.essay(q, "The notes say hi.")
    ev = q.evaluation(rv)
    printed("\n".join(ev.lines), data.review()["run"])
    d1 = ev.run_dir
    id1 = d1.name
    want = data.review(id1)
    c = d1 / "rv" / "essay"
    k, r = load(c / "review.json"), load(c / "result.json")
    assert k == data.REVIEW_KEPT, k
    assert at(r, "verdict") == "REVIEW", r
    assert at(r, "review") == {"question": "Do the notes answer the brief?"}, r
    # Shown awaiting review until a verdict is recorded; then the verdict and note.
    printed("\n".join(review(d1, "rv/essay")), want["show"])
    printed("\n".join(review(d1, "rv/essay", "pass", "Clear and short.")), want["record"])
    printed("\n".join(review(d1, "rv/essay")), want["shown"])
    reviews = q.t / "out" / "reviews" / "rv" / "essay.jsonl"
    assert len(reviews.read_text().splitlines()) == 1, "the verdict is not one line"
    # The next run: the latest verdict and note beside its new output.
    data.essay(q, "The notes say hello.")
    printed("\n".join(q.evaluation(rv, runs=2).lines), want["next"])
    # Refused: a bad verdict, a blank note, a case that is no review case.
    with pytest.raises(UsageError, match="the verdict is pass or fail"):
        review(d1, "rv/essay", "maybe", "x")
    with pytest.raises(UsageError, match="the note is not blank"):
        review(d1, "rv/essay", "fail", " ")
    graded = q.evaluation(q.t / "evals" / "trig", ["reads"]).run_dir
    with pytest.raises(UsageError, match="not a review case"):
        review(graded, "trig/reads", "pass", "x")
