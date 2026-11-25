"""The scenarios of tests/gate/kit/test_lane_merge_optout.py (its items), this file their command
(testkit.main): `octo-feather-lane merge-ask` reads the owner decision lines of the review verdict
comment and the lane's behaviour-neutral opt-outs into its tier (spec issue-lifecycle #gates-tiers;
issue #1259), offline: the testkit's gh answers only real gh's recorded answers
(testkit/recordings/merge-tier-1259.json, one tape per scenario), never its store.

The realcase PRs: on 0xTomDaniel/octo-feather-realcase, base branch gh1255-1259-base (B, the
commit lane_merge_tier.py builds), each lane's verdict comment posted by `octo-feather-lane
verdict` from its review report, the PR body a section building no criterion: PR #16
(gh1255-1259-cleared, C: one Behaviour-neutral commit adding agents/cleared.md, its verdict
`Opt-out cleared: 6195f3b`), PR #17 (gh1255-1259-uncleared, U: the same shape, its verdict naming
no opt-out), PR #18 (gh1255-1259-decision, D: lib.py, its verdict carrying `Owner decision: ...`),
PR #19 (gh1255-1259-demo, two Behaviour-neutral commits A1 and A2, its verdict clearing A1 and
carrying an owner decision line). Each tape is one real merge-ask run with all four open. The
scratch repo rebuilds those commits byte for byte (GIT_ENV) and records a full gate pass at each
head, as the recording did.
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
TAPES = Path(__file__).parent / "testkit" / "recordings" / "merge-tier-1259.json"
BASE = "gh1255-1259-base"
NOTE = "Behaviour-neutral: a new note no role loads"
# each lane branch: its commits (message, files) on B, and its head as pushed (headRefOid)
LANES: dict[str, tuple[list[tuple[str, dict[str, str]]], str]] = {
    "cleared": (
        [
            (
                f"docs(agents): a cleared note\n\n{NOTE}",
                {"agents/cleared.md": "A note no role loads.\n"},
            )
        ],
        "6195f3b615ad1ce1b12fd9c4d2815d24acc1640d",
    ),
    "uncleared": (
        [
            (
                f"docs(agents): an uncleared note\n\n{NOTE}",
                {"agents/uncleared.md": "A note no role loads.\n"},
            )
        ],
        "eac74d94c741e5e83829dbde56536d3ae22ada09",
    ),
    "decision": (
        [("feat: the sandbox switch", {"lib.py": "SANDBOX = False\n"})],
        "da6fc7a9ec7d841543d712ad3cc50710c3380991",
    ),
    "demo": (
        [
            (f"docs(agents): note a\n\n{NOTE}", {"agents/demo-a.md": "Note a.\n"}),
            (f"docs(agents): note b\n\n{NOTE}", {"agents/demo-b.md": "Note b.\n"}),
        ],
        "fe72f6c047274f614feef7fc5f94c444f195bb03",
    ),
}
PRS = {"cleared": 16, "uncleared": 17, "decision": 18, "demo": 19}


class Lanes:
    """The scratch repo R, the realcase lanes rebuilt on B, a full pass recorded at each head."""

    def __init__(self, s: Scratch) -> None:
        self.s, self.r = s, s.root / "repo"
        s.env.pop("HERDR_SESSION", None)
        s.env |= {"XDG_STATE_HOME": str(s.root / "xdg"), "OCTO_FEATHER_QC_DIR": str(s.root / "qc")}
        s.prepare("merge-tier-optout", Lanes.build)

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
        for lane, (commits, head) in LANES.items():
            s.git(r, "checkout", "-q", "-b", f"gh1255-1259-{lane}", B)
            got = [commit(msg, files) for msg, files in commits]
            assert got[-1] == head, f"{lane} rebuilt"
            s.git(r, "checkout", "-q", "--detach", head)
            s.run([G, "record", "--reason", "recording", "--seconds", "1"], cwd=r)
        s.git(r, "update-ref", f"refs/remotes/origin/{BASE}", B)

    def ask(self, scenario: str, lane: str) -> Ran:
        tapes = cast("dict[str, list[dict[str, object]]]", json.loads(TAPES.read_text()))
        (self.s.gh.dir / "tape.json").write_text(json.dumps(tapes[scenario]))
        self.s.git(self.r, "checkout", "-q", f"gh1255-1259-{lane}")
        return self.s.run([L, "merge-ask", str(PRS[lane])], cwd=self.r)


CLEARED = "cleared by the review verdict: " + NOTE
UNCLEARED = "not cleared by the review verdict: " + NOTE


def optout_cleared(s: Scratch) -> None:
    """Realcase PR #16, one opt-out its clear verdict names cleared:
    issue-lifecycle#acceptance-tier-optout-cleared (the reason's form: octo-feather-lane --help,
    merge-ask)."""
    out = Lanes(s).ask("optout_cleared", "cleared").out
    assert block(out) == ["Tier: 2", f"- opt-out 6195f3b {CLEARED}", "Waits for: nobody"], out


def optout_uncleared(s: Scratch) -> None:
    """Realcase PR #17, one opt-out its clear verdict does not name:
    issue-lifecycle#acceptance-tier-optout-uncleared (the reason's form: octo-feather-lane --help,
    merge-ask)."""
    out = Lanes(s).ask("optout_uncleared", "uncleared").out
    want = ["Tier: 3", f"- opt-out eac74d9 {UNCLEARED}", "Waits for: the owner"]
    assert block(out) == want, out


def owner_decision_verdict(s: Scratch) -> None:
    """Realcase PR #18, its clear verdict carrying an `Owner decision:` line, the section none:
    issue-lifecycle#acceptance-tier-owner-decision (the reason's form: octo-feather-lane --help,
    merge-ask)."""
    out = Lanes(s).ask("owner_decision_verdict", "decision").out
    line = "Owner decision: lib.py adds SANDBOX = False, a change to the sandbox policy (ADR 0022)"
    assert block(out) == ["Tier: 3", f"- {line}", "Waits for: the owner"], out


def demo(s: Scratch) -> None:
    """Realcase PR #19, two opt-outs (A1 cleared, A2 not) and an owner decision line, each a
    reason (the reason's form: octo-feather-lane --help, merge-ask)."""
    out = Lanes(s).ask("demo", "demo").out
    assert block(out) == [
        "Tier: 3",
        "- Owner decision: the demo lane asks the owner to read its notes",
        f"- opt-out 86fdb97 {CLEARED}",
        f"- opt-out fe72f6c {UNCLEARED}",
        "Waits for: the owner",
    ], out


if __name__ == "__main__":
    main(optout_cleared, optout_uncleared, owner_decision_verdict, demo)
