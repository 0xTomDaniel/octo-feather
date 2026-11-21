"""The kit's `just setup` installs the template's pre-commit hook on `just fast` (quality
#acceptance-fast-hook, #recipe-fast; templates #tpl-hooks; #1211), in a throwaway git copy of the
kit (tests/gate/kit/gate_recipes_first.py's: static checks check-dashes and check-probe, test items
tests/a.sh, end-to-end, and tests/b.sh, here running git in a repo of its own and logging the git
dir it found to PROBE), never this checkout, whose git config a worktree shares. The run is in a
worktree of the copy, as a kit lane's is: git hands a hook there the absolute GIT_DIR and
GIT_INDEX_FILE of the worktree.

red: after `just setup` in the worktree, a `git commit` adding one em dash is refused, its output
the fast tier's (`heavy slot: not needed: fast tier`) naming check-dashes and the file and line it
found, HEAD unchanged.
green: after `just setup` there, that dash added and then gone (the fix), `git commit` goes
through, the fast tier having run tests/b.sh, whose git found its own repo, not the worktree's
that git hands its hook. Two scenarios, each one fast tier run, as each stays in the per-test CPU
budget (gate-budget.toml test_cpu_seconds): a refused commit leaves nothing behind (red's HEAD).
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from gate_recipes_first import DASH, copy_run, kit_copy
from testkit import Scratch, main

if TYPE_CHECKING:
    from pathlib import Path

# The file the commits add, in no kit copy: kit_copy takes every file git lists, staged ones too,
# so a hook running this test copies what its own commit stages.
RED = "hook-red.txt"
GIT = ("git", "-c", "user.email=t@t", "-c", "user.name=t", "-c", "commit.gpgsign=false")
INNER = """#!/usr/bin/env bash
d="$(mktemp -d)"
git -C "$d" init -q
echo "b $(git -C "$d" rev-parse --absolute-git-dir) $d/.git" >> "$PROBE"
"""


def head(s: Scratch, k: Path) -> str:
    return s.git(k, "rev-parse", "HEAD")


def worktree(s: Scratch) -> Path:
    """The copy's worktree, `just setup` run in it, one em dash staged in RED."""
    (s.root / "user-mise").mkdir()
    k = kit_copy(s)
    (k / "tests" / "b.sh").write_text(INNER)
    budget = k / "gate-budget.toml"  # one worker: fewer processes, the same tier
    one = re.sub(
        r"^fast_workers = \d+$", "fast_workers = 1", budget.read_text(), flags=re.MULTILINE
    )
    budget.write_text(one)
    s.git(k, "commit", "-qam", "b runs git, one fast worker")
    assert not (k / RED).exists(), f"{RED} is in the kit copy already"
    w = s.root / "wt"
    s.git(k, "worktree", "add", "-q", "-b", "gh1", str(w))
    ran, _ = copy_run(s, w, "just", "setup")
    assert ran.rc == 0, f"just setup: exit {ran.rc}\n{ran.out}"
    (w / RED).write_text(f"one {DASH} dash\n")
    s.git(w, "add", RED)
    return w


def red(s: Scratch) -> None:
    w = worktree(s)
    before = head(s, w)
    ran, probe = copy_run(s, w, *GIT, "commit", "-m", "red")
    said = f"git commit (red): exit {ran.rc}\nprobe: {probe}\n{ran.out}"
    assert ran.rc != 0, said
    assert "heavy slot: not needed: fast tier" in ran.out, f"want the fast tier: {said}"
    assert "test_recipe[check-dashes]" in ran.out, said
    assert f"{RED}:1:one {DASH} dash" in ran.out, said
    assert head(s, w) == before, f"want no commit: {said}"


def green(s: Scratch) -> None:
    w = worktree(s)
    (w / RED).write_text("one dash, gone\n")
    s.git(w, "add", RED)
    ran, probe = copy_run(s, w, *GIT, "commit", "-m", "green")
    said = f"git commit (green): exit {ran.rc}\nprobe: {probe}\n{ran.out}"
    assert ran.rc == 0, said
    assert "heavy slot: not needed: fast tier" in ran.out, f"want the fast tier: {said}"
    assert s.git(w, "log", "-1", "--format=%s") == "green", said
    inner = [ln.split() for ln in probe if ln.startswith("b ")]
    assert len(inner) == 1, f"want tests/b.sh run once: {said}"
    assert inner[0][1] == inner[0][2], f"want b.sh's git in its own repo: {said}"


if __name__ == "__main__":
    main(red, green)
