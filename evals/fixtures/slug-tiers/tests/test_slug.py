"""In-process tests through `slugger.cli.main`."""

import pytest

from slugger.cli import main


def test_slug_of_a_title(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["Crème Brûlée: A How-To!"]) == 0
    assert capsys.readouterr().out == "creme-brulee-a-how-to\n"


def test_no_letters_is_an_error(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["?!"]) == 2
    assert "no letters" in capsys.readouterr().err
