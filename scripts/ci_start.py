#!/usr/bin/env python3
"""ci_start: octo-feather-lane's ci-start. Moved from scripts/octo-feather-lane, the dispatcher (ticket #1333)."""

import functools
import json
import re
import subprocess
import time
from typing import TYPE_CHECKING, Any, cast

import lane_cli
import merge_ask
from lane_cli import KIT, Refuse, gh, pr_number, pr_view, take_repo

if TYPE_CHECKING:
    from collections.abc import Callable


no_traceback = cast("Callable[[Any], Callable[[list[str]], int]]", lane_cli.no_traceback)


git = functools.partial(merge_ask.git, err=Refuse)   # the lane's git calls raise its own Refuse (merge_ask.git)
full_pass = functools.partial(merge_ask.full_pass, err=Refuse)   # ci-start's full pass (merge_ask, Interface)
pr_base = merge_ask.pr_base   # the base a PR's commits are read against (its docstring)


@no_traceback
def cmd_ci_start(args: list[str]) -> int:
    """CI on the lane's final head (when: spec issue-lifecycle #lanes-one-head): refuse unless the local HEAD is the PR's head and has a current full
    gate pass, mark a draft PR ready (gh pr ready), then wait at most --wait seconds for CI's full run on that head to
    start (ci_full_run), and print its jobs."""
    args, repo = take_repo(args)
    files: list[str] = []; rest: list[str] = []; i, base_arg, wait = 0, cast("str | None", None), 120.0
    while i < len(args):
        if args[i] in ("--status", "--base", "--wait") and i + 1 < len(args):
            if args[i] == "--status":
                files.append(args[i + 1])
            elif args[i] == "--base":
                base_arg = args[i + 1]
            elif re.fullmatch(r"[0-9]+", args[i + 1]):
                wait = float(args[i + 1])
            else:
                raise Refuse(f"--wait needs whole seconds, got {args[i + 1]!r}")
            i += 2
        else:
            rest.append(args[i]); i += 1
    if len(rest) != 1:
        raise Refuse(f"usage: octo-feather-lane ci-start PR [--status FILE...] [--base REF] [--wait SECONDS] [--repo O/R] (got {' '.join(args) or 'nothing'})")
    pr = pr_number(rest[0])
    d = cast("dict[str, object]", pr_view(pr, "isDraft,headRefOid,baseRefName,headRefName", repo))
    head = str(d["headRefOid"]).lower(); h = head[:12]
    local = git("rev-parse", "HEAD")[1].strip().lower()
    if local != head:
        raise Refuse(f"local HEAD {local[:12]} is not PR #{pr}'s head {h}: push it (git push), then rerun in the lane worktree")
    why = full_pass(head, files, pr_base(cast("str | None", d["baseRefName"]) or "", base_arg))
    if why:
        raise Refuse("; ".join(why))
    if d["isDraft"]:
        gh(["pr", "ready", str(pr), *(["-R", repo] if repo else [])], f"mark PR #{pr} ready for review by hand (gh pr ready {pr})")
        print(f"PR #{pr} marked ready for review at head {h}")
    end = time.monotonic() + wait
    while True:
        why, jobs = ci_full_run(head, repo)
        if not why:
            print(f"CI on {h} (issue-lifecycle #lanes-one-head):")
            print("\n".join(jobs))
            return 0
        left = end - time.monotonic()
        if left <= 0:
            raise Refuse(f"CI's full run did not start on {h} within {wait:g}s: {'; '.join(why)}: check PR #{pr} is ready "
                         "for review and its workflow runs on pull_request ready_for_review, then rerun")
        time.sleep(min(5.0, left))


def workflow_jobs(head: str, path: str) -> int | None:
    """How many jobs the workflow file PATH defines at HEAD (its `jobs` map), read with PyYAML in the kit's locked
    environment (the standard library reads no YAML); None when it is unreadable."""
    rc, text = git("show", f"{head}:{path}", ok=(0, 128))
    if rc:
        return None
    try:
        count = ("import sys, yaml; w = yaml.safe_load(sys.stdin); j = w.get('jobs') if isinstance(w, dict) else None; "
                 "print(len(j) if isinstance(j, dict) else '')")
        p = subprocess.run(["uv", "run", "--project", str(KIT), "--locked", "--offline", "--no-dev", "--quiet", "python", "-c", count],
                           input=text, capture_output=True, text=True, check=False)
    except FileNotFoundError:
        raise Refuse("uv not on PATH: it runs the kit's locked environment that reads the workflow (just install-check)")
    out = p.stdout.strip()
    return int(out) if p.returncode == 0 and out.isdigit() else None


def ci_full_run(head: str, repo: str | None) -> tuple[list[str], list[str]]:
    """([], a line per job) once CI's full run on HEAD has started, else (why not, []); the rule: issue-lifecycle
    #acceptance-ci-alongside. Read for each workflow's latest run on HEAD: its jobs (REST), and the count of jobs its
    workflow file defines at HEAD, since GitHub lists a job that waits on `needs` only once those finish (run
    42118019970: check created when scope completed)."""
    api = f"repos/{repo or '{owner}/{repo}'}/actions"
    def read(path: str, key: str) -> "list[dict[str, object]]":
        out = gh(["api", f"{api}/{path}"], f"read {path} for {head[:12]} (gh auth status)")
        try:
            got = cast("list[object]", json.loads(out)[key])
        except (ValueError, KeyError, TypeError):
            raise Refuse(f"gh api {path} printed no {key}: check the gh on PATH ({out[:100]!r})")
        return [cast("dict[str, object]", r) for r in got if isinstance(r, dict)]
    latest: dict[str, dict[str, object]] = {}
    for r in read(f"runs?head_sha={head}&per_page=100", "workflow_runs"):
        w = str(r.get("workflow_id"))
        if w not in latest or int(str(r.get("id") or 0)) > int(str(latest[w].get("id") or 0)):
            latest[w] = r
    if not latest:
        return ["no workflow run on it yet"], []
    why: list[str] = []; lines: list[str] = []
    for r in latest.values():
        path = str(r.get("path") or "")
        jobs = read(f"runs/{r.get('id')}/jobs?per_page=100", "jobs")
        state = {str(j.get("name")): (str(j.get("status") or "").lower(), str(j.get("conclusion") or "").lower()) for j in jobs}
        # The run's own job list is the fact; the workflow file's job count is only the guard against GitHub creating a
        # needs-dependent job late (run 42118019970 listed check only after scope completed). Started, none skipped, not
        # completed: waiting for completion would put CI before qc and review again (issue-lifecycle #lanes-one-head).
        n = workflow_jobs(head, path)
        if n is None:
            why.append(f"{path or 'its workflow'} at {head[:12]} is unreadable: no job count to compare")
        elif len(jobs) < n:
            why.append(f"run {r.get('id')} lists {len(jobs)} of the {n} jobs {path} defines (a job waiting on `needs` is not created yet)")
        why += [f"run {r.get('id')} job {k} {c or s}" for k, (s, c) in state.items()
                if c == "skipped" or s not in ("queued", "in_progress", "completed")]
        lines += [f"- {j.get('name')} {j.get('conclusion') or j.get('status')} on {head[:12]}: {j.get('html_url')}" for j in jobs]
    return why, ([] if why else lines)


# This module's chunks of octo-feather-lane --help, joined in lane_cli.HELP_ORDER by lane_cli.help_doc.
HELP = {
    "ci-start-usage": """\
  octo-feather-lane ci-start PR [--status FILE...] [--base REF] [--wait SECONDS] [--repo O/R]
                                   CI on the lane's final head (when: issue-lifecycle #lanes-one-head): refuse unless
                                   the local HEAD is the PR head with a current full gate pass, mark the PR
                                   ready (gh pr ready), wait (default 120s) until CI's full run on it has
                                   started (when that is: #acceptance-ci-alongside) and print its jobs
""",
}
