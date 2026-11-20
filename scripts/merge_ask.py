#!/usr/bin/env python3
"""The merge ask's rules: a PR's facts read once into a Snapshot, judged by a pure check.

The design: issue #1146 (its design comment); the rules: issue-lifecycle spec #gates-pr-line,
#lanes-one-head (the checks), the merge ask (octo-feather-lane --help, merge-ask, its Checks
line). Imported by scripts/octo-feather-lane (`merge-ask` builds one snapshot and places each of
check's groups among its own gaps); how a command finds this module: the docstring of
scripts/correction_lanes.py. Standard library only (AGENTS.md Rules, kit scripts). The merge ask's
other rules are still in octo-feather-lane's cmd_merge_ask.

Interface:

    snapshot(pr, repo) -> Snapshot
        The one reader. PR: gh pr view's JSON (body, headRefName, headRefOid,
        statusCheckRollup, baseRefName) of a PR in REPO (None: this directory's). Adds what the
        tracker skill's key-from-branch BRANCH and pr-line KEY printed (ParentLine) or its
        refusal (NoParent), through the real tracker scripts of the target's tracker skill
        (tracker_calls); and the head's GitHub check facts (Checks), each read only when its rule
        needs it, a failed read kept as Unread.
    check(s) -> Ask
        Pure, no I/O: each refusal line the merge ask prints for S, in order, by rule; none when
        S passes.

Shared with octo-feather-lane's other commands: bad_checks (lane status), check_runs (the
carried checks) and ci_workflows (post-merge), each read raising the ERR its caller passes.
"""

__all__ = [  # check's interface, then the helpers octo-feather-lane's other commands share
    "Ask",
    "Checks",
    "NoParent",
    "NoWorkflow",
    "ParentLine",
    "Policy",
    "Reported",
    "Snapshot",
    "Unread",
    "Workflows",
    "bad_checks",
    "check",
    "check_runs",
    "ci_workflows",
    "snapshot",
]

import json
import re
import subprocess
from dataclasses import dataclass
from typing import cast

from tracker_calls import gh, tracker

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


# --- the parent line (spec #gates-pr-line) ---


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
    """A GitHub read that failed: WHY, its refusal as worded."""

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
class Snapshot:
    """A PR's facts, read once: its BODY, head BRANCH, the PARENT the tracker skill names, and its
    head's CHECKS."""

    body: str
    branch: str
    parent: ParentLine | NoParent
    checks: Checks


@dataclass(frozen=True)
class Ask:
    """The merge ask's verdict on a Snapshot, by rule, each list in the order merge-ask prints it:
    GAPS the parent line's refusal lines; CHECKS the Checks rules'; NO_CI the no-CI fact's line on
    a pass, else ''; CURRENT the head's checks after the current-head projection (the rollup when
    it could not be made), which merge-ask's carried checks read. No gap: S passes."""

    gaps: list[str]
    checks: list[str]
    no_ci: str
    current: list[dict[str, object]]


class _Unread(Exception):  # noqa: N818 (a read that failed, kept as Unread)
    """A read's refusal, kept as Unread or NoParent."""


class _Gap(Exception):  # noqa: N818 (a rule's refusal line, as merge-ask prints it)
    """A Checks rule's refusal line, raised where the moved code refused."""


def snapshot(pr: dict[str, object], repo: str | None) -> Snapshot:
    body, branch = str(pr["body"] or ""), str(pr["headRefName"] or "")
    head = str(pr["headRefOid"])
    rollup = cast("list[dict[str, object]]", pr["statusCheckRollup"] or [])
    try:
        key = tracker("key-from-branch", branch, err=_Unread).strip()
        line = tracker("pr-line", key, err=_Unread).strip()
    except _Unread as e:
        parent: ParentLine | NoParent = NoParent(str(e))
    else:
        parent = ParentLine(key, line)
    at = (
        _reported(head, rollup, repo) if rollup else _unreported(head, str(pr["baseRefName"]), repo)
    )
    return Snapshot(body, branch, parent, Checks(head, repo, at))


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


def ci_workflows(repo: str | None, sha: str, *, err: type[Exception]) -> tuple[list[str], str]:
    """The no-CI fact (rule: octo-feather-lane --help, post-merge step 2): the workflow files at
    commit SHA and the source as printed; a failed read raises ERR."""
    name = repo or "{owner}/{repo}"  # gh fills the placeholders from this directory's repo
    src = f"gh api repos/{repo or '<this repo>'}/git/trees/{sha[:12]}"
    tree = sha
    for part in (".github", "workflows", None):
        out = gh(
            ["api", f"repos/{name}/git/trees/{tree}"],
            f"check gh auth status and that {sha[:12]} is in {repo or 'this repo'}, then rerun",
            err=err,
        )
        try:
            entries = [
                (str(e["path"]), str(e["type"]), str(e["sha"])) for e in json.loads(out)["tree"]
            ]
        except (ValueError, KeyError, TypeError) as e:
            msg = (
                f"gh api git/trees/{tree[:12]} printed no tree ({out[:100]!r}): "
                "check the gh on PATH"
            )
            raise err(msg) from e
        if part is None:
            files = [p for p, t, _ in entries if t == "blob" and p.endswith((".yml", ".yaml"))]
            return [f".github/workflows/{p}" for p in files], src
        tree = next((s for p, t, s in entries if p == part and t == "tree"), "")
        if not tree:
            return [], src
    return [], src  # unreachable: the loop returns at its last part


def check(s: Snapshot) -> Ask:
    checks, no_ci, current = head_checks(s.checks)
    return Ask(parent_line(s), checks, no_ci, current)


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
