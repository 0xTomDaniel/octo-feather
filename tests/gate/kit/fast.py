"""The scenarios of tests/gate/kit/test_fast.py (its items), this file their command
(testkit.main): `just fast` (quality #acceptance-fast-affected; what the fast tier runs: quality
#recipe-fast), `just fast-map`, the coverage map it selects from, and `just fast-list`, its dry
run, through the recipes only (the recipes are the surface: each runs the command under test). A
git copy of the kit's tracked files without its tests (tests/*.sh and its pytest kit tests),
holding eight test items: a.sh and b.sh each run their own Python script, c.sh (`# gate: e2e`)
runs a's, d.sh runs a bash script coverage cannot see, e.sh runs b's and fails while the file
$FAST_RAN.fail exists (the mapping run); and tests/fixtures/fast/test_f.py as a pytest kit test
file, each of its three functions its own gate item. The static checks are cut to one with just's
own command-line override (`just --set GATE_RECIPES check-dashes`); the map is built from the
test items (`just fast-map -k "not test_recipe"`). Each item appends its name to FAST_RAN, the
record of what ran.

The copy and its mapping run, with e.sh failing, are prepared once per gate run
(Scratch.prepare): red, yet the map is written from the items that passed, e.sh left out; each
scenario reads that run's output from the prepared tree and works on its own copy. `selects`:
nothing changed, then one script changed (the dry run too). `past_full_pass`: a listed path no
coverage reaches and a file absent at the map head, then a record with no git identity refused,
then a recorded full pass as the diff base."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

from testkit import FIXTURES, ROOT, Scratch, main, pnpm_store, tool_homes

TAG = "fast test"
# Not copied: the kit's own tests.
TESTS = re.compile(r"tests/[^/]*\.sh|tests/gate/test_cpu\.py|tests/gate/kit/(.*/)?test_[^/]*\.py")
ITEM = (
    '#!/usr/bin/env bash\nset -euo pipefail\necho {n} >> "$FAST_RAN"\n'
    '"$(dirname "$0")/../scripts/fixture-{s}"\n'
)
IDENT = ("GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL")


def setenv(s: Scratch) -> None:
    """The copy's runs: the tools' own installs (testkit.tool_homes), the kit's own venv (the
    copy's pyproject and lock are the kit's: uv sync finds it current), pnpm's store the caller's,
    FAST_RAN under this scratch, and a git identity for every command that commits (a recorded
    full pass is a git note), whatever the box has: a runner may have none."""
    s.env |= tool_homes() | {
        "UV_PROJECT_ENVIRONMENT": str(ROOT / ".venv"),
        "npm_config_store_dir": pnpm_store(),
        "FAST_RAN": str(s.root / "ran"),
    }
    s.env |= dict.fromkeys(IDENT[::2], "t") | dict.fromkeys(IDENT[1::2], "t@t")


def build(p: Scratch) -> None:
    """The copy at P/kit, one commit, and its mapping run with e.sh failing, its exit and output
    in P/map.json."""
    k = p.root / "kit"
    names = subprocess.run(
        ["git", "ls-files", "-z"],  # noqa: S607
        cwd=ROOT,
        capture_output=True,
        check=True,
    ).stdout.decode()
    for rel in filter(None, names.split("\0")):
        src = ROOT / rel
        if TESTS.fullmatch(rel) or not (src.is_file() or src.is_symlink()):
            continue
        (k / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, k / rel, follow_symlinks=False)
    sc, ts = k / "scripts", k / "tests"
    for n in "abg":
        (sc / f"fixture-{n}").write_text(f'#!/usr/bin/env python3\nprint("{n} ran")\n')
    for n, script in (("a", "a"), ("b", "b"), ("d", "d")):
        (ts / f"{n}.sh").write_text(ITEM.format(n=n, s=script))
    (ts / "c.sh").write_text(ITEM.format(n="c", s="a").replace("bash\n", "bash\n# gate: e2e\n", 1))
    (sc / "fixture-d").write_text("#!/usr/bin/env bash\necho d ran\n")
    (ts / "e.sh").write_text(ITEM.format(n="e", s="b") + '[[ ! -e "$FAST_RAN.fail" ]]\n')
    shutil.copy(
        FIXTURES / "fast" / "test_f.py", k / "tests" / "gate" / "kit"
    )  # fixture-g: test_two's
    for f in [*sc.glob("fixture-?"), *ts.glob("?.sh")]:
        f.chmod(0o755)
    p.git(k, "init", "-q")
    p.git(k, "add", "-A")
    p.git(k, "commit", "-qm", "base")
    setenv(p)
    Path(f"{p.env['FAST_RAN']}.fail").touch()
    rc, out = just(p, k, "fast-map", "-k", "not test_recipe")
    (p.root / "map.json").write_text(json.dumps({"rc": rc, "out": out}))
    shutil.rmtree(k / "node_modules")  # each copy's own pnpm install, never a copy of this one
    for f in (p.root / "ran", p.root / "ran.fail"):
        f.unlink(missing_ok=True)


def just(s: Scratch, k: Path, *args: str) -> tuple[int, str]:
    """`just ARGS` in the copy K: its exit, and its stdout and stderr as one stream, uncoloured
    (a CI's FORCE_COLOR colours pytest's lines)."""
    p = subprocess.run(
        ["just", *args],  # noqa: S607
        cwd=k,
        env={**s.env, "PYTEST_ADDOPTS": f"{s.env.get('PYTEST_ADDOPTS', '')} --color=no"},
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    return p.returncode, p.stdout


def copy(s: Scratch) -> Path:
    """This scenario's copy, mapped: the prepared mapping run asserted."""
    s.prepare("fast-kit", build)
    setenv(s)
    m = json.loads((s.root / "map.json").read_text())
    rc, out = m["rc"], m["out"]
    assert rc != 0, f"{TAG}: a mapping run with tests/e.sh failing: want it red (exit {rc}): {out}"
    for want in (
        "fast-map: 5 test items mapped at",  # a, b, c, test_one, test_two
        "fast-map: tests/e.sh did not pass: left out of the map",
    ):
        assert want in out, f"{TAG}: the mapping run with tests/e.sh failing lacks '{want}': {out}"
    return s.root / "kit"


def fast(s: Scratch, k: Path, want: str) -> str:
    """`just fast`, green, ran exactly the static check plus the items WANT (sorted,
    space-separated); its output."""
    ran = Path(s.env["FAST_RAN"])
    ran.write_text("")
    rc, out = just(s, k, "--set", "GATE_RECIPES", "check-dashes", "fast")
    assert rc == 0, f"{TAG}: just fast exited {rc}: {out}"
    got = " ".join(sorted(ran.read_text().split()))
    n = len(want.split()) + 1
    assert got == want, f"{TAG}: want the static check and items '{want}', ran '{got}': {out}"
    assert f"=== {n} passed in " in out, f"{TAG}: want {n} passed: {out}"
    return out


def selects(s: Scratch) -> None:
    """Nothing changed: only the items with no recorded coverage, the unmapped one and the one
    that did not pass. One script changed: the static check, the items whose recorded coverage
    reaches it (a.sh, and test_one alone of its file's functions), and the unmapped items, each
    named; the e2e items named skipped. The dry run names the same and runs nothing."""
    k = copy(s)
    out = fast(s, k, "d e")
    assert "fast: tests/e.sh: did not pass the mapping run at" in out, (
        f"{TAG}: e.sh not named: {out}"
    )
    with (k / "scripts" / "fixture-a").open("a") as f:
        f.write("# changed\n")
    ran = Path(s.env["FAST_RAN"])
    ran.write_text("")
    rc, listed = just(s, k, "--set", "GATE_RECIPES", "check-dashes", "fast-list")
    assert rc == 0, f"{TAG}: just fast-list exited {rc}: {listed}"
    assert not ran.read_text(), f"{TAG}: just fast-list ran an item: {ran.read_text()}"
    count = "fast: selected 5 of 9 gate items (1 static, 4 of 8 test items)"
    assert count in listed, f"{TAG}: just fast-list did not count 5 of 9 selected: {listed}"
    out = fast(s, k, "a d e one")
    for want in (
        "fast: check-dashes: static check",
        "fast: tests/a.sh: recorded coverage reaches scripts/fixture-a",
        "fast: tests/gate/kit/test_f.py::test_one: recorded coverage reaches scripts/fixture-a",
        "fast: tests/d.sh: no recorded coverage in the map at",
        "fast: tests/c.sh: e2e",
        "fast: tests/gate/kit/test_f.py::test_e2e: e2e",
        "fast: tests/e.sh: did not pass the mapping run at",
        "fast: selected 5 of 9 gate items",
    ):
        assert want in out, f"{TAG}: '{want}' not in the just fast output: {out}"
        assert want in listed, f"{TAG}: '{want}' not in the just fast-list output: {listed}"


def past_full_pass(s: Scratch) -> None:
    """A listed path no coverage reaches (the list itself) and a file the map cannot know (absent
    at the map head, not on the list), at once: every non-e2e item, each cause named (one run:
    each cause its own part of the reason). Then a full pass recorded after the map: files
    changed up to it are gated, so only changes past it feed coverage selection; a test item
    changed since the map head stays selected (the map does not know its coverage). Before it, a
    record with no git identity (no env, no repo, global or system config) fails naming it and how
    to set it, and records nothing: the gate never makes one up."""
    k = copy(s)
    with (k / "shared-machinery.txt").open("a") as f:
        f.write("# changed\n")
    new = k / "scripts" / "fixture-new"
    new.write_text('#!/usr/bin/env python3\nprint("new")\n')
    out = fast(s, k, "a b d e one two")
    want = (
        r"fast: all 6 non-e2e test items: shared-machinery\.txt on shared-machinery\.txt; "
        r"scripts/fixture-new absent at the map head \w+, outside the coverage map's reach"
    )
    assert re.search(want, out), f"{TAG}: every item, both causes, not named: {out}"
    s.git(k, "checkout", "-q", "shared-machinery.txt")
    new.unlink()
    with (k / "scripts" / "fixture-a").open("a") as f:
        f.write("# gated\n")
    with (k / "tests" / "b.sh").open("a") as f:
        f.write("# changed test\n")
    s.git(k, "commit", "-qam", "past the map")
    head = s.git(k, "rev-parse", "HEAD")
    gate = str(k / "scripts" / "octo-feather-gate")
    noid = s.root / "noid"
    noid.mkdir()
    env = {key: v for key, v in s.env.items() if key not in IDENT}
    env |= {
        "HOME": str(noid),
        "XDG_CONFIG_HOME": str(noid),
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "EMAIL": "",
    }
    record = [gate, "record", "--reason", "full pass", "--seconds", "1"]
    p = subprocess.run(record, cwd=k, env=env, capture_output=True, text=True, check=False)
    said = p.stdout + p.stderr
    want = (
        r"not recorded: no git identity.*"
        r"git config user\.name 'NAME' and git config user\.email 'EMAIL'"
    )
    assert p.returncode != 0, f"{TAG}: a record with no git identity: want a refusal: {said}"
    assert re.search(want, said, re.DOTALL), f"{TAG}: the refusal does not name it: {said}"
    s.run([gate, "passed"], want=1, cwd=k)  # a refused record left no full pass
    s.run(record, cwd=k)
    out = fast(s, k, "b d e")
    for want in (
        f"fast: diff base: {head[:12]}, the latest recorded full pass",
        "fast: tests/b.sh: changed since the map at",
    ):
        assert want in out, f"{TAG}: '{want}' not in the output past a full pass: {out}"


if __name__ == "__main__":
    main(selects, past_full_pass)
