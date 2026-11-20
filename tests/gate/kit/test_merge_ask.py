"""The merge ask's rules, in-process at their interface, `check` of scripts/merge_ask.py (its
module docstring; tickets #1147 and #1149, seams agreed on them before any test): a Snapshot in,
the gaps out. Each test is the command scenario of the same name it replaced in
tests/gate/kit/lane_merge_ask.py (parity: tests/parity/lane-merge-ask-*/). LANE is that file's
lane as merge-ask reads it: PR #7 at H, qc's status commit after the judged head J, its clear
review verdict on J, demo's status file; what the tracker skill prints for a branch is the
Snapshot's parent, as its github-issues and linear scripts print it; the head proof
(octo-feather-lane's head_proof) is the Snapshot's answer to check's Need. The command's wiring
(snapshot over the real tracker scripts, comments, status files and qc reports, the gaps and
the passing ask printed): lane_merge_ask.py merge_ask_passes, no_criterion_lane.
"""

from dataclasses import replace

from merge_ask import Ask, Comment, NoParent, ParentLine, Proof, ProofAsk, Snapshot, check

J = "abcdef1" + "0" * 33  # the judged head: the lane's code commit
H = "abcdef2" + "1" * 33  # PR #7's head: qc's status commit after J
OTHER = "ffee" * 10
URL = "https://github.com/o/r/pull/7#issuecomment-1001"
STATUS = "docs/specs/demo.status.json"
PROOF = f"{J[:12]} to {H[:12]}: qc status commits {H[:12]} change only {STATUS}"
HDR = "| criterion | qc verdict | judged | evidence |\n|---|---|---|---|"
GH6 = ParentLine("6", "Closes #6")
ENG = ParentLine("ENG-123", "Tracks ENG-123")
REMOVE = (
    "remove it (the supervisor's close moves each ticket to done with the tracker skill's "
    "issue-done)"
)


def verdict(head: str = J, says: str = "Verdict: clear", checks: str = "Checks: none") -> str:
    """The review verdict comment `octo-feather-lane verdict` posts for HEAD."""
    return (
        f"<!-- octo-feather-review-verdict -->\n## Code review verdict\n\nHead: {head}\n"
        f"PR head: {H}\n{says}\n{checks}\n\n### Findings\n\nFindings: none blocking.\n"
        "Checks: none\nVerdict: clear\n"
    )


def body(**o: str) -> str:
    """The lane PR's body, its section complete, a line overridden by each of O: parent head
    judged rows review built failed (lane_merge_ask.py Lane.body)."""
    ev = "qc report a1b2.json, cmd ok"
    rows = (
        f"| demo#acceptance-a | pass | judged {J[:7]} | {ev} |\n"
        f"| acceptance-b | pass | judged {J[:7]} | {ev} |"
    )
    return (
        f"{o.get('parent', 'Closes #6')}\n\n## Summary\n\nLane work.\n\n## Merge ask\n\n"
        f"Head: {o.get('head', H[:12])}\n"
        f"Checks: check, ci/x pass on {H[:12]}\n"
        f"Judged: {o.get('judged', PROOF)}\n"
        f"{HDR}\n{o.get('rows', rows)}\n"
        f"Review verdict: {o.get('review', URL)}\n"
        f"Built: {o.get('built', 'demo#acceptance-a acceptance-b')}\n"
        f"{o.get('failed', 'Failed: none')}\n\n## Notes\n\nafter the section\n"
    )


def demo(a: str = "built", pr: int | None = 7) -> dict[str, dict[str, object]]:
    """demo's status file: acceptance-a and -b at A with PR, -c planned, -d built by PR #3."""
    return {
        "acceptance-a": {"status": a, "pr": pr},
        "acceptance-b": {"status": a, "pr": pr},
        "acceptance-c": {"status": "planned", "pr": None},
        "acceptance-d": {"status": "built", "pr": 3},
    }


LANE = Snapshot(
    body(),
    "gh6",
    GH6,
    pr=7,
    head=H,
    commits=[(H, f"qc: built acceptance-a acceptance-b (judged {J[:12]})"), (J, "feat: x")],
    specs={"demo": demo()},
    named=True,
    comments=[Comment(URL, verdict())],
    proofs={ProofAsk(J, H): Proof(PROOF, ())},
)


def ask(s: Snapshot) -> Ask:
    a = check(s)
    assert isinstance(a, Ask), a
    return a


def gaps(parent: ParentLine | NoParent, line: str, branch: str = "gh6") -> list[str]:
    return ask(replace(LANE, body=body(parent=line), branch=branch, parent=parent)).gaps


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
