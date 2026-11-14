"""The `app quote` command, in process and installed."""

import json
import shutil
import subprocess

import pytest

from app.cli import main


def test_unknown_region_is_a_json_error(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["quote", "mars", "1.00:1", "--json"]) == 2
    assert json.loads(capsys.readouterr().out) == {"error": "unknown region mars"}


def test_installed_command_end_to_end() -> None:
    app = shutil.which("app")
    assert app, "run through `uv run` so the app command is on PATH"
    done = subprocess.run(
        [app, "quote", "de", "10.00:1"], capture_output=True, text=True, check=True
    )
    assert done.stdout == "total 11.9000\n"
