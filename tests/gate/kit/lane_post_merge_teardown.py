"""The scenarios of tests/gate/kit/test_lane_post_merge_teardown.py (its items), this file their
command (testkit.main): octo-feather-lane post-merge step 5, teardown (owner ruling 2026-10-29 on
issue 206; issue 399), offline: a throwaway target repo with a bare origin holds lane branch gh12,
its worktree and its merge commit; the testkit's fake gh holds PR #12 merged there with a green
push run and PR #13 based on gh12; the testkit's fake herdr (its FAKE_HERDR agents world) stands
for Herdr under the kit's own herdr-close and herdr-say (HERDR_SESSION unset; space ids no real
Herdr gives, so herdr-close's sweep of tagged processes can match none); a throwaway mise state
dir (MISE_STATE_DIR); a throwaway state dir (XDG_STATE_HOME) holds the lane records,
director.toml and the Spec Chat registries; a throwaway kit install clone (OCTO_FEATHER_KIT_INSTALL,
never the live kit) of another repo, so step 3 leaves it unchanged. Not archived: steps 1-4 run,
step 5 pending, exit 3. Archived: the lane's own space is closed (only its supervisor pane's tab
when shared), its worktree removed and the mise links into it pruned (one into the live repo
kept), PRs based on its branch retargeted before the remote branch is deleted, the local branch
deleted; a rerun prints already for each, on a repo with no workflow as with a green run. A dirty
worktree, the kit install, the main worktree and a review row's root are kept, exit 1.

The world (target repo, origin, worktree, kit install) is prepared once per gate run (testkit
Scratch.prepare); each case is a fresh copy of it, its worktree links rewritten.
"""

from __future__ import annotations

import json
import os
import subprocess
from typing import TYPE_CHECKING

from testkit import ROOT, Ran, Scratch, kit, main

if TYPE_CHECKING:
    from pathlib import Path

ASSETS = ROOT / ".agents" / "skills" / "herdr-comms" / "assets"  # herdr-close, herdr-say
S4 = (
    "post-merge gh12 PR #12: step 1 merged ok; step 2 main CI ok; step 3 kit refresh ok; step 4 "
    "tell supervisors ok"
)
ALREADY = (
    "worktree of gh12 already removed; no open PR based on gh12; local branch gh12 already "
    "deleted; remote branch gh12 already deleted from origin"
)


def build(p: Scratch) -> None:
    """r (main merged gh12 at M, worktree wt on gh12), its bare origin, the kit install of o/kit."""
    t, r = p.root, p.root / "r"
    p.run(["git", "init", "-q", "--bare", "-b", "main", str(t / "origin.git")])
    p.git(t, "init", "-q", "-b", "main", str(r))
    p.git(r, "remote", "add", "origin", str(t / "origin.git"))
    (r / "a").write_text("a\n")
    p.git(r, "add", "a")
    p.git(r, "commit", "-qm", "base")
    p.git(r, "checkout", "-qb", "gh12")
    (r / "b").write_text("b\n")
    p.git(r, "add", "b")
    p.git(r, "commit", "-qm", "lane")
    p.git(r, "checkout", "-q", "main")
    p.git(r, "merge", "-q", "--no-ff", "gh12", "-m", "Merge #12")
    p.git(r, "push", "-q", "origin", "main", "gh12")
    p.git(r, "worktree", "add", "-q", str(t / "wt"), "gh12")
    p.run(["git", "clone", "-q", str(r), str(t / "kit")])
    p.git(t / "kit", "remote", "set-url", "origin", "https://github.com/o/kit.git")


class World:
    """One case's fresh world under S/NAME: its own Scratch (HOME, fakes, gh store)."""

    def __init__(self, s: Scratch, name: str) -> None:
        root = s.root / name
        root.mkdir()
        w = Scratch(root)
        w.prepare("lane-post-merge-teardown", build)
        self.s, self.t = w, root
        self.r, self.wt, self.origin = root / "r", root / "wt", root / "origin.git"
        # the copy's worktree links, both ways (git's own layout: gitworktree(7), DETAILS)
        (self.r / ".git" / "worktrees" / "wt" / "gitdir").write_text(f"{self.wt}/.git\n")
        (self.wt / ".git").write_text(f"gitdir: {self.r}/.git/worktrees/wt\n")
        w.git(self.r, "remote", "set-url", "origin", str(self.origin))
        self.h = w.git(self.r, "rev-parse", "gh12")
        self.m = w.git(self.r, "rev-parse", "main")
        self.state = root / "state"
        self.lanes = self.state / "octo-feather" / "lanes"
        self.reg = self.state / "spec-chat" / "hosting" / "s1"
        (self.lanes / "archive").mkdir(parents=True)
        self.reg.mkdir(parents=True)
        (self.state / "octo-feather" / "director.toml").write_text('pane = "zt1:p1"\n')
        (self.reg / "registry.toml").write_text(
            f'[[resource]]\nslug = "s"\nspec = "docs/s.spec.html"\nroot = "{self.r}"\n'
        )
        herdr = root / "herdr"
        herdr.mkdir()
        self.herdr = herdr
        self.agents(["zt1:p1", "zt5:p1", "zt6:p1"])
        for k in [k for k in w.env if k.startswith(("HERDR_", "OCTO_FEATHER_", "GH_REPO"))]:
            del w.env[k]
        w.env |= {
            "FAKE_HERDR": str(herdr),
            "XDG_STATE_HOME": str(self.state),
            "OCTO_FEATHER_KIT_INSTALL": str(root / "kit"),
            "MISE_STATE_DIR": str(root / "mise"),
            "PATH": f"{w.bin}{os.pathsep}{ASSETS}{os.pathsep}{w.env['PATH']}",
        }
        g = w.gh
        g.put(
            12,
            {
                "number": 12,
                "state": "MERGED",
                "headRefOid": self.h,
                "mergeCommit": {"oid": self.m},
                "baseRefName": "main",
                "headRefName": "gh12",
                "title": "Lane 12",
                "url": "https://github.com/o/r/pull/12",
            },
        )
        g.put(13, {"number": 13, "state": "OPEN", "baseRefName": "gh12", "headRefName": "gh13"})
        g.store("repo.json", {"nameWithOwner": "o/r"})
        g.store("api/repos/o/kit.json", {"nameWithOwner": "o/kit"})
        g.store(
            "run/1.json",
            {
                "databaseId": 1,
                "status": "completed",
                "conclusion": "success",
                "workflowName": "check",
                "url": "https://github.com/o/r/actions/runs/1",
            },
        )

    def agents(self, panes: list[str]) -> None:
        """Herdr's agents: one per pane, each in its own tab, idle."""
        world = {}
        for p in panes:
            space, n = p.split(":p")
            world[p] = {
                "name": f"a-{space}-{n}",
                "pane_id": p,
                "workspace_id": space,
                "tab_id": f"{space}:t{n}",
                "agent_status": "idle",
            }
        (self.herdr / "agents.json").write_text(json.dumps(world))

    def herdr_log(self) -> list[str]:
        p = self.herdr / "log"
        return p.read_text().splitlines() if p.exists() else []

    def closes(self) -> list[str]:
        """The tabs and spaces Herdr was asked to close."""
        return [x for x in self.herdr_log() if x.startswith(("tab close", "workspace close"))]

    def lane(self, path: Path, pane: str, pr: int) -> None:
        """A lane record of issue 12 at PATH."""
        path.write_text(
            f'supervisor = "{pane}"\nrepository = "o/r"\nissue = 12\npr = {pr}\ngoal = "g"\n'
            'started_at = "2026-10-29T00:00:00Z"\n'
        )

    def archived(self, pane: str = "zt5:p1", pr: int = 12) -> None:
        self.lane(self.lanes / "archive" / "gh12.toml", pane, pr)

    def run(self, want: int, **env: str) -> tuple[Ran, str]:
        """post-merge 12 H --lane gh12 from the target repo; its run and step 5 line."""
        cmd = [kit("octo-feather-lane"), "post-merge", "12", self.h, "--lane", "gh12"]
        r = self.s.run([*cmd, "--repo", "o/r", "--wait", "0"], want=want, cwd=self.r, env=env)
        s5 = next((x for x in r.out.split("\n") if x.startswith("step 5 teardown: ")), "")
        assert s5, f"no step 5 line: {r.out}"
        return r, s5

    def last(self, r: Ran) -> str:
        return r.out.split("\n")[-1]

    def branch_on(self, where: Path, *, bare: bool = False) -> bool:
        """Whether branch gh12 is in the repo WHERE (BARE: a bare repo's git dir)."""
        flag = "--git-dir" if bare else "-C"
        cmd = ["git", flag, str(where), "rev-parse", "-q", "--verify", "refs/heads/gh12"]
        return subprocess.run(cmd, capture_output=True, check=False).returncode == 0

    def kept(self, what: str) -> None:
        """What step 5 must not have touched: the worktree, the local and remote branch."""
        ok = self.wt.is_dir() and self.branch_on(self.r) and self.branch_on(self.origin, bare=True)
        assert ok, f"{what}: worktree or branch gone"


def not_archived(s: Scratch) -> None:
    """Not archived (the record still open): steps 1-4 run, step 5 pending, exit 3, nothing
    closed or removed. Archived naming another PR: stopped, nothing torn down."""
    w = World(s, "pending")
    w.lane(w.lanes / "gh12.toml", "zt5:p1", 12)
    r, s5 = w.run(3)
    assert s5 == "step 5 teardown: pending: lane gh12 not archived; rerun on its close report", s5
    assert w.last(r) == f"{S4}; step 5 teardown pending", f"pending: {r.out}"
    assert not w.closes(), f"pending closed: {w.closes()}"
    w.kept("pending")
    w = World(s, "other-pr")
    w.archived(pr=99)
    r, s5 = w.run(1)
    assert s5.startswith("step 5 teardown: stopped: archived lane gh12 names PR #99, not #12"), s5
    assert w.last(r) == f"{S4}; step 5 teardown stopped", f"other pr: {r.out}"
    assert not w.closes(), f"other pr closed: {w.closes()}"
    w.kept("other pr")


def own_space(s: Scratch) -> None:
    """Archived, its own space: the space closed (herdr-close zt5), the worktree removed and the
    mise links into it pruned (the one into the live repo kept), #13 retargeted while gh12 is
    still on origin (a failed retarget stops with gh12 still there), then the local and remote
    branch deleted; exit 0. A rerun prints already for each and changes nothing."""
    w = World(s, "own")
    w.archived()
    w.lane(w.lanes / "other.toml", "zt6:p1", 14)
    mise = w.t / "mise"
    for d, name, target in (
        ("tracked-configs", "r", w.r / "mise.toml"),
        ("tracked-configs", "wt", w.wt / "mise.toml"),
        ("trusted-configs", "wt", w.wt),
    ):
        (mise / d).mkdir(parents=True, exist_ok=True)
        (mise / d / name).symlink_to(target)
    # the retarget fails once: step 5 stops there, gh12 still on origin (retarget before delete)
    w.s.gh.tape({"pr edit 13 --base main -R o/r": [{"err": "HTTP 502\n", "exit": 1}]})
    r, s5 = w.run(1)
    assert "retarget PR #13 to main by hand" in s5, f"failed retarget: {s5}"
    assert w.branch_on(w.origin, bare=True), "the remote branch was deleted before the retarget"
    w.s.gh.tape({})
    w.agents(["zt1:p1", "zt5:p1", "zt6:p1"])
    w.s.git(w.r, "worktree", "add", "-q", str(w.wt), "gh12")
    (mise / "tracked-configs" / "wt").unlink(missing_ok=True)
    (mise / "tracked-configs" / "wt").symlink_to(w.wt / "mise.toml")
    (mise / "trusted-configs" / "wt").unlink(missing_ok=True)
    (mise / "trusted-configs" / "wt").symlink_to(w.wt)
    (w.herdr / "log").unlink()
    r, s5 = w.run(0)
    links = sorted(str(x.relative_to(mise)) for x in mise.rglob("*") if x.is_symlink())
    assert links == ["tracked-configs/r"], f"mise links: {links}"
    assert w.closes() == ["workspace close zt5"], f"own space: closed {w.closes()}"
    assert s5 == (
        f"step 5 teardown: ok: space zt5 closed; worktree {w.wt} removed (2 mise config links "
        "into it pruned); PR #13 retargeted from gh12 to main; local branch gh12 deleted; remote "
        "branch gh12 deleted from origin"
    ), f"teardown line: {s5}"
    assert w.last(r) == f"{S4}; step 5 teardown ok", f"teardown: {r.out}"
    assert not w.wt.is_dir(), "worktree kept"
    assert not w.branch_on(w.r), "local branch kept"
    assert not w.branch_on(w.origin, bare=True), "remote branch kept"
    assert "pr edit 13 --base main -R o/r" in w.s.gh.log(), f"no retarget: {w.s.gh.log()}"
    r, s5 = w.run(0)
    assert s5 == f"step 5 teardown: ok: space zt5 already closed; {ALREADY}", f"rerun: {s5}"


def no_ci(s: Scratch) -> None:
    """The no-CI fact (rule: octo-feather-lane --help, post-merge step 2; exosurface, gh33): the
    same teardown runs; a rerun prints already for each."""
    w = World(s, "no-ci")
    w.archived()
    (w.s.gh.dir / "run" / "1.json").unlink()
    m = w.m
    w.s.gh.store(
        f"api/repos/o/r/git/trees/{m}.json",
        {"sha": m, "tree": [{"path": "a", "type": "blob", "sha": "x"}]},
    )
    r, s5 = w.run(0)
    noci = (
        f"step 2 main CI: ok: no CI: no workflow file under .github/workflows at merge commit "
        f"{m[:12]} (gh api repos/o/r/git/trees/{m[:12]}), so no push run can appear; nothing to "
        "wait for"
    )
    assert noci in r.out.split("\n"), f"no CI step 2: {r.out}"
    assert s5 == (
        f"step 5 teardown: ok: space zt5 closed; worktree {w.wt} removed (0 mise config links "
        "into it pruned); PR #13 retargeted from gh12 to main; local branch gh12 deleted; remote "
        "branch gh12 deleted from origin"
    ), f"no CI teardown: {s5}"
    assert w.last(r) == f"{S4}; step 5 teardown ok", f"no CI teardown: {r.out}"
    assert f"api repos/o/r/git/trees/{m}" in w.s.gh.log(), f"no CI fact not read: {w.s.gh.log()}"
    r, s5 = w.run(0)
    assert s5 == f"step 5 teardown: ok: space zt5 already closed; {ALREADY}", f"no CI rerun: {s5}"
    assert w.last(r) == f"{S4}; step 5 teardown ok", f"no CI rerun: {r.out}"


def shared_space(s: Scratch) -> None:
    """Shared space: another open lane's supervisor, or the director's pane, has the prefix: only
    the supervisor's tab closed (herdr-close of its pane), never the space; a rerun says already."""
    w = World(s, "shared")
    w.archived("zt6:p1")
    w.lane(w.lanes / "other.toml", "zt6:p3", 14)
    _, s5 = w.run(0)
    assert w.closes() == ["tab close zt6:t1"], f"shared lane: {w.closes()}"
    assert s5.startswith("step 5 teardown: ok: tab of zt6:p1 closed in shared space zt6; "), s5
    _, s5 = w.run(0)
    assert s5.startswith("step 5 teardown: ok: tab of zt6:p1 already closed; "), f"shared: {s5}"
    assert w.closes() == ["tab close zt6:t1"], f"shared rerun closed again: {w.closes()}"
    w = World(s, "director")
    w.archived("zt1:p2")
    w.agents(["zt1:p1", "zt1:p2", "zt5:p1", "zt6:p1"])
    w.run(0)
    assert w.closes() == ["tab close zt1:t2"], f"director's space: closed {w.closes()}"


def kept(s: Scratch) -> None:
    """Refused and kept, exit 1, nothing retargeted: a dirty worktree (git's words), a review
    row's root, the kit install, the main worktree; a local branch past the merge commit."""

    def refused(w: World, what: str, want: str, **env: str) -> str:
        r, s5 = w.run(1, **env)
        assert s5.startswith("step 5 teardown: stopped: "), f"{what}: {s5}"
        assert want in s5, f"{what}: {s5}"
        assert w.last(r) == f"{S4}; step 5 teardown stopped", f"{what}: {r.out}"
        assert not [x for x in w.s.gh.log() if x.startswith("pr edit")], f"{what} retargeted"
        w.kept(what)
        return s5

    w = World(s, "dirty")
    w.archived()
    (w.wt / "stray").write_text("x\n")
    refused(
        w,
        "dirty",
        f"worktree {w.wt} not removed (fatal: '{w.wt}' contains modified or untracked files, use "
        "--force to delete it)",
    )
    w = World(s, "review")
    w.archived()
    (w.reg / "registry.toml").write_text(
        f'[[resource]]\nslug = "s"\nspec = "docs/s.spec.html"\nroot = "{w.wt}"\n'
    )
    want = (
        f"worktree {w.wt} kept: it is the root of Spec Chat review row s in {w.reg}/registry.toml"
    )
    refused(w, "review root", want)
    w = World(s, "install")
    w.archived()
    # the worktree as the install: its origin (r's) another GitHub repo, so step 3 leaves it
    other = "https://github.com/o/other.git"
    w.s.git(w.r, "remote", "set-url", "origin", other)
    w.s.git(w.r, "config", f"url.{w.origin}.insteadOf", other)
    w.s.gh.store("api/repos/o/other.json", {"nameWithOwner": "o/other"})
    want = f"worktree {w.wt} kept: it is the kit install"
    refused(w, "kit install", want, OCTO_FEATHER_KIT_INSTALL=str(w.wt))
    w = World(s, "main-wt")
    w.archived()
    w.s.git(w.r, "worktree", "remove", str(w.wt))
    w.s.git(w.r, "checkout", "-q", "gh12")
    w.wt.mkdir()
    refused(w, "main worktree", f"worktree {w.r} kept: it is the main worktree")
    w = World(s, "unmerged")
    w.archived()
    w.s.git(w.wt, "commit", "-q", "--allow-empty", "-m", "later")
    w.s.git(w.r, "worktree", "remove", str(w.wt))
    w.wt.mkdir()
    _, s5 = w.run(1)
    want = f"local branch gh12 kept: it is not an ancestor of merge commit {w.m[:12]}"
    assert s5.startswith("step 5 teardown: stopped: "), f"unmerged: {s5}"
    assert want in s5, f"unmerged: {s5}"
    w.kept("unmerged")


if __name__ == "__main__":
    main(not_archived, own_space, no_ci, shared_space, kept)
