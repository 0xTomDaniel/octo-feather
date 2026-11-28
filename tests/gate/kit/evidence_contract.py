"""`octo-feather-evidence append` validates the target's qc.toml through octo-feather-contract (#1352,
#914; quality #edge-validation-kit), as scenarios (testkit.main).

A scratch target repo, its qc.toml a worked literal; the store under the scratch HOME's state (the
scenario clears XDG_STATE_HOME: never the box's real store). A contract octo-feather-contract refuses
(a wrong-typed `format`; an unknown field) is refused naming the field, exit 1, no record kept; a valid
one appends a record carrying its format.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from testkit import Scratch, kit, main, tool_homes

if TYPE_CHECKING:
    from pathlib import Path

VALID = """format = 2

[entry]
command = "app"

[services]

[fixture]

[values]
name = "Ada"
"""
CRIT = "demo#x"


def _target(s: Scratch, contract: str) -> Path:
    """A committed scratch repo whose qc.toml is CONTRACT, and the drive's outputs folder beside it."""
    s.env |= tool_homes()  # the caller's uv and mise installs: octo-feather-contract runs in the kit's locked env
    repo = s.root / "scratch"
    s.git(s.root, "init", "-q", str(repo))
    (repo / "qc.toml").write_text(contract)
    s.git(repo, "add", "-A")
    s.git(repo, "commit", "-q", "-m", "init")
    (s.root / "out").mkdir()
    (s.root / "out" / "summary.txt").write_text("drove it\n")
    return repo


def _append(s: Scratch, repo: Path, want: int) -> str:
    """`octo-feather-evidence append` for CRIT in REPO, exiting WANT; its stdout and stderr."""
    cmd = [kit("octo-feather-evidence"), "append", "--criterion", CRIT, "--criterion-text", "demo text"]
    r = s.run([*cmd, "--outputs", str(s.root / "out"), "--repo", str(repo)], want=want)
    return r.out + r.err


def _records(s: Scratch, repo: Path) -> list[dict[str, object]]:
    out = s.run([kit("octo-feather-evidence"), "read", "--repo", str(repo), "--json"]).out
    return [r["record"] for r in json.loads(out)]


def _refused(s: Scratch, contract: str, problem: str) -> None:
    repo = _target(s, contract)
    said = _append(s, repo, 1)
    assert problem in said, f"refusal does not say {problem!r}: {said}"
    assert _records(s, repo) == [], f"a refused contract kept a record: {said}"


def wrong_format(s: Scratch) -> None:
    """format = "2" (a string) and an unknown field: refused naming format, no record."""
    _refused(s, VALID.replace("format = 2", 'format = "2"\nmood = "x"'), "format must be an integer")


def unknown_field(s: Scratch) -> None:
    """A valid format and an unknown top-level field mood: refused naming mood, no record."""
    _refused(s, VALID.replace("format = 2", 'format = 2\nmood = "x"'), "unknown key mood")


def valid_appends(s: Scratch) -> None:
    """A valid qc.toml: one record, its contract format 2."""
    repo = _target(s, VALID)
    rid = _append(s, repo, 0).strip()
    recs = _records(s, repo)
    assert [r["id"] for r in recs] == [rid], recs
    contract = recs[0]["contract"]
    assert isinstance(contract, dict) and contract.get("format") == 2, contract


if __name__ == "__main__":
    main(wrong_format, unknown_field, valid_appends)
