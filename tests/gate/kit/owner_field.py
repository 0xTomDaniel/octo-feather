"""scripts/check-owner-field on a scratch lane, as scenarios (testkit.main).

The lane's history: an old writer commit made before the check existed, then a main merge that
brings in the commit adding the check, then a writer commit with the message of real commit
6391de1b (lane gh906, #977), whose writer carried no Owner field. The check passes the old commit
with its notice line, refuses the new one naming the fix, and passes once the fix its refusal names
is done: `git commit --amend` on the last commit, `git rebase -i --rebase-merges <sha>^` with
`reword` on an older one. What the field is: .agents/skills/code-review/SKILL.md, Verdict step.
"""

from __future__ import annotations

import os
from pathlib import Path

from testkit import ROOT, Scratch, kit, main

REAL = """docs(evidence): run-slots pass-over and manual-move smoke, demo and owed eval (#977)

Summary:
- evidence/2026-11-18-run-slots-pass-over.md: drive record 20261118T044043Z-da119200 (22
  cases), tests, the revoke demo transcript (scratch state).
- docs/owed-evals/977.md: the director's revoke-then-grant and revoke-to-dequeue.

Rationale:
- a changed verify map needs a Smoke: line and an owed eval in the same diff (docs/adr/0008).

Validation:
- just check-behavior-smoke, check-dashes.
"""


def _commit(s: Scratch, repo: Path, name: str, msg: str) -> str:
    (repo / name).write_text(name + "\n")
    s.git(repo, "add", "-A")
    s.git(repo, "commit", "-q", "-m", msg)
    return s.git(repo, "rev-parse", "HEAD")


def _lane(s: Scratch) -> Path:
    """A repo whose lane branch gh7 holds an old commit, main's check merged in, then REAL."""
    repo = s.root / "repo"
    s.git(s.root, "init", "-q", "-b", "main", str(repo))
    _commit(s, repo, "base", "base")
    s.git(repo, "checkout", "-q", "-b", "gh7")
    _commit(s, repo, "old", "feat: an old writer commit, before the check")
    s.git(repo, "checkout", "-q", "main")
    (repo / "scripts").mkdir()
    (repo / "scripts" / "check-owner-field").write_text((ROOT / "scripts" / "check-owner-field").read_text())
    s.git(repo, "add", "-A")
    s.git(repo, "commit", "-q", "-m", "feat: check-owner-field\n\nOwners: none")
    s.git(repo, "checkout", "-q", "gh7")
    s.git(repo, "merge", "-q", "--no-edit", "main")
    _commit(s, repo, "new", REAL)
    return repo


def check(s: Scratch, repo: Path, want: int) -> tuple[str, str]:
    ran = s.run([kit("check-owner-field"), "--repo", str(repo), "--base", "main"], want=want)
    return ran.out, ran.err


def refuse_then_amend(s: Scratch) -> None:
    """The real commit without the field is refused naming it and the fix; the old one passes
    with a notice; `git commit --amend` adding `Owners: none` makes the check pass."""
    repo = _lane(s)
    out, err = check(s, repo, 1)
    assert "1 commit(s) older than the check" in out, out
    assert "run-slots pass-over" in err and "report names no owned rule" in err, err
    assert "`Owners: none` when there is none" in err and "git commit --amend" in err and "--rebase-merges <sha>^" in err, err
    s.git(repo, "commit", "-q", "--amend", "-m", REAL + "\nOwners: none\n")
    out, _ = check(s, repo, 0)
    assert "ok (1 commit(s)" in out, out  # the amended one; the old one only noticed


def reword_older(s: Scratch) -> None:
    """A commit without the field under a later one is fixed by the rebase its refusal names,
    `reword` on it; the lane's main merge and the old commit stay as they were."""
    repo = _lane(s)
    _commit(s, repo, "later", "feat: a later commit\n\nOwners: none")
    old = s.git(repo, "log", "-1", "--format=%H", "--grep", "an old writer commit")
    _, err = check(s, repo, 1)
    bad = next(w for w in err.split() if len(w) == 12 and all(c in "0123456789abcdef" for c in w))
    editor = s.root / "add-owners"
    editor.write_text('#!/bin/sh\nprintf "\\nOwners: none\\n" >> "$1"\n')
    editor.chmod(0o755)
    seq = "sed -i '0,/^pick/s/^pick/reword/'"
    s.run(["git", "-C", str(repo), "-c", "user.email=t@example.com", "-c", "user.name=t", "rebase", "-q", "-i",
           "--rebase-merges", f"{bad}^"], env={"GIT_SEQUENCE_EDITOR": seq, "GIT_EDITOR": str(editor)})
    check(s, repo, 0)
    assert s.git(repo, "log", "-1", "--format=%H", "--grep", "an old writer commit") == old
    assert os.path.exists(repo / "later")


if __name__ == "__main__":
    main(refuse_then_amend, reword_older)
