"""Finite external timeout fault for qc_gh.killed, never a product input or a process owner.

Request exactly one delegated launch through the existing invocation-private socket. The
fixture validates the request and owns the real timeout/QC Popen directly. Deliberately exit
143 on TERM without forwarding it: the actual delegated judge must survive until fixture
cleanup, so the unchanged public observer rejects it. No child is launched by this shim.
Python stdlib suffices for this kit-only adapter, as for the existing judge/recorder protocol.
"""

import json
import os
import signal
import socket
import sys
from pathlib import Path


def stopped(_number: int, _frame: object) -> None:
    sys.exit(143)


def expired(_number: int, _frame: object) -> None:
    sys.exit("faulty timeout: cancellation did not arrive within 60 seconds")


signal.signal(signal.SIGTERM, stopped)
signal.signal(signal.SIGALRM, expired)
signal.alarm(60)
with socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET) as peer:
    peer.settimeout(30)
    peer.connect(os.environ["FAKE_PI_HANG_SOCKET"])
    request = {
        "kind": "delegate-timeout",
        "token": os.environ["FAKE_PI_HANG_TOKEN"],
        "argv": sys.argv[1:],
        "cwd": str(Path.cwd()),
    }
    peer.sendall(json.dumps(request).encode())
    if peer.recv(1) != b"!":
        sys.exit("faulty timeout: fixture rejected launch request")
# Readiness comes from the real judge, not this wait. Alarm bounds a missing cancellation.
signal.pause()
sys.exit("faulty timeout: unexpected signal")
