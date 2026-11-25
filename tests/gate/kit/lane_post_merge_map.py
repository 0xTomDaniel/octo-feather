"""The scenarios of tests/gate/kit/test_lane_post_merge_map.py (its items), this file their command
(testkit.main): scripts/octo-feather-lane post-merge step 5, the coverage map (issue 1250; quality
#acceptance-map-after-merge, #acceptance-map-full-daily, #acceptance-map-build-failed), offline.

The world: a target repo's origin (main: B, then three merge commits M1, M2, M3, each changing
files) and its clone, the director's checkout, on main at B; a kit install clone of another repo
(o/kit: step 3 leaves it unchanged); the testkit's fake gh holding PRs 7, 8 and 9 (lanes gh7, gh8,
gh9) merged as M1, M2 and M3, with no CI workflow (step 2 ok at once); the testkit's Herdr
stand-in with the director's pane w9:p99 (director.toml) under the kit's own herdr-say; the
testkit's systemd stand-in (testkit/systemd.py) as systemd-run and systemctl, each unit's end in
its log; a scratch state dir (XDG_STATE_HOME), its slots dir holding the box's fast-run turns.
The target's fast-map recipe is a stand-in build (fake_map.py, committed in the target): the job's
real `just fast-map --since-newest` is proven at its own seam (tests/gate/kit/fast_map.py,
incremental); here what the routine runs is what is proven: the stand-in logs each call (HEAD, its
arguments, its nice value, its checkout) to MAP_LOG, then, unless MAP_LOG.fail exists, writes a
map for HEAD into the clone's map dir. The clone's map dir starts with the map at B and the build
record naming B's full map built an hour before (or more than a day: full_daily).

after_merge: both fast-run turns held (two fast runs live, so the next would wait), PR 7's
routine starts the clone's map job and goes on (exit 3, step 8 pending), its map not yet built;
PR 8's is queued behind it, PR 9's replaces PR 8's; the job's lines say it waits for a free
turn, and no build has run. Once a turn is free the job builds M1, then
M3, each `just fast-map --since-newest` at its merge commit in a scratch worktree (removed
after), at nice 19; M2 is never mapped, and every unit ended.
full_daily: the last full map built more than a day before: PR 7's build is a full `just
fast-map`, recorded as the new full map; PR 8's then re-maps only.
build_failed: the build writes no map (the stand-in fails): the maps stay as they were (B's
alone), and the director gets one message naming the failure; a unit killed at its limit (the
stand-in's FAKE_SYSTEMD_KILLED) the same, through the unit's stop hook.
"""

from __future__ import annotations

import datetime as dt
import fcntl
import json
import os
import re
import sys
import time

import tomllib
from herdr_messaging import ASSETS, agent, herdr_world, lines
from testkit import HERE, ROOT, Ran, Scratch, kit, main

H = "1234567890abcdef1234567890abcdef12345678"  # each PR's pinned head
DIRECTOR = "w9:p99"
JUSTFILE = 'set positional-arguments\n\nfast-map *args:\n    @python3 fake_map.py "$@"\n'
FAKE_MAP = """import json, os, subprocess, sys
from pathlib import Path

def git(*a):
    return subprocess.run(["git", *a], capture_output=True, text=True, check=True).stdout.strip()

head, log = git("rev-parse", "HEAD"), os.environ["MAP_LOG"]
call = {"head": head, "args": sys.argv[1:], "nice": os.getpriority(os.PRIO_PROCESS, 0)}
call["top"] = git("rev-parse", "--show-toplevel")
with open(log, "a") as f:
    f.write(json.dumps(call) + "\\n")
if Path(log + ".fail").exists():
    sys.exit("fake fast-map: failed, no map written")
d = Path(git("rev-parse", "--path-format=absolute", "--git-common-dir"))
d = d / "octo-feather" / "fast-map"
d.mkdir(parents=True, exist_ok=True)
(d / (head + ".json")).write_text(json.dumps({"head": head, "items": {}, "not_passed": []}))
print("fast-map: 0 test items re-mapped at " + head[:12])
"""
STEP5 = (
    "step 5 coverage map: ok: coverage map: started: unit {unit} (systemd-run --user, limit 3600s,"
    " its lines in {maps}/build.log) builds the map for {m}; the routine goes on without it"
)
UNIT = "octo-feather-fast-map-"  # the job unit's name, its clone id after it (--help, step 5)
GREEN = (
    "post-merge {lane} PR #{pr}: step 1 merged ok; step 2 main CI ok; step 3 kit refresh ok; "
    "step 4 checkout ok; step 5 coverage map ok; step 6 stale agents ok; step 7 tell supervisors "
    "ok; step 8 teardown pending"
)


def build(p: Scratch) -> None:
    """origin.git (main: B, M1, M2, M3), the target clone on main at B, the kit install."""
    o, seed = p.root / "origin.git", p.root / "seed"
    p.run(["git", "init", "-q", "--bare", "-b", "main", str(o)])
    p.git(p.root, "init", "-q", "-b", "main", str(seed))
    (seed / "tests").mkdir()
    for n, files in enumerate(
        [
            {"justfile": JUSTFILE, "fake_map.py": FAKE_MAP, "tests/test_a.py": "", "x.py": ""},
            {"tests/test_a.py": "# m1\n", "x.py": "# m1\n"},
            {"tests/test_b.py": "# m2\n"},
            {"x.py": "# m3\n"},
        ]
    ):
        for f, text in files.items():
            (seed / f).write_text(text)
        p.git(seed, "add", "-A")
        p.git(seed, "commit", "-qm", f"c{n}")
    p.git(seed, "push", "-q", str(o), "HEAD:main")
    p.run(["git", "clone", "-q", str(o), str(p.root / "target")])
    p.run(["git", "clone", "-q", str(o), str(p.root / "kit")])
    p.git(p.root / "kit", "remote", "set-url", "origin", "https://github.com/o/kit.git")


class World:
    """The prepared world in S, the target on main at B, its maps: B's, and the record of B's full
    map built AGE seconds before; `post_merge` runs the routine for PR N."""

    def __init__(self, s: Scratch, age: float = 3600) -> None:
        s.prepare("lane-post-merge-map", build)
        self.s, self.t = s, s.root / "target"
        self.b, *self.m = s.git(self.t, "rev-list", "--reverse", "origin/main").split("\n")
        s.git(self.t, "checkout", "-q", "-B", "main", self.b)
        self.maps = self.t / ".git" / "octo-feather" / "fast-map"
        self.maps.mkdir(parents=True)
        self.map(self.b)
        at = dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=age)
        full = {"merge": self.b, "at": at.isoformat(timespec="seconds")}
        record = {"running": None, "queued": None, "last": None, "full": full}
        (self.maps / "build.json").write_text(json.dumps(record))
        self.unit = ""  # the job's unit, as the first started line names it (started)
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
        self.syslog, self.log = s.root / "systemd.log", s.root / "map.log"
        for k in ("VIRTUAL_ENV", "GH_REPO"):
            s.env.pop(k, None)
        s.env |= {
            "XDG_STATE_HOME": str(self.state),
            "OCTO_FEATHER_KIT_INSTALL": str(s.root / "kit"),
            "FAKE_SYSTEMD_LOG": str(self.syslog),
            "MAP_LOG": str(self.log),
            "PATH": f"{ASSETS}{os.pathsep}{s.env['PATH']}",
        }

    def map(self, head: str) -> None:
        (self.maps / f"{head}.json").write_text(
            json.dumps({"head": head, "items": {"tests/test_a.py::t": ["x.py"]}, "not_passed": []})
        )

    def post_merge(self, n: int, want: int = 3, **env: str) -> Ran:
        r = self.s.run(
            [kit("octo-feather-lane"), "post-merge", str(n), H, "--lane", f"gh{n}"],
            want=want,
            cwd=self.t,
            env=env,
        )
        sys.stdout.write(f"$ octo-feather-lane post-merge {n} ...  # exit {r.rc}\n{r.out}\n")
        assert r.out.split("\n")[-1] == GREEN.format(lane=f"gh{n}", pr=n), r.out
        return r

    def step5(self, r: Ran) -> str:
        return next(x for x in r.out.split("\n") if x.startswith("step 5 "))

    def ended(self, units: int) -> None:
        """Waits until UNITS map job units have ended (each logged after its stop hook ran)."""
        end = time.monotonic() + 60
        while sum(f"unit {self.unit} ended" in x for x in lines(self.syslog)) < units:
            assert time.monotonic() < end, f"units never ended: {lines(self.syslog)}"
            time.sleep(0.1)
        build_log = self.maps / "build.log"
        sys.stdout.write(
            f"# the job's lines\n{build_log.read_text() if build_log.exists() else ''}"
        )

    def waiting(self) -> None:
        """Waits until the job's lines (build.log) say it waits for a free fast-run turn; the
        bound is for safety only."""
        log, said = self.maps / "build.log", "map job: waiting for a free fast-run turn (held: "
        end = time.monotonic() + 60
        while said not in (log.read_text() if log.exists() else ""):
            assert time.monotonic() < end, f"the job never said it waits: {lines(log)}"
            time.sleep(0.1)

    def calls(self) -> list[dict[str, object]]:
        """The stand-in fast-map's calls, in order."""
        return [json.loads(x) for x in lines(self.log)]

    def said(self) -> list[str]:
        """Each message Herdr delivered to the director."""
        prompts = lines(self.herdr / "prompts")
        return [x.split("\t", 1)[1] for x in prompts if x.startswith(DIRECTOR)]

    def record(self) -> dict[str, dict[str, object] | None]:
        return json.loads((self.maps / "build.json").read_text())

    def trees(self) -> list[str]:
        """The target clone's worktrees: its main one alone once every scratch one is removed."""
        out = self.s.git(self.t, "worktree", "list", "--porcelain")
        return [x for x in out.split("\n") if x.startswith("worktree ")]


class Turns:
    """Every fast-run turn of the box (fast_runs, the kit's gate-budget.toml) held, as live fast
    runs hold them (tests/gate/heavy_slot.py), until release."""

    def __init__(self, w: World) -> None:
        budget = tomllib.loads((ROOT / "gate-budget.toml").read_text())
        n = int(budget["fast_runs"])
        slots = w.state / "octo-feather" / "slots"
        self.held = [(slots / f"fast-{i}.lock").open("a") for i in range(n)]
        for f in self.held:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)

    def release(self) -> None:
        for f in self.held:
            f.close()


def started(w: World, r: Ran, m: str) -> None:
    """R's step 5 line says the clone's job started for M: its unit, the first such line's, is
    w.unit from then on, and every later one names that same unit."""
    line = w.step5(r)
    pattern = re.escape(STEP5).replace(re.escape("{unit}"), f"({re.escape(UNIT)}\\S+)")
    pattern = pattern.replace(re.escape("{maps}"), re.escape(str(w.maps)))
    got = re.fullmatch(pattern.replace(re.escape("{m}"), m[:12]), line)
    assert got, f"want the job started for {m[:12]}: {r.out}"
    w.unit = w.unit or got[1]
    assert got[1] == w.unit, f"another unit than {w.unit}: {line}"


def after_merge(s: Scratch) -> None:
    w = World(s)
    m1, m2, m3 = w.m
    turns = Turns(w)
    try:
        started(w, w.post_merge(7), m1)
        assert not (w.maps / f"{m1}.json").exists(), "the routine waited for the map"
        r = w.post_merge(8)
        want = f"step 5 coverage map: ok: coverage map: queued: {m2[:12]}, after unit {w.unit}'s"
        assert w.step5(r) == f"{want} build of {m1[:12]}", r.out
        r = w.post_merge(9)
        want = f"step 5 coverage map: ok: coverage map: queued: {m3[:12]}, after unit {w.unit}'s"
        gone = f", replacing queued {m2[:12]}, never mapped"
        assert w.step5(r) == f"{want} build of {m1[:12]}{gone}", r.out
        w.waiting()  # the job says it waits for a turn: every turn is still held
        assert w.calls() == [], f"a build ran while every fast-run turn was held: {w.calls()}"
    finally:
        turns.release()
    w.ended(1)
    calls = w.calls()
    assert [c["head"] for c in calls] == [m1, m3], calls
    for c in calls:
        assert c["args"] == ["--since-newest"], calls
        assert c["nice"] == 19, f"want the lowest priority: {calls}"
        assert c["top"] != str(w.t), f"built in the checkout, not a scratch worktree: {calls}"
    assert (w.maps / f"{m1}.json").is_file(), sorted(p.name for p in w.maps.iterdir())
    assert (w.maps / f"{m3}.json").is_file(), sorted(p.name for p in w.maps.iterdir())
    assert not (w.maps / f"{m2}.json").exists(), "the replaced merge was mapped"
    rec = w.record()
    assert (rec["running"], rec["queued"]) == (None, None), rec
    last = rec["last"] or {}
    assert (last.get("merge"), last.get("result")) == (m3, "ok"), rec
    assert len(w.trees()) == 1, w.trees()
    assert w.said() == [], w.said()


def full_daily(s: Scratch) -> None:
    w = World(s, age=25 * 3600)
    m1, m2, _ = w.m
    started(w, w.post_merge(7), m1)
    w.ended(1)
    started(w, w.post_merge(8), m2)
    w.ended(2)
    calls = w.calls()
    assert [(c["head"], c["args"]) for c in calls] == [(m1, []), (m2, ["--since-newest"])], calls
    full = w.record()["full"]
    assert (full or {}).get("merge") == m1, w.record()


def build_failed(s: Scratch) -> None:
    w = World(s)
    m1, m2, _ = w.m
    before = sorted(p.name for p in w.maps.iterdir())
    (w.log.parent / (w.log.name + ".fail")).touch()
    started(w, w.post_merge(7), m1)
    w.ended(1)
    assert [c["head"] for c in w.calls()] == [m1], w.calls()
    started(w, w.post_merge(8, FAKE_SYSTEMD_KILLED="1"), m2)  # killed at its limit
    w.ended(2)
    maps = sorted(p.name for p in w.maps.iterdir() if p.suffix == ".json")
    assert set(maps) == {f"{w.b}.json", "build.json"}, f"maps changed: {before} -> {maps}"
    said = w.said()
    sys.stdout.write("# the director's messages\n" + "\n".join(said) + "\n")
    assert len(said) == 2, said
    assert said[0].startswith(f"coverage map build for {m1[:12]} (lane gh7, PR #7) failed: "), said
    assert "just fast-map --since-newest exit 1, no map written" in said[0], said
    assert said[1].startswith(f"coverage map build for {m2[:12]} (lane gh8, PR #8) failed: "), said
    assert f"unit {w.unit} ended timeout (killed TERM) while building" in said[1], said
    for x in said:
        assert "the previous map stays the one just fast selects from" in x, said
    rec = w.record()
    assert (rec["running"], rec["queued"]) == (None, None), rec
    assert (rec["last"] or {}).get("result") == "failed", rec
    assert len(w.trees()) == 1, w.trees()


if __name__ == "__main__":
    main(after_merge, full_daily, build_failed)
