"""The kit's git hook stays off the factory (quality #acceptance-setup-not-factory,
#acceptance-hook-machine-commit; #1243), in a throwaway git copy of the kit
(tests/gate/kit/gate_recipes_first.py's: its fast tier's static checks check-dashes and check-probe,
check-probe logging to PROBE) with a linked worktree, as a factory clone holds, never this
checkout, whose git config every lane shares. Neither scenario runs the fast tier.

refused: `just setup` as an implementer in the worktree (lane gh1224's run of 2026-11-23), then
with no role in the worktree, then with no role in the copy's main checkout: each exits non-zero
naming why and saying the hook is for a maintainer's own clone; the clone's git config is the same
after as before, core.hooksPath unset.
skipped: with core.hooksPath set by hand, an em dash staged (a red static check, so a fast tier run
would refuse), commits as supervisor, director and shaper, and a conflicted merge, cherry-pick and
revert each finished with `git commit` as an implementer, each go through, saying why the hook
skipped (the role, MERGE_HEAD, CHERRY_PICK_HEAD, REVERT_HEAD), PROBE empty. An implementer's
red commit runs the fast tier and is refused: tests/gate/kit/fast_hook.py red implementer.
template LANG: a repo of templates/LANG's tracked files, its hook on, a recording `just` first on
PATH exiting 1 (a red fast tier), as scripts/check-templates runs a template's hook: an
implementer's commit calls `just fast` once and is refused; a supervisor's, and a conflicted merge
finished as an implementer, go through, saying why, `just` never called.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from typing import TYPE_CHECKING

from fast_hook import GIT, copy_run
from gate_recipes_first import DASH, kit_copy
from testkit import ROOT, Ran, Scratch, main

if TYPE_CHECKING:
    from pathlib import Path

FOR = "for a maintainer's own clone"
RECORDER = '#!/bin/sh\necho "$*" >> "$JUST_CALLS"\nexit 1\n'


def clone(s: Scratch) -> tuple[Path, Path]:
    """The kit copy and its linked worktree on branch gh1."""
    (s.root / "user-mise").mkdir()
    k = kit_copy(s)
    w = s.root / "wt"
    s.git(k, "worktree", "add", "-q", "-b", "gh1", str(w))
    return k, w


def config(s: Scratch, k: Path) -> str:
    return s.git(k, "config", "--local", "--list")


def refused(s: Scratch) -> None:
    k, w = clone(s)
    before = config(s, k)
    for where, role, why in (
        (w, "implementer", "OCTO_FEATHER_ROLE=implementer"),
        (w, None, "worktrees besides its main one"),
        (k, None, "worktrees besides its main one"),
    ):
        ran, _ = copy_run(s, where, "just", "setup", role=role)
        said = f"just setup in {where.name}, role {role}: exit {ran.rc}\n{ran.out}"
        assert ran.rc != 0, said
        assert why in ran.out, f"want {why!r}: {said}"
        assert FOR in ran.out, said
        assert config(s, k) == before, f"want git config unchanged: {said}"
        assert "core.hookspath" not in config(s, k).lower(), said


def skipped(s: Scratch) -> None:
    k, w = clone(s)
    s.git(k, "config", "core.hooksPath", ".githooks")
    red = w / "hook-red.txt"
    for role in ("supervisor", "director", "shaper"):
        red.write_text(f"{role} {DASH}\n")
        s.git(w, "add", red.name)
        ran, probe = copy_run(s, w, *GIT, "commit", "-m", role, role=role)
        said = f"git commit as {role}: exit {ran.rc}\nprobe: {probe}\n{ran.out}"
        assert ran.rc == 0, said
        assert f"skipped: OCTO_FEATHER_ROLE={role}" in ran.out, said
        assert probe == [], f"want no fast tier run: {said}"
        assert s.git(w, "log", "-1", "--format=%s") == role, said
    first = s.git(w, "rev-list", "--max-parents=1", "-3", "HEAD").split()[-1]  # supervisor's
    for branch in ("main", "pick"):  # each changes RED from main's side: conflicts with gh1
        s.git(k, "switch", "-q", "-C", branch)
        (k / red.name).write_text(f"{branch} {DASH}\n")
        s.git(k, "add", red.name)
        s.git(k, "-c", "core.hooksPath=/dev/null", "commit", "-qm", branch)  # setup, not a case
    s.git(k, "switch", "-q", "main")
    for op, head in (
        ("merge main", "MERGE_HEAD"),
        ("cherry-pick pick", "CHERRY_PICK_HEAD"),
        (f"revert --no-edit {first}", "REVERT_HEAD"),
    ):
        started, _ = copy_run(s, w, *GIT, *op.split(), role="implementer")
        assert started.rc != 0, f"want a conflict from {op}: {started.out}"
        red.write_text(f"{head} {DASH}\n")
        s.git(w, "add", red.name)
        ran, probe = copy_run(s, w, *GIT, "commit", "--no-edit", role="implementer")
        said = f"git commit, {op} in progress: exit {ran.rc}\nprobe: {probe}\n{ran.out}"
        assert ran.rc == 0, said
        assert f"skipped: {head}" in ran.out, said
        assert probe == [], f"want no fast tier run: {said}"
        assert s.git(w, "status", "--porcelain") == "", f"want the commit made: {said}"


def template(s: Scratch, lang: str) -> None:
    src, r, calls = ROOT / "templates" / lang, s.root / lang, s.root / "just-calls"
    for f in filter(None, s.git(src, "ls-files", "-z").split("\0")):
        (r / f).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src / f, r / f, follow_symlinks=False)
    (s.root / "rec").mkdir()
    (s.root / "rec" / "just").write_text(RECORDER)
    (s.root / "rec" / "just").chmod(0o755)
    nohook = ("-c", "core.hooksPath=/dev/null")
    s.git(r, "init", "-q", "-b", "main")
    s.git(r, "add", "-A")
    s.git(r, *nohook, "commit", "-qm", "template")
    s.git(r, "branch", "other")
    s.git(r, "config", "core.hooksPath", ".githooks")
    env = {k: v for k, v in s.env.items() if k != "OCTO_FEATHER_ROLE"}
    env |= {"PATH": f"{s.root / 'rec'}{os.pathsep}{env['PATH']}", "JUST_CALLS": str(calls)}

    def commit(role: str, *args: str) -> tuple[Ran, list[str]]:
        calls.write_text("")
        p = subprocess.run(
            [*GIT, "commit", *args],
            cwd=r,
            env=env | {"OCTO_FEATHER_ROLE": role},
            capture_output=True,
            text=True,
            check=False,
        )
        return Ran(p.returncode, p.stdout + p.stderr, ""), calls.read_text().splitlines()

    (r / "note.txt").write_text("main\n")
    s.git(r, "add", "note.txt")
    ran, called = commit("implementer", "-m", "writer")
    said = f"{lang}, implementer: exit {ran.rc}, just calls {called}\n{ran.out}"
    assert ran.rc != 0, f"want the red fast tier to refuse: {said}"
    assert called == ["fast"], said
    ran, called = commit("supervisor", "-m", "machine")
    said = f"{lang}, supervisor: exit {ran.rc}, just calls {called}\n{ran.out}"
    assert ran.rc == 0, said
    assert "skipped: OCTO_FEATHER_ROLE=supervisor" in ran.out, said
    assert called == [], said
    s.git(r, "switch", "-q", "other")
    (r / "note.txt").write_text("other\n")
    s.git(r, "add", "note.txt")
    s.git(r, *nohook, "commit", "-qm", "other")
    s.git(r, "switch", "-q", "main")
    s.run([*GIT, "-C", str(r), "merge", "other"], want=1)
    (r / "note.txt").write_text("merged\n")
    s.git(r, "add", "note.txt")
    ran, called = commit("implementer", "--no-edit")
    said = f"{lang}, merge in progress: exit {ran.rc}, just calls {called}\n{ran.out}"
    assert ran.rc == 0, said
    assert "skipped: MERGE_HEAD" in ran.out, said
    assert called == [], said


if __name__ == "__main__":
    main(refused, skipped, template)
