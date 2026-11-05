"""Integration tests: `tally.cli.main` in-process."""

import json
from pathlib import Path

import pytest

from tally.cli import main


def test_words_json(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    f = tmp_path / "a.txt"
    f.write_text("one two\nthree\n", encoding="utf-8")
    assert main([str(f), "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"path": str(f), "words": 3}


def test_missing_file_is_a_json_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main([str(tmp_path / "nope.txt"), "--json"]) == 2
    assert "cannot read" in json.loads(capsys.readouterr().out)["error"]
