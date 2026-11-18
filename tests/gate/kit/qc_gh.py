"""The qc judge's GitHub evidence (#34; octo-feather-qc --help, GitHub evidence; docs/adr/0022), no
network (each qc run under `unshare -cn`: no route) and no model: the testkit's fake gh stands
in for GitHub outside the sandbox (the caller's auth is GH_TOKEN), octo-feather-qc-ghsnap
snapshots it before every run, and the fake judge pi (testkit/judge.py) inside the sandbox reads
it through the offline gh (.agents/skills/github-pr/scripts/gh): issue view, pr view --json, api
GET answer; issue comment and api -X POST are refused, counted in the cleanup line and the
report. Also: the brief names the evidence, the snapshot is read-only inside (an escape check:
e2e, quality spec #test-kinds), refetched per run and removed after, also from a run killed
mid-judge; no GitHub remote skips cleanly; a failed fetch aborts before the judge (67) unless
--no-github; PR 0 is refused before the judge; a failed status commit leaves the status file
unmodified; a copy of the kit judges itself. One judged run is prepared once per gate run
(build_run), the scenarios reading it or judging again from it."""

from __future__ import annotations

import json
import os
import queue
import re
import shutil
import signal
import subprocess
import threading
import time
from pathlib import Path
from typing import Any

from testkit import ROOT, Ran, Scratch, kit, main, pnpm_store, tool_homes
from testkit.qc import LIMIT_S, STATUS, target

OFFLINE_GH = ROOT / ".agents" / "skills" / "github-pr" / "scripts" / "gh"
PROOF = "qc sandbox: ok   github: snapshot"
REFUSED = r"gh \(offline read-only snapshot"


def user(login: str) -> dict[str, str]:
    return {"login": login}


def build(p: Scratch) -> None:
    """The target with origin o/r on GitHub (never contacted: only the fake gh is), and GitHub's
    o/r in the fake gh: issues 1 and 3, draft PR 2, one run, branch main."""
    r = target(p)
    p.git(r, "remote", "add", "origin", "https://github.com/o/r.git")
    g = p.gh
    g.store(
        "repo.json",
        {
            "nameWithOwner": "o/r",
            "name": "r",
            "owner": user("o"),
            "defaultBranchRef": {"name": "main"},
        },
    )
    g.store(
        "issue/1.json",
        {
            "number": 1,
            "title": "Evidence issue",
            "state": "OPEN",
            "updatedAt": "2026-10-19T10:00:00Z",
            "author": user("a"),
            "labels": [],
            "comments": [{"author": user("b"), "body": "a comment", "createdAt": "x"}],
            "url": "u1",
            "body": "b",
        },
    )
    g.store(
        "issue/3.json",
        {
            "number": 3,
            "title": "Closed one",
            "state": "CLOSED",
            "updatedAt": "2026-10-18T10:00:00Z",
            "author": user("a"),
            "labels": [],
            "comments": [],
            "url": "u3",
            "body": "",
        },
    )
    g.put(
        2,
        {
            "number": 2,
            "title": "Draft PR",
            "state": "OPEN",
            "isDraft": True,
            "headRefName": "gh1",
            "headRefOid": "abc123",
            "baseRefName": "main",
            "updatedAt": "2026-10-19T11:00:00Z",
            "author": user("a"),
            "labels": [],
            "url": "u2",
            "body": "",
            "reviews": [],
            "commits": [],
            "files": [],
        },
    )
    g.store("pr/2.diff", "diff --git a/x b/x\n")
    g.store(
        "run/7.json",
        {
            "databaseId": 7,
            "status": "completed",
            "conclusion": "success",
            "displayTitle": "check",
            "workflowName": "check",
            "headBranch": "gh1",
            "event": "push",
            "createdAt": "x",
        },
    )
    g.store("api/repos/o/r.json", {"full_name": "o/r"})
    g.store("api/repos/o/r/labels.json", [])
    g.store("api/repos/o/r/branches.json", [{"name": "main", "commit": {"sha": "abc123"}}])
    for n in (1, 2, 3):
        g.store(
            f"api/repos/o/r/issues/{n}/timeline.json",
            [{"event": "labeled"}, {"event": "commented"}],
        )
    g.store("api/repos/o/r/commits/abc123/check-runs.json", {"total_count": 0, "check_runs": []})


def judge(s: Scratch, kit_dir: Path = ROOT) -> None:
    """The fake judge (testkit/judge.py, of the kit at KIT_DIR) as S's pi."""
    (s.bin / "pi").unlink()
    (s.bin / "pi").symlink_to(kit_dir / "tests" / "gate" / "kit" / "testkit" / "judge.py")


def world(s: Scratch, name: str = "qc-gh") -> None:
    """S filled with prepared NAME (build, or build_run), the fake judge its pi."""
    s.prepare(name, build if name == "qc-gh" else build_run)
    judge(s)


def qc(
    s: Scratch, *args: str, want: int, repo: Path | None = None, q: str | None = None, **env: str
) -> Ran:
    """octo-feather-qc (Q, else the kit's) STATUS ARGS in REPO, offline, bounded by LIMIT_S."""
    cmd = ["unshare", "-cn", "timeout", "-k", "5", LIMIT_S, q or kit("octo-feather-qc"), *args]
    return s.run(cmd, want=want, cwd=repo or s.root / "repo", env=env)


def judged(r: Ran) -> tuple[dict[str, Any], str]:
    """Run R's report (the path its last line names) and acceptance-a's fallback judge's stdout."""
    rep = json.loads(Path(r.out.splitlines()[-1].rpartition("; report ")[2]).read_text())
    return rep, rep["fallback"]["acceptance-a"]["stdout"]


def build_run(p: Scratch) -> None:
    """The target judged once, GitHub its evidence; the run's stdout, stderr and report path (under
    this scratch, as <scratch>) and what it left in TMPDIR, in run.json."""
    world(p)
    r = qc(p, STATUS, "5", "acceptance-a", want=0)
    rep = r.out.splitlines()[-1].rpartition("; report ")[2]
    left = sorted(f.name for f in (p.root / "tmp").iterdir())
    rel = str(Path(rep).relative_to(p.root))
    (p.root / "run.json").write_text(
        json.dumps({"out": r.out, "err": r.err, "report": rel, "left": left})
    )


def prepared_run(s: Scratch) -> tuple[dict[str, Any], dict[str, Any], str]:
    """The prepared run (build_run) in this scratch: its run.json, report and judge's stdout."""
    world(s, "qc-gh-run")
    run = json.loads((s.root / "run.json").read_text())
    rep = json.loads((s.root / run["report"]).read_text())
    return run, rep, rep["fallback"]["acceptance-a"]["stdout"]


def unchanged(s: Scratch, base: str) -> None:
    r = s.root / "repo"
    assert s.git(r, "rev-parse", "HEAD") == base, "the status file was committed"
    assert s.git(r, "status", "--porcelain") == "", "the status file was left modified"


def refused_args(s: Scratch) -> None:
    """PR 0 (and a non-number) refused before the judge or any fetch, status untouched; an id given
    twice refused."""
    world(s)
    base = s.git(s.root / "repo", "rev-parse", "HEAD")
    for pr in ("0", "-3", "x", "07"):
        r = qc(s, STATUS, pr, "acceptance-a", want=64)
        assert "PR must be a positive integer" in r.err + r.out, f"PR {pr}: {r.err}"
    assert s.gh.log() == [], f"a refused PR fetched: {s.gh.log()}"
    assert not (s.home / ".local" / "state" / "octo-feather" / "qc").exists(), "a refused PR judged"
    unchanged(s, base)
    r = qc(s, STATUS, "5", "acceptance-a", "acceptance-a", want=64)
    assert "ids given twice" in r.err + r.out, r.err


def snapshot_read(s: Scratch) -> None:
    """A GitHub repo: fetched outside, reads answered inside through the offline gh, writes refused
    and counted, the brief naming the evidence; the snapshot scratch removed after the run."""
    run, rep, j = prepared_run(s)
    err = run["err"]
    line = (
        rf"{PROOF} of o/r at .*issues 2, prs 1, runs 1, branches 1, full views 3; read-only, "
        rf"served by the offline gh \({re.escape(str(OFFLINE_GH))}\)"
    )
    assert re.search(line, err), f"no github proof line: {err}"
    lines = j.splitlines()
    assert f"gh is {OFFLINE_GH}" in lines, f"the judge's gh is not the offline gh: {j}"
    brief = "\n".join(ln[6:] for ln in lines if ln.startswith("BRIEF "))
    assert "history only:" in brief, brief
    assert "GitHub: `gh` is an offline, read-only snapshot of o/r" in brief, brief
    assert "R1 Evidence issue OPEN" in lines, j
    r2 = next(ln for ln in lines if ln.startswith("R2 "))
    assert re.sub(r"\s", "", r2[3:]) == '{"isDraft":true,"title":"DraftPR"}', r2
    assert "R3 2" in lines, j
    assert re.search(
        rf"^W1 {REFUSED}.*not in the read-only snapshot.*no writes", j, re.MULTILINE
    ), j
    assert re.search(rf"^W2 {REFUSED}.*write refused", j, re.MULTILINE), j
    assert "offline gh refusals 2" in run["out"] + err, run["out"]
    assert rep["gh_misses"] == 2, rep["gh_misses"]
    assert rep["github"]["repo"] == "o/r", rep["github"]
    assert rep["github"]["snapshot"]["counts"]["issues"] == 2, rep["github"]
    log = s.gh.log()
    assert not any(ln.startswith(("issue comment", "api -X")) or "POST" in ln for ln in log), (
        f"a judge write reached gh: {log}"
    )
    assert not [f for f in run["left"] if f.startswith(f"qc-ghsnap-{rep['run_id']}-")], (
        f"snapshot scratch left: {run['left']}"
    )


def snapshot_read_only(s: Scratch) -> None:
    """The sandbox's escape check (e2e: quality spec #test-kinds): the judge cannot write the
    snapshot it reads."""
    _, _, j = prepared_run(s)
    assert "ESCAPE" not in j, f"snapshot writable inside the sandbox: {j}"


def killed(s: Scratch) -> None:
    """A run killed mid-judge as a timeout kills it (TERM to it, then to its process group, the 2nd
    send landing during qc's cleanup as on a loaded box, #235) leaves no snapshot behind, and its
    judge does not survive. The kill waits on readiness (the proof line said, the judge started),
    never a sleep."""
    world(s)
    mark = f"9{os.getpid()}{time.monotonic_ns() % 1000}"  # the judge's sleep, unique to this run
    cmd = [
        "unshare",
        "-cn",
        "timeout",
        "-k",
        "5",
        LIMIT_S,
        kit("octo-feather-qc"),
        STATUS,
        "5",
        "acceptance-a",
    ]
    p = subprocess.Popen(
        cmd,
        cwd=s.root / "repo",
        env={**s.env, "FAKE_PI_HANG": mark},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    lines: queue.Queue[str | None] = queue.Queue()
    said: list[str] = []

    def read() -> None:
        assert p.stderr
        for ln in p.stderr:
            lines.put(ln)
        lines.put(None)

    threading.Thread(target=read, daemon=True).start()
    while True:
        ln = lines.get(timeout=float(LIMIT_S))
        assert ln is not None, f"the judge never started: {''.join(said)}"
        said.append(ln)
        if ln.startswith(PROOF):
            break
    while not alive(mark):
        assert p.poll() is None, f"qc ended before its judge started: {''.join(said)}"
        time.sleep(0.01)  # a process-state wait: the judge's sleep is running
    os.kill(p.pid, signal.SIGTERM)
    while True:  # until the group is gone: its leader reaped (poll) and every member exited
        p.poll()
        try:
            os.killpg(p.pid, signal.SIGTERM)
        except ProcessLookupError:
            break
        time.sleep(0.0005)
    rc = p.wait()
    assert rc != 0, "the killed run exited 0"
    left = [f.name for f in (s.root / "tmp").iterdir()]
    assert left == [], f"the killed run left scratch: {left}"
    end = time.monotonic() + 10
    while alive(mark):
        assert time.monotonic() < end, "the killed run's judge survived"
        time.sleep(0.01)


def alive(mark: str) -> bool:
    """Whether a process `sleep MARK` runs."""
    want = f"sleep\0{mark}\0".encode()

    def cmdline(d: Path) -> bytes:
        try:
            return (d / "cmdline").read_bytes()
        except OSError:  # gone meanwhile
            return b""

    return any(cmdline(d) == want for d in Path("/proc").iterdir() if d.name.isdigit())


def fetch_fails(s: Scratch) -> None:
    """A fetch failure (network down, or no auth) aborts before the judge (67), naming --no-github,
    the status file untouched."""
    world(s)
    base = s.git(s.root / "repo", "rev-parse", "HEAD")
    (s.gh.dir / "down").touch()
    r = qc(s, STATUS, "5", "acceptance-a", want=67)
    said = r.out + r.err
    assert re.search(
        r"GitHub snapshot of o/r failed; judge not started.*--no-github.*error connecting",
        said,
        re.DOTALL,
    ), said
    assert "qc sandbox:" not in said, f"the sandbox started after a failed fetch: {said}"
    unchanged(s, base)
    (s.gh.dir / "down").unlink()
    r = qc(s, STATUS, "5", "acceptance-a", want=67, GH_TOKEN="")
    assert "gh auth login" in r.out + r.err, r.err
    unchanged(s, base)


def no_github(s: Scratch) -> None:
    """--no-github with the fetch failing: the run judges without it, said in the proof, the
    offline gh refusing."""
    world(s)
    (s.gh.dir / "down").touch()
    r = qc(s, STATUS, "5", "acceptance-a", "--no-github", want=0)
    assert "qc sandbox: ok   github: SKIPPED (--no-github; o/r not fetched" in r.err, r.err
    _, j = judged(r)
    assert re.search(rf"^R1 {REFUSED}.*\): github: SKIPPED", j, re.MULTILINE), j


def status_commit_fails(s: Scratch) -> None:
    """The status commit fails after the judge ran: exit 3, the status file restored, nothing
    uncommitted. That second run of the prepared target fetched its snapshot anew."""
    world(s, "qc-gh-run")
    r = s.root / "repo"
    s.git(r, "reset", "-q", "--hard", "HEAD~1")  # the prepared run's status commit undone
    base = s.git(r, "rev-parse", "HEAD")
    hooks = s.root / "hooks"
    hooks.mkdir()
    (hooks / "pre-commit").write_text("#!/bin/sh\nexit 1\n")
    (hooks / "pre-commit").chmod(0o755)
    s.git(r, "config", "core.hooksPath", str(hooks))
    ran = qc(s, STATUS, "5", "acceptance-a", want=3)
    assert "status commit failed" in ran.out + ran.err, ran.err
    unchanged(s, base)
    views = [ln for ln in s.gh.log() if ln.startswith("repo view")]
    assert len(views) == 2, f"the snapshot was not refetched per run: {s.gh.log()}"


def snapshot_misses(s: Scratch) -> None:
    """The offline gh on --json, on the snapshot octo-feather-qc-ghsnap wrote of o/r: a field the
    snapshot does not store is refused, logged and counted, never a made-up null; a stored null
    (open PR 2's mergedAt) and a stored value are returned. The fields asked are ones gh takes and
    the writer never fetches (its IF, PF, PL, RUN, repo view): reviews, labels and description,
    asked before of a hand-written snapshot, are fetched (#936); run 7's conclusion is a stored
    value, as gh answers "" for a run in progress, never null."""
    s.prepare("qc-gh", build)
    sn = s.root / "snap"
    s.run([kit("octo-feather-qc-ghsnap"), "o/r", str(sn)])
    miss = s.root / "miss.log"
    env = {"OCTO_FEATHER_GHSNAP": str(sn), "OCTO_FEATHER_GHSNAP_MISS": str(miss)}

    def gh(want: int, *a: str) -> str:
        r = s.run([str(OFFLINE_GH), *a], want=want, env=env)
        return r.out + r.err

    calls = (
        "run view 7 --json jobs",
        "run view 7 --json conclusion,jobs",
        "pr view 2 --json title,projectItems",
        "pr list --json number,isInMergeQueue",
        "issue list --json number,reactionGroups",
        "run list --json databaseId,jobs",
        "repo view --json nameWithOwner,stargazerCount",
    )
    for n, c in enumerate(calls, 1):
        out = gh(1, *c.split())
        field = re.split(r"[, ]", c)[-1]
        assert f"not in snapshot: {field} " in out, f"gh {c}: no 'not in snapshot' refusal: {out}"
        assert "null" not in out, f"gh {c} answered a made-up null: {out}"
        assert len(miss.read_text().splitlines()) == n, (
            f"gh {c}: refusal not logged: {miss.read_text()}"
        )
    assert '"conclusion": "success"' in gh(0, "run", "view", "7", "--json", "conclusion,status")
    assert gh(0, "pr", "view", "2", "--json", "mergedAt", "-q", ".mergedAt") == "null"
    assert '"mergedAt": null' in gh(0, "pr", "list", "--json", "number,mergedAt")
    assert len(miss.read_text().splitlines()) == len(calls), "a stored field was logged as a miss"


def diff_too_large(s: Scratch) -> None:
    """A PR whose diff GitHub refuses as over its file limit (its real answer, recorded:
    testkit/recordings/pr-diff-too-large.json) never aborts the snapshot: its answer recorded
    beside its diff, named in the summary, every other item fetched; the offline gh refuses
    `pr diff` for it, saying so, logged. Any other `pr diff` failure, a 406 that is not
    too_large included, still aborts."""
    s.prepare("qc-gh", build)
    g = s.gh
    g.put(4, {**g.pr(2), "number": 4, "title": "Huge PR", "headRefOid": "def456"})
    g.store("api/repos/o/r/issues/4/timeline.json", [])
    g.store("api/repos/o/r/commits/def456/check-runs.json", {"total_count": 0, "check_runs": []})
    tape = Path(__file__).parent / "testkit" / "recordings" / "pr-diff-too-large.json"
    (rec,) = json.loads(tape.read_text())
    g.store("pr/4.diff.err", rec["err"])
    sn = s.root / "snap"
    r = s.run([kit("octo-feather-qc-ghsnap"), "o/r", str(sn)])
    assert re.search(r"prs 2, .*full views 4.*diff too large on GitHub.*#4", r.out), r.out
    assert (sn / "diff" / "4.too-large").read_text() == rec["err"]
    got = sorted(str(p.relative_to(sn)) for p in sn.rglob("*") if p.is_file())
    for f in ("pr/2.json", "pr/4.json", "diff/2.diff", "issue/1.json", "issue/3.json"):
        assert f in got, f"{f} not fetched: {got}"
    assert "api/repos__o__r__commits__def456__check-runs.json" in got, got
    assert "diff/4.diff" not in got, got
    miss = s.root / "miss.log"
    env = {"OCTO_FEATHER_GHSNAP": str(sn), "OCTO_FEATHER_GHSNAP_MISS": str(miss)}
    o = s.run([str(OFFLINE_GH), "pr", "diff", "4"], want=1, env=env)
    assert re.search(
        rf"{REFUSED}.*diff for pr 4 not in snapshot: too large on GitHub: .*HTTP 406", o.err
    ), o.err
    assert len(miss.read_text().splitlines()) == 1, miss.read_text()
    assert s.run([str(OFFLINE_GH), "pr", "diff", "2"], env=env).out == "diff --git a/x b/x"
    for n, err in enumerate((rec["err"].replace("too_large", "invalid"), "HTTP 502: Bad Gateway")):
        g.store("pr/4.diff.err", err)
        r = s.run([kit("octo-feather-qc-ghsnap"), "o/r", str(s.root / f"snap{n}")], want=1)
        assert f"gh pr diff 4: {err.splitlines()[0]}" in r.err, r.err


def kit_on_kit(s: Scratch) -> None:
    """A copy of the kit judging itself (the kit inside the judged worktree), a repo with no GitHub
    remote: the proof passes and says so; no fetch, the offline gh refusing every call, the
    refusals counted."""
    kc = s.root / "kc"
    # The box's uv Pythons, uv cache and pnpm store, kept while HOME moves: octo-feather-qc collects
    # the copy's tagged tests offline through its just check-tests.
    s.env |= tool_homes() | {"npm_config_store_dir": pnpm_store()}
    files = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],  # noqa: S607
        cwd=ROOT,
        capture_output=True,
        check=True,
    ).stdout.decode()
    for rel in filter(None, files.split("\0")):
        src = ROOT / rel
        if src.is_file() or src.is_symlink():
            (kc / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, kc / rel, follow_symlinks=False)
    s.link_fakes(kc)
    judge(s, kc)
    # The kit's own status files name accepted commits this fresh repo lacks: only zz-demo judged.
    for f in (
        *(kc / "docs" / "specs").glob("*.status.json"),
        *(kc / "docs" / "specs").glob("*.calls.jsonl"),
    ):
        f.unlink()
    shutil.copy(
        ROOT / "tests" / "fixtures" / "spec-status" / "good" / "demo.spec.html",
        kc / "docs" / "specs" / "zz-demo.spec.html",
    )
    git = ["-c", "core.hooksPath=/dev/null", "-c", "user.email=t@t", "-c", "user.name=t"]
    s.git(kc, "init", "-q", "-b", "main")
    s.git(kc, "add", "-A")
    s.git(kc, *git, "commit", "-qm", "kit")
    short = s.git(kc, "rev-parse", "--short", "HEAD")
    s.run([kit("octo-feather-spec-status"), "init", "docs/specs/zz-demo.spec.html", short], cwd=kc)
    s.git(kc, "add", "-A")
    s.git(kc, *git, "commit", "-qm", "status")
    for k, v in (("user.email", "t@t"), ("user.name", "t"), ("commit.gpgsign", "false")):
        s.git(kc, "config", k, v)
    r = qc(
        s,
        "docs/specs/zz-demo.status.json",
        "5",
        "acceptance-a",
        want=0,
        repo=kc,
        q=str(kc / "scripts" / "octo-feather-qc"),
    )
    assert "qc sandbox: ok   HOME, /var/tmp read-only; the kit is the judged worktree" in r.err, (
        r.err
    )
    none = "github: none (no GitHub remote); the offline gh refuses every call (exit 1)"
    assert f"qc sandbox: ok   {none}" in r.err, r.err
    assert s.gh.log() == [], f"a run with no GitHub remote called gh: {s.gh.log()}"
    _, j = judged(r)
    assert re.search(rf"^R1 {REFUSED}.*\): github: none \(no GitHub remote\)", j, re.MULTILINE), j
    assert "offline gh refusals 5" in r.out, r.out


if __name__ == "__main__":
    main(
        refused_args,
        snapshot_read,
        snapshot_read_only,
        killed,
        fetch_fails,
        no_github,
        status_commit_fails,
        snapshot_misses,
        diff_too_large,
        kit_on_kit,
    )
