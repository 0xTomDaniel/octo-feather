"""End-to-end: the installed `tally` command as a process."""

import shutil
import subprocess
from pathlib import Path


def test_installed_command_counts_words(tmp_path: Path) -> None:
    tally = shutil.which("tally")
    assert tally, "run through `uv run` so the tally command is on PATH"
    f = tmp_path / "b.txt"
    f.write_text("a b c d\n", encoding="utf-8")
    done = subprocess.run([tally, str(f)], capture_output=True, text=True, check=True)
    assert done.stdout == "4\n"
