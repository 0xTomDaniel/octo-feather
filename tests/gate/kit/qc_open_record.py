"""The qc sandbox's open record (quality#acceptance-qc-eval-verdict; octo-feather-qc-sandbox --help,
R; eval-cases schema, Open record), run by hand (`octo-feather-qc-sandbox -- CMD`, no Pi, no
model) in a scratch repo, the kit under test a scratch kit (QC_KIT, a git repo in HOME): the
recorder's line lists, kit-relative, each tracked kit file the judge read (cat), ran (a script's
exec) or imported (Python, its __pycache__ already holding the module), and each tracked dir it
listed, marked whole; an untracked kit file it read is absent, and so is a tracked file only the
host read during the run (the kit's own read-only view). A kit dir whose watch the kernel refuses
(the watch limit reached) leaves the record not whole, naming why, with no list.

Mid-run is fixed by event order, no timing: the judge holds on a FIFO handshake while the host
reads the kit; the host then lets it run on. The watch limit is the kernel's own, per user
namespace (/proc/sys/user/max_inotify_watches, as a busy box's max_user_watches runs out): the
sandbox runs in a user namespace allowing one watch, as its caller's uid."""

from __future__ import annotations

import json
import os
import py_compile
import re
import select
import subprocess
from typing import TYPE_CHECKING, Any

from testkit import Scratch, kit, main, tool_homes

if TYPE_CHECKING:
    from pathlib import Path


def scratch_kit(s: Scratch) -> Path:
    """S's kit under test: GLOSSARY.md, NOTICE, bin/tool (a script), lib/mod.py (its __pycache__
    compiled on the host) and docs/sub/a.md tracked; scratch.txt not."""
    k = s.home / "kit"
    for rel, text in (
        ("GLOSSARY.md", "g\n"),
        ("NOTICE", "n\n"),
        ("bin/tool", "#!/bin/sh\necho tool ran\n"),
        ("lib/mod.py", "X = 1\n"),
        ("docs/sub/a.md", "a\n"),
    ):
        (k / rel).parent.mkdir(parents=True, exist_ok=True)
        (k / rel).write_text(text)
    (k / "bin" / "tool").chmod(0o755)
    s.git(k, "init", "-q", "-b", "main")
    s.git(k, "add", "-A")
    s.git(k, "commit", "-qm", "kit")
    (k / "scratch.txt").write_text("untracked\n")
    py_compile.compile(str(k / "lib" / "mod.py"), doraise=True)
    assert list((k / "lib" / "__pycache__").glob("mod.*.pyc")), "no __pycache__ for lib/mod.py"
    return k


def repo(s: Scratch) -> Path:
    r = s.root / "repo"
    r.mkdir()
    s.git(r, "init", "-q", "-b", "main")
    (r / "README").write_text("x\n")
    s.git(r, "add", "-A")
    s.git(r, "commit", "-qm", "init")
    return r


def opens(err: str) -> dict[str, Any]:
    """The recorder's line's open record."""
    line = next(ln for ln in err.splitlines() if ln.startswith('qc sandbox: record {"attempts"'))
    return json.loads(line.split("record ", 1)[1])["opens"]


def whole(s: Scratch) -> None:
    """Read, ran, imported and listed kit paths recorded; the untracked file and the host's
    mid-run read absent; whole."""
    k, r = scratch_kit(s), repo(s)
    at, go = s.bin / "qc-at", s.bin / "qc-go"
    os.mkfifo(at)
    os.mkfifo(go)
    cmd = (
        f"cat {k}/GLOSSARY.md >/dev/null; {k}/bin/tool; ls {k}/docs/sub >/dev/null; "
        f"python3 -c 'import sys; sys.path.insert(0, \"{k}/lib\"); import mod'; "
        f'cat {k}/scratch.txt >/dev/null; : > "{at}"; cat "{go}" >/dev/null'
    )
    afd = os.open(at, os.O_RDONLY | os.O_NONBLOCK)
    p = subprocess.Popen(
        [kit("octo-feather-qc-sandbox"), "--", "sh", "-c", cmd],
        cwd=r,
        env={**s.env, **tool_homes(), "QC_KIT": str(k)},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        held = False
        while p.poll() is None:  # the judge's open and close of the FIFO: a hang-up here
            if select.select([afd], [], [], 0.1)[0]:
                held = True
                break
        assert held, f"the judge never reached the handshake: {p.communicate()}"
        assert (k / "NOTICE").read_text() == "n\n"  # the host reads the live kit mid-run
        gfd = os.open(go, os.O_WRONLY)  # held until the judge opens it to read
        os.close(gfd)
        out, err = p.communicate(timeout=120)
    finally:
        os.close(afd)
        if p.poll() is None:
            p.kill()
            p.wait()
    assert p.returncode == 0, (out, err)
    assert "tool ran" in out, out
    assert "FAIL" not in err, err
    got = opens(err)
    assert got["whole"] is True, got
    assert got["files"] == ["GLOSSARY.md", "bin/tool", "lib/mod.py"], got
    assert "docs/sub/" in got["dirs"], got
    assert "qc sandbox: open record: whole, 3 kit files" in err, err


def not_whole(s: Scratch) -> None:
    """Kit dir watches the kernel refuses: not whole, naming them, and no list."""
    k, r = scratch_kit(s), repo(s)
    box = kit("octo-feather-qc-sandbox")
    ids = f"--map-user={os.getuid()} --map-group={os.getgid()}"
    limited = (
        "echo 1 > /proc/sys/user/max_inotify_watches && "
        f"exec unshare --user {ids} -- {box} -- cat {k}/GLOSSARY.md"
    )
    ran = s.run(
        ["unshare", "-r", "sh", "-c", limited],
        cwd=r,
        env={**tool_homes(), "QC_KIT": str(k)},
    )
    got = opens(ran.err)
    assert set(got) == {"whole", "why"}, got
    assert got["whole"] is False, got
    why = r"[1-5] of 5 kit dir watches not added: (\S+/ \(No space left on device\)(, )?)+"
    assert re.fullmatch(why, str(got["why"])), got
    assert "qc sandbox: open record: NOT whole (" in ran.err, ran.err


if __name__ == "__main__":
    main(whole, not_whole)
