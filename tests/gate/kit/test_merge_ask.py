"""The merge ask's rules, in-process at their interface, `check` of scripts/merge_ask.py (its
module docstring; tickets #1147, #1148, seam agreed on each before any test): a Snapshot in, the
gaps out. Each test is the command scenario of the same name it replaced in
tests/gate/kit/lane_merge_ask.py (parity: tests/parity/lane-merge-ask-*/; test_merge_ask_checks:
single_gaps' Checks part); what the tracker skill prints for a branch is the Snapshot's parent,
as its github-issues and linear scripts print it; GitHub's answers keep the shapes
lane_merge_ask.py's API comment cites. The command's wiring (snapshot over the real tracker
scripts and gh, the gaps printed): lane_merge_ask.py merge_ask_passes, no_criterion_lane,
single_gaps, no_ci.
"""

from merge_ask import (
    Ask,
    Checks,
    NoParent,
    NoWorkflow,
    ParentLine,
    Policy,
    Reported,
    Snapshot,
    Unread,
    Workflows,
    check,
)

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


# --- the checks (spec #lanes-one-head; octo-feather-lane --help, merge-ask Checks line) ---

H = HEAD[:12]
THIS = "gh api repos/<this repo>"
TREE = f"{THIS}/git/trees/{H}"
ERR502 = "gh: Server Error (HTTP 502)"
UNPROTECTED: dict[str, object] = {
    "name": "main",
    "protected": False,
    "protection": {
        "enabled": False,
        "required_status_checks": {"enforcement_level": "off", "contexts": [], "checks": []},
    },
}
NO_RULE: tuple[object, str] = ([], "")


def asked(at: Reported | Workflows | NoWorkflow | Unread, repo: str | None = None) -> Ask:
    return check(Snapshot(body("Closes #6"), "gh6", GH6, Checks(HEAD, repo, at)))


def rollup(i: int, **kv: object) -> Reported:
    """CHECK_OK with its check I updated with KV."""
    r = [dict(c) for c in CHECK_OK]
    r[i].update(kv)
    return Reported(r, None)


def policy(
    branch: tuple[object, str] = (UNPROTECTED, ""), rules: tuple[object, str] | None = NO_RULE
) -> NoWorkflow:
    """No workflow file at the head, the base main's policy: gh api branches/main's and
    rules/branches/main's answers, each (its JSON, '') or (None, gh's error); RULES None unread."""
    return NoWorkflow(Policy("main", branch, rules))


def but(why: str) -> list[str]:
    return [f"Checks: none reported on head {H}, no workflow file there ({TREE}), but {why}"]


def test_merge_ask_checks() -> None:
    """Every check on the head passes (spec #lanes-one-head): a failing, pending or erroring check
    run or status context fails naming it; none reported with workflow files at the head fails
    naming them."""
    fix = "fix them (a red check is never pre-existing)"
    wait = "wait for them to finish, then rerun"
    cases: list[tuple[Reported | Workflows, list[str]]] = [
        (Reported(CHECK_OK, None), []),
        (rollup(0, conclusion="FAILURE"), [f"Checks: failing on head {H}: check failure; {fix}"]),
        (
            rollup(0, status="IN_PROGRESS", conclusion=""),
            [f"Checks: pending on head {H}: check in_progress; {wait}"],
        ),
        (rollup(1, state="PENDING"), [f"Checks: pending on head {H}: ci/x pending; {wait}"]),
        (rollup(1, state="ERROR"), [f"Checks: failing on head {H}: ci/x error; {fix}"]),
        (
            Workflows([".github/workflows/check.yml"]),
            [
                (
                    f"Checks: none reported on head {H}, its workflows "
                    ".github/workflows/check.yml; push the head and wait for CI"
                )
            ],
        ),
    ]
    for at, want in cases:
        ask = asked(at)
        assert (ask.checks, ask.no_ci) == (want, ""), (at, ask)


def test_merge_ask_no_ci() -> None:
    """No check reported and no workflow file at the head (rule: --help, merge-ask Checks line):
    the base's required-check policy decides: no check required passes, naming both facts and
    their sources; a check required by branch protection or a ruleset fails naming it."""
    rules = f"{THIS}/rules/branches/main"
    no_ci = (
        f"no CI: no workflow file under .github/workflows at head {H} ({TREE}); base main "
        f"requires no check ({THIS}/branches/main: no required status check; {rules}: "
    )
    ask = asked(policy())
    assert (ask.checks, ask.no_ci) == (
        [],
        no_ci + "no required_status_checks rule), so required checks are none",
    ), ask
    plan = (  # GitHub's answer on a plan without rulesets, as gh prints it
        "gh: Upgrade to GitHub Pro or make this repository public to enable this feature. "
        "(HTTP 403)"
    )
    ask = asked(policy(rules=(None, plan)))
    assert (ask.checks, ask.no_ci) == (
        [],
        no_ci + "rulesets unavailable on this plan, none in force), so required checks are none",
    ), ask
    req = {
        "enforcement_level": "everyone",
        "contexts": ["ci/legacy"],
        "checks": [{"context": "build", "app_id": 1}],
    }
    prot = {"protected": True, "protection": {"enabled": True, "required_status_checks": req}}
    required = "push the head and wait for them"
    ask = asked(policy((prot, "")))
    assert (ask.checks, ask.no_ci) == (
        but(
            f"base main requires checks build, ci/legacy ({THIS}/branches/main, "
            f"repos/<this repo>/rules/branches/main): {required}"
        ),
        "",
    ), ask
    vercel = {"required_status_checks": [{"context": "vercel"}]}
    ruleset = [{"type": "deletion"}, {"type": "required_status_checks", "parameters": vercel}]
    ask = asked(policy(rules=(ruleset, "")))
    assert ask.checks == but(
        f"base main requires checks vercel ({THIS}/branches/main, "
        f"repos/<this repo>/rules/branches/main): {required}"
    ), ask
    ask = asked(policy(rules=(ruleset, "")), "o/r")  # a named repo is named in each source
    tree = f"gh api repos/o/r/git/trees/{H}"
    assert ask.checks == [
        (
            f"Checks: none reported on head {H}, no workflow file there ({tree}), but base main "
            "requires checks vercel (gh api repos/o/r/branches/main, "
            f"repos/o/r/rules/branches/main): {required}"
        )
    ], ask


def test_merge_ask_no_ci_unread() -> None:
    """A base policy or a head's tree gh cannot read fails closed, naming the read: one Checks
    item, never a pass."""
    fix = "fix gh auth status or read access, then rerun"
    unread = "the required checks of base main could not be read"
    cases: list[tuple[Reported | Workflows | NoWorkflow | Unread, list[str]]] = [
        (policy((None, ERR502), None), but(f"{unread} ({THIS}/branches/main: {ERR502}): {fix}")),
        (
            policy(({"protected": True}, ""), None),
            but(f"{unread} ({THIS}/branches/main: no protection.required_status_checks): {fix}"),
        ),
        (
            policy(rules=(None, ERR502)),
            but(
                "the rulesets of base main could not be read "
                f"({THIS}/rules/branches/main: {ERR502}): {fix}"
            ),
        ),
        (
            NoWorkflow(Unread("gh not on PATH: install the GitHub CLI and log in")),
            but("gh not on PATH: install the GitHub CLI and log in"),
        ),
        (
            Unread(f"gh api repos/{{owner}}/{{repo}}/git/trees/{HEAD} failed ({ERR502})"),
            [
                (
                    f"Checks: none reported on head {H}, and the no-CI fact could not be read "
                    f"(gh api repos/{{owner}}/{{repo}}/git/trees/{HEAD} failed ({ERR502}))"
                )
            ],
        ),
    ]
    for at, want in cases:
        ask = asked(at)
        assert (ask.checks, ask.no_ci) == (want, ""), (at, ask)
