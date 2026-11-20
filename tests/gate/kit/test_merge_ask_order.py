"""The merge-order rule (issue-lifecycle spec #gates-merge-order), in-process at its interface,
`check` of scripts/merge_ask.py (ticket #1152, seam `merge_ask.check` posted on it): a Snapshot
whose Order holds the other open PRs as the reads gave them, each pin's lines as octo-feather-qa
--verdict prints them (its --help, Verdict), the merge-order lines out. The command's wiring (the
reads over real git, gh pr list and octo-feather-qa): lane_merge_order.py."""

from merge_ask import Ask, Checks, Order, ParentLine, Pin, Reported, Sibling, Snapshot, check

RUN = "20260101T000000Z-abc123/s1/c1"
HEAD = (
    "Merge order (issue-lifecycle #gates-merge-order; shown only: this merge ask passes or "
    "fails the same without it):"
)


def qa(word: str, fresh: str) -> str:
    """An octo-feather-qa --verdict line for RUN with freshness FRESH."""
    run = "run 20260101T000000Z-abc123, kit 0123456789ab, runs 2/2 passed"
    return f"{word} s1/c1: stored PASS, {run}; {fresh}"


FRESH = qa("PASS", "fresh at HEAD aaaaaaaaaaaa")
OLD = qa("INSUFFICIENT", "stale at HEAD aaaaaaaaaaaa: README.md changed")
NEW = qa(
    "INSUFFICIENT",
    "stale at HEAD bbbbbbbbbbbb: README.md changed; .agents/skills/s/SKILL.md changed; "
    "evals/s1/cases.json case c1 changed",
)
MISSING = (
    "INSUFFICIENT s1/c1: run 20260101T000000Z-abc123: missing: run 20260101T000000Z-abc123 has "
    "no readable s1/c1/result.json in /q"
)


H = "0123456789ab" + "0" * 28
# the head's checks as the PR's rollup reports them, all passing (test_merge_ask_checks.py)
CHECKS = Checks(
    H, None, Reported([{"__typename": "StatusContext", "context": "c", "state": "SUCCESS"}], None)
)


def order(o: Order) -> list[str]:
    """The merge-order lines check shows for a lane PR with order O; its gaps the same without O."""
    body = f"Closes #6\n\n## Merge ask\n\nHead: {H[:12]}\nBuilt: none\nFailed: none\n"
    s = Snapshot(body, "gh6", ParentLine("6", "Closes #6"), CHECKS, pr=7, head=H, order=o)
    ask, alone = check(s), check(Snapshot(body, "gh6", s.parent, CHECKS, pr=7, head=H))
    assert isinstance(ask, Ask), ask
    assert isinstance(alone, Ask), alone
    assert (ask.gaps, ask.refusal, alone.order) == (alone.gaps, alone.refusal, []), ask
    return ask.order


def test_merge_order_names_stales_and_conflicts() -> None:
    """A PR whose pin goes stale only with this lane merged is named with the items newly stale
    (README.md was stale on main already); a conflicting PR with its files; a pin stale alike on
    both sides, or fresh on both, is not named."""
    prs = [
        Sibling(12, "gh12", [], [Pin(RUN, OLD, NEW)]),
        Sibling(13, "gh13", ["app.py", "notes.txt"], []),
        Sibling(14, "gh14", [], [Pin(RUN, OLD, OLD), Pin(RUN, FRESH, FRESH)]),
    ]
    assert order(Order("main", prs, [])) == [
        HEAD,
        (
            f"- PR #12 (gh12): this merge stales its pinned run {RUN}: .agents/skills/s/SKILL.md "
            "changed; evals/s1/cases.json case c1 changed"
        ),
        "- PR #13 (gh13): its head conflicts with this head in app.py, notes.txt",
    ]


def test_merge_order_unread_and_none() -> None:
    """A pin octo-feather-qa judged no freshness for and a failed read (a fetch, a qc.toml the
    contract rejects) each print one line naming it, never a gap; nothing named prints none, with
    the count of other open PRs."""
    prs = [Sibling(12, "gh12", [], [Pin(RUN, MISSING, MISSING)])]
    fetch = "PR #15 (gh15) head 0123456789ab: git fetch -q failed (couldn't find remote ref)"
    qc = (
        "PR #16 (gh16) head 0123456789ab: qc.toml at 0123456789ab fails octo-feather-contract "
        "(demo.demo#acceptance-z: missing covers)"
    )
    assert order(Order("main", prs, [fetch, qc])) == [
        HEAD,
        f"- not read: PR #12 (gh12) pinned run {RUN}: octo-feather-qa said {MISSING}",
        f"- not read: {fetch}",
        f"- not read: {qc}",
    ]
    none = "none this merge would stale or conflict with"
    assert order(Order("main", [], [])) == [
        HEAD,
        f"- none: 0 other open pull requests on main, {none}",
    ]
    one = [Sibling(14, "gh14", [], [Pin(RUN, FRESH, FRESH)])]
    assert order(Order("gh1146", one, [])) == [
        HEAD,
        f"- none: 1 other open pull request on gh1146, {none}",
    ]
