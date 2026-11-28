"""`octo-feather-evidence append` validates the target's qc.toml through octo-feather-contract
(#1352, #914; quality #edge-validation-kit), as scenarios (testkit.main).

A scratch target repo, its qc.toml a worked literal; the store under the scratch HOME's state
(the scenario clears XDG_STATE_HOME: never the box's real store). A contract octo-feather-contract
refuses (a wrong-typed `format`; an unknown field) is refused naming the field, exit 1, no record
kept; a valid one appends a record carrying its format.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, cast

from testkit import Scratch, get, kit, main, obj, tool_homes

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
    """A committed scratch repo whose qc.toml is CONTRACT, and the drive's outputs beside it."""
    # The caller's uv and mise installs: octo-feather-contract runs in the kit's locked env.
    s.env |= tool_homes()
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
    cmd = [kit("octo-feather-evidence"), "append", "--criterion", CRIT, "--criterion-text", "t"]
    r = s.run([*cmd, "--outputs", str(s.root / "out"), "--repo", str(repo)], want=want)
    return r.out + r.err


def _records(s: Scratch, repo: Path) -> list[object]:
    """REPO's records as `octo-feather-evidence read --json` lists them."""
    out = s.run([kit("octo-feather-evidence"), "read", "--repo", str(repo), "--json"]).out
    rows: object = json.loads(out)
    assert isinstance(rows, list), out
    return [obj(r, "read item")["record"] for r in cast("list[object]", rows)]


def _refused(s: Scratch, contract: str, problem: str) -> None:
    repo = _target(s, contract)
    said = _append(s, repo, 1)
    assert problem in said, f"refusal does not say {problem!r}: {said}"
    assert _records(s, repo) == [], f"a refused contract kept a record: {said}"


def wrong_format(s: Scratch) -> None:
    """format = "2" (a string) and an unknown field: refused naming format, no record."""
    bad = VALID.replace("format = 2", 'format = "2"\nmood = "x"')
    _refused(s, bad, "format must be an integer")


def unknown_field(s: Scratch) -> None:
    """A valid format and an unknown top-level field mood: refused naming mood, no record."""
    _refused(s, VALID.replace("format = 2", 'format = 2\nmood = "x"'), "unknown key mood")


def valid_appends(s: Scratch) -> None:
    """A valid qc.toml: one record, its contract format 2."""
    repo = _target(s, VALID)
    rid = _append(s, repo, 0).strip()
    recs = _records(s, repo)
    assert [obj(r, "record")["id"] for r in recs] == [rid], recs
    contract = obj(obj(recs[0], "record")["contract"], "contract")
    assert get(contract, "format", int, "contract") == 2, contract


if __name__ == "__main__":
    main(wrong_format, unknown_field, valid_appends)
