"""The scenarios of tests/gate/kit/test_lane_merge_guard.py (its items), this file their command
(testkit.main): `octo-feather-lane merge` and `octo-feather-lane relay` (their rules:
`octo-feather-lane --help`, merge and relay; issue #1266), offline: the testkit's gh answers only
real gh's recorded answers (testkit/recordings/merge-guard-1266.json, one tape per scenario),
never its store.

The realcase (0xTomDaniel/octo-feather-realcase, public, throwaway content): base branch
gh1255-1266-base (BASE: app.py, the demo status file, its CI also on a push to that branch);
PR #34 on gh1255-1266-order (app.py line 1 B; issue #31), #35 on gh1255-1266-other (app.py line
1 C: it conflicts with #34), PR #36 on gh1255-1266-owner (adds d.py, R; issue #32), its
section's `Failed:` listing demo#acceptance-c; PR #39 on gh1255-1266-self2 (adds e.py and a
clarifying spec call in docs/specs/demo.calls.jsonl: tier 2; issue #37), PR #40 on
gh1255-1266-order2 (app.py line 2 G and the same call: tier 2; issue #38), #41 on
gh1255-1266-other2 (app.py line 2 H: it conflicts with #40). Each section names its head,
`Built: none`. The scenario's world (World): the realcase's objects
(testkit/recordings/realcase-1266.bundle, fetched after the recordings, so GitHub's merge commits
too), the base checked out at the base as recorded, the lane worktree at the head, a scratch
state dir holding the lane's record and director.toml (the director's pane zd1:p1, the
supervisor's zs1:p1), a scratch kit install of the kit repo (step 3 leaves it, the PR being
another repo's), Herdr's stand-in. Each command runs in the lane worktree, with `--repo`.
Recorded in this order, each a real run from such a world (2026-11-24): owner and order (each
refused, nothing merged); #33 and #34 merged (B2); the fix F pushed to #36, head (refused); B2
merged into #36 as M2, carry (#36 merged, B3); #35 closed (it conflicts with B3), self_merge (#39
merged, B4), relayed (#40 refused, then merged on the relay).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING, cast

from herdr_messaging import ASSETS, agent
from testkit import Scratch, kit, main

if TYPE_CHECKING:
    from testkit import Ran

L = kit("octo-feather-lane")
HERE = Path(__file__).parent / "testkit" / "recordings"
TAPES = HERE / "merge-guard-1266.json"
REPO = "0xTomDaniel/octo-feather-realcase"
BASE = "gh1255-1266-base"
SUP, DIRECTOR = "zs1:p1", "zd1:p1"
# the realcase commits as pushed (each PR's headRefOid on its tape)
B0 = "f0885dccda3fd182fdd221122e8659b0b8106d1c"  # the base before any merge
HB = "9bc1520502a9731ef9d417cceb64110c16e55893"  # PR #34's head
B2 = "a2bea8864634735a84ac298c75a3a500cc90fc17"  # the base once #34 merged too
F = "7f7e09c5147b71f4e26d7f18c9fd1a901ffcb208"  # PR #36's fix commit after R
M2 = "16dc9236b3d097aa39d0c67b437855adcb9c84cb"  # PR #36's clean merge of B2 after F
B3 = "d96a6756a9adfd27ebb6048f47bafa47ec4218d9"  # the base once #36 merged too
E = "7c8fd62a66adf15c5f0f074565989da29125a9a2"  # PR #39's head
B4 = "4808a098fb1c06a2aeb3e10528ad83ecec073add"  # the base once #39 merged
G = "bd4fccb637aa804ac5b053e27e23287519920efa"  # PR #40's head
R = "d44992873d6361b0a58179e352005b908edef91e"  # PR #36's head the relay names


class World:
    """S's world for lane LANE (gh1255-1266-<lane>), PR, parent ISSUE, the lane worktree at HEAD
    and the base at BASE_AT; gh answers SCENARIO's tape."""

    source = str(HERE / "realcase-1266.bundle")

    def __init__(  # noqa: PLR0913, PLR0917  the lane's facts
        self, s: Scratch, scenario: str, lane: str, pr: int, issue: int, head: str, base_at: str
    ) -> None:
        self.s, self.pr, self.head = s, pr, head
        self.lane = f"gh1255-1266-{lane}"
        for k in [k for k in s.env if k.startswith(("HERDR_", "OCTO_FEATHER_"))]:
            del s.env[k]
        st = s.root / "state"
        self.st = st / "octo-feather"
        lanes = self.st / "lanes"
        lanes.mkdir(parents=True)
        (lanes / f"{self.lane}.toml").write_text(
            f'supervisor = "{SUP}"\nrepository = "{REPO}"\nissue = "gh{issue}"\npr = {pr}\n'
            'goal = "g"\nstarted_at = "2026-11-24T00:00:00Z"\n'
        )
        (self.st / "director.toml").write_text(f'pane = "{DIRECTOR}"\n')
        herdr = s.root / "herdr"
        herdr.mkdir()
        (herdr / "agents.json").write_text(json.dumps({SUP: agent(SUP, self.lane, "idle")}))
        ki = s.root / "kit"
        s.run(["git", "init", "-q", "-b", "main", str(ki)])
        s.git(ki, "remote", "add", "origin", "https://github.com/0xTomDaniel/octo-feather.git")
        s.run(["git", "-C", str(ki), "commit", "-q", "--allow-empty", "-m", "kit"])
        s.env |= {
            "XDG_STATE_HOME": str(st),
            "OCTO_FEATHER_QC_DIR": str(s.root / "qc"),
            "OCTO_FEATHER_KIT_INSTALL": str(ki),
            "FAKE_HERDR": str(herdr),
            "PATH": f"{ASSETS}{os.pathsep}{s.env['PATH']}",
            "GIT_AUTHOR_NAME": "t",
            "GIT_AUTHOR_EMAIL": "t@example.com",
            "GIT_COMMITTER_NAME": "t",
            "GIT_COMMITTER_EMAIL": "t@example.com",
        }
        self.r, self.wt = s.root / "repo", s.root / "wt"
        s.run(["git", "clone", "-q", "--no-checkout", self.source, str(self.r)])
        s.git(self.r, "checkout", "-q", "-B", BASE, base_at)
        s.git(self.r, "update-ref", f"refs/remotes/origin/{BASE}", base_at)
        s.git(self.r, "worktree", "add", "-q", "-B", self.lane, str(self.wt), head)
        self.tape(scenario)

    def tape(self, scenario: str) -> None:
        """S's gh answering only SCENARIO's recordings."""
        tapes = cast("dict[str, list[dict[str, object]]]", json.loads(TAPES.read_text()))
        (self.s.gh.dir / "tape.json").write_text(json.dumps(tapes[scenario]))

    def run(self, want: int, *args: str, pane: str = SUP) -> Ran:
        """octo-feather-lane ARGS in the lane worktree from PANE, exit WANT, printed as said."""
        r = self.s.run([L, *args], want=want, cwd=self.wt, env={"HERDR_PANE_ID": pane})
        said = f"$ octo-feather-lane {' '.join(args)}  # exit {r.rc}\n{r.out}\n{r.err}"
        sys.stdout.write(said.rstrip() + "\n")  # each command and its output: the demo's
        return r

    def merge(self, want: int, head: str | None = None) -> Ran:
        return self.run(want, "merge", str(self.pr), head or self.head, "--repo", REPO)

    def relay(self, want: int, head: str | None = None, pane: str = DIRECTOR) -> Ran:
        return self.run(want, "relay", str(self.pr), head or self.head, pane=pane)

    def relays(self) -> list[dict[str, object]]:
        """The relay lines in the director's hand-off log."""
        log = self.st / "director.handoffs.jsonl"
        rows = [json.loads(x) for x in log.read_text().splitlines()] if log.exists() else []
        return [x for x in rows if x.get("kind") == "relay"]

    def merged(self) -> list[str]:
        """Each `pr merge` gh was asked."""
        return [x for x in self.s.gh.log() if x.startswith("pr merge")]


def stays_open(w: World, r: Ran) -> None:
    """Refused before any merge: no `pr merge` asked, the refusal says the PR stays open."""
    assert not w.merged(), w.s.gh.log()
    assert f"nothing merged, PR #{w.pr} stays open" in r.err, r.err


def went(w: World, r: Ran, head: str) -> None:
    """Merged at HEAD: gh asked to merge pinned to it, and step 1 read it merged there."""
    assert w.merged() == [f"pr merge {w.pr} --merge --match-head-commit {head} -R {REPO}"], (
        w.merged()
    )
    out = r.out.splitlines()
    assert f"merged: PR #{w.pr} at head {head[:12]} (lane {w.lane})" in out, r.out
    assert any(x.startswith("step 1 merged: ok: ") for x in out), r.out


CALL = "- spec call demo 2026-11-24T03:00:00Z clarifies acceptance-a"
FAILED = "- failed criterion demo#acceptance-c: repair ticket #99 (recorded case)"


def owner(s: Scratch) -> None:
    """issue-lifecycle#acceptance-merge-guard-owner: `merge 36 R`, PR #36 tier 3 (its Failed list),
    no relay on record."""
    w = World(s, "owner", "owner", 36, 32, R, B0)
    r = w.merge(1)
    assert "its merge waits for the owner, and no relay of its merge is on record" in r.err, r.err
    assert f"(Tier: 3; {FAILED}; Waits for: the owner)" in r.err, r.err
    stays_open(w, r)


def order(s: Scratch) -> None:
    """issue-lifecycle#acceptance-merge-guard-order: `merge 34 HB`, PR #34 tier 1, #35 open with its
    head conflicting, no relay on record."""
    w = World(s, "order", "order", 34, 31, HB, B0)
    r = w.merge(1)
    why = "the director's order (PR #35: its head conflicts with this head in app.py)"
    assert f"its merge waits for {why}, and no relay of its merge is on record" in r.err, r.err
    assert "(Tier: 1; Waits for: " in r.err, r.err
    stays_open(w, r)


def relay_director_only(s: Scratch) -> None:
    """issue-lifecycle#acceptance-merge-relay-director-only: `relay 36 R` from the supervisor's
    pane, PR #36 tier 3; then `merge 36 R`."""
    w = World(s, "owner", "owner", 36, 32, R, B0)
    r = w.relay(1, pane=SUP)
    assert "only the director relays a merge" in r.err, r.err
    assert "nothing recorded" in r.err, r.err
    assert w.relays() == [], w.relays()
    assert not s.gh.log(), s.gh.log()
    r = w.merge(1)
    assert "its merge waits for the owner" in r.err, r.err
    stays_open(w, r)


def self_merge(s: Scratch) -> None:
    """issue-lifecycle#acceptance-tier-self-merge: `merge 39 E`, PR #39 tier 2 (a clarifying spec
    call), no open PR set back, no relay; its parent #37."""
    w = World(s, "self", "self2", 39, 37, E, B3)
    r = w.merge(0)
    allowed = f"allowed: PR #39 at {E[:12]}, its merge ask (Tier: 2; {CALL}; Waits for: nobody)"
    assert allowed in r.err.splitlines(), r.err
    went(w, r, E)
    assert "37: done" in r.out.splitlines(), r.out
    assert w.relays() == [], w.relays()


def relayed(s: Scratch) -> None:
    """issue-lifecycle#acceptance-tier-relayed: `merge 40 G`, PR #40 tier 2 (a clarifying spec
    call), #41 open with its head conflicting; then `relay 40 G` from the director's pane, `merge
    40 G` again."""
    w = World(s, "relayed", "order2", 40, 38, G, B4)
    why = "the director's order (PR #41: its head conflicts with this head in app.py)"
    r = w.merge(1)
    assert f"its merge waits for {why}, and no relay of its merge is on record" in r.err, r.err
    assert f"(Tier: 2; {CALL}; Waits for: {why})" in r.err, r.err
    stays_open(w, r)
    r = w.relay(0)
    assert r.out.startswith(f"relayed: PR #40 at head {G[:12]} (lane {w.lane}); recorded in "), (
        r.out
    )
    got = [(x["lane"], x["pr"], x["head"]) for x in w.relays()]
    assert got == [(w.lane, 40, G)], w.relays()
    r = w.merge(0)
    allowed = f"allowed: PR #40 at {G[:12]} on the director's relay of that head, its merge ask"
    assert f"{allowed} (Tier: 2; {CALL}; Waits for: {why})" in r.err.splitlines(), r.err
    went(w, r, G)


def head(s: Scratch) -> None:
    """issue-lifecycle#acceptance-merge-guard-head: `merge 36 F`, PR #36 tier 3, the director's
    relay on record naming R, the fix commit F after it."""
    w = World(s, "head", "owner", 36, 32, F, B2)
    w.relay(0, R)
    r = w.merge(1)
    both = f"the director's relay on record allows head {R[:12]}, the merge was given head {F[:12]}"
    assert both in r.err, r.err
    assert f"commit {F[:12]} " in r.err, r.err
    stays_open(w, r)


def carry(s: Scratch) -> None:
    """A relay carried (--help, merge, allowed): `merge 36 M2`, PR #36 tier 3, the director's relay
    on record naming F, M2 a clean merge of the base after it."""
    w = World(s, "carry", "owner", 36, 32, M2, B2)
    w.relay(0, F)
    r = w.merge(0)
    carried = f"relay carried: the director's relay of PR #36 at {F[:12]} carries to {M2[:12]}: "
    line = next((x for x in r.out.splitlines() if x.startswith(carried)), "")
    assert f"clean merge of main {M2[:12]}: lane hunks identical" in line, r.out
    went(w, r, M2)


if __name__ == "__main__":
    main(owner, order, relay_director_only, self_merge, relayed, head, carry)
