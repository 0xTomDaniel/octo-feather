"""The factory evals' fact grading and stop rule, in-process at the grading module's interface:
`plan`, `watch` and `grade` of scripts/eval_grading.py (its docstring; ticket #1089, seams agreed
on it before any test). Each test runs a stub suite's cases (testkit/qa_box.py's builders, the
command items' own): the real watch runs scripts/pi-role on the case's role, which launches the
testkit's Pi stand-in (pi_agent.py, first on PATH; its docstring: what each STUB- token makes it
do) in a scratch git repo, then grade; no qc sandbox and no octo-feather-qa process per case. Each
asserts every case's verdict and the deciding facts with the literals the command items it
replaced asserted (parity: tests/parity/<item>/). The command's wiring (the sandbox, artifacts,
printed lines, selection, usage) stays in tests/qa.sh, tests/qa-rt.sh and the other qa items."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest
from testkit import Scratch
from testkit import qa_box as data
from testkit.qa_box import Qa, graded_check

if TYPE_CHECKING:
    from pathlib import Path

    from eval_grading import Run


@pytest.fixture
def q(tmp_path: Path) -> Qa:
    """One test's qa world (testkit/qa_box.py's Qa) in its own scratch."""
    return Qa(Scratch(tmp_path))


def fs_marks(r: Run) -> list[object]:
    """The marks of each qa_fs event the watcher wrote in R's transcript, in order."""
    lines = (r.transcript or "").splitlines()
    return [json.loads(x)["marks"] for x in lines if '"type": "qa_fs"' in x]


def by_target(r: Run) -> dict[tuple[str, object], tuple[str, str]]:
    """R's graded facts by (skill, before): (status, evidence)."""
    return {(str(f["skill"]), f.get("before")): (f["status"], str(f["evidence"])) for f in r.graded}


DECLARED_TIMEOUT = ("early", "earlyrb")  # each stopped by the watcher's timeout (suite timeout_s 8)


@pytest.mark.criterion("quality#acceptance-qa-per-case", "quality#acceptance-qa-role-cases")
def test_qa_declared(q: Qa) -> None:
    """declared (schema.md, Final JSON): one of its list passes (ok also reads tdd early and still
    passes: the watcher kept it running), outside the list, no block and two blocks fail."""
    wants = [w for w in data.declared(q) if w.line.split("/")[1] not in DECLARED_TIMEOUT]
    runs = q.graded(q.t / "dec", "dec", ["ok", "out", "none", "two"])
    graded_check(runs, wants)


@pytest.mark.e2e
@pytest.mark.criterion("quality#acceptance-qa-per-case", "quality#acceptance-qa-role-cases")
def test_qa_declared_timeout(q: Qa) -> None:
    """A run the watcher's timeout stops (a real wait: suite timeout_s 8; why no time seam: #1089):
    declared fails stopped before its final message; skill_read_before final_message fails, its
    target never reached (schema.md, Facts)."""
    wants = [w for w in data.declared(q) if w.line.split("/")[1] in DECLARED_TIMEOUT]
    runs = q.graded(q.t / "dec", "dec", DECLARED_TIMEOUT)
    graded_check(runs, wants)
    assert all((r.stop or {}).get("stop") == "timeout" for r in runs.values()), runs


@pytest.mark.criterion("quality#acceptance-qa-per-case", "quality#acceptance-qa-role-cases")
def test_qa_field_lines(q: Qa) -> None:
    """field_lines column-0 only (bullet and fenced fail; none, every, includes, Owner restated,
    other fields, a two-word field), tool_called (an error or empty result skipped, a named
    tool's text result passes, none called fails), branch_paths committed and uncommitted
    (untouched, touched)."""
    q.fl()
    graded_check(q.graded(q.t / "fl", "fl"), data.field_lines())


@pytest.mark.criterion("quality#acceptance-qa-per-case", "quality#acceptance-qa-role-cases")
def test_qa_before_tool(q: Qa) -> None:
    """tool_called_before before edit_under (rules: schema.md, Facts, Before targets): a search
    before the first write under the path passes; one only after it, or a run that never writes
    there, fails; skill_read_before takes edit_under too."""
    wants, _ = data.before_tool(q)
    graded_check(q.graded(q.t / "tb", "tb"), wants)


@pytest.mark.criterion("quality#acceptance-qa-skill-triggers")
def test_qa_cap_batch(q: Qa) -> None:
    """At the max_tool_calls bound (3; the stop rule: octo-feather-qa --help): a skill read in
    flight in the codemode batch that crosses it is graded, the run stopped once decided at 5
    calls; a read started after that batch is never credited, the run stopped at the bound."""
    wants = data.cap_batch(q)
    runs = q.graded(q.t / "cb", "cb")
    graded_check(runs, wants)
    assert runs["inbatch"].stop is not None
    assert runs["afterbatch"].stop is not None
    assert (runs["inbatch"].stop["stop"], runs["inbatch"].stop["tool_calls"]) == ("decided", 5)
    assert (runs["afterbatch"].stop["stop"], runs["afterbatch"].stop["tool_calls"]) == (
        "max_tool_calls",
        4,
    )


@pytest.mark.criterion("quality#acceptance-qa-per-case", "quality#acceptance-qa-skill-triggers")
def test_qa_stop(q: Qa) -> None:
    """The trig suite's linger (a model that never ends: stopped once its fact is decided) and
    crash (a pi that exits 3 without an answer: its case fails, not passing skill_not_read)."""
    runs = q.graded(q.t / "evals", "trig", ["linger", "crash"])
    assert runs["linger"].verdict == "PASS", runs["linger"]
    assert (runs["linger"].stop or {}).get("stop") == "decided", runs["linger"]
    assert runs["crash"].verdict == "FAIL", runs["crash"]
    assert "run: pi exited 3 on its own" in runs["crash"].deciding, runs["crash"]


@pytest.mark.criterion(
    "quality#acceptance-qa-per-case",
    "quality#acceptance-qa-skill-triggers",
    "quality#acceptance-qa-role-cases",
)
def test_qa_rt(q: Qa) -> None:
    """The rt suite's cases on the plain fixtures but setup (its repo setup: tests/qa-rt.sh): skill
    load (read, cat; ls, grep, head, truncated; a fixture-only skill), declared_includes
    pass, missing, not a list, a kit_contract_edit fact failing on an unread skill; no grading
    keeps a private key."""
    q.rt()
    runs = q.graded(q.t / "rt", "rt", [c for c in data.RT if c != "setup"])
    graded_check(runs, [w for w in data.rt() if w.line != "PASS rt/setup"])
    assert all(not str(k).startswith("_") for f in runs["partial"].graded for k in f), runs
    # agents/x.md, AGENTS.md, a patch
    assert fs_marks(runs["roleedit"]) == [
        ["edit", "kit_contract_edit"],
        ["edit"],
        ["edit", "kit_contract_edit"],
    ], runs["roleedit"]
    g = runs["roleedit"].graded[0]
    assert g["status"] == "fail", g
    assert "first kit_contract_edit at tool call 2 of 4 (bash mkdir -p agents" in g["evidence"], g
    assert "no load of tdd/SKILL.md" in g["evidence"], g


@pytest.mark.criterion("quality#acceptance-qa-per-case", "quality#acceptance-qa-role-cases")
def test_qa_rt_targets(q: Qa) -> None:
    """The rt suite's cases on the python-app fixtures: before targets from filesystem snapshots
    (test_write by the fixture's declared tests, edit, git_commit, git_push, gh_call,
    final_message, kit_contract_edit), a target never reached fails."""
    q.rt()
    runs = q.graded(q.t / "rt", "rt", data.RT_TARGETS)
    lines_, want = data.rt_targets()
    graded_check(runs, lines_)
    g = by_target(runs["order"])
    for k, (st, ev) in want.items():
        assert g[k][0] == st, (k, g[k])
        assert ev in g[k][1], (k, g[k])
    fs = [json.loads(x) for x in (runs["order"].transcript or "").splitlines() if '"qa_fs"' in x]
    assert [e["marks"] for e in fs] == [
        ["edit", "test_write"],
        ["git_commit"],
        ["git_push"],
        ["gh_call"],
    ], fs
    assert fs[-1]["gh"] == ["gh pr create --title x"], fs[-1]
    g2 = {f.get("before"): str(f["evidence"]) for f in runs["fsonly"].graded}
    assert "first test_write at tool call 4 of 4" in g2["test_write"], g2
    assert "first edit at tool call 4 of 4" in g2["edit"], g2
    # tests/README.md, tests/test_y.py, specs/cli_check.py
    assert fs_marks(runs["declared"]) == [["edit"], ["edit"], ["edit", "test_write"]], runs[
        "declared"
    ]
    g3 = runs["declared"].graded[0]
    assert g3["status"] == "pass", g3
    assert (
        "first test_write at tool call 5 of 5 (bash echo 'def test_c(): pass' > specs/cli_check.py)"
        in str(g3["evidence"])
    ), g3
    g4 = {f.get("before"): (f["status"], str(f["evidence"])) for f in runs["contract"].graded}
    assert g4["edit"][0] == "fail", g4
    assert "first edit at tool call 2 of 4" in g4["edit"][1], g4
    kce = g4["kit_contract_edit"]
    assert kce[0] == "pass", g4
    assert "loaded at tool call 3 of 4" in kce[1], g4
    assert "before first kit_contract_edit at tool call 4 of 4" in kce[1], g4
    tw = (
        "test_write: target never reached (no test_write in 4 tool calls); "
        "loaded at tool call 3 of 4"
    )
    assert g4["test_write"][0] == "fail", g4
    assert tw in g4["test_write"][1], g4
