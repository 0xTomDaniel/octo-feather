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
import sys
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
    message = f"run left an owned child to its caller (0 means still live): {pid}"
    raise AssertionError(message)


def _cleanup_survivor(handle: int | None, p: subprocess.Popen[bytes]) -> None:
    """Release this scenario's retained child pidfd and wait only its owned children."""
    try:
        if handle is not None:
            try:
                signal.pidfd_send_signal(handle, signal.SIGKILL)
                sys.stdout.write("CLEANUP fixture: SIGKILL sent through owned pidfd\n")
                sys.stdout.flush()
            except ProcessLookupError:
                sys.stdout.write("CLEANUP fixture: owned pidfd already exited\n")
                sys.stdout.flush()
            finally:
                os.close(handle)
    finally:
        try:
            if p.poll() is None:
                p.kill()
            sys.stdout.write(f"CLEANUP fixture: launcher waited rc={p.wait()}\n")
            sys.stdout.flush()
        finally:
            try:
                while True:
                    adopted, status = os.waitpid(-1, 0)
                    sys.stdout.write(
                        f"CLEANUP fixture: reaped owned child={adopted} status={status}\n"
                    )
                    sys.stdout.flush()
            except ChildProcessError:
                sys.stdout.write("CLEANUP fixture: all owned children reaped (ECHILD)\n")
                sys.stdout.flush()


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
            sys.stdout.write(f"START live owned survivor pid={pid}; launcher={p.pid}\n")
            sys.stdout.flush()
            rc = p.wait(timeout=30)
            out.seek(0)
            err.seek(0)
            proof = err.read()
            sys.stdout.write(f"PRODUCT launcher rc={rc}\n{proof}\n")
            sys.stdout.flush()
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
                message = f"launcher failed complete reaping: {adopted}"
                raise AssertionError(message)
        finally:
            _cleanup_survivor(handle, p)


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


def _cancel_changed(text: str, before: str, after: str) -> str:
    assert text.count(before) == 1, "cancellation fixture source drift"
    return text.replace(before, after)


def _h_signals():
    """Defer interrupts through Popen's unassigned interval AND cleanup/reporting."""
    pending = []
    saved = {s: signal.getsignal(s) for s in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)}
    def mark(n, _frame):
        pending.append(n)
    for s in saved:
        signal.signal(s, mark)
    return pending, saved


def _h_restore(saved):
    primary = None
    for s, handler in saved.items():
        try:
            signal.signal(s, handler)
        except BaseException as error:
            primary = _h_first(primary,error,"handler restoration")
    if primary is not None:
        raise primary


def _h_subreaper():
    import ctypes
    if ctypes.CDLL(None, use_errno=True).prctl(36, 1, 0, 0, 0) != 0:
        raise OSError(ctypes.get_errno(), 'test owned-child subreaper unavailable')


def _h_drain(end):
    """Existing owned-subtree mechanism, never process-group/foreign PID discovery."""
    from pathlib import Path
    forced = False
    waits = []
    while True:
        try:
            pid, status = os.waitpid(-1, os.WNOHANG)
        except ChildProcessError:
            return True, forced, waits
        if pid:
            waits.append([pid, status])  # raw actual wait, not fabricated Popen.returncode
            continue
        children = set()
        for tid in os.listdir('/proc/self/task'):
            try:
                children.update(map(int, Path('/proc/self/task', tid, 'children').read_text().split()))
            except FileNotFoundError:
                if tid == str(os.getpid()):
                    raise
        for child in children:
            fd = os.pidfd_open(child)  # own unreaped child; this scope alone waits
            try:
                try:
                    signal.pidfd_send_signal(fd, signal.SIGKILL)
                    forced = True
                except ProcessLookupError:
                    pass
            finally:
                os.close(fd)
        if time.monotonic() >= end:
            return False, forced, waits
        time.sleep(min(.01, max(0, end-time.monotonic())))


def _h_cleanup(p, fd, end):
    errors = []
    forced = False
    if p is not None and p.returncode is None:
        forced = True
        try:
            if fd is not None:
                signal.pidfd_send_signal(fd, signal.SIGKILL)
            else:
                # Direct child still unreaped: failed enrollment, not PID discovery.
                os.kill(p.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        except BaseException as error:
            errors.append('root stop: '+str(error))
        try:
            p.wait(timeout=max(0, end-time.monotonic()))
        except BaseException as error:
            errors.append('root wait: '+str(error))
    try:
        complete, descendants_forced, waits = _h_drain(end)
        forced = forced or descendants_forced
    except BaseException as error:
        complete, waits = False, []
        errors.append('owned drain: '+str(error))
    if fd is not None:
        try:
            os.close(fd)
        except BaseException as error:
            errors.append('pidfd close: '+str(error))
    return {'forced': forced, 'complete': complete and not errors, 'errors': errors, 'raw_adopted_waits': waits}


def _h_text(error):
    return None if error is None else f'{type(error).__name__}: {error}'


def _h_first(primary,error,stage):
    if primary is None:
        error.add_note('first failure stage: '+stage)
        return error
    primary.add_note(f'secondary {stage}: {type(error).__name__}: {error}')
    for note in getattr(error,'__notes__',[]):
        primary.add_note(note)
    return primary


def _h_cleanup_attempt(p,fd,end,primary):
    try:
        cleanup=_h_cleanup(p,fd,end)
    except BaseException as error:
        primary=_h_first(primary,error,'owned cleanup')
        cleanup={'forced':None,'complete':False,'errors':['owned cleanup unproved'],'raw_adopted_waits':[]}
    if not cleanup['complete'] or cleanup['forced']:
        primary=_h_first(primary,RuntimeError(str(cleanup)),'owned cleanup disposition')
    return cleanup,primary


def _h_publish(path,result,primary,saved):
    # Serialization, write, close and restoration are separate secondary attempts.
    stream=None
    if path is not None:
        try:
            stream=path.open('x')
        except BaseException as error:
            primary=_h_first(primary,error,'terminal open')
        if stream is not None:
            try:
                json.dump(result,stream,indent=2)
            except BaseException as error:
                primary=_h_first(primary,error,'terminal serialization/write')
            try:
                stream.close()
            except BaseException as error:
                primary=_h_first(primary,error,'terminal close')
    try:
        _h_restore(saved)
    except BaseException as error:
        primary=_h_first(primary,error,'terminal restoration')
    if primary is not None:
        try:
            sys.stderr.write(_h_text(primary)+'\n'+'\n'.join(getattr(primary,'__notes__',[]))+'\n')
        except BaseException as error:
            primary=_h_first(primary,error,'terminal diagnostics')
        raise primary


def running_cancel(s: Scratch, mode='SIGINT'):
    import ast
    import hashlib
    from pathlib import Path

    KIT = ROOT
    OUT = s.root/'running-cancel'
    assert mode in ('SIGINT','SIGTERM','REPORT_TERM')
    end = time.monotonic() + 150
    OUT.mkdir(mode=0o700)  # exclusive, existing attempts are never reused
    modules = KIT / 'node_modules'
    assert modules.resolve(strict=True) == modules and modules.is_dir()
    sdk = (modules / '@anthropic-ai/sandbox-runtime').resolve(strict=True)
    assert sdk.is_relative_to(modules)
    assert json.loads((sdk / 'package.json').read_text())['version'] == '0.0.81'
    fixture = OUT/'fixture-kit'
    (fixture/'tests/gate/kit/testkit').mkdir(parents=True)
    (fixture/'tests/lib').mkdir(parents=True)
    for name in ('scripts','mise.toml','mise.lock'):
        (fixture/name).symlink_to(KIT/name, target_is_directory=(KIT/name).is_dir())
    (fixture/'tests/fixtures').symlink_to(KIT/'tests/fixtures', target_is_directory=True)
    original_observer = KIT / 'tests/gate/kit/testkit/qc_escape_observer.py'
    observer = original_observer.read_text()
    observer = _cancel_changed(observer,
        '        binds = env.get("OCTO_FEATHER_QC_RO_BINDS", "")',
        '        control = Path(directory) / "tty-input"\n'
        '        os.mkfifo(control, 0o600)\n'
        '        control_fd = os.open(control, os.O_RDWR | os.O_NONBLOCK | os.O_CLOEXEC)\n'
        '        env["QC_CANCEL_TTY_INPUT"] = str(control)\n'
        '        env["QC_CANCEL_ARTIFACTS"] = os.environ["QC_CANCEL_ARTIFACTS"]\n'
        '        binds = env.get("OCTO_FEATHER_QC_RO_BINDS", "")')
    observer = _cancel_changed(observer,
        '                                peer.sendall(b"!" if ready else b"pending")',
        '                                if ready:\n'
        '                                    # This request is still blocked inside the real judge.\n'
        '                                    # The CLI cannot have returned normally past this barrier.\n'
        '                                    assert child.poll() is None\n'
        '                                    print("CANCEL original-three LIVE; public QC ready request still blocked", flush=True)\n'
        '                                    assert os.write(control_fd, b"\\x03") == 1\n'
        '                                    print("CANCEL public TTY input Ctrl-C written", flush=True)\n'
        '                                    stop = time.monotonic() + 15\n'
        '                                    dead = []\n'
        '                                    for name, fd in handles:\n'
        '                                        gone = exited(fd, max(0, stop-time.monotonic()))\n'
        '                                        print(f"CANCEL before harness cleanup {name} pidfd={fd} {\'EXITED\' if gone else \'LIVE\'}", flush=True)\n'
        '                                        dead.append(gone)\n'
        '                                    if not all(dead):\n'
        '                                        raise AssertionError("original actor survived public cancellation BEFORE safety cleanup")\n'
        '                                    # Do not release the held judge into a normal completion.\n'
        '                                    # Its socket may already be gone due to cancellation.\n'
        '                                else:\n'
        '                                    peer.sendall(b"pending")')
    observer = _cancel_changed(observer, '                if failures:\n',
                       '                os.close(control_fd)\n                if failures:\n')
    # Existing observer's normal check remains authoritative and before finally.
    # Its original safety cleanup is not a cancellation witness.
    ast.parse(observer)
    obs = fixture / 'tests/gate/kit/testkit/qc_running_cancel_witness_observer.py'
    with obs.open('x') as f:
        f.write(observer)
    controller = OUT/'public-controller.py'
    with controller.open('x') as f:
        f.write('def _h_signals():\n    """Defer interrupts through Popen\'s unassigned interval AND cleanup/reporting."""\n    pending = []\n    saved = {s: signal.getsignal(s) for s in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)}\n    def mark(n, _frame):\n        pending.append(n)\n    for s in saved:\n        signal.signal(s, mark)\n    return pending, saved\n\n\ndef _h_restore(saved):\n    primary = None\n    for s, handler in saved.items():\n        try:\n            signal.signal(s, handler)\n        except BaseException as error:\n            primary = _h_first(primary,error,"handler restoration")\n    if primary is not None:\n        raise primary\n\n\ndef _h_subreaper():\n    import ctypes\n    if ctypes.CDLL(None, use_errno=True).prctl(36, 1, 0, 0, 0) != 0:\n        raise OSError(ctypes.get_errno(), \'test owned-child subreaper unavailable\')\n\n\ndef _h_drain(end):\n    """Existing owned-subtree mechanism, never process-group/foreign PID discovery."""\n    forced = False\n    waits = []\n    while True:\n        try:\n            pid, status = os.waitpid(-1, os.WNOHANG)\n        except ChildProcessError:\n            return True, forced, waits\n        if pid:\n            waits.append([pid, status])  # raw actual wait, not fabricated Popen.returncode\n            continue\n        children = set()\n        for tid in os.listdir(\'/proc/self/task\'):\n            try:\n                children.update(map(int, Path(\'/proc/self/task\', tid, \'children\').read_text().split()))\n            except FileNotFoundError:\n                if tid == str(os.getpid()):\n                    raise\n        for child in children:\n            fd = os.pidfd_open(child)  # own unreaped child; this scope alone waits\n            try:\n                try:\n                    signal.pidfd_send_signal(fd, signal.SIGKILL)\n                    forced = True\n                except ProcessLookupError:\n                    pass\n            finally:\n                os.close(fd)\n        if time.monotonic() >= end:\n            return False, forced, waits\n        time.sleep(min(.01, max(0, end-time.monotonic())))\n\n\ndef _h_cleanup(p, fd, end):\n    errors = []\n    forced = False\n    if p is not None and p.returncode is None:\n        forced = True\n        try:\n            if fd is not None:\n                signal.pidfd_send_signal(fd, signal.SIGKILL)\n            else:\n                # Direct child still unreaped: failed enrollment, not PID discovery.\n                os.kill(p.pid, signal.SIGKILL)\n        except ProcessLookupError:\n            pass\n        except BaseException as error:\n            errors.append(\'root stop: \'+str(error))\n        try:\n            p.wait(timeout=max(0, end-time.monotonic()))\n        except BaseException as error:\n            errors.append(\'root wait: \'+str(error))\n    try:\n        complete, descendants_forced, waits = _h_drain(end)\n        forced = forced or descendants_forced\n    except BaseException as error:\n        complete, waits = False, []\n        errors.append(\'owned drain: \'+str(error))\n    if fd is not None:\n        try:\n            os.close(fd)\n        except BaseException as error:\n            errors.append(\'pidfd close: \'+str(error))\n    return {\'forced\': forced, \'complete\': complete and not errors, \'errors\': errors, \'raw_adopted_waits\': waits}\n\n\ndef _h_text(error):\n    return None if error is None else f\'{type(error).__name__}: {error}\'\n\n\ndef _h_first(primary,error,stage):\n    if primary is None:\n        error.add_note(\'first failure stage: \'+stage)\n        return error\n    primary.add_note(f\'secondary {stage}: {type(error).__name__}: {error}\')\n    for note in getattr(error,\'__notes__\',[]):\n        primary.add_note(note)\n    return primary\n\n\ndef _h_cleanup_attempt(p,fd,end,primary):\n    try:\n        cleanup=_h_cleanup(p,fd,end)\n    except BaseException as error:\n        primary=_h_first(primary,error,\'owned cleanup\')\n        cleanup={\'forced\':None,\'complete\':False,\'errors\':[\'owned cleanup unproved\'],\'raw_adopted_waits\':[]}\n    if not cleanup[\'complete\'] or cleanup[\'forced\']:\n        primary=_h_first(primary,RuntimeError(str(cleanup)),\'owned cleanup disposition\')\n    return cleanup,primary\n\n\ndef _h_publish(path,result,primary,saved):\n    # Serialization, write, close and restoration are separate secondary attempts.\n    stream=None\n    if path is not None:\n        try:\n            stream=path.open(\'x\')\n        except BaseException as error:\n            primary=_h_first(primary,error,\'terminal open\')\n        if stream is not None:\n            try:\n                json.dump(result,stream,indent=2)\n            except BaseException as error:\n                primary=_h_first(primary,error,\'terminal serialization/write\')\n            try:\n                stream.close()\n            except BaseException as error:\n                primary=_h_first(primary,error,\'terminal close\')\n    try:\n        _h_restore(saved)\n    except BaseException as error:\n        primary=_h_first(primary,error,\'terminal restoration\')\n    if primary is not None:\n        try:\n            sys.stderr.write(_h_text(primary)+\'\\n\'+\'\\n\'.join(getattr(primary,\'__notes__\',[]))+\'\\n\')\n        except BaseException as error:\n            primary=_h_first(primary,error,\'terminal diagnostics\')\n        raise primary\n\n\nimport os,select,signal,subprocess,sys,time,json\nfrom pathlib import Path\n# Existing direct-child/self-pidfd/adopted-child ownership, no group discovery.\nmode,*argv=sys.argv[1:]\nend=time.monotonic()+float(os.environ[\'QC_TEST_RUN_TIMEOUT\'])\np=None; fd=None; actual=None; primary=None; sent=False; later=False; observed=[]\npending,saved=_h_signals()\ntry:\n    _h_subreaper()\n    control=os.open(os.environ[\'QC_CANCEL_TTY_INPUT\'],os.O_RDWR|os.O_NONBLOCK)\n    try:\n        p=subprocess.Popen(argv,start_new_session=True)\n        fd=os.pidfd_open(p.pid)\n        while actual is None:\n            if pending: raise InterruptedError(\'controller interrupted: \'+str(pending))\n            if time.monotonic()>=end-2: raise TimeoutError(\'public call exceeded owned controller budget\')\n            if mode==\'REPORT_TERM\' and sent and not later:\n                event=os.waitid(os.P_PIDFD,fd,os.WSTOPPED|os.WNOHANG|os.WNOWAIT)\n                if event is not None:\n                    if event.si_code!=os.CLD_STOPPED or event.si_status!=signal.SIGSTOP:\n                        raise AssertionError(\'not the planted reporting-window stop\')\n                    observed.append({\'stage\':\'reporting\',\'si_code\':event.si_code,\'si_status\':event.si_status,\'at_ns\':time.monotonic_ns()})\n                    signal.pidfd_send_signal(fd,signal.SIGTERM)\n                    signal.pidfd_send_signal(fd,signal.SIGCONT)\n                    later=True\n            if select.select([control],[],[],min(.02,max(0,end-2-time.monotonic())))[0]:\n                os.read(control,4096)\n                if not sent:\n                    signal.pidfd_send_signal(fd,signal.SIGTERM)\n                    observed.append({\'stage\':\'original-three-live\',\'at_ns\':time.monotonic_ns()})\n                    sent=True\n            try: actual=p.wait(timeout=min(.02,max(0,end-2-time.monotonic())))\n            except subprocess.TimeoutExpired: pass\n        if mode==\'REPORT_TERM\' and not later:\n            raise AssertionError(\'no independently witnessed later reporting signal\')\n    except BaseException as error:\n        primary=_h_first(primary,error,"controller loop")\n    finally:\n        try:\n            os.close(control)\n        except BaseException as error:\n            primary=_h_first(primary,error,"controller control close")\nexcept BaseException as error:\n    primary=_h_first(primary,error,"controller setup")\nfinally:\n    cleanup,primary=_h_cleanup_attempt(p,fd,end,primary)\n    result={\'actual_public_rc\':actual,\'primary_error\':_h_text(primary),\'pending\':pending,\'windows\':observed,\'cleanup\':cleanup}\n    _h_publish(Path(os.environ[\'QC_CANCEL_ARTIFACTS\'])/\'controller-result.json\',result,primary,saved)\nif primary or pending or cleanup[\'forced\'] or not cleanup[\'complete\']:\n    raise SystemExit(70)\nraise SystemExit(actual if actual is not None and actual>=0 else 70)\n')
    lib = (KIT / 'tests/lib/qc.sh').read_text()
    old = 'bounded() { timeout -k 5 "$lim" "$@" & echo $! > "$t/pids/run"; wait $!; set -- $?; rm -f "$t/pids/run"; return "$1"; }'
    new = '''bounded() {
  local command log actual
  if [[ "${QC_CANCEL_ACTIVE:-}" != 1 ]]; then
    timeout -k 5 "$lim" "$@"; return $?
  fi
  if [[ "$QC_CANCEL_MODE" != SIGINT ]]; then
    /usr/bin/python3 "$QC_CANCEL_CONTROLLER" "$QC_CANCEL_MODE" "$@"; return $?
  fi
  printf -v command '%q ' "$@"
  log="$(mktemp "$QC_CANCEL_ARTIFACTS/tty.XXXXXX")"
  # Only public QC and its descendants get this controlling TTY, not this
  # fixture shell or the authenticated observer. No numeric signal authority.
  timeout --foreground -k 5 "$lim" /usr/bin/script --quiet --return --flush --command "$command" "$log" < "$QC_CANCEL_TTY_INPUT" &
  echo $! > "$t/pids/run"
  wait $!; actual=$?
  printf 'TTY actual waited rc=%s log=%s\\n' "$actual" "$log" >&2
  printf '%s\\n' "$actual" >> "$QC_CANCEL_ARTIFACTS/tty-waited-rcs"
  rm -f "$t/pids/run"
  return "$actual"
}'''
    lib = _cancel_changed(lib, old, new)
    with (fixture / 'tests/lib/qc-running-cancel-witness.sh').open('x') as f:
        f.write(lib)
    case = (KIT / 'tests/qc-escapes.sh').read_text()
    case = _cancel_changed(case, '/gate/kit/testkit/qc_escape_observer.py', '/gate/kit/testkit/qc_running_cancel_witness_observer.py')
    case = _cancel_changed(case, '/lib/qc.sh"', '/lib/qc-running-cancel-witness.sh"')
    marker = 'run 0 escape $st 5 acceptance-a\n'
    assert case.count(marker) == 1
    before, _normal_assertions = case.split(marker)
    # Original normal case is NOT edited/retired. This separate cancellation
    # case keeps its proof-abort prefix and original actor generation intact.
    case = before + '''set +e
expected_head="$(git rev-parse HEAD)"
printf '%s\n' "$expected_head" > "$QC_CANCEL_ARTIFACTS/expected-head"
mkdir "$QC_CANCEL_ARTIFACTS/public-reports"
(
  set -o noclobber
  QC_CANCEL_ACTIVE=1 OCTO_FEATHER_QC_DIR="$QC_CANCEL_ARTIFACTS/public-reports" FAKE_QC=escape bounded "$Q" $st 5 acceptance-a > "$QC_CANCEL_ARTIFACTS/public-invocation.output" 2>&1
); actual=$?
(set -o noclobber; printf '%s\n' "$actual" > "$QC_CANCEL_ARTIFACTS/public-invocation.rc")
out="$(< "$QC_CANCEL_ARTIFACTS/public-invocation.output")"
set -e
/usr/bin/python3 -c 'import time;print(time.monotonic_ns())' > "$QC_CANCEL_ARTIFACTS/public-returned-ns"
printf '%s\\n' "$out"
printf 'CANCEL public terminal waited rc=%s\\n' "$actual"
[[ "$actual" == "$QC_CANCEL_EXPECTED_EXIT" ]] || fail "not a completed public cancellation: $actual"
python3 "$QC_ESCAPE_HELPER" check || fail "same original processes survived public cancellation"
echo 'CANCEL original SAME THREE check completed BEFORE fixture EXIT trap'
# Read the existing operational PUBLIC report, never payload stdout markers.
/usr/bin/python3 - "$QC_CANCEL_ARTIFACTS/public-reports" "$QC_CANCEL_ARTIFACTS/public-sandbox.json" <<'PY_REPORT'
import json,re,sys
from pathlib import Path
files=list(Path(sys.argv[1]).glob('*.json'))
if len(files)!=1:
    raise SystemExit('missing/ambiguous current invocation public report')
report=json.loads(files[0].read_text())
head,run_id=report.get('head'),report.get('run_id')
expected=Path(sys.argv[2]).with_name('expected-head').read_text().strip()
if not re.fullmatch('[0-9a-f]{40}',expected) or head != expected or not isinstance(run_id,str) or not re.fullmatch('[0-9a-f]{6}',run_id) or not re.fullmatch(re.escape(expected)+r'-[0-9]{8}T[0-9]{6}Z-'+re.escape(run_id)+r'[.]json',files[0].name):
    raise SystemExit('unbound public report')
sandbox=report['fallback']['acceptance-a']['sandbox']
if report.get('model') != 'fixture/cancellation-contract' or report.get('ids') != ['acceptance-a'] or set(report.get('fallback',{})) != {'acceptance-a'} or sandbox.get('session') != 'qc-'+expected[:12]+'-'+run_id+'-j0':
    raise SystemExit('public report/session mismatch')
with Path(sys.argv[2]).open('x') as f:
    json.dump(sandbox,f)
PY_REPORT
/usr/bin/python3 - "$QC_CANCEL_ARTIFACTS/public-sandbox.json" "$QC_CANCEL_ARTIFACTS/public-native-witness.json" <<'PY_WITNESS'
import json,os,sys
from pathlib import Path
record=json.loads(Path(sys.argv[1]).read_text())
w=record.get('native_lifecycle')
positive=(isinstance(w,dict) and all(w.get(k) is True for k in ('initialized','signal_acked','payload_exit','reset_completed'))
          and type(w.get('ready')) is int and w['ready'] > 0
          and w.get('owner_forced') is False and w.get('caller_forced') is False
          and w.get('node_exit') == int(os.environ['QC_CANCEL_EXPECTED_EXIT'])
          and w.get('signal') == os.environ['QC_CANCEL_SIGNAL']
          and record.get('capability_error') is None and w.get('capability_error') is None
          and w.get('native_forced') is False and w.get('owner_errors') == []
          and w.get('native_finalized') is True and w.get('adopted_reaped') is True
          and w.get('node_log_drained') is True and w.get('deadline_ok') is True
          and record.get('owner_exit') == int(os.environ['QC_CANCEL_EXPECTED_EXIT'])
          and record.get('caller_errors') == [] and record.get('drain_complete') is True
          and record.get('deadline_ok') is True
          and type(record.get('cancel_deadline_ns')) is int
          and record['cancel_deadline_ns'] == w.get('cancel_deadline_ns')
          and int(Path(sys.argv[1]).with_name('public-returned-ns').read_text()) <= record['cancel_deadline_ns']
          and record.get('native_cleanup_errors') == [])
with Path(sys.argv[2]).open('x') as f:
    json.dump({'native_lifecycle':w,'eligible':bool(positive)},f)
if not positive:
    raise SystemExit('missing/failed authenticated public native lifecycle witness; NOT eligible')
PY_WITNESS

'''
    target = fixture / 'tests/qc-running-cancel-witness.sh'
    with target.open('x') as f:
        f.write(case)
    target.chmod(0o755)
    for p, text in [(obs, observer), (fixture/'tests/lib/qc-running-cancel-witness.sh', lib), (target, case)]:
        with (OUT / (p.name + '.sha256')).open('x') as f:
            f.write(hashlib.sha256(text.encode()).hexdigest() + '\n')
    env = dict(os.environ, OCTO_FEATHER_QC_MODEL='fixture/cancellation-contract', QC_CANCEL_ARTIFACTS=str(OUT), QC_CANCEL_MODE=mode, QC_CANCEL_SIGNAL='SIGINT' if mode == 'SIGINT' else 'SIGTERM', QC_CANCEL_EXPECTED_EXIT='130' if mode == 'SIGINT' else '143', QC_CANCEL_CONTROLLER=str(controller), QC_TEST_TIMEOUT='120',
               QC_TEST_RUN_TIMEOUT='20', CI='true', FORCE_COLOR='1', GATE_WORKERS='0')
    # All three proof-abort runs and the actual cancellation share this budget.
    # No model capture, wrapper SDK substitution, or private Recorder invocation.
    child = None
    fd = None
    actual = None
    primary = None
    eligible = False
    pending, saved = _h_signals()
    streams = []
    try:
        _h_subreaper()
        if time.monotonic() >= end-5:
            raise TimeoutError('fixture preparation exhausted CASE budget; not launched')
        out = (OUT/'observer.stdout').open('xb'); streams.append(out)
        err = (OUT/'observer.stderr').open('xb'); streams.append(err)
        child = subprocess.Popen(['/usr/bin/bash', str(target)], cwd=KIT, env=env,
                                 stdin=subprocess.DEVNULL, stdout=out, stderr=err)
        fd = os.pidfd_open(child.pid)  # protected unassigned/enrollment interval
        while actual is None:
            if pending:
                raise InterruptedError('CASE interrupted: '+str(pending))
            left = end-5-time.monotonic()
            if left <= 0:
                raise TimeoutError('CASE execution exhausted owned budget')
            try:
                actual = child.wait(timeout=min(.05,left))
            except subprocess.TimeoutExpired:
                pass
    except BaseException as error:
        primary = _h_first(primary,error,"CASE execution")
    finally:
        cleanup,primary = _h_cleanup_attempt(child,fd,end,primary)
        for stream in reversed(streams):
            try:
                stream.close()
            except BaseException as error:
                primary = _h_first(primary,error,"CASE output close")
        witness_path = OUT/'public-native-witness.json'
        witness = None
        try:
            if witness_path.is_file():
                witness = json.loads(witness_path.read_text())
        except BaseException as error:
            primary = _h_first(primary,error,"witness parse")
        eligible = (actual == 0 and primary is None and not pending and not cleanup['forced']
                    and cleanup['complete'] and isinstance(witness,dict) and witness.get('eligible') is True)
        _h_publish(OUT/'actual-result.json',{'actual_case_rc':actual,'safety_cleanup_used':cleanup['forced'],
                       'cleanup_complete':cleanup['complete'],'cleanup':cleanup,'primary_error':_h_text(primary),
                       'pending':pending,'graceful_lease_close_evidence':witness,'eligible':eligible,
                       'scope':'actual same-handle precleanup AND public witness, never cleanup-derived PASS'},primary,saved)
    assert eligible and not pending, str(OUT/'actual-result.json')


def early_cancel(s: Scratch, entry: str = "owner") -> None:
    """A private genuine-source stop seed witnesses enrollment, never startup death."""
    from pathlib import Path
    r = repo(s)
    end = time.monotonic() + 25
    pending, saved = _h_signals()
    child = None
    fd = None
    observed = None
    actual = None
    primary = None
    note = s.root / "capture.json"
    command = ([kit("octo-feather-qc"), "--capture-case", str(note), "--", "true"]
               if entry == "capture" else [kit("octo-feather-qc-sandbox"), "--", "true"])
    with (s.root / "window.stdout").open("wb+") as out, (s.root / "window.stderr").open("wb+") as err:
        try:
            _h_subreaper()
            child = subprocess.Popen(command, cwd=r, env={**s.env, **tool_homes()},
                                     stdout=out, stderr=err, start_new_session=True)
            fd = os.pidfd_open(child.pid)
            while observed is None:
                if pending or time.monotonic() >= end-3:
                    raise TimeoutError("no owned enrollment-window witness")
                event = os.waitid(os.P_PIDFD, fd, os.WSTOPPED | os.WNOHANG | os.WNOWAIT)
                if event is not None:
                    assert event.si_code == os.CLD_STOPPED and event.si_status == signal.SIGSTOP
                    observed = {"si_code": event.si_code, "si_status": event.si_status, "at_ns": time.monotonic_ns()}
                    signal.pidfd_send_signal(fd, signal.SIGTERM)
                    signal.pidfd_send_signal(fd, signal.SIGCONT)
                elif child.poll() is not None:
                    raise AssertionError("startup death is NOT enrollment evidence")
                else:
                    time.sleep(min(.01, max(0,end-3-time.monotonic())))
            actual = child.wait(timeout=max(0,end-3-time.monotonic()))
        except BaseException as error:
            primary = str(error)
        finally:
            cleanup = _h_cleanup(child,fd,end)
            result = {"window": observed, "actual_root_rc": actual, "primary_error": primary,
                      "pending": pending, "cleanup": cleanup, "scope": "enrollment sensitivity only; not graceful baseline proof"}
            result_dir = Path(os.environ.get("QC_CONTRACT_CASE_OUT", str(s.root)))
            result_dir.mkdir(exist_ok=True)
            (result_dir / "window-result.json").write_text(json.dumps(result,indent=2))
            _h_restore(saved)
        assert observed is not None and actual == 143 and primary is None and not pending, result
        assert cleanup["complete"] and not cleanup["forced"], result
        if entry == "capture":
            record = json.loads(note.read_text())
            assert record["ran"] is None and record["cancelled"] is True and record["exit"] == 143, record
        else:
            err.seek(0)
            lines = err.read().decode(errors="replace").splitlines()
            record = next(json.loads(line.split("record ",1)[1]) for line in lines if line.startswith("qc sandbox: record {") and "native_lifecycle" in line)
            assert record["native_lifecycle"]["owner_received_signal"] == signal.SIGTERM, record


if __name__ == "__main__":
    main(by_hand, srt_missing, network, nested, refused_host, blocking_stdio, reaped, live_survivor, running_cancel, early_cancel)
