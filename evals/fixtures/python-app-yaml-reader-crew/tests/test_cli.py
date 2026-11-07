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


def test_hello_file_greets_each_listed_name(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    names = tmp_path / "names.yaml"
    names.write_text("names:\n  - Ada\n  - Grace\nteam: crew\n")
    assert main(["hello-file", str(names), "--json"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert [json.loads(line) for line in lines] == [
        {"name": "Ada", "text": "Hello, Ada"},
        {"name": "Grace", "text": "Hello, Grace"},
    ]


def test_hello_file_without_names_is_a_json_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    names = tmp_path / "names.yaml"
    names.write_text("team: crew\n")
    assert main(["hello-file", str(names), "--json"]) == 2
    assert json.loads(capsys.readouterr().out) == {
        "error": f"{names}: no names listed under `names:` or `crew:`"
    }


def test_hello_file_reads_a_crew_list(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    names = tmp_path / "names.yaml"
    names.write_text("crew:\n  - Ada\n  - Grace\nteam: crew\n")
    assert main(["hello-file", str(names)]) == 0
    assert capsys.readouterr().out == "Hello, Ada\nHello, Grace\n"
