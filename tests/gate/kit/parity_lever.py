"""tests/parity/lever.py, run as a command on a scratch kit of a few files (ticket #1361, seam
`rule: tests/parity/lever.py` agreed on it before any test), as scenarios (testkit.main).

The scratch kit is a git repo holding the lever (copied: it finds its kit beside itself), a
justfile whose `test` recipe runs the one test it is given, and two cases. Its first commit
(old_at) holds an old test, its executable stand-in and a symlink to it; the next drops them.
`needs`: the restored old side sees the stand-in executable and the link a link, as git holds
them at old_at, and parity holds. `net`: the old and new tests connect to a listener on the
caller's loopback; both fail, and the listener counts no connection.
"""

from __future__ import annotations

import re
import shutil
import socket
from pathlib import Path

from testkit import ROOT, Scratch, main

JUSTFILE = r"""set positional-arguments

# The one test named (a gate item id tests/gate/test_gate.py::test_script[F] stands for F), run.
test *args:
    #!/usr/bin/env bash
    for a in "$@"; do [[ $a == -* ]] || id="$a"; done
    [[ $id =~ \[(.*)\]$ ]] && id="${BASH_REMATCH[1]}"
    exec "./$id"
"""
OLD = """#!/usr/bin/env bash
set -eu
d="$(dirname "$0")/fixtures/lever"
[[ -L $d/link && $(readlink "$d/link") == stub ]] || { echo "old: link is no link"; exit 1; }
[[ -x $d/stub ]] || { echo "old: stub is not executable"; exit 1; }
"$d/link"
"""
STUB = "#!/bin/sh\necho stub ran\n"
NEW = "#!/bin/sh\necho new ran\n"
PROBE = """#!/usr/bin/env bash
: 3<>"/dev/tcp/127.0.0.1/$PROBE_PORT" || exit 1
echo "probe: reached 127.0.0.1:$PROBE_PORT"
"""


def _write(p: Path, body: str, mode: int = 0o644) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body)
    p.chmod(mode)


def _kit(s: Scratch) -> Path:
    """S/kit, the scratch kit: old_at holds tests/old.sh, tests/fixtures/lever/stub (mode 755)
    and tests/fixtures/lever/link (a symlink to stub); HEAD drops them and adds the cases."""
    k = s.root / "kit"
    s.git(s.root, "init", "-q", str(k))
    lever = k / "tests" / "parity" / "lever.py"
    lever.parent.mkdir(parents=True)
    shutil.copy2(ROOT / "tests" / "parity" / "lever.py", lever)
    _write(k / "justfile", JUSTFILE)
    _write(k / "tests" / "old.sh", OLD, 0o755)
    _write(k / "tests" / "fixtures" / "lever" / "stub", STUB, 0o755)
    (k / "tests" / "fixtures" / "lever" / "link").symlink_to("stub")
    _write(k / "tests" / "probe.sh", PROBE, 0o755)
    s.git(k, "add", "-A")
    s.git(k, "commit", "-qm", "old")
    old_at = s.git(k, "rev-parse", "HEAD")
    s.git(k, "rm", "-rq", "tests/old.sh", "tests/fixtures")
    _write(k / "tests" / "new.sh", NEW, 0o755)
    for name, old, needs, new in (
        ("needs", "tests/old.sh", '["tests/fixtures/lever"]', "tests/new.sh"),
        ("net", "tests/probe.sh", "[]", "tests/probe.sh"),
    ):
        toml = f'old = "{old}"\nold_at = "{old_at}"\nneeds = {needs}\nnew = "{new}"\n'
        _write(k / "tests" / "parity" / name / "case.toml", toml)
    s.git(k, "add", "-A")
    s.git(k, "commit", "-qm", "cases")
    return k


def _log(out: str, name: str) -> str:
    """The run log NAME in the log dir the lever printed last."""
    m = re.search(r"logs: (\S+)$", out)
    assert m, out
    return (Path(m[1]) / name).read_text()


def needs_as_git_holds(s: Scratch) -> None:
    """The old side runs with the stand-in executable and the link a link, as at old_at: parity
    holds, and the old run's log shows the stand-in ran through the link."""
    k = _kit(s)
    ran = s.run(["python3", str(k / "tests" / "parity" / "lever.py"), "needs"], cwd=k)
    assert "defect: none  old: pass (exit 0)  new: pass (exit 0)" in ran.out, ran
    assert "parity holds" in ran.out, ran
    assert "stub ran" in _log(ran.out, "none.old.log"), ran


def network_unreached(s: Scratch) -> None:
    """The old and new tests connect to a listener on the caller's loopback: both fail, and the
    listener holds no connection from either."""
    k = _kit(s)
    with socket.create_server(("127.0.0.1", 0)) as srv:
        port = str(srv.getsockname()[1])
        lever = ["python3", str(k / "tests" / "parity" / "lever.py"), "net"]
        ran = s.run(lever, cwd=k, env={"PROBE_PORT": port}, want=1)
        srv.settimeout(0)
        reached = 0
        while True:
            try:
                srv.accept()[0].close()
            except OSError:  # none pending
                break
            reached += 1
    assert "defect: none  old: FAIL (exit 1)  new: FAIL (exit 1)" in ran.out, ran
    assert reached == 0, f"{reached} connection(s) reached the caller's loopback: {ran}"
    for side in ("old", "new"):
        log = _log(ran.out, f"none.{side}.log")
        assert "Connection refused" in log, log  # it tried, and found no listener
        assert "probe: reached" not in log, log


if __name__ == "__main__":
    main(needs_as_git_holds, network_unreached)
