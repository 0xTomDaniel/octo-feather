"""scripts/check-parity, run as a command in scratch git repos with real git (ticket #1273, seam
`rule: scripts/check-parity` agreed on it before any test), as scenarios (testkit.main).

A parity case's patch (tests/parity/CASE/*.patch) is made with `git diff` against a scratch repo's
file; a later commit moving that file's lines makes it stale. check-parity names each stale
patch with git's own error and exits 1, pointing at the re-anchor paragraph of
`tests/parity/lever.py --help`; with every patch applying (one at a line offset, as the lever's
plain `git apply` takes it), or no tests/parity, it exits 0.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from testkit import Scratch, kit, main

if TYPE_CHECKING:
    from pathlib import Path

LINES = "".join(f"line {i}\n" for i in range(1, 21))


def _repo(s: Scratch) -> Path:
    """A scratch repo holding cmd.sh (twenty lines) and two parity cases, each one patch seeding a
    defect in it: a/drop.patch drops line 5, b/edit.patch rewrites line 15."""
    repo = s.root / "repo"
    s.git(s.root, "init", "-q", str(repo))
    (repo / "cmd.sh").write_text(LINES)
    s.git(repo, "add", "-A")
    s.git(repo, "commit", "-qm", "cmd.sh")
    for case, old, new in (("a/drop", "line 5\n", ""), ("b/edit", "line 15\n", "broken 15\n")):
        (repo / "cmd.sh").write_text(LINES.replace(old, new))
        patch = repo / "tests" / "parity" / f"{case}.patch"
        patch.parent.mkdir(parents=True, exist_ok=True)
        patch.write_text(f"seeds {case}\n" + s.git(repo, "diff") + "\n")
        (repo / "cmd.sh").write_text(LINES)
    s.git(repo, "add", "-A")
    s.git(repo, "commit", "-qm", "cases")
    return repo


def stale_named(s: Scratch) -> None:
    """The code under a's patch moved: run from a subdir, check-parity names that patch with
    git's error, not b's, points at lever.py --help, and exits 1."""
    repo = _repo(s)
    (repo / "cmd.sh").write_text(LINES.replace("line 4\n", "moved 4\n"))
    s.git(repo, "commit", "-qam", "move line 4")
    ran = s.run([kit("check-parity")], want=1, cwd=repo / "tests" / "parity")
    assert "tests/parity/a/drop.patch" in ran.out, ran
    assert "patch does not apply" in ran.out, ran  # git's own error
    assert "b/edit.patch" not in ran.out + ran.err, ran
    assert "tests/parity/lever.py --help" in ran.err, ran


def applying_ok(s: Scratch) -> None:
    """A repo with no tests/parity exits 0; so does one whose patches all apply, one at a line
    offset (two lines added above it)."""
    bare = s.root / "bare"
    s.git(s.root, "init", "-q", str(bare))
    s.run([kit("check-parity")], cwd=bare)
    repo = _repo(s)
    (repo / "cmd.sh").write_text("new a\nnew b\n" + LINES)
    s.git(repo, "commit", "-qam", "offset")
    s.run([kit("check-parity")], cwd=repo)


if __name__ == "__main__":
    main(stale_named, applying_ok)
