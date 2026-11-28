"""tests/parity/lever.py, run as a command on a scratch kit of a few files (tickets #1361, #1368,
seam `rule: tests/parity/lever.py` agreed on it before any test), as scenarios (testkit.main).

The scratch kit is a git repo holding the lever (copied: it finds its kit beside itself), a
justfile whose `test` recipe runs the one test it is given (a pytest one under the gate's
tests/gate/heavy_slot.py, a gate-budget.toml of one fast-run turn, on GATE_WORKERS xdist workers,
as check-tests runs it), and three cases. Its first commit
(old_at) holds an old test, its executable stand-in and a symlink to it; the next drops them.
`needs`: the restored old side sees the stand-in executable and the link a link, as git holds
them at old_at, and parity holds. `net`: the old and new tests connect to a listener on the
caller's loopback; both fail, and the listener counts no connection. `pyt`: a pytest old item and
new file, run with --background while the box's one fast-run turn is held and MemAvailable reads
under the floor (a file bound over /proc/meminfo by bwrap, the reading the box's kernel gives).
"""

from __future__ import annotations

import fcntl
import re
import shutil
import socket
import subprocess
import time
from pathlib import Path

from testkit import ROOT, Scratch, main

JUSTFILE = r"""set positional-arguments

# The one test named (a gate item id tests/gate/test_gate.py::test_script[F] stands for F), run:
# a pytest one by pytest.
test *args:
    #!/usr/bin/env bash
    for a in "$@"; do [[ $a == -* ]] || id="$a"; done
    [[ $id =~ \[(.*)\]$ ]] && id="${BASH_REMATCH[1]}"
    [[ $id == *.py* ]] || exec "./$id"
    exec python3 -m pytest -p tests.gate.heavy_slot -p no:cacheprovider -n "${GATE_WORKERS:-8}" "$@"
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
TEST = "def test_ok() -> None:\n    pass\n"
BUDGET = "fast_workers = 3\nfast_runs = 1\n"
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
    _write(k / "tests" / "test_old.py", TEST)
    _write(k / "tests" / "test_new.py", TEST)
    _write(k / "gate-budget.toml", BUDGET)
    _write(k / "tests" / "gate" / "heavy_slot.py", (ROOT / "tests/gate/heavy_slot.py").read_text())
    s.git(k, "add", "-A")
    s.git(k, "commit", "-qm", "old")
    old_at = s.git(k, "rev-parse", "HEAD")
    s.git(k, "rm", "-rq", "tests/old.sh", "tests/fixtures")
    _write(k / "tests" / "new.sh", NEW, 0o755)
    for name, old, needs, new in (
        ("needs", "tests/old.sh", '["tests/fixtures/lever"]', "tests/new.sh"),
        ("net", "tests/probe.sh", "[]", "tests/probe.sh"),
        ("pyt", "tests/test_old.py::test_ok", "[]", "tests/test_new.py"),
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


def _meminfo(f: Path, gib: int) -> None:
    f.write_text(f"MemTotal: {16 * 2**20} kB\nMemAvailable: {gib * 2**20} kB\n")


def _lever_proc(root: int) -> int:
    """The lever's pid among ROOT's descendants: python3 running lever.py (bwrap's child)."""
    todo = [root]
    while todo:
        pid = todo.pop()
        argv = Path(f"/proc/{pid}/cmdline").read_bytes().split(b"\0")
        if argv[0].endswith(b"python3") and argv[1].endswith(b"lever.py"):
            return pid
        for t in Path(f"/proc/{pid}/task").iterdir():
            todo += [int(c) for c in (t / "children").read_text().split()]
    msg = f"no lever.py under pid {root}"
    raise AssertionError(msg)


def background_run(s: Scratch) -> None:
    """--background with the box's one fast-run turn held and MemAvailable 1 GiB: the lever waits,
    printing the wait, at nice 19 and idle IO; once MemAvailable reads 8 GiB it runs, each run a
    fast-tier one of one process taking no turn and waiting for none, and parity holds."""
    k = _kit(s)
    slots = s.home / ".local" / "state" / "octo-feather" / "slots"
    slots.mkdir(parents=True)
    mem = s.root / "meminfo"
    _meminfo(mem, 1)
    lever = ["python3", str(k / "tests" / "parity" / "lever.py"), "--background", "pyt"]
    bind = ["bwrap", "--dev-bind", "/", "/", "--bind", str(mem), "/proc/meminfo", "--"]
    with (slots / "fast-0.lock").open("a") as turn:
        fcntl.flock(turn, fcntl.LOCK_EX | fcntl.LOCK_NB)  # the box's one turn, held
        p = subprocess.Popen([*bind, *lever], cwd=k, env=s.env, stdout=subprocess.PIPE, text=True)
        assert p.stdout is not None
        out = ""
        while "lever: memory: waiting from" not in out:
            line = p.stdout.readline()
            assert line, f"the lever ended before waiting: {out}"
            out += line
        lever_pid = _lever_proc(p.pid)
        nice = int(Path(f"/proc/{lever_pid}/stat").read_text().rsplit(")", 1)[1].split()[16])
        ionice = ["ionice", "-p", str(lever_pid)]
        io = subprocess.run(ionice, capture_output=True, text=True, check=True)
        time.sleep(1)
        _meminfo(mem, 8)
        rest, _ = p.communicate(timeout=120)
        out += rest
    assert p.returncode == 0, out
    assert (nice, io.stdout.strip()) == (19, "idle"), (nice, io.stdout)
    assert "MemAvailable 1.0 GiB, under the floor 3 GiB" in out, out
    assert "lever: memory: wait ended " in out, out
    assert "MemAvailable 8.0 GiB, the floor 3 GiB" in out, out
    assert "defect: none  old: pass (exit 0)  new: pass (exit 0)" in out, out
    for side in ("old", "new"):
        log = _log(out, f"none.{side}.log")
        assert "heavy slot: not needed: fast tier, 1 worker (cap 3)" in log, log
        assert "fast tier: waiting my turn" not in log, log
    assert sorted(f.name for f in slots.iterdir()) == ["fast-0.lock"], "a record left or a turn"


if __name__ == "__main__":
    main(needs_as_git_holds, network_unreached, background_run)
