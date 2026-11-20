"""The command scenario of tests/gate/kit/test_qa_analyst.py (its item test_analyze_usage), this
file its command (testkit.main): scripts/octo-feather-qa --analyze's usage exits (rules:
octo-feather-qa --help, Analysis). The analysis itself: test_qa_analyst.py, in-process (#1090)."""

from __future__ import annotations

from testkit import ROOT, Scratch, main


def analyze_usage(s: Scratch) -> None:
    """--analyze with no readable summary.json, or with another option: exit 64."""
    q = [str(ROOT / "scripts" / "octo-feather-qa"), "--analyze"]
    err = s.run([*q, str(s.root / "nowhere")], want=64).err
    assert "no readable summary.json" in err, err
    err = s.run([*q, str(s.root), "--runs", "2"], want=64).err
    assert "--analyze takes one RUN_DIR and no other option" in err, err


if __name__ == "__main__":
    main(analyze_usage)
