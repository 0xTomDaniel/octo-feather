"""QA selection and reference refusals without launching any case.

Partial qa.sh, qa-kit-ref.sh and qa-baseline.sh conversion. Valid input suites
are fixture data; unknown selections/references stop before sandbox/model work.
"""

import json

from testkit import Scratch, kit, main


def selection_refusals(s: Scratch) -> None:
    """Unknown suite/case and zero sample retain the original usage exits."""
    root = s.root / "evals"
    d = root / "trig"
    (d / "reference").mkdir(parents=True)
    (root / "fixtures" / "fx").mkdir(parents=True)
    (root / "fixtures" / "fx" / "README.md").write_text("fixture\n")
    (d / "suite.json").write_text(json.dumps({
        "suite": "trig", "kind": "skill-trigger", "description": "selection inputs",
        "max_tool_calls": 5, "timeout_s": 60,
    }))
    (d / "cases.json").write_text(json.dumps([{
        "id": "reads", "role": "implementer", "fixture": "fx", "task": "Build it.",
        "should_trigger": True, "split": "train",
    }]))
    (d / "reference" / "expectations.json").write_text(json.dumps({
        "reads": {"facts": [{"fact": "skill_read", "skill": "tdd"}]},
    }))
    q = [kit("octo-feather-qa"), "--evals", str(root)]
    for args in (("--suite", "nope"), ("--case", "nope"), ("--sample", "0")):
        got = s.run([*q, *args], want=64)
        assert "qa: run " not in got.out + got.err, got
    for flag, name in (("--kit-ref", "kit-ref"), ("--baseline", "baseline")):
        got = s.run([*q, "--case", "reads", flag, "no-such-ref"], want=64)
        assert f"{name} no-such-ref: no such commit" in got.out + got.err, got
        assert "qa: run " not in got.out + got.err, got
    s.run([*q, "--baseline"], want=64)


if __name__ == "__main__":
    main(selection_refusals)
