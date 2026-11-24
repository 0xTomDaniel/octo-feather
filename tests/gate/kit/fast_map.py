"""`just fast` (quality #acceptance-fast-affected; what the fast tier runs: quality #recipe-fast),
`just fast-map`, the coverage map it selects from, and `just fast-list`, its dry run, through the
commands only, in a throwaway git copy of the kit (tests/gate/kit/fast_slot_free.py's box: the
kit's tracked files without its tests, its own octo-feather-slot over a scratch XDG_STATE_HOME,
lane gh8 holding the heavy grant, fast_workers 1, one static check, check-probe, logging to
PROBE). The copy runs in the kit's own synced venv by its real path (UV_PROJECT_ENVIRONMENT, as
tests/gate/kit/check_languages.py runs a copy), so no scenario builds one. Its test items, each
appending its name (a tests/*.sh with the priority it ran at, nice(1) and ionice(1)) to RAN:
tests/a.sh and tests/b.sh each run their own Python script, tests/c.sh (`# gate: e2e`) runs a's,
tests/d.sh a bash script coverage cannot see, tests/e.sh runs b's and fails while RAN.fail exists;
and tests/fixtures/fast/test_f.py as a pytest kit test file, each of its three functions its own
gate item (test_one runs fixture-a, test_two fixture-g, test_e2e carries pytest's e2e marker).
That copy is prepared once per gate run (testkit Scratch.prepare), and once more with a coverage
map: `just fast-map` run with RAN.fail present, its exit and output kept beside it.

slot_free (quality #acceptance-fast-map-slot-free): while gh8's run holds the heavy slot, gh7's
`just fast-map` (no grant: a run asking the slot would be refused, exit 75) passes, says it runs
as the fast tier at the lowest priority, runs every non-e2e test item (a, b, d, e, one, two) at
that priority, never the e2e ones or the static check (check-probe logs nothing), and maps the
five whose Python it measured, naming d.sh, which left no coverage data; the slot still names
gh8's run. The run's exit is the tests' and the map's alone: on a lane branch whose
gate-budget.toml puts every item over the per-test CPU budget and whose tests/b.sh changed since
main, the budget, which would fail a gate run on b.sh, does not judge the mapping run. Then,
fixture-a changed, `just fast-list` chooses a.sh and test_one (their coverage reaches it) and
d.sh (unmapped), each named with why, the e2e items named skipped, and runs none.
behind (quality #acceptance-fast-map-behind): main at M0, then M1 and M2; branch lane cut at M0
with a commit of its own; coverage maps at M0, M1 and M2 (the map file `just fast-map` writes,
scripts/octo-feather-gate --help, here holding no item, so every item is unmapped). On lane,
`just fast-list` names the map at M0 two main commits behind main's newest map at M2, then selects
from it; on main at M2 it names none.
On the mapped copy:
unchanged: the mapping run with e.sh failing was red, yet wrote the map from the items that
passed (a, b, one, two), e.sh named left out; `just fast` with nothing changed runs only the items
with no recorded coverage, d (unmapped) and e (did not pass), e named so, as `just fast-list`
names it first, running nothing.
one_script: fixture-a changed: `just fast` runs the static check, the items whose recorded
coverage reaches fixture-a (a.sh, and test_one alone of its file's functions) and the unmapped
ones, each named; the e2e items named skipped.
listed: a change to shared-machinery.txt (listed, no coverage reaches it): every non-e2e item;
`just fast-list` names the same selection and runs nothing.
absent: a file absent at the map head, not on the list: every non-e2e item, the file named.
full_pass: a commit past the map (fixture-a gated, tests/b.sh changed); with no git identity the
record of its full pass is refused, naming how to set one, and records nothing; recorded, only
changes past it feed coverage selection, and b.sh, changed since the map head, stays selected.
diff_base (quality #acceptance-fast-diff-base): three main commits past the map (one changing
shared-machinery.txt, one adding a file, one changing tests/b.sh), then branch lane cut from main
with fixture-a changed in a commit of its own: `just fast-list` names the diff base, lane's merge
base with main, and chooses a.sh and test_one (coverage reaches fixture-a), b.sh (changed since
the map), d.sh and e.sh (unmapped), each with why, and none for main's listed or added files.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from typing import TYPE_CHECKING

from fast_slot_free import LOWEST, PANE, TIER, agent, box, held, status
from gate_recipes_first import gate_env
from testkit import FIXTURES, ROOT, Scratch, main

if TYPE_CHECKING:
    from pathlib import Path

ITEM = """#!/usr/bin/env bash
{tag}set -euo pipefail
echo "{n} $(nice) $(ionice)" >> "$RAN"
"$(dirname "$0")/../scripts/fixture-{script}"
"""
PY = '#!/usr/bin/env python3\nprint("{n} ran")\n'
IDENT = {
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@t",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@t",
}


def items(p: Scratch, k: Path) -> None:
    """K's test items and fixture scripts (this file's docstring), committed."""
    for n in ("a", "b", "g"):
        (k / "scripts" / f"fixture-{n}").write_text(PY.format(n=n))
    (k / "scripts" / "fixture-d").write_text("#!/usr/bin/env bash\necho d ran\n")
    for n, script, tag in (("a", "a", ""), ("b", "b", ""), ("c", "a", "# gate: e2e\n")):
        (k / "tests" / f"{n}.sh").write_text(ITEM.format(n=n, tag=tag, script=script))
    (k / "tests" / "d.sh").write_text(ITEM.format(n="d", tag="", script="d"))
    e = ITEM.format(n="e", tag="", script="b") + '[[ ! -e "$RAN.fail" ]]\n'
    (k / "tests" / "e.sh").write_text(e)
    for x in [*(k / "scripts").glob("fixture-*"), *(k / "tests").glob("?.sh")]:
        x.chmod(0o755)
    test_f = (FIXTURES / "fast" / "test_f.py").read_text()
    (k / "tests" / "gate" / "kit" / "test_f.py").write_text(test_f)
    p.git(k, "add", "-A")
    p.git(k, "commit", "-qm", "the fast items")


def build(p: Scratch) -> None:
    items(p, box(p))


def kit(s: Scratch, *, mapped: bool = False) -> Path:
    """The prepared copy in S, with its map when MAPPED (build_mapped), S's env as box sets it,
    the copy's venv the kit's own."""
    if mapped:
        s.prepare("fast-mapped", build_mapped)
    else:
        s.prepare("fast-map", build)
    s.env = {k: v for k, v in s.env.items() if k not in PANE}
    s.env |= {
        "XDG_STATE_HOME": str(s.root / "state"),
        "UV_PROJECT_ENVIRONMENT": os.path.realpath(ROOT / ".venv"),
    }
    return s.root / "kit"


def just(s: Scratch, k: Path, *recipe: str, **env: str) -> tuple[int, str, list[str]]:
    """`just RECIPE` in K as gh7's implementer: its exit, its output (stdout and stderr together),
    and the names RAN logged."""
    ran = s.root / "ran"
    ran.write_text("")
    p = subprocess.run(
        ["just", *recipe],  # noqa: S607
        cwd=k,
        env=gate_env(s, s.root / "probe", RAN=str(ran), FAST_RAN=str(ran), **agent("w9"), **env),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    return p.returncode, p.stdout, ran.read_text().splitlines()


def build_mapped(p: Scratch) -> None:
    k = kit(p)
    (p.root / "ran.fail").touch()
    rc, out, _ = just(p, k, "fast-map")
    (p.root / "ran.fail").unlink()
    (p.root / "map.out").write_text(f"exit {rc}\n{out}")


def fast(s: Scratch, k: Path, want: str) -> str:
    """`just fast` in K, green, having run exactly the static check and the items WANT (sorted,
    space-separated); its output."""
    rc, out, ran = just(s, k, "fast")
    got = " ".join(sorted(ln.split()[0] for ln in ran))
    said = f"just fast: exit {rc}, ran {got!r}, want {want!r}\n{out}"
    assert rc == 0, said
    assert got == want, said
    assert re.search(rf"=+ {len(want.split()) + 1} passed in ", out), said
    return out


def slot_free(s: Scratch) -> None:
    k = kit(s)
    (s.root / "probe").write_text("")
    s.git(k, "checkout", "-q", "-b", "lane")
    budget = k / "gate-budget.toml"
    tiny = "test_cpu_seconds = 0.001"
    text = re.sub(r"^test_cpu_seconds = .*$", tiny, budget.read_text(), flags=re.MULTILINE)
    budget.write_text(text)
    with (k / "tests" / "b.sh").open("a") as f:
        f.write("# changed in the lane\n")
    s.git(k, "commit", "-qam", "every item over the CPU budget; b.sh changed since main")
    with held(s, k):
        rc, out, ran = just(s, k, "fast-map", GATE_WORKERS="8")
        said = f"just fast-map: exit {rc}\nran: {ran}\n{out}"
        assert rc == 0, said
        assert f"heavy slot: not needed: fast tier, {TIER}" in out, said
        assert sorted(ln.split()[0] for ln in ran) == ["a", "b", "d", "e", "one", "two"], said
        assert all(ln.endswith(LOWEST) for ln in ran if " " in ln), f"want {LOWEST}: {said}"
        assert re.search(r"fast-map: 5 test items mapped at [0-9a-f]{12}: ", out), said
        no_data = "fast-map: tests/d.sh: no coverage data: left out of the map, always selected"
        assert no_data in out, said
        static = (s.root / "probe").read_text()
        assert static == "", f"a static check ran: {static}\n{said}"
        st = status(s, k)
        assert re.search(r"run holding it now: pid \d+ of lane gh8 since ", st), st
    with (k / "scripts" / "fixture-a").open("a") as f:
        f.write("# one-script change\n")
    rc, out, ran = just(s, k, "fast-list")
    said = f"just fast-list: exit {rc}\n{out}"
    assert rc == 0, said
    assert ran == [], f"an item ran: {said}"
    for want in (
        "fast: tests/a.sh: recorded coverage reaches scripts/fixture-a",
        "fast: tests/gate/kit/test_f.py::test_one: recorded coverage reaches scripts/fixture-a",
        "fast: tests/d.sh: no recorded coverage in the map at ",
        "fast: tests/c.sh: e2e (# gate: e2e): skipped",
        "fast: tests/gate/kit/test_f.py::test_e2e: e2e (marker): skipped",
        "fast: 3 non-e2e test items skipped",
        "fast: selected 4 of 9 gate items (1 static, 3 of 8 test items)",
    ):
        assert want in out, f"want {want!r}: {said}"
    for skipped in ("tests/b.sh", "tests/e.sh", "test_f.py::test_two"):
        assert f"fast: {skipped}:" not in out, said


def behind(s: Scratch) -> None:
    k = kit(s)
    heads = [s.git(k, "rev-parse", "HEAD")]
    s.git(k, "branch", "lane")
    for n in (1, 2):
        (k / f"main-{n}.txt").write_text(f"{n}\n")
        s.git(k, "add", "-A")
        s.git(k, "commit", "-qm", f"main {n}")
        heads.append(s.git(k, "rev-parse", "HEAD"))
    maps = k / ".git" / "octo-feather" / "fast-map"
    maps.mkdir(parents=True)
    for h in heads:
        (maps / f"{h}.json").write_text(json.dumps({"head": h, "items": {}, "not_passed": []}))
    rc, out, _ = just(s, k, "fast-list")
    said = f"just fast-list on main: exit {rc}\n{out}"
    assert rc == 0, said
    assert "behind main's newest map" not in out, said
    s.git(k, "checkout", "-q", "lane")
    (k / "lane.txt").write_text("lane\n")
    s.git(k, "add", "-A")
    s.git(k, "commit", "-qm", "lane")
    rc, out, ran = just(s, k, "fast-list")
    said = f"just fast-list on lane: exit {rc}\n{out}"
    assert rc == 0, said
    line = (
        f"fast: map at {heads[0][:12]}: 2 main commits behind main's newest map at"
        f" {heads[2][:12]} (main): more items may be selected; merge main for a newer map"
    )
    assert line in out, f"want {line!r}: {said}"
    assert "fast: all 6 non-e2e test items: lane.txt absent at the map head " in out, said
    assert "fast: selected 7 of 9 gate items (1 static, 6 of 8 test items)" in out, said
    assert ran == [], f"an item ran: {said}"


def unchanged(s: Scratch) -> None:
    k = kit(s, mapped=True)
    m = (s.root / "map.out").read_text()
    assert not m.startswith("exit 0\n"), f"want the mapping run red (e.sh failed): {m}"
    assert re.search(r"fast-map: 4 test items mapped at ", m), f"want a, b, one, two: {m}"
    assert "fast-map: tests/e.sh did not pass: left out of the map, always selected" in m, m
    failed = (
        r"fast: tests/e\.sh: did not pass the mapping run at [0-9a-f]{12}, so unmapped:"
        r" always selected"
    )
    rc, dry, ran = just(s, k, "fast-list")
    said = f"just fast-list: exit {rc}\n{dry}"
    assert rc == 0, said
    assert ran == [], f"an item ran: {said}"
    assert re.search(failed, dry), f"want e.sh named as not passing the mapping run: {said}"
    out = fast(s, k, "d e")
    assert re.search(failed, out), out


def one_script(s: Scratch) -> None:
    k = kit(s, mapped=True)
    with (k / "scripts" / "fixture-a").open("a") as f:
        f.write("# changed\n")
    out = fast(s, k, "a d e one")
    for want in (
        "fast: check-probe: static check",
        "fast: tests/a.sh: recorded coverage reaches scripts/fixture-a",
        "fast: tests/gate/kit/test_f.py::test_one: recorded coverage reaches scripts/fixture-a",
        "fast: tests/d.sh: no recorded coverage in the map at",
        "fast: tests/c.sh: e2e",
        "fast: tests/gate/kit/test_f.py::test_e2e: e2e",
        "fast: tests/e.sh: did not pass the mapping run at",
        "fast: selected 5 of 9 gate items (1 static, 4 of 8 test items)",
    ):
        assert want in out, f"want {want!r} in just fast: {out}"


def listed(s: Scratch) -> None:
    k = kit(s, mapped=True)
    with (k / "shared-machinery.txt").open("a") as f:
        f.write("# changed\n")
    rc, dry, ran = just(s, k, "fast-list")
    said = f"just fast-list: exit {rc}\n{dry}"
    assert rc == 0, said
    assert ran == [], f"an item ran: {said}"
    out = fast(s, k, "a b d e one two")
    for want in (
        "fast: all 6 non-e2e test items: shared-machinery.txt on shared-machinery.txt",
        "fast: selected 7 of 9 gate items (1 static, 6 of 8 test items)",
    ):
        assert want in out, f"want {want!r} in just fast: {out}"
        assert want in dry, f"want {want!r} in just fast-list: {dry}"


def absent(s: Scratch) -> None:
    k = kit(s, mapped=True)
    (k / "scripts" / "fixture-new").write_text('#!/usr/bin/env python3\nprint("new")\n')
    out = fast(s, k, "a b d e one two")
    want = "fast: all 6 non-e2e test items: scripts/fixture-new absent at the map head "
    assert want in out, out
    assert ", outside the coverage map's reach" in out, out


def full_pass(s: Scratch) -> None:
    k = kit(s, mapped=True)
    with (k / "scripts" / "fixture-a").open("a") as f:
        f.write("# gated\n")
    with (k / "tests" / "b.sh").open("a") as f:
        f.write("# changed test\n")
    s.git(k, "commit", "-qam", "past the map")
    head = s.git(k, "rev-parse", "HEAD")
    gate = [str(k / "scripts" / "octo-feather-gate")]
    noid = s.root / "noid"
    noid.mkdir()
    bare = {k: v for k, v in s.env.items() if k not in IDENT} | {
        "HOME": str(noid),
        "XDG_CONFIG_HOME": str(noid),
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "EMAIL": "",
    }
    record = [*gate, "record", "--reason", "full pass", "--seconds", "1"]
    p = subprocess.run(record, cwd=k, env=bare, capture_output=True, text=True, check=False)
    said = f"exit {p.returncode}\n{p.stdout}{p.stderr}"
    assert p.returncode != 0, said
    assert "not recorded: no git identity" in said, said
    assert "git config user.name 'NAME' and git config user.email 'EMAIL'" in said, said
    s.run([*gate, "passed"], cwd=k, want=1)
    s.run(record, cwd=k, env=IDENT)
    out = fast(s, k, "b d e")
    for want in (
        f"fast: diff base: {head[:12]}, the latest recorded full pass",
        "fast: tests/b.sh: changed since the map at",
    ):
        assert want in out, f"want {want!r}: {out}"


def diff_base(s: Scratch) -> None:
    k = kit(s, mapped=True)
    with (k / "shared-machinery.txt").open("a") as f:
        f.write("# main's own change\n")
    s.git(k, "commit", "-qam", "main: the list")
    (k / "scripts" / "fixture-main").write_text('#!/usr/bin/env python3\nprint("main")\n')
    s.git(k, "add", "-A")
    s.git(k, "commit", "-qm", "main: a new file")
    with (k / "tests" / "b.sh").open("a") as f:
        f.write("# main changed this test\n")
    s.git(k, "commit", "-qam", "main: a test")
    left = s.git(k, "rev-parse", "HEAD")
    s.git(k, "checkout", "-qb", "lane")
    with (k / "scripts" / "fixture-a").open("a") as f:
        f.write("# one-script change\n")
    s.git(k, "commit", "-qam", "lane: one script")
    rc, out, ran = just(s, k, "fast-list")
    said = f"just fast-list: exit {rc}\n{out}"
    assert rc == 0, said
    assert ran == [], f"an item ran: {said}"
    for want in (
        f"fast: diff base: {left[:12]}, HEAD's merge base with main",
        "fast: tests/a.sh: recorded coverage reaches scripts/fixture-a",
        "fast: tests/gate/kit/test_f.py::test_one: recorded coverage reaches scripts/fixture-a",
        "fast: tests/b.sh: changed since the map at ",
        "fast: tests/d.sh: no recorded coverage in the map at ",
        "fast: tests/e.sh: did not pass the mapping run at ",
        "fast: 1 non-e2e test items skipped",
        "fast: selected 6 of 9 gate items (1 static, 5 of 8 test items)",
    ):
        assert want in out, f"want {want!r}: {said}"
    for main_only in ("shared-machinery.txt", "fixture-main", "test_f.py::test_two:"):
        assert main_only not in out, f"want no {main_only!r}: {said}"


if __name__ == "__main__":
    main(slot_free, behind, unchanged, one_script, listed, absent, full_pass, diff_base)
