#!/usr/bin/env python3
"""The kit's gh and tracker-skill calls, shared by octo-feather-lane and correction_lanes.

`gh` and `tracker` run the real tool (gh on PATH; a tracker skill's scripts in the kit's
.agents/skills), `tracker_skill` names the target's tracker skill, `utc` reads gh's and the
records' times. The reads over them: `pr_view` (a PR's fields), `ci_workflows` (a commit's
workflow files), `issue_view` (a ticket), with `head_matches` (a named head against a PR's,
`SHA` the form of a named commit) and `key_order` (tracker keys in order). Each call raises
the error class its caller passes (ERR), so each command keeps its own refusals. Standard
library only; how a command finds this module: the docstring of scripts/correction_lanes.py.
"""

import datetime as dt
import importlib.machinery
import importlib.util
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any, cast

KIT = Path(__file__).resolve().parent.parent
SHA = re.compile(r"[0-9a-fA-F]{7,40}")  # a commit as named: 7 to 40 hex


def gh(args: list[str], fix: str, *, err: type[Exception]) -> str:
    """gh ARGS' stdout; ERR naming FIX when it fails."""
    try:
        p = subprocess.run(
            ["gh", *args],  # noqa: S607 (gh from PATH, as the command runs it)
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,
            check=False,
        )
    except FileNotFoundError as e:
        msg = "gh not on PATH: install the GitHub CLI and log in (just install-check)"
        raise err(msg) from e
    if p.returncode:
        said = (p.stderr or p.stdout).strip().splitlines()
        why = said[-1][:300] if said else f"exit {p.returncode}"
        msg = f"gh {' '.join(args[:3])} failed ({why}): {fix}"
        raise err(msg)
    return p.stdout


def tracker_skill(err: type[Exception]) -> str:
    """The target's tracker skill: scripts/pi-role's tracker_skill resolves it from the
    .octo-feather.toml of the git repo at the current directory, docs/adr/0004."""
    loader = importlib.machinery.SourceFileLoader("pi_role", str(KIT / "scripts" / "pi-role"))
    spec = importlib.util.spec_from_loader("pi_role", loader)
    assert spec is not None, "a SourceFileLoader always yields a spec"
    pr = importlib.util.module_from_spec(spec)
    loader.exec_module(pr)
    try:
        return str(pr.tracker_skill(str(KIT / ".agents" / "skills")))
    except SystemExit as e:
        msg = (
            f"{e.code}: set `tracker` in the target's .octo-feather.toml to a tracker the kit has,"
            " then rerun"
        )
        raise err(msg) from e


def tracker(
    script: str,
    *args: str,
    err: type[Exception],
    skill: str | None = None,
    env: dict[str, str] | None = None,
    stdin: str | None = None,
) -> str:
    """Run SCRIPT of SKILL, by default the target's tracker skill (tracker_skill); its stdout. ENV
    is added to the script's environment, STDIN its input. A failure raises ERR naming the script
    and its reason."""
    skill = skill or tracker_skill(err)
    path = KIT / ".agents" / "skills" / skill / "scripts" / script
    try:
        p = subprocess.run(
            [str(path), *args],
            capture_output=True,
            text=True,
            timeout=120,
            env={**os.environ, **(env or {})},
            input=stdin,
            stdin=subprocess.DEVNULL if stdin is None else None,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        msg = (
            f"tracker script {skill}/{script} {' '.join(args)} did not run ({e}): check the"
            " tracker CLI and network, then rerun"
        )
        raise err(msg) from e
    if p.returncode:
        why = " ".join((p.stderr or p.stdout).split())[:400] or f"exit {p.returncode}"
        msg = (
            f"tracker script {skill}/{script} {' '.join(args)} failed ({why}): fix the cause it"
            " names, then rerun"
        )
        raise err(msg)
    return p.stdout


# gh's and the tracker's JSON is typed Any: each caller narrows the fields it reads.
def pr_view(pr: int, fields: str, repo: str | None, *, err: type[Exception]) -> dict[str, Any]:
    """`gh pr view PR --json FIELDS` (in REPO, else this directory's repo): the object, every
    field present; ERR otherwise."""
    out = gh(
        ["pr", "view", str(pr), "--json", fields, *(["-R", repo] if repo else [])],
        f"check PR #{pr} exists in {repo or 'this repo'}, and gh auth status",
        err=err,
    )
    try:
        d: object = json.loads(out)
    except ValueError as e:
        msg = f"gh pr view {pr} printed no JSON: check the gh on PATH ({out[:100]!r})"
        raise err(msg) from e
    if not isinstance(d, dict) or any(f not in d for f in fields.split(",")):
        msg = f"gh pr view {pr} lacks fields {fields}: update gh (2.40 or later)"
        raise err(msg)
    return cast("dict[str, Any]", d)


def ci_workflows(repo: str | None, sha: str, *, err: type[Exception]) -> tuple[list[str], str]:
    """The no-CI fact (rule: octo-feather-lane --help, post-merge step 2): the workflow files at
    commit SHA and the source as printed."""
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
            raw = cast("list[dict[str, object]]", json.loads(out)["tree"])
            entries = [(str(e["path"]), str(e["type"]), str(e["sha"])) for e in raw]
        except (ValueError, KeyError, TypeError) as e:
            msg = (
                f"gh api git/trees/{tree[:12]} printed no tree ({out[:100]!r}): check the gh on"
                " PATH"
            )
            raise err(msg) from e
        if part is None:
            wf = [p for p, t, _ in entries if t == "blob" and p.endswith((".yml", ".yaml"))]
            return [f".github/workflows/{p}" for p in wf], src
        tree = next((s for p, t, s in entries if p == part and t == "tree"), "")
        if not tree:
            return [], src
    return [], src  # unreachable: the loop returns at its last part


def head_matches(named: str, head: str) -> bool:
    """Whether NAMED, a sha (SHA), is a prefix of HEAD."""
    return bool(SHA.fullmatch(named)) and head.lower().startswith(named.lower())


def issue_view(key: str, *, err: type[Exception]) -> dict[str, Any]:
    """The tracker skill's issue-view of KEY: {key, ..., state, children}, children a list of key
    strings."""
    out = tracker("issue-view", key, err=err)
    try:
        d: object = json.loads(out)
        if (
            not isinstance(d, dict)
            or not isinstance(cast("dict[str, object]", d).get("key"), str)
            or not isinstance(kids := cast("dict[str, object]", d).get("children"), list)
            or not all(isinstance(k, str) for k in cast("list[object]", kids))
        ):
            msg = "no key or children list of key strings"
            raise ValueError(msg)  # noqa: TRY301 (one message for both failures, as JSON's own)
    except ValueError as e:
        msg = (
            f"issue-view {key} printed unreadable JSON ({e}): the tracker skill's issue-view must"
            " print key and children, then rerun"
        )
        raise err(msg) from e
    return cast("dict[str, Any]", d)


def key_order(k: str) -> tuple[str, int]:
    """Keys in tracker order: the prefix, then the trailing number (101 before 110, ENG-9 before
    ENG-10)."""
    m = re.fullmatch(r"(.*?)(\d+)", k)
    return (m.group(1), int(m.group(2))) if m else (k, 0)


def utc(s: object) -> dt.datetime | None:
    """S as a UTC instant: an ISO 8601 date and time with Z or an offset, fractional seconds
    allowed (2026-10-29T14:06:08Z, 2026-10-29T14:06:08.770516+00:00); None for anything else, a
    time with no zone included."""
    if not isinstance(s, str) or "T" not in s:
        return None
    try:
        t = dt.datetime.fromisoformat(s[:-1] + "+00:00" if s.endswith("Z") else s)
    except ValueError:
        return None
    return None if t.tzinfo is None else t.astimezone(dt.timezone.utc)
