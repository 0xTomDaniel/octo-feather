"""The scenarios of tests/gate/kit/test_lane_ci_start.py (its items), this file their command
(testkit.main): scripts/octo-feather-lane ci-start (issue-lifecycle#acceptance-ci-alongside; the
rule: issue-lifecycle #lanes-one-head), offline: the testkit's gh answers only real gh's recorded
answers (testkit/recordings/lane-ci-start.json, one tape per scenario), the PR and GitHub's
workflow runs and jobs on its head (REST). ci-start refuses an unpushed head and a head with no
recorded full gate pass before marking the PR ready; else marks it ready and succeeds only once
CI's full run has started, as the head's workflow file and the run's jobs show.

The lane repo rebuilds, byte for byte, the commits the recording pushed (fixed identity and
dates, GIT_ENV): ROOT, the scratch base branch, holding only the workflow (WORKFLOW: check.yml's
shape, a scope job, then check needing it, made trivial); B, the old test's base commit; the
final head H; U, an unpushed commit on H; S, a status-only head on ROOT; K, a head on H whose
message skips CI. Prepared once per gate run; a scenario records the full gate passes it needs.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, cast

from testkit import Ran, Scratch, kit, main

if TYPE_CHECKING:
    from collections.abc import Mapping

# gh 2.102.0 on 0xTomDaniel/octo-feather, 2026-11-17 (each recording's source): one real
# session on scratch draft PR 946 (PR), base branch BASE (ROOT), head branch gh930-recording, with
# the real `octo-feather-lane ci-start` at each moment a scenario names; then closed, both
# branches deleted.
TAPE = Path(__file__).parent / "testkit" / "recordings" / "lane-ci-start.json"
PR = 946
BASE = "gh930-recording-base"
DATE = "2026-11-17T00:00:00Z"
GIT_ENV = {
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@example.com",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@example.com",
    "GIT_AUTHOR_DATE": DATE,
    "GIT_COMMITTER_DATE": DATE,
}
WF = ".github/workflows/ci.yml"
WORKFLOW = """\
# The gh930 recording's CI (tests/gate/kit/lane_ci_start.py): check.yml's shape, made trivial.
on:
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review]
jobs:
  scope:
    if: github.event.pull_request.draft == false
    runs-on: ubuntu-24.04
    outputs:
      code: ${{ steps.diff.outputs.code }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - id: diff
        run: |
          sleep 15
          base=${{ github.event.pull_request.base.sha }} head=${{ github.event.pull_request.head.sha }}
          if git diff --name-only "$base" "$head" | grep -qv '^docs/specs/.*[.]status[.]json$'
          then echo code=true >> "$GITHUB_OUTPUT"; else echo code=false >> "$GITHUB_OUTPUT"; fi
  check:
    needs: scope
    if: needs.scope.outputs.code != 'false'
    concurrency: gh930-recording-check
    runs-on: ubuntu-24.04
    steps:
      - run: if [ "${{ github.event.action }}" != synchronize ]; then sleep 90; fi
"""  # noqa: E501 (the recorded workflow, byte for byte: ROOT's sha)


def commit(s: Scratch, repo: Path, msg: str, files: Mapping[str, str]) -> str:
    """FILES written in REPO and committed as MSG with the recording's identity and date."""
    for name, text in files.items():
        (repo / name).parent.mkdir(parents=True, exist_ok=True)
        (repo / name).write_text(text)
    s.git(repo, "add", "-A")
    s.run(["git", "-C", str(repo), "commit", "-q", "-m", msg], env=GIT_ENV)
    return s.git(repo, "rev-parse", "HEAD")


def root(s: Scratch, repo: Path) -> str:
    """REPO, a new git repo, at ROOT (the scratch base branch: the workflow alone)."""
    s.git(repo.parent, "init", "-q", "-b", "main", repo.name)
    # the repo's own identity too: octo-feather-gate record writes a git note (a commit)
    for k, v in (("user.email", "t@example.com"), ("user.name", "t"), ("commit.gpgsign", "false")):
        s.git(repo, "config", k, v)
    return commit(s, repo, "ci: the recording's workflow", {WF: WORKFLOW})


def build(p: Scratch) -> None:
    r = p.root / "repo"
    h = {"root": root(p, r)}
    h["b"] = commit(p, r, "base", {"app.py": "one\n"})
    h["h"] = commit(p, r, "feat: x", {"app.py": "one\ntwo\n"})
    h["u"] = commit(p, r, "feat: y", {"app.py": "one\ntwo\nthree\n"})
    p.git(r, "checkout", "-q", "--detach", h["h"])
    h["k"] = commit(p, r, "chore: z [skip ci]", {"app.py": "one\ntwo\nz\n"})
    p.git(r, "checkout", "-q", "--detach", h["root"])
    status = '{"spec": "demo.spec.html", "criteria": {}}\n'
    h["s"] = commit(p, r, "qc: status only", {"docs/specs/demo.status.json": status})
    p.git(r, "update-ref", f"refs/remotes/origin/{BASE}", h["root"])
    (p.root / "heads.json").write_text(json.dumps(h))


class Lane:
    """The prepared lane repo in S, its heads, and S's gh on this scenario's tape."""

    def __init__(self, s: Scratch, scenario: str) -> None:
        s.prepare("lane-ci-start", build)
        s.env.pop("HERDR_SESSION", None)
        s.env["XDG_STATE_HOME"] = str(s.root / "xdg")
        self.s, self.repo = s, s.root / "repo"
        self.h: dict[str, str] = json.loads((s.root / "heads.json").read_text())
        self.tape = cast("list[dict[str, object]]", json.loads(TAPE.read_text())[scenario])
        self.since = 0
        s.gh.store("tape.json", self.tape)

    def at(self, head: str, *, record: bool = False) -> None:
        """The lane worktree at HEAD (its full gate pass recorded, with RECORD)."""
        self.s.git(self.repo, "checkout", "-q", "--detach", self.h[head])
        if record:
            gate = [kit("octo-feather-gate"), "record", "--reason", "lane final head"]
            self.s.run([*gate, "--seconds", "1"], cwd=self.repo)

    def github(self, head: str, *, draft: bool, ci: str) -> None:
        """The recorded moment the next ci-start reads: PR at HEAD, a DRAFT or not, its CI as
        CI says. Its next `pr view` answer on the tape holds that head and draft state."""
        views = [r for r in self.tape if str(r["request"]).startswith(f"pr view {PR} ")]
        seen = sum(x.startswith(f"pr view {PR} ") for x in self.s.gh.log())
        assert len(views) > seen, f"no recorded PR view for the moment: {ci}"
        d = json.loads(str(views[seen]["out"]))
        got = (d["headRefOid"], d["isDraft"])
        assert got == (self.h[head], draft), f"the tape's PR at {ci}: {got}"
        self.since = len(self.s.gh.log())

    def ci_start(self, want: int, *args: str) -> Ran:
        return self.s.run(
            [kit("octo-feather-lane"), "ci-start", str(PR), *args], want=want, cwd=self.repo
        )

    def unready(self, what: str) -> None:
        """No `pr ready` since the moment last named."""
        log = self.s.gh.log()[self.since :]
        assert not [x for x in log if x.startswith("pr ready")], (
            f"{what} marked the PR ready: {log}"
        )


def refusals(s: Scratch) -> None:
    """The local head not the PR's head (not pushed: the local HEAD U one commit past the PR's H):
    refused, the PR left a draft. No recorded full gate pass on the head: refused, the PR left a
    draft."""
    lane = Lane(s, "refusals")
    h12, u12 = lane.h["h"][:12], lane.h["u"][:12]
    lane.at("u")
    lane.github("h", draft=True, ci="opened as a draft: run 1, its jobs skipped")
    r = lane.ci_start(1)
    assert f"local HEAD {u12} is not PR #{PR}'s head {h12}: push it" in r.err, (
        f"unpushed head: {r.err}"
    )
    lane.unready("an unpushed head")
    lane.at("h")
    lane.github("h", draft=True, ci="opened as a draft: run 1, its jobs skipped")
    r = lane.ci_start(1)
    assert f"head {h12} has no current recorded full gate pass" in r.err, f"no full pass: {r.err}"
    lane.unready("a head with no full pass")


def started(s: Scratch) -> None:
    """issue-lifecycle#acceptance-ci-alongside, the demo: the final head H (its full pass
    recorded), a draft: marked ready; its run's scope job runs and check is not created yet
    (GitHub creates a job waiting on needs once they finish): ci-start keeps waiting; then check
    is running: started, the jobs printed. Already ready (a fix round): no ready call; scope done,
    check running: started."""
    lane = Lane(s, "started")
    h12 = lane.h["h"][:12]
    lane.at("h", record=True)
    lane.github("h", draft=True, ci="opened as a draft: run 1, its jobs skipped")
    r = lane.ci_start(0, "--wait", "30")
    log = s.gh.log()
    assert f"pr ready {PR}" in log, f"not marked ready: {log}"
    assert sum(f"actions/runs/{RUN2}/jobs" in x for x in log) == POLLS, (
        f"did not wait past scope running: {log}"
    )
    want = f"- scope success on {h12}: {JOBS[0]}\n- check in_progress on {h12}: {JOBS[1]}"
    assert r.out.endswith(want), f"the started run not printed: {r.out}"
    lane.github("h", draft=False, ci="ready: run 2's scope done, its check running")
    r = lane.ci_start(0)
    lane.unready("a ready PR")
    want = f"- check in_progress on {h12}: {JOBS[1]}"
    assert want in r.out.split("\n"), f"ready PR: {r.out}"


def not_started(s: Scratch) -> None:
    """Not started within --wait, each refused naming why: scope running with check not created,
    or (scope done) check pending, behind run 2's check in its concurrency group; check skipped
    (the status-only head S); no run at all (K, its message skipping CI, a draft). --wait 0 where
    the recording's one poll outlasted its 1s: the replay answers at once, so 1s would poll
    twice; K's two polls, --wait 1, as recorded."""
    lane = Lane(s, "not_started")
    within = f"CI's full run did not start on {lane.h['h'][:12]} within 0s: "
    lane.at("h", record=True)
    lane.github("h", draft=False, ci="reopened: run 3's scope running, its check not created")
    r = lane.ci_start(1, "--wait", "0")
    why = f"run {RUN3} lists 1 of the 2 jobs {WF} defines"
    assert within + why in r.err, f"scope running, check absent: {r.err}"
    lane.github("h", draft=False, ci="run 3's scope done, its check pending")
    r = lane.ci_start(1, "--wait", "0")
    assert f"within 0s: run {RUN3} job check pending" in r.err, f"check pending: {r.err}"
    lane.at("s", record=True)
    lane.github("s", draft=False, ci="S pushed: run 4's check skipped")
    r = lane.ci_start(1, "--wait", "0")
    assert f"within 0s: run {RUN4} job check skipped" in r.err, f"check skipped: {r.err}"
    lane.at("k", record=True)
    lane.github("k", draft=True, ci="a draft again, K pushed: no run")
    r = lane.ci_start(1, "--wait", "1")
    assert "within 1s: no workflow run on it yet" in r.err, f"no run: {r.err}"


# The recording's runs on H: 1 (opened as a draft, its jobs skipped), RUN2 (marked ready; its
# jobs read POLLS times while ci-start waited, scope running alone 3 times), RUN3 (reopened); on
# S, RUN4; and RUN2's scope and check jobs.
RUN2, RUN3, RUN4 = 44009368075, 44009439029, 44009515195
POLLS = 4
ACTIONS = "https://github.com/0xTomDaniel/octo-feather/actions/runs"
JOBS = (f"{ACTIONS}/{RUN2}/job/133792374396", f"{ACTIONS}/{RUN2}/job/133792516055")

if __name__ == "__main__":
    main(refusals, started, not_started)
