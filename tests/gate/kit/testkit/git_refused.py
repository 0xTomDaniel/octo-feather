#!/usr/bin/env python3
"""A stand-in for a git remote refusing credentials (a private pin, git not signed in; #463), put
first on PATH as `git` by a scenario itself (testkit's docstring): `git ... fetch ...` replays the
recording below; any other git call runs the real git, the next on PATH after this one's dir.

Recording (a tape, never a simulator: tdd skill, mocking.md): real git 2.43.0, prompts off
(GIT_TERMINAL_PROMPT=0, no credential helper), fetching from https://github.com a repo it must
sign in for, printed exactly this stderr, no stdout, and exited 128.
"""

import os
import shutil
import sys
from pathlib import Path

STDERR = "fatal: could not read Username for 'https://github.com': terminal prompts disabled\n"
EXIT = 128

if "fetch" in sys.argv[1:]:
    sys.stderr.write(STDERR)
    sys.exit(EXIT)
here = Path(sys.argv[0]).absolute().parent
dirs = os.environ["PATH"].split(os.pathsep)
rest = os.pathsep.join(d for d in dirs if Path(d).absolute() != here)
real = shutil.which("git", path=rest)
if real is None:
    sys.exit("git_refused: no real git on PATH after the stand-in")
os.execv(real, [real, *sys.argv[1:]])  # noqa: S606 (the real git, by its full path)
