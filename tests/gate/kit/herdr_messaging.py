"""Herdr messaging never fails silently or hangs (#666; #585, #619; owner rulings #585 and #619
2026-11-05), through the commands with the testkit's Herdr stand-in (testkit/herdr.py, its
FAKE_HERDR world): herdr-spawn returns only once its agent reads idle on `herdr agent wait`, so
an agent that turns ready late is not returned early, and a herdr-say right after it is
delivered; a herdr-say whose `herdr agent get` lookup fails names that lookup (not the up-chain
refusal, 77); a prompt Herdr reports stalled exits non-zero naming the pane and its state; and
`octo-feather-lane post-merge` step 4 to a busy (working) supervisor returns within its bound,
its step 4 line naming the supervisor NOT told (lane, pane, timeout, the re-send command) and going
on to tell the others (director rule #619).

post-merge step 4 (owner ruling on issue 206; issues 398, 458): live supervisors of the PR's repo
(every lane on a kit PR) told once, by the kit's own herdr-say with its bound, with the merge, PR,
title and rule files, one prod line each, a rerun telling nothing new; parked and gone lanes
listed, never sent to; a failed send named, no prod line, exit 1; any other herdr failure stops
the step; step 5 reached, the kit's own herdr-close run and Herdr's workspace_not_found read as
already closed. Space ids `zt*`, which no real Herdr gives, so herdr-close's sweep of processes
tagged with a closed space can reach no box process."""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
from typing import TYPE_CHECKING

from testkit import HERE, ROOT, Scratch, kit, main

if TYPE_CHECKING:
    from pathlib import Path

ASSETS = ROOT / ".agents" / "skills" / "herdr-comms" / "assets"
TELL_BOUND = 20  # post-merge step 4's bound on one send, seconds (octo-feather-lane --help)


def herdr_world(s: Scratch, agents: dict[str, dict[str, object]] | None = None) -> Path:
    """S's Herdr: the stand-in's agents world, holding AGENTS, the caller's Herdr and kit
    variables cleared (a scenario's caller is no pane unless it sets one)."""
    d = s.root / "herdr"
    d.mkdir()
    (d / "agents.json").write_text(json.dumps(agents or {}))
    for k in [k for k in s.env if k.startswith(("HERDR_", "OCTO_FEATHER_"))]:
        del s.env[k]
    s.env["FAKE_HERDR"] = str(d)
    return d


def agent(pane: str, name: str, status: str, ready_at: float = 0) -> dict[str, object]:
    w = pane.split(":", maxsplit=1)[0]
    return {
        "name": name,
        "pane_id": pane,
        "workspace_id": w,
        "tab_id": f"{w}:t{pane.split(':p')[1]}",
        "agent_status": status,
        "ready_at": ready_at,
    }


SUPERVISOR = {
    "OCTO_FEATHER_ROLE": "supervisor",
    "OCTO_FEATHER_PARENT": "w0:p1",
    "HERDR_PANE_ID": "w1:p0",
    "HERDR_WORKSPACE_ID": "w1",
}


def lines(p: Path) -> list[str]:
    return p.read_text().splitlines() if p.exists() else []


def spawn_ready_late(s: Scratch) -> None:
    """An agent that turns idle 2 s after its start: herdr-spawn returns only once Herdr reads it
    idle (never while it still boots), and a herdr-say to its pane right after is delivered,
    nothing left typed and unsent."""
    d = herdr_world(s)
    (d / "ready_after").write_text("2")
    s.identity()
    wt = s.root / "wt"
    wt.mkdir()
    spawn = [str(ASSETS / "herdr-spawn"), "--workspace", "w1", "--name", "implementer-gh1"]
    ran = s.run([*spawn, "--role", "implementer", "--cwd", str(wt)], env=SUPERVISOR)
    pane = next(x.removeprefix("pane=") for x in ran.out.split() if x.startswith("pane="))
    got = json.loads(s.run(["herdr", "agent", "get", pane]).out)["result"]["agent"]
    assert got["agent_status"] == "idle", f"spawn returned while the agent read {got}"
    s.run([str(ASSETS / "herdr-say"), pane, "the brief"], env=SUPERVISOR)
    assert lines(d / "prompts") == [f"{pane}\tthe brief"], lines(d / "prompts")
    assert lines(d / "typed") == [], lines(d / "typed")


def say_lookup_fails(s: Scratch) -> None:
    """A supervisor's herdr-say to its worker while `herdr agent get` fails: an error naming the
    lookup and what it printed, never the up-chain refusal (77); nothing prompted."""
    d = herdr_world(s, {"w1:p2": agent("w1:p2", "implementer-gh1", "idle")})
    (d / "get-down").touch()
    ran = s.run([str(ASSETS / "herdr-say"), "w1:p2", "hi"], want=69, env=SUPERVISOR)
    assert "herdr agent get w1:p2" in ran.err, ran.err
    assert "server not reachable" in ran.err, ran.err
    assert "up its chain" not in ran.err, ran.err
    assert not lines(d / "prompts"), lines(d / "prompts")


def say_stalled(s: Scratch) -> None:
    """A prompt Herdr reports stalled (typed, never seen to land): herdr-say exits non-zero, its
    last line naming the pane and the state Herdr reads it in, and Herdr's own error kept."""
    late = time.time() + 3600
    d = herdr_world(s, {"w1:p2": agent("w1:p2", "implementer-gh1", "idle", late)})
    ran = s.run([str(ASSETS / "herdr-say"), "implementer-gh1", "hi"], want=1)
    last = ran.err.splitlines()[-1]
    assert "agent_prompt_stalled" in ran.err, ran.err
    assert "w1:p2" in last, ran.err
    assert "unknown" in last, ran.err
    assert lines(d / "typed") == ["w1:p2\thi"], lines(d / "typed")


def merged_repo(s: Scratch) -> tuple[Path, str]:
    """A repo whose main merged PR 7 (head H, changing a role file): its dir and H."""
    r = s.root / "repo"
    s.run(["git", "init", "-q", "-b", "main", str(r)])
    (r / "agents").mkdir()
    (r / "agents" / "supervisor.md").write_text("a\n")
    s.git(r, "add", "-A")
    s.git(r, "commit", "-qm", "base")
    s.git(r, "checkout", "-qb", "gh7")
    (r / "agents" / "supervisor.md").write_text("b\n")
    s.git(r, "commit", "-qam", "change")
    head = s.git(r, "rev-parse", "HEAD")
    s.git(r, "checkout", "-q", "main")
    s.git(r, "merge", "-q", "--no-ff", "gh7", "-m", "Merge #7")
    return r, head


def post_merge_busy(s: Scratch) -> None:
    """post-merge after PR 7 merged, lane live1's supervisor w1:p1 busy (working the whole run),
    lane live2's w2:p1 idle: step 4 returns within its bound; live2 told (its prod line), live1
    NOT told, named with its pane, the timeout, its state and the herdr-say that re-sends it by
    hand, no prod line; the summary names live1 NOT told; exit 1."""
    busy = agent("w1:p1", "live1", "working")
    d = herdr_world(s, {"w1:p1": busy, "w2:p1": agent("w2:p1", "live2", "idle")})
    r, head = merged_repo(s)
    merge = s.git(r, "rev-parse", "HEAD")
    url = "https://github.com/o/r/pull/7"
    s.gh.put(
        7,
        {
            "state": "MERGED",
            "headRefOid": head,
            "mergeCommit": {"oid": merge},
            "baseRefName": "main",
            "headRefName": "gh7",
            "title": "Add foo",
            "url": url,
        },
    )
    run = {"databaseId": 1, "status": "completed", "conclusion": "success"}
    s.gh.store("run/1.json", run | {"workflowName": "check", "url": f"{url}/checks"})
    # Step 3 asks `gh repo view` for the PR's repo and the kit install's origin: the fake gh knows
    # only o/r, so a gh first on PATH names the install's origin o/kit (step 3 then leaves it).
    gh = s.root / "ghbin"
    gh.mkdir()
    (gh / "gh").write_text(
        '#!/bin/sh\n[ "$1 $2 $3" = "repo view https://github.com/o/kit.git" ] && '
        'exec echo \'{"nameWithOwner": "o/kit"}\'\n'
        '[ "$1 $2" = "repo view" ] && exec echo \'{"nameWithOwner": "o/r"}\'\n'
        f'exec {s.bin}/gh "$@"\n'
    )
    (gh / "gh").chmod(0o755)
    kit_clone = s.root / "kit"
    s.run(["git", "clone", "-q", str(r), str(kit_clone)])
    s.git(kit_clone, "remote", "set-url", "origin", "https://github.com/o/kit.git")
    lanes = s.home / ".local" / "state" / "octo-feather" / "lanes"
    lanes.mkdir(parents=True)
    for n, issue in ((1, 11), (2, 12)):
        (lanes / f"live{n}.toml").write_text(
            f'supervisor = "w{n}:p1"\nrepository = "o/r"\nissue = {issue}\ngoal = "g"\n'
            'started_at = "2026-11-06T00:00:00Z"\n'
        )
    env = s.env | {
        "PATH": f"{gh}{os.pathsep}{ASSETS}{os.pathsep}{s.env['PATH']}",
        "OCTO_FEATHER_KIT_INSTALL": str(kit_clone),
    }
    cmd = [kit("octo-feather-lane"), "post-merge", "7", head, "--lane", "gh7", "--repo", "o/r"]
    t0 = time.monotonic()
    p = subprocess.run(
        [*cmd, "--wait", "0"],
        cwd=r,
        env=env,
        capture_output=True,
        text=True,
        timeout=TELL_BOUND + 60,
        check=False,
    )
    took = time.monotonic() - t0
    said = f"exit {p.returncode} after {took:.0f}s\n{p.stdout}\n{p.stderr}"
    assert p.returncode == 1, said
    assert took < TELL_BOUND + 20, said
    tell = next((x for x in p.stdout.splitlines() if x.startswith("step 4 ")), "")
    assert tell.startswith("step 4 tell supervisors: stopped: NOT told: live1 w1:p1: "), said
    assert f"send timed out after {TELL_BOUND}s" in tell, said
    assert f"w1:p1 (pane w1:p1) still working after {TELL_BOUND}s" in tell, said
    assert "re-send by hand: herdr-say w1:p1 'main moved to " in tell, said
    assert "; NOT told: live1 w1:p1; told: live2 w2:p1;" in tell, said
    last = p.stdout.splitlines()[-1]
    want = "step 5 teardown not run; NOT told: live1 w1:p1 (step 4 names each re-send)"
    assert last.endswith(f"step 4 tell supervisors stopped; {want}"), said
    assert [x.split("\t")[0] for x in lines(d / "prompts")] == ["w1:p1", "w2:p1"], said
    prods = [json.loads(x) for x in lines(lanes.parent / "director.handoffs.jsonl")]
    assert [x["issue"] for x in prods] == [12], said


# A kit install's recipes step 3's refresh runs (by the real just): nothing to fetch or check.
TELL_JUSTFILE = "vendored-fetch:\n    @true\n\ninstall-check target:\n    @true\n"
RULED = ".agents/skills/foo/SKILL.md, agents/supervisor.md"
REREAD = "re-read the changed ones before your next step."


def build_tell(p: Scratch) -> None:
    """repo: main merged gh7 (two rule files and a product file changed) then gh8 (a file under
    no rule path); kit: a clone of it at main, its origin o/kit (Tell fetches it from repo);
    shas.json: each merge commit and the head it merged."""
    r = p.root / "repo"
    p.run(["git", "init", "-q", "-b", "main", str(r)])
    for f, text in (("agents/supervisor.md", "a"), ("src/app.py", "a"), ("docs/notes.md", "a")):
        (r / f).parent.mkdir(parents=True, exist_ok=True)
        (r / f).write_text(text + "\n")
    (r / "justfile").write_text(TELL_JUSTFILE)
    p.git(r, "add", "-A")
    p.git(r, "commit", "-qm", "base")
    for branch, files in (
        ("gh7", ("agents/supervisor.md", ".agents/skills/foo/SKILL.md", "src/app.py")),
        ("gh8", ("docs/notes.md",)),
    ):
        p.git(r, "checkout", "-qb", branch)
        for f in files:
            (r / f).parent.mkdir(parents=True, exist_ok=True)
            (r / f).write_text(f"{branch}\n")
        p.git(r, "add", "-A")
        p.git(r, "commit", "-qm", "change")
        p.git(r, "checkout", "-q", "main")
        p.git(r, "merge", "-q", "--no-ff", branch, "-m", f"Merge #{branch[2:]}")
    k = p.root / "kit"
    p.run(["git", "clone", "-q", str(r), str(k)])
    p.git(k, "remote", "set-url", "origin", "https://github.com/o/kit.git")
    log = p.git(r, "log", "--first-parent", "--format=%H %P", "main").splitlines()
    (m2, _, h2), (m, _, h) = (x.split() for x in log[:2])
    (p.root / "shas.json").write_text(json.dumps({"m": m, "h": h, "m2": m2, "h2": h2}))


class Tell:
    """The prepared repo and kit install in S, its lanes and director log, Herdr's world, the
    kit's herdr-say and herdr-close on PATH; `run` runs post-merge from the repo."""

    def __init__(self, s: Scratch) -> None:
        s.prepare("lane-post-merge-tell", build_tell)
        self.s, self.r = s, s.root / "repo"
        self.d = herdr_world(s)
        s.env.pop("GH_REPO", None)
        st = s.root / "state" / "octo-feather"
        self.lanes, self.dlog = st / "lanes", st / "director.handoffs.jsonl"
        self.lanes.mkdir(parents=True)
        rec = s.root / "rec"
        rec.mkdir()
        for n in ("uv", "pnpm"):  # step 3's refresh reaching the registries: argv_recorder.sh
            (rec / n).symlink_to(HERE / "argv_recorder.sh")
        s.env |= {
            "XDG_STATE_HOME": str(s.root / "state"),
            "OCTO_FEATHER_KIT_INSTALL": str(s.root / "kit"),
            "ARGV_LOG": str(s.root / "argv.log"),
            "PATH": os.pathsep.join([str(rec), str(ASSETS), s.env["PATH"]]),
            # The kit install's origin, o/kit, is this copy's repo: a url rewrite in git's env
            # (no git call; the prepared tree's path is not this copy's).
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": f"url.{self.r}.insteadOf",
            "GIT_CONFIG_VALUE_0": "https://github.com/o/kit.git",
        }
        shas = json.loads((s.root / "shas.json").read_text())
        self.m, self.h, self.m2, self.h2 = (shas[k] for k in ("m", "h", "m2", "h2"))
        s.gh.store("repo.json", {"nameWithOwner": "o/r"})
        s.gh.store("api/repos/o/kit.json", {"nameWithOwner": "o/kit"})
        run = {"databaseId": 1, "status": "completed", "conclusion": "success"}
        url = "https://github.com/o/r/actions/runs/1"
        s.gh.store("run/1.json", run | {"workflowName": "check", "url": url})
        self.store("o/r", "Add foo")

    def store(self, repo: str, title: str) -> None:
        """PRs 7 (TITLE, of REPO) and 8 (Notes, of o/r), merged."""
        for n, head, merge, t, at in (
            (7, self.h, self.m, title, repo),
            (8, self.h2, self.m2, "Notes", "o/r"),
        ):
            pr = {
                "state": "MERGED",
                "headRefOid": head,
                "mergeCommit": {"oid": merge},
                "baseRefName": "main",
                "headRefName": f"gh{n}",
                "title": t,
                "url": f"https://github.com/{at}/pull/{n}",
            }
            self.s.gh.put(n, pr)

    def lane(self, name: str, pane: str, repo: str, issue: int) -> None:
        (self.lanes / f"{name}.toml").write_text(
            f'supervisor = "{pane}"\nrepository = "{repo}"\nissue = {issue}\ngoal = "g"\n'
            'started_at = "2026-10-29T00:00:00Z"\n'
        )

    def parked(self, lane: str, pane: str, at: str) -> None:
        line = {"at": at, "kind": "parked", "pane": pane, "name": lane}
        with (self.lanes / f"{lane}.handoffs.jsonl").open("a") as f:
            f.write(json.dumps(line) + "\n")

    def live(self, *panes: str, blocked: str = "") -> None:
        """Herdr's agents: PANES live (idle), BLOCKED (one of them) on a dialog."""
        live = {p: agent(p, p, "blocked" if p == blocked else "idle") for p in panes}
        (self.d / "agents.json").write_text(json.dumps(live))

    def run(self, want: int, pr: int, *args: str) -> tuple[str, str]:
        """post-merge PR (its head) ARGS --wait 0, exit WANT, no traceback: its step 4 line and
        its last line."""
        head = self.h if pr == 7 else self.h2
        cmd = [kit("octo-feather-lane"), "post-merge", str(pr), head, *args, "--wait", "0"]
        ran = self.s.run(cmd, want=want, cwd=self.r)
        tell = [x for x in ran.out.splitlines() if re.match(r"step [0-9]+ tell supervisors: ", x)]
        assert tell, f"no tell supervisors line: {ran.out}"
        self.out = ran.out
        return tell[0], ran.out.splitlines()[-1]

    def said(self) -> list[str]:
        """Each pane a send was tried to, sorted; each send bounded by post-merge's bound."""
        sends = [x for x in lines(self.d / "log") if x.startswith("agent prompt ")]
        bound = f" --timeout {TELL_BOUND * 1000}"
        assert all(x.endswith(bound) for x in sends), f"a send without{bound}: {sends}"
        return sorted(x.split()[2] for x in sends)

    def told(self) -> list[str]:
        return [x.split("\t", 1)[1] for x in lines(self.d / "prompts")]

    def prods(self) -> list[dict[str, object]]:
        return [json.loads(x) for x in lines(self.dlog)]

    def clear(self) -> None:
        """The sends, Herdr's call log and the director log emptied."""
        for f in (self.d / "log", self.d / "prompts", self.dlog):
            f.write_text("")


def told_live(t: Tell) -> None:
    """tell_supervisors' first phase: live, parked and another repo's lanes; a rerun; a merge
    with no rule file."""
    t.lane("gh7", "zt0:p1", "o/r", 7)
    t.lane("live1", "zt1:p1", "o/r", 11)
    t.lane("parked", "zt2:p1", "o/r", 12)
    t.lane("other", "zt3:p1", "x/y", 13)
    t.parked("parked", "zt2:p0", "2026-10-28T00:00:00Z")
    t.parked("parked", "zt2:p1", "2026-10-29T00:00:00Z")
    t.live("zt0:p1", "zt1:p1", "zt3:p1")
    earlier = '{"at": "2026-10-29T00:00:00+00:00", "kind": "prod", "issue": 11, "note": "earlier"}'
    t.dlog.write_text(earlier + "\n")
    tell, last = t.run(3, 7, "--lane", "gh7", "--repo", "o/r")
    assert t.said() == ["zt1:p1"], t.said()
    want = f"main moved to {t.m[:12]} (#7 Add foo); rule files changed: {RULED}; {REREAD}"
    assert t.told() == [want], t.told()
    assert "told: live1 zt1:p1" in tell, tell
    gone = "gone: director to resume or archive: none"
    assert tell.endswith(f"not woken: parked zt2:p1; {gone}"), tell
    assert last.endswith("tell supervisors ok; step 5 teardown pending"), last
    assert "agent get zt3:p1" not in lines(t.d / "log"), lines(t.d / "log")
    prods = t.prods()
    assert len(prods) == 2, prods
    note = f"post-merge {t.m} #7: main moved, told live1 to re-read {RULED}"
    p = prods[1]
    assert sorted(p) == ["at", "issue", "kind", "note"], p
    assert (p["kind"], p["issue"], p["note"]) == ("prod", 11, note), p
    assert re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9:.]+\+00:00", str(p["at"])), p
    tell, _ = t.run(3, 7, "--lane", "gh7", "--repo", "o/r")
    assert len(t.told()) == 1, f"rerun sent again: {t.told()}"
    assert len(t.prods()) == 2, f"rerun logged again: {t.prods()}"
    assert "already told: live1" in tell, tell
    assert "not woken: parked zt2:p1" in tell, tell
    t.run(3, 8, "--lane", "gh7", "--repo", "o/r")
    none = f"main moved to {t.m2[:12]} (#8 Notes); rule files changed: none; {REREAD}"
    assert t.told()[-1] == none, t.told()
    assert t.prods()[-1]["note"] == f"post-merge {t.m2} #8: main moved, told live1 to re-read none"


def told_kit(t: Tell) -> None:
    """tell_supervisors' kit PR phase: the sends and the director log emptied first."""
    t.store("o/kit", "Kit rule")
    t.clear()
    t.run(3, 7, "--lane", "gh7", "--repo", "o/kit")
    assert t.said() == ["zt1:p1", "zt3:p1"], f"{t.said()}: {t.out}"
    assert sorted(int(str(p["issue"])) for p in t.prods()) == [11, 13], t.prods()


def told_failed(t: Tell) -> None:
    """tell_supervisors' failed send phase, on the o/r PR again: live2 added, live1 blocked on
    a dialog (the kit's herdr-say exits 75)."""
    t.store("o/r", "Add foo")
    t.clear()
    t.lane("live2", "zt4:p1", "o/r", 14)
    t.live("zt0:p1", "zt1:p1", "zt3:p1", "zt4:p1", blocked="zt1:p1")
    tell, last = t.run(1, 7, "--lane", "gh7", "--repo", "o/r")
    assert t.said() == ["zt1:p1", "zt4:p1"], t.said()
    assert "stopped: " in tell, tell
    assert "herdr-say failed: live1 zt1:p1 exit 75" in tell, tell
    assert "told: live2 zt4:p1" in tell, tell
    assert [p["issue"] for p in t.prods()] == [14], t.prods()
    assert "tell supervisors stopped" in last, last
    t.live("zt0:p1", "zt1:p1", "zt3:p1", "zt4:p1")
    t.run(3, 7, "--lane", "gh7", "--repo", "o/r")
    assert t.said() == ["zt1:p1", "zt1:p1", "zt4:p1"], f"retry: {t.said()}"
    assert [p["issue"] for p in t.prods()] == [14, 11], t.prods()


def told_gone(t: Tell) -> None:
    """tell_supervisors' issue 458 phase: every lane record and hand-off log replaced first."""
    for f in t.lanes.iterdir():
        f.unlink()
    t.clear()
    t.lane("live1", "zt1:p1", "o/r", 11)
    t.lane("parked", "zt2:p1", "o/r", 12)
    t.lane("gone", "zt5:p1", "o/r", 15)
    t.lane("moved", "zt6:p1", "o/r", 16)
    t.parked("parked", "zt2:p1", "2026-10-29T00:00:00Z")
    t.parked("moved", "zt6:p1", "2026-10-28T00:00:00Z")
    t.parked("moved", "zt6:p0", "2026-10-29T00:00:00Z")
    t.live("zt1:p1")
    gone = "gone: director to resume or archive: gone zt5:p1, moved zt6:p1"
    tell, _ = t.run(3, 7, "--lane", "gh1", "--repo", "o/r")
    assert t.said() == ["zt1:p1"], t.said()
    want = "told: live1 zt1:p1; already told: none; not woken: parked zt2:p1; " + gone
    assert tell.startswith("step 4 tell supervisors: ok: "), tell
    assert tell.endswith(want), tell
    pending = "step 5 teardown: pending: lane gh1 not archived; rerun on its close report"
    assert pending in t.out.splitlines(), t.out
    # Archived: step 5 runs the kit's herdr-close on space zt9, which Herdr has not: its close
    # fails, and Herdr's workspace_not_found (stderr) reads as already closed.
    (t.lanes / "archive").mkdir()
    (t.lanes.parent / "director.toml").write_text('pane = "zt0:p9"\n')
    t.s.git(t.r, "remote", "add", "origin", str(t.r))
    (t.lanes / "archive" / "gh1.toml").write_text(
        'supervisor = "zt9:p1"\nrepository = "o/r"\nissue = 1\npr = 7\ngoal = "g"\n'
        'started_at = "2026-10-29T00:00:00Z"\n'
    )
    t.run(0, 7, "--lane", "gh1", "--repo", "o/r")
    down = (
        "step 5 teardown: ok: space zt9 already closed; worktree of gh1 already removed; no open "
        "PR based on gh1; local branch gh1 already deleted; remote branch gh1 already deleted "
        "from origin"
    )
    assert down in t.out.splitlines(), t.out
    log = lines(t.d / "log")
    assert "workspace close zt9" in log, f"herdr-close asked no close: {log}"
    assert "workspace get zt9" in log, f"teardown asked no workspace get: {log}"
    # Any other herdr failure still stops step 4, named; the other lanes are still handled.
    (t.lanes / "archive" / "gh1.toml").unlink()
    (t.d / "get-down").write_text("zt2:p1\n")
    tell, _ = t.run(1, 7, "--lane", "gh1", "--repo", "o/r")
    stop = (
        "step 4 tell supervisors: stopped: parked zt2:p1: herdr agent get zt2:p1 failed (herdr: "
        "server not reachable)"
    )
    assert tell.startswith(stop), tell
    assert tell.endswith(gone), tell


def tell_supervisors(s: Scratch) -> None:
    """Only a live supervisor of the PR's repo gets one message naming the merge commit, PR,
    title and changed rule files, by the kit's herdr-say bounded by post-merge's bound; the --lane
    lane, a parked one (its latest parked line names its pane) and another repo's lane (never
    looked up) none; one canonical prod line per lane told, after the director's own; step 4 ok,
    step 5 pending, exit 3. A rerun sends and logs nothing new (already told). A merge touching no
    rule file says none, and is told again. A kit PR (o/kit, the install's own repo): every lane
    runs kit roles, so another repo's live lane is told too, one prod line each (step 3 refreshes
    the install first: its recipes no-ops by the real just, uv and pnpm argv_recorder.sh). A send
    that fails (its supervisor blocked on a dialog, herdr-say's 75): named, no prod line for it,
    the others still tried and told, the step stopped, exit 1; a rerun tells only that one. Issue
    458: --lane gh1 with a live, a parked and two gone lanes (one never parked, one whose latest
    parked line names an older pane): only the live one told, the rest listed, step 4 ok, step 5
    pending (not archived). Archived: step 5 runs, the kit's herdr-close failing and Herdr's
    workspace_not_found read as already closed. Any other herdr failure (Herdr unreachable on the
    parked lane's lookup) stops step 4, named, the other lanes still handled. One
    world, the old test's order: each phase resets only what it names."""
    t = Tell(s)
    told_live(t)
    told_kit(t)
    told_failed(t)
    told_gone(t)


if __name__ == "__main__":
    main(spawn_ready_late, say_lookup_fails, say_stalled, post_merge_busy, tell_supervisors)
