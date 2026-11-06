"""The scenarios of tests/gate/kit/test_lane_ci_start.py (its items), this file their command
(testkit.main): scripts/octo-feather-lane ci-start (issue-lifecycle#acceptance-ci-alongside; the
rule: issue-lifecycle #lanes-one-head), no network: the testkit's fake gh holds draft PR #7 of o/r
and, as tapes, GitHub's workflow runs and jobs on its head (REST; a run's jobs move on between
reads). ci-start refuses an unpushed head and a head with no recorded full gate pass before
marking the PR ready; else marks it ready and succeeds only once CI's full run has started, as
the head's workflow file and the run's jobs show. The lane worktree (origin/main B, the final
head H, its workflow: a scope job, then check needing it) is prepared once per gate run."""

from __future__ import annotations

import json

from testkit import Ran, Scratch, kit, main

API = "api repos/{owner}/{repo}/actions/"
WORKFLOW = (
    "on: pull_request\njobs:\n  scope:\n    runs-on: x\n"
    "  check:\n    needs: scope\n    runs-on: x\n"
)


def build(p: Scratch) -> None:
    r = p.root / "repo"
    (r / ".github" / "workflows").mkdir(parents=True)
    p.git(r, "init", "-q", "-b", "main")
    (r / ".github" / "workflows" / "ci.yml").write_text(WORKFLOW)
    (r / "app.py").write_text("one\n")
    p.git(r, "add", "-A")
    p.git(r, "commit", "-qm", "base")
    p.git(r, "update-ref", "refs/remotes/origin/main", "HEAD")
    p.git(r, "checkout", "-q", "-b", "gh6")
    (r / "app.py").write_text("one\ntwo\n")
    p.git(r, "commit", "-qam", "feat: x")


class Lane:
    def __init__(self, s: Scratch) -> None:
        s.prepare("lane-ci-start", build)
        s.env.pop("HERDR_SESSION", None)
        s.env["XDG_STATE_HOME"] = str(s.root / "xdg")
        self.s, self.repo = s, s.root / "repo"
        self.h = s.git(self.repo, "rev-parse", "HEAD")
        self.h12 = self.h[:12]

    def pr(
        self, head: str, *, draft: bool, runs: bool = True, jobs: list[str] | None = None
    ) -> None:
        """PR #7 at HEAD (a DRAFT); with RUNS, the head's latest run 2 of the workflow beside an
        earlier run 1 the draft skipped, run 2's JOBS (each read's answer, the last repeated)."""
        self.s.gh.put(
            7,
            {
                "number": 7,
                "isDraft": draft,
                "headRefOid": head,
                "baseRefName": "main",
                "headRefName": "gh6",
            },
        )
        wf = ".github/workflows/ci.yml"
        listed = {
            "total_count": 2,
            "workflow_runs": [{"id": n, "workflow_id": 5, "path": wf} for n in (2, 1)],
        }
        skipped = [
            {"name": n, "status": "completed", "conclusion": "skipped", "html_url": "u1"}
            for n in ("scope", "check")
        ]
        empty = {"total_count": 0, "workflow_runs": []}
        self.s.gh.tape(
            {
                f"{API}runs?head_sha={head}&per_page=100": [
                    json.dumps(listed if runs else empty) + "\n"
                ],
                f"{API}runs/1/jobs?per_page=100": [
                    json.dumps({"total_count": 2, "jobs": skipped}) + "\n"
                ],
                f"{API}runs/2/jobs?per_page=100": jobs or [jobs_of("in_progress", "")],
            }
        )

    def ci_start(self, want: int, *args: str) -> Ran:
        return self.s.run(
            [kit("octo-feather-lane"), "ci-start", "7", *args], want=want, cwd=self.repo
        )

    def unready(self, what: str) -> None:
        log = self.s.gh.log()
        assert not [x for x in log if x.startswith("pr ready")], (
            f"{what} marked the PR ready: {log}"
        )


def jobs_of(scope: str, sc: str, check: str = "", cc: str = "") -> str:
    """Run 2's jobs as GitHub lists them: scope at SCOPE/SC, check at CHECK/CC (absent: none)."""
    j = [
        {
            "name": "scope",
            "status": scope,
            "conclusion": sc or None,
            "html_url": "https://github.com/o/r/actions/runs/2/job/1",
        }
    ]
    if check:
        j.append(
            {
                "name": "check",
                "status": check,
                "conclusion": cc or None,
                "html_url": "https://github.com/o/r/actions/runs/2/job/2",
            }
        )
    return json.dumps({"total_count": len(j), "jobs": j}) + "\n"


def refusals(s: Scratch) -> None:
    """The local head not the PR's head (not pushed): refused, the PR left a draft. No recorded
    full gate pass on the head: refused, the PR left a draft."""
    lane = Lane(s)
    b = s.git(lane.repo, "rev-parse", "HEAD~1")
    lane.pr(b, draft=True)
    r = lane.ci_start(1)
    assert f"local HEAD {lane.h12} is not PR #7's head {b[:12]}: push it" in r.err, (
        f"unpushed head: {r.err}"
    )
    lane.unready("an unpushed head")
    lane.pr(lane.h, draft=True)
    r = lane.ci_start(1)
    assert f"head {lane.h12} has no current recorded full gate pass" in r.err, (
        f"no full pass: {r.err}"
    )
    lane.unready("a head with no full pass")


def started(s: Scratch) -> None:
    """issue-lifecycle#acceptance-ci-alongside, the demo: the final head (its full pass recorded),
    a draft: marked ready; its run's scope job runs and check is not created yet (GitHub creates a
    job waiting on needs once they finish): ci-start keeps waiting; then check is queued: started,
    the jobs printed. Already ready (a fix round): no ready call; scope done, check running:
    started."""
    lane = Lane(s)
    s.run(
        [kit("octo-feather-gate"), "record", "--reason", "lane final head", "--seconds", "1"],
        cwd=lane.repo,
    )
    lane.pr(
        lane.h,
        draft=True,
        jobs=[jobs_of("in_progress", ""), jobs_of("completed", "success", "queued")],
    )
    r = lane.ci_start(0, "--wait", "30")
    log = s.gh.log()
    assert "pr ready 7" in log, f"not marked ready: {log}"
    assert sum("actions/runs/2/jobs" in x for x in log) == 2, (
        f"did not wait past scope running: {log}"
    )
    want = (
        f"- scope success on {lane.h12}: https://github.com/o/r/actions/runs/2/job/1\n"
        f"- check queued on {lane.h12}: https://github.com/o/r/actions/runs/2/job/2"
    )
    assert r.out.endswith(want), f"the started run not printed: {r.out}"
    lane.pr(lane.h, draft=False, jobs=[jobs_of("completed", "success", "in_progress")])
    r = lane.ci_start(0)
    lane.unready("a ready PR")
    want = f"- check in_progress on {lane.h12}: https://github.com/o/r/actions/runs/2/job/2"
    assert want in r.out.split("\n"), f"ready PR: {r.out}"


def not_started(s: Scratch) -> None:
    """Not started within --wait, each refused naming why: scope running with check not created,
    or with check pending; check skipped (a status-only head); no run at all."""
    lane = Lane(s)
    s.run(
        [kit("octo-feather-gate"), "record", "--reason", "lane final head", "--seconds", "1"],
        cwd=lane.repo,
    )
    within = f"CI's full run did not start on {lane.h12} within 1s: "
    for jobs, why in (
        (
            jobs_of("in_progress", ""),
            "run 2 lists 1 of the 2 jobs .github/workflows/ci.yml defines",
        ),
        (jobs_of("in_progress", "", "pending"), "run 2 job check pending"),
        (jobs_of("completed", "success", "completed", "skipped"), "run 2 job check skipped"),
    ):
        lane.pr(lane.h, draft=False, jobs=[jobs])
        r = lane.ci_start(1, "--wait", "1")
        assert within + why in r.err, f"{why}: {r.err}"
    lane.pr(lane.h, draft=True, runs=False)
    r = lane.ci_start(1, "--wait", "1")
    assert "within 1s: no workflow run on it yet" in r.err, f"no run: {r.err}"


if __name__ == "__main__":
    main(refusals, started, not_started)
