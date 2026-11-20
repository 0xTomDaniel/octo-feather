"""The merge-order rule (issue-lifecycle spec #gates-merge-order), in-process at its interface,
`check` of scripts/merge_ask.py (ticket #1152, seam `merge_ask.check` posted on it): a Snapshot
whose Order holds the other open PRs as the reads gave them, each pin's lines as octo-feather-qa
--verdict prints them (its --help, Verdict), the merge-order lines out. The command's wiring (the
reads over real git, gh pr list and octo-feather-qa): lane_merge_order.py."""

from merge_ask import Order, ParentLine, Pin, Sibling, Snapshot, check

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


def order(o: Order) -> list[str]:
    body = "Closes #6\n\n## Merge ask\n\nHead: 0123456789ab\n"
    s = Snapshot(body, "gh6", ParentLine("6", "Closes #6"), o)
    ask = check(s)
    assert ask.gaps == check(Snapshot(body, "gh6", ParentLine("6", "Closes #6"))).gaps, ask
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
    """A pin octo-feather-qa judged no freshness for and a failed read each print one line naming
    it; nothing named prints none, with the count of other open PRs."""
    prs = [Sibling(12, "gh12", [], [Pin(RUN, MISSING, MISSING)])]
    fetch = "PR #15 (gh15) head 0123456789ab: git fetch -q failed (couldn't find remote ref)"
    assert order(Order("main", prs, [fetch])) == [
        HEAD,
        f"- not read: PR #12 (gh12) pinned run {RUN}: octo-feather-qa said {MISSING}",
        f"- not read: {fetch}",
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
