"""The scenarios of tests/gate/kit/test_qc_copies.py (its items), this file their command
(testkit.main): the qc sandbox test's credential-copies section (the live box: testkit.qc.box; the
fake judge: testkit/judge.py, FAKE_QC). No judge write persists (the worktree is an overlay on
the run tmpfs): copies of Pi's credentials into ignored scratch/, .git, over 64 MiB, an
intermediate refresh, token values alone, into HOME; the judge's rewrites of auth.json and
models.json hit per-run copies, the box files byte-identical."""

from __future__ import annotations

import json
from pathlib import Path

from testkit import Ran, Scratch, main
from testkit.qc import AUTH, MODELS, box, judged, latest


def copycase(s: Scratch, mode: str, *copies: str) -> Ran:
    """One judge (MODE) passing: its COPIES gone, the worktree pristine, no Pi credential left in
    the repo or HOME outside Pi's own dir."""
    r = s.root / "repo"
    ran = judged(s, mode, "acceptance-a", want=0)
    for f in copies:
        p = Path(f) if f.startswith("/") else r / f
        assert not p.exists(), f"{mode}: credential copy {f} survived"
    left = s.git(r, "status", "--porcelain", "--ignored")
    assert left == "", f"{mode}: worktree not pristine: {left}"
    for top in (r, s.home):
        for p in top.rglob("*"):
            if ".pi" in p.relative_to(top).parts or not p.is_file() or p.is_symlink():
                continue
            assert b"SECRET-pi" not in p.read_bytes(), f"{mode}: a Pi credential survived in {p}"
    return ran


def piok(s: Scratch, mode: str, ran: Ran) -> None:
    """The box's Pi files untouched: only auth.json (mode 600) and models.json, their bytes as
    built, no auth_writeback reported."""
    d = s.home / ".pi" / "agent"
    assert sorted(p.name for p in d.iterdir()) == ["auth.json", "models.json"], list(d.iterdir())
    assert (d / "auth.json").stat().st_mode & 0o777 == 0o600, f"{mode}: auth.json mode changed"
    assert (d / "auth.json").read_text() == AUTH, f"{mode}: box auth.json changed"
    assert (d / "models.json").read_text() == MODELS, f"{mode}: box models.json changed"
    sb = json.dumps(latest(s)["fallback"]["acceptance-a"]["sandbox"])
    assert "auth_writeback" not in ran.out + sb, f"{mode}: auth_writeback still reported"


def credential_copies(s: Scratch) -> None:
    """Credential copies cannot survive anywhere: into ignored scratch/ and .git, and one over 64
    MiB, live in the overlay and die with the run."""
    box(s)
    copycase(s, "copycreds", "scratch/a", ".git/m")
    copycase(s, "bigcopy", "scratch/big")


def pi_rewrite(s: Scratch) -> None:
    """The judge rewrites both Pi files: its per-run copies, discarded, the box files
    byte-identical, no OAuth warning."""
    box(s)
    ran = copycase(s, "rewrite")
    piok(s, "rewrite", ran)
    assert "OAuth" not in ran.out, f"rewrite: OAuth warning without OAuth credentials: {ran.out}"


def pi_refresh(s: Scratch) -> None:
    """A token refresh in place (intermediate copies into scratch/, .git and HOME): discarded,
    never written back, the proof saying no writable persistent path; token values alone copied:
    discarded."""
    box(s)
    ran = copycase(s, "refresh", "scratch/oldauth", ".git/oldauth", str(s.home / "oldauth"))
    piok(s, "refresh", ran)
    proof = "qc sandbox: ok   writable persistent paths: none"
    assert proof in ran.out.splitlines(), f"proof must say writable persistent paths: none: {ran.out}"
    ran = copycase(s, "token", "scratch/tok", ".git/tok2")
    piok(s, "token", ran)


if __name__ == "__main__":
    main(credential_copies, pi_rewrite, pi_refresh)
