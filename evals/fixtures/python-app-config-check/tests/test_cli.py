"""Integration (in-process CLI) and end-to-end (installed `app` command) tests."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from app.cli import main


def test_hello_json_in_process(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["hello", "Ada", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"name": "Ada", "text": "Hello, Ada"}


def test_empty_name_is_a_json_error(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["hello", "  ", "--json"]) == 2
    assert json.loads(capsys.readouterr().out) == {"error": "name must not be empty"}


def test_installed_command_end_to_end() -> None:
    app = shutil.which("app")
    assert app, "run through `uv run` so the app command is on PATH"
    done = subprocess.run(
        [app, "hello", "Grace", "--json"], capture_output=True, text=True, check=True
    )
    assert json.loads(done.stdout) == {"name": "Grace", "text": "Hello, Grace"}


def test_config_missing_a_key_is_refused(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    config = tmp_path / "app.toml"
    config.write_text('name = "Ada"\n')
    assert main(["config-check", str(config), "--json"]) == 2
    assert json.loads(capsys.readouterr().out)["missing"] == ["greeting"]


def test_complete_config_passes(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    config = tmp_path / "app.toml"
    config.write_text('name = "Ada"\ngreeting = "Hello"\n')
    assert main(["config-check", str(config), "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["missing"] == []
