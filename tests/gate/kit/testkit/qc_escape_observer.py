"""Invocation-owned observer for the legacy public QC escape scenario (#751).

Extend #749's private socket, nonce and SCM_RIGHTS self-pidfd mechanism. Kit-only
Python stdlib suffices: no host PID discovery, foreign /proc, or product input.
A registering process execs the original sleep, retaining its actual identity.
"""

import json
import os
from pathlib import Path
import secrets
import select
import signal
import socket
import struct
import subprocess
import sys
import tempfile
import time


LABELS = {"herdr-server", "escape-unshare", "escape-setsid"}


def exited(fd: int, seconds: float = 0) -> bool:
    return bool(select.select([fd], [], [], seconds)[0])


def client(label: str, duration: str = "") -> None:
    if label == "ready":
        end = time.monotonic() + 20
        while time.monotonic() < end:
            with socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET) as peer:
                peer.settimeout(5)
                peer.connect(os.environ["QC_ESCAPE_SOCKET"])
                peer.sendall(json.dumps({"token": os.environ["QC_ESCAPE_NONCE"], "label": label}).encode())
                if peer.recv(4096) == b"!":
                    return
            time.sleep(0.05)
        sys.exit("escape observer: actual sleeps did not become ready")
    with socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET) as peer:
        peer.settimeout(30)
        peer.connect(os.environ["QC_ESCAPE_SOCKET"])
        record = json.dumps({"token": os.environ["QC_ESCAPE_NONCE"], "label": label}).encode()
        if label == "check":
            peer.sendall(record)
        else:
            fd = os.pidfd_open(os.getpid())
            try:
                socket.send_fds(peer, [record], [fd])
            finally:
                os.close(fd)
        reply = peer.recv(4096)
        if reply != b"!":
            sys.exit(reply.decode() or "escape observer: missing ACK")
        if label != "check":
            # close-on-exec socket EOF lets the receiver wait until this exact
            # registering process has crossed exec, not merely queued a record.
            os.execvp("sleep", ["sleep", duration])  # noqa: S606, S607


def supervise(argv: list[str]) -> int:
    handles: list[tuple[str, int]] = []
    checked = False
    child: subprocess.Popen[bytes] | None = None
    # Private writable socket endpoint only, not a new persistent store.
    with tempfile.TemporaryDirectory(prefix="qc-owned-") as directory:
        endpoint = str(Path(directory) / "socket")
        nonce = secrets.token_hex(32)
        env = dict(os.environ, QC_ESCAPE_SOCKET=endpoint, QC_ESCAPE_NONCE=nonce,
                   QC_ESCAPE_HELPER=str(Path(__file__).resolve()))
        binds = env.get("OCTO_FEATHER_QC_RO_BINDS", "")
        env["OCTO_FEATHER_QC_RO_BINDS"] = ":".join(filter(None, [binds, directory]))
        with socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET) as server:
            server.bind(endpoint)
            server.listen(16)
            server.settimeout(0.2)
            try:
                child = subprocess.Popen(argv, env=env, start_new_session=True)  # noqa: S603
                deadline = time.monotonic() + int(env.get("QC_TEST_TIMEOUT", "600")) + 30
                while child.poll() is None:
                    if time.monotonic() >= deadline:
                        raise TimeoutError("escape observer: scenario deadline")
                    try:
                        peer, _ = server.accept()
                    except TimeoutError:
                        continue
                    with peer:
                        peer.settimeout(5)
                        _pid, uid, _gid = struct.unpack("3i", peer.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
                        data, fds, flags, _ = socket.recv_fds(peer, 4096, 4)
                        accepted = False
                        try:
                            record = json.loads(data)
                            if uid != os.getuid() or record.get("token") != nonce or flags:
                                raise ValueError("escape observer: invalid child-origin record")
                            label = record.get("label")
                            counts = {name: sum(n == name for n, _ in handles) for name in LABELS}
                            if label == "ready" and not fds:
                                ready = all(counts[name] >= 1 for name in LABELS) and all(
                                    not exited(fd) for name, fd in handles if name != "herdr-server"
                                )
                                peer.sendall(b"!" if ready else b"pending")
                            elif label == "check" and not fds:
                                if counts["herdr-server"] < 1 or counts["escape-unshare"] != 1 or counts["escape-setsid"] != 1:
                                    raise ValueError(f"escape observer: missing/duplicate actual processes: {counts}")
                                end = time.monotonic() + 10
                                for name, fd in handles:
                                    dead = exited(fd, max(0, end - time.monotonic()))
                                    print(f"OWNED after QC {name} pidfd={fd} {'EXITED' if dead else 'LIVE'}", flush=True)
                                    if not dead:
                                        peer.sendall(b"sandbox processes survived the run")
                                        break
                                else:
                                    checked = True
                                    peer.sendall(b"!")
                            elif label in LABELS and len(fds) == 1:
                                fd = fds[0]
                                if exited(fd):
                                    raise ValueError("escape observer: process not live before exec")
                                handles.append((label, fd))
                                accepted = True
                                print(f"OWNED ready {label} pidfd={fd} LIVE before exec", flush=True)
                                peer.sendall(b"!")
                                if peer.recv(1) != b"":
                                    raise ValueError("escape observer: expected close-on-exec EOF")
                            else:
                                raise ValueError("escape observer: unexpected request")
                        finally:
                            if not accepted:
                                for fd in fds:
                                    os.close(fd)
                rc = child.wait(timeout=5)
                return rc if rc else (0 if checked else 1)
            finally:
                signal.signal(signal.SIGTERM, signal.SIG_IGN)
                signal.signal(signal.SIGINT, signal.SIG_IGN)
                failures = []
                # Numeric group signals only while the direct child remains unreaped.
                if child is not None and child.returncode is None:
                    try:
                        os.killpg(child.pid, signal.SIGTERM)
                        try:
                            child.wait(timeout=10)
                        except subprocess.TimeoutExpired:
                            os.killpg(child.pid, signal.SIGKILL)
                            child.wait(timeout=10)
                    except (OSError, subprocess.TimeoutExpired) as error:
                        failures.append(f"launcher: {error}")
                for label, fd in handles:
                    try:
                        if not exited(fd):
                            try:
                                signal.pidfd_send_signal(fd, signal.SIGKILL)
                            except ProcessLookupError:
                                pass
                        if not exited(fd, 10):
                            failures.append(label)
                        print(f"OWNED cleanup {label} pidfd={fd} {'LIVE' if label in failures else 'EXITED'}", flush=True)
                    except OSError as error:
                        failures.append(f"{label}: {error}")
                    finally:
                        os.close(fd)
                if failures:
                    raise RuntimeError(f"escape observer: cleanup failed: {failures}")


def stopped(number: int, _frame: object) -> None:
    raise SystemExit(128 + number)


if __name__ == "__main__":
    if sys.argv[1] == "supervise":
        signal.signal(signal.SIGTERM, stopped)
        signal.signal(signal.SIGINT, stopped)
        sys.exit(supervise(sys.argv[2:]))
    client(*sys.argv[1:])
