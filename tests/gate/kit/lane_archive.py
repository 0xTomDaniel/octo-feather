"""The scenarios of tests/gate/kit/test_lane_archive.py (its items), this file their command
(testkit.main): scripts/octo-feather-lane archive (spec comms #acceptance-lane-archive): a temp
state dir (default and named HERDR_SESSION), a lane closed through the command: sha256 before =
after (the hand-off log: its lines unchanged, then the lane reflection's line, spec comms
#reflection-lane), lanes/ no longer lists it, archive/ holds both; a lane without a hand-off log;
each refusal leaves every file in place. The testkit's Pi stand-in answers as the reflector (no
gap found: testkit.reflector; tests/gate/kit/lane_reflect.py covers the reflection itself), the
testkit's herdr finds no server, the testkit's gh is the tracker."""

from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
from typing import TYPE_CHECKING

from testkit import Scratch, kit, main, reflector

if TYPE_CHECKING:
    from pathlib import Path


class State:
    def __init__(self, s: Scratch) -> None:
        self.s = s
        for k in ("HERDR_PANE_ID", "PI_SESSION_FILE", "OCTO_FEATHER_REFLECT_ARGS"):
            s.env.pop(k, None)
        s.env["XDG_STATE_HOME"] = str(s.root / "state")
        reflector(s)
        self.state = s.root / "state"
        self.top = self.state / "octo-feather" / "lanes"

    def seed(self, d: Path, name: str, *, log: bool = True) -> None:
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{name}.toml").write_bytes(
            'issue = "gh0"\nsupervisor = "w1:p2"\ngoal = "x é"\n'.encode()
        )
        if log:  # no final newline
            (d / f"{name}.handoffs.jsonl").write_text(
                '{"at":"2026-10-20T00:00:00Z","kind":"attempt"}\n{"kind":"integration"}'
            )

    def archive(self, name: str, session: str = "", want: int = 0) -> str:
        r = self.s.run(
            [kit("octo-feather-lane"), "archive", name], want=want, env={"HERDR_SESSION": session}
        )
        return (r.out + ("\n" + r.err if r.err else "")).strip("\n")

    def archive_ok(self, lanes: Path, name: str, session: str) -> None:
        """Archive NAME and check every claim."""
        rec = hashlib.sha256((lanes / f"{name}.toml").read_bytes()).hexdigest()
        orig = (lanes / f"{name}.handoffs.jsonl").read_bytes()
        out = self.archive(name, session).split("\n")
        assert f"archived: {lanes}/archive/{name}.toml sha256={rec}" in out, (
            f"no record sha line: {out}"
        )
        log = (lanes / "archive" / f"{name}.handoffs.jsonl").read_bytes()
        sha = hashlib.sha256(log).hexdigest()
        line = f"archived: {lanes}/archive/{name}.handoffs.jsonl sha256={sha}"
        assert line in out, f"no log sha line: {out}"
        assert (
            hashlib.sha256((lanes / "archive" / f"{name}.toml").read_bytes()).hexdigest() == rec
        ), "record bytes changed"
        reflected(log, orig)
        left = [p.name for p in lanes.iterdir() if p.name.startswith(f"{name}.")]
        assert not left, f"lanes/ still lists {name}: {left}"

    def tree(self) -> list[tuple[str, ...]]:
        """Every entry under the state dir: its path, type, link count, link target, bytes."""
        out: list[tuple[str, ...]] = []
        for p in sorted(self.state.rglob("*")):
            st = p.lstat()
            link = str(p.readlink()) if p.is_symlink() else ""
            body = hashlib.sha256(p.read_bytes()).hexdigest() if stat.S_ISREG(st.st_mode) else ""
            out.append((str(p), oct(stat.S_IFMT(st.st_mode)), str(st.st_nlink), link, body))
        return out

    def refuse(self, want: str, name: str) -> None:
        """Archive NAME refused, saying WANT, every entry under the state dir unchanged."""
        before = self.tree()
        p = subprocess.run(
            [kit("octo-feather-lane"), "archive", name],
            env=self.s.env | {"HERDR_SESSION": ""},
            cwd=self.s.root,
            capture_output=True,
            text=True,
            check=False,
        )
        out = p.stdout + "\n" + p.stderr
        assert p.returncode != 0, f"archive {name} did not refuse"
        assert want in out, f"refusal for {name} did not say {want!r}: {out}"
        assert "Traceback" not in out, f"refusal for {name} printed a traceback: {out}"
        assert self.tree() == before, f"refusal for {name} moved or changed files"


def reflected(got: bytes, orig: bytes) -> None:
    """GOT is ORIG's bytes, a newline if they lacked one, then one reflection line, 0 findings."""
    head = orig + (b"\n" if orig and not orig.endswith(b"\n") else b"")
    assert got.startswith(head), "lane lines changed"
    tail = got[len(head) :].decode().splitlines()
    assert len(tail) == 1, tail
    d = json.loads(tail[0])
    assert d["kind"] == "reflection", tail
    assert d["findings"] == 0, tail


def archived(s: Scratch) -> None:
    """Default session (HERDR_SESSION empty): state at the top; a second lane untouched. Named
    session: state under sessions/<key>; the default session's same-named lane stays. No hand-off
    log: the reflection writes its first line, archived beside the record."""
    st = State(s)
    top = st.top
    st.seed(top, "gh0")
    st.seed(top, "gh1")
    other = [(p.name, p.read_bytes()) for p in sorted(top.glob("gh1.*"))]
    st.archive_ok(top, "gh0", "")
    assert [(p.name, p.read_bytes()) for p in sorted(top.glob("gh1.*"))] == other, (
        "another lane changed"
    )
    named = st.state / "octo-feather" / "sessions" / "s1" / "lanes"
    st.seed(named, "gh2")
    st.seed(top, "gh2")
    st.archive_ok(named, "gh2", "s1")
    assert (top / "gh2.toml").is_file(), "named session touched the default session"
    assert not (top / "archive" / "gh2.toml").exists(), "named session touched the default session"
    st.seed(top, "gh3", log=False)
    out = st.archive("gh3")
    assert f"archived: {top}/archive/gh3.toml sha256=" in out, f"no-log output: {out}"
    assert f"archived: {top}/archive/gh3.handoffs.jsonl sha256=" in out, f"no-log output: {out}"
    reflected((top / "archive" / "gh3.handoffs.jsonl").read_bytes(), b"")
    assert not (top / "gh3.toml").exists(), "no-log move wrong"
    assert not (top / "gh3.handoffs.jsonl").exists(), "no-log move wrong"


def refusals(s: Scratch) -> None:
    """Each refusal non-zero, naming why, every entry under the state dir unchanged: a missing
    record (a stray log of that name stays), an archived record already there, an archived log
    already there, a bad name; non-regular sources before any move: a symlinked record, a
    symlinked log, a directory record, a directory log."""
    st = State(s)
    top = st.top
    st.seed(top / "archive", "gh0")  # gh0 archived before
    (top / "gh4.handoffs.jsonl").write_text("{}\n")
    st.refuse("no lane record", "gh4")
    st.seed(top, "gh0")
    st.refuse(f"archive target exists: {top}/archive/gh0.toml", "gh0")
    st.seed(top, "gh5")
    (top / "archive" / "gh5.handoffs.jsonl").write_text("old\n")
    st.refuse(f"archive target exists: {top}/archive/gh5.handoffs.jsonl", "gh5")
    st.refuse("usage", "../gh1")
    (top / "seed.toml").write_text("issue = 0\n")
    (top / "gh7.toml").symlink_to("seed.toml")
    (top / "gh7.handoffs.jsonl").write_text("{}\n")
    st.refuse(f"not a regular file: {top}/gh7.toml", "gh7")
    (top / "gh8.toml").write_text("issue = 0\n")
    (top / "seed.jsonl").write_text("{}\n")
    (top / "gh8.handoffs.jsonl").symlink_to("seed.jsonl")
    st.refuse(f"not a regular file: {top}/gh8.handoffs.jsonl", "gh8")
    (top / "gh9.toml").mkdir()
    (top / "gh9.handoffs.jsonl").write_text("{}\n")
    st.refuse(f"not a regular file: {top}/gh9.toml", "gh9")
    (top / "gh10.toml").write_text("issue = 0\n")
    (top / "gh10.handoffs.jsonl").mkdir()
    st.refuse(f"not a regular file: {top}/gh10.handoffs.jsonl", "gh10")


def read_only(s: Scratch) -> None:
    """Execution failure (read-only lanes/: the link into archive/ works, the unlink of the source
    fails): exit 1, no partial archive, no hard link left behind; with no archive/ yet, mkdir fails,
    refused cleanly, nothing created; a retry after restoring permissions succeeds. Skipped as
    uid 0 (it ignores chmod)."""
    if os.getuid() == 0:
        return
    st = State(s)
    ro = st.state / "octo-feather" / "sessions" / "ro" / "lanes"
    st.seed(ro, "gh6")
    (ro / "archive").mkdir()

    def files() -> dict[str, bytes]:
        return {str(p.relative_to(ro)): p.read_bytes() for p in ro.rglob("*") if p.is_file()}

    before = files()
    ro.chmod(0o555)
    try:
        out = st.archive("gh6", "ro", want=1)
        assert "move failed" in out, f"read-only lanes/: no move-failed message: {out}"
        assert files() == before, f"read-only lanes/: partial archive: {files()}"
        assert not list((ro / "archive").iterdir()), "read-only lanes/: archive/ not empty"
        assert (ro / "gh6.toml").stat().st_nlink == 1, "read-only lanes/: record still hard-linked"
        ro.chmod(0o755)
        (ro / "archive").rmdir()
        ro.chmod(0o555)
        out = st.archive("gh6", "ro", want=1)
        assert "move failed" in out, f"read-only lanes/, no archive/: {out}"
        assert not (ro / "archive").exists(), "read-only lanes/, no archive/: archive/ created"
        assert files() == before, "read-only lanes/, no archive/: files changed"
    finally:
        ro.chmod(0o755)
    st.archive_ok(ro, "gh6", "ro")


if __name__ == "__main__":
    main(archived, refusals, read_only)
