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


def test_request_with_unknown_field_is_refused(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["hello", "--request", '{"name": "Ada", "mood": "glad"}', "--json"]) == 2
    assert json.loads(capsys.readouterr().out) == {"error": "invalid request"}


ROSTER = {
    "team": "crew",
    "exported": "2026-11-02T09:00:00Z",
    "members": [
        {"name": "Ada", "role": "lead", "active": True},
        {"name": "Linus", "role": "ops", "active": False},
        {"name": "Grace", "role": "dev", "active": True},
    ],
}


def test_hello_team_greets_active_members(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    roster = tmp_path / "roster.json"
    roster.write_text(json.dumps(ROSTER), encoding="utf-8")
    assert main(["hello-team", str(roster)]) == 0
    assert capsys.readouterr().out == "Hello, Ada\nHello, Grace\n"


def test_hello_team_json_lines(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    roster = tmp_path / "roster.json"
    roster.write_text(json.dumps(ROSTER), encoding="utf-8")
    assert main(["hello-team", str(roster), "--json"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert [json.loads(line) for line in lines] == [
        {"name": "Ada", "text": "Hello, Ada"},
        {"name": "Grace", "text": "Hello, Grace"},
    ]


def test_installed_command_end_to_end() -> None:
    app = shutil.which("app")
    assert app, "run through `uv run` so the app command is on PATH"
    done = subprocess.run(
        [app, "hello", "--request", '{"name": "Grace"}', "--json"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(done.stdout) == {"name": "Grace", "text": "Hello, Grace"}
