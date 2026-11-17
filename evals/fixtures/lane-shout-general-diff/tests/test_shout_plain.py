"""End-to-end: plain `--shout`, the installed `app` command in a subprocess."""

import shutil
import subprocess


def test_shout_plain() -> None:
    app = shutil.which("app")
    assert app, "run through `uv run` so the app command is on PATH"
    args = [app, "hello", "Ada", "--shout"]
    done = subprocess.run(args, capture_output=True, text=True, check=True)
    assert done.stdout == "HELLO, ADA!\n"
