#!/usr/bin/env python3
"""Fake `pi` as the qc judge (the testkit's stand-in for Pi, which the kit does not own): no model.

Run by octo-feather-qc's agent fallback in its sandbox, its brief the last argument. It prints
which gh it was given, the brief's lines (each prefixed BRIEF), then the answers of three reads
(R1 issue view, R2 pr view --json, R3 api GET) and two writes (W1 issue comment, W2 api -X POST)
through that gh, each prefixed; with a snapshot ($OCTO_FEATHER_GHSNAP) it tries to write it,
printing ESCAPE for each write that lands. Then its report: acceptance-a passed at the brief's
head. `--version` exits 0; FAKE_PI_HANG=N sleeps N seconds instead (a judge that never ends).
"""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


def say(line: str) -> None:
    sys.stdout.write(line + "\n")


def lands(p: Path) -> bool:
    """Whether a write to P lands."""
    try:
        p.write_text("hacked\n")
    except OSError:
        return False
    return True


a = sys.argv[1:]
if a[:1] == ["--version"]:
    sys.exit(0)
if hang := os.environ.get("FAKE_PI_HANG"):
    os.execvp("sleep", ["sleep", hang])  # noqa: S606, S607
brief = a[-1] if a else ""
say(f"gh is {shutil.which('gh')}")
for ln in brief.splitlines():
    say(f"BRIEF {ln}")


def gh(tag: str, *args: str) -> None:
    p = subprocess.run(["gh", *args], capture_output=True, text=True, check=False)  # noqa: S607
    say(f"{tag} {' '.join((p.stdout + p.stderr).split())}")


gh("R1", "issue", "view", "1", "--json", "title,state", "-q", '.title + " " + .state')
gh("R2", "pr", "view", "2", "--json", "isDraft,title")
gh("R3", "api", "repos/o/r/issues/1/timeline", "-q", "length")
gh("W1", "issue", "comment", "1", "-b", "hacked")
gh("W2", "api", "-X", "POST", "repos/o/r/issues", "-f", "title=x")
if snap := os.environ.get("OCTO_FEATHER_GHSNAP"):
    subprocess.run(["chmod", "-R", "u+w", snap], capture_output=True, check=False)  # noqa: S607
    for what, p in (
        ("snapshot", Path(snap) / "x"),
        ("snapshot item", Path(snap) / "issue" / "1.json"),
    ):
        if lands(p):
            say(f"ESCAPE {what} writable")
m = re.search(r"head ([0-9a-f]{40})", brief)
h = m.group(1) if m else ""
report = (
    f'{{"head": "{h}", "criteria": [{{"id": "acceptance-a", "verdict": "pass", '
    '"command": "gh issue view 1", "output": "ok", "why": "history only: shown"}]}'
)
say(f"```json\n{report}\n```")
