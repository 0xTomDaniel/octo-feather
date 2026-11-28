"""A real lane merge and archive on the realcase repo as a scratch world, for the kit items that
replay its recorded gh tapes (#1267): gh1249's case (GH1249, #1256), for herdr_messaging.py
tell_supervisors; the gh1255 remerge's (REMERGE, #1266), whose merge asks the merge ask check
first, for lane_merge.py merge_starts_routine and lane_archive_teardown.py archive_tears_down.
RealCase builds it; recordings and recorded read the tapes, testkit/recordings/*.json,
unmodified."""

from __future__ import annotations

import json
import os
import sys
from typing import TYPE_CHECKING, NamedTuple

from testkit import HERE, ROOT, MissingFixtureError, Ran, Scratch, kit, reflector

if TYPE_CHECKING:
    from pathlib import Path

ASSETS = ROOT / ".agents" / "skills" / "herdr-comms" / "assets"  # the kit's herdr-say


def lines(p: Path) -> list[str]:
    return p.read_text().splitlines() if p.exists() else []


# Supervisor A's environment in its own pane (RealCase), as octo-feather-start and Herdr give it:
# its role, the director's pane (testkit.reflector's w9:p99) its parent, its own pane and
# workspace; so herdr-say's up-chain guard (docs/adr/0015) is active as in that pane (#1249).
REALCASE_SUPERVISOR = {
    "OCTO_FEATHER_ROLE": "supervisor",
    "OCTO_FEATHER_PARENT": "w9:p99",
    "HERDR_PANE_ID": "zt1:p1",
    "HERDR_WORKSPACE_ID": "zt1",
}
RECORDINGS = HERE / "recordings"
# gh1249's real case (#1256, commit 59140bba's message; the run's report: #1256's last comment):
# supervisor A of lane gh10 (parent issue 10, sub-issue 11) merging PR #14 of this repo, with
# lane B (gh12) live, before the merge guard (#1266); its merge tape recorded, unmodified.
REALCASE = "0xTomDaniel/octo-feather-realcase"


class Case(NamedTuple):
    """One recorded real case: its BUNDLE (recordings/<name>.bundle, its SHAs the tapes'), its
    merge TAPE (step 1's read of the merged PR in it), the PR, lane A's key LANE (its parent
    issue's lane key; its branch), lane B's key OTHER (open beside it, of the same repo)."""

    bundle: str
    tape: str
    pr: int
    lane: str
    other: str


GH1249 = Case("realcase-gh1249", "lane-merge-realcase", 14, "gh10", "gh12")
# gh1255's remerge (#1266, #1268): supervisor A of lane gh45 (parent issue 45, sub-issue 46)
# merging PR #47 (base gh1255-remerge-base) with the merge guard, then archiving gh45, lane B
# (gh12) open; every gh call recorded, unmodified.
REMERGE = Case("realcase-remerge", "lane-merge-remerge", 47, "gh45", "gh12")
REMERGE_TAPES = ("lane-merge-remerge", "lane-archive-remerge")  # in the run's call order


def merged_view(pr: int) -> str:
    """Step 1's read of merged PR (the merge tape's): its merge commit and base."""
    return f"pr view {pr} --json state,headRefOid,mergeCommit,baseRefName,headRefName -R {REALCASE}"


def recordings(name: str) -> list[dict[str, object]]:
    """testkit/recordings/NAME.json's recordings, as recorded; a missing one fails naming it."""
    p = RECORDINGS / f"{name}.json"
    if not p.is_file():
        msg = f"testkit: recording {name} is missing: no file {p}"
        raise MissingFixtureError(msg)
    return json.loads(p.read_text())


def recorded(name: str, request: str) -> str:
    """The stdout real gh gave REQUEST's first recording in recordings NAME."""
    return next(str(r["out"]) for r in recordings(name) if r["request"] == request)


class RealCase:
    """S as CASE (default GH1249) stood at lane A's merge: gh answers only from the recordings of
    TAPES, one tape.json in the run's call order (testkit/gh.py's header, tape mode); origin.git
    the realcase repo from the case's bundle (recordings/<bundle>.bundle, unmodified, its SHAs
    the tapes'); the director's checkout `director`, a clone of it on the PR's base at the merge
    commit's first parent (the run's step 4 fast-forwarded it); the kit install `kit`, a repo
    whose origin is the kit's GitHub URL (the one step 3 asked gh about), never fetched as the
    PR is not the kit's; testkit.reflector's state dir and Herdr world (the director w9:p99),
    lane A's record (`issue` its lane key, `pr` the case's PR, as lane start and supervisor A
    wrote it) and lane B's, both of the realcase repo; Herdr's agents the director, A's
    supervisor zt1:p1 and B's zt2:p1, each idle; every command run in A's supervisor's environment
    (REALCASE_SUPERVISOR), the kit's herdr-say first on PATH."""

    MERGED = merged_view(GH1249.pr)  # GH1249's step 1 read

    def __init__(self, s: Scratch, *tapes: str, case: Case = GH1249) -> None:
        self.s = s
        s.gh.store("tape.json", [r for t in tapes for r in recordings(t)])
        self.origin, self.checkout, self.kit = (
            s.root / n for n in ("origin.git", "director", "kit")
        )
        bundle = RECORDINGS / f"{case.bundle}.bundle"
        s.run(["git", "clone", "-q", "--bare", str(bundle), str(self.origin)])
        s.run(["git", "clone", "-q", str(self.origin), str(self.checkout)])
        merged = json.loads(recorded(case.tape, merged_view(case.pr)))
        self.merge, self.base = merged["mergeCommit"]["oid"], merged["baseRefName"]
        s.git(self.checkout, "checkout", "-q", "-B", self.base, f"{self.merge}^1")
        s.git(s.root, "init", "-q", str(self.kit))
        s.git(self.kit, "remote", "add", "origin", "https://github.com/0xTomDaniel/octo-feather")
        self.top = reflector(s)
        self.lanes = self.top / "lanes"
        self.lanes.mkdir()
        for name, pane in ((case.lane, "zt1:p1"), (case.other, "zt2:p1")):
            (self.lanes / f"{name}.toml").write_text(
                f'supervisor = "{pane}"\nrepository = "{REALCASE}"\nissue = "{name}"\n'
                'goal = "g"\nstarted_at = "2026-11-24T21:37:22Z"\nwaiting_on = ""\n'
                + (f"pr = {case.pr}\n" if name == case.lane else "")
            )
        self.herdr = s.root / "herdr"
        world = json.loads((self.herdr / "agents.json").read_text())
        world["w9:p99"]["agent_status"] = "idle"
        for name, pane in (
            (case.lane, "zt1:p1"),
            (case.other, "zt2:p1"),
        ):  # as herdr_messaging.agent
            w = pane.split(":")[0]
            world[pane] = {"name": name, "pane_id": pane, "workspace_id": w}
            world[pane] |= {"tab_id": f"{w}:t1", "agent_status": "idle", "ready_at": 0}
        (self.herdr / "agents.json").write_text(json.dumps(world))
        s.env.pop("GH_REPO", None)
        s.env |= REALCASE_SUPERVISOR | {"OCTO_FEATHER_KIT_INSTALL": str(self.kit)}
        s.env["PATH"] = f"{ASSETS}{os.pathsep}{s.env['PATH']}"

    def lane(self, *args: str, want: int = 0, cwd: Path | None = None) -> Ran:
        """`octo-feather-lane ARGS` from the director's checkout (or CWD), exit WANT; the command
        and its output printed (the demo's)."""
        r = self.s.run([kit("octo-feather-lane"), *args], want=want, cwd=cwd or self.checkout)
        said = f"$ octo-feather-lane {' '.join(args)}  # exit {r.rc}\n{r.out}\n{r.err}"
        sys.stdout.write(said.rstrip() + "\n")
        return r

    def told(self) -> list[str]:
        """Each prompt Herdr delivered, `<pane>\\t<text>`."""
        return lines(self.herdr / "prompts")

    def prods(self) -> list[dict[str, object]]:
        """The director log's prod lines."""
        logged = [json.loads(x) for x in lines(self.top / "director.handoffs.jsonl")]
        return [x for x in logged if x.get("kind") == "prod"]
