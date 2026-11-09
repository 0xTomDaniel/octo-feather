"""QA schema input scenarios through the real public commands.

Partial conversions of qa-shape, qa-before-tool and qa-review: validation only,
not transcript grading. Fixture writers create input data, never kit command
replacements, synthetic transcripts or classifier responses.
"""

from __future__ import annotations

import copy
import json
import shutil
from typing import TYPE_CHECKING

from testkit import ROOT, Scratch, kit, main

if TYPE_CHECKING:
    from pathlib import Path

CaseData = dict[str, object]
FactData = dict[str, object]
Expectations = dict[str, dict[str, list[FactData]]]


def write_suite(
    root: Path, name: str, kind: str, cases: list[CaseData], expectations: Expectations,
) -> None:
    """The existing suite JSON format, as caller-supplied input to check-evals."""
    d = root / name
    (d / "reference").mkdir(parents=True, exist_ok=True)
    (root / "fixtures" / "fx").mkdir(parents=True, exist_ok=True)
    (root / "fixtures" / "fx" / "README.md").write_text("fixture\n")
    (d / "suite.json").write_text(json.dumps({
        "suite": name, "kind": kind, "description": "QA schema inputs",
        "max_tool_calls": 10, "timeout_s": 60,
    }))
    (d / "cases.json").write_text(json.dumps(cases))
    (d / "reference" / "expectations.json").write_text(json.dumps(expectations))


def trigger_inputs() -> tuple[list[CaseData], Expectations]:
    cases: list[CaseData] = [
        {"id": i, "role": "implementer", "fixture": "fx", "task": task,
         "should_trigger": trigger, "split": split}
        for i, task, trigger, split in (
            ("reads", "Build it. STUB-READ-TDD", True, "train"),
            ("near", "Only look. STUB-READ-TDD", False, "held-out"),
            ("quiet", "Only look.", False, "train"),
        )
    ]
    expectations: Expectations = {
        "reads": {"facts": [{"fact": "skill_read", "skill": "tdd"}]},
        "near": {"facts": [{"fact": "skill_not_read", "skill": "tdd"}]},
        "quiet": {"facts": [{"fact": "skill_not_read", "skill": "tdd"}]},
    }
    return cases, expectations


def trigger_case_fields(s: Scratch) -> None:
    root = s.root / "evals"
    cases, expectations = trigger_inputs()
    write_suite(root, "trig", "skill-trigger", cases, expectations)
    s.run([kit("check-evals"), str(root)])
    variants: list[tuple[int, str | None, CaseData, str]] = [
        (0, "task", {}, "trig/cases.json case reads: field task: missing"),
        (1, "split", {}, "trig/cases.json case near: field split: missing"),
        (0, None, {"facts": expectations["reads"]["facts"]},
         "trig/cases.json case reads: field facts: unknown field"),
        (0, None, {"branch": "x"},
         "trig/cases.json case reads: field branch: unknown field; "
         "only a role-transcript case sets up a repo"),
        (0, None, {"should_trigger": False},
         "case reads: field should_trigger: false, but no skill_not_read fact"),
        (0, None, {"role": "nobody"}, "case reads: field role: no kit role agents/nobody.md"),
    ]
    for index, removed, updates, expected in variants:
        c = copy.deepcopy(cases)
        if removed:
            del c[index][removed]
        c[index].update(updates)
        write_suite(root, "trig", "skill-trigger", c, expectations)
        got = s.run([kit("check-evals"), str(root)], want=1)
        assert expected in got.out + got.err, got
    # The last input is the legacy malformed-role QA refusal.
    got = s.run([kit("octo-feather-qa"), "--evals", str(root)], want=2)
    assert "field role: no kit role" in got.out + got.err, got
    assert "qa: run " not in got.out + got.err, got


def trigger_fact_fields(s: Scratch) -> None:
    root = s.root / "evals"
    cases, expectations = trigger_inputs()
    variants: list[tuple[list[FactData], str]] = [
        ([{"fact": "skill_vibes", "skill": "tdd"}],
         "case reads fact #1: field fact: unknown fact type 'skill_vibes'"),
        ([{"fact": "skill_read", "skill": "nope"}],
         "case reads fact #1: field skill: no .agents/skills/nope/SKILL.md "
         "in the kit or in fixture fx"),
        ([{"fact": "skill_read", "skill": "tdd"}, {"fact": "attempt_blocked", "kind": "vibes"}],
         "case reads fact #2: field kind: must be one of "
         "['credential', 'herdr', 'lane_state', 'network', 'repo'], got 'vibes'"),
        ([{"fact": "skill_read", "skill": "tdd"}, {"fact": "declared", "field": "", "in": []}],
         "case reads fact #2: field field: must be a non-empty string"),
        ([{"fact": "skill_read", "skill": "tdd"},
          {"fact": "declared", "field": "rung", "in": [1]}],
         "case reads fact #2: field in: must be a non-empty list of strings"),
    ]
    for facts, expected in variants:
        e = copy.deepcopy(expectations)
        e["reads"]["facts"] = facts
        write_suite(root, "trig", "skill-trigger", cases, e)
        got = s.run([kit("check-evals"), str(root)], want=1)
        assert expected in got.out + got.err, got
    e = copy.deepcopy(expectations)
    del e["quiet"]
    write_suite(root, "trig", "skill-trigger", cases, e)
    got = s.run([kit("check-evals"), str(root)], want=1)
    assert "trig/cases.json case quiet: field id: no expectations" in got.out + got.err, got
    e = copy.deepcopy(expectations)
    e["ghost"] = e["quiet"]
    write_suite(root, "trig", "skill-trigger", cases, e)
    got = s.run([kit("check-evals"), str(root)], want=1)
    assert "trig/reference/expectations.json case ghost: field id: no case in cases.json" in (
        got.out + got.err
    ), got


def trigger_leaks(s: Scratch) -> None:
    root = s.root / "evals"
    cases, expectations = trigger_inputs()
    reordered = json.dumps(
        dict(reversed(list(expectations["quiet"]["facts"][0].items()))), indent=3,
    )
    for index, suffix, expected in (
        (0, " Read .agents/skills/tdd/SKILL.md first.",
         "case reads: field task: shows the agent its grade (skill path tdd/SKILL.md)"),
        (2, " Graded on " + json.dumps(expectations["quiet"]["facts"][0]),
         "case quiet: field task: shows the agent its grade (fact #1 as JSON"),
        (2, " Grade: " + reordered,
         "case quiet: field task: shows the agent its grade (fact #1 as JSON"),
        (0, " See skills/tdd/ for it.",
         "case reads: field task: shows the agent its grade (skill path skills/tdd)"),
    ):
        c = copy.deepcopy(cases)
        c[index]["task"] = str(c[index]["task"]) + suffix
        write_suite(root, "trig", "skill-trigger", c, expectations)
        got = s.run([kit("check-evals"), str(root)], want=1)
        assert expected in got.out + got.err, got
    cases[0]["task"] = (
        str(cases[0]["task"]) + ' Use the implement skill; .agents/skills/implement-spec/SKILL.md'
        ' and skills/implement-spec/ are not it; {"fact": "skill_read"}'
    )
    expectations["reads"]["facts"][0]["skill"] = "implement"
    write_suite(root, "trig", "skill-trigger", cases, expectations)
    s.run([kit("check-evals"), str(root)])


def trigger_shape(s: Scratch) -> None:
    """Original trigger field/leak oracles, including QA refusal, not role setup fields."""
    trigger_case_fields(s)
    trigger_fact_fields(s)
    trigger_leaks(s)


def before_shape(s: Scratch) -> None:
    """All four qa-before-tool malformed target/tools oracles, same case id."""
    root = s.root / "evals"
    cases: list[CaseData] = [
        {"id": "searched", "role": "implementer", "fixture": "fx", "task": "Build it."},
    ]
    fact: FactData = {
        "fact": "tool_called_before", "tools": ["web_a", "web_b"],
        "before": {"edit_under": ["lib/x/"]},
    }
    write_suite(root, "tb", "role-transcript", cases, {"searched": {"facts": [fact]}})
    s.run([kit("check-evals"), str(root)])
    variants: list[tuple[dict[str, object] | None, str]] = [
        ({"edit_under": []},
         "field before: edit_under must be a non-empty list of relative paths"),
        ({"edit_under": ["/abs/"]},
         "field before: edit_under must be a non-empty list of relative paths"),
        ({"edit_under": ["lib/"], "x": 1}, "field before: must be one of"),
        (None, "field tools: missing"),
    ]
    for target, expected in variants:
        f = copy.deepcopy(fact)
        if target is None:
            del f["tools"]
        else:
            f["before"] = target
        write_suite(root, "tb", "role-transcript", cases, {"searched": {"facts": [f]}})
        got = s.run([kit("check-evals"), str(root)], want=1)
        assert "case searched fact #1: " + expected in got.out + got.err, got


def review_shape(s: Scratch) -> None:
    """A review requires its question and cannot carry graded facts."""
    root = s.root / "evals"
    case: CaseData = {
        "id": "essay", "role": "implementer", "fixture": "fx", "task": "Write the notes.",
        "review": {"question": "Do the notes answer the brief?"},
    }
    write_suite(root, "rv", "role-transcript", [case], {"essay": {"facts": []}})
    s.run([kit("check-evals"), str(root)])
    case["review"] = {}
    write_suite(root, "rv", "role-transcript", [case], {"essay": {"facts": []}})
    got = s.run([kit("check-evals"), str(root)], want=1)
    assert "rv/cases.json case essay: field review.question: missing or blank" in (
        got.out + got.err
    ), got
    case["review"] = {"question": "Do the notes answer the brief?"}
    write_suite(root, "rv", "role-transcript", [case], {
        "essay": {"facts": [{"fact": "skill_read", "skill": "tdd"}]},
    })
    got = s.run([kit("check-evals"), str(root)], want=1)
    assert "rv/reference/expectations.json case essay: field facts: a review case has none" in (
        got.out + got.err
    ), got


def role_shape(s: Scratch) -> None:
    """Role setup and declared_includes validation from tests/qa-shape.sh."""
    root = s.root / "evals"
    shutil.copytree(ROOT / "evals" / "fixtures" / "python-app", root / "fixtures" / "py")
    (root / "fixtures" / "fx2" / "tests").mkdir(parents=True)
    (root / "fixtures" / "fx2" / "README.md").write_text("head\n")
    (root / "fixtures" / "fx2" / "tests" / "test_y.py").write_text("def test_y(): pass\n")
    skill = root / "fixtures" / "fxs" / ".agents" / "skills" / "repo-only" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text(
        "---\nname: repo-only\ndescription: a fixture skill\n---\n\nDrive the app this way.\n",
    )
    cases: list[CaseData] = [
        {"id": "order", "role": "implementer", "fixture": "py", "task": "Do it.",
         "branch": "impl-t1", "origin": True, "fake_gh": True},
        {"id": "setup", "role": "implementer", "fixture": "fx", "task": "Do it.",
         "branch": "work", "head": {"fixture": "fx2", "branch": "hb", "message": "head msg"}},
        {"id": "incl", "role": "implementer", "fixture": "fx", "task": "Do it."},
        {"id": "repoload", "role": "implementer", "fixture": "fxs", "task": "Do it."},
    ]
    expectations: Expectations = {
        "order": {"facts": [
            {"fact": "skill_read_before", "skill": "tdd", "before": "test_write"},
            {"fact": "skill_read_before", "skill": "commit", "before": "test_write"},
            {"fact": "skill_read_before", "skill": "commit", "before": "git_commit"},
            {"fact": "skill_read_before", "skill": "tdd", "before": "git_push"},
            {"fact": "skill_read_before", "skill": "github-pr", "before": "gh_call"},
        ]},
        "setup": {"facts": [{"fact": "skill_not_read", "skill": "pull"}]},
        "incl": {"facts": [
            {"fact": "declared_includes", "field": "blocking", "items": [{"test": "t.py::a"}]},
        ]},
        "repoload": {"facts": [{"fact": "skill_read", "skill": "repo-only"}]},
    }
    write_suite(root, "rt", "role-transcript", cases, expectations)
    s.run([kit("check-evals"), str(root)])
    variants: list[tuple[int, str | None, CaseData, str]] = [
        (0, None, {"branch": "a..b"}, "case order: field branch: must be a branch name"),
        (0, None, {"origin": False},
         "case order: field origin: must be true (leave it out for false)"),
        (0, None, {"fake_gh": "yes"}, "case order: field fake_gh: must be true"),
        (1, None, {"head": {"fixture": "fx2", "branch": "hb"}},
         "case setup: field head.message: missing"),
        (1, None, {"head": {"fixture": "nope", "branch": "hb", "message": "m"}},
         "case setup: field head.fixture: no fixture dir"),
        (1, None, {"head": {"fixture": "fx2", "branch": "work", "message": "m"}},
         "case setup: field head.branch: must be a new branch name"),
        (1, None, {"head": "fx2"}, "case setup: field head: must be an object"),
        (0, "origin", {},
         "case order fact #4: field before: git_push needs the case's origin: true"),
        (0, "fake_gh", {},
         "case order fact #5: field before: gh_call needs the case's fake_gh: true"),
        (0, None, {"fixture": "fx"},
         "case order fact #1: field before: test_write needs fixture fx to declare its tests"),
        (0, None, {"head": {"fixture": "fx2", "branch": "hb", "message": "m"}},
         "case order fact #1: field before: test_write needs fixture fx2 to declare its tests"),
        (3, None, {"head": {"fixture": "fx2", "branch": "hb", "message": "m"}},
         "case repoload fact #1: field skill: no .agents/skills/repo-only/SKILL.md "
         "in the kit or in fixture fx2"),
    ]
    for index, removed, updates, expected in variants:
        c = copy.deepcopy(cases)
        if removed:
            del c[index][removed]
        c[index].update(updates)
        write_suite(root, "rt", "role-transcript", c, expectations)
        got = s.run([kit("check-evals"), str(root)], want=1)
        assert expected in got.out + got.err, got
    variants_facts: list[tuple[str, str, object, str]] = [
        ("order", "before", "lunch", "case order fact #1: field before: must be one of"),
        ("incl", "items", [{"test": 1}],
         "case incl fact #1: field items: must be a non-empty list of "
         "non-empty objects of string values"),
        ("incl", "items", [], "case incl fact #1: field items: must be a non-empty list"),
        ("incl", "field", None, "case incl fact #1: field field: missing"),
    ]
    for cid, key, value, expected in variants_facts:
        e = copy.deepcopy(expectations)
        if value is None:
            del e[cid]["facts"][0][key]
        else:
            e[cid]["facts"][0][key] = value
        write_suite(root, "rt", "role-transcript", cases, e)
        got = s.run([kit("check-evals"), str(root)], want=1)
        assert expected in got.out + got.err, got


def field_shape(s: Scratch) -> None:
    """field_lines, branch_paths, tool_called and ran malformed-input oracles."""
    root = s.root / "evals"
    cases: list[CaseData] = [
        {"id": i, "role": "implementer", "fixture": "fx", "task": "Do it."}
        for i in ("fnone", "fexact", "fweb", "rpass")
    ]
    expectations: Expectations = {
        "fnone": {"facts": [
            {"fact": "field_lines", "field": "Check", "none": True},
            {"fact": "field_lines", "field": "Check", "every": {"class": ["exact"]}},
            {"fact": "field_lines", "field": "Blocked"},
            {"fact": "branch_paths", "untouched": ["scripts/", "justfile"], "touched": ["src/"]},
        ]},
        "fexact": {"facts": [
            {"fact": "field_lines", "field": "Check", "includes": [
                {"class": "exact", "path": "scripts/check-exec"},
            ], "every": {"class": ["exact"]}},
        ]},
        "fweb": {"facts": [
            {"fact": "tool_called", "tools": ["web_a", "web_b"]},
            {"fact": "field_lines", "field": "Prior art"},
        ]},
        "rpass": {"facts": [
            {"fact": "ran", "program": "runme", "args": ["lane", "show", "{head}"]},
        ]},
    }
    write_suite(root, "fl", "role-transcript", cases, expectations)
    s.run([kit("check-evals"), str(root)])
    variants: list[tuple[str, int, str, object, str]] = [
        ("fnone", 0, "field", None, "case fnone fact #1: field field: missing"),
        ("fnone", 0, "lines", 1, "case fnone fact #1: field lines: unknown field for field_lines"),
        ("fnone", 0, "field", "Checks", "case fnone fact #1: field field: must be a field name"),
        ("fnone", 0, "none", "yes", "case fnone fact #1: field none: only true"),
        ("fexact", 0, "includes", [{"klass": "exact"}],
         "case fexact fact #1: field includes: must be a non-empty list of "
         "non-empty objects of string values, keys from"),
        ("fexact", 0, "every", {"class": "exact"},
         "case fexact fact #1: field every: must be a non-empty object of string lists"),
        ("fnone", 3, "untouched", None, "case fnone fact #4: field untouched: missing"),
        ("rpass", 0, "program", None, "case rpass fact #1: field program: missing"),
        ("rpass", 0, "program", "a/b", "case rpass fact #1: field program: must be a command name"),
        ("rpass", 0, "args", "lane show",
         "case rpass fact #1: field args: must be a list of strings"),
        ("rpass", 0, "exit", 0, "case rpass fact #1: field exit: unknown field for ran"),
        ("fweb", 0, "tools", [],
         "case fweb fact #1: field tools: must be a non-empty list of tool names"),
        ("fweb", 0, "tools", ["web a"],
         "case fweb fact #1: field tools: must be a non-empty list of tool names"),
        ("fweb", 0, "tools", None, "case fweb fact #1: field tools: missing"),
        ("fweb", 1, "field", "Prior  art", "case fweb fact #2: field field: must be a field name"),
        ("fnone", 3, "untouched", "scripts/",
         "case fnone fact #4: field untouched: must be a non-empty list of relative paths"),
        ("fnone", 3, "touched", ["../x"],
         "case fnone fact #4: field touched: must be a non-empty list of relative paths"),
        ("fnone", 3, "paths", [],
         "case fnone fact #4: field paths: unknown field for branch_paths"),
    ]
    for cid, index, key, value, expected in variants:
        e = copy.deepcopy(expectations)
        if value is None:
            if cid == "fnone" and index == 3:
                e[cid]["facts"][index] = {"fact": "branch_paths"}
            else:
                del e[cid]["facts"][index][key]
        else:
            e[cid]["facts"][index][key] = value
        write_suite(root, "fl", "role-transcript", cases, e)
        got = s.run([kit("check-evals"), str(root)], want=1)
        assert expected in got.out + got.err, got


if __name__ == "__main__":
    main(trigger_shape, before_shape, review_shape, role_shape, field_shape)
