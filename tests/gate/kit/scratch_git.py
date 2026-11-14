"""A scratch's git starts no automatic maintenance (#916), as scenarios (testkit.main).

A prepared scratch is copied while later callers read it (Scratch.prepare); a `git maintenance run
--auto` or `gc --auto` a git command started there would keep writing in .git through the copy
(.git/objects/maintenance.lock vanishing mid-copy, #915). The repo's own config asks for auto gc
at once, run in the foreground (gc.auto=1, no detach), and three loose blobs sit in objects/17/,
over gc's sampled threshold, so a commit that starts it packs them before it returns; git's trace
(GIT_TRACE) logs every git command started.
"""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

from testkit import Scratch, main

if TYPE_CHECKING:
    from pathlib import Path


def _blobs_in_17(n: int) -> list[bytes]:
    """N file contents whose git blob ids start with 17, the objects dir gc --auto samples."""
    found: list[bytes] = []
    i = 0
    while len(found) < n:
        c = f"x{i}\n".encode()
        i += 1
        if hashlib.sha1(b"blob %d\0" % len(c) + c).hexdigest().startswith("17"):  # noqa: S324
            found.append(c)
    return found


def _loose(s: Scratch, repo: Path) -> int:
    """REPO's loose object count (git count-objects)."""
    return int(s.git(repo, "count-objects", "-v").splitlines()[0].removeprefix("count: "))


def no_auto_maintenance(s: Scratch) -> None:
    """A commit through the scratch in a repo whose config triggers auto gc at once starts no
    maintenance run or gc, and its loose objects stay loose."""
    repo = s.root / "repo"
    s.git(s.root, "init", "-q", str(repo))
    for k, v in (("gc.auto", "1"), ("gc.autoDetach", "false"), ("maintenance.autoDetach", "false")):
        s.git(repo, "config", k, v)
    for i, c in enumerate(_blobs_in_17(3)):
        (repo / f"f{i}").write_bytes(c)
    s.git(repo, "add", "-A")
    trace = s.root / "trace"
    s.env["GIT_TRACE"] = str(trace)
    s.git(repo, "commit", "-q", "-m", "x")
    started = [ln for ln in trace.read_text().splitlines() if "--auto" in ln]
    assert not started, "git started auto maintenance in a scratch:\n" + "\n".join(started)
    assert _loose(s, repo) == 5, "the loose objects were packed"  # 3 blobs, a tree, a commit


if __name__ == "__main__":
    main(no_auto_maintenance)
