"""The dispatcher's lazy imports (#1338, owner ruling 2026-11-28 #1274), at its seam, the command
`scripts/check-lane-dispatch` (rule: `scripts/check-lane-dispatch`). Each case copies the command
and scripts/check_rules.py into a scratch tree's scripts/, writes that tree's dispatcher
(scripts/octo-feather-lane) and runs the command there, so it reads the scratch dispatcher.
"""

import shutil
import subprocess
import sys
from pathlib import Path

from testkit import ROOT

HEAD = '#!/usr/bin/env python3\n"""dispatcher"""\n\nimport importlib\nimport sys\n\n'
LAZY = "from lane_cli import Refuse, help_doc\n\n\ndef main():\n    import merge_ask\n"


def run(tmp: Path, dispatcher: str) -> subprocess.CompletedProcess[str]:
    (tmp / "scripts").mkdir()
    for name in ("check-lane-dispatch", "check_rules.py"):
        shutil.copy2(ROOT / "scripts" / name, tmp / "scripts" / name)
    (tmp / "scripts/octo-feather-lane").write_text(dispatcher, encoding="utf-8")
    cmd = [sys.executable, str(tmp / "scripts/check-lane-dispatch")]
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def test_top_level_kit_import_fails(tmp_path: Path) -> None:
    ran = run(tmp_path, HEAD + "import merge_ask\n" + LAZY)
    assert ran.returncode == 1, ran
    assert ran.stdout == "scripts/octo-feather-lane:7:import merge_ask\n", ran
    assert "move it into the module of the command that uses it" in ran.stderr, ran


def test_lane_cli_and_stdlib_pass(tmp_path: Path) -> None:
    ran = run(tmp_path, HEAD + "try:\n    import os.path\nexcept ImportError:\n    pass\n" + LAZY)
    ok = (0, "lane-dispatch: ok (4 imports)\n", "")
    assert (ran.returncode, ran.stdout, ran.stderr) == ok, ran
