"""The qc sandbox run by hand on anthropics/sandbox-runtime (srt; octo-feather-qc-sandbox
--help, docs/adr/0022 the sandbox paragraph), no model: `octo-feather-qc-sandbox -- CMD` in a
repo, every input defaulted, prints its pre-run proof naming srt, and CMD's escapes fail (a
write to HOME, an umount of a mask, a live Herdr session through the shim) and leave nothing
(its worktree write discarded, listed in the upper record); without srt in the kit's
node_modules (no pnpm install yet), it refuses before any judge, naming the install command; the
network: a run with no Pi reaches no host, a Pi run only the hosts of Pi's models.json (here a
local provider, through srt's proxy), an allowed host never an attempt; a refused host is one
attempt-record entry; the judge's stdio stays blocking; every process the run starts is reaped
within it; run by hand inside a qc sandbox (nested), its proof passes."""

from __future__ import annotations

import ctypes
import http.server
import json
import os
import re
import select
import shutil
import signal
import subprocess
import threading
import time
from typing import TYPE_CHECKING

from testkit import ROOT, Scratch, kit, main, tool_homes

if TYPE_CHECKING:
    from pathlib import Path

SRT = "qc sandbox: ok   judge runs in the srt sandbox (@anthropic-ai/sandbox-runtime "


def repo(s: Scratch) -> Path:
    r = s.root / "repo"
    r.mkdir()
    s.git(r, "init", "-q", "-b", "main")
    (r / "README").write_text("x\n")
    s.git(r, "add", "-A")
    s.git(r, "commit", "-qm", "init")
    (s.home / ".config" / "herdr").mkdir(parents=True)
    return r


def by_hand(s: Scratch) -> None:
    r = repo(s)
    cmd = (
        'touch "$HOME/x"; echo "touch $?"; umount "$HOME/.config/herdr"; echo "umount $?"; '
        'herdr --session default workspace list; echo w > newfile; echo "wrote $?"'
    )
    ran = s.run([kit("octo-feather-qc-sandbox"), "--", "sh", "-c", cmd], cwd=r, env=tool_homes())
    assert SRT in ran.err, ran.err
    for want in ("touch 1", "umount 32", "wrote 0"):
        assert want in ran.out, (want, ran.out)
    assert "FAIL" not in ran.err, ran.err
    assert '{"upper": [["new", "newfile"]]}' in ran.err, ran.err
    assert not (s.home / "x").exists()
    assert not (r / "newfile").exists()
    assert s.git(r, "status", "--porcelain") == ""


def srt_missing(s: Scratch) -> None:
    """A kit checkout whose node_modules lacks srt (no `pnpm install` yet): refused before any
    judge, naming the package.json pin and the install command."""
    r = repo(s)
    k = s.root / "kit"
    shutil.copytree(ROOT / "scripts", k / "scripts", symlinks=True)
    shutil.copy(ROOT / "package.json", k)
    ran = s.run(
        [str(k / "scripts" / "octo-feather-qc-sandbox"), "--", "true"],
        cwd=r,
        want=66,
        env=tool_homes(),
    )
    for want in (
        "qc sandbox: FAIL srt (@anthropic-ai/sandbox-runtime ",
        f"not installed in {k}/node_modules (found: none)",
        f"run pnpm install --frozen-lockfile --dir {k}",
        "judge not started (exit 66)",
    ):
        assert want in ran.err, (want, ran.err)


def refused_host(s: Scratch) -> None:
    """A host outside the allowlist, asked for twice: srt refuses it, and the attempt record holds
    exactly one entry for it (kind network, refused, naming the host and srt's reason)."""
    r = repo(s)
    py = (
        "import urllib.request\n"
        "for _ in range(2):\n"
        "    try: urllib.request.urlopen('http://blocked.invalid/', timeout=5)\n"
        "    except Exception as e: print('refused', e)\n"
    )
    ran = s.run(
        [kit("octo-feather-qc-sandbox"), "--", "python3", "-c", py], cwd=r, env=tool_homes()
    )
    assert ran.out.count("refused") == 2, ran.out
    rec = next(ln for ln in ran.err.splitlines() if ln.startswith('qc sandbox: record {"attempts"'))
    got = [a for a in json.loads(rec.split("record ", 1)[1])["attempts"] if a["kind"] == "network"]
    assert len(got) == 1, got
    assert got[0]["attempt"] is True, got
    assert got[0]["refused"] is True, got
    assert got[0]["what"] == "connect blocked.invalid:80", got
    assert got[0]["result"].startswith("srt refused: "), got


def blocking_stdio(s: Scratch) -> None:
    """The judge's stdin, stdout and stderr stay blocking (srt's Node never holds them: it would
    set O_NONBLOCK on the open file description itself), so a burst written into a pipe its reader
    drains late completes: 4 MB, read only after a pause."""
    r = repo(s)
    # A refused host first: srt's Node then writes (its violation line), as a Herdr server's
    # update check makes it on the box.
    py = (
        "import fcntl, os, sys, time, urllib.request\n"
        "try: urllib.request.urlopen('http://blocked.invalid/', timeout=5)\n"
        "except Exception: pass\n"
        "time.sleep(1)\n"
        "nb = [bool(fcntl.fcntl(f, fcntl.F_GETFL) & os.O_NONBLOCK) for f in (0, 1, 2)]\n"
        "print('nonblock', nb, file=sys.stderr, flush=True)\n"
        "sys.stdout.buffer.write(b'x' * 4_000_000)\n"
        "sys.stdout.flush()\n"
    )
    p = subprocess.Popen(
        [kit("octo-feather-qc-sandbox"), "--", "python3", "-c", py],
        cwd=r,
        env={**s.env, **tool_homes()},
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(2)  # the judge fills the pipe first
    out, err = p.communicate(timeout=120)
    e = err.decode(errors="replace")
    assert p.returncode == 0, e
    assert "nonblock [False, False, False]" in e, e
    assert len(out) == 4_000_000, (len(out), e)


def reaped(s: Scratch) -> None:
    """Every process the run starts is reaped within it (none left to its caller), so the caller's
    CPU count (getrusage of its children) holds the whole run: the caller made a child subreaper,
    after the run no orphan of it is reparented there."""
    r = repo(s)
    ctypes.CDLL(None).prctl(36, 1, 0, 0, 0)  # PR_SET_CHILD_SUBREAPER
    ran = s.run([kit("octo-feather-qc-sandbox"), "--", "true"], cwd=r, env=tool_homes())
    assert SRT in ran.err, ran.err
    assert "qc sandbox: FAIL" not in ran.err, ran.err
    try:
        pid, _ = os.waitpid(-1, os.WNOHANG)
    except ChildProcessError:
        return
    raise AssertionError(f"run left an owned child to its caller (0 means still live): {pid}")


def live_survivor(s: Scratch) -> None:
    """Real bwrap still runs; its wrapper leaves a live owned child outside its PID namespace."""
    r = repo(s)
    ctypes.CDLL(None).prctl(36, 1, 0, 0, 0)
    real = shutil.which("bwrap")
    assert real is not None
    pidfile = s.bin / "survivor.pid"
    wrapper = s.bin / "bwrap"
    # srt 0.0.81 linux-sandbox-utils.js:3039 adds --unshare-pid to the actual launch,
    # not the dependency/version probes. Delegate every argument to the real installed binary.
    wrapper.write_text(
        "#!/usr/bin/env python3\n"
        "import os, sys, time\n"
        "if '--unshare-pid' in sys.argv and os.fork() == 0:\n"
        "    os.setsid()\n"
        "    for fd in (0, 1, 2):\n"
        "        os.dup2(os.open('/dev/null', os.O_RDWR), fd)\n"
        f"    with open({str(pidfile)!r}, 'w') as f: f.write(str(os.getpid()))\n"
        "    time.sleep(120)\n"
        "    os._exit(0)\n"
        f"os.execv({real!r}, [{real!r}, *sys.argv[1:]])\n"
    )
    wrapper.chmod(0o755)
    handle = None
    with (s.root / "stdout").open("w+") as out, (s.root / "stderr").open("w+") as err:
        p = subprocess.Popen(
            [kit("octo-feather-qc-sandbox"), "--", "true"],
            cwd=r,
            env={**s.env, **tool_homes()},
            stdout=out,
            stderr=err,
        )
        try:
            deadline = time.monotonic() + 30
            while not pidfile.exists() and p.poll() is None and time.monotonic() < deadline:
                time.sleep(0.01)
            assert pidfile.exists(), "actual bwrap launch did not start the survivor"
            pid = int(pidfile.read_text())
            handle = os.pidfd_open(pid)
            poll = select.poll()
            poll.register(handle, select.POLLIN)
            assert not poll.poll(0), "survivor already exited before launcher deadline"
            assert p.poll() is None, "launcher exited before live-child observation"
            print(f"START live owned survivor pid={pid}; launcher={p.pid}", flush=True)
            rc = p.wait(timeout=30)
            out.seek(0)
            err.seek(0)
            proof = err.read()
            print(f"PRODUCT launcher rc={rc}", flush=True)
            print(proof, flush=True)
            assert SRT in proof, proof
            assert rc == 66, (rc, proof)
            records = [
                json.loads(ln.split("record ", 1)[1])
                for ln in proof.splitlines()
                if ln.startswith("qc sandbox: record ")
            ]
            survivors = [v for rec in records for v in rec.get("orphans_left", [])]
            assert any(v.startswith(f"{pid} ") for v in survivors), (pid, survivors, proof)
            assert poll.poll(0), "owned survivor was not terminated"
            try:
                adopted, _ = os.waitpid(-1, os.WNOHANG)
            except ChildProcessError:
                pass
            else:
                raise AssertionError(f"launcher failed complete reaping: {adopted}")
        finally:
            try:
                if handle is not None:
                    try:
                        signal.pidfd_send_signal(handle, signal.SIGKILL)
                        print("CLEANUP fixture: SIGKILL sent through owned pidfd", flush=True)
                    except ProcessLookupError:
                        print("CLEANUP fixture: owned pidfd already exited", flush=True)
                    finally:
                        os.close(handle)
            finally:
                try:
                    if p.poll() is None:
                        p.kill()
                    print(f"CLEANUP fixture: launcher waited rc={p.wait()}", flush=True)
                finally:
                    while True:
                        try:
                            adopted, status = os.waitpid(-1, 0)
                            print(
                                f"CLEANUP fixture: reaped owned child={adopted} status={status}",
                                flush=True,
                            )
                        except ChildProcessError:
                            print("CLEANUP fixture: all owned children reaped (ECHILD)", flush=True)
                            break


def nested(s: Scratch) -> None:
    """The by-hand run inside a qc sandbox (a nested run, as a demo of the kit judging itself runs
    it): the inner proof passes, its live-record masks holding though the outer run's state dir is
    its caller's (none shows an entry)."""
    r = repo(s)
    sb = kit("octo-feather-qc-sandbox")
    ident = "-c user.name=t -c user.email=t@t"
    repo2 = f'cd "$(mktemp -d)" && git init -q && git {ident} commit -q --allow-empty -m x'
    inner = f"{repo2} && {sb} -- echo inner-ran"
    ran = s.run([sb, "--", "sh", "-c", inner], cwd=r, env=tool_homes())
    assert "inner-ran" in ran.out, (ran.out, ran.err)
    assert "qc sandbox: FAIL" not in ran.err, ran.err
    masked = re.findall(
        r"live records masked \((\d+) paths, (\d+) bytes or entries visible\)", ran.err
    )
    assert len(masked) == 2, ran.err  # the outer proof's line, then the inner's
    assert all(v == "0" for _, v in masked), masked


class _Ok(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"provider")

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002  # the base class's own name
        pass


def network(s: Scratch) -> None:
    r = repo(s)
    srv = http.server.HTTPServer(("127.0.0.1", 0), _Ok)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{srv.server_address[1]}/v1"
    pi = s.home / ".pi" / "agent"
    pi.mkdir(parents=True)
    (pi / "models.json").write_text(
        json.dumps({"providers": {"p": {"baseUrl": url, "apiKey": "k"}}})
    )
    py = f'import urllib.request; print(urllib.request.urlopen("{url}", timeout=5).read().decode())'
    get = f"python3 -c '{py}' 2>&1 | tail -1"
    sb = [kit("octo-feather-qc-sandbox"), "--", "sh", "-c", get]
    none = s.run(sb, cwd=r, env=tool_homes())  # by hand: no Pi, so no host at all
    assert "network allowlist: none" in none.err, none.err
    assert "provider" not in none.out, none.out
    host = url.split("/")[2]
    piran = s.run(sb, cwd=r, env=tool_homes() | {"QC_PI": ""})
    assert f"network allowlist: {host}" in piran.err, piran.err
    assert piran.out == "provider", (piran.out, piran.err)
    assert '"kind": "network"' not in piran.err, piran.err  # an allowed host is no attempt
    srv.shutdown()


if __name__ == "__main__":
    main(by_hand, srt_missing, network, nested, refused_host, blocking_stdio, reaped, live_survivor)
