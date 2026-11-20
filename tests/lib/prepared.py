#!/usr/bin/env python3
"""prepared.py: the template installs gate items share, each prepared once per gate run (#509).

A test helper run as a command (tests/evidence.sh, contract.sh, tests/gate/kit/testkit/template.py);
in tests/lib/ so the gate's tests/*.sh glob does not collect it.

  prepared.py typescript DIR
      prints the path of templates/typescript's tracked files with its packages installed offline
      from the kit's pnpm store (node_modules), prepared under $GATE_RUN_DIR (one dir per gate run,
      shared by every xdist worker: tests/gate/test_gate.py), else under DIR (a bare run of one
      test: its own throwaway dir). The first caller prepares it under an exclusive lock, every
      later caller of the run waits on that lock and reuses it: pytest-xdist's documented "session
      fixture once" pattern (a file lock beside the shared tmp dir), with the stdlib's fcntl.flock
      in place of the filelock library (the kit's own scripts stay stdlib-only). The tree is
      read-only by contract: a test copies what it needs (`cp -a`), never writes it. A failed
      install exits 1 with pnpm's output and the fetch command; the next caller tries again.
      Prepared under $GATE_RUN_DIR, its CPU is billed to its own line, shared-typescript, never to
      the item that happened to build it (GATE_SHARED_CPU: tests/gate/conftest.py).
"""

import contextlib
import fcntl
import json
import os
import pathlib
import resource
import shutil
import subprocess
import sys

KIT = pathlib.Path(__file__).resolve().parents[2]


def tool(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        sys.exit(f"prepared.py: {name} is not on PATH")
    return path


def typescript(dest: pathlib.Path) -> None:
    src = KIT / "templates" / "typescript"
    ls = subprocess.run([tool("git"), "ls-files", "-z"], cwd=src, capture_output=True, check=True)
    for f in filter(None, ls.stdout.decode().split("\0")):
        (dest / f).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src / f, dest / f)
    pnpm = tool("pnpm")
    store = subprocess.run(
        [pnpm, "store", "path"], cwd=KIT, capture_output=True, text=True, check=True
    ).stdout.strip()
    r = subprocess.run(
        [pnpm, "install", "--offline", "--frozen-lockfile", "--silent"],
        cwd=dest,
        capture_output=True,
        text=True,
        env={**os.environ, "npm_config_store_dir": store},
        check=False,
    )
    if r.returncode != 0:
        sys.exit(
            f"{r.stdout}{r.stderr}prepared.py: typescript: pnpm install --offline failed: "
            "fill the pnpm store first (pnpm fetch in templates/typescript)"
        )


def _cpu() -> float:
    s, c = resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)
    return s.ru_utime + s.ru_stime + c.ru_utime + c.ru_stime


def main() -> None:
    if len(sys.argv) != 3 or sys.argv[1] != "typescript":
        sys.exit("usage: prepared.py typescript DIR")
    base = pathlib.Path(os.environ.get("GATE_RUN_DIR") or sys.argv[2])
    tree, done = base / "prepared-typescript", base / "prepared-typescript.done"
    with (base / "prepared-typescript.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if not done.exists():
            shutil.rmtree(tree, ignore_errors=True)  # a caller before failed part way
            tree.mkdir()
            cpu = _cpu()
            typescript(tree)
            if os.environ.get("GATE_RUN_DIR") and (bill := os.environ.get("GATE_SHARED_CPU")):
                line = {"line": "shared-typescript", "cpu_s": round(_cpu() - cpu, 3)}
                with contextlib.suppress(OSError), pathlib.Path(bill).open("a") as f:
                    f.write(json.dumps(line) + "\n")
            done.touch()
    sys.stdout.write(f"{tree}\n")


if __name__ == "__main__":
    main()
