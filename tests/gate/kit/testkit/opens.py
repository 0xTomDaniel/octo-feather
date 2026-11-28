"""A stand-in open record for a scenario's stored eval runs made without the qc sandbox (a stub
suite's in-process runs, a run written by hand): each current run of a case dir gets, in its
sandbox.json, the open record the sandbox stores (eval-cases schema, Open record) and the proof
line naming the kit under test, as octo-feather-qa --verdict reads them (its --help, Verdict).
A real one: tests/fixtures/qa-open-record (qa_pinned_opens.py)."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path


def opens_whole(
    case_dir: Path, kit: Path, files: Sequence[str] = (), dirs: Sequence[str] = ()
) -> None:
    """Each run of CASE_DIR's result.json `runs` (none: the case dir itself) given a whole open
    record of FILES and DIRS, its proof naming KIT the kit under test; a run with no transcript
    an empty one."""
    res = json.loads((case_dir / "result.json").read_text())
    for r in cast("list[dict[str, object]]", res.get("runs") or [{"dir": "."}]):
        rd = case_dir / str(r.get("dir", "."))
        sb = rd / "sandbox.json"
        rec = cast("dict[str, object]", json.loads(sb.read_text())) if sb.is_file() else {}
        proof = [*cast("list[str]", rec.get("proof") or [])]
        proof.append(f"qc sandbox: ok   kit under test {kit} is its own read-only view")
        rec |= {"proof": proof, "opens": {"whole": True, "files": [*files], "dirs": [*dirs]}}
        sb.write_text(json.dumps(rec))
        (rd / "transcript.jsonl").touch()
