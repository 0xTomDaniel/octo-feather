"""scripts/check-owner-field on a scratch lane, as scenarios (testkit.main).

The lane's history: an old writer commit made before the check existed, then a main merge that
brings in the commit adding the check, then a writer commit with the message of real commit
6391de1b (lane gh906, #977), whose writer carried no Owner field. The check passes the old commit
with its notice line, refuses the new one naming the fix, and passes once the fix its refusal names
is done: `git commit --amend` on the last commit, `git rebase -i --rebase-merges <sha>^` with
`reword` on an older one. What the field is: .agents/skills/code-review/SKILL.md, Verdict step.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from testkit import ROOT, Scratch, kit, main

if TYPE_CHECKING:
    from pathlib import Path

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
    src = ROOT / "scripts" / "check-owner-field"
    (repo / "scripts" / "check-owner-field").write_text(src.read_text())
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
    for said in (
        "run-slots pass-over",
        "report names no owned rule",
        "`Owners: none` when there is none",
    ):
        assert said in err, err
    for fix in ("git commit --amend", "--rebase-merges <sha>^"):
        assert fix in err, err
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
    ident = ["-c", "user.email=t@example.com", "-c", "user.name=t"]
    rebase = ["rebase", "-q", "-i", "--rebase-merges", f"{bad}^"]
    s.run(
        ["git", "-C", str(repo), *ident, *rebase],
        env={"GIT_SEQUENCE_EDITOR": seq, "GIT_EDITOR": str(editor)},
    )
    check(s, repo, 0)
    assert s.git(repo, "log", "-1", "--format=%H", "--grep", "an old writer commit") == old
    assert (repo / "later").exists()


def qc_status_commit(s: Scratch) -> None:
    """The qc script's status-only commit (the message and file of real commit db00d5a8, lane
    gh1076) passes with no field; the same message on a commit that also changes another file is
    a writer's and is refused, as is a writer commit with no field."""
    repo = _lane(s)
    s.git(repo, "commit", "-q", "--amend", "-m", REAL + "\nOwners: none\n")
    (repo / "docs" / "specs").mkdir(parents=True)
    qc = (
        "qc: built acceptance-checkout-follows-main acceptance-checkout-kept "
        "acceptance-stale-agents (judged 5b87ad5f1419)"
    )
    _commit(s, repo, "docs/specs/issue-lifecycle.status.json", qc)
    out, _ = check(s, repo, 0)
    notice = [ln for ln in out.splitlines() if "qc status commit(s)" in ln]
    assert len(notice) == 1, out
    assert "1 qc status commit(s) without it passed" in notice[0], out
    assert "ok (1 commit(s)" in out, out
    (repo / "docs" / "specs" / "issue-lifecycle.status.json").write_text("{}\n")
    _commit(s, repo, "other", qc)
    _, err = check(s, repo, 1)
    assert "qc: built" in err, err
    assert "report names no owned rule" in err, err
    s.git(repo, "reset", "-q", "--hard", "HEAD^")
    _commit(s, repo, "writer", "feat: a writer commit with no field")
    _, err = check(s, repo, 1)
    assert "a writer commit with no field" in err, err


if __name__ == "__main__":
    main(refuse_then_amend, reword_older, qc_status_commit)
