#!/usr/bin/env python3
"""launch.py: what one launch of scripts/octo-feather-lane costs before and after the split, and how often the
lane's heaviest tests launch it (#1334, director's addition). Python stdlib only.

  launch.py launches MAIN_TREE SPLIT_TREE [--n N] [--only NAME]
      N rounds (default 20); each round runs every command once on each tree, the tree order alternating by round
      so box load falls on both alike, and `python3 -c pass` once as the interpreter floor. Each launch: CPU
      (ru_utime + ru_stime of the child, os.wait4) and wall (perf_counter around fork to reap). Isolation: an empty
      cwd, a scratch HOME and XDG_STATE_HOME, PATH = a dir whose gh and herdr refuse offline, then /usr/bin:/bin
      (the script's `#!/usr/bin/env python3` finds the system python3, the same for both trees). Prints a
      markdown table, median and p90 (nearest rank) per command and tree, and the load averages.
  launch.py tests MAIN_TREE SPLIT_TREE --runs R ID...
      Per tree: one `just test ID...` under `strace -f -e trace=execve` counting, per test file, the launches of
      octo-feather-lane (an execve of a path ending in /octo-feather-lane, or of an interpreter whose next argument
      is one), each attributed to its test file by the GATE_ITEM in that execve's environment; then R runs of `just test ID...`
      with --junitxml, each test file's CPU the sum of its items' cpu_s (the gate's own per-item CPU,
      tests/gate/conftest.py), and the whole run's CPU (os.wait4 on just, children included) and wall.
"""

from __future__ import annotations

import argparse
import os
import re
import statistics
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from pathlib import Path

COMMANDS: list[tuple[str, list[str]]] = [
    ("--help", ["--help"]),
    ("no argument", []),
    ("tickets 1 (no spec dir: refused after parsing)", ["tickets", "1"]),
    ("seam 1 (usage refusal)", ["seam", "1"]),
    ("report (offline: scratch state, gh refusing)", ["report"]),
    ("merge-ask abc (refusal)", ["merge-ask", "abc"]),
]
FLOOR = "python3 -c pass (floor)"


def q(xs: list[float], p: float) -> float:
    xs = sorted(xs)
    return xs[min(len(xs) - 1, max(0, round(p * (len(xs) - 1))))]


def scratch() -> tuple[dict[str, str], Path]:
    d = Path(tempfile.mkdtemp(prefix="launch-"))
    (d / "bin").mkdir()
    for tool in ("gh", "herdr"):
        f = d / "bin" / tool
        f.write_text('#!/bin/sh\necho "offline (launch harness)" >&2; exit 1\n')
        f.chmod(0o755)
    for sub in ("home", "state", "cwd"):
        (d / sub).mkdir()
    env = {"HOME": str(d / "home"), "XDG_STATE_HOME": str(d / "state"), "PATH": f"{d / 'bin'}:/usr/bin:/bin",
           "LANG": "C.UTF-8"}
    return env, d / "cwd"


def once(argv: list[str], env: dict[str, str], cwd: Path) -> tuple[float, float, int]:
    """(CPU seconds of the child, wall seconds, exit status) of one launch."""
    t = time.perf_counter()
    p = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
    _pid, status, ru = os.wait4(p.pid, 0)
    wall = time.perf_counter() - t
    p.returncode = os.waitstatus_to_exitcode(status)
    return ru.ru_utime + ru.ru_stime, wall, p.returncode


def launches(main_tree: Path, split_tree: Path, n: int, only: str | None) -> None:
    env, cwd = scratch()
    trees = {"main": main_tree.resolve(), "split": split_tree.resolve()}
    heads = {k: subprocess.run(["git", "-C", str(v), "rev-parse", "--short=12", "HEAD"], capture_output=True,
                               text=True, check=True).stdout.strip() for k, v in trees.items()}
    cmds = [c for c in COMMANDS if only is None or c[0] == only]
    cpu: dict[tuple[str, str], list[float]] = {}
    wall: dict[tuple[str, str], list[float]] = {}
    codes: dict[tuple[str, str], set[int]] = {}
    loads = [os.getloadavg()]
    for r in range(n):
        order = ["main", "split"] if r % 2 == 0 else ["split", "main"]
        for name, args in cmds:
            for tree in order:
                c, w, rc = once([str(trees[tree] / "scripts/octo-feather-lane"), *args], env, cwd)
                cpu.setdefault((name, tree), []).append(c)
                wall.setdefault((name, tree), []).append(w)
                codes.setdefault((name, tree), set()).add(rc)
        c, w, rc = once(["python3", "-c", "pass"], env, cwd)
        cpu.setdefault((FLOOR, "-"), []).append(c)
        wall.setdefault((FLOOR, "-"), []).append(w)
        codes.setdefault((FLOOR, "-"), set()).add(rc)
        loads.append(os.getloadavg())
    py = subprocess.run(["python3", "--version"], env=env, capture_output=True, text=True, check=False).stdout.strip()
    print(f"Trees: main {heads['main']} ({trees['main']}), split {heads['split']} ({trees['split']}). {n} launches "
          f"per command and tree, interleaved (tree order alternating by round). Interpreter: {py} (/usr/bin/env).")
    l1 = [x[0] for x in loads]
    print(f"Box load average (1 min) over the run: start {l1[0]:.1f}, median {statistics.median(l1):.1f}, "
          f"max {max(l1):.1f}, end {l1[-1]:.1f}.\n")
    print("| command | tree | exit | CPU median ms | CPU p90 ms | wall median ms | wall p90 ms |")
    print("|---|---|---|---|---|---|---|")
    for name, _a in [*cmds, (FLOOR, [])]:
        for tree in (["-"] if name == FLOOR else ["main", "split"]):
            cs, ws = cpu[(name, tree)], wall[(name, tree)]
            print(f"| {name} | {tree} | {','.join(map(str, sorted(codes[(name, tree)])))} | "
                  f"{1000 * statistics.median(cs):.0f} | {1000 * q(cs, .9):.0f} | "
                  f"{1000 * statistics.median(ws):.0f} | {1000 * q(ws, .9):.0f} |")


LANE = re.compile(r'execve\("([^"]*)", \[(.*?)\]')
ITEM = re.compile(r'"GATE_ITEM=([^"]*)"')


def count_launches(tree: Path, ids: list[str]) -> tuple[dict[str, int], int]:
    """Per test file, the launches of octo-feather-lane in one `just test IDS` under strace (-v: each execve's
    environment, whose GATE_ITEM names the gate item that started it); and just's exit status."""
    with tempfile.TemporaryDirectory(prefix="launch-strace-") as d:
        out = Path(d, "trace")
        p = subprocess.run(["strace", "-f", "-qq", "-v", "-s", "400", "-e", "trace=execve", "-e", "signal=none",
                            "-o", str(out), "just", "test", *ids], cwd=tree, capture_output=True, text=True,
                           stdin=subprocess.DEVNULL, check=False)
        per: dict[str, int] = {}
        for ln in out.read_text(errors="replace").splitlines():
            m = LANE.search(ln)
            if not m or " = -1 " in ln:
                continue
            path, argv = m.group(1), re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(2))
            if not (path.endswith("/octo-feather-lane") or (len(argv) > 1 and "python" in Path(path).name
                                                           and argv[1].endswith("/octo-feather-lane"))):
                continue
            it = ITEM.search(ln)
            item = it.group(1) if it else "unattributed"
            f = item.split("::")[0]
            per[f] = per.get(f, 0) + 1
        return per, p.returncode


def junit_cpu(xml: Path) -> dict[str, float]:
    out: dict[str, float] = {}
    for case in ET.parse(xml).iter("testcase"):  # noqa: S314  # our own pytest's report
        props = {p.get("name"): p.get("value") for p in case.iter("property")}
        if "cpu_s" not in props:
            continue
        cls, name = case.get("classname", ""), case.get("name", "")
        f = ("tests/" + name.removeprefix("test_script[tests/").removesuffix("]")) if name.startswith(
            "test_script[") else cls.replace(".", "/") + ".py"
        out[f] = out.get(f, 0.0) + float(props["cpu_s"] or 0)
    return out


def tests(main_tree: Path, split_tree: Path, runs: int, ids: list[str]) -> None:
    trees = {"main": main_tree.resolve(), "split": split_tree.resolve()}
    for tree, root in trees.items():
        per, rc = count_launches(root, ids)
        print(f"{tree}: launches of octo-feather-lane under strace (just test exit {rc}): {per}")
    print(f"Box load average (1 min) before the timed runs: {os.getloadavg()[0]:.1f}")
    rows: dict[str, dict[str, list[float]]] = {}
    totals: dict[str, list[tuple[float, float]]] = {"main": [], "split": []}
    for r in range(runs):
        for tree in (["main", "split"] if r % 2 == 0 else ["split", "main"]):
            with tempfile.TemporaryDirectory(prefix="launch-junit-") as d:
                xml = Path(d, "j.xml")
                t = time.perf_counter()
                p = subprocess.Popen(["just", "test", f"--junitxml={xml}", *ids], cwd=trees[tree],
                                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                _pid, status, ru = os.wait4(p.pid, 0)
                totals[tree].append((ru.ru_utime + ru.ru_stime, time.perf_counter() - t))
                sys.stderr.write(f"launch: {tree} run {r + 1}: exit {os.waitstatus_to_exitcode(status)}\n")
                got: dict[str, float] = junit_cpu(xml) if xml.is_file() else {}
                for f, c in got.items():
                    rows.setdefault(f, {}).setdefault(tree, []).append(c)
    print("\n| test file | main CPU s (runs) | split CPU s (runs) |\n|---|---|---|")
    for f in sorted(rows):
        m, s = rows[f].get("main", []), rows[f].get("split", [])
        print(f"| {f} | {' '.join(f'{x:.1f}' for x in m)} | {' '.join(f'{x:.1f}' for x in s)} |")
    print(f"\nBox load average (1 min) after the timed runs: {os.getloadavg()[0]:.1f}")
    for tree, xs in totals.items():
        print(f"\n{tree}: whole `just test` run CPU s {' '.join(f'{c:.1f}' for c, _w in xs)}; wall s "
              f"{' '.join(f'{w:.0f}' for _c, w in xs)} (wall includes waiting for a fast-run turn)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("launches")
    s.add_argument("main_tree", type=Path)
    s.add_argument("split_tree", type=Path)
    s.add_argument("--n", type=int, default=20)
    s.add_argument("--only")
    s = sub.add_parser("tests")
    s.add_argument("main_tree", type=Path)
    s.add_argument("split_tree", type=Path)
    s.add_argument("--runs", type=int, default=3)
    s.add_argument("ids", nargs="+")
    a = ap.parse_args()
    if a.cmd == "launches":
        launches(a.main_tree, a.split_tree, a.n, a.only)
    else:
        tests(a.main_tree, a.split_tree, a.runs, a.ids)


if __name__ == "__main__":
    main()
