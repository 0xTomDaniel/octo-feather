"""The scenario of tests/gate/kit/test_lane_merge_declaration.py (its item), this file its command
(testkit.main): `octo-feather-lane merge-ask` gives a tier 3 reason for each check the clear review
verdict classes `declaration` (spec issue-lifecycle #gates-tiers, row tier-declaration; issue
#1285), offline: the testkit's gh answers only real gh's recorded answers
(testkit/recordings/merge-tier-1285.json), never its store.

The realcase PR: on 0xTomDaniel/octo-feather-realcase, base branch gh1255-1285-base (B, the commit
lane_merge_tier.py builds), PR #43 (gh1255-1285-declaration, D: one commit adding check.py), its
verdict comment posted by `octo-feather-lane verdict` from a clear review report classing two
checks, one `class: declaration` and one `class: exact`, the PR body a section building no
criterion. The lane's parent is kit issue #1255 (key-from-branch of its gh1255 branch), so the
tape was recorded from a clone whose origin is the kit repo, running `merge-ask 43 --repo
0xTomDaniel/octo-feather-realcase`: the tracker reads #1255 there, no correction marker, no
replay. The scratch repo rebuilds B and D byte for byte (GIT_ENV) and records a full gate pass
at D, as the recording did.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, cast

from lane_merge_tier import APP, GIT_ENV, STATUS, B, block, status
from testkit import Scratch, kit, main

if TYPE_CHECKING:
    from testkit import Ran

L = kit("octo-feather-lane")
G = kit("octo-feather-gate")
TAPES = Path(__file__).parent / "testkit" / "recordings" / "merge-tier-1285.json"
REPO = "0xTomDaniel/octo-feather-realcase"
BASE = "gh1255-1285-base"
LANE = "gh1255-1285-declaration"
D = "706f8406acfa12a050851408306cb8028387848d"  # PR #43's headRefOid on its tape
CHECK_PY = '''"""Refuse a PR body that names no risk."""
import sys

body = sys.stdin.read()
if not any(ln.startswith("Risk: ") for ln in body.splitlines()):
    sys.exit("check: the PR body names no `Risk:` line")
'''


class Lane:
    """The scratch repo R, the realcase lane rebuilt on B, a full pass recorded at its head."""

    def __init__(self, s: Scratch) -> None:
        self.s, self.r = s, s.root / "repo"
        s.env.pop("HERDR_SESSION", None)
        s.env |= {"XDG_STATE_HOME": str(s.root / "xdg"), "OCTO_FEATHER_QC_DIR": str(s.root / "qc")}
        s.prepare("merge-tier-declaration", Lane.build)

    @staticmethod
    def build(s: Scratch) -> None:
        r = s.root / "repo"
        s.git(s.root, "init", "-q", "-b", BASE, "repo")
        for k, v in (
            ("user.email", "t@example.com"),
            ("user.name", "t"),
            ("commit.gpgsign", "false"),
        ):
            s.git(r, "config", k, v)

        def commit(msg: str, files: dict[str, str]) -> str:
            for name, text in files.items():
                (r / name).parent.mkdir(parents=True, exist_ok=True)
                (r / name).write_text(text)
            s.git(r, "add", "-A")
            s.run(["git", "-C", str(r), "commit", "-q", "-m", msg], env=GIT_ENV)
            return s.git(r, "rev-parse", "HEAD")

        assert commit("base", {"app.py": APP, STATUS: status(None)}) == B, "B rebuilt"
        s.git(r, "checkout", "-q", "-b", LANE)
        msg = "feat: refuse a PR body that names no risk"
        assert commit(msg, {"check.py": CHECK_PY}) == D, "D rebuilt"
        s.run([G, "record", "--reason", "recording", "--seconds", "1"], cwd=r)
        s.git(r, "update-ref", f"refs/remotes/origin/{BASE}", B)

    def ask(self, scenario: str) -> Ran:
        tapes = cast("dict[str, list[dict[str, object]]]", json.loads(TAPES.read_text()))
        (self.s.gh.dir / "tape.json").write_text(json.dumps(tapes[scenario]))
        return self.s.run([L, "merge-ask", "43", "--repo", REPO], cwd=self.r)


def tier_declaration(s: Scratch) -> None:
    """Realcase PR #43, its clear verdict classing one check as a declaration and one as exact,
    nothing else for the owner: tier 3, naming the declaration check alone, waiting for the
    owner."""
    out = Lane(s).ask("tier_declaration").out
    check = (
        "check.py: a PR body names its risk on a `Risk:` line (ADR 0008) | reads: the PR body's "
        "declared Risk line | class: declaration"
    )
    assert block(out) == ["Tier: 3", f"- declaration check: {check}", "Waits for: the owner"], out


if __name__ == "__main__":
    main(tier_declaration)
