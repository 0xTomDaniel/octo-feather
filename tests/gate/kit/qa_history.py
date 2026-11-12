"""History fixture validation via check-evals, partial tests/qa-history.sh coverage.

No role is launched. The whole-tree export and role-visible commit/tree oracles
remain with the legacy test until strict replay and paired parity are available.
"""

import copy
import json

from testkit import ROOT, Scratch, kit, main


def history_shape(s: Scratch) -> None:
    """Unknown repository, absent commit, short SHA and missing commit are refused."""
    at = s.git(ROOT, "rev-parse", "711392a")
    target = s.home / "src" / "tgt"
    target.mkdir(parents=True)
    s.git(target, "init", "-q", "-b", "main")
    (target / "deep" / "er").mkdir(parents=True)
    (target / "deep" / "er" / "leaf.txt").write_text("t\n")
    s.git(target, "add", "-A")
    s.git(target, "-c", "core.hooksPath=/dev/null", "commit", "-qm", "tgt")
    tgt = s.git(target, "rev-parse", "HEAD")
    root = s.root / "evals"
    d = root / "hi"
    (d / "reference").mkdir(parents=True)
    (root / "fixtures").mkdir()
    (d / "suite.json").write_text(
        json.dumps(
            {
                "suite": "hi",
                "kind": "role-transcript",
                "description": "history inputs",
                "max_tool_calls": 10,
                "timeout_s": 120,
            }
        )
    )
    cases = [
        {
            "id": "kit",
            "role": "implementer",
            "fixture": {"repo": "kit", "commit": at},
            "task": "Look.",
        },
        {
            "id": "clone",
            "role": "implementer",
            "fixture": {"repo": "tgt", "commit": tgt},
            "task": "Look.",
        },
    ]
    (d / "reference" / "expectations.json").write_text(
        json.dumps(
            {i: {"facts": [{"fact": "skill_not_read", "skill": "pull"}]} for i in ("kit", "clone")}
        )
    )
    (d / "cases.json").write_text(json.dumps(cases))
    s.run([kit("check-evals"), str(root)])
    variants: list[tuple[int, dict[str, str], str]] = [
        (
            0,
            {"repo": "nosuch", "commit": at},
            (
                "hi/cases.json case kit: field fixture.repo: "
                "'nosuch' is not kit or a git clone at ~/src/<name>"
            ),
        ),
        (
            0,
            {"repo": "kit", "commit": "0" * 40},
            "hi/cases.json case kit: field fixture.commit: no commit " + "0" * 40 + " in",
        ),
        (
            1,
            {"repo": "tgt", "commit": tgt[:9]},
            "hi/cases.json case clone: field fixture.commit: must be a full 40 character sha",
        ),
        (1, {"repo": "tgt"}, "hi/cases.json case clone: field fixture.commit: missing"),
    ]
    for index, fixture, expected in variants:
        c = copy.deepcopy(cases)
        c[index]["fixture"] = fixture
        (d / "cases.json").write_text(json.dumps(c))
        got = s.run([kit("check-evals"), str(root)], want=1)
        assert expected in got.out + got.err, got


if __name__ == "__main__":
    main(history_shape)
