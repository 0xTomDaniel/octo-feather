"""A gate run leaves the caller's mise state and its repo's git config as it found them (#664,
#584, #587; owner ruling 2026-11-05): `just test` in a git copy of the kit, its caller's mise state
dir a scratch one, with one seeded item. Without a seed the run passes and names what it found
unchanged; a seeded item that writes a tracked-configs link into the caller's state, or a key into
the copy's .git/config (the repo's git common dir config), fails the run naming the change, though
the item itself passes."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

from testkit import ROOT, Ran, Scratch, main, pnpm_store, tool_homes

ITEM = "tests/gate/test_gate.py::test_script[tests/zz-seed.sh]"
# The seeded item: as SEED says, a link into the caller's mise state (SEED_STATE: the item sees
# only the gate's own per-run state dir, so the caller's is handed to it), or a key in its repo's
# git config; else nothing. It passes either way.
SEED = """#!/usr/bin/env bash
set -euo pipefail
case "${SEED:-}" in
  link) ln -s /nowhere/seeded/mise.toml "$SEED_STATE/tracked-configs/seeded" ;;
  config) git config --local seed.leak yes ;;
esac
"""
# The kit gate's own settings and venv, never the copy's run's.
GATE = (
    "GATE_NESTED",
    "GATE_RECIPES",
    "GATE_WORKERS",
    "GATE_RUN_DIR",
    "GATE_ITEM",
    "HERDR_SESSION",
    "VIRTUAL_ENV",
)


def kit_copy(s: Scratch) -> Path:
    """The kit's files (tracked, and new ones git would track) in a git repo of their own, with
    the seeded item."""
    k = s.root / "kit"
    files = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],  # noqa: S607
        cwd=ROOT,
        capture_output=True,
        check=True,
    ).stdout.decode()
    subprocess.run(
        ["tar", "-cf", str(s.root / "kit.tar"), "--null", "-T", "-"],  # noqa: S607
        cwd=ROOT,
        input=files.encode(),
        check=True,
    )
    k.mkdir()
    subprocess.run(["tar", "-xf", str(s.root / "kit.tar"), "-C", str(k)], check=True)  # noqa: S607
    (k / "tests" / "zz-seed.sh").write_text(SEED)
    (k / "tests" / "zz-seed.sh").chmod(0o755)
    s.git(k, "init", "-q", "-b", "main")
    s.git(k, "add", "-A")
    s.git(k, "commit", "-qm", "copy")
    return k


def gate(s: Scratch, k: Path, seed: str, want: int | None) -> Ran:
    """`just test ITEM` in K with SEED; its stdout and stderr together, as a shell's 2>&1."""
    env = {k: v for k, v in s.env.items() if k not in GATE}
    env |= tool_homes() | {
        "npm_config_store_dir": pnpm_store(),
        "MISE_STATE_DIR": str(s.root / "user-mise"),
        "GATE_WORKERS": "1",
        "SEED": seed,
        "SEED_STATE": str(s.root / "user-mise"),
    }
    p = subprocess.run(
        ["just", "test", ITEM],  # noqa: S607
        cwd=k,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    said = f"just test (SEED={seed}): exit {p.returncode}, want {want}\n{p.stdout}"
    assert want is None or p.returncode == want, said
    return Ran(p.returncode, p.stdout, "")


def seeded(s: Scratch) -> None:
    """Clean, then each seed: the clean run passes naming the state and config it found
    unchanged; each seed fails naming its change, and the item itself passed."""
    st = s.root / "user-mise"
    (st / "tracked-configs").mkdir(parents=True)
    (st / "trusted-configs").mkdir()
    (st / "tracked-configs" / "kept").symlink_to("/nowhere/kept/mise.toml")
    k = kit_copy(s)
    cfg = re.escape(str(k / ".git" / "config"))
    ok = gate(s, k, "", 0)
    assert re.search(
        rf"check-tests: unchanged by the gate: {re.escape(str(st))}/tracked-configs \(\d+ entries\), "
        rf"{re.escape(str(st))}/trusted-configs \(0 entries\), {cfg} \(sha256 [0-9a-f]{{12}}\)",
        ok.out,
    ), ok.out
    link = gate(s, k, "link", None)
    assert link.rc != 0, link.out
    assert re.search(r"1 passed", link.out), link.out
    assert re.search(
        rf"check-tests: FAIL the gate changed the caller's mise state or the repo's git config \(#664\):\n"
        rf"  {re.escape(str(st))}/tracked-configs/seeded: added -> /nowhere/seeded/mise\.toml\n",
        link.out,
    ), link.out
    (st / "tracked-configs" / "seeded").unlink()
    conf = gate(s, k, "config", None)
    assert conf.rc != 0, conf.out
    assert re.search(r"1 passed", conf.out), conf.out
    assert re.search(
        rf"check-tests: FAIL the gate changed the caller's mise state or the repo's git config \(#664\):\n"
        rf"  {cfg}: changed \(sha256 [0-9a-f]{{12}} -> [0-9a-f]{{12}}\): \+\[seed\] \+\tleak = yes\n",
        conf.out,
    ), conf.out
    assert os.readlink(st / "tracked-configs" / "kept") == "/nowhere/kept/mise.toml"


if __name__ == "__main__":
    main(seeded)
