"""The kit's `just setup` installs the template's pre-commit hook on `just fast` (quality
#acceptance-fast-hook, #recipe-fast; templates #tpl-hooks; #1211), in a throwaway git copy of the
kit (tests/gate/kit/gate_recipes_first.py's: static checks check-dashes and check-probe, test items
tests/a.sh, end-to-end, and tests/b.sh, here running git in a repo of its own and logging the git
dir it found to PROBE), never this checkout, whose git config a worktree shares. `just setup` runs
in the copy's main checkout, as a maintainer's (no OCTO_FEATHER_ROLE), before the copy has a
worktree (#acceptance-setup-not-factory refuses it after); the commits run in a worktree added then:
git hands a hook there the absolute GIT_DIR and GIT_INDEX_FILE of the worktree.

red [ROLE]: after `just setup`, a `git commit` in the worktree (as ROLE: none, a maintainer;
implementer, a writer, #acceptance-hook-machine-commit) adding one em dash is refused, its output
the fast tier's (`heavy slot: not needed: fast tier`) naming check-dashes and the file and line it
found, HEAD unchanged.
green: after `just setup`, that dash added and then gone (the fix), `git commit` goes
through, the fast tier having run tests/b.sh, whose git found its own repo, not the worktree's
that git hands its hook. Two scenarios, each one fast tier run, as each stays in the per-test CPU
budget (gate-budget.toml test_cpu_seconds): a refused commit leaves nothing behind (red's HEAD).
"""

from __future__ import annotations

import re
import subprocess
from functools import cache
from typing import TYPE_CHECKING

from gate_recipes_first import DASH, gate_env, kit_copy
from testkit import Ran, Scratch, main

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


def copy_run(s: Scratch, w: Path, *cmd: str, role: str | None = None) -> tuple[Ran, list[str]]:
    """CMD in W in the env a copy's gate runs in, OCTO_FEATHER_ROLE ROLE (None: a maintainer's,
    unset, whatever the gate's pane has): its exit and output (stdout and stderr together), and
    PROBE's lines."""
    probe = s.root / "probe"
    probe.write_text("")
    p = subprocess.run(
        list(cmd),
        cwd=w,
        env=copy_env(s) | ({"OCTO_FEATHER_ROLE": role} if role else {}),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    return Ran(p.returncode, p.stdout, ""), probe.read_text().splitlines()


@cache
def copy_env(s: Scratch) -> dict[str, str]:
    """gate_env for S, PROBE its probe, OCTO_FEATHER_ROLE unset: asked once per scratch, as
    gate_env asks uv for its dirs each time."""
    return {k: v for k, v in gate_env(s, s.root / "probe").items() if k != "OCTO_FEATHER_ROLE"}


def head(s: Scratch, k: Path) -> str:
    return s.git(k, "rev-parse", "HEAD")


def worktree(s: Scratch) -> Path:
    """The copy's worktree, `just setup` run before it in the main checkout, one em dash staged
    in RED."""
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
    ran, _ = copy_run(s, k, "just", "setup")
    assert ran.rc == 0, f"just setup: exit {ran.rc}\n{ran.out}"
    w = s.root / "wt"
    s.git(k, "worktree", "add", "-q", "-b", "gh1", str(w))
    (w / RED).write_text(f"one {DASH} dash\n")
    s.git(w, "add", RED)
    return w


def red(s: Scratch, role: str = "") -> None:
    w = worktree(s)
    before = head(s, w)
    ran, probe = copy_run(s, w, *GIT, "commit", "-m", "red", role=role or None)
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
