"""Role-skill coverage validation from tests/qa.sh, through check-evals only.

Copies the kit's existing eval input data. No role execution, fixture setup,
tracker request or synthetic external response is involved.
"""

import json
import shutil
from typing import cast

from testkit import ROOT, Scratch, kit, main

CaseData = dict[str, object]
Expectations = dict[str, dict[str, object]]


def coverage_gap(s: Scratch) -> None:
    """One dropped held-out pull near miss names its exact missing quadrant."""
    s.run([kit("check-evals")])
    root = s.root / "kit-evals"
    shutil.copytree(ROOT / "evals", root)
    d = root / "skill-triggers"
    cases = cast("list[CaseData]", json.loads((d / "cases.json").read_text()))
    expectations = cast(
        "Expectations",
        json.loads((d / "reference" / "expectations.json").read_text()),
    )
    gone = {
        c["id"]
        for c in cases
        if c["role"] == "implementer"
        and not c["should_trigger"]
        and c["split"] == "held-out"
        and expectations[str(c["id"])]["facts"] == [{"fact": "skill_not_read", "skill": "pull"}]
    }
    assert gone, "no held-out near miss for implementer pull in the kit suite"
    (d / "cases.json").write_text(json.dumps([c for c in cases if c["id"] not in gone]))
    (d / "reference" / "expectations.json").write_text(
        json.dumps({k: v for k, v in expectations.items() if k not in gone})
    )
    got = s.run([kit("check-evals"), str(root)], want=1)
    expected = (
        "skill-triggers: role implementer skill pull: "
        "no case for should_trigger false split held-out"
    )
    assert expected in got.out + got.err, got


def tracker_coverage(s: Scratch) -> None:
    """Resolve tracker from each fixture; refuse an unknown tracker explicitly."""
    root = s.root / "trk-evals"
    shutil.copytree(ROOT / "evals", root)
    d = root / "skill-triggers"
    cases = cast("list[CaseData]", json.loads((d / "cases.json").read_text()))
    expectations = cast(
        "Expectations",
        json.loads((d / "reference" / "expectations.json").read_text()),
    )
    gone = {
        c["id"]
        for c in cases
        if c["role"] == "supervisor"
        and c["should_trigger"]
        and c["split"] == "train"
        and expectations[str(c["id"])]["facts"]
        == [
            {"fact": "skill_read", "skill": "github-issues"},
        ]
    }
    assert gone, "no train should case for supervisor github-issues in the kit suite"
    (d / "cases.json").write_text(json.dumps([c for c in cases if c["id"] not in gone]))
    (d / "reference" / "expectations.json").write_text(
        json.dumps({k: v for k, v in expectations.items() if k not in gone})
    )
    got = s.run([kit("check-evals"), str(root)], want=1)
    out = got.out + got.err
    expected = (
        "skill-triggers: role supervisor skill github-issues: "
        "no case for should_trigger true split train;"
    )
    assert expected in out, got
    assert sum(": role " in line and " skill " in line for line in out.splitlines()) == 1, got
    linear = s.root / "lin-evals"
    shutil.copytree(ROOT / "evals", linear)
    config = linear / "fixtures" / "lane-mini" / ".octo-feather.toml"
    config.write_text('tracker = "linear"\n')
    got = s.run([kit("check-evals"), str(linear)], want=1)
    out = got.out + got.err
    for role in ("director", "implementer", "supervisor"):
        expected = (
            f"skill-triggers: role {role} skill linear: no case for should_trigger true split train"
        )
        assert expected in out, got
    assert "skill {tracker}" not in out, got
    assert "skill github-issues:" not in out, got
    config.write_text('tracker = "jira"\n')
    got = s.run([kit("check-evals"), str(linear)], want=1)
    expected = (
        "fixtures/lane-mini/.octo-feather.toml: field tracker: 'jira' has no kit tracker skill"
    )
    assert expected in got.out + got.err, got


if __name__ == "__main__":
    main(coverage_gap, tracker_coverage)
