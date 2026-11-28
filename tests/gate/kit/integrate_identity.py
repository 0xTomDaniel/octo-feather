"""`just integrate` with no git commit identity refuses before merging, naming the identity and
how the factory supplies it per process, never as a conflict (#888, #1350; owner ruling
2026-11-28 #1349); with one, a real conflict still names its paths. Through
octo-feather-integrate in a scratch target: main, lane worktree gh7, worker branches; git reads
no user config (no system file, GIT_CONFIG_GLOBAL /dev/null) and no identity env.

unset: no identity anywhere, a worker branch w2 that merges cleanly: integrate exits 78 naming
the commit identity, the four GIT_ env keys every role launch sets from the box onboarding file's
[identity] table, and the command that sets it (scripts/pi-role --help, Commit identity); no
conflict line, no gate tier, the lane as it was. conflict: the identity in the process env, as a
role launch sets it, and lane and w1 both editing f: exit 1, `conflict: w1 in f`, the lane as it
was and clean."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from testkit import Scratch, kit, main

if TYPE_CHECKING:
    from pathlib import Path

IDENT_ENV = tuple(f"GIT_{w}_{f}" for w in ("AUTHOR", "COMMITTER") for f in ("NAME", "EMAIL"))
NO_IDENTITY = 78


def world(s: Scratch) -> tuple[Path, Path]:
    """S's target with no git identity: main holding f and a gate, lane gh7 editing f, worker w1
    editing f too, worker w2 adding b. Returns the repo and the lane worktree."""
    for k in (*IDENT_ENV, "EMAIL", "GIT_CONFIG_SYSTEM"):
        s.env.pop(k, None)
    s.env |= {"GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1"}
    r, lane, w1 = s.root / "repo", s.root / "lane", s.root / "w1"
    r.mkdir()
    (r / "justfile").write_text("check:\n    true\n")
    (r / "f").write_text("a\n")
    s.git(r, "init", "-q", "-b", "main")
    s.git(r, "add", "-A")
    s.git(r, "commit", "-qm", "base")
    for wt, b, f, text in (
        (lane, "gh7", "f", "lane\n"),
        (w1, "w1", "f", "worker\n"),
        (s.root / "w2", "w2", "b", "b\n"),
    ):
        s.git(r, "worktree", "add", "-q", "-b", b, str(wt))
        (wt / f).write_text(text)
        s.git(wt, "add", "-A")
        s.git(wt, "commit", "-qm", b)
    return r, lane


def unset(s: Scratch) -> None:
    repo, lane = world(s)
    start = s.git(lane, "rev-parse", "HEAD")
    ran = s.run([kit("octo-feather-integrate"), "7", "w2"], cwd=repo, want=NO_IDENTITY)
    out = ran.out + "\n" + ran.err
    onboarding = s.home / ".local" / "state" / "octo-feather" / "onboarding.toml"
    assert re.search(r"refused before integrating, lane gh7: no git commit identity", ran.err), out
    assert ", ".join(IDENT_ENV[:3]) + " and " + IDENT_ENV[3] in ran.err, out
    assert f"[identity] name and email in the box onboarding file {onboarding}" in ran.err, out
    assert f'{kit("pi-role")} --set-identity "Your Name" you@example.com' in ran.err, out
    assert "conflict" not in out, out
    assert "tier:" not in out, out
    assert s.git(lane, "rev-parse", "HEAD") == start, f"{lane} moved"


def conflict(s: Scratch) -> None:
    repo, lane = world(s)
    start = s.git(lane, "rev-parse", "HEAD")
    ident = {k: "t@example.com" if k.endswith("EMAIL") else "t" for k in IDENT_ENV}
    ran = s.run([kit("octo-feather-integrate"), "7", "w1"], cwd=repo, want=1, env=ident)
    assert re.search(r"^conflict: w1 in f$", ran.err, re.MULTILINE), ran.err
    assert "identity" not in ran.err, ran.err
    assert s.git(lane, "rev-parse", "HEAD") == start, f"{lane} not reset"
    assert s.git(lane, "status", "--porcelain") == "", f"{lane} left dirty"


if __name__ == "__main__":
    main(unset, conflict)
