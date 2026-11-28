#!/usr/bin/env python3
"""pr_git: a PR's git facts over its base, each read raising the ERR its caller passes, and the full
pass carried along them. Moved from scripts/merge_ask.py, which imports them, for the lane's
commands that use them (ticket #1335, evidence/gh1274-split/split.py helpers); standard library
only (AGENTS.md Rules, kit scripts)."""

__all__ = [  # what merge_ask.py and the lane's command groups import from here
    "QC_COMMIT",
    "Commit",
    "Gate",
    "Git",
    "Merge",
    "Unread",
    "_AbortError",
    "_RefusedError",
    "_Unread",
    "_gate_facts",
    "_git_facts",
    "full_pass",
    "full_pass_of",
    "git",
    "head_proof",
    "pr_base",
    "pr_commits",
    "resolution_files",
]

import dataclasses
import functools
import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from typing import cast

from lane_cli import Refuse
from tracker_calls import KIT


@dataclass(frozen=True)
class Unread:
    """A read that failed: WHY, its refusal as worded."""

    why: str


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


class _Unread(Exception):  # noqa: N818 (a read that failed, kept as Unread)
    """A read's refusal, kept as Unread."""


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


class _RefusedError(Exception):
    """The head proof refused (a commit not in the repo, a status file outside it): its message."""


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


QC_COMMIT = re.compile(r"^qc: built (.*?)(?: \(judged ([0-9a-f]+)\))?\s*$")


lane_git = functools.partial(git, err=Refuse)


def pr_commits(pr: int, head: str, base: str) -> list[tuple[str, str]]:
    """PR's commits, (sha, subject) each, newest first, read from this directory's repo: `git log BASE..HEAD`, HEAD the
    PR's head (gh's headRefOid), BASE its base branch on origin or --base; never `gh pr view --json commits`, which
    lists at most 100. Refused when either is not a commit here: the lane worktree with both fetched."""  # noqa: E501
    if lane_git("cat-file", "-e", f"{head}^{{commit}}", ok=(0, 1, 128))[0]:
        raise Refuse(  # noqa: TRY003
            f"PR #{pr}'s head {head[:12]} is not a commit in this repo: run it in the lane worktree after "  # noqa: E501, EM102
            "git fetch origin (the PR's commits are read from git)"
        )
    if lane_git("rev-parse", "--verify", "-q", f"{base}^{{commit}}", ok=(0, 1))[0]:
        raise Refuse(  # noqa: TRY003
            f"base {base} is not a commit here: git fetch origin, or pass --base REF (the PR's base branch)"  # noqa: E501, EM102
        )
    out = lane_git("log", "--format=%H%x00%s", f"{base}..{head}")[1]
    return [cast("tuple[str, str]", tuple(l.split("\0", 1))) for l in out.split("\n") if "\0" in l]  # noqa: E741
