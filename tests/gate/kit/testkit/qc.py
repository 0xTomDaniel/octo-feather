"""The qc scenarios' shared scratch target and runs (tests/gate/kit/qc_*.py): what `just qc` judges
is octo-feather-qc --help's, its contract quality spec #qc-contract."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

from testkit import FIXTURES, ROOT, Ran, Scratch, kit

if TYPE_CHECKING:
    from collections.abc import Mapping

STATUS = "docs/specs/demo.status.json"
MODEL = json.loads((ROOT / "evals" / "judgment-model.json").read_text())["model"]
RID = r"[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}"  # an evidence record id (octo-feather-evidence --help)
# Each qc run killed after this many seconds, as the old scripts bounded theirs: a hang fails.
LIMIT_S = "180"
# Unset in every qc scenario (clean), as the old qc scripts unset them: a Herdr pane's session, a
# qc report dir, a sandbox PATH, the stub judge's modes, a claims gate's claims.
UNSET = (
    "HERDR_SESSION",
    "HERDR_SOCKET_PATH",
    "HERDR_BIN_PATH",
    "HERDR_ENV",
    "OCTO_FEATHER_QC_DIR",
    "OCTO_FEATHER_QC_PATH",
    "OCTO_FEATHER_QC_CLAIMS",
    "FAKE_QC_JUDGE",
    "FAKE_QC_FAIL",
)


def clean(s: Scratch) -> None:
    """S's env without UNSET."""
    for k in UNSET:
        s.env.pop(k, None)


def report(r: Ran) -> dict[str, object]:
    """Qc run R's report: the file its last stdout line names (octo-feather-qc --help, Report)."""
    return json.loads(Path(r.out.splitlines()[-1].rpartition("; report ")[2]).read_text())


def block(out: str, first: str, n: int = 2) -> list[str]:
    """The result block in qc's stdout OUT whose first line starts FIRST: it and the N lines
    after it (as grep -A N); empty when none does."""
    ls = out.splitlines()
    k = next((i for i, x in enumerate(ls) if x.startswith(first)), None)
    return [] if k is None else ls[k : k + n + 1]


def target(s: Scratch, files: Mapping[str, str] = {}) -> Path:
    """S's repo: the good demo spec (tests/fixtures/spec-status/good) and FILES committed, its
    status file then initialized at that commit (octo-feather-spec-status init) and committed."""
    r = s.root / "repo"
    (r / "docs" / "specs").mkdir(parents=True)
    s.git(r, "init", "-q", "-b", "main")
    for k, v in (("user.email", "t@t"), ("user.name", "t"), ("commit.gpgsign", "false")):
        s.git(r, "config", k, v)
    shutil.copy(FIXTURES / "spec-status" / "good" / "demo.spec.html", r / "docs" / "specs")
    for name, text in files.items():
        (r / name).parent.mkdir(parents=True, exist_ok=True)
        (r / name).write_text(text)
    s.git(r, "add", "-A")
    s.git(r, "commit", "-qm", "accepted")
    short = s.git(r, "rev-parse", "--short", "HEAD")
    s.run([kit("octo-feather-spec-status"), "init", "docs/specs/demo.spec.html", short], cwd=r)
    s.git(r, "add", "-A")
    s.git(r, "commit", "-qm", "status")
    return r


def qc(s: Scratch, repo: Path, *args: str, want: int, env: Mapping[str, str] | None = None) -> Ran:
    """`octo-feather-qc STATUS ARGS...` (what `just qc` runs) in REPO, bounded by LIMIT_S."""
    return s.run(
        ["timeout", "-k", "5", LIMIT_S, kit("octo-feather-qc"), STATUS, *args],
        want=want,
        cwd=repo,
        env=env,
    )


def reports(s: Scratch, head: str) -> list[dict[str, object]]:
    """The qc reports at HEAD, oldest first (octo-feather-qc --help, Report)."""
    q = Path(s.run([kit("octo-feather-state")]).out) / "qc"
    return [json.loads(p.read_text()) for p in sorted(q.glob(f"{head}-*.json"))]
