"""The launch's stash guard (spec roles#launch-stash-guard, #acceptance-stash-guard; #1308): every
agent pi-role launches runs git through scripts/stash-guard/, so in a repository with 2+
worktrees a git stash that writes the shared stash is refused naming a WIP commit, and nothing
else about git changes. Driven through `pi-role`: a headless `pi-role agents/implementer.md -p`
starts a stand-in pi that runs $STUB_RUN in its shell, as a role's bash call would (no model
call); a pane's PATH is `pi-role --json`'s "path". Real git, in scratch repos; the entry set
aside before any guard is made with real git off the guard's PATH."""

from __future__ import annotations

import json
import os
from pathlib import Path

from testkit import ROOT, Ran, Scratch, kit, main

WIP = "git commit -am wip"
# The stand-in pi (Pi, which the kit does not own): launched as a role, it runs $STUB_RUN in its
# shell and exits with that shell's exit; any other call does nothing.
PI = (
    "#!/bin/sh\n"
    'case " $* " in *" --octo-feather-role "*) ;; *) exit 0 ;; esac\n'
    'exec sh -c "$STUB_RUN"\n'
)


def world(s: Scratch) -> None:
    """The stand-in pi first on PATH, the commit identity set, and no stash guard on the caller's
    PATH (a gate run from an agent's shell has one), so a plain `git` here is real git."""
    pib = s.root / "pibin"
    pib.mkdir()
    (pib / "pi").write_text(PI)
    (pib / "pi").chmod(0o755)
    path = [d for d in s.env["PATH"].split(os.pathsep) if Path(d).name != "stash-guard"]
    s.env["PATH"] = os.pathsep.join([str(pib), *path])
    s.identity()


def repo(s: Scratch, name: str) -> Path:
    """A scratch repo NAME with one committed file f."""
    r = s.root / name
    s.run(["git", "init", "-q", "-b", "main", str(r)])
    (r / "f").write_text("base\n")
    s.git(r, "add", "f")
    s.git(r, "commit", "-qm", "base")
    return r


def agent(s: Scratch, cwd: Path, run: str, *, want: int) -> Ran:
    """A headless implementer launched through pi-role at CWD whose shell runs RUN."""
    return s.run(
        [kit("pi-role"), str(ROOT / "agents" / "implementer.md"), "-p", "brief"],
        want=want,
        cwd=cwd,
        env={"STUB_RUN": run},
    )


def two_worktrees(s: Scratch) -> tuple[Path, Path]:
    """A repo (first worktree) and a linked second one, the first's stash holding one entry, set
    aside with real git."""
    world(s)
    first = repo(s, "first")
    second = s.root / "second"
    s.git(first, "worktree", "add", "-q", "-b", "lane2", str(second))
    (first / "f").write_text("first's work\n")
    s.git(first, "stash", "push", "-q", "-m", "first wip")
    return first, second


def pane(s: Scratch, cwd: Path, caller: str) -> str:
    """The PATH a pane launch at CWD gives its agent: `pi-role --json`'s "path" (herdr-spawn hands
    it to the tab), for a caller whose PATH is CALLER."""
    out = s.run(
        [kit("pi-role"), "--json", str(ROOT / "agents" / "implementer.md")],
        cwd=cwd,
        env={"PATH": caller},
    ).out
    return json.loads(out)["path"]


def refused(s: Scratch) -> None:
    """In the second worktree an agent's git stash drop, and its git stash push with changes, are
    refused naming the WIP commit; the first's stash list still shows its entry, the second's
    changes stay in its worktree; git stash list runs unchanged. A pane agent (its PATH from
    `pi-role --json`) is refused the same, the caller's stub pi still found first, and a git the
    caller put earlier on PATH still the git that runs."""
    first, second = two_worktrees(s)
    entry = s.git(first, "stash", "list")
    assert "first wip" in entry, entry
    ran = agent(s, second, "git stash drop", want=1)
    assert WIP in ran.err, ran.err
    assert "git reset --soft HEAD~1" in ran.err, ran.err
    assert s.git(first, "stash", "list") == entry
    (second / "f").write_text("second's work\n")
    for push in (
        "git stash",
        "git stash push -q -u -m x",
        "git -C ../first stash pop",
        "git stash clear",
        "git stash -m --help",
        "git stash -m -h",
        "git stash push -qm --help",
    ):
        ran = agent(s, second, push, want=1)
        assert WIP in ran.err, (push, ran.err)
    assert (second / "f").read_text() == "second's work\n"
    assert s.git(first, "stash", "list") == entry
    assert agent(s, second, "git stash list", want=0).out == entry
    path = pane(s, second, s.env["PATH"])
    ran = s.run(
        ["sh", "-c", "command -v pi; git stash drop"], want=1, cwd=second, env={"PATH": path}
    )
    assert ran.out == str(s.root / "pibin" / "pi"), ran.out
    assert WIP in ran.err, ran.err
    assert s.git(first, "stash", "list") == entry
    own = s.root / "owngit"
    own.mkdir()
    (own / "git").write_text('#!/bin/sh\necho "caller git $*"\n')
    (own / "git").chmod(0o755)
    path = pane(s, second, f"{own}{os.pathsep}{s.env['PATH']}")
    ran = s.run(["sh", "-c", "git status"], cwd=second, env={"PATH": path})
    assert ran.out == "caller git status", ran.out


def unchanged(s: Scratch) -> None:
    """An argv without `stash`, in a two-worktree repo, through the guard: git's own output, stderr,
    exit code and stdin; a read-only stash (show) too. In a repo with one worktree an agent's git
    stash and git stash pop run as git's own."""
    first, second = two_worktrees(s)
    for cmd, want in (
        ("git rev-parse --verify nosuch", 128),
        ("git log -1 --format=%s", 0),
        ("echo hi | git hash-object --stdin", 0),
        ("git -C ../first stash show --stat", 0),
        ("git --version stash", 0),
        ("git -h stash", 0),
        ("git stash push -q --help", 129),
    ):
        got = agent(s, second, cmd, want=want)
        real = s.run(["sh", "-c", cmd], want=want, cwd=second)
        assert (got.out, got.err) == (real.out, real.err), (cmd, got, real)
    assert s.git(first, "stash", "list") != ""
    r = repo(s, "solo")
    (r / "f").write_text("work\n")
    ran = agent(s, r, "git stash -q && git stash list && git stash pop -q", want=0)
    assert ran.out.startswith("stash@{0}: WIP on main"), ran.out
    assert (r / "f").read_text() == "work\n"
    assert s.git(r, "stash", "list") == ""


if __name__ == "__main__":
    main(refused, unchanged)
