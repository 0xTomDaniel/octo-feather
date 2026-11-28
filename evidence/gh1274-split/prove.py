#!/usr/bin/env python3
"""The real artifact, before and after (principle-prove-it-works, ticket #1333): each invocation below run through
the hub at 67ce2d7b (its tree in a scratch copy) and through this tree's dispatcher, in one scratch HOME and
state dir, no Herdr pane and no OpenRouter key; stdout, stderr and exit code compared byte for byte, the two
scripts dirs written <SCRIPTS>.

  uv run --locked --offline python evidence/gh1274-split/prove.py [--base REV]

Prints one line per invocation, `same` or `DIFFERS` with both outputs; exit 0 only when every one is the same.
The invocations: every command with no arguments (its usage or its read of an empty state dir; start, which fetches
the kit install's origin first, as -h), and commands given input they read or refuse: fields and ticket on stdin,
post-merge of a lane with no record, merge-ask and merge of a malformed PR, verdict with a malformed head.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
BASE = sys.argv[sys.argv.index("--base") + 1] if "--base" in sys.argv else "67ce2d7b"
COMMANDS = ["archive", "reflect", "verdict", "fields", "merge-ask", "ci-start", "resolution", "judge", "tickets",
            "done", "ticket", "seam", "skills", "spend", "report", "intake", "merge", "relay", "post-merge", "stale"]
REPORT = """Verdict: approve
Range: 0123456..89abcde
Checks: none
Owners: none
"""
DRAFT = """## Acceptance criteria

- quality#acceptance-gate-green: demo: `just fast`
"""
CASES: list[tuple[list[str], str]] = [([c], "") for c in COMMANDS] + [
    (["start", "-h"], ""),
    (["fields", "-"], REPORT),
    (["ticket", "-"], DRAFT),
    (["post-merge", "--lane", "nosuch"], ""),
    (["merge-ask", "abc"], ""),
    (["merge", "0", "abc"], ""),
    (["verdict", "1", "xyz", "-"], REPORT),
]


def run(lane: Path, args: list[str], stdin: str, env: dict[str, str]) -> tuple[int, str, str]:
    p = subprocess.run([str(lane), *args], input=stdin, capture_output=True, text=True, env=env, timeout=120,
                       check=False, cwd=env["HOME"])
    tag = str(lane.parent)
    return p.returncode, p.stdout.replace(tag, "<SCRIPTS>"), p.stderr.replace(tag, "<SCRIPTS>")


def main() -> int:
    bad = 0
    with tempfile.TemporaryDirectory() as t:
        base = Path(t) / "base"
        base.mkdir()
        arch = subprocess.run(["git", "archive", BASE], cwd=ROOT, capture_output=True, check=True).stdout
        subprocess.run(["tar", "-x", "-C", str(base)], input=arch, check=True)
        home = Path(t) / "home"
        home.mkdir()
        env = {k: v for k, v in os.environ.items() if not k.startswith("HERDR_") and k != "OPENROUTER_API_KEY"}
        env.update(HOME=str(home), XDG_STATE_HOME=str(home / "state"))
        state = subprocess.run([str(ROOT / "scripts" / "octo-feather-state")], capture_output=True, text=True,
                               env=env, check=True).stdout.strip()
        Path(state, "lanes").mkdir(parents=True, exist_ok=True)
        for args, stdin in CASES:
            old = run(base / "scripts" / "octo-feather-lane", args, stdin, env)
            new = run(ROOT / "scripts" / "octo-feather-lane", args, stdin, env)
            name = " ".join(args)
            if old == new:
                print(f"same: octo-feather-lane {name}: exit {new[0]}, {len(new[1])} bytes out, {len(new[2])} err")
            else:
                bad += 1
                print(f"DIFFERS: octo-feather-lane {name}:\n  hub   {old!r}\n  split {new!r}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
