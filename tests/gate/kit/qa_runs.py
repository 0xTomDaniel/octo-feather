"""QA repeat-count usage through the real CLI, without a model or sandbox.

Partial replacement of tests/qa-runs.sh: only its usage oracles. Repeated-run
results and artifacts remain legacy coverage pending recorded external responses
and paired parity. No substitute transcript is generated here.
"""

from testkit import Scratch, kit, main


def runs_usage(s: Scratch) -> None:
    """Invalid counts fail before starting a run; help documents the option."""
    q = kit("octo-feather-qa")
    for value in ("0", "-1", "two"):
        got = s.run([q, "--runs", value], want=64)
        assert "runs needs a positive integer" in got.out + got.err, got
        assert "qa: run " not in got.out + got.err, got
    got = s.run([q, "--runs"], want=64)
    assert "qa: run " not in got.out + got.err, got
    got = s.run([q, "--help"])
    assert any(line.startswith("  --runs N  ") for line in got.out.splitlines()), got


if __name__ == "__main__":
    main(runs_usage)
