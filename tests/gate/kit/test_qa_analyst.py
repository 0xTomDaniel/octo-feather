"""The deterministic analysis (spec quality#acceptance-qa-analyst; rules: octo-feather-qa --help,
Analysis), in-process at the grading module's `analysis` (scripts/eval_grading.py, its docstring;
ticket #1090, seams agreed on it before any test): each test produces the an suite's runs on the
kit copy's two kits as the command does (testkit/qa_box.py: Qa.evaluation, Qa.kits; c1 the
implementer not listing tdd, c2 the head), stored by the module's writers alone, and asserts the
flags with the literals the command items it replaced asserted (parity: tests/parity/qa-analyst/).
--analyze's rerun of a stored run is the command's (test_analyze_rerun); its usage exits:
tests/gate/kit/qa_analyst.py, through `case` (tests/gate/kit/conftest.py)."""

from __future__ import annotations

import subprocess
from collections.abc import Callable
from typing import TYPE_CHECKING

import pytest
from eval_grading import analysis
from qa_analyst import analyze_usage
from testkit import Scratch
from testkit.qa_box import NO_PULL, Evaluation, Q, Qa

if TYPE_CHECKING:
    from pathlib import Path

    from eval_grading import Result

Case = Callable[..., None]
HEAD = "qa: analysis (deterministic, no model; rules: octo-feather-qa --help, --analyze):"
# Each case's time mean on each kit, as the runs record it (record's seconds): baseline, current.
STATED = {"same": (10.0, 10.0), "costly": (10.0, 20.0)}


@pytest.fixture
def q(tmp_path: Path) -> Qa:
    """One test's qa world (testkit/qa_box.py's Qa) in its own scratch."""
    return Qa(Scratch(tmp_path))


def compared(q: Qa, *ids: str, runs: int, stated: bool = False) -> Evaluation:
    """The an suite's cases IDS run RUNS times each, c1 the baseline beside c2; each run's
    seconds STATED's when STATED."""
    k = q.kits()
    configs = [k.c1._replace(name="baseline"), k.c2._replace(name="current", ref=None)]

    def secs(c: str, cfg: str, _k: int) -> float:
        return STATED[c][cfg == "current"]

    return q.evaluation(q.an(), ids, runs=runs, configs=configs, secs=secs if stated else None)


def flags(ev: Evaluation) -> tuple[Result, list[str]]:
    """The analysis of EV's cases (each combine's result)."""
    return analysis(ev.cases)


@pytest.mark.criterion("quality#acceptance-qa-analyst")
def test_comparison(q: Qa) -> None:
    """--baseline, one run each of same and costly, each run's time stated: same
    non-discriminating, costly a cost tradeoff in time and tokens (its stub's 3 more messages on
    c2: 220 to 550 tokens)."""
    ev = compared(q, "same", "costly", runs=1, stated=True)
    a, got = flags(ev)
    want = [
        HEAD,
        "  non-discriminating case an/same: every run on both kits passed",
        (
            "  cost tradeoff an/costly: pass rate 1.00 on both kits; time mean 10.0 to 20.0;"
            " tokens mean 220.0 to 550.0"
        ),
    ]
    assert got == want, got
    assert a["threshold"] == 0.5, a
    assert a["non_discriminating_facts"] == a["high_variance"] == [], a
    tokens = {x["case"]: x.get("tokens") for x in a["cost_tradeoffs"]}
    assert tokens.get("an/costly") == {"baseline": 220.0, "current": 550.0}, a
    assert tokens.get("an/same") is None, a


@pytest.mark.criterion("quality#acceptance-qa-analyst")
def test_variance(q: Qa) -> None:
    """--baseline, two runs: a case passing every other run on the current kit, and never on c1,
    is high variance on that kit, and its pull fact, passing in every run, is non-discriminating."""
    a, got = flags(compared(q, "alt", runs=2))
    want = [
        HEAD,
        "  non-discriminating fact an/alt: skill_not_read pull: pass in every run on both kits",
        "  high variance an/alt: current kit pass rate 0.50 +/- 0.71",
    ]
    assert got == want, got
    hv = [{"case": "an/alt", "kit": "current", "pass_rate": 0.5, "stddev": 0.7071}]
    assert a["high_variance"] == hv, a
    nd = [{"case": "an/alt", "fact": NO_PULL, "status": "pass"}]
    assert a["non_discriminating_facts"] == nd, a
    assert a["non_discriminating_cases"] == a["cost_tradeoffs"] == [], a


@pytest.mark.criterion("quality#acceptance-qa-analyst")
def test_no_baseline(q: Qa) -> None:
    """No baseline, two runs: high variance alone, never a comparison flag (alt's pull fact is
    non-discriminating only beside a baseline: test_variance)."""
    k = q.kits()
    ev = q.evaluation(q.an(), ["alt"], runs=2, configs=[k.c2._replace(ref=None)])
    _, got = flags(ev)
    assert got == [HEAD, "  high variance an/alt: pass rate 0.50 +/- 0.71"], got


def test_analyze_rerun(q: Qa) -> None:
    """--analyze on a stored run (one --baseline run each of same and costly): the analysis of
    its cases, from summary.json alone, starting no pi and no sandbox (a poison pi first on
    PATH, which no rerun may start)."""
    ev = compared(q, "same", "costly", runs=1)
    live = flags(ev)[1]
    poison = q.t / "poison"
    poison.mkdir()
    (poison / "pi").write_text(f"#!/bin/sh\ntouch {q.t / 'ran'}\nexit 99\n")
    (poison / "pi").chmod(0o755)
    env = {"PATH": f"{poison}:{q.s.env['PATH']}"}
    p = subprocess.run(
        [Q, "--analyze", str(ev.run_dir)],
        env={**q.s.env, **env},
        capture_output=True,
        text=True,
        check=False,
    )
    assert p.returncode == 0, p
    rerun = p.stdout.splitlines()
    assert rerun[rerun.index(HEAD) :] == live, f"rerun: {p.stdout}\nlive: {live}"
    assert not (q.t / "ran").exists(), f"the rerun started pi: {p.stdout}"
    assert "qc sandbox" not in p.stdout + p.stderr, f"the rerun started a sandbox: {p.stderr}"


def test_analyze_usage(case: Case) -> None:
    case(analyze_usage)
