#!/usr/bin/env python3
"""The merge ask's rules: a PR's facts read once into a Snapshot, judged by a pure check.

The design: issue #1146 (its design comment); the rules: issue-lifecycle spec #gates-pr-line,
#acceptance-merge-ask-evidence, #acceptance-merge-ask-no-criterion, #lanes-one-head,
#delivery-qa-triage, quality spec #qc-results, the merge ask (octo-feather-lane --help,
merge-ask). Imported by scripts/octo-feather-lane (`merge-ask` builds one snapshot, checks it
and adds its own Checks, carried-check and full-pass items between check's; `verdict`, `fields`
and the head proof share the review comment's and the report's parsers below); how a command
finds this module: the docstring of scripts/correction_lanes.py. Standard library only
(AGENTS.md Rules, kit scripts). The merge ask's other rules (Checks, the head proof, the full
pass, the gate time) are still in octo-feather-lane's cmd_merge_ask.

Interface:

    snapshot(pr, files, read, qc_dir, err=...) -> Snapshot
        The one reader: the status FILES (--status), then the PR through READ, the command's
        reader ((gh pr view's JSON, the PR's commits or why they are unread)), what the
        tracker skill's key-from-branch and pr-line print for its head branch (ParentLine) or
        its refusal (NoParent), and the qc reports in QC_DIR at each commit of the PR. An
        unreadable status file raises ERR.
    check(s) -> Ask | Need
        Pure, no I/O. Need: the head proof (octo-feather-lane's head_proof) the rules need
        next, by its arguments; the caller adds its answer to S.proofs and checks again. Ask:
        each refusal line the merge ask prints for S, in order, in three parts the command's
        own items go between; none when S passes; with what a passing ask prints.
"""

__all__ = [
    "Ask",
    "Comment",
    "Need",
    "NoParent",
    "ParentLine",
    "Proof",
    "ProofAsk",
    "ProofError",
    "Snapshot",
    "check",
    "snapshot",
]

import dataclasses
import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from tracker_calls import tracker

# GitHub's closing keywords: a PR body line with one closes that GitHub issue at merge, named
# as #N, as owner/repo#N or by the issue URL.
CLOSES = re.compile(
    r"\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\b:?\s+"
    r"(?:[\w.-]+/[\w.-]+#|https?://(?:www\.)?github\.com/[\w.-]+/[\w.-]+/issues/|#)(\d+)\b",
    re.IGNORECASE,
)

# --- the snapshot ---


@dataclass(frozen=True)
class ParentLine:
    """The lane's parent as the tracker skill names it: KEY (key-from-branch), LINE (pr-line)."""

    key: str
    line: str


@dataclass(frozen=True)
class NoParent:
    """The tracker skill refused to name the parent: WHY, its error as tracker_calls words it."""

    why: str


@dataclass(frozen=True)
class Comment:
    """A PR comment as gh printed it: its URL and BODY ("" for none)."""

    url: str
    body: str


@dataclass(frozen=True)
class ProofAsk:
    """A head proof the rules need: octo-feather-lane's head_proof(JUDGED, HEAD, the --status
    files, the base, at=AT, kept=KEPT, rerun=RERUN, resolved=dict(RESOLVED) or None), its
    defaults head_proof's own."""

    judged: str
    head: str
    at: str = "judged head"
    kept: str = "the qc verdict"
    rerun: str = ""
    resolved: tuple[tuple[str, str], ...] | None = None


@dataclass(frozen=True)
class Proof:
    """head_proof's answer: LINE, the proof line, when HEAD stands for JUDGED, else WHY each
    part does not."""

    line: str | None
    why: tuple[str, ...]


@dataclass(frozen=True)
class ProofError:
    """head_proof refused (a commit or the base not in the repo, a status file outside it):
    WHY, its message."""

    why: str


@dataclass(frozen=True)
class Snapshot:
    """A PR's facts, read once."""

    # the parent line (#1147): the PR's BODY, head BRANCH and the PARENT the tracker skill names
    body: str
    branch: str
    parent: ParentLine | NoParent
    # the criterion, review and qc rules (#1149): PR number, HEAD (gh's headRefOid), its COMMITS
    # (sha, subject; newest first) or UNREAD, the gap naming why none were read; the SPECS,
    # {slug: criteria} of the --status files, NAMED when any was passed; the PR's COMMENTS; QC,
    # each PR commit's (lowercase sha) latest qc result per criterion (<spec>#<id>: (result,
    # report name)); PROOFS, each head proof the command answered (check's Need)
    pr: int = 0
    head: str = ""
    commits: list[tuple[str, str]] = dataclasses.field(default_factory=list)
    unread: str = ""
    specs: dict[str, dict[str, dict[str, object]]] = dataclasses.field(default_factory=dict)
    named: bool = False
    comments: list[Comment] = dataclasses.field(default_factory=list)
    qc: dict[str, dict[str, tuple[dict[str, object], str]]] = dataclasses.field(
        default_factory=dict
    )
    proofs: dict[ProofAsk, Proof | ProofError] = dataclasses.field(default_factory=dict)


@dataclass(frozen=True)
class Ask:
    """The merge ask's verdict on a Snapshot. Its gaps, each a refusal line, in three parts in
    the order printed: HEAD (the PR commits, parent line, section and Head; the command's Checks
    items follow), JUDGED (the criterion table to the Judged line; the command's carried checks
    and full pass follow) and REVIEW (the review verdict to the criterion rows against Built
    and Failed); none when it passes. REFUSAL: why nothing can be judged (exit 1, no gap).
    What a passing ask prints and the command reads: SECTION, the `## Merge ask` lines; JUDGED_HEAD
    and PROOF (its head proof line); CLASSES, the review's check classes; SOURCES, each row's
    decision source; JUDGMENTS, the model judgment comments (shown only)."""

    head: list[str]
    judged: list[str] = dataclasses.field(default_factory=list)
    review: list[str] = dataclasses.field(default_factory=list)
    refusal: str = ""
    section: list[str] = dataclasses.field(default_factory=list)
    judged_head: str | None = None
    proof: str | None = None
    classes: list[str] = dataclasses.field(default_factory=list)
    sources: list[str] = dataclasses.field(default_factory=list)
    judgments: list[str] = dataclasses.field(default_factory=list)

    @property
    def gaps(self) -> list[str]:
        return [*self.head, *self.judged, *self.review]


@dataclass(frozen=True)
class Need:
    """The head proof check needs next (PROOF); answer it in Snapshot.proofs, then check again."""

    proof: ProofAsk


class _TrackerError(Exception):
    """A tracker script's refusal, kept as NoParent."""


def snapshot(
    pr: int,
    files: list[str],
    read: Callable[[], tuple[dict[str, object], list[tuple[str, str]] | str]],
    qc_dir: Path,
    *,
    err: type[Exception],
) -> Snapshot:
    specs = statuses(files, err) if files else {}
    view, commits = read()
    body, branch = str(view["body"] or ""), str(view["headRefName"] or "")
    head = cast("str", view["headRefOid"])
    try:
        key = tracker("key-from-branch", branch, err=_TrackerError).strip()
        line = tracker("pr-line", key, err=_TrackerError).strip()
        parent: ParentLine | NoParent = ParentLine(key, line)
    except _TrackerError as e:
        parent = NoParent(str(e))
    raw = cast("list[dict[str, object]]", view["comments"] or [])
    comments = [Comment(str(c.get("url") or ""), str(c.get("body") or "")) for c in raw]
    listed = commits if isinstance(commits, list) else []
    shas = {oid.lower() for oid, _ in listed} | {head.lower()}
    return Snapshot(
        body,
        branch,
        parent,
        pr=pr,
        head=head,
        commits=listed,
        unread="" if isinstance(commits, list) else commits,
        specs=specs,
        named=bool(files),
        comments=comments,
        qc={sha: qc_latest(qc_dir, sha) for sha in sorted(shas)},
    )


def statuses(files: list[str], err: type[Exception]) -> dict[str, dict[str, dict[str, object]]]:
    """{spec slug: criteria} from each --status file; ERR naming the first unreadable one."""
    specs: dict[str, dict[str, dict[str, object]]] = {}
    for f in files:
        try:
            d = json.loads(Path(f).read_text())
            slug = re.sub(r"\.spec\.html$", "", Path(d["spec"]).name)
            crit = d["criteria"]
            assert isinstance(crit, dict)
            assert all(isinstance(v, dict) for v in cast("dict[str, object]", crit).values())
        except (OSError, ValueError, KeyError, TypeError, AssertionError) as e:
            msg = (
                f"--status {f} is not a readable status file ({type(e).__name__}: {e}): name "
                "docs/specs/<slug>.status.json"
            )
            raise err(msg) from None
        specs[slug] = cast("dict[str, dict[str, object]]", crit)
    return specs


def qc_latest(d: Path, judged: str) -> dict[str, tuple[dict[str, object], str]]:
    """Each criterion's (<spec>#<id>) latest result in the qc reports in D at the JUDGED head,
    with its report's name (reports: octo-feather-qc --help, Report; OCTO_FEATHER_QC_DIR as
    there)."""
    latest: dict[str, tuple[dict[str, object], str]] = {}
    for p in sorted(
        d.glob(f"{judged.lower()}-*.json"),
        key=lambda p: (p.name.split("-")[1], p.stat().st_mtime_ns),
    ):
        # <head>-<UTC stamp>-<runid>.json, oldest first: a rerun's result replaces the earlier one
        try:
            rep = json.loads(p.read_text(encoding="utf-8"))
            spec, results = str(rep.get("spec")), list(rep.get("results") or [])
        except (OSError, ValueError, AttributeError, TypeError):
            continue
        for r in cast("list[object]", results):
            if isinstance(r, dict) and "id" in r:
                r_ = cast("dict[str, object]", r)
                latest[f"{spec}#{r_['id']}"] = (r_, p.name)
    return latest


# --- the check ---


class _NeedError(Exception):
    """A head proof the rules need that S.proofs lacks: check returns it as a Need."""

    def __init__(self, ask: ProofAsk) -> None:
        super().__init__(ask)
        self.ask = ask


def check(s: Snapshot) -> Ask | Need:
    try:
        return _check(s)
    except _NeedError as m:
        return Need(m.ask)


def parent_line(s: Snapshot) -> list[str]:
    """Spec #gates-pr-line: the body carries the tracker skill's pr-line for the lane's parent
    (the key its key-from-branch reads from the PR branch), and closes no other GitHub issue."""
    if isinstance(s.parent, NoParent):
        return [
            (
                f"parent line: cannot name it for branch {s.branch!r} ({s.parent.why}); "
                "push the lane from its lane branch (docs/adr/0011)"
            )
        ]
    key, want = s.parent.key, s.parent.line
    lines = [ln.strip() for ln in s.body.splitlines()]
    got = [
        ln
        for ln in lines
        if ln == want
        or (ln.startswith(want) and not re.match(r"[\w-]", ln[len(want) : len(want) + 1]))
    ]
    out = (
        []
        if got
        else [
            (
                f"parent line: missing; add the line `{want}` "
                f"(the tracker skill's pr-line {key}) to the PR body"
            )
        ]
    )
    for ln in lines:
        for m in CLOSES.finditer(ln):
            if ln in got and m.end() <= len(want):
                # the parent line's own closing link (GitHub: Closes #<parent>), never the rest
                # of its line
                continue
            out.append(
                f"parent line: `{ln[:80]}` closes GitHub issue #{m.group(1)}, "
                f"not the lane's parent line `{want}`; remove it (the supervisor's close moves "
                "each ticket to done with the tracker skill's issue-done)"
            )
    return out


def _proved(s: Snapshot, ask: ProofAsk) -> tuple[str | None, list[str]]:
    """(proof line, why not) of S's answer to ASK, a refusal its one why."""
    p = s.proofs.get(ask)
    if p is None:
        raise _NeedError(ask)
    return (None, [p.why]) if isinstance(p, ProofError) else (p.line, list(p.why))


def _check(s: Snapshot) -> Ask:
    pr, head = s.pr, s.head
    # --- the PR's commits, the parent line, the section and its Head ---
    first = [f"PR commits: {s.unread}"] if s.unread else []
    first += parent_line(s)
    sec = section(s.body)
    if sec is None:
        first.append(
            "`## Merge ask` section: none in the PR body; add it (format: octo-feather-lane with "
            "no arguments)"
        )
    lines = sec or []
    no_crit = no_criterion(lines, s.commits, s.specs, pr)
    if not s.named and not no_crit:  # a lane that claims a criterion names its status files
        return Ask([], refusal=NO_STATUS)
    h = field(lines, "Head")
    if not h or not h[1]:
        first.append(f"Head: missing; add `Head: {head}`")
    elif not head_matches(h[1].strip("`"), head):
        first.append(
            f"Head: names {h[1]}, the PR's head is {head[:12]} (stale): judge {head[:12]} (qc, "
            "review) and rewrite the section for it"
        )
    # --- the criterion table, qc's insufficient evidence, the judged head and its proof ---
    judged_gaps, t, rows, judged = criteria(s, lines, no_crit=no_crit)
    resolved = resolution_verdicts(s.comments)
    judged, proof, why = judged_proof(s, lines, judged, resolved, no_crit=no_crit)
    judged_gaps += why
    # --- the review verdict and its check classes, Built, Failed, the rows against them ---
    rest, classes = review(s, lines, judged, resolved)
    gaps, built = built_ids(s, lines, no_crit=no_crit)
    rest += gaps
    gaps, fails = failed(s, lines)
    rest += gaps
    if t is not None:
        rest += rows_against(rows, built, fails)
    return Ask(
        first,
        judged_gaps,
        rest,
        section=lines,
        judged_head=judged,
        proof=proof,
        classes=classes,
        sources=sources(s, rows, judged),
        judgments=judgment_lines(s.comments),
    )


def criteria(  # noqa: C901, PLR0912  one branch per row gap, in the order printed
    s: Snapshot, lines: list[str], *, no_crit: bool
) -> tuple[list[str], int | None, dict[str, str], str | None]:
    """(the criterion table's gaps, its header's index, {criterion: qc verdict} of its rows, the
    one head they judge) (spec #acceptance-merge-ask-evidence, quality #qc-results)."""
    pr, head, specs = s.pr, s.head, s.specs
    miss: list[str] = []
    rows: dict[str, str] = {}
    judged_at: set[str] = set()
    t = next(
        (
            i
            for i, ln in enumerate(lines)
            if re.fullmatch(
                r"\|\s*criterion\s*\|\s*qc verdict\s*\|\s*judged\s*\|\s*evidence\s*\|",
                ln.strip(),
                re.IGNORECASE,
            )
        ),
        None,
    )
    if t is None:
        old = any(
            re.fullmatch(
                r"\|\s*criterion\s*\|\s*qc verdict\s*\|\s*evidence\s*\|", ln.strip(), re.IGNORECASE
            )
            for ln in lines
        )
        if not no_crit:
            miss.append(
                f"criterion table: {'no judged column' if old else 'missing'}; add `| criterion "
                "| qc verdict | judged | evidence |` with one row per claimed criterion, judged "
                "naming the head just qc judged"
            )
    else:
        for ln in lines[t + 1 :]:
            if not ln.strip().startswith("|"):
                break
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            if all(re.fullmatch(r":?-+:?", c) for c in cells):
                continue
            if len(cells) != ROW_CELLS:
                miss.append(
                    f"criterion row `{ln.strip()}`: needs 4 cells, criterion | qc verdict | "
                    "judged <sha> | evidence"
                )
                continue
            cid, why = resolve(cells[0], specs)
            v = cells[1].strip("`*").lower()
            if not cid:
                miss.append(f"criterion row: {why}")
                continue
            if cid in rows:
                miss.append(f"criterion row {cid}: listed twice; keep one")
            if v == "insufficient evidence":  # a result, never a failure to triage (#qc-results)
                miss.append(
                    f"criterion row {cid}: insufficient evidence is never triaged; rerun just qc "
                    "on it until it gives pass or fail"
                )
            elif v not in ("pass", "fail"):
                miss.append(
                    f"criterion row {cid}: qc verdict {cells[1]!r}; write pass or fail, as the qc "
                    "report says"
                )
            if not cells[3]:
                miss.append(
                    f"criterion row {cid}: no evidence; name the qc report and the command it ran"
                )
            sha, why = judged_sha(cells[2], s.commits, head, pr)
            if sha:
                judged_at.add(sha)
            else:
                miss.append(f"criterion row {cid}: {why}")
            rows[cid] = v
        if not rows and not no_crit:
            miss.append("criterion table: no rows; add one per claimed criterion")
    judged = next(iter(judged_at)) if len(judged_at) == 1 else None
    if len(judged_at) > 1:
        miss.append(
            f"criterion table: rows name {len(judged_at)} judged heads "
            f"({', '.join(sorted(x[:12] for x in judged_at))}); qc and the review judge one "
            "head: run just qc, naming every criterion the lane builds, and the review on one "
            "integrated head"
        )
    if judged and specs:
        miss += qc_insufficient(s.qc.get(judged, {}), judged, set(specs))
    return miss, t, rows, judged


def judged_proof(
    s: Snapshot, lines: list[str], judged: str | None, resolved: dict[str, str], *, no_crit: bool
) -> tuple[str | None, str | None, list[str]]:
    """(the judged head, its proof line to the PR head, the gaps): with no criterion the
    review verdict's head, or the PR head past a resolved merge; the Judged line names its proof
    (spec #lanes-one-head)."""
    head = s.head
    miss: list[str] = []
    jl = field(lines, "Judged")
    if no_crit:  # no qc: the review verdict's head is the judged head (spec #lanes-one-head)
        judged, why = verdict_head(lines, s.comments, s.commits, head, s.pr)
        miss += [why] if why else []
        # a resolved merge after it: the PR head is judged, the review verdict kept below by its
        # resolution verdict; a refused proof leaves it (named by the proof below)
        if judged and resolved:
            plain = ProofAsk(judged, head)
            if not isinstance(s.proofs.get(plain), ProofError) and _proved(s, plain)[1]:
                kept = ProofAsk(judged, head, resolved=tuple(resolved.items()))
                if not isinstance(s.proofs.get(kept), ProofError) and not _proved(s, kept)[1]:
                    judged = head.lower()
    if not judged:
        return None, None, miss
    proof, why = _proved(s, ProofAsk(judged, head))
    miss += [f"Judged: {w}" for w in why]
    if (
        proof
        and (not no_crit or jl or judged != head.lower())
        and (not jl or jl[1].strip("`") != proof)
    ):
        miss.append(
            f"Judged: {'names ' + repr(jl[1]) if jl else 'missing'}; add the check's proof line "
            f"`Judged: {proof}`"
        )
    return judged, proof, miss


def built_ids(s: Snapshot, lines: list[str], *, no_crit: bool) -> tuple[list[str], set[str]]:
    """(Built's gaps, the ids it lists): exactly the status files' built with this PR, each in
    a `qc: built` commit of the PR (docs/adr/0022)."""
    pr, specs = s.pr, s.specs
    miss: list[str] = []
    built: set[str] = set()
    b = field(lines, "Built")
    if not b:
        miss.append("Built: missing; add `Built: <ids qc flipped to built>` (or `Built: none`)")
    elif b[1].strip("`").lower() != "none":
        for tok in filter(None, re.split(r"[\s,]+", b[1])):
            cid, why = resolve(tok, specs)
            if cid:
                built.add(cid)
            else:
                miss.append(f"Built: {why}")
    status = {
        f"{sl}#{k}"
        for sl, cr in specs.items()
        for k, v in cr.items()
        if v.get("status") == "built" and v.get("pr") == pr
    }
    if b and built != status:
        miss.append(
            f"Built: lists {' '.join(sorted(built)) or 'none'}, the status files hold built with "
            f"PR #{pr}: {' '.join(sorted(status)) or 'none'}; list exactly those (never edit the "
            "status file by hand)"
        )
    qc = [QC_COMMIT.match(sj) for _, sj in s.commits]
    qc_ids = {x for q in qc if q for x in q.group(1).split() if x != "(none)"}
    unpassed = sorted(c for c in built if c.split("#", 1)[1] not in qc_ids)
    if no_crit:
        pass  # builds no criterion: no qc run, no qc commit
    elif not any(qc):
        miss.append(
            f"Built: no `qc: built` commit on PR #{pr}; run just qc on the lane head "
            "(docs/adr/0022)"
        )
    elif unpassed:  # a subset: a later qc run may reset an earlier pass to planned
        miss.append(
            f"Built: {' '.join(unpassed)} in no `qc: built` commit of PR #{pr} (they passed "
            f"{' '.join(sorted(qc_ids)) or 'none'}); built only by just qc: run just qc on the "
            "head for them, never edit the status file by hand"
        )
    return miss, built


def failed(s: Snapshot, lines: list[str]) -> tuple[list[str], dict[str, str]]:
    """(Failed's gaps, {criterion: triage} it lists): `Failed: none`, or one `- <id>: <triage>`
    line per failed criterion (spec #delivery-qa-triage)."""
    miss: list[str] = []
    fails: dict[str, str] = {}
    f = field(lines, "Failed")
    if not f:
        miss.append(
            "Failed: missing; add `Failed: none`, or `Failed:` then one `- <id>: <triage>` line "
            "per failed criterion"
        )
    elif f[1].lower() not in ("none", ""):
        miss.append(
            f"Failed: {f[1]!r}; write `Failed: none`, or `Failed:` then one `- <id>: <triage>` "
            "line per failed criterion"
        )
    elif f[1] == "":
        for ln in lines[f[0] + 1 :]:
            fm = re.match(r"\s*[-*]\s+([^:\s]+):?\s*(.*)$", ln)
            if not fm:
                break
            cid, why = resolve(fm.group(1), s.specs)
            if not cid:
                miss.append(f"Failed: {why}")
                continue
            fails[cid] = fm.group(2).strip()
            if not fails[cid]:
                miss.append(
                    f"Failed: {cid} has no triage; add `- {cid}: <repair ticket, judging fix, or "
                    "outside the lane and why>` (spec #delivery-qa-triage)"
                )
        if not fails:
            miss.append(
                "Failed: empty list; write `Failed: none` or one `- <id>: <triage>` line per "
                "failed criterion"
            )
    return miss, fails


def rows_against(rows: dict[str, str], built: set[str], fails: dict[str, str]) -> list[str]:
    """The criterion rows' gaps against Built and Failed: a row each, pass in Built, fail
    triaged and not built."""
    miss = [
        f"criterion row {cid}: missing (it is in Built); add `| {cid} | pass | judged <sha> | "
        "<evidence> |`"
        for cid in sorted(built - rows.keys())
    ]
    miss += [
        f"criterion row {cid}: missing (it is in Failed); add `| {cid} | fail | judged <sha> "
        "| <evidence> |`"
        for cid in sorted(fails.keys() - rows.keys())
    ]
    for cid, v in sorted(rows.items()):
        if v == "pass" and cid not in built:
            miss.append(
                f"criterion row {cid}: pass but not in Built; qc flips each pass to built, so "
                "rerun just qc or correct the row"
            )
        if v == "fail" and cid not in fails:
            miss.append(
                f"criterion row {cid}: fail with no triage; add `- {cid}: <triage>` under Failed "
                "(spec #delivery-qa-triage)"
            )
        if v == "fail" and cid in built:
            miss.append(f"criterion row {cid}: fail but in Built; rerun just qc on it")
    return miss


def sources(s: Snapshot, rows: dict[str, str], judged: str | None) -> list[str]:
    """Shown on a pass: each row's decision source, the latest qc result at the judged head
    (quality spec #qc-results)."""
    if not rows or not judged:
        return []
    latest = s.qc.get(judged, {})
    return [
        (
            f"Decision sources (the latest qc result at the judged head {judged[:12]}; quality "
            "spec #qc-results):"
        ),
        *(
            f"- {cid}: {latest[cid][0].get('decision') or 'none named'}"
            if cid in latest
            else f"- {cid}: no qc result at the judged head"
            for cid in sorted(rows)
        ),
    ]


def review(  # noqa: C901  one branch per verdict gap, in the order printed
    s: Snapshot, lines: list[str], judged: str | None, resolved: dict[str, str]
) -> tuple[list[str], list[str]]:
    """(the gaps of the Review verdict and Reviewed lines, the review's check classes): this PR's
    marker comment, on the JUDGED head or one the head proof carries to it, clear, with usable
    check classes and no proxy (docs/adr/0008)."""
    pr, head = s.pr, s.head
    miss: list[str] = []
    review_checks: list[str] = []
    rproof: str | None = None
    rwhy: list[str] = []
    rv = field(lines, "Review verdict")
    url = rv[1].strip("<>` ") if rv else ""
    m = COMMENT_URL.fullmatch(url)
    if not rv:
        miss.append(
            f"Review verdict: missing; run `octo-feather-lane verdict {pr} "
            f"{(judged or head)[:12]} <report>` and add `Review verdict: <the URL it prints>`"
        )
    elif not m or int(m.group(2)) != pr:
        miss.append(
            f"Review verdict: {url or 'empty'} is not a comment on PR #{pr}; link the URL "
            "`octo-feather-lane verdict` printed"
        )
    else:
        c = next((c for c in s.comments if c.url.endswith(f"#issuecomment-{m.group(3)}")), None)
        cb = c.body if c else ""
        hdr = cb.split("\n### Findings", 1)[0]  # the helper's own header, never the quoted report
        ch = HEAD_LINE.search(hdr)
        cvs = verdicts(hdr)
        cv = cvs[-1] if len(set(cvs)) == 1 else None
        rh = str(ch.group(1)).lower() if ch else None
        rat = [oid.lower() for oid, _ in s.commits if rh and oid.lower().startswith(rh)]
        if judged and cb.lstrip().startswith(MARKER) and len(rat) == 1 and rat[0] != judged:
            # reviewed before the judged head
            rproof, rwhy = _proved(
                s,
                ProofAsk(
                    rat[0],
                    judged,
                    at="reviewed head",
                    kept="the review verdict",
                    resolved=tuple(resolved.items()),
                    rerun=(
                        f"review {judged[:12]} afresh in full, then `octo-feather-lane verdict "
                        f"{pr} {judged[:12]} <report>`"
                    ),
                ),
            )
        if c is None:
            miss.append(
                f"Review verdict: comment {m.group(3)} not on PR #{pr}; link the URL "
                "`octo-feather-lane verdict` printed"
            )
        elif not cb.lstrip().startswith(MARKER):
            miss.append(
                f"Review verdict: {url} is not a verdict comment (no marker); post it with "
                "`octo-feather-lane verdict`"
            )
        elif judged and (not ch or not judged.startswith(ch.group(1).lower())) and not rproof:
            miss += [f"Review verdict: {w}" for w in rwhy] or [
                (
                    f"Review verdict: the comment names head {ch.group(1) if ch else 'none'}, "
                    f"not the judged head {judged[:12]}; review {judged[:12]}, then "
                    f"`octo-feather-lane verdict {pr} {judged[:12]} <report>`"
                )
            ]
        elif cv != "clear":
            miss.append(
                f"Review verdict: {cv or 'none or conflicting'}, not clear; fix the blocking "
                "findings, qc and review again"
            )
        else:
            review_checks, why = check_lines(hdr)
            proxy = [c for c in review_checks if c.endswith("| class: proxy")]
            if why:
                miss.append(
                    "Review verdict: the comment carries no usable check classification "
                    f"({why[0]}): have the review report hold {CHECK_FORM}, then "
                    f"`octo-feather-lane verdict {pr} {(judged or head)[:12]} <report>`"
                )
            elif proxy:
                miss.append(
                    f"Review verdict: clear with a proxy check ({proxy[0]}): a proxy check blocks "
                    "(docs/adr/0008); delete or replace it, review again, and post the verdict "
                    "with `octo-feather-lane verdict`"
                )
    rl = field(lines, "Reviewed")
    if rproof and (not rl or rl[1].strip("`") != rproof):
        miss.append(
            f"Reviewed: {'names ' + repr(rl[1]) if rl else 'missing'}; add the check's proof "
            f"line `Reviewed: {rproof}`"
        )
    return miss, review_checks


# --- the rules' readers of the section, the comments and the commits ---


def section(body: str) -> list[str] | None:
    lines = (body or "").replace("\r\n", "\n").split("\n")
    for i, ln in enumerate(lines):
        if re.fullmatch(r"##\s+merge ask\s*", ln.strip(), re.IGNORECASE):
            end = next(
                (j for j in range(i + 1, len(lines)) if re.match(r"#{1,2}\s", lines[j])), len(lines)
            )
            return [x.rstrip() for x in lines[i:end]]
    return None


def field(lines: list[str], name: str) -> tuple[int, str] | None:
    for i, ln in enumerate(lines):
        m = re.match(rf"\s*{name}:\s*(.*)$", ln, re.IGNORECASE)
        if m:
            return i, m.group(1).strip()
    return None


def resolve(
    tok: str, specs: dict[str, dict[str, dict[str, object]]]
) -> tuple[str | None, str | None]:
    """(spec#id, None) or (None, why)."""
    tok = tok.strip().strip("`*")
    if "#" in tok:
        slug, cid = tok.split("#", 1)
        slug = re.sub(r"\.spec\.html$", "", slug.split("/")[-1])
        if slug not in specs:
            return None, (
                f"{tok}: spec {slug} has no --status file (pass --status "
                f"docs/specs/{slug}.status.json)"
            )
        return (
            (f"{slug}#{cid}", None)
            if cid in specs[slug]
            else (None, f"{tok}: no criterion {cid} in {slug}'s status file")
        )
    hits = [sl for sl in specs if tok in specs[sl]]
    if len(hits) == 1:
        return f"{hits[0]}#{tok}", None
    return None, (
        f"{tok}: in {' and '.join(hits)}; write <spec>#{tok}"
        if hits
        else f"{tok}: no such criterion in the --status files"
    )


def judged_sha(
    cell: str, commits: list[tuple[str, str]], head: str, pr: int
) -> tuple[str | None, str | None]:
    """(the PR commit a row's judged cell names, None) or (None, why)."""
    m = JUDGED.fullmatch(cell.strip())
    if not m:
        return None, (
            f"judged {cell or 'empty'!r}; write `judged <sha>`, the head qc and the review judged "
            "(7+ hex)"
        )
    sha = m.group(1).lower()
    at = [oid for oid, _ in commits if oid.lower().startswith(sha)]
    if len(at) != 1:
        return None, (
            f"judged {sha} is {'ambiguous among' if at else 'not a commit of'} PR #{pr}; name the "
            "head qc and the review judged (the sha in its `qc: built ... (judged <sha>)` commit, "
            f"or the PR head {head[:12]})"
        )
    return at[0].lower(), None


def no_criterion(
    lines: list[str],
    commits: list[tuple[str, str]],
    specs: dict[str, dict[str, dict[str, object]]],
    pr: int,
) -> bool:
    """The lane builds no criterion (spec #lanes-one-head): `Built: none`, `Failed: none`, no
    criterion row, no `qc: built` commit on the PR and no status entry built with it."""
    b, f = field(lines, "Built"), field(lines, "Failed")
    if not b or b[1].strip("`").lower() != "none" or not f or f[1].strip("`").lower() != "none":
        return False
    t = next(
        (
            i
            for i, ln in enumerate(lines)
            if re.fullmatch(r"\|\s*criterion\s*\|.*\|", ln.strip(), re.IGNORECASE)
        ),
        None,
    )
    for ln in lines[t + 1 :] if t is not None else []:
        if not ln.strip().startswith("|"):
            break
        if not all(re.fullmatch(r":?-+:?", c.strip()) for c in ln.strip().strip("|").split("|")):
            return False
    if any(QC_COMMIT.match(sj) for _, sj in commits):
        return False
    return not any(
        v.get("status") == "built" and v.get("pr") == pr
        for cr in specs.values()
        for v in cr.values()
    )


def verdict_head(
    lines: list[str], comments: list[Comment], commits: list[tuple[str, str]], head: str, pr: int
) -> tuple[str | None, str | None]:
    """(the PR commit the linked review verdict comment names as its Head, None), or (None,
    why); (None, None) when there is no such comment to read (the Review verdict check names
    that)."""
    rv = field(lines, "Review verdict")
    m = COMMENT_URL.fullmatch(rv[1].strip("<>` ")) if rv else None
    c = next((c for c in comments if m and c.url.endswith(f"#issuecomment-{m.group(3)}")), None)
    cb = c.body if c else ""
    if not cb.lstrip().startswith(MARKER):
        return None, None
    ch = HEAD_LINE.search(cb.split("\n### Findings", 1)[0])
    at = [oid for oid, _ in commits if ch and oid.lower().startswith(ch.group(1).lower())]
    if len(at) != 1:
        return None, (
            f"Review verdict: the comment names head {ch.group(1) if ch else 'none'}, not one "
            f"commit of PR #{pr}: review the PR head {head[:12]}, then `octo-feather-lane verdict "
            f"{pr} {head[:12]} <report>`"
        )
    return at[0].lower(), None


def qc_insufficient(
    latest: dict[str, tuple[dict[str, object], str]], judged: str, specs: set[str]
) -> list[str]:
    """Each criterion of the SPECS (slugs) whose LATEST result in the qc reports at the JUDGED
    head is insufficient evidence (quality spec #qc-results), named with what is missing and
    its report."""
    out: dict[str, tuple[str, str]] = {}  # <spec>#<id>: (what is missing, report), or ("", report)
    for cid, (r, name) in latest.items():
        if cid.split("#", 1)[0] in specs:
            short = r.get("verdict") == "insufficient evidence"
            missing = "; ".join(map(str, cast("list[object]", r.get("missing") or [])))
            out[cid] = ((missing or "evidence incomplete") if short else "", name)
    return [
        f"criterion {cid}: insufficient evidence at the judged head {judged[:12]} ({why}; qc "
        f"report {name}): never triaged; make what is missing available, then rerun just qc on "
        "it until it gives pass or fail"
        for cid, (why, name) in sorted(out.items())
        if why
    ]


def resolution_verdicts(comments: list[Comment]) -> dict[str, str]:
    """{merge sha: URL} of each clear `verdict --resolution` comment among COMMENTS (spec
    #lanes-one-head)."""
    out: dict[str, str] = {}
    for c in comments:
        rm = RESOLUTION_HEAD.match(c.body.lstrip())
        hdr = c.body.split("\n### Findings", 1)[0]
        vs = verdicts(hdr)
        if rm and set(vs) == {"clear"} and not check_lines(hdr)[1]:
            out[rm.group(1)] = c.url
    return out


def judgment_lines(comments: list[Comment]) -> list[str]:
    """One line per judgment comment on the PR, for the owner beside the review verdict. Read
    for display only: no gate reads a judge's answer (spec judgment#rule-advisory)."""
    out: list[str] = []
    for c in comments:
        b = c.body.lstrip()
        m = re.match(r"<!-- octo-feather-model-judgment: ([\w.-]+) -->", b)
        if not m:
            continue
        hdr = b.split("\n### ", 1)[0].split("\n")
        f = {
            k: v.strip()
            for k, v in (ln.split(":", 1) for ln in hdr if ":" in ln)
            if k in JUDGMENT_FIELDS
        }
        url = c.url or "?"
        if any(k not in f for k in JUDGMENT_FIELDS) or not f["Judgment"].startswith(
            "model judgment"
        ):
            out.append(
                f"- {m.group(1)}: unreadable judgment comment, ignored (rerun octo-feather-lane "
                f"judge): {url}"
            )
            continue
        out.append(
            f"- {f['Question']}: {f['Answer']}, confidence {f['Confidence']} (model judgment by "
            f"{f['Model']}, advisory: no gate reads it; calibration: {f['Calibration']}; PR head "
            f"{f['PR head'][:12]}, review head {f['Review head'][:12]}): {url}"
        )
    return out


# --- the review comment, the code review's report and the PR's commits, as written (issue #48) ---

MARKER = "<!-- octo-feather-review-verdict -->"
# The one comment per reviewed resolution of a main merge, naming the merge (issue-lifecycle
# #lanes-one-head); octo-feather-lane's RESOLUTION_MARKER writes it.
RESOLUTION_HEAD = re.compile(r"^<!-- octo-feather-review-resolution: ([0-9a-f]{40}) -->")
SHA = re.compile(r"[0-9a-fA-F]{7,40}")
COMMENT_URL = re.compile(r"https://github\.com/([^/\s]+/[^/\s]+)/pull/(\d+)#issuecomment-(\d+)")
VERDICT_LINE = re.compile(r"^Verdict: (clear|blocking)\s*$")
HEAD_LINE = re.compile(r"^Head:\s*`?([0-9a-fA-F]{7,40})`?\s*$", re.MULTILINE)
QC_COMMIT = re.compile(r"^qc: built (.*?)(?: \(judged ([0-9a-f]+)\))?\s*$")
JUDGED = re.compile(r"`?(?:judged\s+)?`?([0-9a-fA-F]{7,40})`?", re.IGNORECASE)


CHECK_LINE = re.compile(r"^Check:[ \t]*(.*?)\s*$")
CHECK_SHAPE = re.compile(
    r"`?([^`\s|]+?)`?:\s+(\S[^|]*?)\s*\|\s*reads:\s*(\S[^|]*?)\s*\|\s*class:\s*(\S+)"
)
# The rule ends on its owner in parentheses, non-empty: `<rule> (<owner>)` (docs/adr/0008: the
# owned rule, never the docstring).
OWNED = re.compile(r"(\S.*?)\s+\(([^()]*[^()\s][^()]*)\)")
CHECKS_LINE = re.compile(r"^Checks:[ \t]*(.*?)\s*$")
CHECK_FORM = (
    "`Checks: none` when the diff adds or changes nothing to classify (docs/adr/0008, Who builds "
    "what), else one line each `Check: <path>: <rule> (<owner>) | reads: <what it reads> | "
    "class: exact|proxy` (docs/adr/0008)"
)
JUDGMENT_FIELDS = (
    "Judgment",
    "Question",
    "Model",
    "Answer",
    "Confidence",
    "Calibration",
    "PR head",
    "Review head",
)
ROW_CELLS = 4  # criterion | qc verdict | judged <sha> | evidence
NO_STATUS = "name the lane's status file: --status docs/specs/<slug>.status.json (once per spec)"


# The Markdown this module reads, no more. scope: .agents/skills/code-review/SKILL.md (Verdict
# step) for a verdict report; scope: octo-feather-lane --help (ticket) for a ticket body.
FENCE = re.compile(r"`{3,}|~{3,}")


def markdown(text: str, *, comments: bool = False) -> list[tuple[str, str]]:
    """Each line of TEXT with its kind, `fence`, `quote`, `comment` or `text`, in the scope
    above. With COMMENTS a line holding only comment is `comment` and any other line comes with
    its comments cut out."""
    out: list[tuple[str, str]] = []
    fence: str | None = None
    quote, cmt = False, False  # cmt: an HTML comment is open
    for ln in text.replace("\r\n", "\n").split("\n"):
        if fence:
            s = ln.rstrip(" \t")
            if len(s) >= len(fence) and s == fence[0] * len(s):
                fence = None
            out.append((ln, "fence"))
            continue
        was, t = cmt, ln
        if comments:
            t, cmt = cut_comments(ln, open_=cmt)
            if (was or t != ln) and not t.strip():
                out.append((ln, "comment"))
                continue
        if not was and (f := FENCE.match(t)):
            fence, quote = f.group(0), False
            out.append((ln, "fence"))
            continue
        quote = (quote or (not was and t.startswith(">"))) and bool(t.strip())
        out.append((t, "quote" if quote else "text"))
    return out


def cut_comments(ln: str, *, open_: bool) -> tuple[str, bool]:
    """(L with its HTML comments cut, whether one is open at its end), OPEN_ if one is open at
    its start."""
    out, i = "", 0
    while True:
        if open_:
            e = ln.find("-->", i)
            if e < 0:
                return out, True
            i, open_ = e + 3, False
        s = ln.find("<!--", i)
        if s < 0:
            return out + ln[i:], False
        out, i, open_ = out + ln[i:s], s + 4, True


def outside(text: str) -> list[str]:
    """The lines markdown() reads as text, in order."""
    return [ln for ln, kind in markdown(text) if kind == "text"]


def verdicts(text: str) -> list[str]:
    """Every `Verdict: clear|blocking` line in the verdict reader's scope, in order (scope:
    .agents/skills/code-review/SKILL.md (Verdict step))."""
    # column 0: `> Verdict:` never matches
    return [m.group(1) for ln in outside(text) if (m := VERDICT_LINE.match(ln))]


def check_lines(text: str) -> tuple[list[str], list[str]]:
    """(the report's check classification as normalized lines, why it is unusable)
    (docs/adr/0008)."""
    checks: list[tuple[str, str]] = []
    nones: list[str] = []
    why: list[str] = []
    for ln in outside(text):
        if m := CHECKS_LINE.match(ln):
            nones.append(m.group(1))
        elif m := CHECK_LINE.match(ln):
            s = CHECK_SHAPE.fullmatch(m.group(1))
            if not s:
                why.append(
                    f"check line `{ln.strip()}` is not `Check: <path>: <rule> (<owner>) | "
                    "reads: <what it reads> | class: exact|proxy`"
                )
                continue
            path, rule, reads, cls = s.groups()
            o = OWNED.fullmatch(rule)
            if not o:
                why.append(
                    f"check line for {path} names no owner: write its rule as stated where it "
                    "is owned, then the owner in parentheses, `<rule> (<spec criterion, ADR or "
                    "owner ruling>)` (docs/adr/0008)"
                )
                continue
            rule = f"{o.group(1)} ({o.group(2).strip()})"
            if cls.lower() not in ("exact", "proxy"):
                why.append(
                    f"check line for {path} has class {cls!r}; write `class: exact` or "
                    "`class: proxy` (docs/adr/0008)"
                )
                continue
            checks.append(
                (f"Check: {path}: {rule} | reads: {reads} | class: {cls.lower()}", cls.lower())
            )
    bad_none = [v for v in nones if v.strip("`").lower() != "none"]
    if bad_none:
        why.append(
            f"`Checks: {bad_none[0]}`; `Checks:` takes only `none`; name each check on its own "
            "`Check:` line"
        )
    if not checks and not nones and not why:
        why.append(f"report classifies no check: add {CHECK_FORM}")
    if checks and nones:
        why.append(
            "report has `Checks: none` and `Check:` lines; keep the `Check:` lines, one per "
            "added or changed check"
        )
    lines = [c for c, _ in checks] or (["Checks: none"] if nones and not bad_none else [])
    return lines, why


def head_matches(named: str, head: str) -> bool:
    return bool(SHA.fullmatch(named)) and head.lower().startswith(named.lower())
