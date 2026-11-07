"""The scenario of tests/gate/kit/test_spec_chat_install.py (its item), this file its command
(testkit.main): `just spec-chat REPO` (scripts/octo-feather-spec-chat), offline, over a Spec Chat
clone whose installer is the testkit's stand-in (testkit.spec_chat_clone: it records its argv and
links skills like the real one). Links land in REPO/.agents/skills, ignored in info/exclude once,
nothing under HOME, no provider dirs; a rerun adds nothing. A subdir REPO is refused naming its
top, the installer not run; a linked worktree top is accepted; a non-git REPO, a missing clone and
an absent default clone (~/src/spec-chat) each fail naming the fix."""

from __future__ import annotations

import re
import subprocess
from collections.abc import Callable
from typing import TYPE_CHECKING

from testkit import ROOT, Scratch, main, spec_chat_clone, tool_homes

if TYPE_CHECKING:
    from pathlib import Path

TAG = "spec-chat-install test"
Run = Callable[..., tuple[int, str]]
LINKS = ("spec-chat-shape", "spec-chat-review", "repair-specs")


def install(s: Scratch) -> None:
    t = s.root.resolve()
    s.env["XDG_STATE_HOME"] = str(t / "state")
    s.env |= tool_homes()  # mise's own installs and caches, never the scratch HOME's
    clone = spec_chat_clone(t / "clone")
    repo = t / "work" / "repo"
    repo.mkdir(parents=True)
    s.git(repo, "-c", "init.defaultBranch=main", "init", "-q")
    # A committed link elsewhere is the repo's own: never ignored.
    (repo / ".agents" / "skills").mkdir(parents=True)
    (repo / ".agents" / "skills" / "own").symlink_to("/tmp")  # noqa: S108
    s.git(repo, "add", "-A")
    s.git(repo, "commit", "-qm", "init")

    def run(target: str, clone_dir: str | None = str(clone)) -> tuple[int, str]:
        env = {k: v for k, v in s.env.items() if k != "SPEC_CHAT_CLONE"}
        if clone_dir is not None:
            env["SPEC_CHAT_CLONE"] = clone_dir
        p = subprocess.run(
            ["just", "--justfile", str(ROOT / "justfile"), "spec-chat", target],  # noqa: S607
            cwd=t / "work",
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        return p.returncode, p.stdout

    for i in (1, 2):
        rc, out = run("repo")
        assert rc == 0, f"{TAG}: run {i} failed: {out}"
        assert f"fake installer: linked into {repo}" in out, f"{TAG}: installer output lost: {out}"
    argv = (clone / "argv").read_text()
    assert argv == f"--agents-only\n--prefix\n{repo}\n", f"{TAG}: installer argv: {argv!r}"
    for name in LINKS:
        link = repo / ".agents" / "skills" / name
        assert link.is_symlink(), f"{TAG}: missing link {name}"
        assert (link / "SKILL.md").is_file(), f"{TAG}: link {name} reaches no SKILL.md"
    status = s.git(repo, "status", "--porcelain")
    assert status == "", f"{TAG}: git status not clean: {status}"
    excl = (repo / ".git" / "info" / "exclude").read_text().splitlines()
    for name in LINKS:
        n = excl.count(f"/.agents/skills/{name}")
        assert n == 1, f"{TAG}: exclude line for {name} {n} times, want once"
    assert not any("skills/own" in ln for ln in excl), f"{TAG}: repo's own link was ignored"
    home = list(s.home.rglob("*"))
    assert not home, f"{TAG}: created under HOME: {home}"
    # No provider link dirs: the repo top holds only what it had.
    top = sorted(p.name for p in repo.iterdir())
    assert top == [".agents", ".git"], f"{TAG}: repo top changed: {top}"

    refusals(s, run, clone, repo)


def refusals(s: Scratch, run: Run, clone: Path, repo: Path) -> None:
    t = s.root.resolve()
    (clone / "argv").unlink()
    (repo / "sub").mkdir()
    rc, out = run("repo/sub")
    assert rc != 0, f"{TAG}: subdir REPO succeeded: {out}"
    top_named = re.search(rf"pass {re.escape(str(repo))}$", out, re.MULTILINE)
    assert top_named, f"{TAG}: subdir error does not name the top: {out}"
    assert not (clone / "argv").exists(), f"{TAG}: installer ran for a subdir REPO"
    assert not list((repo / "sub").iterdir()), f"{TAG}: created in subdir"

    # A linked worktree top is a checkout top: accepted, its links ignored too.
    wt = t / "work" / "wt"
    s.git(repo, "worktree", "add", "-q", str(wt), "-b", "wt")
    rc, out = run("wt")
    assert rc == 0, f"{TAG}: linked worktree failed: {out}"
    assert (wt / ".agents" / "skills" / "spec-chat-shape").is_symlink(), f"{TAG}: no link in wt"
    status = s.git(wt, "status", "--porcelain")
    assert status == "", f"{TAG}: worktree status not clean: {status}"

    (t / "work" / "plain").mkdir()
    rc, out = run("plain")
    assert rc != 0, f"{TAG}: non-git REPO succeeded: {out}"
    assert "git init" in out, f"{TAG}: non-git error names no fix: {out}"
    rc, out = run("repo", str(t / "nope"))
    assert rc != 0, f"{TAG}: missing clone succeeded: {out}"
    assert "SPEC_CHAT_CLONE" in out, f"{TAG}: missing-clone error names no fix: {out}"
    rc, out = run("repo", None)
    assert rc != 0, f"{TAG}: default clone absent but succeeded: {out}"
    assert f"{s.home}/src/spec-chat" in out, f"{TAG}: default clone not ~/src/spec-chat: {out}"


if __name__ == "__main__":
    main(install)
