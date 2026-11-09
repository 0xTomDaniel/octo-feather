"""The scenarios of tests/gate/kit/test_qc_capture.py (its items), this file their command
(testkit.main): qc capture (quality spec #qc-capture, #qc-judgment, #qc-results) through
octo-feather-qc (what `just qc` runs) and octo-feather-evidence read, with the testkit's fake
herdr and no model: a scratch target whose qc.toml declares a passing and a failing demo is
judged twice at one head. Each run appends one evidence record per demo at that head (command,
exit status, output, criterion text hash, contract version) and names it; both runs give pass and
fail, evidence complete, decision source the demo's checks (#acceptance-qc-capture,
#acceptance-qc-same-verdict). A criterion with no declared demo goes to the agent fallback (the
stub judge tests/fixtures/qc-judge/pi), alone in its brief, its result labelled agent fallback
with its own record (tests/gate/kit/test_qc_fallback.py). An invalid demo declaration is refused
before anything runs. The target with its two demos is prepared once per gate run (build)."""

from __future__ import annotations

import contextlib
import hashlib
import json
import re
import secrets
import select
import signal
import socket
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from testkit import FIXTURES, Ran, Scratch, kit, main
from testkit.qc import RID, STATUS, block, clean, qc, report, target

CONTRACT = """format = 1
[entry]
command = "true"
[services]
[fixture]
[values]
[demo."demo#acceptance-a"]
command = 'echo "a checks pass in $QC_REPO"'
covers = ["src/a"]
tests = ["tests/a.sh"]
"""
DEMO_B = """[demo."demo#acceptance-b"]
command = "echo b checks fail >&2; exit 3"
covers = ["src/b"]
tests = ["tests/b.sh"]
"""


def build(p: Scratch) -> None:
    target(p, {"qc.toml": CONTRACT + DEMO_B})


def world(s: Scratch) -> tuple[Path, str]:
    s.prepare("qc-capture", build)
    clean(s)
    r = s.root / "repo"
    return r, s.git(r, "rev-parse", "HEAD")


def contract(s: Scratch, r: Path, text: str, what: str) -> None:
    (r / "qc.toml").write_text(text)
    s.git(r, "commit", "-qam", f"contract {what}")


def judged(s: Scratch, r: Path, want: int) -> Ran:
    return qc(s, r, "9", "acceptance-a", "acceptance-b", want=want)


def record(lines: list[str], why: str) -> str:
    """The record id a result block's evidence line names, its decision WHY."""
    rx = rf"^  evidence complete; decision {why}; record ({RID})$"
    m = next((m for ln in lines[1:] if (m := re.match(rx, ln))), None)
    assert m, f"no '{why}' evidence line naming a record: {lines}"
    return m.group(1)


def evidence(s: Scratch, r: Path, *args: str) -> list[dict[str, Any]]:
    out = s.run([kit("octo-feather-evidence"), "read", "--repo", ".", *args, "--json"], cwd=r).out
    return json.loads(out)


def cancelled_capture(s: Scratch) -> None:
    """Cancel the public capture root while its actual detached descendant is live.

    The descendant hands over its own pidfd before exec sleep. No numeric lookup,
    report-derived liveness or unrelated substitute process establishes cleanup.
    """
    r, _ = world(s)
    observer = s.root / "capture-observer"
    observer.mkdir(mode=0o700)
    address = observer / "sock"
    token = secrets.token_hex(24)
    sleeper = (
        "import os,socket,sys; "
        "c=socket.socket(socket.AF_UNIX,socket.SOCK_SEQPACKET); "
        "c.connect(sys.argv[1]); f=os.pidfd_open(os.getpid()); "
        "socket.send_fds(c,[sys.argv[2].encode()],[f]); "
        "assert c.recv(1)==b'!'; c.close(); os.close(f); "
        "os.execvp('sleep',['sleep','300'])"
    )
    payload = (
        "import subprocess,sys; "
        "p=subprocess.Popen([sys.executable,'-c',sys.argv[1],*sys.argv[2:]],"
        "start_new_session=True); p.wait()"
    )
    handle = None
    with socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET) as listener, tempfile.TemporaryFile() as log:
        listener.bind(str(address))
        listener.listen(1)
        listener.settimeout(30)
        p = subprocess.Popen(
            [kit("octo-feather-qc"), "--capture-case", str(s.root / "capture.json"),
             "--", sys.executable, "-c", payload, sleeper, str(address), token],
            cwd=r, env={**s.env, "OCTO_FEATHER_QC_RO_BINDS": str(observer)},
            stdout=log, stderr=log, start_new_session=True,
        )
        try:
            with listener.accept()[0] as peer:
                peer.settimeout(30)
                message, handles, flags, _ = socket.recv_fds(peer, 4096, 1)
                if handles:
                    handle = handles[0]
                assert len(handles) == 1 and not flags & (socket.MSG_TRUNC | socket.MSG_CTRUNC)
                assert message.decode() == token
                live = select.poll()
                live.register(handle, select.POLLIN)
                assert not live.poll(0), "actual capture descendant not live before cancellation"
                peer.sendall(b"!")
            # The actual root is still unreaped; signal ONLY it, not the descendant
            # session or the launcher's group. Product cancellation must clean those.
            p.send_signal(signal.SIGTERM)
            rc = p.wait(timeout=15)
            log.seek(0)
            output = log.read().decode(errors="replace")
            assert rc != 0, output
            assert live.poll(5000), f"actual detached capture descendant survived: {output}"
            assert not list((s.root / "tmp").iterdir()), output
        finally:
            try:
                if handle is not None:
                    try:
                        with contextlib.suppress(ProcessLookupError):
                            signal.pidfd_send_signal(handle, signal.SIGKILL)
                        dead = select.poll()
                        dead.register(handle, select.POLLIN)
                        assert dead.poll(5000), "owned capture descendant cleanup failed"
                    finally:
                        os.close(handle)
            finally:
                # Retain the root until bounded graceful cleanup, then escalate.
                if p.returncode is None:
                    p.terminate()
                    try:
                        p.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        p.kill()
                        p.wait(timeout=10)


def twice(s: Scratch) -> None:
    """Two runs at one head: each gives PASS acceptance-a and FAIL acceptance-b from the demos'
    checks, evidence complete, each naming its record; no judge started; a's status commit (built,
    its record, commit, tests; b planned); the report's results. Four distinct records, each read
    back through the store's command: at the head, clean, the demo's command, exit status and
    output, the criterion text's hash (the fixture spec's text, a worked literal), the contract's
    format and the hash of its bytes."""
    r, head = world(s)
    ids: list[str] = []
    for n in (1, 2):
        s.git(r, "reset", "-q", "--hard", head)
        q = judged(s, r, 1)
        a = record(
            block(q.out, 'PASS acceptance-a: $ echo "a checks pass in $QC_REPO"'),
            "demo checks",
        )
        b = record(
            block(q.out, "FAIL acceptance-b: $ echo b checks fail >&2; exit 3"), "demo checks"
        )
        assert (
            block(q.out, "PASS acceptance-a: ")[0]
            == 'PASS acceptance-a: $ echo "a checks pass in $QC_REPO"'
        ), q.out
        assert (
            block(q.out, "FAIL acceptance-b: ")[0]
            == "FAIL acceptance-b: $ echo b checks fail >&2; exit 3"
        ), q.out
        assert not re.search("pi-role|qc-judge", q.err), f"run {n}: a judge started: {q.err}"
        ids += [a, b]
        assert (
            s.git(r, "log", "-1", "--format=%s") == f"qc: built acceptance-a (judged {head[:12]})"
        )
        c = json.loads(s.git(r, "show", f"HEAD:{STATUS}"))["criteria"]
        built = {"status": "built", "pr": 9, "record": a, "commit": head, "tests": ["tests/a.sh"]}
        assert c["acceptance-a"] == built, c
        assert c["acceptance-b"] == {"status": "planned", "pr": None}, c
        res = {x["id"]: x for x in report(q)["results"]}
        assert sorted(res) == ["acceptance-a", "acceptance-b"], res
        for i, v, rec in (("acceptance-a", "pass", a), ("acceptance-b", "fail", b)):
            x = res[i]
            got = (x["verdict"], x["evidence"], x["decision"], x["record"], x["head"])
            assert got == (v, "complete", "demo checks", rec, head), x
    assert len(set(ids)) == 4, f"two runs must append four distinct records: {ids}"
    recs = {x["record"]["id"]: x for x in evidence(s, r, "--commit", head)}
    assert sorted(recs) == sorted(ids), (sorted(recs), ids)
    csha = hashlib.sha256((r / "qc.toml").read_bytes()).hexdigest()
    want = {
        "demo#acceptance-a": (
            "Given a user, When acceptance-a runs, then it prints ok.",
            'echo "a checks pass in $QC_REPO"',
            "0",
            f"a checks pass in {r}\n",
            "",
        ),
        "demo#acceptance-b": (
            "Given a user, When acceptance-b runs, then it prints ok.",
            "echo b checks fail >&2; exit 3",
            "3",
            "",
            "b checks fail\n",
        ),
    }
    for x in recs.values():
        rec, out = x["record"], Path(x["dir"]) / "outputs"
        text, cmd, code, so, se = want[rec["criterion"]["id"]]
        assert rec["revision"] == head and rec["dirty"] is False, rec  # noqa: PT018
        assert rec["criterion"]["text_sha256"] == hashlib.sha256(text.encode()).hexdigest(), rec
        assert rec["criterion"]["text_from"] == "spec", rec
        assert rec["contract"] == {"format": 1, "sha256": csha}, rec
        got = {
            n: (out / n).read_text()
            for n in ("demo.cmd", "demo.exit", "demo.stdout", "demo.stderr")
        }
        assert got == {
            "demo.cmd": cmd + "\n",
            "demo.exit": code + "\n",
            "demo.stdout": so,
            "demo.stderr": se,
        }, got


def fallback_beside(s: Scratch) -> None:
    """Only undeclared criteria get the agent fallback: acceptance-b without a demo goes to the
    stub judge alone, acceptance-a is captured; each built entry names its record, the commit it
    was captured at and its demo's tests: none for the fallback's (#acceptance-built-links)."""
    r, _ = world(s)
    contract(s, r, CONTRACT, "one demo")
    h = s.git(r, "rev-parse", "HEAD")
    q = qc(
        s,
        r,
        "9",
        "acceptance-a",
        "acceptance-b",
        want=0,
        env={"OCTO_FEATHER_QC_PATH": str(FIXTURES / "qc-judge")},
    )
    a = record(block(q.out, "PASS acceptance-a: "), "demo checks")
    bl = block(q.out, "PASS acceptance-b: ")
    assert bl, q.out
    assert bl[0] == "PASS acceptance-b: $ judge acceptance-b", q.out
    b = record(bl, "agent fallback")
    c = json.loads(s.git(r, "show", f"HEAD:{STATUS}"))["criteria"]
    assert c["acceptance-a"] == {
        "status": "built",
        "pr": 9,
        "record": a,
        "commit": h,
        "tests": ["tests/a.sh"],
    }, c
    assert c["acceptance-b"] == {
        "status": "built",
        "pr": 9,
        "record": b,
        "commit": h,
        "tests": [],
    }, c
    lines = report(q)["fallback"]["acceptance-b"]["stdout"].splitlines()
    brief = [ln for ln in lines if ln.startswith("BRIEF ")]
    assert brief == [
        "BRIEF - acceptance-b: Given a user, When acceptance-b runs, then it prints ok."
    ], f"the judge's brief named the demo's criterion: {lines}"


def invalid_demo(s: Scratch) -> None:
    """An invalid demo declaration (a demo without covers or tests): refused naming the problem, no
    demo run, no record appended."""
    r, _ = world(s)
    contract(
        s, r, CONTRACT + '[demo."demo#acceptance-b"]\ncommand = "true"\n', "demo without covers"
    )
    before = len(evidence(s, r))
    q = judged(s, r, 64)
    assert "qc.toml is not a valid contract" in q.err, q.err
    assert "demo.demo#acceptance-b: missing covers" in q.err, q.err
    assert "qc: demo " not in q.err, f"a demo ran: {q.err}"
    assert len(evidence(s, r)) == before, "invalid contract: a record was appended"


if __name__ == "__main__":
    main(twice, fallback_beside, invalid_demo, cancelled_capture)
