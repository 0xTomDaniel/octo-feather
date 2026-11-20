"""The merge ask's rules, in-process at their interface, `check` of scripts/merge_ask.py (its
module docstring; ticket #1147, seam agreed on it before any test): a Snapshot in, the gaps out.
Each test is the command scenario of the same name it replaced in tests/gate/kit/lane_merge_ask.py
(parity: tests/parity/lane-merge-ask-parent-line/); what the tracker skill prints for a branch is
the Snapshot's parent, as its github-issues and linear scripts print it. The command's wiring
(snapshot over the real tracker scripts, the gaps printed): lane_merge_ask.py merge_ask_passes,
no_criterion_lane.
"""

from merge_ask import Checks, NoParent, ParentLine, Reported, Snapshot, check

HEAD = "0123456789ab" + "0" * 28
# The head's checks as the PR's rollup reports them, all passing (gh pr view statusCheckRollup)
CHECK_OK: list[dict[str, object]] = [
    {"__typename": "CheckRun", "name": "check", "status": "COMPLETED", "conclusion": "SUCCESS"},
    {"__typename": "StatusContext", "context": "ci/x", "state": "SUCCESS"},
]
PASSING = Checks(HEAD, None, Reported(CHECK_OK, None))

GH6 = ParentLine("6", "Closes #6")
ENG = ParentLine("ENG-123", "Tracks ENG-123")
REMOVE = (
    "remove it (the supervisor's close moves each ticket to done with the tracker skill's "
    "issue-done)"
)


def body(parent: str) -> str:
    """A lane PR body: PARENT, then a summary and a merge ask section."""
    return (
        f"{parent}\n\n## Summary\n\nLane work.\n\n## Merge ask\n\nHead: 0123456789ab\n"
        "Checks: check, ci/x pass on 0123456789ab\nBuilt: demo#acceptance-a\nFailed: none\n"
        "\n## Notes\n\nafter the section\n"
    )


def gaps(parent: ParentLine | NoParent, line: str, branch: str = "gh6") -> list[str]:
    return check(Snapshot(body(line), branch, parent, PASSING)).gaps


def missing(p: ParentLine) -> str:
    return (
        f"parent line: missing; add the line `{p.line}` (the tracker skill's pr-line {p.key}) "
        "to the PR body"
    )


def closes(line: str, n: int, p: ParentLine) -> str:
    return (
        f"parent line: `{line}` closes GitHub issue #{n}, not the lane's parent line "
        f"`{p.line}`; {REMOVE}"
    )


def test_merge_ask_parent_line() -> None:
    """The parent line (spec #gates-pr-line): the tracker skill's pr-line for the key the PR
    branch names, and no other line closes an issue: only the parent's own closing link is
    exempt, never the rest of its line; an issue URL closes too. A Linear lane (spec
    #acceptance-pr-tracks): Tracks ENG-123 for branch eng-123, no Closes line. A branch the
    tracker skill names no parent for fails naming its refusal."""
    url = "https://github.com/o/r/issues/9"
    cases: list[tuple[ParentLine, str, list[str]]] = [
        (GH6, "Closes #6", []),
        (GH6, "", [missing(GH6)]),
        (GH6, "Closes #60", [missing(GH6), closes("Closes #60", 60, GH6)]),
        (GH6, "Closes #6\nAlso fixes #9", [closes("Also fixes #9", 9, GH6)]),
        (GH6, "Closes #6, fixes #9", [closes("Closes #6, fixes #9", 9, GH6)]),
        (GH6, "Closes #6 closes o/r#6", [closes("Closes #6 closes o/r#6", 6, GH6)]),
        (GH6, f"Closes #6\nResolves {url}", [closes(f"Resolves {url}", 9, GH6)]),
        (ENG, "Tracks ENG-123", []),
        (ENG, "Closes #6", [missing(ENG), closes("Closes #6", 6, ENG)]),
        (ENG, "Tracks ENG-123\nCloses #6", [closes("Closes #6", 6, ENG)]),
        (ENG, "Tracks ENG-123; Closes #6", [closes("Tracks ENG-123; Closes #6", 6, ENG)]),
        (ENG, "Tracks ENG-1234", [missing(ENG)]),
    ]
    for p, line, want in cases:
        got = gaps(p, line, "gh6" if p is GH6 else "eng-123")
        assert got == want, (p, line, got)
    why = (
        "tracker script github-issues/key-from-branch main failed (key-from-branch: branch main "
        "names no GitHub issue (no gh<N> part)): fix the cause it names, then rerun"
    )
    refused = (
        f"parent line: cannot name it for branch 'main' ({why}); push the lane from its lane "
        "branch (docs/adr/0011)"
    )
    assert gaps(NoParent(why), "Closes #6", "main") == [refused]
