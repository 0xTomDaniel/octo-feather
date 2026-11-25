"""The gate runs its static checks first (quality #recipes-static-first,
#acceptance-gate-recipes-first; #1019), through `just fast` and `just check` in a throwaway git
copy of the kit's tracked files without its tests, as tests/fast.sh builds one. The copy's
justfile declares two static checks, GATE_RECIPES "check-dashes check-probe" (check-probe, added
to it, logs its name), and its test items are tests/a.sh and tests/b.sh, each logging its name,
tests/a.sh end-to-end by its header (`# gate: e2e`), so `just check` asks the slot and `just fast`
does not (quality #recipes-static-first);
its octo-feather-slot is a stand-in (the box's slot, a system a scratch run must not reach) that
logs each call and answers as the real one does for a lane (scripts/octo-feather-slot --help,
hold): without a grant (the default) `later:` to `hold --if-granted` and `free:` to a plain hold
(the real one's answer under heavy_items); with SLOT_GRANTED set, `held:` to any hold, holding
until its stdin closes, then logging `slot released`. One log, PROBE, so its order is the run's.
A scratch state dir holds the trend file.

red (fast, check or nested, the lane without a grant; granted, `just check` with it): one em
dash committed in the copy makes check-dashes red. `just fast`, `just check` and a nested `just
check` (GATE_NESTED, as a gate item runs a copy's gate: sequential) each exit non-zero, naming
check-dashes and showing its output, the file and line it found; no test item ran, no trend line
says full, and the slot was asked only `--if-granted`: never a slot the lane does not hold (`just
fast`, the fast tier, asked nothing at all).
Granted, that first ask took the lane's slot, before any static check, and the slot was released
at the run's end.
green: with the dash gone, `just check` passes: the slot asked `--if-granted` (later), then
check-probe ran once, then the slot was asked once for every item (4), then each test item ran
once; one trend line, tier full, its steps the four items.
"""

from __future__ import annotations

import json
import re
import subprocess
from typing import TYPE_CHECKING

from testkit import ROOT, Ran, Scratch, main, pnpm_store, tool_homes

if TYPE_CHECKING:
    from pathlib import Path

RECIPES = ("check-dashes", "check-probe")
SCRIPTS = ("a", "b")
ITEMS = 4  # every recipe and test item of the copy
LEFT_OUT = r"tests/[^/]*\.sh|tests/gate/test_cpu\.py|tests/gate/kit/(.*/)?test_[^/]*\.py"
# The kit gate's own settings, venv and capture, never the copy's run's.
OUTER = (
    "GATE_NESTED",
    "GATE_RECIPES",
    "GATE_WORKERS",
    "GATE_RUN_DIR",
    "GATE_ITEM",
    "HERDR_SESSION",
    "VIRTUAL_ENV",
    "OCTO_FEATHER_QC_CLAIMS",
    "OCTO_FEATHER_QC_CAPTURE_DIR",
)
SLOT = """#!/usr/bin/env bash
echo "slot $*" >> "$PROBE"
[[ "$1" == hold ]] || exit 0
if [[ -n "${SLOT_GRANTED:-}" ]]; then
  echo "held: stand-in"
  cat >/dev/null
  echo "slot released" >> "$PROBE"
elif [[ " $* " == *" --if-granted "* ]]; then
  echo "later: stand-in"
else
  echo "free: stand-in"
fi
"""
ASK = f"slot hold --kind heavy --items {ITEMS}"
EARLY = f"{ASK} --if-granted"
DASH = "\u2014"


def kit_copy(s: Scratch) -> Path:
    k = s.root / "kit"
    k.mkdir()
    files = subprocess.run(
        ["git", "ls-files", "-z"],  # noqa: S607
        cwd=ROOT,
        capture_output=True,
        check=True,
    ).stdout.decode()
    kept = "\0".join(f for f in files.split("\0") if f and not re.fullmatch(LEFT_OUT, f))
    tar = subprocess.run(
        ["tar", "-cf", "-", "--null", "-T", "-"],  # noqa: S607
        cwd=ROOT,
        input=kept.encode(),
        capture_output=True,
        check=True,
    ).stdout
    subprocess.run(["tar", "-xf", "-", "-C", str(k)], input=tar, check=True)  # noqa: S607
    jf = k / "justfile"
    text = re.sub(
        r"^export GATE_RECIPES := .*$",
        f'export GATE_RECIPES := "{" ".join(RECIPES)}"',
        jf.read_text(),
        count=1,
        flags=re.MULTILINE,
    )
    jf.write_text(text + '\ncheck-probe:\n    @echo check-probe >> "$PROBE"\n')
    for n in SCRIPTS:
        e2e = "# gate: e2e\n" if n == "a" else ""
        (k / "tests" / f"{n}.sh").write_text(f'#!/usr/bin/env bash\n{e2e}echo {n} >> "$PROBE"\n')
        (k / "tests" / f"{n}.sh").chmod(0o755)
    (k / "scripts" / "octo-feather-slot").write_text(SLOT)
    # none of its recipes here needs a package: check-tests' install is cheap
    s.run([str(ROOT / "tests" / "lib" / "no-packages.py"), str(k)])
    s.git(k, "init", "-q", "-b", "main")
    s.git(k, "add", "-A")
    s.git(k, "commit", "-qm", "copy")
    return k


def gate_env(s: Scratch, probe: Path, **env: str) -> dict[str, str]:
    """The env a copy's gate runs in: S's but the kit gate's own, PROBE its log, ENV over it."""
    run_env = {k: v for k, v in s.env.items() if k not in OUTER}
    return (
        run_env
        | tool_homes()
        | {
            "npm_config_store_dir": pnpm_store(),
            "MISE_STATE_DIR": str(s.root / "user-mise"),
            "XDG_STATE_HOME": str(s.root / "state"),
            "GATE_WORKERS": "2",
            "PROBE": str(probe),
            "PYTEST_ADDOPTS": "--color=no",
            **env,
        }
    )


def gate(s: Scratch, k: Path, recipe: str, **env: str) -> tuple[Ran, list[str]]:
    """`just RECIPE` in K: its exit and output (stdout and stderr together), and PROBE's lines."""
    probe = s.root / "probe"
    probe.write_text("")
    p = subprocess.run(
        ["just", recipe],  # noqa: S607
        cwd=k,
        env=gate_env(s, probe, **env),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    return Ran(p.returncode, p.stdout, ""), probe.read_text().splitlines()


def trend(s: Scratch) -> list[dict[str, object]]:
    f = s.root / "state" / "octo-feather" / "check-runs.jsonl"
    return [json.loads(ln) for ln in f.read_text().splitlines()] if f.exists() else []


def red(s: Scratch, how: str) -> None:
    """HOW: fast, check, nested (`just check` under GATE_NESTED), or granted (`just check`, the
    lane holding its grant)."""
    (s.root / "user-mise").mkdir()
    k = kit_copy(s)
    (k / "red.txt").write_text(f"one {DASH} dash\n")
    s.git(k, "add", "red.txt")
    s.git(k, "commit", "-qm", "red")
    recipe = "fast" if how == "fast" else "check"
    env = {"GATE_NESTED": "1"} if how == "nested" else {}
    env |= {"SLOT_GRANTED": "1"} if how == "granted" else {}
    ran, probe = gate(s, k, recipe, **env)
    said = f"just {recipe} ({how}): exit {ran.rc}\nprobe: {probe}\n{ran.out}"
    assert ran.rc != 0, said
    assert "test_recipe[check-dashes]" in ran.out, said
    assert f"red.txt:1:one {DASH} dash" in ran.out, said
    assert "check-dashes: replace the em/en dashes" in ran.out, said
    assert not [ln for ln in probe if ln in SCRIPTS], f"a test item ran: {said}"
    asked = [ln for ln in probe if ln.startswith("slot ")]
    if how == "granted":
        assert probe[0] == EARLY, f"want the lane's slot taken first: {said}"
        assert asked == [EARLY, "slot released"], f"want it held, then released: {said}"
        assert "the heavy slot its lane held is released at the run's end" in ran.out, said
    elif how == "fast":
        assert asked == [], f"want no ask: the fast tier takes no slot: {said}"
        assert "heavy slot: not needed: fast tier, " in ran.out, said
    else:
        assert asked == [EARLY], f"want only the --if-granted ask: {said}"
    full = [t for t in trend(s) if t.get("tier") == "full"]
    assert not full, f"a full trend line: {full}\n{said}"


def green(s: Scratch) -> None:
    (s.root / "user-mise").mkdir()
    k = kit_copy(s)
    ran, probe = gate(s, k, "check")
    said = f"just check: exit {ran.rc}\nprobe: {probe}\n{ran.out}"
    assert ran.rc == 0, said
    want = [EARLY, "check-probe", ASK]
    assert probe[:3] == want, f"want the early ask (later), check-probe once, then one ask: {said}"
    assert sorted(probe[3:]) == list(SCRIPTS), f"want each test item once, after it: {said}"
    lines = trend(s)
    assert len(lines) == 1, f"want one trend line: {lines}\n{said}"
    assert lines[0]["tier"] == "full", f"want tier full: {lines[0]}"
    steps = lines[0]["steps"]
    assert isinstance(steps, list)
    names = sorted(str(st["name"]) for st in steps)  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
    want = sorted(
        [f"test_recipe[{r}]" for r in RECIPES] + [f"test_script[tests/{n}.sh]" for n in SCRIPTS]
    )
    assert names == want, f"trend steps {names}, want {want}"


if __name__ == "__main__":
    main(red, green)
