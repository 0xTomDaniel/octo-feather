"""The scenarios of tests/gate/kit/test_lane_post_merge_parity.py (its items), this file their
command (testkit.main): scripts/octo-feather-lane post-merge step 5, the parity pass (issue 1363;
quality #acceptance-parity-pass-due, #acceptance-parity-pass-capped, #acceptance-parity-pass-told,
#acceptance-parity-network-free), offline.

The world, as tests/gate/kit/lane_post_merge_map.py's: a target repo's origin (main: B, then three
merge commits M1, M2, M3) and its clone, the director's checkout, on main at B; a kit install clone
of another repo (step 3 leaves it unchanged); the fake gh holding PRs 7, 8 and 9 (lanes gh7, gh8,
gh9) merged as M1, M2 and M3, with no CI workflow; the Herdr stand-in with the director's pane
w9:p99 under the kit's own herdr-say; the systemd stand-in as systemd-run and systemctl; a scratch
state dir, its slots dir holding the box's fast-run turns. The target has no fast-map recipe (the
map is skipped: its own scenarios prove it). At B it holds four parity cases, a, b, c and d (b's
patch changes scripts/x, c needs tests/fixtures/c), its gate-budget.toml's pass period (7 days), a
wall cap of 60 s (10 s from M2 on) and a CPU cap of 1 s, and a stand-in lever
(tests/parity/lever.py, committed): it logs each call (case, HEAD, nice value, checkout, the agent
identity it was given) to LEVER_LOG, then does what LEVER_PLAN's entry for the case says (burn: CPU
seconds; sleep: seconds; exit: 0 parity holds, 1 parity fails, 2 refused), printing a line as the
lever does. M1 changes scripts/x, M2 tests/fixtures/c/f and the wall cap, M3 the README. The real
lever's run is proven at its own seam (tests/gate/kit/parity_lever.py); network_free runs it through
the pass, in a target holding it.

due: the last pass began 8 days before, cases b and c proved 3 days and 1 day before, every
fast-run turn held: PR 7's routine (run from a supervisor's pane) starts the pass and goes on
(exit 3), the pass says it waits for a turn and runs no case; once a turn is free it runs a, d, b,
c (never proved first), each at nice 19, at M1 in a scratch worktree (removed after), with no agent
identity, so none of its runs asks a slot; all hold: nothing told. PR 8's routine, inside the
period, starts none.
capped: no pass ever; a and b burn 0.6 s of CPU each, d sleeps past the wall cap. PR 7's pass stops
at the CPU cap after a and b, c and d owed; a pass 8 days later (PR 8) runs c and d first, d
stopped at the wall cap, so d, a and b stay owed.
told: the last pass, 8 days before, proved every case at B; at M3 (PR 9) b fails and c is refused:
the director gets one message naming each with its lever line and its suspect merges (M1 for b's
patch target, M2 for c's needs), neither naming M3; a and d are not named.
network_free: the target holds the real lever and a case whose old and new test connect to a
listener on the caller's loopback: the pass's lever run, in the pass's unit, fails, and the listener
holds no connection.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import shutil
import socket
import sys
import time
from pathlib import Path
from typing import Any

from herdr_messaging import ASSETS, agent, herdr_world, lines
from lane_post_merge_map import DIRECTOR, GREEN, H, Turns
from parity_lever import JUSTFILE, PROBE
from testkit import HERE, ROOT, Ran, Scratch, kit, main

BUDGET = (
    "parity_pass_period_days = 7\n"
    "parity_pass_wall_seconds = {wall}\n"
    "parity_pass_cpu_seconds = 1.0\n"
)
LEVER = """#!/usr/bin/env python3
import json, os, subprocess, sys, tempfile, time
from pathlib import Path

case, root = sys.argv[1], Path(__file__).resolve().parents[2]
plan = json.loads(Path(os.environ["LEVER_PLAN"]).read_text()).get(case, {})
git = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True)
call = {"case": case, "head": git.stdout.strip(), "top": str(root)}
call["nice"] = os.getpriority(os.PRIO_PROCESS, 0)
agent = ("HERDR_PANE_ID", "OCTO_FEATHER_ROLE", "OCTO_FEATHER_PARENT")
call["agent"] = sorted(k for k in agent if k in os.environ)
with open(os.environ["LEVER_LOG"], "a") as f:
    f.write(json.dumps(call) + "\\n")
t = time.process_time()
while time.process_time() - t < plan.get("burn", 0):
    pass
time.sleep(plan.get("sleep", 0))
rc, logs = plan.get("exit", 0), tempfile.mkdtemp(prefix="parity-" + case + "-")
print("restored from b: tests/old.sh")
if rc == 2:
    sys.stderr.write("lever: refused: (a) on the clean tree the old test did not run scripts/x")
    sys.stderr.write(" (exit 1)\\n")
    sys.exit(2)
old = ("pass" if rc == 0 else "FAIL") + " (exit " + str(rc) + ")"
print("defect: none  old: " + old + "  new: pass (exit 0)")
print("parity " + ("holds" if rc == 0 else "FAILS") + ": want both pass with no defect, ", end="")
print("both fail on each; logs: " + logs)
sys.exit(rc)
"""
CASE = 'old = "tests/old_{c}.sh"\nold_at = "0000000"\nneeds = [{needs}]\nnew = "tests/new_{c}.sh"\n'
PATCH = "x breaks\ndiff --git a/scripts/x b/scripts/x\n--- a/scripts/x\n+++ b/scripts/x\n"
STARTED = (
    r"step 5 coverage map: ok: coverage map: skipped: .*; parity pass: started: unit "
    r"(octo-feather-parity-pass-\S+) \(systemd-run --user, wall cap {wall}s, CPU cap 1s, "
    r"limit {limit}s, its lines in {d}/pass\.log\) runs the 4 cases at {m}, oldest proof first, "
    r"{owed} owed \(not run since the last pass began\) first; the routine goes on without it"
)


def _commit(p: Scratch, seed: Path, files: dict[str, str], n: int) -> None:
    for f, text in files.items():
        (seed / f).parent.mkdir(parents=True, exist_ok=True)
        (seed / f).write_text(text)
    for f in files:
        if f.endswith((".py", ".sh")):
            (seed / f).chmod(0o755)
    p.git(seed, "add", "-A")
    p.git(seed, "commit", "-qm", f"c{n}")


def _origin(p: Scratch, commits: list[dict[str, str]]) -> None:
    """origin.git holding COMMITS on main, the target clone of it, the kit install."""
    o, seed = p.root / "origin.git", p.root / "seed"
    p.run(["git", "init", "-q", "--bare", "-b", "main", str(o)])
    p.git(p.root, "init", "-q", "-b", "main", str(seed))
    for n, files in enumerate(commits):
        _commit(p, seed, files, n)
    p.git(seed, "push", "-q", str(o), "HEAD:main")
    p.run(["git", "clone", "-q", str(o), str(p.root / "target")])
    p.run(["git", "clone", "-q", str(o), str(p.root / "kit")])
    p.git(p.root / "kit", "remote", "set-url", "origin", "https://github.com/o/kit.git")


def build(p: Scratch) -> None:
    base = {"gate-budget.toml": BUDGET.format(wall=60), "tests/parity/lever.py": LEVER}
    base["scripts/x"] = "x\n"
    base |= {"tests/fixtures/c/f": "f\n", "README.md": "r\n"}
    for c in "abcd":
        needs = '"tests/fixtures/c"' if c == "c" else ""
        base[f"tests/parity/{c}/case.toml"] = CASE.format(c=c, needs=needs)
    base["tests/parity/b/x-breaks.patch"] = PATCH
    m2 = {"tests/fixtures/c/f": "f2\n", "gate-budget.toml": BUDGET.format(wall=10)}
    _origin(p, [base, {"scripts/x": "x1\n"}, m2, {"README.md": "r3\n"}])


def build_real(p: Scratch) -> None:
    """The target holding the real lever (copied: it finds its repo beside itself), a justfile
    whose `test` runs the one test it names, and one case, net, whose old and new test probe."""
    lever = (ROOT / "tests" / "parity" / "lever.py").read_text()
    base = {"gate-budget.toml": BUDGET.format(wall=600), "tests/parity/lever.py": lever}
    base["justfile"] = JUSTFILE
    base |= {"tests/probe.sh": PROBE, "README.md": "r\n"}
    # old_at HEAD: the old test is the new one, here at every commit
    case = 'old = "tests/probe.sh"\nold_at = "HEAD"\nneeds = []\nnew = "tests/probe.sh"\n'
    base["tests/parity/net/case.toml"] = case
    _origin(p, [base, {"README.md": "r1\n"}, {"README.md": "r2\n"}, {"README.md": "r3\n"}])


class World:
    """The prepared world in S, the target on main at B; PLAN the stand-in lever's plan;
    `post_merge` runs the routine for PR N."""

    def __init__(
        self, s: Scratch, plan: dict[str, dict[str, float]], *, real: bool = False
    ) -> None:
        s.prepare(
            "lane-post-merge-parity-real" if real else "lane-post-merge-parity",
            build_real if real else build,
        )
        self.s, self.t = s, s.root / "target"
        revs = s.git(self.t, "rev-list", "--reverse", "origin/main").split("\n")
        self.b, self.m = revs[-4], revs[-3:]
        s.git(self.t, "checkout", "-q", "-B", "main", self.b)
        self.d = self.t / ".git" / "octo-feather" / "parity-pass"
        self.unit = ""
        s.gh.store("repo.json", {"nameWithOwner": "o/r"})
        s.gh.store("api/repos/o/kit.json", {"nameWithOwner": "o/kit"})
        for n, m in zip((7, 8, 9), self.m, strict=True):
            pr = {"state": "MERGED", "headRefOid": H, "mergeCommit": {"oid": m}}
            pr |= {"baseRefName": "main", "headRefName": f"gh{n}", "title": f"t{n}"}
            s.gh.put(n, pr | {"url": f"https://github.com/o/r/pull/{n}"})
            tree = [{"path": "README.md", "type": "blob", "sha": "r"}]  # no CI workflow
            s.gh.store(f"api/repos/o/r/git/trees/{m}.json", {"sha": m, "tree": tree})
        self.herdr = herdr_world(s, {DIRECTOR: agent(DIRECTOR, "director", "idle")})
        self.state = s.root / "state"
        (self.state / "octo-feather" / "slots").mkdir(parents=True)
        (self.state / "octo-feather" / "director.toml").write_text(f'pane = "{DIRECTOR}"\n')
        (s.bin / "systemd-run").symlink_to(HERE / "systemd.py")
        self.syslog, self.log = s.root / "systemd.log", s.root / "lever.log"
        (s.root / "plan.json").write_text(json.dumps(plan))
        for k in ("VIRTUAL_ENV", "GH_REPO"):
            s.env.pop(k, None)
        s.env |= {
            "XDG_STATE_HOME": str(self.state),
            "OCTO_FEATHER_KIT_INSTALL": str(s.root / "kit"),
            "FAKE_SYSTEMD_LOG": str(self.syslog),
            "LEVER_LOG": str(self.log),
            "LEVER_PLAN": str(s.root / "plan.json"),
            "PATH": f"{ASSETS}{os.pathsep}{s.env['PATH']}",
        }

    def seed(self, began_days: float, cases: dict[str, float]) -> None:
        """The pass record: the last pass began BEGAN_DAYS before; each case of CASES proved at B
        that many days before."""
        self.d.mkdir(parents=True, exist_ok=True)
        seen = {
            c: {"result": "pass", "exit": 0, "merge": self.b, "at": ago(n)}
            for c, n in cases.items()
        }
        rec = {"began": ago(began_days), "running": None, "last": None, "cases": seen}
        (self.d / "pass.json").write_text(json.dumps(rec))

    def age(self, days: float) -> None:
        """The last pass's start moved DAYS back, as if it began then."""
        rec = self.record()
        rec["began"] = ago(days)
        (self.d / "pass.json").write_text(json.dumps(rec))

    def post_merge(self, n: int, **env: str) -> Ran:
        r = self.s.run(
            [kit("octo-feather-lane"), "post-merge", str(n), H, "--lane", f"gh{n}"],
            want=3,
            cwd=self.t,
            env=env,
        )
        sys.stdout.write(f"$ octo-feather-lane post-merge {n} ...  # exit {r.rc}\n{r.out}\n")
        assert r.out.split("\n")[-1] == GREEN.format(lane=f"gh{n}", pr=n), r.out
        return r

    def step5(self, r: Ran) -> str:
        return next(x for x in r.out.split("\n") if x.startswith("step 5 "))

    def started(self, r: Ran, m: str, owed: int, wall: int = 60) -> None:
        """R's step 5 line says the pass started at M, its wall cap WALL, OWED cases owed first;
        its unit is self.unit from then on."""
        line = self.step5(r)
        d = re.escape(str(self.d))
        want = STARTED.format(d=d, m=m[:12], owed=owed, wall=wall, limit=wall + 300)
        got = re.fullmatch(want, line)
        assert got, f"want the pass started at {m[:12]}, {owed} owed: {line}"
        self.unit = self.unit or got[1]
        assert got[1] == self.unit, line

    def ended(self, units: int) -> None:
        """Waits until UNITS pass units have ended (each logged after its stop hook ran)."""
        end = time.monotonic() + 60
        while sum(f"unit {self.unit} ended" in x for x in lines(self.syslog)) < units:
            assert time.monotonic() < end, f"units never ended: {lines(self.syslog)}"
            time.sleep(0.1)
        log = self.d / "pass.log"
        sys.stdout.write(f"# the pass's lines\n{log.read_text() if log.exists() else ''}")

    def waiting(self) -> None:
        log, said = self.d / "pass.log", "parity pass: waiting for a free fast-run turn (held: "
        end = time.monotonic() + 60
        while said not in (log.read_text() if log.exists() else ""):
            assert time.monotonic() < end, f"the pass never said it waits: {lines(log)}"
            time.sleep(0.1)

    def calls(self) -> list[dict[str, Any]]:
        return [json.loads(x) for x in lines(self.log)]

    def said(self) -> list[str]:
        prompts = lines(self.herdr / "prompts")
        return [x.split("\t", 1)[1] for x in prompts if x.startswith(DIRECTOR)]

    def record(self) -> dict[str, Any]:
        return json.loads((self.d / "pass.json").read_text())

    def show(self) -> None:
        """The pass record, on stdout: what a demo reads."""
        sys.stdout.write(f"# the pass record, {self.d / 'pass.json'}\n")
        sys.stdout.write(json.dumps(self.record(), indent=1) + "\n")

    def trees(self) -> list[str]:
        out = self.s.git(self.t, "worktree", "list", "--porcelain")
        return [x for x in out.split("\n") if x.startswith("worktree ")]


def ago(days: float) -> str:
    then = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)
    return then.isoformat(timespec="seconds")


def due(s: Scratch) -> None:
    w = World(s, {})
    m1 = w.m[0]
    w.seed(8, {"b": 3, "c": 1})
    turns = Turns(w.state)
    try:
        r = w.post_merge(7, OCTO_FEATHER_ROLE="supervisor")
        w.started(r, m1, 2)  # a and d, never proved
        w.waiting()  # every fast-run turn held: the pass waits, no case run
        assert w.calls() == [], f"a case ran while every fast-run turn was held: {w.calls()}"
    finally:
        turns.release()
    w.ended(1)
    calls = w.calls()
    assert [c["case"] for c in calls] == ["a", "d", "b", "c"], calls
    for c in calls:
        assert c["nice"] == 19, f"want the lowest priority: {calls}"
        assert (c["head"], c["agent"]) == (m1, []), calls
        assert c["top"] != str(w.t), f"run in the checkout, not a scratch worktree: {calls}"
    rec = w.record()
    for c in "abcd":
        e = rec["cases"][c]
        assert (e["result"], e["exit"], e["merge"]) == ("pass", 0, m1), rec
        assert e["line"].startswith("parity holds: "), rec
        assert Path(e["log"]).is_file(), rec
    assert (rec["last"]["result"], rec["last"]["owed"], rec["running"]) == ("done", [], None), rec
    assert len(w.trees()) == 1, w.trees()
    assert w.said() == [], f"told with no dead case: {w.said()}"
    r = w.post_merge(8)
    line = w.step5(r)
    assert re.search(r"; parity pass: not due: the last began \S+, 0\.0 days ago", line), line
    assert line.endswith("(period 7 days)"), line
    assert len(w.calls()) == 4, f"a merge inside the period ran cases: {w.calls()}"
    assert sum(" --unit=octo-feather-parity-pass-" in x for x in lines(w.syslog)) == 1


def capped(s: Scratch) -> None:
    w = World(s, {"a": {"burn": 0.6}, "b": {"burn": 0.6}, "d": {"sleep": 120}})
    m1, m2, _ = w.m
    w.started(w.post_merge(7), m1, 0)
    w.ended(1)
    assert [c["case"] for c in w.calls()] == ["a", "b"], w.calls()
    w.show()
    last = w.record()["last"]
    assert (last["result"], last["owed"]) == ("capped", ["c", "d"]), last
    assert last["why"].startswith("the CPU cap, 1 s, reached ("), last
    w.age(8)
    w.started(w.post_merge(8), m2, 2, wall=10)
    w.ended(2)
    assert [c["case"] for c in w.calls()] == ["a", "b", "c", "d"], w.calls()
    w.show()
    rec = w.record()
    last = rec["last"]
    assert (last["result"], last["owed"]) == ("capped", ["d", "a", "b"]), last
    assert last["why"] == "the wall cap, 10 s, reached while d ran: stopped", last
    assert "d" not in rec["cases"], rec
    assert (rec["cases"]["c"]["merge"], rec["cases"]["a"]["merge"]) == (m2, m1), rec
    assert len(w.trees()) == 1, w.trees()
    assert w.said() == [], w.said()


def told(s: Scratch) -> None:
    w = World(s, {"b": {"exit": 1}, "c": {"exit": 2}})
    m1, m2, m3 = w.m
    w.seed(8, dict.fromkeys("abcd", 8))
    w.started(w.post_merge(9), m3, 0, wall=10)
    w.ended(1)
    w.show()
    said = w.said()
    sys.stdout.write("# the director's messages\n" + "\n".join(said) + "\n")
    assert len(said) == 1, said
    parts = said[0].split(" | ")
    assert re.fullmatch(
        rf"parity pass at {m3[:12]} \(lane gh9, PR #9, began \S+\): 2 dead cases, each no longer "
        "proving its new test",
        parts[0],
    ), said
    log = w.d / "logs"
    b, c = parts[1], parts[2]
    assert b.startswith(
        "b: fails (exit 1): parity FAILS: want both pass with no defect, both fail on each; logs: "
    ), b
    assert f" (log {log}/b.log); suspect merges since its last pass at {w.b[:12]}: " in b, b
    assert c.startswith(
        "c: refused (exit 2): lever: refused: (a) on the clean tree the old test did not run "
        f"scripts/x (exit 1) (log {log}/c.log); suspect merges since its last pass at {w.b[:12]}: "
    ), c
    assert re.search(rf": {m1[:7]}[0-9a-f]* c1$", b), f"want M1 alone, b's patch target: {b}"
    assert re.search(rf": {m2[:7]}[0-9a-f]* c2$", c), f"want M2 alone, c's needs: {c}"
    assert parts[3:] == ["owed to the next pass: none"], said
    rec = w.record()
    assert [rec["cases"][x]["result"] for x in "abcd"] == ["pass", "fails", "refused", "pass"]


def network_free(s: Scratch) -> None:
    if shutil.which("bwrap") is None:
        sys.exit("bwrap is not on PATH: the lever refuses to run without it (lever.py --help)")
    w = World(s, {}, real=True)
    with socket.create_server(("127.0.0.1", 0)) as srv:
        port = str(srv.getsockname()[1])
        r = w.post_merge(7, PROBE_PORT=port)
        line = w.step5(r)
        got = re.search(r"parity pass: started: unit (octo-feather-parity-pass-\S+) ", line)
        assert got, line
        w.unit = got[1]
        w.ended(1)
        srv.settimeout(0)
        reached = 0
        while True:
            try:
                srv.accept()[0].close()
            except OSError:  # none pending
                break
            reached += 1
    e = w.record()["cases"]["net"]
    assert (e["result"], e["exit"]) == ("fails", 1), e
    assert reached == 0, f"{reached} connection(s) reached the caller's loopback: {e}"
    for side in ("old", "new"):
        out = (Path(e["logs"]) / f"none.{side}.log").read_text()
        assert "Connection refused" in out, out  # it tried, and found no listener
        assert "probe: reached" not in out, out


if __name__ == "__main__":
    main(due, capped, told, network_free)
