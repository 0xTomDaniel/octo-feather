"""QA selection and reference refusals without launching any case.

Partial qa.sh, qa-kit-ref.sh and qa-baseline.sh conversion. Valid input suites
are fixture data; unknown selections/references stop before sandbox/model work.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from testkit import Scratch, kit, kit_repo, main

if TYPE_CHECKING:
    from pathlib import Path


def selection_inputs(s: Scratch) -> Path:
    """The original reads case as fixture input, never an execution stand-in."""
    root = s.root / "evals"
    d = root / "trig"
    (d / "reference").mkdir(parents=True)
    (root / "fixtures" / "fx").mkdir(parents=True)
    (root / "fixtures" / "fx" / "README.md").write_text("fixture\n")
    (d / "suite.json").write_text(
        json.dumps(
            {
                "suite": "trig",
                "kind": "skill-trigger",
                "description": "selection inputs",
                "max_tool_calls": 5,
                "timeout_s": 60,
            }
        )
    )
    (d / "cases.json").write_text(
        json.dumps(
            [
                {
                    "id": "reads",
                    "role": "implementer",
                    "fixture": "fx",
                    "task": "Build it.",
                    "should_trigger": True,
                    "split": "train",
                }
            ]
        )
    )
    (d / "reference" / "expectations.json").write_text(
        json.dumps(
            {
                "reads": {"facts": [{"fact": "skill_read", "skill": "tdd"}]},
            }
        )
    )
    return root


def selection_refusals(s: Scratch) -> None:
    """Unknown suite/case and zero sample retain the original usage exits."""
    root = selection_inputs(s)
    q = [kit("octo-feather-qa"), "--evals", str(root)]
    for args in (("--suite", "nope"), ("--case", "nope"), ("--sample", "0")):
        got = s.run([*q, *args], want=64)
        assert "qa: run " not in got.out + got.err, got
    for flag, name in (("--kit-ref", "kit-ref"), ("--baseline", "baseline")):
        got = s.run([*q, "--case", "reads", flag, "no-such-ref"], want=64)
        assert f"{name} no-such-ref: no such commit" in got.out + got.err, got
        assert "qa: run " not in got.out + got.err, got
    s.run([*q, "--baseline"], want=64)


def missing_role(s: Scratch) -> None:
    """An archived kit missing its role fails before model launch, with real artifacts."""
    root = selection_inputs(s)
    # This is a pre-agent refusal. An accidental launch must not reach either
    # the testkit's default Pi stand-in or a real model process.
    s.without("pi")
    k = kit_repo(s)
    base = s.git(k, "rev-parse", "HEAD")
    role = "agents/implementer.md"
    (k / role).unlink()
    s.git(k, "-c", "core.hooksPath=/dev/null", "commit", "-qam", "kit without role")
    c0 = s.git(k, "rev-parse", "HEAD")
    # The running head must retain its role so the input checker accepts it;
    # only the explicitly selected historical kit lacks the role.
    s.git(k, "restore", "--source", base, "--", role)
    s.git(k, "add", role)
    s.git(k, "-c", "core.hooksPath=/dev/null", "commit", "-qm", "restore head role")
    out = s.root / "out"
    s.env["OCTO_FEATHER_QA_DIR"] = str(out)
    got = s.run(
        [
            str(k / "scripts" / "octo-feather-qa"),
            "--evals",
            str(root),
            "--case",
            "reads",
            "--kit-ref",
            c0,
        ],
        want=1,
    )
    assert any(
        line.startswith("FAIL trig/reads: ")
        and f"kit {c0}: no agents/implementer.md at that commit" in line
        for line in got.out.splitlines()
    ), got
    # These are actual public CLI outputs, not hand-written result fixtures.
    runs = [d for d in out.iterdir() if d.is_dir()]
    assert len(runs) == 1, runs
    case = runs[0] / "trig" / "reads"
    result = json.loads((case / "result.json").read_text())
    given = json.loads((case / "input.json").read_text())
    summary = json.loads((runs[0] / "summary.json").read_text())
    assert (result["verdict"], result["kit_sha"], given["kit_sha"]) == ("FAIL", c0, c0)
    assert (summary["passed"], summary["total"], summary["kit_sha"]) == (0, 1, c0)
    assert not (case / "transcript.jsonl").exists(), "case executed without its selected role"
    assert not list((s.root / "tmp").glob("qa-kit-*")), "archived kit outlived refusal"


if __name__ == "__main__":
    main(selection_refusals, missing_role)
