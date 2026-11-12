"""The scenarios of tests/gate/kit/test_lane_post_merge.py (its items), this file their command
(testkit.main): scripts/octo-feather-lane post-merge, the director's post-merge routine (owner
ruling 2026-10-29 on issue 206; steps 1-2, issue 396), offline: the testkit's fake gh holds PR #7
and the push runs of its merge commit (a tape per run list and run watch: the runs start and end
between calls), and logs every call. Step 1 stops, exit 1, on a PR not merged and on one merged at
another head; step 2 stops on a red run naming its URL, on no run within the --wait bound, and on a
watch that fails with its run unfinished; all runs concluded success passes. Every run ends with a
one-line summary of each step's outcome, and only gh reads run (rerun safe), asserted after every
run. Step 3 (issue 397) refreshes a throwaway kit install clone (OCTO_FEATHER_KIT_INSTALL, always
set here: never the live kit), its origin a local bare repo behind a GitHub URL: the install's own
justfile recipes (vendored-fetch, install-check) and the real mise run; `uv sync` and `pnpm
install`, which would reach the package registries, are testkit/argv_recorder.sh (a plain seam
stand-in for the registries), except where a refresh fails: the real uv fails for real (no lockfile;
the pinned Python absent, downloads off). Step 4 (issue 398, tests/lane-post-merge-tell.sh) reads a
throwaway state dir (XDG_STATE_HOME) with no lane record, so it tells no pane; step 5 (issue 399,
tests/gate/kit/lane_post_merge_teardown.py) finds no archived record, so it is pending and a green
run exits 3.

The kit's origin (B, then the merge commit M with a pyproject, then P past it with a mise.toml; and
M2 off B pinning a Python no one has), its install clone and the target repo are prepared once per
gate run (testkit Scratch.prepare); each case moves the install clone, never clones.
"""

from __future__ import annotations

import json
import os
import re
import sys
from typing import TYPE_CHECKING

from testkit import HERE, ROOT, Ran, Scratch, kit, main, tool_homes

if TYPE_CHECKING:
    from collections.abc import Sequence

H = "1234567890abcdef1234567890abcdef12345678"  # the pinned head
FIELDS = "databaseId,status,conclusion,workflowName,url"  # post-merge's run list fields
BASE_FIELDS = FIELDS + ",headSha"
PR_FIELDS = "state,headRefOid,mergeCommit,baseRefName,headRefName"
PIN = "{}.{}.{}".format(*sys.version_info[:3])  # an installed Python: the one running this
NO_PIN = "3.8.1"  # a Python no box here installs
TREES = "api/repos/o/r/git/trees"
# The gh calls post-merge may make: every one a read.
READS = re.compile(
    r"pr view .*|run list .*|run watch .*|repo view .*|api repos/\S+/git/trees/\S+"
    r"|api repos/\S+/compare/\S+ --jq \.status"
)
# The install's own recipes, run by the real just: each records its call as the recorder does.
JUSTFILE = (
    "vendored-fetch:\n"
    "    @printf '%s\\0' just '{{invocation_directory()}}' vendored-fetch >>\"$ARGV_LOG\"; "
    'echo >>"$ARGV_LOG"\n\n'
    "install-check target:\n"
    "    @printf '%s\\0' just '{{invocation_directory()}}' install-check '{{target}}' "
    '>>"$ARGV_LOG"; echo >>"$ARGV_LOG"\n'
)
SUMMARY = "post-merge gh7 PR #7: step 1 merged {}; step 2 main CI {}; step 3 kit refresh {}; "
STOP1 = SUMMARY.format("stopped", "not run", "not run") + (
    "step 4 tell supervisors not run; step 5 teardown not run"
)
STOP2 = SUMMARY.format("ok", "stopped", "not run") + (
    "step 4 tell supervisors not run; step 5 teardown not run"
)
STOP3 = SUMMARY.format("ok", "ok", "stopped") + (
    "step 4 tell supervisors not run; step 5 teardown not run"
)
GREEN = SUMMARY.format("ok", "ok", "ok") + "step 4 tell supervisors ok; step 5 teardown pending"


def build(p: Scratch) -> None:
    """origin.git (main: B, M, P; py: M2 off B), the install clone of it at B, the target repo."""
    o, seed = p.root / "origin.git", p.root / "seed"
    p.run(["git", "init", "-q", "--bare", "-b", "main", str(o)])
    p.git(p.root, "init", "-q", "-b", "main", str(seed))

    def commit(msg: str, files: dict[str, str]) -> None:
        for f, text in files.items():
            (seed / f).write_text(text)
        p.git(seed, "add", "-A")
        p.git(seed, "commit", "-qm", msg)

    commit("b", {".python-version": f"{PIN}\n", "justfile": JUSTFILE, "a": ""})
    pyproject = '[project]\nname = "k"\nversion = "0"\n'
    commit("m", {"pyproject.toml": pyproject})
    pin = re.search(r'^just = "(.+)"$', (ROOT / "mise.toml").read_text(), re.MULTILINE)
    assert pin, "the kit's mise.toml pins no just"
    lock = (ROOT / "mise.lock").read_text()
    just_lock = lock[lock.index("[[tools.just]]") :]
    just_lock = just_lock[: just_lock.find("\n[[", 1) + 1 or None]
    commit("p", {"mise.toml": f'[tools]\njust = "{pin[1]}"\n', "mise.lock": just_lock})
    p.git(seed, "push", "-q", str(o), "HEAD:main")
    p.git(seed, "checkout", "-q", "-b", "py", "HEAD~2")
    commit("m2", {".python-version": f"{NO_PIN}\n", "pyproject.toml": pyproject})
    p.git(seed, "push", "-q", str(o), "HEAD:py")
    p.run(["git", "clone", "-q", str(o), str(p.root / "kit")])
    p.git(p.root, "init", "-q", str(p.root / "target"))


class Lane:
    """The prepared world in S: the commits, the install, gh's store; `run` runs post-merge."""

    def __init__(self, s: Scratch) -> None:
        s.prepare("lane-post-merge", build)
        self.s, self.kit, self.target = s, s.root / "kit", s.root / "target"
        o = s.root / "origin.git"
        log = s.git(o, "log", "--format=%H", "main")
        self.p, self.m, self.b = log.split("\n")
        self.m2 = s.git(o, "rev-parse", "py")
        self.state = s.root / "state"
        self.argv = s.root / "argv.log"
        rec, rec_pnpm = s.root / "rec", s.root / "rec-pnpm"
        for d, names in ((rec, ("uv", "pnpm")), (rec_pnpm, ("pnpm",))):
            d.mkdir()
            for n in names:
                (d / n).symlink_to(HERE / "argv_recorder.sh")
        # FORCE_COLOR (a CI runner's) unset, NO_COLOR set: the real uv colours its own error, which
        # step 3 quotes and a case asserts in uv's words (testkit.asked, the same).
        for k in ("VIRTUAL_ENV", "HERDR_SESSION", "GH_REPO", "FORCE_COLOR"):
            s.env.pop(k, None)
        s.env["NO_COLOR"] = "1"
        s.env |= {
            "XDG_STATE_HOME": str(self.state),
            "OCTO_FEATHER_KIT_INSTALL": str(self.kit),
            "ARGV_LOG": str(self.argv),
        }
        self.path = {"rec": f"{rec}{os.pathsep}", "real-uv": f"{rec_pnpm}{os.pathsep}"}
        self.homes: dict[str, str] = {}  # the tools' own installs: step 3's real mise and uv
        s.gh.store("repo.json", {"nameWithOwner": "o/r"})
        s.gh.store("api/repos/o/kit.json", {"nameWithOwner": "o/kit"})
        self.merge, self.repo = self.m, ""  # PR #7's merge commit; the --repo gh is asked with
        self.install(self.b, "o/kit")  # steps 1-2: the PR's repo is not the install's

    def install(self, at: str, repo: str = "o/r") -> None:
        """The install clone detached at AT, clean, origin https://github.com/REPO.git (this
        scratch's origin.git behind it); the call log emptied."""
        k, url = self.kit, f"https://github.com/{repo}.git"
        self.s.git(k, "checkout", "-q", "--detach", "-f", at)
        self.s.git(k, "clean", "-qfdx")
        self.s.git(k, "remote", "set-url", "origin", url)
        self.s.git(k, "config", f"url.{self.s.root / 'origin.git'}.insteadOf", url)
        self.argv.unlink(missing_ok=True)

    def head(self) -> str:
        return self.s.git(self.kit, "rev-parse", "HEAD")

    def calls(self) -> list[list[str]]:
        """The refresh calls recorded, each [name, cwd, *argv], in order."""
        if not self.argv.exists():
            return []
        return [x.split("\0")[:-1] for x in self.argv.read_text().splitlines()]

    def pr(self, state: str = "MERGED", head: str = H) -> None:
        """PR #7 STATE at HEAD, its merge commit self.merge."""
        self.s.gh.put(
            7,
            {
                "state": state,
                "headRefOid": head,
                "mergeCommit": {"oid": self.merge} if state == "MERGED" else None,
                "baseRefName": "main",
                "headRefName": "gh7",
            },
        )

    def store(
        self,
        lists: Sequence[Sequence[dict[str, object]]] = ((),),
        watch: dict[int, dict[str, object]] | None = None,
        base: Sequence[Sequence[dict[str, object]]] = (),
        compare: dict[str, str] | None = None,
        wf: Sequence[tuple[str, str]] | None = (("check.yml", "blob"),),
    ) -> None:
        """PR #7 merged at H (self.pr); the merge commit's push runs, LISTS one answer per run
        list (no repetition after exhaustion); each WATCH run's watch answer; BASE the base's later
        push runs of `check` per list; COMPARE each sha's compare
        status against the merge commit; the merge commit's .github/workflows entries WF (None: no
        .github). With self.repo, gh is asked with -R it."""
        g, m, repo = self.s.gh, self.merge, self.repo
        self.pr()
        r = f" -R {repo}" if repo else ""

        def ans(runs: Sequence[dict[str, object]], fields: str) -> str:
            return json.dumps([{f: x[f] for f in fields.split(",")} for x in runs]) + "\n"

        ids = {int(str(x["databaseId"])) for ls in (*lists, *base) for x in ls}
        tapes: dict[str, list[object]] = {
            f"run list --commit {m} --event push --json {FIELDS}{r}": [
                ans(ls, FIELDS) for ls in lists
            ],
            **{f"run watch {i} --exit-status{r}": [(watch or {}).get(i, "")] for i in ids},
        }
        if base:
            key = "run list --branch main --event push --workflow check --limit 20 --json "
            tapes[key + BASE_FIELDS + r] = [ans(ls, BASE_FIELDS) for ls in base]
        for sha, status in (compare or {}).items():
            tapes[f"api repos/{{owner}}/{{repo}}/compare/{m}...{sha} --jq .status"] = [
                status + "\n"
            ]
        g.tape(tapes)
        for f in (g.dir / TREES).glob("*.json") if (g.dir / TREES).is_dir() else ():
            f.unlink()

        def tree(sha: str, entries: Sequence[tuple[str, str, str]]) -> None:
            t = [{"path": p, "type": k, "sha": x} for p, k, x in entries]
            g.store(f"{TREES}/{sha}.json", {"sha": sha, "tree": t})

        if wf is None:
            tree(m, [("README.md", "blob", "r")])
        elif wf:
            tree(m, [("README.md", "blob", "r"), (".github", "tree", "g")])
            tree("g", [("workflows", "tree", "w")])
            tree("w", [(p, k, "b") for p, k in wf])

    def run(self, want: int, *args: str, tools: str = "rec") -> Ran:
        """post-merge ARGS from the target repo, exit WANT; gh only read (each logged call)."""
        env = {"PATH": self.path[tools] + self.s.env["PATH"]} | self.homes
        r = self.s.run([kit("octo-feather-lane"), *args], want=want, cwd=self.target, env=env)
        wrote = [x for x in self.s.gh.log() if not READS.fullmatch(x)]
        assert not wrote, f"{args}: ran a gh write: {self.s.gh.log()}"
        return r


def run1(name: str, status: str, conclusion: str, i: int, head: str = "") -> dict[str, object]:
    """A push run as gh lists it."""
    return {
        "databaseId": i,
        "status": status,
        "conclusion": conclusion,
        "workflowName": name,
        "headSha": head,
        "url": f"https://github.com/o/r/actions/runs/{i}",
    }


def last(r: Ran) -> str:
    return r.out.split("\n")[-1]


def says(r: Ran, what: str, *wants: str, summary: str = "") -> None:
    """R's stdout holds each of WANTS, its last line SUMMARY (when given); WHAT names the case."""
    for w in wants:
        assert w in r.out, f"{what}: no {w!r} in: {r.out}"
    assert not summary or last(r) == summary, f"{what} summary: {last(r)}"


def merged_step(s: Scratch) -> None:
    """Step 1: not merged, merged at another head, gh failing: stop at step 1, step 2 not run, no
    run list. Usage: missing --lane, a HEAD that is no sha."""
    lane = Lane(s)
    green = run1("check", "completed", "success", 11, lane.m)
    lane.store([[green]])
    lane.pr("OPEN")
    r = lane.run(1, "post-merge", "7", H[:7], "--lane", "gh7")
    assert "step 1 merged: stopped: PR #7 is OPEN, not merged" in r.out, f"not merged: {r.out}"
    assert last(r) == STOP1, f"not merged summary: {last(r)}"
    assert not [x for x in s.gh.log() if x.startswith("run ")], (
        f"not merged listed runs: {s.gh.log()}"
    )
    lane.pr("MERGED", "abcdef0" + H)
    r = lane.run(1, "post-merge", "7", H[:12], "--lane", "gh7")
    want = "step 1 merged: stopped: PR #7 merged at head abcdef012345, not at the pinned head "
    says(r, "other head", want + H[:12], summary=STOP1)
    r = lane.run(1, "post-merge", "8", H, "--lane", "gh7")
    assert "step 1 merged: stopped: gh pr view 8 failed" in r.out, f"gh failing: {r.out}"
    assert "step 1 merged stopped" in last(r), f"gh failing: {r.out}"
    r = lane.run(1, "post-merge", "7", H)
    assert "usage: octo-feather-lane post-merge PR HEAD --lane NAME" in r.err, f"usage: {r.err}"
    r = lane.run(1, "post-merge", "7", "nothex", "--lane", "gh7")
    assert "HEAD must be" in r.err, f"bad head: {r.err}"


def main_ci(s: Scratch) -> None:
    """Step 2: a run in progress is watched to its end with --exit-status, a second workflow joins;
    every run success: exit 3 (step 5 pending), one line per step and the summary; the PR's repo
    not the install's leaves it unchanged; a rerun the same. A run appearing within the bound is
    waited for. A red run stops naming its URL; a watch failing while its run reads unfinished
    stops naming it."""
    lane = Lane(s)
    m = lane.m
    m12 = m[:12]
    green = run1("check", "completed", "success", 11, m)
    lint = run1("lint", "completed", "success", 12, m)
    busy = run1("check", "in_progress", "", 11, m)
    red = run1("check", "completed", "failure", 13, m)
    lanes = lane.state / "octo-feather" / "lanes"
    lane.repo = "o/r"
    lane.store(lists=[[busy], [green, lint]])
    for _ in range(2):  # the rerun: same result, still reads only
        r = lane.run(3, "post-merge", "7", H, "--lane", "gh7", "--repo", "o/r")
        step1 = f"PR #7 (gh7) merged into main at head {H[:12]}, merge commit {m12}"
        assert r.out.split("\n")[0] == f"step 1 merged: ok: {step1}", f"step 1 line: {r.out}"
        says(
            r,
            "green",
            f"step 2 main CI: ok: 2 push runs on {m12} concluded success: check "
            "https://github.com/o/r/actions/runs/11, lint https://github.com/o/r/actions/runs/12",
            "step 3 kit refresh: ok: kit install unchanged: PR in o/r, install is o/kit",
            f"step 4 tell supervisors: ok: no other open lane in {lanes} to tell",
            summary=GREEN,
        )
        assert len(r.out.split("\n")) == 6, f"green prints one line per step, a summary: {r.out}"
        assert (lane.head(), lane.calls()) == (lane.b, []), "other repo moved or refreshed"
        log = s.gh.log()
        assert "run watch 11 --exit-status -R o/r" in log, f"run not watched in o/r: {log}"
        assert f"pr view 7 --json {PR_FIELDS} -R o/r" in log, f"pr view: {log}"
        lane.store(lists=[[busy], [green, lint]])
    lane.repo = ""
    lane.store(lists=[[], [green]])
    r = lane.run(3, "post-merge", "7", H, "--lane", "gh7", "--wait", "1")
    says(r, "late run", f"step 2 main CI: ok: 1 push run on {m12} concluded success")
    lane.store(lists=[[red, lint]], watch={13: {"err": "run 13 failed\n", "exit": 1}})
    r = lane.run(1, "post-merge", "7", H, "--lane", "gh7")
    red_line = f"step 2 main CI: stopped: main CI red on {m12}: check failure "
    says(r, "red", red_line + "https://github.com/o/r/actions/runs/13", summary=STOP2)
    assert "concluded success" not in r.out, f"red: {r.out}"
    lane.store(
        lists=[[busy], [busy]], watch={11: {"err": "failed to get run: HTTP 502\n", "exit": 1}}
    )
    r = lane.run(1, "post-merge", "7", H, "--lane", "gh7")
    assert re.search(
        r"step 2 main CI: stopped: gh run watch 11 failed.*https://github.com/o/r/actions/runs/11",
        r.out,
    ), f"watch failed: {r.out}"


def no_ci(s: Scratch) -> None:
    """Step 2 with no run: no run within the bound stops naming the workflows (either suffix,
    beside other files); an unreadable tree stops naming the read. No workflow file (no .github,
    or none in .github/workflows) is the no-CI fact: one run list, no wait, steps 3-5 run, rerun
    the same."""
    lane = Lane(s)
    m = lane.m
    m12 = m[:12]
    lane.store()
    r = lane.run(1, "post-merge", "7", H, "--lane", "gh7", "--wait", "0")
    none = f"stopped: no push run on merge commit {m12} within 0s, its workflows .github/workflows/"
    says(r, "no run", f"step 2 main CI: {none}check.yml", summary=STOP2)
    lane.store(wf=())
    r = lane.run(1, "post-merge", "7", H, "--lane", "gh7", "--wait", "0")
    tree = f"gh api repos/{{owner}}/{{repo}}/git/trees/{m} failed (gh: Not Found (HTTP 404))"
    says(r, "unreadable tree", f"step 2 main CI: stopped: {tree}")
    lane.store(wf=[("deploy.yaml", "blob"), ("README.md", "blob"), ("ci", "tree")])
    r = lane.run(1, "post-merge", "7", H, "--lane", "gh7", "--wait", "0", "--repo", "o/r")
    says(r, "yaml workflow", f"{none}deploy.yaml:")
    assert f"api repos/o/r/git/trees/{m}" in s.gh.log(), f"--repo tree read: {s.gh.log()}"
    noci = (
        f"step 2 main CI: ok: no CI: no workflow file under .github/workflows at merge commit "
        f"{m12} (gh api repos/<this repo>/git/trees/{m12}), so no push run can appear; nothing "
        "to wait for"
    )
    other = [("README.md", "blob"), ("ci.yml.off", "blob"), ("old.yml", "tree")]
    for wf in (None, other, None):
        lane.store(wf=wf)
        r = lane.run(3, "post-merge", "7", H, "--lane", "gh7", "--wait", "1")
        assert noci in r.out.split("\n"), f"no CI ({wf}): {r.out}"
        assert last(r) == GREEN, f"no CI summary: {r.out}"
        lists = [x for x in s.gh.log() if x.startswith("run ")]
        assert len(lists) == 1, f"no CI listed runs again or watched: {s.gh.log()}"


def superseded(s: Scratch) -> None:
    """A run cancelled by a later push (concurrency cancel-in-progress; rule: octo-feather-lane
    --help, post-merge step 2) defers to the first later push run of its workflow on main whose
    head contains the merge commit (gh compare ahead or identical): ok only on its success, naming
    both; still running, it is watched to its end; cancelled in turn, it defers again; red, it
    stops naming both; none within the bound (only an older one, and one on a diverged head)
    stops as red; another run red beside the cancelled one stops first, no later-run read."""
    lane = Lane(s)
    m = lane.m
    m12 = m[:12]
    sn, so, sp = "a" * 40, "b" * 40, "c" * 40
    cmp = {sn: "ahead", sp: "identical", so: "diverged"}
    gone = run1("check", "completed", "cancelled", 21, m)
    old = run1("check", "completed", "success", 20, so)
    lint = run1("lint", "completed", "success", 12, m)
    via = (
        "check https://github.com/o/r/actions/runs/21 cancelled, superseded by "
        f"https://github.com/o/r/actions/runs/22 on {sn[:12]} (contains {m12})"
    )
    base = [
        old,
        run1("check", "completed", "failure", 26, sp),
        run1("check", "completed", "success", 22, sn),
        run1("check", "completed", "success", 23, so),
    ]
    lane.store(lists=[[gone, lint]], base=[base], compare=cmp)
    r = lane.run(3, "post-merge", "7", H, "--lane", "gh7", "--wait", "0")
    want = (
        f"step 2 main CI: ok: 2 push runs on {m12} concluded success: {via}, lint "
        "https://github.com/o/r/actions/runs/12"
    )
    assert want in r.out.split("\n"), f"superseded: {r.out}"
    log = s.gh.log()
    assert (
        f"run list --branch main --event push --workflow check --limit 20 --json {BASE_FIELDS}"
        in log
    ), f"superseded reads: {log}"
    assert f"api repos/{{owner}}/{{repo}}/compare/{m}...{sn} --jq .status" in log, log
    lane.store(
        lists=[[gone]],
        base=[
            [run1("check", "in_progress", "", 22, sn)],
            [run1("check", "completed", "success", 22, sn)],
        ],
        compare=cmp,
    )
    r = lane.run(3, "post-merge", "7", H, "--lane", "gh7", "--wait", "0")
    want = f"step 2 main CI: ok: 1 push run on {m12} concluded success: {via}"
    assert want in r.out.split("\n"), f"superseded watched: {r.out}"
    assert "run watch 22 --exit-status" in s.gh.log(), f"superseded watched: {s.gh.log()}"
    lane.store(
        lists=[[gone]],
        base=[
            [run1("check", "completed", "cancelled", 22, sn)],
            [
                run1("check", "completed", "cancelled", 22, sn),
                run1("check", "completed", "success", 25, sp),
            ],
        ],
        compare=cmp,
    )
    r = lane.run(3, "post-merge", "7", H, "--lane", "gh7", "--wait", "0")
    want = (
        f"step 2 main CI: ok: 1 push run on {m12} concluded success: check "
        "https://github.com/o/r/actions/runs/21 cancelled, superseded by "
        f"https://github.com/o/r/actions/runs/25 on {sp[:12]} (contains {m12})"
    )
    assert want in r.out.split("\n"), f"superseded twice: {r.out}"
    lane.store(lists=[[gone]], base=[[run1("check", "completed", "failure", 22, sn)]], compare=cmp)
    r = lane.run(1, "post-merge", "7", H, "--lane", "gh7", "--wait", "0")
    want = (
        f"step 2 main CI: stopped: main CI red on {m12}: {via}, failure; fix main first, nothing "
        "after this step runs"
    )
    assert want in r.out.split("\n"), f"superseded red: {r.out}"
    lane.store(
        lists=[[gone]], base=[[old, run1("check", "completed", "success", 23, so)]], compare=cmp
    )
    r = lane.run(1, "post-merge", "7", H, "--lane", "gh7", "--wait", "0")
    want = (
        f"step 2 main CI: stopped: main CI red on {m12}: check cancelled "
        "https://github.com/o/r/actions/runs/21, and no later push run of check on main "
        f"containing {m12} within 0s; check main's runs (gh run list --branch), then rerun"
    )
    assert want in r.out.split("\n"), f"no superseding run: {r.out}"
    lane.store(
        lists=[[gone, run1("lint", "completed", "failure", 12, m)]],
        base=[[run1("check", "completed", "success", 22, sn)]],
        compare=cmp,
    )
    r = lane.run(1, "post-merge", "7", H, "--lane", "gh7", "--wait", "0")
    want = (
        f"step 2 main CI: stopped: main CI red on {m12}: lint failure "
        "https://github.com/o/r/actions/runs/12;"
    )
    assert want in r.out, f"red beside cancelled: {r.out}"
    assert not [x for x in s.gh.log() if "--branch" in x], f"red beside cancelled: {s.gh.log()}"


def kit_refresh(s: Scratch) -> None:
    """Step 3, the PR's repo the install's (o/r). Behind: fetch, fast-forward to M, still detached;
    no mise.toml at M, so no mise; each refresh command runs in the install, install-check for the
    target repo. Rerun: no move, the refresh commands run again. Past M, with a mise.toml there:
    no move, the kit's own locked tools installed first (octo-feather-mise-install, #493 AC5). A
    failing refresh command stops naming it, later ones not run. The pinned Python absent: uv
    sync never downloads it, and the stop names the install command for the pin."""
    import shutil  # noqa: PLC0415 (lazy: the other scenarios' start does not pay it)

    assert shutil.which("uv"), "no uv: the failing refresh cases need it"
    lane = Lane(s)
    lane.homes = tool_homes()
    m, b, k, t = lane.m, lane.b, lane.kit, lane.target
    b12, m12 = b[:12], m[:12]
    green = run1("check", "completed", "success", 11, m)
    refresh = [
        ["just", str(k), "vendored-fetch"],
        ["uv", str(k), "sync", "--locked"],
        ["pnpm", str(k), "install", "--frozen-lockfile"],
        ["just", str(k), "install-check", str(t)],
    ]
    ff = f"kit install {k} fast-forwarded {b12}..{m12}; just vendored-fetch ok; "
    stop3 = "step 3 kit refresh: stopped: "
    lane.store(lists=[[green], [green], [green], [green]])  # behind, rerun, past, failing uv
    lane.install(b)
    r = lane.run(3, "post-merge", "7", H, "--lane", "gh7")
    says(
        r,
        "behind",
        f"step 3 kit refresh: ok: {ff}uv sync --locked ok; pnpm install --frozen-lockfile ok; "
        f"just install-check {t} ok (no mise.toml: mise install skipped)",
        summary=GREEN,
    )
    assert (lane.head(), lane.calls()) == (m, refresh), f"behind: {lane.calls()}"
    attached = s.run(["git", "-C", str(k), "symbolic-ref", "-q", "HEAD"], want=1)
    assert attached.out == "", "behind install left detached HEAD"
    lane.argv.unlink()
    r = lane.run(3, "post-merge", "7", H, "--lane", "gh7")
    no_move = f"step 3 kit refresh: ok: kit install {k} at {{}}, at or past {m12}: no move; "
    says(r, "rerun", no_move.format(m12) + "just vendored-fetch ok")
    assert (lane.head(), lane.calls()) == (m, refresh), f"rerun: {lane.calls()}"
    # The user's global mise config (MISE_CONFIG_DIR, a scratch one) requests a tool P's
    # mise.lock lacks: a bare `mise install --locked` fails on it, so ok shows only the install's
    # own tools were installed.
    user = s.root / "mise-config"
    user.mkdir()
    (user / "config.toml").write_text('[tools]\nnode = "4.0.0"\n')
    s.env["MISE_CONFIG_DIR"] = str(user)
    lane.install(lane.p)
    r = lane.run(3, "post-merge", "7", H, "--lane", "gh7")
    mise = "octo-feather-mise-install . ok; just vendored-fetch ok"
    says(r, "past", no_move.format(lane.p[:12]) + mise)
    assert (lane.head(), lane.calls()) == (lane.p, refresh), f"past: {lane.calls()}"
    # the real uv: M's pyproject has no uv.lock, so `uv sync --locked` fails
    lane.install(b)
    r = lane.run(1, "post-merge", "7", H, "--lane", "gh7", tools="real-uv")
    uv = "uv sync --locked failed (exit {}: error: {}"
    says(
        r,
        "failing tool",
        stop3 + ff + uv.format(1, "Unable to find lockfile at `uv.lock`, but `--locked` was "),
        f"): fix it in {k}, then rerun",
        summary=STOP3,
    )
    assert lane.calls() == refresh[:1], f"failing tool ran on: {lane.calls()}"
    # the real uv, M2's pin absent, downloads off
    lane.merge = lane.m2
    lane.store(lists=[[run1("check", "completed", "success", 11, lane.m2)]])
    lane.install(b)
    r = lane.run(1, "post-merge", "7", H, "--lane", "gh7", tools="real-uv")
    says(
        r,
        "missing pin",
        f"{stop3}kit install {k} fast-forwarded {b12}..{lane.m2[:12]}; just vendored-fetch ok; "
        + uv.format(2, f"No interpreter found for Python {NO_PIN} in managed installations or ")
        + f"search path): the kit's pinned Python {NO_PIN} (.python-version) is not installed "
        f"and post-merge never downloads one: run `uv python install --no-bin {NO_PIN}` in {k}, "
        "then rerun",
        summary=STOP3,
    )
    assert lane.calls() == refresh[:1], f"missing pin ran on: {lane.calls()}"
    assert not (k / ".venv").exists(), "missing pin: uv made a venv (a Python downloaded)"


def install_stops(s: Scratch) -> None:
    """Step 3 on a dirty or diverged install: stop naming it, nothing changed (HEAD, the file, no
    refresh)."""
    lane = Lane(s)
    m12, b, k = lane.m[:12], lane.b, lane.kit
    stop3 = "step 3 kit refresh: stopped: "
    green = run1("check", "completed", "success", 11, lane.m)
    lane.store(lists=[[green], [green]])  # dirty, then diverged
    lane.install(b)
    (k / "stray").write_text("x\n")
    r = lane.run(1, "post-merge", "7", H, "--lane", "gh7")
    says(r, "dirty", f"{stop3}kit install {k} is dirty (?? stray)", summary=STOP3)
    assert (lane.head(), lane.calls()) == (b, []), f"dirty install changed: {lane.calls()}"
    assert (k / "stray").is_file(), "dirty install lost its file"
    lane.install(b)
    (k / "d").write_text("")
    s.git(k, "add", "d")
    s.git(k, "commit", "-qm", "d")
    d = lane.head()
    r = lane.run(1, "post-merge", "7", H, "--lane", "gh7")
    diverged = f"kit install {k} at {d[:12]} has diverged from merge commit {m12}"
    says(r, "diverged", stop3 + diverged, summary=STOP3)
    assert (lane.head(), lane.calls()) == (d, []), f"diverged install changed: {lane.calls()}"


if __name__ == "__main__":
    main(merged_step, main_ci, no_ci, superseded, kit_refresh, install_stops)
