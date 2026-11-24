"""The scenarios of tests/gate/kit/test_lane_merge_tier.py (its items), this file their command
(testkit.main): `octo-feather-lane merge-ask` sorts the ask into a tier and prints its block, `Tier:
N`, a `- <reason>` line each, `Waits for: ...` (spec issue-lifecycle #gates-tiers,
#gates-tier-relay; issue #1257), offline: the testkit's gh answers only real gh's recorded answers
(testkit/recordings/merge-tier-1257.json, one tape per scenario), never its store.

The realcase PRs (RealCase): on 0xTomDaniel/octo-feather-realcase (the standing private test
repo), base branch gh1255-1257-base (B: app.py and a status file, criteria a, b, c planned); PR #1
a lane on gh1255-1257-tier (J changes app.py's line 1, qc's status commit H builds a and b with PR
#1), its clear review verdict on J posted by octo-feather-lane verdict; PR #2 a spec PR on
gh1255-1257-spec (S adds the accepted spec and its status file, no criterion claimed), its clear
verdict on S; PR #3 on gh1255-1257-other (X sets app.py's line 1 otherwise: it conflicts with H).
Each tape is one real merge-ask run, the PR body as the scenario names it: tier_one (PR #1, a
complete section, #2 open), spec_pr (PR #2, #1 open), tier_failed (PR #1, `Failed:` listing
demo#acceptance-c with its triage, its fail row added), failing_ask (that body, its Head naming J:
stale), order_waits (PR #1's complete section, #2 and #3 open). The scratch repo rebuilds those
commits byte for byte (GIT_ENV), the full gate pass recorded at J and S as the recording did.

The history cases (History): merged kit PRs replayed at their merged head from a scratch repo
borrowing the kit's objects (git alternates), the base their merge commit's first parent, a full
pass recorded there: #1184, whose section carries two `Owner decision N (...):` lines, and #1248,
the spec PR merged with no `## Merge ask` section (a failing ask). Their merge order reads today's
open PRs on main (the tape) against what this repo's objects hold, so only the tier lines it does
not move are asserted.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, cast

from testkit import ROOT, Scratch, kit, main

if TYPE_CHECKING:
    from testkit import Ran

L = kit("octo-feather-lane")
G = kit("octo-feather-gate")
TAPES = Path(__file__).parent / "testkit" / "recordings" / "merge-tier-1257.json"
DATE = "2026-11-24T00:00:00Z"
GIT_ENV = {
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@example.com",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@example.com",
    "GIT_AUTHOR_DATE": DATE,
    "GIT_COMMITTER_DATE": DATE,
}
BASE = "gh1255-1257-base"
STATUS = "docs/specs/demo.status.json"
# the realcase commits as pushed (each PR's headRefOid on its tape)
B = "3f40ebe2b39954920c03fdf9047532177fcbf808"
J = "0eba0fe0257ddb91c247f48729ae089b4429be31"
H = "e8bfbde9214fb295e00da7aa4994c2807513fb71"
S = "cb18ec8681b3161c6506d0c50182a9f3fbe0f13f"
X = "0cbc5ea84c17be0f88f3c18cf311b412ca9e8985"
APP = "".join(f"{i}\n" for i in range(1, 21))
INCOMPLETE = "Incomplete merge ask (it fails below; never send this tier):"
FAILED = "- failed criterion demo#acceptance-c: repair ticket #99"


def block(out: str) -> list[str]:
    """The tier block OUT prints: `Tier:` to its `Waits for:` line."""
    lines = out.splitlines()
    starts = [i for i, ln in enumerate(lines) if ln.startswith("Tier: ")]
    assert len(starts) == 1, f"not one tier block: {out}"
    i = starts[0]
    j = next(k for k in range(i, len(lines)) if lines[k].startswith("Waits for: "))
    return lines[i : j + 1]


def on_tape(s: Scratch, scenario: str) -> None:
    """S's gh answering only SCENARIO's recordings."""
    tapes = cast("dict[str, list[dict[str, object]]]", json.loads(TAPES.read_text()))
    (s.gh.dir / "tape.json").write_text(json.dumps(tapes[scenario]))


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
    """The scratch repo R, the realcase commits rebuilt, checked out at H on the lane branch."""

    def __init__(self, s: Scratch) -> None:
        self.s, self.r = s, s.root / "repo"
        s.env.pop("HERDR_SESSION", None)
        s.env |= {"XDG_STATE_HOME": str(s.root / "xdg"), "OCTO_FEATHER_QC_DIR": str(s.root / "qc")}
        s.prepare("merge-tier-realcase", RealCase.build)

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

        def record(sha: str) -> None:
            s.git(r, "checkout", "-q", "--detach", sha)
            s.run([G, "record", "--reason", "recording", "--seconds", "1"], cwd=r)

        line1 = APP.split("\n", 1)[1]
        assert commit("base", {"app.py": APP, STATUS: status(None)}) == B, "B rebuilt"
        s.git(r, "checkout", "-q", "-b", "gh1255-1257-tier")
        assert commit("feat: x", {"app.py": "one\n" + line1}) == J, "J rebuilt"
        assert (
            commit(f"qc: built acceptance-a acceptance-b (judged {J[:12]})", {STATUS: status(1)})
            == H
        )
        s.git(r, "checkout", "-q", "--detach", B)
        spec = {"acceptance-z": {"status": "planned", "pr": None}}
        files = {
            "docs/specs/demo2.spec.html": "<p>the accepted spec</p>\n",
            "docs/specs/demo2.status.json": json.dumps(
                {"spec": "demo2.spec.html", "accepted_commit": "0123abc", "criteria": spec}
            )
            + "\n",
        }
        assert commit("spec: demo2, accepted", files) == S, "S rebuilt"
        s.git(r, "checkout", "-q", "--detach", B)
        assert commit("feat: other", {"app.py": "uno\n" + line1}) == X, "X rebuilt"
        record(J)
        record(S)
        s.git(r, "checkout", "-q", "gh1255-1257-tier")
        s.git(r, "update-ref", f"refs/remotes/origin/{BASE}", B)

    def ask(self, scenario: str, pr: int, want: int = 0) -> Ran:
        on_tape(self.s, scenario)
        st = ["--status", STATUS] if pr == 1 else []
        return self.s.run([L, "merge-ask", str(pr), *st], want=want, cwd=self.r)


def history(s: Scratch, pr: int, head: str, base: str) -> Path:
    """A scratch repo borrowing the kit's objects at merged PR's HEAD, origin/main at BASE (its
    merge commit's first parent), a full pass recorded there; S's gh on PR's tape."""
    s.env.pop("HERDR_SESSION", None)
    s.env |= {"XDG_STATE_HOME": str(s.root / "xdg"), "OCTO_FEATHER_QC_DIR": str(s.root / "qc")}
    r = s.root / "repo"
    common = s.run(
        ["git", "-C", str(ROOT), "rev-parse", "--path-format=absolute", "--git-common-dir"]
    )
    s.run(["git", "init", "-q", "-b", "lane", str(r)])
    (r / ".git" / "objects" / "info" / "alternates").write_text(common.out + "/objects\n")
    has = subprocess.run(  # git from PATH
        ["git", "-C", str(r), "cat-file", "-e", f"{head}^{{commit}}"],  # noqa: S607
        check=False,
    )
    assert has.returncode == 0, f"the kit repo lacks PR #{pr}'s head: git fetch origin main"
    for k, v in (("user.email", "t@example.com"), ("user.name", "t"), ("commit.gpgsign", "false")):
        s.git(r, "config", k, v)
    s.git(r, "update-ref", "refs/remotes/origin/main", base)
    s.git(r, "reset", "-q", "--hard", head)
    s.run([G, "record", "--reason", "replay", "--seconds", "1"], cwd=r)
    on_tape(s, f"history_{pr}")
    return r


def history_ask(s: Scratch, r: Path, pr: int, want: int) -> Ran:
    st = [
        x
        for p in sorted((r / "docs" / "specs").glob("*.status.json"))
        for x in ("--status", str(p.relative_to(r)))
    ]
    return s.run([L, "merge-ask", str(pr), *st], want=want, cwd=r)


def tier_one(s: Scratch) -> None:
    """Realcase PR #1, a complete section, #2 open and setting nothing back: tier 1, no reason,
    waiting for nobody, printed after the section on stdout."""
    out = RealCase(s).ask("tier_one", 1).out
    assert block(out) == ["Tier: 1", "Waits for: nobody"], out
    lines = out.splitlines()
    assert lines.index("Tier: 1") > lines.index("Failed: none"), out


def tier_failed(s: Scratch) -> None:
    """Realcase PR #1 passing with `Failed:` listing demo#acceptance-c and its triage: tier 3,
    naming it, waiting for the owner."""
    out = RealCase(s).ask("tier_failed", 1).out
    assert block(out) == ["Tier: 3", FAILED, "Waits for: the owner"], out


def order_waits(s: Scratch) -> None:
    """Realcase PR #1's complete section with #3 open, its head conflicting with #1's in app.py:
    tier 1, waiting for the director's order, naming #3."""
    out = RealCase(s).ask("order_waits", 1).out
    why = "PR #3: its head conflicts with this head in app.py"
    assert block(out) == ["Tier: 1", f"Waits for: the director's order ({why})"], out


def spec_pr(s: Scratch) -> None:
    """Realcase PR #2, the accepted spec plus its status file, Built and Failed none, no criterion
    row: tier 1, waiting for nobody."""
    out = RealCase(s).ask("spec_pr", 2).out
    assert block(out) == ["Tier: 1", "Waits for: nobody"], out


def failing_ask(s: Scratch) -> None:
    """Realcase PR #1 with Failed listing a criterion and its Head stale: exit 1, stdout empty, its
    tier block on stderr after the incomplete mark, before the items. Kit PR #1248, merged with no
    section: the same, at tier 1."""
    r: Ran = RealCase(s).ask("failing_ask", 1, want=1)
    assert not r.out, f"a failing merge ask printed to stdout: {r.out}"
    err = r.err.splitlines()
    i = err.index(INCOMPLETE)
    assert err[i + 1 : i + 4] == ["Tier: 3", FAILED, "Waits for: the owner"], r.err
    assert i < next(k for k, x in enumerate(err) if "merge ask incomplete" in x), r.err


def failing_history(s: Scratch) -> None:
    """Kit PR #1248, the spec PR merged with no `## Merge ask` section: exit 1, stdout empty,
    `Tier: 1` on stderr after the incomplete mark, waiting for the director's order: open PR
    #1246's pinned runs are not read (a real unread merge order)."""
    head, base = (
        "08548de59a78ea1644fab491706bbdef7250de49",
        "7b39556a6f17b02665bf92194b302842a9fe5219",
    )
    r = history_ask(s, history(s, 1248, head, base), 1248, 1)
    assert not r.out, f"a failing merge ask printed to stdout: {r.out}"
    err = r.err.splitlines()
    i = err.index(INCOMPLETE)
    assert err[i + 1] == "Tier: 1", r.err
    # the tape's open PR #1246 pins runs no qa store here holds: a merge-order read that failed,
    # so the ask cannot prove no PR is set back and waits for the director's order
    assert err[i + 2].startswith("Waits for: the director's order ("), r.err
    # read here (its pins), or its head not in this repo's objects (the PR not read): unread both
    assert "PR #1246: its pinned run " in err[i + 2] or "not read: PR #1246 " in err[i + 2], r.err
    assert "`## Merge ask` section: none in the PR body" in r.err, r.err


def owner_decision(s: Scratch) -> None:
    """Kit PR #1184, its section carrying `Owner decision 1 (...): ...` and `Owner decision 2
    (optional): ...` at column 0: tier 3, each shown as written, waiting for the owner."""
    head, base = (
        "e43afc656d1117c7cce58b57f259f42566e9a707",
        "6adc851386f7a846346c37f28c87264e30a3dd3a",
    )
    out = history_ask(s, history(s, 1184, head, base), 1184, 0).out
    got = block(out)
    assert got[0] == "Tier: 3", out
    assert got[-1] == "Waits for: the owner", out
    assert len(got) == 4, got
    assert got[1].startswith(
        "- Owner decision 1 (the pre-commit hook, not built; moved from #1183 "
    ), got
    assert got[2].startswith("- Owner decision 2 (optional): #1178 reverted"), got


if __name__ == "__main__":
    main(tier_one, tier_failed, order_waits, spec_pr, failing_ask, failing_history, owner_decision)
