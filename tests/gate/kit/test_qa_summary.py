"""An evaluation's summary.json and the lines it ends with, in-process at the grading module's
`summarize` (scripts/eval_grading.py, its docstring; ticket #1090, its seam records at #1090
comment 7028433795). Each test produces its runs as the command does (testkit/qa_box.py,
Qa.evaluation: the real watch over pi-role and the Pi stand-in, then grade, stored by record,
combine and summarize) and asserts what summarize wrote and returned, with the literals the
command items asserted (tests/qa-runs.sh, tests/qa-baseline.sh, tests/qa-review.sh,
test_qa_analyst.py comparison, before #1090). The runs and cases themselves: test_qa_stored.py,
test_qa_analyst.py."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from eval_grading import analysis
from testkit import Scratch
from testkit import qa_box as data
from testkit.jsonwalk import at
from testkit.qa_box import Qa, load, printed

if TYPE_CHECKING:
    from pathlib import Path

TOTALS = "^qa: 0/1 passed"
# Each an case's time mean on each kit, as the runs record it (record's seconds): baseline, current.
STATED = {"same": (10.0, 10.0), "costly": (10.0, 20.0)}


@pytest.fixture
def q(tmp_path: Path) -> Qa:
    """One test's qa world (testkit/qa_box.py's Qa) in its own scratch."""
    return Qa(Scratch(tmp_path))


@pytest.mark.criterion("quality#acceptance-qa-repeats", "quality#acceptance-public-surfaces")
def test_qa_summary_runs(q: Qa) -> None:
    """--runs 3 of alt (its stub reads tdd on odd runs only): summary.json's passed, total, runs
    and the case's pass rate; the totals line counting the case failing one run as not passed. A
    review case's run: counted as not passed."""
    want = data.runs(q)
    ev = q.evaluation(q.t / "alt" / "trig", ["alt"], runs=3)
    sm = load(ev.run_dir / "summary.json")
    assert (at(sm, "passed"), at(sm, "total"), at(sm, "runs")) == (0, 1, 3), sm
    assert at(sm, "cases", 0, "pass_rate") == 0.6667, sm
    printed("\n".join(ev.ending), [w for w in want["alt"] if w.text == TOTALS])
    data.essay(q, "The notes say hi.")
    ev = q.evaluation(q.t / "rv" / "rv")
    printed("\n".join(ev.ending), [w for w in data.review()["run"] if w.text == TOTALS])


@pytest.mark.criterion(
    "quality#acceptance-qa-baseline",
    "quality#acceptance-qa-analyst",
    "quality#acceptance-public-surfaces",
)
def test_qa_summary_kits(q: Qa) -> None:
    """summary.json of a case's runs on one kit (its tokens mean, the stub's runs 1 and 2 220
    and 240 tokens) and on both (baseline c1 beside current c2: both kit shas, passed and total);
    its analysis that of its cases (same and costly on both kits, each run's time stated)."""
    k = q.kits()
    c1, c2 = k.c1.sha, k.c2.sha
    ev = q.evaluation(q.t / "evals" / "trig", ["reads"], runs=2, configs=[k.c2._replace(ref=None)])
    assert at(load(ev.run_dir / "summary.json"), "cases", 0, "tokens", "mean") == 230
    configs = [k.c1._replace(name="baseline", ref=c1[:9]), k.c2._replace(name="current", ref=None)]
    ev = q.evaluation(q.t / "evals" / "trig", ["reads"], runs=2, configs=configs)
    sm = load(ev.run_dir / "summary.json")
    assert at(sm, "baseline", "kit_sha") == c1, sm
    assert at(sm, "kit_sha") == c2, sm
    assert (at(sm, "passed"), at(sm, "total")) == (1, 1), sm

    def secs(c: str, cfg: str, _k: int) -> float:
        return STATED[c][cfg == "current"]

    configs = [k.c1._replace(name="baseline"), k.c2._replace(name="current", ref=None)]
    ev = q.evaluation(q.an(), ["same", "costly"], configs=configs, secs=secs)
    a, _ = analysis(ev.cases)
    sm = load(ev.run_dir / "summary.json")
    assert at(sm, "analysis") == a, sm
