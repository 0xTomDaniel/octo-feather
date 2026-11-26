"""The merge ask's rules, in-process at their interface, `check` of scripts/merge_ask.py (its
module docstring; tickets #1147 and #1149, seams agreed on them before any test): a Snapshot in,
the gaps out. Each test is the command scenario of the same name it replaced in
tests/gate/kit/lane_merge_ask.py (parity: tests/parity/lane-merge-ask-*/). LANE is that file's
lane as merge-ask reads it: PR #7 at H, qc's status commit after the judged head J, its clear
review verdict on J, demo's status file; what the tracker skill prints for a branch is the
Snapshot's parent, as its github-issues and linear scripts print it; its git facts (Git) the
lane's commits as git reads them (facts). The command's wiring
(snapshot over the real tracker scripts, comments, status files and qc reports, the gaps and
the passing ask printed): lane_merge_ask.py merge_ask_passes, no_criterion_lane. The Checks
rules: test_merge_ask_checks.py.
"""

import datetime as dt
from dataclasses import replace
from pathlib import Path

from merge_ask import (
    Ask,
    Checks,
    Comment,
    Commit,
    Gate,
    Git,
    Merge,
    NoParent,
    ParentLine,
    Reported,
    Snapshot,
    Trend,
    Unread,
    check,
)

B = "abcdef0" + "2" * 33  # origin/main, the lane's base
M = "abcdef3" + "3" * 33  # a later main commit, a merge's second parent
J = "abcdef1" + "0" * 33  # the judged head: the lane's code commit
H = "abcdef2" + "1" * 33  # PR #7's head: qc's status commit after J
OTHER = "ffee" * 10
URL = "https://github.com/o/r/pull/7#issuecomment-1001"
STATUS = "docs/specs/demo.status.json"
PROOF = f"{J[:12]} to {H[:12]}: qc status commits {H[:12]} change only {STATUS}"
HDR = "| criterion | qc verdict | judged | evidence |\n|---|---|---|---|"
GH6 = ParentLine("6", "Closes #6")
ENG = ParentLine("ENG-123", "Tracks ENG-123")
# the head's checks as the PR's rollup reports them, all passing (test_merge_ask_checks.py)
CHECK_OK: list[dict[str, object]] = [
    {"__typename": "CheckRun", "name": "check", "status": "COMPLETED", "conclusion": "SUCCESS"},
    {"__typename": "StatusContext", "context": "ci/x", "state": "SUCCESS"},
]
CODE = frozenset({"app.py"})
DIFF = ":100644 100644 a b M"  # app.py's line in the lane's diff (git diff --raw)
ONLY = frozenset({STATUS})


def facts(*commits: tuple[str, str, frozenset[str] | Merge]) -> Git:
    """The lane's git facts over origin/main at B: COMMITS oldest first, each (sha, subject, the
    files it changes, or a merge's facts), each the next one's first parent (a merge's second:
    M, on main); every lane diff the same (a merge of main moved none), the status file demo's."""
    got: dict[str, Commit] = {}
    walks: dict[str, tuple[str, ...]] = {}
    prev, seen = B, list[str]()
    for sha, subject, what in commits:
        seen.append(sha)
        got[sha] = (
            Commit((prev, M), subject, merge=what)
            if isinstance(what, Merge)
            else Commit((prev,), subject, what)
        )
        walks[sha] = tuple(seen)
        prev = sha
    diffs: dict[str, dict[str, str]] = {c: {} for c in seen}
    topo = tuple(reversed(seen))
    return Git(
        "origin/main", here=True, topo=topo, commits=got, walks=walks, diffs=diffs, status=ONLY
    )


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
    Checks(H, None, Reported(CHECK_OK, None)),
    pr=7,
    head=H,
    commits=[(H, f"qc: built acceptance-a acceptance-b (judged {J[:12]})"), (J, "feat: x")],
    specs={"demo": demo()},
    named=True,
    comments=[Comment(URL, verdict())],
    git=facts(
        (J, "feat: x", CODE), (H, f"qc: built acceptance-a acceptance-b (judged {J[:12]})", ONLY)
    ),
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


# --- the criterion, review and qc rules (#1149) ---

CHECK_FORM = (
    "`Checks: none` when the diff adds or changes nothing to classify (docs/adr/0008, Who builds "
    "what), else one line each `Check: <path>: <rule> (<owner>) | reads: <what it reads> | "
    "class: exact|proxy|declaration` (docs/adr/0008)"
)
QC = f"qc: built acceptance-a acceptance-b (judged {J[:12]})"


def sha(c: str) -> str:
    """A commit sha of the lane, C repeated."""
    return c * 40


def lane(head: str, *commits: tuple[str, str], **o: str) -> Snapshot:
    """PR #7 at HEAD, its COMMITS (newest first; J's changes app.py, each after it the status
    file), its section the complete one with HEAD and the head proof's line from J, and each
    of O."""
    after = [c for c, sj in reversed(commits) if c != J and sj.startswith("qc: built")]
    proof = f"{J[:12]} to {head[:12]}: qc status commits {' '.join(c[:12] for c in after)}"
    o = {"head": head[:12], "judged": f"{proof} change only {STATUS}", **o}
    chain = [(c, sj, CODE if c == J else ONLY) for c, sj in reversed(commits)]
    return replace(LANE, body=body(**o), head=head, commits=list(commits), git=facts(*chain))


def gaps_of(s: Snapshot) -> list[str]:
    return ask(s).gaps


def test_merge_ask_head() -> None:
    """The section's Head names the PR's head (single_gaps): a stale or missing head fails."""
    stale = (
        f"Head: names {OTHER[:12]}, the PR's head is {H[:12]} (stale): judge {H[:12]} (qc, review) "
        "and rewrite the section for it"
    )
    assert gaps_of(replace(LANE, body=body(head=OTHER[:12]))) == [stale]
    assert gaps_of(replace(LANE, body=body(head=""))) == [f"Head: missing; add `Head: {H}`"]
    assert gaps_of(LANE) == []


def test_merge_ask_rows_and_built() -> None:
    """Rows against Built, Built against the status files and the PR's `qc: built` commits."""
    a = f"| demo#acceptance-a | pass | judged {J[:7]} | r |"

    def rows(extra: str) -> Snapshot:
        return replace(LANE, body=body(rows=f"{a}{extra}"))

    assert gaps_of(rows("")) == [
        (
            "criterion row demo#acceptance-b: missing (it is in Built); add `| demo#acceptance-b | "
            "pass | judged <sha> | <evidence> |`"
        )
    ]
    assert gaps_of(rows(f"\n| demo#acceptance-b | pass | judged {J[:7]} | |")) == [
        "criterion row demo#acceptance-b: no evidence; name the qc report and the command it ran"
    ]
    assert gaps_of(rows(f"\n| demo#acceptance-b | ok | judged {J[:7]} | r |")) == [
        (
            "criterion row demo#acceptance-b: qc verdict 'ok'; write pass or fail, as the qc "
            "report says"
        )
    ]
    zz = f"\n| demo#acceptance-b | pass | judged {J[:7]} | r |\n"
    zz += f"| demo#acceptance-zz | pass | judged {J[:7]} | r |"
    assert gaps_of(rows(zz)) == [
        "criterion row: demo#acceptance-zz: no criterion acceptance-zz in demo's status file"
    ]
    assert gaps_of(replace(LANE, body=body(built="demo#acceptance-a"))) == [
        (
            "Built: lists demo#acceptance-a, the status files hold built with PR #7: "
            "demo#acceptance-a demo#acceptance-b; list exactly those (never edit the status file "
            "by hand)"
        ),
        (
            "criterion row demo#acceptance-b: pass but not in Built; qc flips each pass to built, "
            "so rerun just qc or correct the row"
        ),
    ]
    # a Built id the status file holds but no qc: built commit names: qc's commit, a only
    qa = sha("3")
    only_a = lane(qa, (qa, f"qc: built acceptance-a (judged {J[:12]})"), (J, "feat: x"))
    assert gaps_of(only_a) == [
        (
            "Built: demo#acceptance-b in no `qc: built` commit of PR #7 (they passed "
            "acceptance-a); built only by just qc: run just qc on the head for them, never edit "
            "the status file by hand"
        )
    ]
    # built by an earlier qc run, reset to planned by a later one (PR #49: ac060f9, a56de61)
    q1, q2 = sha("4"), sha("5")
    q1_ = (q1, "qc: built acceptance-a acceptance-c (judged 0123456789ab)")
    reset = lane(q2, (q2, QC), q1_, (J, "feat: x"))
    assert gaps_of(reset) == []
    qn = sha("6")
    assert gaps_of(lane(qn, (qn, "chore: status"), (J, "feat: x"))) == [
        (
            f"Judged: commit {qn[:12]} 'chore: status' after the judged head {J[:12]} is not a "
            "`qc: built ... (judged <sha>)` commit: only just qc writes the status file; drop it, "
            f"then run just qc and the review again, in parallel, on {qn[:12]}"
        ),
        "Built: no `qc: built` commit on PR #7; run just qc on the lane head (docs/adr/0022)",
    ]


def test_merge_ask_review_link() -> None:
    """Review verdict: this PR's marker comment, on the judged head, clear, with usable check
    classes (no proxy); its exact check lines listed."""

    def says(c: str) -> Snapshot:
        return replace(LANE, comments=[Comment(URL, c)])

    link = "link the URL `octo-feather-lane verdict` printed"
    assert gaps_of(replace(LANE, body=body(review=""))) == [
        f"Review verdict: empty is not a comment on PR #7; {link}"
    ]
    pr8 = "https://github.com/o/r/pull/8#issuecomment-1001"
    assert gaps_of(replace(LANE, body=body(review=pr8))) == [
        f"Review verdict: {pr8} is not a comment on PR #7; {link}"
    ]
    other = URL.removesuffix("1001") + "4242"
    assert gaps_of(replace(LANE, body=body(review=other))) == [
        f"Review verdict: comment 4242 not on PR #7; {link}"
    ]
    assert gaps_of(says(verdict(OTHER))) == [
        (
            f"Review verdict: the comment names head {OTHER}, not the judged head {J[:12]}; review "
            f"{J[:12]}, then `octo-feather-lane verdict 7 {J[:12]} <report>`"
        )
    ]
    assert gaps_of(says(verdict(says="Verdict: blocking"))) == [
        "Review verdict: blocking, not clear; fix the blocking findings, qc and review again"
    ]
    assert gaps_of(says(verdict(checks=""))) == [
        (
            "Review verdict: the comment carries no usable check classification (report classifies "
            f"no check: add {CHECK_FORM}): have the review report hold {CHECK_FORM}, then "
            f"`octo-feather-lane verdict 7 {J[:12]} <report>`"
        )
    ]
    proxy = "Check: scripts/x: r (ADR 1) | reads: y | class: proxy"
    assert gaps_of(says(verdict(checks=proxy))) == [
        (
            f"Review verdict: clear with a proxy check ({proxy}): a proxy check blocks "
            "(docs/adr/0008); delete or replace it, review again, and post the verdict with "
            "`octo-feather-lane verdict`"
        )
    ]
    exact = "Check: scripts/x: r (ADR 1) | reads: y | class: exact"
    passed = ask(says(verdict(checks=exact)))
    assert (passed.gaps, passed.classes) == ([], [exact])
    assert ask(LANE).classes == ["Checks: none"]
    assert gaps_of(says("Verdict: clear")) == [
        (
            f"Review verdict: {URL} is not a verdict comment (no marker); post it with "
            "`octo-feather-lane verdict`"
        )
    ]


def test_merge_ask_judged_rows() -> None:
    """Each row's judged head is a commit of the PR, written `judged <sha>`, in a table with the
    judged column; a multi-spec lane names each spec's status file, a qc id outside them not
    demanded."""
    b = f"\n| demo#acceptance-b | pass | judged {J[:7]} | r |"
    deadbee = replace(LANE, body=body(rows=f"| demo#acceptance-a | pass | judged deadbee | r |{b}"))
    assert gaps_of(deadbee) == [
        (
            "criterion row demo#acceptance-a: judged deadbee is not a commit of PR #7; name the "
            "head qc and the review judged (the sha in its `qc: built ... (judged <sha>)` commit, "
            f"or the PR head {H[:12]})"
        )
    ]
    yesterday = replace(LANE, body=body(rows=f"| demo#acceptance-a | pass | yesterday | r |{b}"))
    assert gaps_of(yesterday) == [
        (
            "criterion row demo#acceptance-a: judged 'yesterday'; write `judged <sha>`, the head "
            "qc and the review judged (7+ hex)"
        )
    ]
    old = replace(
        LANE, body=body().replace(HDR.splitlines()[0], "| criterion | qc verdict | evidence |")
    )
    assert gaps_of(old) == [
        (
            "criterion table: no judged column; add `| criterion | qc verdict | judged | evidence "
            "|` with one row per claimed criterion, judged naming the head `just qc` judged"
        )
    ]
    qx = sha("7")
    qcx = (qx, "qc: built acceptance-x (judged 0123456789ab)")
    extra = lane(qx, qcx, *LANE.commits)
    assert gaps_of(extra) == []
    rows = f"| demo#acceptance-a | pass | judged {J[:7]} | r |{b}\n"
    rows += f"| other#acceptance-x | pass | judged {J[:7]} | r |"
    built = "acceptance-a acceptance-b other#acceptance-x"
    other = {"acceptance-x": {"status": "built", "pr": 7}}
    two = lane(qx, qcx, *LANE.commits, rows=rows, built=built)
    assert gaps_of(replace(two, specs={"demo": demo(), "other": other})) == []


def test_merge_ask_failed_triage() -> None:
    """A failed criterion with triage passes; insufficient evidence (quality spec #qc-results) is
    never triaged, from its row or from the latest qc result at the judged head, until a rerun
    gives pass or fail; an untriaged fail and Failed's malformed forms fail."""
    rows = f"| demo#acceptance-a | pass | judged {J[:7]} | r |\n"
    rows += f"| demo#acceptance-b | pass | judged {J[:7]} | r |"
    c_fail = f"\n| demo#acceptance-c | fail | judged {J[:7]} | r |"
    triage = "- acceptance-c: outside the lane, the spec behaviour is untouched (reason)"
    passed = ask(replace(LANE, body=body(failed=f"Failed:\n{triage}", rows=rows + c_fail)))
    assert passed.gaps == []
    assert triage in passed.section
    never = (
        "insufficient evidence is never triaged; rerun just qc on it until it gives pass or fail"
    )
    short = rows.replace("| pass | judged", "| insufficient evidence | judged").replace(
        "| demo#acceptance-a | insufficient evidence", "| demo#acceptance-a | pass"
    )
    assert gaps_of(replace(LANE, body=body(rows=short))) == [
        f"criterion row demo#acceptance-b: {never}"
    ]
    missing = (
        "demo did not run to its end (exit 77, a step it needs could not run here): needs GitHub"
    )
    report = f"{J}-20261029T100000Z-abc123.json"
    a = {"id": "acceptance-a", "verdict": "pass", "decision": "demo checks"}
    b = {"id": "acceptance-b", "verdict": "insufficient evidence", "missing": [missing]}
    latest = {"demo#acceptance-a": (a, report), "demo#acceptance-b": (b, report)}
    assert gaps_of(replace(LANE, qc={J: latest})) == [
        (
            f"criterion demo#acceptance-b: insufficient evidence at the judged head {J[:12]} "
            f"({missing}; qc report {report}): never triaged; make what is missing available, then "
            "rerun just qc on it until it gives pass or fail"
        )
    ]
    rerun = {**latest, "demo#acceptance-b": ({"id": "acceptance-b", "verdict": "pass"}, report)}
    assert gaps_of(replace(LANE, qc={J: rerun})) == []  # the rerun at that head gave it pass
    assert gaps_of(replace(LANE, body=body(rows=rows + c_fail))) == [
        (
            "criterion row demo#acceptance-c: fail with no triage; add `- demo#acceptance-c: "
            "<triage>` under Failed (spec #delivery-qa-triage)"
        )
    ]
    assert gaps_of(
        replace(LANE, body=body(failed="Failed:\n- acceptance-c:", rows=rows + c_fail))
    ) == [
        (
            "Failed: demo#acceptance-c has no triage; add `- demo#acceptance-c: <repair ticket, "
            "judging fix, or outside the lane and why>` (spec #delivery-qa-triage)"
        )
    ]
    assert gaps_of(
        replace(LANE, body=body(failed="Failed:\n- acceptance-c: repair ticket #9"))
    ) == [
        (
            "criterion row demo#acceptance-c: missing (it is in Failed); add `| demo#acceptance-c "
            "| fail | judged <sha> | <evidence> |`"
        )
    ]
    assert gaps_of(replace(LANE, body=body(failed="Failed: some"))) == [
        (
            "Failed: 'some'; write `Failed: none`, or `Failed:` then one `- <id>: <triage>` line "
            "per failed criterion"
        )
    ]


def test_merge_ask_passes() -> None:
    """A complete section passes with its section, check classes and each row's decision source:
    none yet, then the latest qc result's at the judged head (quality#acceptance-qc-fallback)."""
    a = ask(LANE)
    assert (a.gaps, a.section[0], a.judged_head, a.proof) == ([], "## Merge ask", J, PROOF)
    src = (
        f"Decision sources (the latest qc result at the judged head {J[:12]}; quality spec "
        "#qc-results):"
    )
    none = "no qc result at the judged head"
    assert a.sources == [src, f"- demo#acceptance-a: {none}", f"- demo#acceptance-b: {none}"]
    report = f"{J}-20261029T090000Z-src123.json"
    qc = {
        "demo#acceptance-a": ({"id": "acceptance-a", "decision": "tagged test assertions"}, report),
        "demo#acceptance-b": ({"id": "acceptance-b", "decision": "demo checks"}, report),
    }
    assert ask(replace(LANE, qc={J: qc})).sources == [
        src,
        "- demo#acceptance-a: tagged test assertions",
        "- demo#acceptance-b: demo checks",
    ]


def test_merge_ask_one_judged_head() -> None:
    """One judged head (spec #lanes-one-head): the rows name one head, the head proof's line for
    it is the section's Judged line; each why it gives is a gap, a refusal its one."""
    assert gaps_of(replace(LANE, body=body(judged=""))) == [
        f"Judged: names ''; add the check's proof line `Judged: {PROOF}`"
    ]
    two = f"| demo#acceptance-a | pass | judged {J[:7]} | r |\n"
    two += f"| demo#acceptance-b | pass | judged {H[:7]} | r |"
    assert gaps_of(replace(LANE, body=body(rows=two))) == [
        (
            f"criterion table: rows name 2 judged heads ({J[:12]}, {H[:12]}); qc and the review "
            "judge one head: run just qc, naming every criterion the lane builds, and the review "
            "on one integrated head"
        )
    ]
    outside = "--status /x/demo.status.json is outside this repo (/r): run merge-ask ..."
    refused = replace(LANE, git=replace(LANE.git or facts(), status=Unread(outside)))
    assert gaps_of(refused) == [f"Judged: {outside}"]
    # H may add only qc's status commit (one_judged_head): a code commit, a qc commit carrying
    # another file or a hand status edit after it fails naming it; qc rerun at the exact head
    # passes
    f, q, st = sha("b"), sha("c"), sha("d")
    rerun = "run just qc and the review again, in parallel, on"
    qc = f"qc: built acceptance-a (judged {J[:12]})"
    for at, subject, files, why in (
        (f, "feat: after qc", CODE, "changes app.py, not only the status file qc writes"),
        (q, qc, ONLY | {"stray.txt"}, "changes stray.txt, not only the status file qc writes"),
        (st, "fix status", ONLY, "is not a `qc: built ... (judged <sha>)` commit: only just qc"),
    ):
        tail = f" ({STATUS}): {rerun} {at[:12]}" if "only the status" in why else ""
        tail = tail or f" writes the status file; drop it, then {rerun} {at[:12]}"
        chain = [(J, "feat: x", CODE), (H, QC, ONLY), (at, subject, files)]
        s = replace(
            LANE,
            body=body(head=at[:12]),
            head=at,
            commits=[(at, subject), *LANE.commits],
            git=facts(*chain),
        )
        want = f"Judged: commit {at[:12]} {subject!r} after the judged head {J[:12]} {why}{tail}"
        assert gaps_of(s) == [want], (subject, gaps_of(s))
    exact = replace(
        LANE,
        body=body(head=f[:12], judged=f"{f[:12]} is the PR head", rows=lane_rows(f[:9])),
        head=f,
        commits=[(f, "feat: after qc"), *LANE.commits],
        git=facts((J, "feat: x", CODE), (H, QC, ONLY), (f, "feat: after qc", CODE)),
        comments=[Comment(URL, verdict(f))],
    )
    assert gaps_of(exact) == []


def lane_rows(at: str) -> str:
    """Rows a and b judged at AT, evidence r."""
    return (
        f"| demo#acceptance-a | pass | judged {at} | r |\n"
        f"| demo#acceptance-b | pass | judged {at} | r |"
    )


R = sha("e")  # PR #7's head: a merge of main after H


def merged(merge: Merge, diff: str = DIFF, subject: str = "Merge main") -> Snapshot:
    """PR #7 at R, a merge MERGE of H with main's M, the lane's diff at R DIFF (J's: DIFF)."""
    g = facts((J, "feat: x", CODE), (H, QC, ONLY), (R, subject, merge))
    diffs = {J: {"app.py": DIFF}, H: {"app.py": DIFF}, R: {"app.py": diff}}
    return replace(
        LANE,
        body=body(head=R[:12]),
        head=R,
        commits=[(R, subject), *LANE.commits],
        git=replace(g, diffs=diffs),
    )


def test_merge_ask_main_merges() -> None:
    """Main merges (the rule: spec #lanes-one-head): one the rule lets keep the qc verdict
    keeps it, the check giving its proof line; one touching a lane file, resolving a conflict,
    changing a file beyond git's automatic merge, or merging another branch: qc reruns."""
    proof = (
        f"{J[:12]} to {R[:12]}: qc status commits {H[:12]} change only {STATUS}; clean merge of "
        f"main {R[:12]}: lane hunks identical (1 file, sha256 970d7aa3e679)"
    )
    clean = merged(Merge(onto=True))
    assert gaps_of(clean) == [
        f"Judged: names {PROOF!r}; add the check's proof line `Judged: {proof}`"
    ]
    assert gaps_of(replace(clean, body=body(head=R[:12], judged=proof))) == []
    rerun = f"run just qc and the review again, in parallel, on {R[:12]}"
    moved = merged(Merge(onto=True), diff=":100644 100644 a c M")
    assert gaps_of(moved) == [
        (
            "Judged: after merging origin/main, the lane's own hunks changed in app.py (main "
            "changed the lane's own lines, or the lane's diff moved): the qc verdict does not "
            f"carry over; {rerun}"
        )
    ]
    resolved = "Merge main, conflict resolved"
    conflict = merged(Merge(onto=True, conflict=True, resolution=("app.py",)), subject=resolved)
    assert gaps_of(conflict) == [
        (
            f"Judged: merge {R[:12]} {resolved!r} resolved a conflict with origin/main: the qc "
            f"verdict does not carry over; {rerun}"
        )
    ]
    evil = merged(Merge(onto=True, beyond=("evil.txt",), resolution=("evil.txt",)))
    assert gaps_of(evil) == [
        (
            f"Judged: merge {R[:12]} 'Merge main' changes evil.txt beyond git's automatic merge: "
            f"{rerun}"
        )
    ]
    side = merged(Merge(onto=False), subject="Merge side")
    assert gaps_of(side) == [
        (
            f"Judged: merge {R[:12]} 'Merge side' brings in {M[:12]}, not origin/main: only a "
            f"merge of main keeps the qc verdict; {rerun}"
        )
    ]


def test_merge_ask_main_changed_lane_hunks() -> None:
    """issue-lifecycle#acceptance-one-head: a clean merge of main that changed the lane's own
    changes refuses, naming the file. J's lane diff of app.py is two hunks (their form:
    merge_ask._lane_diff); main made the second edit too, so at R the lane's hunk is gone."""
    two = "100644 100644 M\n@@\n-1\n+one\n@@\n-20\n+lane"
    rerun = f"run just qc and the review again, in parallel, on {R[:12]}"
    shrunk = merged(Merge(onto=True), diff="100644 100644 M\n@@\n-1\n+one")
    g = shrunk.git
    assert g is not None
    shrunk = replace(shrunk, git=replace(g, diffs={**g.diffs, J: {"app.py": two}}))
    assert gaps_of(shrunk) == [
        (
            "Judged: after merging origin/main, the lane's own hunks changed in app.py (main "
            "changed the lane's own lines, or the lane's diff moved): the qc verdict does not "
            f"carry over; {rerun}"
        )
    ]


N = sha("8")  # PR #8's head: a fix off main, no qc commit
URL8 = "https://github.com/o/r/pull/8#issuecomment-1008"


def pr8(at: str = N, *after: tuple[str, str], **o: str) -> Snapshot:
    """PR #8, a lane building no criterion, at AT (AFTER its commits after N), its review
    verdict on N, its section with each of O: parent head judged table built failed."""
    section = (
        f"{o.get('parent', 'Closes #6')}\n\n## Merge ask\n\n"
        f"Head: {o.get('head', at[:12])}\nChecks: check, ci/x pass\n"
        f"{o.get('judged', '')}\n{o.get('table', '')}\n"
        f"Review verdict: {URL8}\nBuilt: {o.get('built', 'none')}\n"
        f"{o.get('failed', 'Failed: none')}\n"
    )
    return Snapshot(
        section,
        "gh6",
        GH6,
        Checks(at, None, Reported(CHECK_OK, None)),
        pr=8,
        head=at,
        commits=[*after, (N, "fix: a rule")],
        comments=[Comment(URL8, verdict(N))],
        git=facts((N, "fix: a rule", CODE), *((c, sj, Merge(onto=True)) for c, sj in after)),
    )


def test_merge_ask_no_criterion_lane() -> None:
    """A lane building no criterion passes on head, parent line and the review verdict alone,
    with no table or its header, its status files optional; each item still checked; the
    verdict's head is the judged head: a commit after it needs the head proof's line."""
    for tbl in ("", HDR):
        for named in (False, True):
            s = replace(pr8(table=tbl), named=named, specs={"demo": demo()} if named else {})
            a = ask(s)
            assert (a.gaps, a.section[0], "Built: none" in a.section) == ([], "## Merge ask", True)
    assert gaps_of(pr8(head=OTHER[:12])) == [
        (
            f"Head: names {OTHER[:12]}, the PR's head is {N[:12]} (stale): judge {N[:12]} (qc, "
            "review) and rewrite the section for it"
        )
    ]
    assert gaps_of(pr8(parent="")) == [missing(GH6)]
    blocking = replace(pr8(), comments=[Comment(URL8, verdict(N, says="Verdict: blocking"))])
    assert gaps_of(blocking) == [
        "Review verdict: blocking, not clear; fix the blocking findings, qc and review again"
    ]
    unclassed = replace(pr8(), comments=[Comment(URL8, verdict(N, checks=""))])
    assert gaps_of(unclassed) == [
        (
            "Review verdict: the comment carries no usable check classification (report classifies "
            f"no check: add {CHECK_FORM}): have the review report hold {CHECK_FORM}, then "
            f"`octo-feather-lane verdict 8 {N[:12]} <report>`"
        )
    ]
    nm = sha("9")
    merged = pr8(nm, (nm, "Merge main"))
    p = (
        f"{N[:12]} to {nm[:12]}: no qc status commit; clean merge of main {nm[:12]}: lane hunks "
        "identical (0 files, sha256 e3b0c44298fc)"
    )
    assert gaps_of(merged) == [f"Judged: missing; add the check's proof line `Judged: {p}`"]
    assert gaps_of(pr8(nm, (nm, "Merge main"), judged=f"Judged: {p}")) == []
    # the verdict's head is the judged head: a code commit after it fails (no --status: the
    # status files none)
    nf = sha("f")
    after = pr8(nf, head=nf[:12])
    after = replace(
        after,
        commits=[(nf, "fix: more"), (N, "fix: a rule")],
        git=replace(facts((N, "fix: a rule", CODE), (nf, "fix: more", CODE)), status=frozenset()),
    )
    assert gaps_of(after) == [
        (
            f"Judged: commit {nf[:12]} 'fix: more' after the judged head {N[:12]} changes app.py, "
            f"not only the status file qc writes (): run just qc and the review again, in "
            f"parallel, on {nf[:12]}"
        )
    ]
    # the full pass: N's recorded pass carries to the head N, never to a code commit after it
    ident: dict[str, object] = {"gate_config": "c" * 64, "list": "absent"}
    rec: dict[str, object] = {"tier": "full", "head": N, "clean": True, **ident}
    assert gaps_of(replace(pr8(), gate=Gate((0, ident), {N: rec}))) == []
    n2 = sha("0")
    fix = (
        f"run the full gate, just check, on {n2[:12]} and record its pass (octo-feather-integrate "
        "--full records it; octo-feather-gate --help)"
    )
    later = replace(
        pr8(n2, head=n2[:12]),
        commits=[(n2, "fix: no full pass"), (N, "fix: a rule")],
        comments=[Comment(URL8, verdict(n2))],
        git=replace(
            facts((N, "fix: a rule", CODE), (n2, "fix: no full pass", CODE)), status=frozenset()
        ),
        gate=Gate((0, ident), {n2: {}, N: rec}),
    )
    assert gaps_of(later) == [
        (
            f"Full pass: head {n2[:12]} has no current recorded full gate pass for that head and "
            f"its gate configuration; the full pass recorded at {N[:12]} does not carry over: "
            f"commit {n2[:12]} 'fix: no full pass' after the full pass {N[:12]} changes app.py, "
            f"not only the status file qc writes (): {fix}"
        )
    ]


def test_merge_ask_gate_time() -> None:
    """issue-lifecycle#acceptance-merge-ask-gate-budget: the full gate's wall time on the final
    head (J's run: H adds only qc's status commit) against gate-budget.toml at the head, flagged
    over budget and grown past the share, beside the trend (passed full runs on the head's
    history: B's three; a subset run on H and a red full run on J stay out) and the slowest
    items; no gate on timing: the ask passes, or fails with the same items, as with none."""
    path = Path("/s/octo-feather/check-runs.jsonl")
    now = dt.datetime(2026, 10, 5, 12, 0, tzinfo=dt.UTC)
    budget = "budget_seconds = 150\ngrowth_share = 0.25\ntrend_runs = 3\n"
    j, h, b = J[:12], H[:12], B[:12]
    head = (
        f"Gate time (the full gate on the final head against gate-budget.toml at {h}; the code "
        "reviewer judges it, no gate reads it: issue-lifecycle #lanes-checkpoints):"
    )
    history = frozenset({B, J, H})
    none = replace(LANE, trend=Trend(path, None, history, budget, now))
    assert ask(none).gate_time == [head, f"  no gate run recorded ({path}: none)"]

    def run(
        start: str, sha: str, total: float, rc: int = 0, tier: str = "full"
    ) -> dict[str, object]:
        steps = [
            {"name": "tests/a.sh", "seconds": int(total) - 30, "result": "ok"},
            {"name": "tests/b.sh", "seconds": 20.5, "result": "ok"},
            {"name": "check-lint", "seconds": 1.0, "result": "ok"},
        ]
        return {
            "start": start,
            "head": sha,
            "total_s": total,
            "exit": rc,
            "tier": tier,
            "steps": steps,
        }

    day = "2026-10-0{}T{}:00:00Z".format
    rows = [
        run(day(1, 10), B, 100),
        run(day(2, 10), B, 120),
        run(day(3, 10), B, 110),
        run(day(4, 10), J, 90, 1),
        run(day(4, 11), J, 200.5),
        run(day(4, 12), H, 5, tier="subset"),
    ]
    trend = Trend(path, (list(enumerate(rows, 1)), []), history, budget, now)
    timed = replace(LANE, trend=trend)
    assert ask(timed).gate_time == [
        head,
        (
            f"  full gate: 200.5s, head {j}, started {day(4, 11)} (1d1h0m ago): OVER BUDGET by "
            "50.5s (budget 150s)"
        ),
        (
            "  growth: +82.3% over the trend's median 110s (the 3 passed full runs before it); set "
            "share 25%: GROWN"
        ),
        (
            f"  trend: 100s {b} {day(1, 10)}, 120s {b} {day(2, 10)}, 110s {b} {day(3, 10)}, "
            f"200.5s {j} {day(4, 11)} (passed full runs, oldest first)"
        ),
        "  slowest: tests/a.sh 170s, tests/b.sh 20.5s, check-lint 1s",
    ]
    for s in (LANE, replace(LANE, body=body(review=""))):  # a pass, a refusal: the same gaps
        assert (
            ask(replace(s, trend=trend)).gaps
            == ask(replace(s, trend=None)).gaps
            == ask(replace(s, trend=Trend(path, None, history, budget, now))).gaps
        )
    assert ask(replace(LANE, body=body(review=""))).gaps != []


def test_merge_ask_criterion_claimed() -> None:
    """A lane that claims a criterion (a qc commit, a Built or Failed id, a status entry built
    with the PR) with no rows is refused naming the table (#acceptance-merge-ask-evidence); one
    with a Built id needs its status files."""
    nq = sha("a")
    built8 = {**demo(), "acceptance-a": {"status": "built", "pr": 8}}
    for tbl in ("", HDR):
        want = "criterion table: " + (
            "no rows; add one per claimed criterion"
            if tbl
            else "missing; add `| criterion | qc verdict | judged | evidence |` with one row per "
            "claimed criterion, judged naming the head `just qc` judged"
        )
        for claimed in (
            pr8(nq, (nq, "qc: built acceptance-a (judged 0123456789ab)"), table=tbl),
            pr8(table=tbl, built="demo#acceptance-a"),
            pr8(table=tbl, failed="Failed:\n- acceptance-c: repair ticket #9"),
            replace(pr8(table=tbl), specs={"demo": built8}),
        ):
            s = replace(claimed, named=True, specs=claimed.specs or {"demo": demo()})
            assert ask(s).judged == [want], (tbl, s)
    unnamed = ask(pr8(built="acceptance-a"))
    assert (unnamed.refusal, unnamed.gaps) == (
        "name the lane's status file: --status docs/specs/<slug>.status.json (once per spec)",
        [],
    )
