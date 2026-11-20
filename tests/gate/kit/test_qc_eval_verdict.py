"""--verdict's freshness (spec quality#acceptance-qc-eval-verdict; the rules: octo-feather-qa
--help, Verdict) in-process at the grading module's `verdict` (scripts/eval_grading.py, its
docstring; ticket #1090, seams agreed on it before any test): a scratch target holding a role,
launch, skill, case and fixture files (tests/gate/kit/qc_eval_verdict.py's, its case the
implementer's, which the kit's pi-role launches), its stored runs produced on its own suite as
the command does (testkit/qa_box.py, Qa.evaluation) and written by the module's writers alone,
at its first commit; judged at later heads. test_same_verdict and test_insufficient run qc on the
demo in its sandbox, through `case` (tests/gate/kit/conftest.py)."""

from __future__ import annotations

import json
import sys
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING

import pytest
from eval_grading import INSUFFICIENT, Judged, UsageError, review, verdict
from qc_eval_verdict import FILES, insufficient, same_verdict
from testkit import ROOT, Scratch
from testkit.qa_box import Config, Qa
from testkit.qc import target

if TYPE_CHECKING:
    from pathlib import Path

Case = Callable[..., None]
CASE = {"id": "c1", "role": "implementer", "fixture": "fx", "task": "Do it. STUB-READ-TDD"}
FACTS = [{"fact": "skill_read", "skill": "tdd"}]
EXPS = "evals/s1/reference/expectations.json"
SUITE = {"suite": "s1", "kind": "role-transcript", "description": "verdict", "timeout_s": 60}
WORLD = {
    **{k: v for k, v in FILES.items() if k != "agents/worker.md"},
    "agents/implementer.md": "the implementer role\n",
    "evals/s1/suite.json": json.dumps(SUITE),
    "evals/s1/cases.json": json.dumps([CASE]),
    EXPS: json.dumps({"c1": {"facts": FACTS}}),
}
SIBLING = (
    ("evals/s1/cases.json", json.dumps([CASE, dict(CASE, id="c2")])),
    (EXPS, json.dumps({"c1": {"facts": FACTS}, "c2": {"facts": FACTS}})),
)


@pytest.fixture
def q(tmp_path: Path) -> Qa:
    """One test's qa world (testkit/qa_box.py's Qa) in its own scratch."""
    return Qa(Scratch(tmp_path))


def change(q: Qa, r: Path, base: str, files: tuple[tuple[str, str], ...]) -> None:
    """R reset to BASE, then FILES written and committed."""
    q.s.git(r, "reset", "-q", "--hard", base)
    for path, text in files:
        (r / path).write_text(text)
    q.s.git(r, "commit", "-qam", f"change {' '.join(p for p, _ in files)}")


def stored(q: Qa, s: Path, sha: str, *, runs: int = 2) -> str:
    """The cases of the suite in S run RUNS times on this kit, recorded at kit SHA; its run id."""
    return q.evaluation(s, runs=runs, configs=[Config("", ROOT, None, sha)]).run_dir.name


def judged(q: Qa, r: Path, *pins: str, want: int) -> str:
    """--verdict PINS at R's head, its code WANT; its lines and its insufficient-evidence line."""
    j: Judged = verdict(list(pins), cwd=str(r), qa_dir=q.t / "out")
    out = "\n".join([*j.lines, j.insufficient or ""])
    assert j.code == want, out
    if want == INSUFFICIENT:
        assert (j.insufficient or "").startswith("octo-feather-qa: insufficient evidence: "), out
    return out


@pytest.mark.criterion("quality#acceptance-qc-eval-verdict")
def test_verdict_freshness(q: Qa) -> None:
    """--verdict in the judged repo: fresh PASS 0; a stored FAIL 1; each file the run reads
    changed (a fixture, a launched skill and extension, the case's own entry in cases.json and in
    expectations.json) 77 naming it; fresh 0 at heads changing only an unlaunched skill or adding a
    sibling case, or rebasing the fixture onto a base with the same tree."""
    r = target(q.s, WORLD, exe=("scripts/pi-role",))
    sha, h1 = q.s.git(r, "rev-parse", "HEAD~1"), q.s.git(r, "rev-parse", "HEAD")
    # The runs at kit sha: c1 (PASS twice), and c1 as its stub alternates (run 2 skips the read:
    # a stored FAIL); produced at once.
    alt = q.t / "alt" / "s1"
    q.s.run(["cp", "-r", str(r / "evals"), str(q.t / "alt")])
    task = "Do it. STUB-READ-TDD STUB-ALTERNATE"
    (alt / "cases.json").write_text(json.dumps([dict(CASE, task=task)]))
    with ThreadPoolExecutor() as pool:
        made = [pool.submit(stored, q, d, sha) for d in (r / "evals" / "s1", alt)]
        run, fa = (m.result() for m in made)
    pin = f"{run}/s1/c1"
    out = judged(q, r, pin, want=0)
    want = f"PASS s1/c1: stored PASS, run {run}, kit {sha[:12]}, runs 2/2 passed; fresh at HEAD"
    assert f"{want} {h1[:12]}" in out, out
    out = judged(q, r, pin, f"{fa}/s1/c1", want=1)
    assert f"FAIL s1/c1: stored FAIL, run {fa}, kit" in out, out
    assert "runs 1/2 passed" in out, out
    for files, named in (
        ((("evals/fixtures/fx/a.txt", "fixture, changed\n"),), "evals/fixtures/fx tree changed"),
        (
            ((".agents/skills/s/SKILL.md", "the skill, changed\n"),),
            ".agents/skills/s/SKILL.md changed",
        ),
        ((("extensions/e.ts", "changed\n"),), "extensions/e.ts changed"),
        (
            (("evals/s1/cases.json", json.dumps([dict(CASE, task="Other.")])),),
            "evals/s1/cases.json case c1 changed",
        ),
        (((EXPS, json.dumps({"c1": {"facts": [*FACTS, *FACTS]}})),), f"{EXPS} case c1 changed"),
    ):
        change(q, r, h1, files)
        out = judged(q, r, pin, want=INSUFFICIENT)
        assert f"INSUFFICIENT s1/c1: stored PASS, run {run}" in out, out
        assert named in out.splitlines()[-1], out
    for files in (((".agents/skills/other/SKILL.md", "changed\n"),), SIBLING):
        change(q, r, h1, files)
        assert want in judged(q, r, pin, want=0)
    # fx rewritten as base fixture `bs` plus a manifest (schema.md, Fixtures): the same tree, fresh;
    # a byte of the base changed: fx's tree changed.
    q.s.git(r, "reset", "-q", "--hard", h1)
    (r / "evals/fixtures/bs").mkdir()
    q.s.git(r, "mv", "evals/fixtures/fx/a.txt", "evals/fixtures/bs/a.txt")
    (r / "evals/fixtures/fx/.eval-fixture.json").write_text(json.dumps({"base": "bs"}))
    q.s.git(r, "add", "-A")
    q.s.git(r, "commit", "-qm", "fx onto base bs")
    assert want in judged(q, r, pin, want=0)
    (r / "evals/fixtures/bs/a.txt").write_text("fixture, changed\n")
    q.s.git(r, "commit", "-qam", "base byte")
    out = judged(q, r, pin, want=INSUFFICIENT)
    assert "evals/fixtures/fx tree changed" in out.splitlines()[-1], out


@pytest.mark.criterion("quality#acceptance-qc-eval-verdict")
def test_verdict_insufficient(q: Qa) -> None:
    """--verdict in the judged repo: a run at a kit sha that is no commit there 77; a review case
    with no recorded verdict 77, then its recorded fail 1; usage refused."""
    r = target(q.s, WORLD, exe=("scripts/pi-role",))
    # A kit sha that is no commit here.
    bad = stored(q, r / "evals" / "s1", "0" * 40, runs=1)
    out = judged(q, r, f"{bad}/s1/c1", want=INSUFFICIENT)
    assert f"kit sha {'0' * 40} of run {bad} is not a commit" in out, out
    # A review case: no verdict recorded, then a recorded fail.
    rv = dict(CASE, id="rv", review={"question": "Good?"})
    (r / "evals" / "s1" / "cases.json").write_text(json.dumps([CASE, rv]))
    (r / EXPS).write_text(json.dumps({"c1": {"facts": FACTS}, "rv": {"facts": []}}))
    q.s.git(r, "commit", "-qam", "review case")
    rid = q.evaluation(
        r / "evals" / "s1",
        ["rv"],
        configs=[Config("", ROOT, None, q.s.git(r, "rev-parse", "HEAD"))],
    ).run_dir
    rpin = f"{rid.name}/s1/rv"
    out = judged(q, r, rpin, want=INSUFFICIENT)
    assert f"no maintainer verdict recorded for review case s1/rv in run {rid.name}" in out, out
    review(rid, "s1/rv", "fail", "n")
    out = judged(q, r, rpin, want=1)
    assert f"FAIL s1/rv: stored FAIL, run {rid.name}" in out, out
    assert "review; fresh at HEAD" in out, out
    for bad_pins in ((), ("x/y",), ("--runs", "2")):
        with pytest.raises(UsageError, match="--verdict takes one or more RUN_ID/SUITE/CASE"):
            verdict(list(bad_pins), cwd=str(r), qa_dir=q.t / "out")


@pytest.mark.e2e
@pytest.mark.skipif(sys.platform == "darwin", reason="the qc sandbox needs Linux")
@pytest.mark.criterion("quality#acceptance-qc-eval-verdict")
def test_same_verdict(case: Case) -> None:
    case(same_verdict)


@pytest.mark.e2e
@pytest.mark.skipif(sys.platform == "darwin", reason="the qc sandbox needs Linux")
@pytest.mark.criterion("quality#acceptance-qc-eval-verdict")
def test_insufficient(case: Case) -> None:
    case(insufficient)
