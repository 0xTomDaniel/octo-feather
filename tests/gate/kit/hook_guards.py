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
would refuse), commits as supervisor, director and shaper, and a conflicted merge finished with
`git commit` as an implementer, each go through, saying why the hook skipped, PROBE empty.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fast_hook import GIT, copy_run
from gate_recipes_first import DASH, kit_copy
from testkit import Scratch, main

if TYPE_CHECKING:
    from pathlib import Path

FOR = "for a maintainer's own clone"


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
    (k / red.name).write_text(f"main {DASH}\n")
    s.git(k, "add", red.name)
    s.git(k, "-c", "core.hooksPath=/dev/null", "commit", "-qm", "main")  # setup, not a case
    merge, _ = copy_run(s, w, *GIT, "merge", "main", role="implementer")
    assert merge.rc != 0, f"want a conflict: {merge.out}"
    red.write_text(f"merged {DASH}\n")
    s.git(w, "add", red.name)
    ran, probe = copy_run(s, w, *GIT, "commit", "--no-edit", role="implementer")
    said = f"git commit, merge in progress: exit {ran.rc}\nprobe: {probe}\n{ran.out}"
    assert ran.rc == 0, said
    assert "skipped: MERGE_HEAD" in ran.out, said
    assert probe == [], f"want no fast tier run: {said}"
    assert len(s.git(w, "log", "-1", "--format=%P").split()) == 2, f"want the merge made: {said}"


if __name__ == "__main__":
    main(refused, skipped)
