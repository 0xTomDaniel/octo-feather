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
