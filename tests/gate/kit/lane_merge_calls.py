"""The scenarios of tests/gate/kit/test_lane_merge_calls.py (its items), this file their command
(testkit.main): `octo-feather-lane merge-ask` sorts the spec calls the lane diff adds into the
tier (spec issue-lifecycle #gates-tiers; issue #1258; the block's form: octo-feather-lane --help,
merge-ask), offline: the testkit's gh answers only real gh's recorded answers
(testkit/recordings/merge-tier-1258.json, one tape per scenario), never its store.

The realcase PRs (RealCase): on 0xTomDaniel/octo-feather-realcase, each lane its own base branch
gh1255-1258-base-<lane> at B (app.py, the demo status file, criteria a, b, c planned, and a call
log holding an earlier lane's adds call: never the lane's), so no PR of these sets another back.
Each lane branch gh1255-1258-<lane> commits J (app.py's line 1, one call appended to
docs/specs/demo.calls.jsonl), then qc's status commit H building a and b with its PR; its clear
review verdict on J posted by octo-feather-lane verdict. PRs: #21 clarify (a clarifies call), #22
adds, #23 weakens (no ruling), #24 ruled (an adds call linking the owner's ruling, issue #20's
comment, made before the call; the verdict's report carried `Ruling covers: <it>`), #25
unconfirmed (the same J as #24, its verdict silent), #26 denied (an adds call the owner denied).
Each tape is one real merge-ask run on its PR with a complete section; tier_highest is #21's with
`Failed:` listing demo#acceptance-c with its triage, its fail row added. The scratch repo rebuilds
those commits byte for byte (GIT_ENV), a full gate pass recorded at each J as the recording did.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, cast

from lane_merge_tier import GIT_ENV, block
from testkit import Scratch, kit, main

if TYPE_CHECKING:
    from testkit import Ran

L = kit("octo-feather-lane")
G = kit("octo-feather-gate")
TAPES = Path(__file__).parent / "testkit" / "recordings" / "merge-tier-1258.json"
STATUS = "docs/specs/demo.status.json"
CALLS = "docs/specs/demo.calls.jsonl"
APP = "".join(f"{i}\n" for i in range(1, 21))
AT = "2026-11-24T22:35:47Z"  # the lanes' calls, made after the ruling
RULING = "https://github.com/0xTomDaniel/octo-feather-realcase/issues/20#issuecomment-7146417272"
RULED_AT = "2026-11-24T22:35:41Z"  # GitHub's created_at of RULING
# the realcase commits as pushed: B, then per lane (J, H, its PR)
B = "c062ef8d1b9625e5b34b5aa443a8929b5a5c8798"
LANES = {
    "clarify": (
        "fc7089e7b532889b078f801deacfec4394bb5963",
        "b3700d45b503c5c63906c10814fbc11ed0288158",
        21,
    ),
    "adds": (
        "2672059cb1f2bd8a3d04719480a4d4ffa9c16348",
        "382aee818332718417cdb62b3f856e7a8be3c0c2",
        22,
    ),
    "weakens": (
        "a4a1e560d42a4b4f45cc2bfc262b0a7983389d24",
        "ffabe3fe98326876e84bdd608979358913af8ac2",
        23,
    ),
    "ruled": (
        "dd7c79c40a3a31468b053b91e821882be34bc6f9",
        "a818206696e85f0b22a54e214936997772ec1d62",
        24,
    ),
    "unconfirmed": (
        "dd7c79c40a3a31468b053b91e821882be34bc6f9",
        "13ba0786a8c956eb8af79bdf33e51afb8e372204",
        25,
    ),
    "denied": (
        "25df3ae49ffe18411eb99ec4d3abb8a2a9b4aa61",
        "70b65937352665199b0768cb17a7da7e2e578683",
        26,
    ),
}
FAILED = "- failed criterion demo#acceptance-c: repair ticket #99"


def call(at: str, kind: str, anchors: list[str], what: str, **extra: object) -> str:
    """One call log line as the recording wrote it."""
    c = {
        "at": at,
        "lane": "gh1255",
        "role": "supervisor",
        "kind": kind,
        "anchors": anchors,
        "criteria": [a for a in anchors if a.startswith("acceptance-")],
        "what": what,
        "why": "the realcase recording for #1258",
        "passes_as_written": False,
        "evidence": "a recorded case of the merge ask's tier (octo-feather #1258)",
        **extra,
    }
    return json.dumps(c) + "\n"


PRIOR = call("2026-11-01T00:00:00Z", "adds", ["acceptance-c"], "an earlier lane added acceptance-c")
ADDS_D = "adds acceptance-d"
CALL = {
    "clarify": call(AT, "clarifies", ["acceptance-a"], "acceptance-a's wording made exact"),
    "adds": call(AT, "adds", ["acceptance-d"], ADDS_D),
    "weakens": call(
        AT, "weakens", ["acceptance-c"], "acceptance-c no longer asks for the second case"
    ),
    "ruled": call(AT, "adds", ["acceptance-d"], f"{ADDS_D}, as the owner ruled", ruling=RULING),
    "denied": call(
        AT,
        "adds",
        ["acceptance-e"],
        "adds acceptance-e",
        denied={"at": "2026-11-24T22:36:42Z", "note": "the owner denied it: not in this spec"},
    ),
}


def status(pr: int | None) -> str:
    """The demo status file: a and b built with PR (planned with none), c planned."""
    ab = {"status": "built", "pr": pr} if pr else {"status": "planned", "pr": None}
    crit = {
        "acceptance-a": ab,
        "acceptance-b": ab,
        "acceptance-c": {"status": "planned", "pr": None},
    }
    spec = {"spec": "demo.spec.html", "accepted_commit": "0123abc", "criteria": crit}
    return json.dumps(spec) + "\n"


class RealCase:
    """The scratch repo R, the realcase commits rebuilt, each lane on its branch."""

    def __init__(self, s: Scratch) -> None:
        self.s, self.r = s, s.root / "repo"
        s.env.pop("HERDR_SESSION", None)
        s.env |= {"XDG_STATE_HOME": str(s.root / "xdg"), "OCTO_FEATHER_QC_DIR": str(s.root / "qc")}
        s.prepare("merge-calls-realcase", RealCase.build)

    @staticmethod
    def build(s: Scratch) -> None:
        r = s.root / "repo"
        s.git(s.root, "init", "-q", "-b", "gh1255-1258-base", "repo")
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

        assert commit("base", {"app.py": APP, STATUS: status(None), CALLS: PRIOR}) == B
        line1 = APP.split("\n", 1)[1]
        for lane, (j, h, pr) in LANES.items():
            s.git(r, "update-ref", f"refs/remotes/origin/gh1255-1258-base-{lane}", B)
            if lane == "unconfirmed":  # #24's J, its own qc commit
                s.git(r, "checkout", "-q", "-b", f"gh1255-1258-{lane}", j)
            else:
                s.git(r, "checkout", "-q", "-b", f"gh1255-1258-{lane}", B)
                got = commit(
                    f"feat: {lane}", {"app.py": f"{lane}\n{line1}", CALLS: PRIOR + CALL[lane]}
                )
                assert got == j, f"J of {lane} rebuilt"
            msg = f"qc: built acceptance-a acceptance-b (judged {j[:12]})"
            assert commit(msg, {STATUS: status(pr)}) == h, f"H of {lane} rebuilt"
        for j in sorted({j for j, _, _ in LANES.values()}):
            s.git(r, "checkout", "-q", "--detach", j)
            s.run([G, "record", "--reason", "recording", "--seconds", "1"], cwd=r)

    def ask(self, scenario: str, lane: str) -> Ran:
        """merge-ask on LANE's PR, S's gh answering only SCENARIO's recordings."""
        tapes = cast("dict[str, list[dict[str, object]]]", json.loads(TAPES.read_text()))
        (self.s.gh.dir / "tape.json").write_text(json.dumps(tapes[scenario]))
        self.s.git(self.r, "checkout", "-q", f"gh1255-1258-{lane}")
        pr = str(LANES[lane][2])
        return self.s.run([L, "merge-ask", pr, "--status", STATUS], cwd=self.r)


def name(kind: str, anchor: str) -> str:
    return f"- spec call demo {AT} {kind} {anchor}"


def tier_clarify(s: Scratch) -> None:
    """Realcase PR #21, one clarifying call and nothing else, the base holding an earlier lane's
    call: issue-lifecycle#acceptance-tier-clarify (the reason's form: octo-feather-lane --help,
    merge-ask)."""
    out = RealCase(s).ask("tier_clarify", "clarify").out
    assert block(out) == ["Tier: 2", name("clarifies", "acceptance-a"), "Waits for: nobody"], out


def tier_adds(s: Scratch) -> None:
    """Realcase PR #22, an adds call linking no ruling: issue-lifecycle#acceptance-tier-adds
    (the reason's form: octo-feather-lane --help, merge-ask)."""
    out = RealCase(s).ask("tier_adds", "adds").out
    want = f"{name('adds', 'acceptance-d')}: no ruling linked"
    assert block(out) == ["Tier: 3", want, "Waits for: the owner"], out


def tier_weakens(s: Scratch) -> None:
    """Realcase PR #23, a weakens call linking no ruling: issue-lifecycle#acceptance-tier-weakens
    (the reason's form: octo-feather-lane --help, merge-ask)."""
    out = RealCase(s).ask("tier_weakens", "weakens").out
    want = f"{name('weakens', 'acceptance-c')}: no ruling linked"
    assert block(out) == ["Tier: 3", want, "Waits for: the owner"], out


def tier_ruled(s: Scratch) -> None:
    """Realcase PR #24, an adds call linking the owner's ruling made before it, the verdict carrying
    `Ruling covers:` it: issue-lifecycle#acceptance-tier-ruled (the reason's form: octo-feather-lane
    --help, merge-ask)."""
    out = RealCase(s).ask("tier_ruled", "ruled").out
    want = (
        f"{name('adds', 'acceptance-d')}: ruled by {RULING} ({RULED_AT}), the review verdict "
        "covers it"
    )
    assert block(out) == ["Tier: 2", want, "Waits for: nobody"], out


def tier_ruling_unconfirmed(s: Scratch) -> None:
    """Realcase PR #25, the same call, the verdict silent on the ruling:
    issue-lifecycle#acceptance-tier-ruling-unconfirmed (the reason's form: octo-feather-lane --help,
    merge-ask)."""
    out = RealCase(s).ask("tier_ruling_unconfirmed", "unconfirmed").out
    got = block(out)
    assert got[0] == "Tier: 3", out
    assert got[-1] == "Waits for: the owner", out
    assert len(got) == 3, got
    assert got[1].startswith(f"{name('adds', 'acceptance-d')}: ruling {RULING} "), got
    assert got[1].endswith(f"the review verdict carries no `Ruling covers: {RULING}`"), got


def tier_denied(s: Scratch) -> None:
    """Realcase PR #26, an adds call the owner denied (the reason's form: octo-feather-lane --help,
    merge-ask)."""
    out = RealCase(s).ask("tier_denied", "denied").out
    want = f"{name('adds', 'acceptance-e')}: denied 2026-11-24T22:36:42Z"
    assert block(out) == ["Tier: 2", want, "Waits for: nobody"], out


def tier_highest(s: Scratch) -> None:
    """Realcase PR #21's clarifying call with `Failed:` listing demo#acceptance-c:
    issue-lifecycle#acceptance-tier-highest (the reason's form: octo-feather-lane --help,
    merge-ask)."""
    out = RealCase(s).ask("tier_highest", "clarify").out
    want = ["Tier: 3", FAILED, name("clarifies", "acceptance-a"), "Waits for: the owner"]
    assert block(out) == want, out


if __name__ == "__main__":
    main(
        tier_clarify,
        tier_adds,
        tier_weakens,
        tier_ruled,
        tier_ruling_unconfirmed,
        tier_denied,
        tier_highest,
    )
