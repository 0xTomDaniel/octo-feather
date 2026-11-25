#!/usr/bin/env python3
"""The merge ask's rules: a PR's facts read once into a Snapshot, judged by a pure check.

The design: issue #1146 (its design comment); the rules: issue-lifecycle spec #gates-pr-line,
#lanes-one-head (the checks, the judged head), #acceptance-merge-ask-evidence,
#acceptance-merge-ask-no-criterion, #delivery-qa-triage, quality spec #qc-results, the merge ask
(octo-feather-lane --help, merge-ask, its Checks line). Imported by scripts/octo-feather-lane
(`merge-ask` builds one snapshot, checks it and prints check's groups around its own `Checks:
missing` item; `verdict` and `fields` share the review comment's and the report's parsers
below, and `verdict` its review rounds: Round, posted_rounds, check_set); how a command finds
this module: the docstring of scripts/correction_lanes.py. Standard
library only (AGENTS.md Rules, kit scripts). The head proof (#lanes-one-head), the carried
checks, the full pass and the gate time (#lanes-checkpoints) are judged here too (#1150).

Interface:

    snapshot(pr, repo, files, read, qc_dir, trend, err=..., lanes, base=None) -> Snapshot
        The one reader: the status FILES (--status), then PR in REPO (None: this directory's)
        through READ, the command's reader ((gh pr view's JSON: body, headRefName, headRefOid,
        statusCheckRollup, baseRefName, comments; the PR's commits or why they are unread)),
        what the tracker skill's key-from-branch and pr-line print for its head branch
        (ParentLine) or its refusal (NoParent), the head's GitHub check facts (Checks), each read
        only when its rule needs it, a failed read kept as Unread, and the qc reports in QC_DIR
        at each commit of the PR. An unreadable status file raises ERR. Spec #gates-merge-order
        (Order): every other open PR on the PR's base branch (gh pr list, its answer validated
        against schemas/gh-pr-list.schema.json), its head fetched (git fetch origin
        pull/N/head) when this repo lacks it, git merge-tree of the two heads, the
        octo-feather-qa --verdict pins its qc.toml demos name at its head (the qc.toml
        validated by octo-feather-contract; one that fails is not read), and that command's
        lines for them at the base (pr_base: BASE, --base, else origin/<base branch>) and at the
        base merged with the head (a commit-tree, no ref moved), each run in a scratch detached
        worktree. The lane's git facts over the base (Git: each PR commit's parents, subject,
        files or merge facts, its walk, the lane diff at each when the PR holds a merge), the
        full pass's (Gate: octo-feather-gate config and passed, read along the lane until one
        carries over), the gate time's (Trend: TREND, the state dir's check-runs.jsonl, the
        head's history, gate-budget.toml at the head) and the judged head's check runs, read
        only when a check skipped on the head and a Judged proof carries it. A correction lane's
        replay (Replay, #1226; read only when the verdict comment lists a Check line): its parent
        issue through the tracker skill's issue-view, the clean sample from LANES (the state
        dir's lanes/) and each `## Replay` row's command run at the head, each in its own qc
        sandbox over one GitHub snapshot (_runs; never outside it). The lane's behaviour-neutral
        opt-outs (Snapshot.optouts, #1259): the kit's check-behavior-smoke run here, its lines.
        The code owners files at the head and the merge base (Owned, #1260; _code_owners): their
        lines, the repository owner's login (REPO, else gh repo view; read only when a file
        exists) and the lane's changed paths each gives them, matched by git check-ignore
        (_owned).
    check(s) -> Ask
        Pure, no I/O. Each refusal line the merge ask prints for S, in order, by rule, in the
        parts the command's own item goes between; none when S passes; with what a passing ask
        prints; Ask.order, the merge-order lines (spec #gates-merge-order), and Ask.gate_time,
        never a gap. Ask.tier (Tier, spec #gates-tiers), on any Ask: the tier, its reasons and
        whom the merge waits for (the block's form and the reasons: octo-feather-lane --help,
        merge-ask). Its spec calls' reads (snapshot, _calls): each `*.calls.jsonl` the diff from
        the merge base to the head changes, at both (git show), and each added call's ruling's
        created_at (gh api).

Shared with octo-feather-lane's other commands: bad_checks (lane status), check_runs, git,
resolution_files (verdict, resolution), full_pass (ci-start: its reads, then its rule), and the
gate time's lines (report: budget_parse, budget_lines, passed_full, numbered_jsonl, stamp), each
read raising the ERR its caller passes. The plain gh reads (ci_workflows) and head_matches come
from scripts/tracker_calls.py.
"""

__all__ = [  # check's interface, then the helpers octo-feather-lane's other commands share
    "Ask",
    "Checks",
    "Comment",
    "Commit",
    "Gate",
    "Git",
    "Kind",
    "Merge",
    "NoParent",
    "NoWorkflow",
    "Order",
    "ParentLine",
    "Pin",
    "Policy",
    "Reported",
    "Round",
    "Sibling",
    "Snapshot",
    "Tier",
    "Trend",
    "Unread",
    "Workflows",
    "bad_checks",
    "budget_lines",
    "budget_parse",
    "check",
    "check_runs",
    "check_set",
    "full_pass",
    "git",
    "numbered_jsonl",
    "passed_full",
    "posted_rounds",
    "pr_base",
    "resolution_files",
    "snapshot",
    "stamp",
]

import contextlib
import dataclasses
import datetime as dt
import functools
import hashlib
import importlib.machinery
import importlib.util
import io
import json
import os
import re
import shlex
import statistics
import subprocess
import sys
import tempfile
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, NamedTuple, ParamSpec, Protocol, TypedDict, TypeVar, cast

import tomllib
from correction_lanes import MARK, Refused, lane_logs, lane_record, quoted
from tracker_calls import KIT, ci_workflows, gh, head_matches, tracker, utc

# GitHub's closing keywords: a PR body line with one closes that GitHub issue at merge, named
# as #N, as owner/repo#N or by the issue URL.
CLOSES = re.compile(
    r"\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\b:?\s+"
    r"(?:[\w.-]+/[\w.-]+#|https?://(?:www\.)?github\.com/[\w.-]+/[\w.-]+/issues/|#)(\d+)\b",
    re.IGNORECASE,
)

# GitHub's answer to rules/branches on a plan without rulesets, as gh prints it on stderr `gh: <it>
# (HTTP 403)` (private repo, free plan; 0xTomDaniel/exosurface read 2026-11-05): no ruleset can be
# in force.
NO_RULESETS = "Upgrade to GitHub Pro or make this repository public to enable this feature."


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


# --- the checks (spec #lanes-one-head; octo-feather-lane --help, merge-ask Checks line) ---


@dataclass(frozen=True)
class Unread:
    """A read that failed: WHY, its refusal as worded."""

    why: str


@dataclass(frozen=True)
class Reported:
    """Checks reported on the head: the PR's ROLLUP (gh pr view statusCheckRollup, never empty)
    and, read only when it names a check (name and workflow) twice, RUNS: the head's check runs
    (REST check-runs) and its workflow runs (actions/runs as gh printed them); None otherwise."""

    rollup: list[dict[str, object]]
    runs: tuple[list[dict[str, object]], str] | Unread | None


@dataclass(frozen=True)
class Workflows:
    """No check reported on the head, and the workflow FILES under .github/workflows there."""

    files: list[str]


@dataclass(frozen=True)
class Policy:
    """The BASE branch's required-check policy: gh api's branches/BASE (BRANCH) and
    rules/branches/BASE (RULES), each (its JSON, '') or (None, why it could not be read); RULES
    read only when BRANCH names its required checks, else None."""

    base: str
    branch: tuple[object, str]
    rules: tuple[object, str] | None


@dataclass(frozen=True)
class NoWorkflow:
    """No check reported and no workflow file at the head: the base's POLICY, or why gh could not
    read it."""

    policy: Policy | Unread


@dataclass(frozen=True)
class Checks:
    """The HEAD commit's checks in REPO (None: this directory's): reported, or none reported and
    then the workflow files at it, none and the base's policy, or why the files could not be read
    (Unread)."""

    head: str
    repo: str | None
    at_head: Reported | Workflows | NoWorkflow | Unread


@dataclass(frozen=True)
class Comment:
    """A PR comment as gh printed it: its URL and BODY ("" for none)."""

    url: str
    body: str


# --- the head proof, the full pass and the gate time (#1150; spec #lanes-one-head,
# #lanes-checkpoints) ---

MERGE_PARENTS = 2  # a merge of main has two parents (spec #lanes-one-head)


@dataclass(frozen=True)
class Merge:
    """A two-parent merge's facts: ONTO, its second parent is an ancestor of the base; CONFLICT,
    git merge-tree of its parents conflicts; BEYOND, the files it changes beyond git's automatic
    merge (git diff --name-only, split on whitespace), None when its tree is that merge's;
    RESOLUTION, the files its resolution changed (resolution_files), read only when it conflicts
    or changes something beyond."""

    onto: bool
    conflict: bool = False
    beyond: tuple[str, ...] | None = None
    resolution: tuple[str, ...] = ()


@dataclass(frozen=True)
class Commit:
    """A commit of the PR: its PARENTS, SUBJECT (git log %s), the FILES a one-parent commit
    changes (git diff-tree), a two-parent merge's MERGE facts."""

    parents: tuple[str, ...]
    subject: str
    files: frozenset[str] = frozenset()
    merge: Merge | None = None


@dataclass(frozen=True)
class Git:
    """The lane's git facts over BASE, read once. HERE: the PR head is a commit in this repo.
    TOPO: `git rev-list --topo-order HEAD ^BASE`, Unread when git refused it. COMMITS: each of those
    commits; WALKS, each one's own `git rev-list --reverse C ^BASE` (git's order, oldest first,
    which every walk between two of them keeps; read only when the PR holds a merge, else the
    one chain's prefix); DIFFS, each one's lane diff (its own diff from its merge base with
    BASE, {path: its hunks (_lane_diff)}, status files aside), read only when the PR holds a merge.
    STATUS: the --status files relative to the repo's top, Unread naming one outside it."""

    base: str
    here: bool = True
    topo: tuple[str, ...] | Unread = ()
    commits: dict[str, Commit] = dataclasses.field(default_factory=dict)
    walks: dict[str, tuple[str, ...]] = dataclasses.field(default_factory=dict)
    diffs: dict[str, dict[str, str]] = dataclasses.field(default_factory=dict)
    status: frozenset[str] | Unread = frozenset()


@dataclass(frozen=True)
class Gate:
    """The full pass's facts (octo-feather-gate --help): CONFIG, `config HEAD`'s exit and identity
    fields ({} when unreadable); PASSES, `passed C`'s record ({} for none) of each lane commit
    read, the head first, then the topo order, up to the first that carries over."""

    config: tuple[int, dict[str, object]]
    passes: dict[str, dict[str, object]] = dataclasses.field(default_factory=dict)


@dataclass(frozen=True)
class Trend:
    """The gate time's facts: PATH, the state dir's check-runs.jsonl, and its ROWS
    (numbered_jsonl; None: no file); HISTORY, the head's last 1000 commits; BUDGET,
    gate-budget.toml at the head (None: no such file); NOW, when they were read. A failed read:
    Unread."""

    path: Path
    rows: tuple[list[tuple[int, dict[str, object]]], list[int]] | Unread | None
    history: frozenset[str] | Unread
    budget: str | Unread | None
    now: dt.datetime


# --- the merge order (#1152, spec #gates-merge-order): the open PRs this merge sets back ---


@dataclass(frozen=True)
class Pin:
    """A stored eval run an open PR's qc.toml demo pins (RUN_ID/SUITE/CASE, RUN), and the line
    octo-feather-qa --verdict printed for it at the base (MAIN) and at the base merged with this
    lane's head (MERGED)."""

    run: str
    main: str
    merged: str


@dataclass(frozen=True)
class Sibling:
    """Another open PR: NUMBER, head BRANCH, the files git merge-tree finds in conflict between its
    head and this lane's (CONFLICTS), and the runs its demos pin (PINS)."""

    number: int
    branch: str
    conflicts: list[str]
    pins: list[Pin]


@dataclass(frozen=True)
class Order:
    """The other open PRs on BASE (PRS, by number), and each read that failed (UNREAD), one line."""

    base: str
    prs: list[Sibling]
    unread: list[str]


@dataclass(frozen=True)
class Replayed:
    """A replay row's command as merge-ask ran it at the PR head in its own qc sandbox: its EXIT
    (None: it did not run) and its OUT, stdout then stderr; UNSERVED why the sandbox could not
    serve it ('' when it could), WROTE the writes the sandbox discarded (`<kind> <path>`)."""

    exit: int | None
    out: str
    unserved: str = ""
    wrote: tuple[str, ...] = ()


@dataclass(frozen=True)
class Replay:
    """A correction lane's replay facts (spec issue-lifecycle #lanes-correction, #1222): KEY its
    parent issue, CLS the class its title's marker (correction_lanes.MARK) names, PATHS the
    verdict's Check paths, FINDINGS the ids (`<lane> <at>`) of the finding lines its body and
    comments quote (correction_lanes.quoted), SAMPLE the clean lanes the fixed rule picks
    (_sample), RUNS each replayed row's sandboxed run, by its row, TABLE the PR body's `## Replay`
    rows and why a row is unreadable (_replay_table)."""

    key: str
    cls: str
    paths: tuple[str, ...]
    findings: tuple[str, ...]
    sample: tuple[str, ...]
    runs: "dict[Row, Replayed]"
    table: "tuple[list[Row], list[str]] | None" = None  # _replay_table's: None, no section


@dataclass(frozen=True)
class Owned:
    """A code owners file's facts at one end of the lane (spec #gates-tier-areas, #1260): FILE,
    the file GitHub reads (CODE_OWNERS, the first found), ` at the merge base <sha>` after it for
    the base's; OWNER, `@<login>` of the repository's owner; PATHS, each path the lane changes
    whose last matching line names OWNER, with that line's number and text; REFUSED, each line
    whose pattern git reads otherwise than GitHub (number, text, why), none matched when any is."""

    file: str
    owner: str
    paths: tuple[tuple[str, int, str], ...] = ()
    refused: tuple[tuple[int, str, str], ...] = ()


@dataclass(frozen=True)
class Snapshot:
    """A PR's facts, read once."""

    # the parent line (#1147): the PR's BODY, head BRANCH and the PARENT the tracker skill names
    body: str
    branch: str
    parent: ParentLine | NoParent
    # the checks (#1148): the head's CHECKS
    checks: Checks
    # the criterion, review and qc rules (#1149): PR number, HEAD (gh's headRefOid), its COMMITS
    # (sha, subject; newest first) or UNREAD, the gap naming why none were read; the SPECS,
    # {slug: criteria} of the --status files, NAMED when any was passed; the PR's COMMENTS; QC,
    # each PR commit's (lowercase sha) latest qc result per criterion (<spec>#<id>: (result,
    # report name))
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
    # the merge order (#1152): ORDER, the other open PRs on the base, None when not read
    order: Order | None = None
    # the head proof, the carried checks, the full pass and the gate time (#1150): the lane's
    # GIT facts, the full pass's GATE facts, the gate time's TREND, each None when not read (no
    # rule on it); RUNS, the judged head's check runs (check_runs) or why they are unread, None
    # when not read (none)
    git: Git | None = None
    gate: Gate | None = None
    trend: Trend | None = None
    runs: list[dict[str, object]] | Unread | None = None
    # the review rounds' chain (#1220, spec #lanes-one-head): FORK, git merge-base of the head
    # and the base, '' when not read
    fork: str = ""
    # the correction lane's replay (#1222): None when the lane is none or its verdict lists no
    # check
    replay: Replay | Unread | None = None
    # the lane's behaviour-neutral opt-outs (#1259): (commit, `Behaviour-neutral: <reason>`) each
    # as check-behavior-smoke prints them from FORK to the head, or why unread; None when not read
    optouts: list[tuple[str, str]] | Unread | None = None
    # the code owners files at the head and the merge base (#1260): None when neither has one
    owners: tuple[Owned, ...] | Unread | None = None
    # the lane's spec calls (#1258, spec #gates-tiers): CALLS, those its diff adds, read at the
    # head, and their rulings' times; Unread naming why not (no merge base among them)
    calls: "Calls | Unread | None" = None


@dataclass(frozen=True)
class Ask:
    """The merge ask's verdict on a Snapshot. Its gaps, each a refusal line, in six parts in the
    order printed: HEAD (the PR commits, parent line, section and Head; the command's `Checks:
    missing` follows), CHECKS (the Checks rules'), JUDGED (the criterion table to the Judged
    line), CARRIED (the checks skipped on the head, carried from the judged head), FULL (the
    full pass) and REVIEW (the review verdict to the criterion rows against Built and Failed);
    none when it passes. REFUSAL: why nothing can be judged (exit 1, no gap); ABORT: a read the
    full pass needs failed, the refusal alone (exit 1, no gap, no merge order). What a passing
    ask prints and the command reads: SECTION, the `## Merge ask` lines; JUDGED_HEAD and PROOF
    (its head proof line); CLASSES, the review's check classes; SOURCES, each row's decision
    source; JUDGMENTS, the model judgment comments (shown only); ORDER, the merge-order lines
    (shown only, spec #gates-merge-order, on any Ask); NO_CI, the no-CI fact's line on a pass,
    else ''; CURRENT, the head's checks after the current-head projection (the rollup when it
    could not be made); CARRIED_OK, a line per skipped check carried; TIER, the ask's tier
    (Tier, spec #gates-tiers: on any Ask check returns); GATE_TIME, the gate time
    lines (shown only, spec #lanes-checkpoints); ROUNDS, the verdict comment's review rounds, one
    line each, its check lines indented under it."""

    head: list[str]
    checks: list[str] = dataclasses.field(default_factory=list)
    no_ci: str = ""
    current: list[dict[str, object]] = dataclasses.field(default_factory=list)
    judged: list[str] = dataclasses.field(default_factory=list)
    review: list[str] = dataclasses.field(default_factory=list)
    refusal: str = ""
    section: list[str] = dataclasses.field(default_factory=list)
    judged_head: str | None = None
    proof: str | None = None
    classes: list[str] = dataclasses.field(default_factory=list)
    sources: list[str] = dataclasses.field(default_factory=list)
    judgments: list[str] = dataclasses.field(default_factory=list)
    order: list[str] = dataclasses.field(default_factory=list)
    carried: list[str] = dataclasses.field(default_factory=list)
    full: list[str] = dataclasses.field(default_factory=list)
    abort: str = ""
    carried_ok: list[str] = dataclasses.field(default_factory=list)
    gate_time: list[str] = dataclasses.field(default_factory=list)
    rounds: list[str] = dataclasses.field(default_factory=list)
    replay: str = ""  # the correction lane's `Replay:` line (#1222), '' for none
    tier: "Tier | None" = None  # the ask's tier (spec #gates-tiers), on any Ask check returns

    @property
    def gaps(self) -> list[str]:
        return [*self.head, *self.checks, *self.judged, *self.carried, *self.full, *self.review]


class _TrackerError(Exception):
    """A tracker script's refusal, kept as NoParent."""


class _Unread(Exception):  # noqa: N818 (a read that failed, kept as Unread)
    """A read's refusal, kept as Unread."""


class _Gap(Exception):  # noqa: N818 (a rule's refusal line, as merge-ask prints it)
    """A Checks rule's refusal line, raised where the moved code refused."""


def snapshot(  # noqa: PLR0913  each read's input, the command's reader among them
    pr: int,
    repo: str | None,
    files: list[str],
    read: Callable[[], tuple[dict[str, object], list[tuple[str, str]] | str]],
    qc_dir: Path,
    *,
    trend: Path,
    err: type[Exception],
    lanes: Path,
    base: str | None = None,
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
    rollup = cast("list[dict[str, object]]", view["statusCheckRollup"] or [])
    at = (
        _reported(head, rollup, repo)
        if rollup
        else _unreported(head, str(view["baseRefName"]), repo)
    )
    raw = cast("list[dict[str, object]]", view["comments"] or [])
    comments = [Comment(str(c.get("url") or ""), str(c.get("body") or "")) for c in raw]
    listed = commits if isinstance(commits, list) else []
    shas = {oid.lower() for oid, _ in listed} | {head.lower()}
    base_branch = str(view["baseRefName"] or "")
    order = _order(pr, head, base_branch or "main", pr_base(base_branch, base), repo)
    g = _git_facts(head, pr_base(base_branch, base), files, err)
    why = ""
    try:
        fork = git("merge-base", head, pr_base(base_branch, base), err=_Unread)[1].strip()
    except _Unread as e:
        fork, why = "", str(e)
    try:
        calls: Calls | Unread = _calls(head, fork) if fork else Unread(why)
    except _Unread as e:
        calls = Unread(str(e))
    s = Snapshot(
        body,
        branch,
        parent,
        Checks(head, repo, at),
        pr=pr,
        head=head,
        commits=listed,
        unread="" if isinstance(commits, list) else commits,
        specs=specs,
        named=bool(files),
        comments=comments,
        qc={sha: qc_latest(qc_dir, sha) for sha in sorted(shas)},
        order=order,
        git=g,
        gate=_gate_facts(g, head),
        trend=_trend(trend, head),
        fork=fork,
        optouts=_optouts(head, fork) if fork else Unread("no merge base of the head and the base"),
        owners=_code_owners(head, fork, repo),
        calls=calls,
    )
    # the judged head's check runs: read only when a check skipped on the head and a Judged proof
    # carries it (the rules' own judged head and proof, over the facts read above)
    a = _check(s)
    s = dataclasses.replace(s, replay=_replay(s, a.classes, repo, lanes))
    if a.refusal or a.abort or not _skipped(a.current) or not a.proof:
        return s
    if not a.judged_head or a.judged_head == head.lower():
        return s
    try:
        runs: list[dict[str, object]] | Unread = check_runs(
            a.judged_head, repo, "the judged head", err=_Unread
        )
    except _Unread as e:
        runs = Unread(str(e))
    return dataclasses.replace(s, runs=runs)


def pr_base(ref: str, base: str | None) -> str:
    """The base a PR's commits are read against: BASE (--base) when given, else REF, its base
    branch, on origin."""
    return base or f"origin/{ref or 'main'}"


def git(*args: str, ok: tuple[int, ...] = (0,), err: type[Exception]) -> tuple[int, str]:
    """git ARGS here: (exit, stdout); ERR naming the fix on another exit than OK's."""
    try:
        p = subprocess.run(
            ["git", *args],  # noqa: S607 (git from PATH)
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,
            check=False,
        )
    except FileNotFoundError:
        msg = "git not on PATH: install git"
        raise err(msg) from None
    if p.returncode not in ok:
        said = (p.stderr or p.stdout).strip().splitlines()
        msg = (
            f"git {' '.join(args[:2])} failed "
            f"({said[-1][:200] if said else f'exit {p.returncode}'}): run merge-ask in the lane "
            "worktree with the PR head and the base fetched (git fetch origin)"
        )
        raise err(msg)
    return p.returncode, p.stdout


def resolution_files(merge: str, *, err: type[Exception]) -> list[str]:
    """The files MERGE's resolution changed: what `git show --remerge-diff` prints for it
    (issue-lifecycle #lanes-one-head)."""
    out = git("show", "--remerge-diff", "--format=", "--name-only", "-z", merge, err=err)[1]
    return sorted(filter(None, out.split("\0")))


def gate(*args: str) -> tuple[int, str]:
    """scripts/octo-feather-gate's exit code and stdout (it owns the full pass record and the gate
    configuration)."""
    p = subprocess.run(
        [sys.executable, str(KIT / "scripts" / "octo-feather-gate"), *args],
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
        check=False,
    )
    return p.returncode, p.stdout


def _git_facts(head: str, base: str, files: list[str], err: type[Exception]) -> Git:
    """Git's reads (its docstring): a failed read of a listed commit raises ERR."""

    def run(*args: str, ok: tuple[int, ...] = (0,)) -> str:
        return git(*args, ok=ok, err=err)[1]

    here = not git("cat-file", "-e", f"{head}^{{commit}}", ok=(0, 1, 128), err=err)[0]
    try:
        topo = tuple(git("rev-list", "--topo-order", head, f"^{base}", err=_Unread)[1].split())
    except _Unread as e:
        return Git(base, here, Unread(str(e)))
    status = _status(files)
    walk = [
        ln.split() for ln in run("rev-list", "--reverse", "--parents", head, f"^{base}").split("\n")
    ]
    subjects = dict(
        cast("tuple[str, str]", tuple(ln.split("\0", 1)))
        for ln in run("log", "--format=%H%x00%s", head, f"^{base}").split("\n")
        if "\0" in ln
    )
    commits: dict[str, Commit] = {}
    walks: dict[str, tuple[str, ...]] = {}
    for c, *parents in filter(None, walk):
        subject = subjects[c].strip()
        if len(parents) == 1:
            diff = run("diff-tree", "--no-commit-id", "--name-only", "-r", "-z", c)
            commits[c] = Commit(tuple(parents), subject, frozenset(filter(None, diff.split("\0"))))
        elif len(parents) == MERGE_PARENTS:
            commits[c] = Commit(
                tuple(parents), subject, merge=_merge(c, parents[0], parents[1], base, err)
            )
        else:
            commits[c] = Commit(tuple(parents), subject)
    merged = any(len(k.parents) > 1 for k in commits.values())
    for i, c in enumerate(commits):  # one chain of commits has one walk order: its own
        walks[c] = (
            tuple(run("rev-list", "--reverse", c, f"^{base}").split())
            if merged
            else tuple(commits)[: i + 1]
        )
    diffs: dict[str, dict[str, str]] = {}
    if merged:  # a lane diff is read for a merge only
        aside: frozenset[str] = status if isinstance(status, frozenset) else frozenset()
        for c in commits:
            mb = run("merge-base", c, base).strip()
            out = run("diff", "--raw", "--no-renames", "--no-abbrev", "-z", mb, c).split("\0")
            raw = {f: m for m, f in zip(out[0::2], out[1::2], strict=False) if f and f not in aside}
            diffs[c] = _lane_diff(raw, _patch(mb, c, err))
    return Git(base, here, topo, commits, walks, diffs, status)


def _patch(old: str, new: str, err: type[Exception]) -> str:
    """`git diff -U0` of OLD to NEW, its bytes decoded losslessly (a file need not be UTF-8), the
    user's diff settings that change its form set aside."""
    args = ["diff", "-U0", "--no-renames", "--no-color", "--no-ext-diff", "--no-textconv"]
    args += ["--src-prefix=a/", "--dst-prefix=b/", old, new]
    p = subprocess.run(  # bytes: git() decodes its text strictly
        ["git", *args],  # noqa: S607 (git from PATH)
        capture_output=True,
        stdin=subprocess.DEVNULL,
        check=False,
    )
    if p.returncode:
        git(*args, err=err)  # git's refusal, named as every read here names it
    return p.stdout.decode(errors="surrogateescape")


def _lane_diff(raw: dict[str, str], patch: str) -> dict[str, str]:
    """Each file's hunks in the lane's diff (spec #lanes-one-head: hunk by hunk wherever main's
    changes elsewhere in a file moved its lines), from RAW, {path: its `git diff --raw` line},
    and PATCH, git diff -U0 of the same commits: its modes and status, then each hunk's removed
    and added lines, git's `@@` line numbers aside. A binary file, or one whose path git quotes,
    is its raw line, blob ids and all, as before."""
    sections: dict[str, list[str] | None] = {}  # None: binary
    for part in re.split(r"^diff --git ", patch, flags=re.MULTILINE)[1:]:
        head, *body = part.split("\n")
        at = next((i for i, ln in enumerate(body) if ln.startswith("@@")), len(body))
        binary = any(ln.startswith(("Binary files ", "GIT binary patch")) for ln in body[:at])
        hunks = ["@@" if ln.startswith("@@") else ln for ln in body[at:] if ln]
        had = sections.get(head, [])  # a type change is two sections
        sections[head] = None if binary or had is None else [*had, *hunks]
    out: dict[str, str] = {}
    for f, m in raw.items():
        hunks = sections.get(f"a/{f} b/{f}")
        if hunks is None:
            out[f] = m
            continue
        src, dst, _, _, st = m.lstrip(":").split()
        out[f] = "\n".join([f"{src} {dst} {st}", *hunks])
    return out


def _merge(c: str, ours: str, theirs: str, base: str, err: type[Exception]) -> Merge:
    """Merge's reads for merge C of OURS and THEIRS: the rest only when THEIRS is on BASE."""
    if git("merge-base", "--is-ancestor", theirs, base, ok=(0, 1), err=err)[0]:
        return Merge(onto=False)
    rc, out = git("merge-tree", "--write-tree", "--no-messages", ours, theirs, ok=(0, 1), err=err)
    auto, tree = (
        out.split("\n", 1)[0].strip(),
        git("rev-parse", f"{c}^{{tree}}", err=err)[1].strip(),
    )
    beyond = (
        None if auto == tree else tuple(git("diff", "--name-only", auto, tree, err=err)[1].split())
    )
    resolution = tuple(resolution_files(c, err=err)) if rc or beyond is not None else ()
    return Merge(onto=True, conflict=bool(rc), beyond=beyond, resolution=resolution)


def _status(files: list[str]) -> frozenset[str] | Unread:
    """The --status FILES relative to this repo's top; Unread naming one outside it."""
    try:
        top = os.path.realpath(git("rev-parse", "--show-toplevel", err=_Unread)[1].strip())
    except _Unread as e:
        return Unread(str(e))
    out: set[str] = set()
    for f in files:
        rel = os.path.relpath(os.path.realpath(f), top)
        if rel.startswith(".."):
            return Unread(
                f"--status {f} is outside this repo ({top}): run merge-ask in the lane worktree, "
                "naming its status file"
            )
        out.add(rel)
    return frozenset(out)


def _gate_facts(g: Git, head: str) -> Gate:
    """Gate's reads: HEAD's identity, then each lane commit's record until one carries over."""
    rc, out = gate("config", head)
    try:
        raw: object = json.loads(out) if rc == 0 else {}
    except ValueError:
        raw = {}
    facts = Gate((rc, cast("dict[str, object]", raw) if isinstance(raw, dict) else {}))
    if not g.here or not facts.config[1] or isinstance(g.topo, Unread):
        return facts  # the full pass stops there
    for c in [head, *(r for r in g.topo if r.lower() != head.lower())]:
        rc, out = gate("passed", c)
        try:
            rec: object = json.loads(out) if rc == 0 else None
        except ValueError:
            rec = None
        facts.passes[c] = cast("dict[str, object]", rec) if isinstance(rec, dict) else {}
        if _carries(g, facts.config[1], head, c, facts.passes[c]) == []:
            break
    return facts


def _trend(path: Path, head: str) -> Trend:
    """Trend's reads: PATH, the head's history, gate-budget.toml at it."""
    try:
        rows: tuple[list[tuple[int, dict[str, object]]], list[int]] | Unread | None = (
            numbered_jsonl(path)
        )
    except (OSError, UnicodeDecodeError) as e:
        rows = Unread(str(e))
    try:
        history: frozenset[str] | Unread = frozenset(
            git("rev-list", "--max-count=1000", head, err=_Unread)[1].split()
        )
    except _Unread as e:
        history = Unread(str(e))
    try:
        rc, text = git("show", f"{head}:{BUDGET}", ok=(0, 128), err=_Unread)
        budget: str | Unread | None = None if rc else text
    except _Unread as e:
        budget = Unread(str(e))
    now = dt.datetime.now(dt.UTC).replace(microsecond=0)
    return Trend(path, rows, history, budget, now)


def _reported(head: str, rollup: list[dict[str, object]], repo: str | None) -> Reported:
    """Reported's reads: the head's runs only when the rollup names a check twice."""
    checks = [c for c in rollup if c.get("__typename") == "CheckRun"]
    keys = [(str(c.get("name")), str(c.get("workflowName"))) for c in checks]
    if len(keys) == len(set(keys)):
        return Reported(rollup, None)
    try:
        runs = check_runs(head, repo, "the PR head", err=_Unread)
        out = gh(
            ["api", f"repos/{repo or '{owner}/{repo}'}/actions/runs?head_sha={head}&per_page=100"],
            f"read workflow identities on {head[:12]} (gh auth status)",
            err=_Unread,
        )
    except _Unread as e:
        return Reported(rollup, Unread(str(e)))
    return Reported(rollup, (runs, out))


def _unreported(head: str, base: str, repo: str | None) -> Workflows | NoWorkflow | Unread:
    """No check reported: the workflow files at HEAD, and only when there are none BASE's policy."""
    try:  # an unreadable no-CI fact is this one item failing closed, never an abort of the check
        wf = ci_workflows(repo, head, err=_Unread)[0]
        if wf:
            return Workflows(wf)
    except _Unread as e:
        return Unread(str(e))
    try:
        branch = _api(repo, f"branches/{base}")
        try:
            _branch_required(branch[0])
        except (KeyError, TypeError):
            return NoWorkflow(Policy(base, branch, None))
        return NoWorkflow(Policy(base, branch, _api(repo, f"rules/branches/{base}")))
    except _Unread as e:
        return NoWorkflow(Unread(str(e)))


def _api(repo: str | None, path: str) -> tuple[object, str]:
    """gh api repos/REPO/PATH: (its JSON, '') or (None, why: gh's last line, or no JSON)."""
    try:
        p = subprocess.run(
            ["gh", "api", f"repos/{repo or '{owner}/{repo}'}/{path}"],  # noqa: S607 (gh from PATH)
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,
            check=False,
        )
    except FileNotFoundError as e:
        msg = "gh not on PATH: install the GitHub CLI and log in (just install-check)"
        raise _Unread(msg) from e
    err = (p.stderr or p.stdout).strip().splitlines()
    if p.returncode:
        return None, err[-1][:200] if err else f"exit {p.returncode}"
    try:
        return json.loads(p.stdout), ""
    except ValueError:
        return None, f"no JSON ({p.stdout[:80]!r})"


def check_runs(
    sha: str, repo: str | None, what: str, *, err: type[Exception]
) -> list[dict[str, object]]:
    """GitHub's check runs on commit SHA (REST check-runs, the latest of each), each {id, name,
    status, conclusion, html_url}. WHAT names the commit in a refusal, raised as ERR."""
    out = gh(
        ["api", f"repos/{repo or '{owner}/{repo}'}/commits/{sha}/check-runs?per_page=100"],
        f"read the check runs of {sha[:12]}, {what} (gh auth status)",
        err=err,
    )
    try:
        data = json.loads(out)
        got = cast("list[object]", data["check_runs"])
        if data.get("total_count", len(got)) > len(got):
            msg = "incomplete check runs"
            raise ValueError(msg)  # noqa: TRY301 (refused below, as every malformed page)
    except (ValueError, KeyError, TypeError) as e:
        msg = (
            f"gh api check-runs of {sha[:12]} printed no check runs: check the gh on PATH "
            f"({out[:100]!r})"
        )
        raise err(msg) from e
    return [cast("dict[str, object]", r) for r in got if isinstance(r, dict)]


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


def check(s: Snapshot) -> Ask:
    a = dataclasses.replace(_check(s), tier=tier(s))
    return dataclasses.replace(a, order=merge_order(s.order)) if s.order else a


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


class _RefusedError(Exception):
    """The head proof refused (a commit not in the repo, a status file outside it): its message."""


def _proved(
    s: Snapshot, judged: str, head: str, **kw: str | dict[str, str] | None
) -> tuple[str | None, list[str]] | _RefusedError:
    """head_proof over S's git facts (KW its at, kept, rerun, resolved), or its refusal."""
    try:
        return head_proof(s.git or Git(""), judged, head, **kw)  # pyright: ignore[reportArgumentType]
    except _RefusedError as e:
        return e


def _why(p: tuple[str | None, list[str]] | _RefusedError) -> tuple[str | None, list[str]]:
    """(proof line, why not) of a head proof, a refusal its one why."""
    return (None, [str(p)]) if isinstance(p, _RefusedError) else p


def _check(s: Snapshot) -> Ask:
    pr, head = s.pr, s.head
    checks, no_ci, current = head_checks(s.checks)
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
        return Ask([], checks, no_ci, current, refusal=NO_STATUS)
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
    # --- the checks skipped on the head, carried from the judged head; the full pass ---
    carried, carried_ok = carried_checks(current, head, judged, proof, s.runs)
    try:
        full = [f"Full pass: {w}" for w in full_pass_of(s.git, s.gate, head)] if s.gate else []
    except _AbortError as e:
        return Ask([], checks, no_ci, current, abort=str(e))
    # --- the review verdict and its check classes, Built, Failed, the rows against them ---
    rest, classes, rounds = review(s, lines, judged, resolved)
    gaps, built = built_ids(s, lines, no_crit=no_crit)
    rest += gaps
    gaps, fails = failed(s, lines)
    rest += gaps
    if t is not None:
        rest += rows_against(rows, built, fails)
    gaps, replayed = replay(s)
    rest += gaps
    rest += code_owner_gaps(s.owners)
    return Ask(
        first,
        checks,
        no_ci,
        current,
        judged_gaps,
        rest,
        section=lines,
        judged_head=judged,
        proof=proof,
        classes=classes,
        sources=sources(s, rows, judged),
        judgments=judgment_lines(s.comments),
        carried=carried,
        full=full,
        carried_ok=carried_ok,
        gate_time=gate_time(s.git, s.trend, head) if s.trend else [],
        rounds=rounds,
        replay=replayed,
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
            plain = _proved(s, judged, head)
            if not isinstance(plain, _RefusedError) and plain[1]:
                kept = _proved(s, judged, head, resolved=resolved)
                if not isinstance(kept, _RefusedError) and not kept[1]:
                    judged = head.lower()
    if not judged:
        return None, None, miss
    proof, why = _why(_proved(s, judged, head))
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
) -> tuple[list[str], list[str], list[str]]:
    """(the gaps of the Review verdict and Reviewed lines, the review's check classes, its rounds'
    lines): this PR's marker comment, on the JUDGED head or one the head proof carries to it,
    clear, with usable check classes and no proxy (docs/adr/0008), its rounds chained from the
    base to its head (spec #lanes-one-head)."""
    pr, head = s.pr, s.head
    miss: list[str] = []
    review_checks: list[str] = []
    shown: list[str] = []
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
            rproof, rwhy = _why(
                _proved(
                    s,
                    rat[0],
                    judged,
                    at="reviewed head",
                    kept="the review verdict",
                    resolved=resolved,
                    rerun=(
                        f"review {judged[:12]} afresh in full, then `octo-feather-lane verdict "
                        f"{pr} {judged[:12]} <report>`"
                    ),
                )
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
            rounds, bad = posted_rounds(cb)
            shown = [ln for n, r in enumerate(rounds, 1) for ln in r.shown(n)]
            miss += [f"Review verdict: {w}" for w in bad]
            miss += [f"Review verdict: {w}" for w in chain_gaps(s, rounds)]
    rl = field(lines, "Reviewed")
    if rproof and (not rl or rl[1].strip("`") != rproof):
        miss.append(
            f"Reviewed: {'names ' + repr(rl[1]) if rl else 'missing'}; add the check's proof "
            f"line `Reviewed: {rproof}`"
        )
    return miss, review_checks, shown


# --- the head proof, the carried checks, the full pass and the gate time (#1150) ---


def head_proof(  # noqa: C901, PLR0912, PLR0913, PLR0915  one branch per commit kind (moved whole)
    g: Git,
    judged: str,
    head: str,
    *,
    at: str = "judged head",
    kept: str = "the qc verdict",
    rerun: str = "",
    resolved: dict[str, str] | None = None,
) -> tuple[str | None, list[str]]:
    """(proof line, []) when the PR HEAD stands for the JUDGED head, else (None, why each part
    does not), over the lane's git facts G (what may lie between them: spec #lanes-one-head).
    AT names what JUDGED is, KEPT what carries over, RERUN the fix (a full gate pass: full_pass).
    RESOLVED, for the review verdict only: {merge sha: URL} of each clear resolution verdict,
    whose merge's resolution files may move. _RefusedError: a commit not in the repo, a status
    file outside it."""
    j, h = judged[:12], head[:12]
    if head.lower() == judged.lower():
        return f"{j} is the PR head", []
    rerun = rerun or f"run just qc and the review again, in parallel, on {h}"
    for sha in (judged, head):
        if sha.lower() not in g.walks:
            msg = (
                f"commit {sha[:12]} is not in this repo: run merge-ask in the lane worktree after "
                "git fetch origin"
            )
            raise _RefusedError(msg)
    if judged.lower() not in g.walks[head.lower()]:
        return None, [f"{at} {j} is not an ancestor of the PR head {h} (rebased or reset): {rerun}"]
    if isinstance(g.status, Unread):
        raise _RefusedError(g.status.why)
    status, base = g.status, g.base
    why: list[str] = []
    qc: list[str] = []
    merges: list[str] = []
    touched: set[str] = set()
    reviewed: dict[str, list[str]] = {}
    gone = set(g.walks[judged.lower()])
    for c in (c for c in g.walks[head.lower()] if c not in gone):
        k = g.commits[c]
        parents, s = k.parents, k.subject
        if len(parents) == 1:
            other = sorted(k.files - status)
            if other:
                why.append(
                    f"commit {c[:12]} {s[:60]!r} after the {at} {j} changes {', '.join(other)}, "
                    f"not only the status file{'s' * (len(status) > 1)} qc writes "
                    f"({', '.join(sorted(status))}): {rerun}"
                )
            elif not ((q := QC_COMMIT.match(s)) and q.group(2)):
                why.append(
                    f"commit {c[:12]} {s[:60]!r} after the {at} {j} is not a `qc: built ... "
                    f"(judged <sha>)` commit: only just qc writes the status file; drop it, then "
                    f"{rerun}"
                )
            else:
                qc.append(c)
                touched |= k.files
        elif len(parents) != MERGE_PARENTS or k.merge is None or not k.merge.onto:
            why.append(
                f"merge {c[:12]} {s[:60]!r} brings in {', '.join(p[:12] for p in parents[1:])}, "
                f"not {base}: only a merge of main keeps {kept}; {rerun}"
            )
        else:
            m = k.merge
            hint = (
                ""
                if resolved is None
                else " without a clear resolution verdict naming it (review what "
                f"`octo-feather-lane resolution {c[:12]}` prints, then `octo-feather-lane verdict "
                f"<PR> {c[:12]} <report> --resolution`)"
            )
            if (m.conflict or m.beyond is not None) and resolved is not None and c in resolved:
                reviewed[c] = list(m.resolution)
            elif m.conflict:
                why.append(
                    f"merge {c[:12]} {s[:60]!r} resolved a conflict with {base}: {kept} does not "
                    f"carry over{hint}; {rerun}"
                )
            elif m.beyond is not None:
                why.append(
                    f"merge {c[:12]} {s[:60]!r} changes {', '.join(m.beyond)} beyond git's "
                    f"automatic merge{hint}: {rerun}"
                )
            else:
                merges.append(c)
    proof = f"{j} to {h}: " + (
        f"qc status commits {' '.join(c[:12] for c in qc)} change only {', '.join(sorted(touched))}"
        if qc
        else "no qc status commit"
    )
    if (merges or reviewed) and not why:
        before, after = g.diffs[judged.lower()], g.diffs[head.lower()]
        moved = sorted(
            p
            for p in before.keys() | after.keys()
            if before.get(p) != after.get(p) and not any(p in fs for fs in reviewed.values())
        )
        if moved:
            why.append(
                f"after merging {base}, the lane's own hunks changed in {', '.join(moved)} (main "
                f"changed the lane's own lines, or the lane's diff moved): {kept} does not carry "
                f"over; {rerun}"
            )
        elif merges:
            d = hashlib.sha256(
                "\n".join(f"{p} {before[p]}" for p in sorted(before)).encode(
                    errors="surrogateescape"
                )
            ).hexdigest()
            proof += (
                f"; clean merge{'s' * (len(merges) > 1)} of main {' '.join(c[:12] for c in merges)}"
                f": lane hunks identical ({len(before)} file{'s' * (len(before) != 1)}, sha256 "
                f"{d[:12]})" + (" outside the resolved files" if reviewed else "")
            )
        if not moved:
            proof += "".join(
                f"; resolution of merge {c[:12]} ({', '.join(fs)}) reviewed clear: "
                f"{(resolved or {})[c]}"
                for c, fs in reviewed.items()
            )
    return (None, why) if why else (proof, [])


def _skipped(rollup: list[dict[str, object]]) -> list[str]:
    """The checks ROLLUP reports skipped (a status context never is)."""
    return sorted(
        {
            str(c.get("name") or "?")
            for c in rollup
            if c.get("__typename") != "StatusContext"
            and "conclusion" in c
            and str(c.get("conclusion") or "").upper() == "SKIPPED"
        }
    )


def carried_checks(
    rollup: list[dict[str, object]],
    head: str,
    judged: str | None,
    proof: str | None,
    runs: list[dict[str, object]] | Unread | None,
) -> tuple[list[str], list[str]]:
    """(why each check skipped on HEAD fails, a line per one that passes; when a skipped check
    counts: spec issue-lifecycle #lanes-one-head). PROOF is the head proof's line for JUDGED to
    HEAD, RUNS the judged head's check runs (None: none)."""
    skipped = _skipped(rollup)
    h = head[:12]
    if not skipped:
        return [], []
    if not judged or judged == head.lower() or not proof:
        return [
            (
                f"Checks: skipped on head {h}: {', '.join(skipped)}; a skipped check is no pass "
                f"and no Judged proof carries a judged head's CI to {h} (issue-lifecycle "
                "#lanes-one-head): run `octo-feather-lane ci-start <PR>` on the judged head, wait "
                "for its CI, then rerun"
            )
        ], []
    if isinstance(runs, Unread):
        return [f"Checks: {runs.why}"], []
    j = judged[:12]
    why: list[str] = []
    ok: list[str] = []
    for name in skipped:
        at = (
            f"Checks: {name} skipped on head {h}, carried from the judged head {j} by the Judged "
            "proof, and"
        )
        r = max(
            (r for r in runs or [] if r.get("name") == name),
            key=lambda r: int(str(r.get("id") or 0)),
            default=None,
        )
        status = str((r or {}).get("status") or "").lower()
        concl = str((r or {}).get("conclusion") or "").lower()
        if r is None:
            why.append(
                f"{at} {j} has no {name} run; run `octo-feather-lane ci-start <PR>` on {j}, wait "
                "for its CI, then rerun"
            )
        elif status != "completed":
            why.append(
                f"{at} pending on {j}: {name} {status or 'pending'}; wait for it to finish, then "
                "rerun"
            )
        elif concl == "skipped":
            why.append(
                f"{at} skipped on {j} too: CI never ran there; run `octo-feather-lane ci-start "
                f"<PR>` on {j}, then rerun"
            )
        elif concl not in ("success", "neutral"):
            why.append(
                f"{at} failing on {j}: {name} {concl or 'none'}; fix it (a red check is never "
                "pre-existing)"
            )
        else:
            ok.append(f"- {name}: skipped on {h}; {concl} on {j}, the judged head")
    return why, ok


class _AbortError(Exception):
    """A read the full pass needs failed: the merge ask refuses with it alone."""


def _fix(head: str) -> str:
    return (
        f"run the full gate, just check, on {head[:12]} and record its pass "
        "(octo-feather-integrate --full records it; octo-feather-gate --help)"
    )


def _carries(
    g: Git, ident: dict[str, object], head: str, c: str, rec: dict[str, object]
) -> list[str] | None:
    """Why lane commit C's recorded full pass REC does not carry over to HEAD (none: it does);
    None when REC is no full pass of C."""
    if rec.get("tier") != "full" or str(rec.get("head", "")).lower() != c.lower():
        return None
    fix = _fix(head)
    if rec.get("clean") is not True:
        no = [
            (
                f"it was recorded on a dirty tree (clean {json.dumps(rec.get('clean'))}): it "
                f"proves nothing; {fix}"
            )
        ]
    else:
        try:
            _, no = head_proof(g, c, head, at="full pass", kept="the full pass", rerun=fix)
        except _RefusedError as e:
            no = [str(e)]
    return no or [
        f"its {k} {str(rec.get(k))[:12]} is not the head's current {str(v)[:12]} "
        f"(octo-feather-gate config {head[:12]}): stale; {fix}"
        for k, v in ident.items()
        if rec.get(k) != v
    ]


def full_pass_of(g: Git | None, gt: Gate, head: str) -> list[str]:
    """[] when HEAD has a current recorded full gate pass, else why not (the rule:
    issue-lifecycle #lanes-checkpoints). Current: recorded (octo-feather-gate passed) on a clean
    tree at HEAD, or at a lane commit the head proof proves HEAD stands for, with the identity
    fields of HEAD itself (octo-feather-gate config). _AbortError: the lane's commits unread."""
    g = g or Git("")
    h = head[:12]
    if not g.here:
        return [
            (
                f"commit {h} is not in this repo: run merge-ask in the lane worktree after git "
                "fetch origin"
            )
        ]
    rc, ident = gt.config
    if not ident:
        return [
            (
                f"head {h}: its gate configuration is unreadable (octo-feather-gate config {h} "
                f"exit {rc}): {_fix(head)}"
            )
        ]
    if isinstance(g.topo, Unread):
        raise _AbortError(g.topo.why)
    why: list[str] = []
    for c in [head, *(r for r in g.topo if r.lower() != head.lower())]:
        no = _carries(g, ident, head, c, gt.passes.get(c, {}))
        if no is None:
            continue
        if not no:
            return []
        why = why or [f"the full pass recorded at {c[:12]} does not carry over: {w}" for w in no]
    return [
        f"head {h} has no current recorded full gate pass for that head and its gate "
        "configuration"
        + (
            f"; {'; '.join(why)}"
            if why
            else f" (none recorded on {h} or the lane commits before it): {_fix(head)}"
        )
    ]


def full_pass(head: str, files: list[str], base: str, *, err: type[Exception]) -> list[str]:
    """ci-start's full pass: the lane's git and gate facts read (as snapshot reads them), then
    full_pass_of; a read it needs that failed raises ERR."""
    g = _git_facts(head, base, files, err)
    try:
        return full_pass_of(g, _gate_facts(g, head), head)
    except _AbortError as e:
        raise err(str(e)) from None


def gate_time(g: Git | None, t: Trend, head: str) -> list[str]:  # noqa: PLR0911 (one per line)
    """The full gate's wall time on the final head against gate-budget.toml at that head, with
    its trend and slowest items (spec issue-lifecycle #lanes-checkpoints). Shown only: the code
    reviewer judges it, no gate reads it, and merge-ask passes or fails the same without it."""
    g = g or Git("")
    h = head[:12]
    title = (
        f"Gate time (the full gate on the final head against {BUDGET} at {h}; the code reviewer "
        "judges it, no gate reads it: issue-lifecycle #lanes-checkpoints):"
    )
    if isinstance(t.rows, Unread):
        return [title, f"  unread: {t.rows.why}"]
    if t.rows is None:
        return [title, f"  no gate run recorded ({t.path}: none)"]
    if isinstance(g.topo, Unread):
        return [title, f"  unread: {g.topo.why}"]
    lane = [head, *(r for r in g.topo if r != head)]
    if isinstance(t.history, Unread):
        return [title, f"  unread: {t.history.why}"]
    runs = passed_full(t.rows[0], set(t.history))
    last = next((r for c in lane for r in reversed(runs) if r.get("head") == c), None)
    if last is None:
        return [
            title,
            f"  no passed full gate run recorded on {h} or the lane commits before it ({t.path})",
        ]
    if isinstance(t.budget, Unread):
        return [title, f"  unread: {t.budget.why}"]
    budget, why = budget_parse(t.budget)
    return [title, *budget_lines(last, runs[: runs.index(last)], budget, why, t.now, "  ")]


# --- the gate time's lines, shared with octo-feather-lane's report (moved whole, #1150) ---

BUDGET = (
    "gate-budget.toml"  # the repo root's gate-time budget, kept by the factory (form: budget_text)
)
BUDGET_TREND = 5  # trend runs shown when the repo has no budget file to set trend_runs
SLOWEST = 5  # slowest items shown


Budget = dict[str, float]  # budget_seconds, growth_share, trend_runs (an int)
Run = dict[str, object]  # one check-runs.jsonl line


def numbered_jsonl(path: Path) -> tuple[list[tuple[int, Run]], list[int]] | None:
    """A JSON lines file's object lines with their numbers, and the numbers of the lines that are
    not one; None with no file."""
    if not path.exists():
        return None
    rows: list[tuple[int, Run]] = []
    bad: list[int] = []
    for i, ln in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not ln.strip():
            continue
        try:
            d: object = json.loads(ln)
        except ValueError:
            d = None
        if isinstance(d, dict):
            rows.append((i, cast("Run", d)))
        else:
            bad.append(i)
    return rows, bad


def budget_parse(text: str | None) -> tuple[Budget | None, str]:
    """gate-budget.toml's three numbers, or None and why: absent (text None) or invalid.
    budget_seconds: the full gate's wall-time budget; growth_share: the share of growth over the
    trend's median that is flagged; trend_runs: how many passed full runs before the latest make
    the trend. Stdlib tomllib: the kit's scripts stay stdlib-only (AGENTS.md)."""
    if text is None:
        return None, f"{BUDGET}: none"
    try:
        d: dict[str, object] = tomllib.loads(text)
    except tomllib.TOMLDecodeError as e:
        return None, f"{BUDGET}: {e}"
    least = {"budget_seconds": 0.0, "growth_share": 0.0, "trend_runs": 1.0}
    ok: Budget = {}
    for k, low in least.items():
        v = d.get(k)
        if (
            isinstance(v, (int, float))
            and not isinstance(v, bool)
            and (v > low if k == "budget_seconds" else v >= low)
            and (k != "trend_runs" or isinstance(v, int))
        ):
            ok[k] = v
    bad = [f"{k} {d.get(k)!r} is not a number of the right range" for k in least if k not in ok]
    # the per-test CPU budget, optional: the gate's own (tests/gate/conftest.py) reads it
    cpu = d.get("test_cpu_seconds")
    if cpu is not None and (isinstance(cpu, bool) or not isinstance(cpu, (int, float)) or cpu <= 0):
        bad.append(f"test_cpu_seconds {cpu!r} is not a number of the right range")
    # octo-feather-slot reads and checks them
    slots = {
        "heavy_items",
        "heavy_slots",
        "eval_slots",
        "slot_grace_seconds",
        "slot_bound_seconds",
        "fast_workers",  # the fast tier's cap: tests/gate/heavy_slot.py reads it
        "fast_runs",  # fast-tier runs at once on the box: tests/gate/heavy_slot.py reads it
    }
    bad += [f"unknown key {k}" for k in sorted(set(d) - set(least) - {"test_cpu_seconds"} - slots)]
    return (None, f"{BUDGET}: " + "; ".join(bad)) if bad else (ok, "")


def total(d: Run) -> float:
    t = d.get("total_s")
    return float(t) if isinstance(t, (int, float)) else 0.0


def passed_full(rows: list[tuple[int, Run]], heads: set[str]) -> list[Run]:
    """check-runs.jsonl lines of passed full gate runs (tier full, exit 0, the runner's own
    fields) on HEADS, oldest first."""
    runs = [
        d
        for _, d in rows
        if d.get("tier") == "full"
        and d.get("exit") == 0
        and d.get("head") in heads
        and utc(d.get("start")) is not None
        and isinstance(d.get("total_s"), (int, float))
    ]
    # UTC instants of one form: text order is time order
    return sorted(runs, key=lambda d: str(d.get("start")))


def secs(x: float) -> str:
    return f"{round(x, 3):g}s"


def budget_lines(  # noqa: PLR0913, PLR0917  the run, its trend, the budget and how it is shown
    last: Run, before: list[Run], budget: Budget | None, why: str, now: object, pad: str
) -> list[str]:
    """The full gate run LAST against BUDGET, with the trend (passed full runs BEFORE it, oldest
    first) and its slowest items; flags OVER BUDGET and GROWN. Display only: no gate reads it
    (issue-lifecycle #lanes-checkpoints)."""
    t = total(last)
    run = (
        f"{pad}full gate: {secs(t)}, head {str(last.get('head'))[:12]}, started "
        f"{stamp(last.get('start'), now)}"
    )
    if budget is None:
        out = [f"{run}: no budget ({why})"]
    else:
        b = float(budget["budget_seconds"])
        out = [
            f"{run}: "
            + (
                f"OVER BUDGET by {secs(t - b)}"
                if t > b
                else f"within budget, {secs(b - t)} to spare"
            )
            + f" (budget {secs(b)})"
        ]
    base = before[-int(budget["trend_runs"] if budget else BUDGET_TREND) :]
    if not base:
        out.append(f"{pad}growth: no passed full run before it to compare")
    else:
        med = statistics.median(total(d) for d in base)
        grow = (t - med) / med if med else 0.0
        g = (
            f"{pad}growth: {grow:+.1%} over the trend's median {secs(med)} (the {len(base)} "
            f"passed full run{'s' * (len(base) > 1)} before it)"
        )
        if budget is None:
            out.append(f"{g}; no set share ({why})")
        else:
            share = float(budget["growth_share"])
            out.append(
                f"{g}; set share {share * 100:g}%: " + ("GROWN" if grow > share else "within")
            )
    out.append(
        f"{pad}trend: "
        + ", ".join(
            f"{secs(total(d))} {str(d.get('head'))[:12]} {d.get('start')}" for d in [*base, last]
        )
        + " (passed full runs, oldest first)"
    )
    raw = last.get("steps")
    steps: list[tuple[float, str]] = []
    for x in cast("list[object]", raw) if isinstance(raw, list) else []:
        st = cast("dict[str, object]", x) if isinstance(x, dict) else {}
        sec = st.get("seconds")
        if isinstance(sec, (int, float)):
            steps.append((float(sec), str(st.get("name"))))
    top = sorted(steps, key=lambda s: (-s[0], s[1]))[:SLOWEST]
    out.append(
        f"{pad}slowest: "
        + (", ".join(f"{name} {secs(sec)}" for sec, name in top) or "no items recorded")
    )
    return out


def stamp(s: object, now: object) -> str:
    t = utc(s)
    if t is None:
        return f"{s!r} (not a UTC instant)" if s not in (None, "") else "(not recorded)"
    n = int((cast("dt.datetime", now) - t).total_seconds())
    sign, n = ("", n) if n >= 0 else ("-", -n)
    d, h, m = n // 86400, n // 3600 % 24, n // 60 % 60
    age = (f"{d}d" if d else "") + (f"{h}h" if d or h else "") + f"{m}m"
    return f"{t:%Y-%m-%dT%H:%M:%SZ} ({sign}{age} ago)"


# --- the checks ---


def head_checks(c: Checks) -> tuple[list[str], str, list[dict[str, object]]]:
    """The Checks rules on C (spec #lanes-one-head; octo-feather-lane --help, merge-ask Checks
    line): (their gaps, the no-CI line, the current checks), as Ask names them."""
    h = c.head[:12]
    miss: list[str] = []
    no_ci = ""
    rollup: list[dict[str, object]] = []
    at = c.at_head
    if isinstance(at, Reported):
        rollup = at.rollup
        try:
            rollup = current_checks(at, c.head)
        except _Gap as e:
            miss.append(f"Checks: {e}")
    elif isinstance(at, Unread):
        miss.append(
            f"Checks: none reported on head {h}, and the no-CI fact could not be read ({at.why})"
        )
    elif isinstance(at, Workflows):
        miss.append(
            f"Checks: none reported on head {h}, its workflows {', '.join(at.files)}; "
            "push the head and wait for CI"
        )
    else:
        src = f"gh api repos/{c.repo or '<this repo>'}/git/trees/{h}"
        try:
            no_ci = (
                f"no CI: no workflow file under .github/workflows at head {h} ({src}); "
                + required_none(c.repo, at.policy)
            )
        except _Gap as e:
            miss.append(
                f"Checks: none reported on head {h}, no workflow file there ({src}), but {e}"
            )
    failed, pending = bad_checks(rollup)
    if failed:
        miss.append(
            f"Checks: failing on head {h}: {', '.join(failed)}; "
            "fix them (a red check is never pre-existing)"
        )
    if pending:
        miss.append(
            f"Checks: pending on head {h}: {', '.join(pending)}; "
            "wait for them to finish, then rerun"
        )
    return miss, no_ci, rollup


def bad_checks(rollup: list[dict[str, object]]) -> tuple[list[str], list[str]]:
    """(the failed checks, the pending ones) of ROLLUP (gh pr view statusCheckRollup), each
    `<name> <state>`."""
    failed: list[str] = []
    pending: list[str] = []
    for c in cast("list[dict[str, str]]", rollup):
        name = c.get("name") or c.get("context") or "?"
        if c.get("__typename") == "StatusContext" or ("state" in c and "conclusion" not in c):
            s = (c.get("state") or "").upper()
            (
                pending if s in ("PENDING", "EXPECTED", "") else failed if s != "SUCCESS" else []
            ).append(f"{name} {s.lower() or 'pending'}")
        elif (c.get("status") or "COMPLETED").upper() != "COMPLETED" or not c.get("conclusion"):
            pending.append(f"{name} {(c.get('status') or 'pending').lower()}")
        elif c["conclusion"].upper() not in ("SUCCESS", "NEUTRAL", "SKIPPED"):
            failed.append(f"{name} {c['conclusion'].lower()}")
    return failed, pending


def current_checks(at: Reported, head: str) -> list[dict[str, object]]:  # noqa: C901, PLR0915 (moved whole, #1148)
    """Project repeated checks through GitHub's actual head runs, retaining app/workflow/context
    identity."""
    rollup = at.rollup
    if at.runs is None:
        return rollup
    if isinstance(at.runs, Unread):
        raise _Gap(at.runs.why)
    runs, out = at.runs

    def obj(value: object) -> dict[str, object]:
        if not isinstance(value, dict):
            msg = "expected an object"
            raise ValueError(msg)  # noqa: TRY004 (refused below, as every malformed page)
        return cast("dict[str, object]", value)

    def number(value: object) -> int:
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            msg = "expected a positive integer identity"
            raise ValueError(msg)
        return value

    def text(value: object) -> str:
        if not isinstance(value, str) or not value:
            msg = "expected nonempty text"
            raise ValueError(msg)
        return value

    checks = [c for c in rollup if c.get("__typename") == "CheckRun"]
    try:
        data = obj(json.loads(out))
        raw = data["workflow_runs"]
        if not isinstance(raw, list):
            msg = "expected workflow runs"
            raise ValueError(msg)  # noqa: TRY004, TRY301 (refused below, as every malformed page)
        workflows = [obj(w) for w in cast("list[object]", raw)]
        if number(data.get("total_count", len(workflows))) > len(workflows):
            msg = "incomplete workflow runs"
            raise ValueError(msg)  # noqa: TRY301
        suites: dict[int, int] = {}
        latest: dict[int, tuple[int, int]] = {}
        for w in workflows:
            if w["head_sha"] != head:
                msg = "workflow on another head"
                raise ValueError(msg)  # noqa: TRY301
            suite, workflow, rid = (
                number(w["check_suite_id"]),
                number(w["workflow_id"]),
                number(w["id"]),
            )
            suites[suite] = workflow
            latest[workflow] = max(latest.get(workflow, (0, 0)), (rid, suite))
        identities: dict[str, tuple[int, int, str]] = {}
        grouped: dict[tuple[int, int, str], list[dict[str, object]]] = {}
        for r in runs:
            if r["head_sha"] != head:
                msg = "check on another head"
                raise ValueError(msg)  # noqa: TRY301
            suite, app = number(obj(r["check_suite"])["id"]), number(obj(r["app"])["id"])
            number(r["id"])
            text(r["status"])
            if r["conclusion"] is not None:
                text(r["conclusion"])
            key = (app, suites[suite], text(r["name"]))
            identities[text(r["html_url"])] = key
            grouped.setdefault(key, []).append(r)
        projected = [c for c in rollup if c.get("__typename") != "CheckRun"]
        seen: set[tuple[int, int, str]] = set()
        for c in checks:
            key = identities[text(c["detailsUrl"])]
            if key in seen:
                continue
            seen.add(key)
            candidates = [
                r for r in grouped[key] if number(obj(r["check_suite"])["id"]) == latest[key[1]][1]
            ]
            r = max(candidates, key=lambda r: number(r["id"]), default=None)
            projected.append(
                {
                    "__typename": "CheckRun",
                    "name": key[2],
                    "status": r["status"] if r else "QUEUED",
                    "conclusion": r["conclusion"] if r else None,
                }
            )
    except (ValueError, KeyError, TypeError) as e:
        msg = (
            f"current check identities on {head[:12]} unavailable ({e}): "
            "reread GitHub's complete head checks"
        )
        raise _Gap(msg) from e
    return projected


def _branch_required(branch: object) -> list[str]:
    """The checks gh api branches/BASE's JSON BRANCH requires; KeyError or TypeError when it names
    none (no protection.required_status_checks)."""
    prot = cast("dict[str, object]", cast("dict[str, object]", branch)["protection"])
    rsc = cast("dict[str, list[dict[str, object]]]", prot["required_status_checks"])
    return sorted({str(c) for c in rsc["contexts"]} | {str(c["context"]) for c in rsc["checks"]})


def required_none(repo: str | None, p: Policy | Unread) -> str:
    """The base branch's required-check policy P, when it requires no check: the line naming both
    sources. Raise _Gap naming the required checks, or the source that could not be read (fail
    closed)."""
    if isinstance(p, Unread):
        raise _Gap(p.why)
    base = p.base
    shown = f"repos/{repo or '<this repo>'}"
    br, why = p.branch
    try:
        req = _branch_required(br)
    except (KeyError, TypeError) as e:
        msg = (
            f"the required checks of base {base} could not be read "
            f"(gh api {shown}/branches/{base}: {why or 'no protection.required_status_checks'}): "
            "fix gh auth status or read access, then rerun"
        )
        raise _Gap(msg) from e
    rules, why = p.rules or (None, "not read")
    if why == f"gh: {NO_RULESETS} (HTTP 403)":
        rsrc = (
            f"gh api {shown}/rules/branches/{base}: rulesets unavailable on this plan, "
            "none in force"
        )
    elif isinstance(rules, list):
        try:
            for r in cast("list[dict[str, object]]", rules):
                if r["type"] == "required_status_checks":
                    params = cast("dict[str, list[dict[str, object]]]", r["parameters"])
                    req += sorted(str(c["context"]) for c in params["required_status_checks"])
        except (KeyError, TypeError) as e:
            msg = (
                f"the rulesets of base {base} could not be read "
                f"(gh api {shown}/rules/branches/{base}: "
                "a required_status_checks rule with no contexts): check the gh on PATH, then rerun"
            )
            raise _Gap(msg) from e
        rsrc = f"gh api {shown}/rules/branches/{base}: no required_status_checks rule"
    else:
        msg = (
            f"the rulesets of base {base} could not be read (gh api {shown}/rules/branches/{base}: "
            f"{why or 'no rule list'}): fix gh auth status or read access, then rerun"
        )
        raise _Gap(msg)
    if req:
        msg = (
            f"base {base} requires checks {', '.join(dict.fromkeys(req))} "
            f"(gh api {shown}/branches/{base}, "
            f"{shown}/rules/branches/{base}): push the head and wait for them"
        )
        raise _Gap(msg)
    return (
        f"base {base} requires no check "
        f"(gh api {shown}/branches/{base}: no required status check; {rsrc}), "
        "so required checks are none"
    )


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
    "class: exact|proxy|declaration` (docs/adr/0008)"
)
# The declaration class: docs/adr/0008 rung 2; how merge-ask shows it: spec issue-lifecycle
# #lanes-one-head.
DECLARATION = "| class: declaration"
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
                    "reads: <what it reads> | class: exact|proxy|declaration`"
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
            if cls.lower() not in ("exact", "proxy", "declaration"):
                why.append(
                    f"check line for {path} has class {cls!r}; write `class: exact`, "
                    "`class: proxy` or `class: declaration` (docs/adr/0008)"
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


CLEARED_LINE = re.compile(r"^Opt-out cleared:[ \t]*(.*?)\s*$")


def decision_lines(text: str) -> tuple[list[str], list[str], list[str]]:
    """(TEXT's owner decision lines as written, the commits its `Opt-out cleared:` lines name, why
    a line is unusable), in the verdict reader's scope (form: .agents/skills/code-review/SKILL.md,
    Verdict step, Report fields; #1259)."""
    owner: list[str] = []
    cleared: list[str] = []
    why: list[str] = []
    for ln in outside(text):
        if m := CLEARED_LINE.match(ln):
            sha = m.group(1).strip("`")
            if SHA_NAMED.fullmatch(sha):
                cleared.append(sha.lower())
            else:
                why.append(
                    f"`{ln.strip()}` is not `Opt-out cleared: <commit sha>`, the opt-out's commit "
                    "as `check-behavior-smoke` names it (7 to 40 hex)"
                )
        elif OWNER_DECISION.match(ln):
            if ln.split(":", 1)[1].strip():
                owner.append(ln.rstrip())
            else:
                why.append(f"`{ln.strip()}` names no decision: write the decision after the colon")
    return list(dict.fromkeys(owner)), list(dict.fromkeys(cleared)), why


# The review rounds of the verdict comment (#1220, spec #lanes-one-head): octo-feather-lane
# verdict writes them under ROUNDS, one ROUND_LINE each, its check lines under it; merge-ask reads
# them. A comment with no ROUNDS section (posted before rounds) is one legacy round: the whole
# lane, ending at its Head (#1218 design, term 1).
ROUNDS = "### Rounds"
ROUND_LINE = re.compile(
    r"^- Round \d+: (\S+)\.\.([0-9a-f]{7,40}), (full|delta|legacy)(?: \([^()]*\))?, "
    r"verdict (clear|blocking)$"
)
ROUND_CHECK = re.compile(r"^  - (Checks?: .*)$")
Kind = Literal["full", "delta", "legacy"]


@dataclass(frozen=True)
class Round:
    """One posted review round: START..END the range its reviewer diffed (START '' for a legacy
    round, the whole lane), KIND full (START on the base), delta (START the previous round's END)
    or legacy, its VERDICT and its CHECKS (normalized check lines, `Checks: none` alone)."""

    start: str
    end: str
    kind: Kind
    verdict: str
    checks: tuple[str, ...]

    def line(self, n: int) -> list[str]:
        """Its lines in the comment, as round N."""
        kind = "legacy (posted before rounds)" if self.kind == "legacy" else self.kind
        head = f"- Round {n}: {self.start or 'lane'}..{self.end}, {kind}, verdict {self.verdict}"
        return [head, *(f"  - {c}" for c in self.checks)]

    def shown(self, n: int) -> list[str]:
        """Its lines as merge-ask prints them, as round N."""
        span = (
            f"the lane to {self.end[:12]}, posted before rounds (counted whole)"
            if self.kind == "legacy"
            else f"{self.start[:12]}..{self.end[:12]} {self.kind}"
        )
        return [f"- Round {n}: {span}, verdict {self.verdict}", *(f"  - {c}" for c in self.checks)]


def posted_rounds(body: str) -> tuple[list[Round], list[str]]:
    """(the rounds of the verdict comment BODY, why a line of its rounds is unreadable); one
    legacy round when it has no rounds section, none when it names no Head either."""
    hdr = body.split("\n### Findings", 1)[0]
    if f"\n{ROUNDS}\n" not in hdr:
        h, vs = HEAD_LINE.search(hdr), verdicts(hdr)
        if not h:
            return [], []
        cls = tuple(check_lines(hdr)[0])
        return [Round("", h.group(1).lower(), "legacy", vs[-1] if vs else "", cls)], []
    rounds: list[Round] = []
    bad: list[str] = []
    for ln in hdr.split(f"\n{ROUNDS}\n", 1)[1].split("\n"):
        if m := ROUND_LINE.match(ln):
            start = "" if m.group(3) == "legacy" else m.group(1).lower()
            kind = cast("Kind", m.group(3))
            rounds.append(Round(start, m.group(2).lower(), kind, m.group(4), ()))
        elif (c := ROUND_CHECK.match(ln)) and rounds:
            r = rounds[-1]
            rounds[-1] = dataclasses.replace(r, checks=(*r.checks, c.group(1)))
        elif ln.strip():
            bad.append(
                f"unreadable round line `{ln.strip()[:80]}` in the comment's {ROUNDS}; post the "
                "next round with `octo-feather-lane verdict`, which rewrites them"
            )
    return rounds, bad


def check_set(rounds: list[Round]) -> list[str]:
    """The lane's check lines over ROUNDS: the latest full (or legacy) round's, then each later
    delta's, a later line for the same path and rule replacing the earlier one; `Checks: none`
    when none."""
    i = max((k for k, r in enumerate(rounds) if r.kind != "delta"), default=0)
    out: dict[tuple[str, ...], str] = {}
    for r in rounds[i:]:
        for c in r.checks:
            s = CHECK_SHAPE.fullmatch(c[len("Check: ") :]) if c.startswith("Check: ") else None
            if s:
                out[s.groups()[:2]] = c
    return list(out.values()) or ["Checks: none"]


def chain_gaps(s: Snapshot, rounds: list[Round]) -> list[str]:
    """Why ROUNDS, S's verdict comment's, do not chain from the base to their last head (the rule:
    octo-feather-lane --help, merge-ask)."""
    if not rounds:
        return []
    i = len(rounds) - 1
    while i > 0 and rounds[i].start == rounds[i - 1].end:
        i -= 1
    first, lane = rounds[i], {oid.lower() for oid, _ in s.commits}
    if first.kind == "legacy" or (first.kind == "full" and first.start not in lane):
        return []
    fork = s.fork[:12] or (s.git.base if s.git else "the base")
    a, b = first.start[:12], rounds[-1].end[:12]
    return [
        (
            f"the review rounds cover {a}..{b} only: no posted round covers {fork}..{a}, the lane "
            f"before them; post the round that reviewed up to {a} with `octo-feather-lane "
            f"verdict`, or review the lane from {fork} and post that round"
        )
    ]


# The correction lane's replay, pure (#1222; spec issue-lifecycle #lanes-correction; the rule:
# octo-feather-lane --help, merge-ask). Its reads: _replay, at the end.

REPLAY_HEAD = ("finding", "case", "command", "result")  # its table's columns, in order
CLAIMS = {"caught": "caught", "missed": "pass", "pass": "pass"}  # a result, the run it claims
NOT_REPLAYABLE = "not replayable:"
TAIL = 300  # characters of a run's output a refusal quotes


class Row(NamedTuple):
    """A `## Replay` row: FINDING (an id `<lane> <at>`, `trigger` or `clean <lane>`), CASE, the
    COMMAND cell's text (backticks cut) and its RESULT."""

    finding: str
    case: str
    command: str
    result: str


def _ran(run: Replayed, cls: str) -> str | None:
    """What RUN shows for the issue's class CLS, `caught` or `pass` (the rule: octo-feather-lane
    --help, merge-ask), else None."""
    if run.exit == 0:
        return "pass"
    return "caught" if run.exit is not None and cls in run.out else None


def replay(s: Snapshot) -> tuple[list[str], str]:
    """(the gaps of S's `## Replay` table, its `Replay:` line) for a correction lane; ([], '')
    for any other lane."""
    r = s.replay
    if r is None:
        return [], ""
    if isinstance(r, Unread):
        return [f"Replay: {r.why}"], ""
    table = r.table
    rows, bad = table or ([], [])
    gaps = [f"Replay: {w}" for w in bad]
    if table is None:
        gaps.append(
            f"Replay: no `## Replay` section; #{r.key} is a correction lane ({r.cls}) and the "
            "verdict lists a check: add `| finding | case | command | result |`, a row per "
            "finding and per clean lane below (octo-feather-lane --help, merge-ask)"
        )
    findings = r.findings or ("trigger",)
    named = {row.finding for row in rows}
    gaps += [
        f"Replay: no row for finding `{f}`" + (" (the issue lists no finding)" * (f == "trigger"))
        for f in findings
        if f not in named
    ]
    gaps += [
        f"Replay: no row for clean lane `clean {x}`" for x in r.sample if f"clean {x}" not in named
    ]
    shown: dict[str, list[str]] = {}  # each row's finding, the results its runs showed
    said_rows: list[str] = []  # each row as its sandboxed run showed it
    for row in rows:
        if row.result.startswith(NOT_REPLAYABLE) and row.result[len(NOT_REPLAYABLE) :].strip():
            shown.setdefault(row.finding, [])
            said_rows.append(f"- `{row.finding}`: {row.result} (as the row says; not run)")
            continue
        claim = CLAIMS.get(row.result)
        if claim is None:
            gaps.append(
                f"Replay: row `{row.finding}` result `{row.result}` is none of caught, missed, "
                "pass, `not replayable: <why>`"
            )
            continue
        if _program(row.command) not in r.paths:
            gaps.append(
                f"Replay: row `{row.finding}` runs `{row.command}`, whose program is no path on a "
                f"verdict Check line ({', '.join(r.paths)}): replay the lane's own check"
            )
            continue
        run = r.runs.get(row, Replayed(None, "not run"))
        if run.unserved:  # never run outside the sandbox: shown, not judged
            shown.setdefault(row.finding, [])
            said_rows.append(f"- `{row.finding}`: {NOT_REPLAYABLE} {run.unserved}")
            continue
        got = _ran(run, r.cls)
        if got != claim:
            said = " ".join(run.out.split())[-TAIL:]
            how = f"exited {run.exit}" if run.exit is not None else "did not run"
            needs = f"a non-zero exit naming {r.cls}" if claim == "caught" else "exit 0"
            gaps.append(
                f"Replay: row `{row.finding}` claims {row.result} ({needs}); its run at "
                f"{s.head[:12]} {how}: ...{said}"
            )
            continue
        shown.setdefault(row.finding, []).append(claim)
        wrote = f"; {len(run.wrote)} writes discarded: {', '.join(run.wrote[:3])}" * bool(run.wrote)
        said_rows.append(f"- `{row.finding}`: {row.result}, sandboxed run exited {run.exit}{wrote}")
    k = sum("caught" in shown.get(f, []) for f in findings)
    m = sum(f in shown and not shown[f] for f in findings)
    clean = [shown[f"clean {x}"] for x in r.sample if shown.get(f"clean {x}")]
    refused = sum("caught" in c for c in clean)
    line = (
        f"Replay: caught {k} of {len(findings)} ({m} not replayable); false refusals {refused} of "
        f"{len(clean)} clean"
    )
    return gaps, "\n".join([line, *said_rows])


# The merge-order rule, pure (spec #gates-merge-order)

# The freshness tail of an octo-feather-qa --verdict line (its --help, Verdict): fresh, stale with
# each stale item, or missing with why.
FRESHNESS = re.compile(
    r"^\S+ \S+: stored \S+, run \S+, kit \S+, [^;]*; "
    r"(?:fresh at HEAD \w+|stale at HEAD \w+: (?P<stale>.*)|missing: .*)$"
)


def _stale(line: str) -> list[str] | None:
    """The stale items LINE names (none when fresh); None when it judged no freshness."""
    m = FRESHNESS.match(line)
    if m is None or line.split("; ", 1)[1].startswith("missing: "):
        return None
    return m.group("stale").split("; ") if m.group("stale") else []


def merge_order(o: Order) -> list[str]:
    """The merge-order lines for O: what they name and that they are never a gap, issue-lifecycle
    spec #gates-merge-order; a pin's newly stale items, those octo-feather-qa names stale only
    with this lane merged in."""
    out: list[str] = []
    for p in o.prs:
        who = f"PR #{p.number} ({p.branch})"
        if p.conflicts:
            out.append(f"- {who}: its head conflicts with this head in {', '.join(p.conflicts)}")
        for pin in p.pins:
            was, now = _stale(pin.main), _stale(pin.merged)
            if was is None or now is None:
                said = pin.main if was is None else pin.merged
                out.append(f"- not read: {who} pinned run {pin.run}: octo-feather-qa said {said}")
            elif new := [x for x in now if x not in was]:
                out.append(f"- {who}: this merge stales its pinned run {pin.run}: {'; '.join(new)}")
    out += [f"- not read: {u}" for u in o.unread]
    if not out:
        n = len(o.prs)
        out = [
            (
                f"- none: {n} other open pull request{'s' * (n != 1)} on {o.base}, none this "
                "merge would stale or conflict with"
            )
        ]
    head = (
        "Merge order (issue-lifecycle #gates-merge-order; shown only: this merge ask passes or "
        "fails the same without it):"
    )
    return [head, *out]


# The tier rule, pure (spec #gates-tiers, #gates-tier-relay; issue #1257): each reason one entry


class Reason(NamedTuple):
    """One reason the ask found: the TIER it gives and its TEXT, the `- <text>` line printed."""

    tier: int
    text: str


# The opt-outs check-behavior-smoke prints (that script owns what an opt-out is)
OPT_OUT = re.compile(r"^behavior smoke: opt-out ([0-9a-f]{7,40}) Behaviour-neutral: (.*)$")
SHA_NAMED = re.compile(r"[0-9a-fA-F]{7,40}")


@dataclass(frozen=True)
class Tier:
    """The ask's tier N, its REASONS and whom its merge WAITS for (octo-feather-lane --help,
    merge-ask)."""

    n: int
    reasons: list[Reason]
    waits: str

    @property
    def lines(self) -> list[str]:
        """The tier block as merge-ask prints it."""
        reasons = [f"- {r.text}" for r in self.reasons]
        return [f"Tier: {self.n}", *reasons, f"Waits for: {self.waits}"]


# a column-0 line starting `Owner decision` up to its first colon (#1184 wrote `Owner decision 1
# (...): ...`); it only raises a tier, so the looser match is the safe side
OWNER_DECISION = re.compile(r"Owner decision[^:\n]*:", re.IGNORECASE)
OWNER_TIER = 3  # the tier that waits for the owner, whatever the merge order names


def sets_back(o: Order) -> list[str]:
    """`PR #N: <why>` for each other open PR O names this merge sets back, or may: its head
    conflicting with this one, a pinned run this merge newly stales, a pinned run not read
    (merge_order's own findings); then `not read: <line>` for each read of O that failed. A read
    that failed cannot prove no PR is set back, so it waits as one that is."""
    out: list[str] = []
    for p in o.prs:
        files = ", ".join(p.conflicts)
        why = [f"its head conflicts with this head in {files}"] if files else []
        for pin in p.pins:
            was, now = _stale(pin.main), _stale(pin.merged)
            if was is None or now is None:
                why.append(f"its pinned run {pin.run} not read")
            elif [x for x in now if x not in was]:
                why.append(f"this merge stales its pinned run {pin.run}")
        if why:
            out.append(f"PR #{p.number}: {' and '.join(why)}")
    return out + [f"not read: {u}" for u in o.unread]


def tier(s: Snapshot) -> Tier:
    """S's tier from the records the ask already holds (the rule: octo-feather-lane --help,
    merge-ask)."""
    lines = section(s.body) or []
    fails = failed(s, lines)[1]
    reasons = [Reason(3, f"failed criterion {c}{': ' + w if w else ''}") for c, w in fails.items()]
    hdr = _verdict_header(s, lines)
    owner, cleared, _ = decision_lines(hdr)
    clear = set(verdicts(hdr)) == {"clear"}
    said = [ln.strip() for ln in lines if OWNER_DECISION.match(ln)]
    reasons += [Reason(3, ln) for ln in dict.fromkeys([*said, *(x.strip() for x in owner)])]
    reasons += _opt_out_reasons(s.optouts, cleared if clear else [])
    declared = [c for c in check_lines(hdr)[0] if c.endswith(DECLARATION)] if clear else []
    reasons += [Reason(3, "declaration check: " + c.removeprefix("Check: ")) for c in declared]
    seen: set[str] = set()  # a path either end's file gives the owner, named once (head first)
    for o in s.owners if isinstance(s.owners, tuple) else ():
        for p, n, ln in o.paths:
            if p not in seen:
                seen.add(p)
                reasons.append(
                    Reason(3, f"code owner: {p} is {o.owner}'s ({o.file} line {n}: `{ln}`)")
                )
    reasons += call_reasons(s, lines)
    n = max((r.tier for r in reasons), default=1)
    back = sets_back(s.order) if s.order else []
    if n >= OWNER_TIER:
        waits = "the owner"
    elif back:
        waits = f"the director's order ({'; '.join(back)})"
    else:
        waits = "nobody"
    return Tier(n, reasons, waits)


def relay_proof(s: Snapshot, relayed: str, head: str) -> tuple[str | None, list[str]]:
    """(proof line, []) when the director's relay recorded for the full head RELAYED carries to
    the full HEAD over S's git facts, else (None, why) (when it carries: octo-feather-lane --help,
    merge, allowed)."""
    r, h = relayed.lower(), head.lower()
    rerun = f"send a new merge ask for {h[:12]}"
    p = _why(_proved(s, r, h, at="relayed head", kept="the director's relay", rerun=rerun))
    if p[0] is None or r == h:
        return p
    g = s.git or Git("")
    gone = set(g.walks[r])
    fixes = [c for c in g.walks[h] if c not in gone and len(g.commits[c].parents) == 1]
    why = [
        f"commit {c[:12]} {g.commits[c].subject[:60]!r} after the relayed head {r[:12]} is no "
        f"merge of main: the director's relay does not carry over; {rerun}"
        for c in fixes
    ]
    return (None, why) if why else p


def _opt_out_reasons(
    optouts: list[tuple[str, str]] | Unread | None, cleared: list[str]
) -> list[Reason]:
    """A reason per behaviour-neutral opt-out, CLEARED the commits a clear verdict names (the
    rule: octo-feather-lane --help, merge-ask)."""
    if isinstance(optouts, Unread):
        return [Reason(3, f"behaviour-neutral opt-outs not read: {optouts.why}")]
    out: list[Reason] = []
    for sha, why in optouts or []:
        if any(c.startswith(sha) or sha.startswith(c) for c in cleared):
            out.append(Reason(2, f"opt-out {sha} cleared by the review verdict: {why}"))
        else:
            out.append(Reason(3, f"opt-out {sha} not cleared by the review verdict: {why}"))
    return out


def _optouts(head: str, base: str) -> list[tuple[str, str]] | Unread:
    """The lane's behaviour-neutral opt-outs, (commit, `Behaviour-neutral: <reason>`) each, as
    the kit's check-behavior-smoke prints them for BASE..HEAD in this repo (#1259)."""
    try:
        top = git("rev-parse", "--show-toplevel", err=_Unread)[1].strip()
    except _Unread as e:
        return Unread(str(e))
    cmd = [sys.executable, str(KIT / "scripts" / "check-behavior-smoke")]
    p = subprocess.run(
        [*cmd, "--base", base, "--head", head, "--repo", top],
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
        check=False,
    )
    out = p.stdout.splitlines()
    if p.returncode not in (0, 1) or any(ln.startswith("behavior smoke: skipped") for ln in out):
        said = (p.stdout + p.stderr).strip().splitlines()
        return Unread(f"check-behavior-smoke exit {p.returncode}: {said[-1] if said else ''}")
    found = [m for ln in out if (m := OPT_OUT.match(ln))]
    return [(m.group(1).lower(), f"Behaviour-neutral: {m.group(2)}") for m in found]


def code_owner_gaps(o: tuple[Owned, ...] | Unread | None) -> list[str]:
    """The code owners files' refusal lines: their read that failed, or each line whose pattern git
    reads otherwise than GitHub, named (CODE_OWNERS_DIFFER): never a guessed owner."""
    if isinstance(o, Unread):
        return [f"code owners: {o.why}"]
    return [
        (
            f"code owners: {f.file} line {n} `{ln}`: {why}; git's matcher would read another owner "
            "than GitHub, so no path is sorted: write the line in syntax both read alike "
            "(octo-feather-lane --help, merge-ask)"
        )
        for f in o or ()
        for n, ln, why in f.refused
    ]


# The code owners file (spec #gates-tier-areas; issue #1260): where GitHub looks, in its order, the
# first found the one read (docs.github.com, About code owners).
CODE_OWNERS = (".github/CODEOWNERS", "CODEOWNERS", "docs/CODEOWNERS")
# A CODEOWNERS pattern follows gitignore's rules, matched here by git's own matcher (_owned), save
# where GitHub reads the syntax otherwise (docs.github.com, About code owners: no `\#` escape, no
# `!` negation, no `[ ]` range; the rest as GitHub was seen to read it, github.com/chdsbd/
# gh-codeowners examples/CODEOWNERS). A line using one is refused, naming it, never matched.
CODE_OWNERS_DIFFER: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"!"), "`!` negates in git, GitHub reads no negation"),
    (re.compile(r"[\[\]]"), "`[ ]` is a range in git, GitHub has none and skips the line"),
    (re.compile(r"\\"), "`\\` escapes in git (`\\#` a pattern starting with #), not in GitHub"),
    (re.compile(r"\*\*\*"), "git reads `***` as `**`, GitHub skips the line"),
    (re.compile(r"\*\*/$"), "a last `**/` matches directories only in git, files too in GitHub"),
    (re.compile(r"^/+$"), "git reads a bare `/` otherwise than GitHub, which matches nothing"),
    (re.compile(r"/\*$"), "a last `/*` matches direct files only in GitHub, all below in git"),
)


def code_owner_differs(pattern: str) -> str | None:
    """Why git reads PATTERN, a CODEOWNERS line's first field, otherwise than GitHub; None when
    both read it alike (CODE_OWNERS_DIFFER)."""
    return next((why for rx, why in CODE_OWNERS_DIFFER if rx.search(pattern)), None)


# The lane's spec calls (spec #gates-tiers, #gates-spec-calls, #gates-call-loudness; issue #1258)

RULING_COVERS = re.compile(r"^Ruling covers:[ \t]*(.*?)\s*$")


@dataclass(frozen=True)
class Call:
    """A spec call: its spec's SLUG (its log `<slug>.calls.jsonl`) and the fields the call log
    holds (scripts/octo-feather-spec-status docstring): AT, KIND, ANCHORS, RULING ('' for none)
    and DENIED, the owner's denial's `at` ('' for none)."""

    slug: str
    at: str
    kind: str
    anchors: tuple[str, ...]
    ruling: str = ""
    denied: str = ""

    @property
    def name(self) -> str:
        return f"spec call {self.slug} {self.at} {self.kind} {', '.join(self.anchors)}"


@dataclass(frozen=True)
class Calls:
    """The calls the lane diff adds (ADDED, each log's in its order), and RULINGS: for each call
    not denied that links a ruling of its form (scripts/octo-feather-spec-status, RULING),
    GitHub's created_at of that issue or comment, or why it was not read."""

    added: list[Call]
    rulings: dict[str, str | Unread]


def ruling_covers(text: str) -> list[str]:
    """Each `Ruling covers: <url>` line's value in TEXT, in the verdict reader's scope, in order
    (octo-feather-lane verdict checks its form, ruling_form)."""
    return [m.group(1) for ln in outside(text) if (m := RULING_COVERS.match(ln))]


def ruling_form(url: str) -> bool:
    """URL is of a call's ruling's form (scripts/octo-feather-spec-status, RULING)."""
    return bool(_spec_status().RULING.fullmatch(url))


def _verdict_header(s: Snapshot, lines: list[str]) -> str:
    """The header of the review verdict comment the section's `Review verdict:` links ('' for
    none): the helper's own lines, never the quoted report."""
    rv = field(lines, "Review verdict")
    m = COMMENT_URL.fullmatch(rv[1].strip("<>` ")) if rv else None
    c = next((c for c in s.comments if m and c.url.endswith(f"#issuecomment-{m.group(3)}")), None)
    if not c or not c.body.lstrip().startswith(MARKER):
        return ""
    return c.body.split("\n### Findings", 1)[0]


def _instant(t: str) -> dt.datetime | None:
    try:
        return dt.datetime.fromisoformat(t)
    except ValueError:
        return None


def call_reasons(s: Snapshot, lines: list[str]) -> list[Reason]:
    """A reason per call the lane diff adds, by the rule and in the form octo-feather-lane --help
    (merge-ask, the tier) states."""
    if s.calls is None:
        return []
    if isinstance(s.calls, Unread):
        return [Reason(3, f"spec calls not read: {s.calls.why}")]
    covers = ruling_covers(_verdict_header(s, lines))
    out: list[Reason] = []
    for c in s.calls.added:
        if c.denied:
            out.append(Reason(2, f"{c.name}: denied {c.denied}"))
        elif c.kind == "clarifies":
            out.append(Reason(2, c.name))
        else:
            out.append(_ruled(c, s.calls.rulings.get(c.ruling), covers))
    return out


def _ruled(c: Call, made: str | Unread | None, covers: list[str]) -> Reason:
    """Call_reasons' reason for C, of a kind other than clarifies and not denied: MADE its
    ruling's created_at (None: no ruling of the form _calls reads), COVERS the verdict's
    `Ruling covers:` URLs."""
    r = c.ruling
    if not r:
        return Reason(3, f"{c.name}: no ruling linked")
    if made is None:  # _calls reads every ruling of the form
        return Reason(3, f"{c.name}: ruling {r} is no GitHub issue or issue comment URL")
    if isinstance(made, Unread):
        return Reason(3, f"{c.name}: ruling {r} not read ({made.why})")
    at, when = _instant(c.at), _instant(made)
    if not at or not when or when >= at:
        return Reason(3, f"{c.name}: ruling {r} made {made}, not before the call")
    if r not in covers:
        why = f"the review verdict carries no `Ruling covers: {r}`"
        return Reason(3, f"{c.name}: ruling {r} ({made}) not confirmed: {why}")
    return Reason(2, f"{c.name}: ruled by {r} ({made}), the review verdict covers it")


def _calls(head: str, fork: str) -> Calls:
    """Calls' reads: each `*.calls.jsonl` the lane diff (FORK to HEAD) changes, at both ends; a
    call at HEAD not at FORK (scripts/octo-feather-spec-status's identity: a call denied since is
    the same call) is added; then each such ruling's created_at (gh api). _Unread on a log that is
    not one JSON call per line."""
    spec_status = _spec_status()
    diff = git("diff", "--name-only", "--no-renames", "-z", fork, head, err=_Unread)[1]
    added: list[Call] = []
    for f in sorted(p for p in diff.split("\0") if p.endswith(".calls.jsonl")):
        ends: list[list[dict[str, object]]] = []
        for rev in (fork, head):
            rc, text = git("show", f"{rev}:{f}", ok=(0, 128), err=_Unread)
            got, errs = spec_status.parse_log("" if rc else text, f"{f} at {rev[:12]}")
            if errs:
                raise _Unread(errs[0])
            ends.append(got)
        seen = [spec_status.identity(c) for c in ends[0]]
        for c in ends[1]:
            if (k := spec_status.identity(c)) in seen:
                seen.remove(k)
                continue
            denied = c.get("denied")
            anchors = c.get("anchors")
            added.append(
                Call(
                    Path(f).name.removesuffix(".calls.jsonl"),
                    str(c.get("at", "")),
                    str(c.get("kind", "")),
                    tuple(map(str, cast("list[object]", anchors)))
                    if isinstance(anchors, list)
                    else (),
                    str(c.get("ruling") or ""),
                    str(cast("dict[str, object]", denied).get("at") or "denied")
                    if isinstance(denied, dict) and denied
                    else "",
                )
            )
    rulings: dict[str, str | Unread] = {}
    for c in added:
        m = spec_status.RULING.fullmatch(c.ruling)
        if c.denied or c.kind == "clarifies" or not m or c.ruling in rulings:
            continue
        repo, n, comment = m.groups()
        path = f"repos/{repo}/issues/comments/{comment}" if comment else f"repos/{repo}/issues/{n}"
        try:
            fix = f"read the ruling {c.ruling} (gh auth status)"
            rulings[c.ruling] = gh(["api", path, "--jq", ".created_at"], fix, err=_Unread).strip()
        except _Unread as e:
            rulings[c.ruling] = Unread(str(e))
    return Calls(added, rulings)


@functools.cache
def _spec_status() -> "_SpecStatus":
    """scripts/octo-feather-spec-status, the call log's owner, as a module."""
    loader = importlib.machinery.SourceFileLoader(
        "spec_status", str(KIT / "scripts" / "octo-feather-spec-status")
    )
    spec = importlib.util.spec_from_loader("spec_status", loader)
    assert spec is not None, "a SourceFileLoader always yields a spec"
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return cast("_SpecStatus", mod)


class _SpecStatus(Protocol):
    RULING: re.Pattern[str]

    def parse_log(self, text: str, where: str) -> tuple[list[dict[str, object]], list[str]]: ...
    def identity(self, c: dict[str, object]) -> str: ...


# The merge-order reads (spec #gates-merge-order)


class _UnreadError(Exception):
    """A merge-order read that failed, kept as one Order.unread line."""


QA = KIT / "scripts" / "octo-feather-qa"
CONTRACT = KIT / "scripts" / "octo-feather-contract"
GH_PRS = KIT / "schemas" / "gh-pr-list.schema.json"
# The kit's locked jsonschema, by octo-feather-contract's route (its docstring): this module stays
# standard library only, so the validation runs in the kit's project environment, never the network.
KIT_PYTHON = ["uv", "run", "--project", str(KIT), "--locked", "--offline", "--no-dev", "--quiet"]
VALIDATE = """import json, sys, jsonschema
a = sys.argv[1]  # a schema file, or a schema's JSON text
schema = json.loads(a if a.startswith("{") else open(a, encoding="utf-8").read())
v = jsonschema.validators.validator_for(schema)
v.check_schema(schema)
try:
    doc = json.loads(sys.stdin.read())
except ValueError as e:
    sys.exit(f"not JSON: {e}")
for e in v(schema).iter_errors(doc):
    print(f"{'.'.join(map(str, e.absolute_path)) or 'the answer'}: {e.message}", file=sys.stderr)
    sys.exit(1)
"""
SHELL_OPS = {";", "&&", "||", "|", "&", "(", ")"}
IDENT = {
    f"GIT_{who}_{k}": v
    for who in ("AUTHOR", "COMMITTER")
    for k, v in (("NAME", "merge-ask"), ("EMAIL", "merge-ask@localhost"))
}


def _git(*args: str, ok: tuple[int, ...] = (0,)) -> tuple[int, str]:
    """git ARGS in the current repo: (exit, stdout); _UnreadError naming it on another exit."""
    p = subprocess.run(
        ["git", *args],  # noqa: S607 (git from PATH, as the command runs it)
        capture_output=True,
        text=True,
        env={**os.environ, **IDENT},
        check=False,
    )
    if p.returncode not in ok:
        said = (p.stderr or p.stdout).strip().splitlines()
        msg = f"git {' '.join(args[:2])} failed ({said[-1][:200] if said else p.returncode})"
        raise _UnreadError(msg)
    return p.returncode, p.stdout


def _pins(command: str) -> list[str]:
    """The RUN_ID/SUITE/CASE arguments of each `octo-feather-qa --verdict` in shell COMMAND."""
    lex = shlex.shlex(command, posix=True, punctuation_chars=True)
    lex.whitespace_split = True
    words = list(lex)
    out: list[str] = []
    for i, w in enumerate(words[:-1]):
        if Path(w).name == "octo-feather-qa" and words[i + 1] == "--verdict":
            for a in words[i + 2 :]:
                if a.startswith("-") or a in SHELL_OPS:
                    break
                out.append(a)
    return out


class _Demo(TypedDict, total=False):
    """A qc.toml demo entry as the contract's schema (schemas/qc.v*.schema.json) admits it: the
    key the merge order reads."""

    command: str


def _said(p: subprocess.CompletedProcess[str], prefix: str = "") -> str:
    """P's stderr lines, PREFIX cut from each, joined; its exit when it printed none."""
    lines = [ln.removeprefix(prefix) for ln in p.stderr.strip().splitlines()]
    return "; ".join(lines)[:300] or f"exit {p.returncode}"


def _demo_pins(oid: str) -> list[str]:
    """The pins of every qc.toml demo at commit OID, the contract validated first by
    octo-feather-contract; none without a qc.toml there."""
    rc, text = _git("show", f"{oid}:qc.toml", ok=(0, 128))
    if rc:
        return []
    with tempfile.TemporaryDirectory(prefix="merge-ask-qc-") as tmp:
        path = Path(tmp) / "qc.toml"
        path.write_text(text, encoding="utf-8")
        p = subprocess.run([str(CONTRACT), str(path)], capture_output=True, text=True, check=False)
    if p.returncode:
        why = _said(p, f"octo-feather-contract: {path}: ")
        msg = f"qc.toml at {oid[:12]} fails octo-feather-contract ({why})"
        raise _UnreadError(msg)
    # valid against its format's schema above: [demo] a table of tables, each command a string
    demos = cast("dict[str, _Demo]", tomllib.loads(text).get("demo", {}))
    cmds = [d["command"] for d in demos.values() if "command" in d]
    return list(dict.fromkeys(p for c in cmds for p in _pins(c)))


def _merge_tree(ours: str, theirs: str) -> tuple[str, list[str]]:
    """(the tree git merge-tree writes for OURS and THEIRS, the files in conflict)."""
    rc, out = _git(
        "merge-tree", "--write-tree", "--name-only", "--no-messages", ours, theirs, ok=(0, 1)
    )
    lines = out.splitlines()
    if not lines or not re.fullmatch(r"[0-9a-f]{40,64}", lines[0]):
        msg = f"git merge-tree of {ours[:12]} and {theirs[:12]} printed no tree"
        raise _UnreadError(msg)
    return lines[0], list(dict.fromkeys(lines[1:])) if rc else []


def _merged(base: str, head: str, name: str) -> str:
    """A commit of BASE (NAME) merged with HEAD (git merge-tree, then commit-tree: no ref moved)."""
    tree, conflicts = _merge_tree(base, head)
    if conflicts:
        msg = f"this head does not merge cleanly with {name} ({', '.join(conflicts)})"
        raise _UnreadError(msg)
    return _git("commit-tree", tree, "-p", base, "-p", head, "-m", f"merge-ask: {name} + head")[
        1
    ].strip()


def _verdicts(rev: str, pins: list[str]) -> list[str]:
    """octo-feather-qa --verdict PINS, run in a scratch detached worktree at REV: a line per pin."""
    with tempfile.TemporaryDirectory(prefix="merge-ask-order-") as tmp:
        wt = str(Path(tmp) / "wt")
        _git("worktree", "add", "-q", "--detach", wt, rev)
        try:
            p = subprocess.run(
                [str(QA), "--verdict", *pins], capture_output=True, text=True, cwd=wt, check=False
            )
        finally:
            _git("worktree", "remove", "--force", wt, ok=(0, 128))
    lines = p.stdout.splitlines()
    if p.returncode not in (0, 1, 77) or len(lines) != len(pins):
        said = p.stderr.strip().splitlines()
        msg = (
            f"octo-feather-qa --verdict at {rev[:12]} exited {p.returncode}"
            f" ({said[-1][:200] if said else 'no error line'})"
        )
        raise _UnreadError(msg)
    return lines


class _GhPR(TypedDict):
    """A gh pr list row, as schemas/gh-pr-list.schema.json admits it."""

    number: int
    headRefName: str
    headRefOid: str


class _Open(NamedTuple):
    """An open PR the merge order reads."""

    number: int
    branch: str
    oid: str


def _open_prs(pr: int, base_branch: str, repo: str | None) -> list[_Open]:
    """Every open PR but PR on BASE_BRANCH, by number; gh's answer validated first against
    schemas/gh-pr-list.schema.json."""
    fields = "number,headRefName,headRefOid"
    args = ["pr", "list", "--state", "open", "--base", base_branch, "--limit", "200"]
    out = gh(
        [*args, "--json", fields, *(["-R", repo] if repo else [])],
        "check gh auth status, then rerun",
        err=_UnreadError,
    )
    env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}
    try:
        p = subprocess.run(
            [*KIT_PYTHON, "python", "-c", VALIDATE, str(GH_PRS)],
            input=out,
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
    except OSError as e:
        msg = f"cannot run uv for the kit's locked jsonschema ({e})"
        raise _UnreadError(msg) from e
    if p.returncode:
        msg = f"gh pr list's answer fails schemas/gh-pr-list.schema.json ({_said(p)})"
        raise _UnreadError(msg)
    rows = cast("list[_GhPR]", json.loads(out))  # valid above
    got = [_Open(r["number"], r["headRefName"], r["headRefOid"]) for r in rows]
    return sorted(x for x in got if x.number != pr)


def _sibling(
    head: str, n: int, branch: str, oid: str
) -> tuple[int, str, list[str], list[str]] | str:
    """PR N's (number, branch, files in conflict with HEAD, pins), its head OID fetched when this
    repo lacks it; the unread line when a read fails."""
    try:
        if _git("cat-file", "-e", f"{oid}^{{commit}}", ok=(0, 1, 128))[0]:
            _git("fetch", "-q", "--no-write-fetch-head", "origin", f"pull/{n}/head")
        return n, branch, _merge_tree(head, oid)[1], _demo_pins(oid)
    except _UnreadError as e:
        return f"PR #{n} ({branch}) head {oid[:12]}: {e}"


def _order(pr: int, head: str, base_branch: str, base: str, repo: str | None) -> Order:
    """The Order the reads give for PR at HEAD on BASE_BRANCH (BASE the ref to merge with, REPO
    gh's; spec #gates-merge-order); each failed read one unread line."""
    try:
        rows = _open_prs(pr, base_branch, repo)
    except _UnreadError as e:
        return Order(base_branch, [], [f"open pull requests on {base_branch}: {e}"])
    read = [_sibling(head, *r) for r in rows]
    found = [x for x in read if not isinstance(x, str)]
    unread = [x for x in read if isinstance(x, str)]
    pins = list(dict.fromkeys(p for *_, ps in found for p in ps))
    said: dict[str, tuple[str, str]] = {}
    if pins:
        try:
            main = _git("rev-parse", "--verify", f"{base}^{{commit}}")[1].strip()
            at_main = _verdicts(main, pins)
            at_merged = _verdicts(_merged(main, head, base), pins)
            said = {p: (a, b) for p, a, b in zip(pins, at_main, at_merged, strict=True)}
        except _UnreadError as e:
            unread.append(f"pinned runs {' '.join(pins)}: {e}")
    prs = [Sibling(n, b, c, [Pin(p, *said[p]) for p in ps if p in said]) for n, b, c, ps in found]
    return Order(base_branch, prs, unread)


# The code owners reads (#1260; the rule: tier, code_owner_gaps, above)


class _Line(NamedTuple):
    """A code owners line git and GitHub read alike: its NUMBER, TEXT, PATTERN and OWNERS."""

    number: int
    text: str
    pattern: str
    owners: tuple[str, ...]


def _code_owners(head: str, fork: str, repo: str | None) -> tuple[Owned, ...] | Unread | None:
    """The code owners file at HEAD and at FORK, the merge base (as GitHub reads the base's, so a
    lane editing the file never lowers its own tier: either end's file only raises), each with
    each path the lane changes (git diff FORK HEAD, renames as a delete and an add) its last
    matching line gives to REPO's owner (None: this directory's gh repo, gh repo view); the head's
    first. None when neither end has such a file (no FORK read: the head's alone). A line either
    file's git and GitHub read otherwise (code_owner_differs) is refused and nothing matched."""
    try:
        ends = [(head, "")]
        if fork:
            ends.append((fork, f" at the merge base {fork[:12]}"))
        found: list[tuple[str, list[_Line], tuple[tuple[int, str, str], ...]]] = []
        for rev, at in ends:
            rcs = (
                git("cat-file", "-e", f"{rev}:{f}", ok=(0, 1, 128), err=_Unread)[0]
                for f in CODE_OWNERS
            )
            file = next((f for f, rc in zip(CODE_OWNERS, rcs, strict=False) if not rc), None)
            if file is not None:
                text = git("show", f"{rev}:{file}", err=_Unread)[1]
                found.append((file + at, *_code_owner_lines(text)))
        if not found:
            return None
        if any(refused for *_, refused in found):
            return tuple(Owned(f, "", refused=r) for f, _, r in found if r)
        if repo is None:
            out = gh(
                ["repo", "view", "--json", "nameWithOwner"], "check gh auth status", err=_Unread
            )
            repo = cast("_NamedRepo", _validated(out, NAMED_REPO, "gh repo view"))["nameWithOwner"]
        owner = f"@{repo.split('/', 1)[0]}"
        diff = git("diff", "--name-only", "--no-renames", "-z", fork, head, err=_Unread)[1]
        paths = sorted(filter(None, diff.split("\0")))
        return tuple(Owned(f, owner, _owned(paths, lines, owner)) for f, lines, _ in found)
    except _Unread as e:
        return Unread(f"cannot read the code owners file at {head[:12]} ({e}); fix it, then rerun")


def _code_owner_lines(text: str) -> tuple[list[_Line], tuple[tuple[int, str, str], ...]]:
    """(the lines of code owners file TEXT git and GitHub read alike, each other line's number,
    text and why), comments and blank lines aside; an owner field starting `#` ends the line."""
    lines: list[_Line] = []
    refused: list[tuple[int, str, str]] = []
    for n, raw in enumerate(text.splitlines(), 1):
        words = raw.split()
        if not words or words[0].startswith("#"):
            continue
        if why := code_owner_differs(words[0]):
            refused.append((n, raw.strip(), why))
            continue
        owners: list[str] = []
        for w in words[1:]:
            if w.startswith("#"):
                break
            owners.append(w)
        lines.append(_Line(n, raw.strip(), words[0], tuple(owners)))
    return lines, tuple(refused)


def _owned(paths: list[str], lines: list[_Line], owner: str) -> tuple[tuple[str, int, str], ...]:
    """Each of PATHS whose last matching line of LINES names OWNER (case aside, as GitHub logins),
    with that line's number and text. git check-ignore --no-index (the real matcher, in an empty
    scratch repo, case-sensitive as GitHub) runs one line at a time, the last first: over all the
    lines at once git stops at the first leading directory any line matches (`*` then `*.js`
    gives src/x.js to `*`), where GitHub takes the last line matching the path."""
    left, out = set(paths), list[tuple[str, int, str]]()
    env = {k: v for k, v in os.environ.items() if k not in ("GIT_DIR", "GIT_WORK_TREE")}
    with tempfile.TemporaryDirectory(prefix="merge-ask-owners-") as tmp:
        r, pat = Path(tmp) / "r", Path(tmp) / "pattern"
        _run_git(["init", "-q", "--template=", str(r)], cwd=tmp, env=env)
        for ln in reversed(lines):
            if not left:
                break
            pat.write_text(ln.pattern + "\n", encoding="utf-8")
            args = ["-c", f"core.excludesFile={pat}", "-c", "core.ignorecase=false"]
            args += ["check-ignore", "--no-index", "-v", "-n", "-z", "--stdin"]
            f = _run_git(args, cwd=str(r), env=env, stdin="".join(f"{p}\0" for p in sorted(left)))
            f = f.split("\0")  # source, line number, pattern (empty: none), path; per path
            hit = {f[i + 3] for i in range(0, len(f) - 3, 4) if f[i + 2]}
            left -= hit
            if owner.lower() in (o.lower() for o in ln.owners):
                out += [(p, ln.number, ln.text) for p in hit]
    return tuple(sorted(out))


def _run_git(args: list[str], *, cwd: str, env: dict[str, str], stdin: str = "") -> str:
    """git ARGS in CWD with ENV and STDIN: its stdout; _Unread naming it on an exit past 1."""
    p = subprocess.run(
        ["git", *args],  # noqa: S607 (git from PATH)
        input=stdin,
        capture_output=True,
        text=True,
        cwd=cwd,
        env=env,
        check=False,
    )
    if p.returncode > 1:
        sub = next(a for a in args if a in ("init", "check-ignore"))
        msg = f"git {sub} failed ({_said(p)})"
        raise _Unread(msg)
    return p.stdout


# The correction lane's replay reads (#1222; the rule: replay, above)

MARKED = re.compile(
    re.escape(MARK.split("{}")[0]) + r"([^\]\s]+)[^\]]*" + re.escape(MARK.split("{}")[1])
)
REPLAY_TIMEOUT = 120  # seconds a row's sandboxed run may take, then it is not replayable
UNAVAILABLE = "sandbox unavailable"
SAMPLE = 5  # the clean lanes the fixed rule names (#1218 design, term 4)


def _replay(
    s: Snapshot, classes: list[str], repo: str | None, lanes: Path
) -> Replay | Unread | None:
    """S's Replay when its parent issue's title carries the correction-lane marker and CLASSES,
    the verdict's check lines, name a Check path; None when not; Unread naming the read that
    failed. REPO gh's (None: this directory's), LANES the state dir's lanes/."""
    shapes = (CHECK_SHAPE.fullmatch(c.removeprefix("Check: ")) for c in classes)
    paths = tuple(dict.fromkeys(m.group(1) for m in shapes if m))
    if not paths or not isinstance(s.parent, ParentLine):
        return None
    key = s.parent.key
    try:
        cls = _marked(key)
        if cls is None:
            return None
        out = tracker("issue-view", key, "--notes", err=_Unread)
        got = cast("_Noted", _validated(out, NOTED, f"issue-view {key} --notes"))
        texts = [n["body"] for n in got["notes"]]
        findings = tuple(dict.fromkeys(f"{run} {at}" for t in texts for _, (run, at) in quoted(t)))
        sample = _sample(s, cls, repo, lanes)
        table = _replay_table(s.body)
        rows = [
            row
            for row in dict.fromkeys((table or ([], []))[0])
            if row.result in CLAIMS and _program(row.command) in paths
        ]
        named = [key, *(t for row in rows for t in re.findall(r"#(\d+)", row.case))]
        issues = tuple(dict.fromkeys(int(t) for t in named if t.isdigit()))
        runs = _runs(s.head, rows, issues) if rows else {}
    except _Unread as e:
        return Unread(f"cannot read correction lane facts for #{key} ({e}); fix it, then rerun")
    return Replay(key, cls, paths, findings, sample, runs, table)


def _marked(key: str) -> str | None:
    """The class issue KEY's title marker (correction_lanes.MARK) names; None for no marker."""
    out = tracker("issue-view", key, err=_Unread)
    view = cast("_Titled", _validated(out, TITLED, f"issue-view {key}"))
    m = MARKED.search(view["title"])
    return m.group(1) if m else None


# Each tracker and gh answer the replay reads, validated once at its edge (quality spec
# #acceptance-edge-validated) by the kit's locked jsonschema (VALIDATE), then typed: only the
# fields read, each required with its type; the tools' other fields pass.
TITLED = {"type": "object", "required": ["title"], "properties": {"title": {"type": "string"}}}
NOTED = {  # issue-view --notes (github-issues SKILL.md; skills spec #tracker-script-issue-view)
    "type": "object",
    "required": ["notes"],
    "properties": {
        "notes": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["body"],
                "properties": {"body": {"type": "string"}},
            },
        }
    },
}
NAMED_REPO = {  # gh repo view --json nameWithOwner
    "type": "object",
    "required": ["nameWithOwner"],
    "properties": {"nameWithOwner": {"type": "string", "pattern": "^[^/\\s]+/[^/\\s]+$"}},
}


class _Titled(TypedDict):
    title: str


class _Note(TypedDict):
    body: str


class _Noted(TypedDict):
    notes: list[_Note]


class _NamedRepo(TypedDict):
    nameWithOwner: str  # gh's field


def _kit(script: str, *args: str, stdin: str, what: str) -> str:
    """SCRIPT's stdout, run by the kit's locked Python (KIT_PYTHON, offline) with ARGS and STDIN;
    _Unread naming WHAT and its stderr when it fails or cannot run."""
    env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}
    try:
        p = subprocess.run(
            [*KIT_PYTHON, "python", "-c", script, *args],
            input=stdin,
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
    except OSError as e:
        msg = f"cannot run uv for the kit's locked environment ({e})"
        raise _Unread(msg) from e
    if p.returncode:
        msg = f"{what}: {_said(p)}"
        raise _Unread(msg)
    return p.stdout


def _validated(out: str, schema: Mapping[str, object], what: str) -> object:
    """OUT, WHAT's JSON answer, once SCHEMA holds for it (VALIDATE: the failing field named)."""
    _kit(VALIDATE, json.dumps(schema), stdin=out, what=f"{what} answered no valid JSON")
    return json.loads(out)


# The `## Replay` section read by markdown-it-py (pinned in pyproject.toml and uv.lock) in the
# kit's locked environment, as VALIDATE is; what it reads as a row: octo-feather-lane --help,
# merge-ask. Prints {"section": bool, "tables": [{"head": [cell...], "rows": [[cell...]...]}...]}.
REPLAY_TABLE = """import json, sys
from markdown_it import MarkdownIt
tokens = MarkdownIt("commonmark").enable("table").parse(sys.stdin.read())
section, inside, head, tables, row = False, False, False, [], None
for i, t in enumerate(tokens):
    if t.type == "heading_open" and t.tag in ("h1", "h2"):
        inside = t.tag == "h2" and tokens[i + 1].content.strip().lower() == "replay"
        section = section or inside
    elif inside and t.type == "table_open":
        tables.append({"head": [], "rows": []})
    elif inside and t.type == "tr_open":
        row = []
    elif inside and t.type == "inline" and row is not None:
        row.append("".join(c.content for c in t.children or []).strip())
    elif inside and t.type in ("thead_open", "thead_close"):
        head = t.type == "thead_open"
    elif inside and t.type == "tr_close":
        if head:
            tables[-1]["head"] = row
        else:
            tables[-1]["rows"].append(row)
        row = None
print(json.dumps({"section": section, "tables": tables}))
"""


class _Table(TypedDict):
    head: list[str]
    rows: list[list[str]]


class _Section(TypedDict):
    section: bool
    tables: list[_Table]


def _replay_table(body: str) -> tuple[list[Row], list[str]] | None:
    """(the `## Replay` section's rows in BODY, why a table or row of it is no row, empty fields
    named); None when BODY has no such section. The rule: octo-feather-lane --help, merge-ask."""
    out = _kit(REPLAY_TABLE, stdin=body or "", what="the PR body's Markdown (markdown-it-py)")
    got = cast("_Section", json.loads(out))  # REPLAY_TABLE's own answer, its shape above
    if not got["section"]:
        return None
    form = f"`| {' | '.join(REPLAY_HEAD)} |`"
    rows: list[Row] = []
    bad: list[str] = []
    for t in got["tables"]:
        if tuple(c.lower() for c in t["head"]) != REPLAY_HEAD:
            bad.append(f"table `| {' | '.join(t['head'])} |` is not {form}")
            continue
        for n, cells in enumerate(t["rows"], 1):
            row = Row(*cells)
            empty = [f for f, v in zip(REPLAY_HEAD, cells, strict=True) if not v]
            if empty:
                who = row.finding or f"#{n} of the table"
                bad.append(f"row `{who}`: {', '.join(empty)} empty; a row is {form}")
                continue
            rows.append(row)
    return rows, bad


def _runs(head: str, rows: list[Row], issues: tuple[int, ...]) -> dict[Row, Replayed]:
    """Each of ROWS run in its own qc sandbox (octo-feather-qc sandboxed(), as its capture() runs a
    demo: writes discarded, no Pi, no network) over this worktree, which must be at HEAD, and one
    offline read-only GitHub snapshot (octo-feather-qc github_snapshot(), ISSUES in full) for all
    of them. A row the sandbox cannot serve gets Replayed.unserved, never a run outside it."""
    qc = _qc()
    at = git("rev-parse", "HEAD", err=_Unread)[1].strip()
    if at != head:
        why = f"this worktree is at {at[:12]}, not the PR head {head[:12]}: rerun there"
        return dict.fromkeys(rows, Replayed(None, "", why))
    runid = os.urandom(3).hex()
    snap, said = _quiet(qc.github_snapshot, False, runid, issues)  # noqa: FBT003  qc's own
    if snap is None:  # its fetch failed (67)
        return dict.fromkeys(rows, Replayed(None, "", f"no GitHub snapshot: {said}"))
    try:
        return {
            row: _run(qc, row.command, snap, f"merge-ask-{head[:12]}-{runid}-r{n}")
            for n, row in enumerate(rows)
        }
    finally:
        if "dir" in snap:
            qc.drop(str(snap["dir"]))


class _Record(TypedDict, total=False):
    """The fields of a qc sandbox record (octo-feather-qc sandboxed();
    scripts/octo-feather-qc-sandbox, steps 7 and 10) a replay reads: the proof lines, the attempt
    record or why it is missing, the overlay upper dir's entries ([kind, path])."""

    proof: list[str]
    attempts: list[dict[str, object]]
    attempts_error: str
    upper: list[list[str]]


class _Qc(Protocol):
    """What a replay uses of scripts/octo-feather-qc (_qc): its one sandbox and snapshot."""

    def github_snapshot(
        self,
        skip: bool,  # noqa: FBT001  qc's own signature
        runid: str,
        issues: tuple[int, ...],
    ) -> dict[str, object]: ...

    def sandboxed(
        self, judge: list[str], session: str, gh: dict[str, object], *, pi: bool
    ) -> tuple[subprocess.CompletedProcess[str] | None, _Record]: ...

    def drop(self, path: str) -> None: ...

    def worktree_writes(self, upper: list[list[str]]) -> list[str]: ...


_P = ParamSpec("_P")
_T = TypeVar("_T")


def _quiet(call: Callable[_P, _T], *args: _P.args, **kw: _P.kwargs) -> tuple[_T | None, str]:
    """(CALL(*ARGS, **KW), '') with what it streams to stderr dropped (the sandbox's proof and
    cleanup lines, each row's: its record keeps what a reason needs); (None, its last stderr line
    and exit) when it exits, as octo-feather-qc's die() does on a sandbox or snapshot it cannot
    have. Stated limit: one thread, as merge-ask is."""
    sink = io.TextIOWrapper(io.BytesIO(), encoding="utf-8", errors="replace", write_through=True)
    try:
        with contextlib.redirect_stderr(sink):
            return call(*args, **kw), ""
    except SystemExit as e:
        said = sink.buffer.getvalue().decode(errors="replace").strip()
        return None, f"{(said.splitlines() or [''])[-1][:TAIL]} (exit {e.code})"


def _qc() -> _Qc:
    """scripts/octo-feather-qc as a module: its sandbox and snapshot, not a second (as
    octo-feather-qa loads it)."""
    loader = importlib.machinery.SourceFileLoader(
        "octo_feather_qc", str(KIT / "scripts" / "octo-feather-qc")
    )
    spec = importlib.util.spec_from_loader("octo_feather_qc", loader)
    assert spec is not None, "a SourceFileLoader always yields a spec"
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return cast("_Qc", mod)  # a module from a path: typed by what a replay uses of it


def _program(command: str) -> str | None:
    """COMMAND's program, split as a shell would without one; None when it cannot be split."""
    try:
        argv = shlex.split(command)
    except ValueError:
        return None
    return argv[0] if argv else None


def _run(qc: _Qc, command: str, snap: dict[str, object], session: str) -> Replayed:
    """COMMAND run in its own qc sandbox (the demo command shape of octo-feather-qc capture(), at
    this worktree's top, under REPLAY_TIMEOUT) with the offline gh over SNAP; unserved: the proof
    failed or the sandbox is unavailable, or the run made an attempt the sandbox refused (an
    offline gh refusal, a masked path, a host), named."""
    root = git("rev-parse", "--show-toplevel", err=_Unread)[1].strip()
    cmd = [
        "timeout",
        "--foreground",
        "-k",
        "10",
        str(REPLAY_TIMEOUT),
        "env",
        f"QC_REPO={root}",
        "sh",
        "-c",
        'cd "$QC_REPO" || exit 127; exec sh -c "$1"',
        "qc-demo",
        command,
    ]
    got, said = _quiet(qc.sandboxed, cmd, session, snap, pi=False)
    if got is None:  # unshare missing (66) or macOS (69)
        return Replayed(None, "", f"{UNAVAILABLE}: {said}")
    run, rec = got
    if run is None:
        failed = [
            ln.split("FAIL", 1)[1].strip()[:TAIL] for ln in rec.get("proof", []) if "FAIL" in ln
        ]
        return Replayed(None, "", f"{UNAVAILABLE}: {'; '.join(failed) or 'its proof failed'}")
    refused = [a for a in rec.get("attempts", []) if a.get("refused")]
    why = "; ".join(f"{a.get('what')}: {a.get('result')}"[:TAIL] for a in refused[:2])
    if "attempts_error" in rec:
        why = f"no attempt record ({rec['attempts_error']})"
    if run.returncode in (124, 137):
        why = why or f"timed out after {REPLAY_TIMEOUT}s"
    wrote = tuple(qc.worktree_writes(rec.get("upper", [])))  # git's own and ignored ones aside
    return Replayed(run.returncode, run.stdout + run.stderr, why, wrote)


def _sample(s: Snapshot, cls: str, repo: str | None, lanes: Path) -> tuple[str, ...]:
    """The clean sample's lanes for the issue's class CLS (the rule: octo-feather-lane --help,
    merge-ask), REPO the PR's (None: this directory's gh repo), LANES the state dir's lanes/."""
    if repo is None:
        out = gh(["repo", "view", "--json", "nameWithOwner"], "check gh auth status", err=_Unread)
        repo = cast("_NamedRepo", _validated(out, NAMED_REPO, "gh repo view"))["nameWithOwner"]
    name = repo
    shas = [oid for oid, _ in s.commits] or [s.head]
    times = git("show", "-s", "--format=%ct", *shas, err=_Unread)[1].split()
    first = dt.datetime.fromtimestamp(min(int(t) for t in times), dt.timezone.utc)
    found: list[tuple[dt.datetime, str]] = []
    for lane, path, lines in lane_logs(lanes):
        if path.parent.name != "archive" or not lines:
            continue
        try:
            rec = lane_record(lanes, lane)
        except Refused as e:
            raise _Unread(str(e)) from e
        if not rec or str(rec[1].get("repository") or "").lower() != name.lower():
            continue
        last = utc(lines[-1].get("at"))
        if last is None or last >= first:
            continue
        if any(d.get("kind") == "finding" and d.get("class") == cls for d in lines):
            continue
        found.append((last, lane))
    return tuple(lane for _, lane in sorted(found, reverse=True)[:SAMPLE])
