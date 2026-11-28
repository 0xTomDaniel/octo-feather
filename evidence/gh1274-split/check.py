#!/usr/bin/env python3
"""The split's checks (ticket #1333; design section 4), each by machine on the real tree. One command runs them all:

  uv run --locked --offline python evidence/gh1274-split/check.py [--base REV]

REV (default 67ce2d7b) is the commit holding the hub before the split. Prints one line per check, `ok` or `FAIL`
with what failed; exit 0 only when every check holds.

  source    every moved function is the hub's text with exactly the printed rewrites (rewrites.json); in post_merge.py,
            merge_ask.py and start_lane.py, where moved code is formatted, the same compared as ast (no positions)
  names     every global a moved function reads resolves in its new module to what it resolved to in the hub (probe.py,
            run on the hub at REV and on this tree); no moved function reads __file__, __doc__ or sys.argv outside
            the tables
  help      octo-feather-lane --help, no arguments (stderr, exit 64) and start -h byte-identical to the pin taken on
            REV before the move (pin/)
  lazy      the dispatcher imports only lane_cli and the standard library at its top; each command loads, of the
            command modules, only its own (a run per command, its modules read from sys.modules)
  launch    pm_unit_start, pm_unit_run and the --map-job branch launch scripts/octo-feather-lane (a run, the systemd
            and process calls recorded instead of made)
  baseline  per rule, as many ruff and basedpyright violations in the split files as in the hub at REV
  tests     git diff REV -- tests/ touches only tests/parity/
"""

from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import tables as T  # noqa: E402

ROOT = Path(subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True,
                           cwd=HERE).stdout.strip())
BASE = sys.argv[sys.argv.index("--base") + 1] if "--base" in sys.argv else "67ce2d7b"
META = json.loads((HERE / "rewrites.json").read_text(encoding="utf-8"))
UV = ["uv", "run", "--locked", "--offline", "--quiet"]


def git(*a: str) -> str:
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True, check=True).stdout


def item(src: str, name: str) -> tuple[ast.AST, list[str]]:
    """The def NAME in SRC and its lines, decorators and the comment lines right above it included."""
    lines = src.splitlines()
    prev = 0
    for n in ast.parse(src).body:
        first = min([n.lineno, *[d.lineno for d in getattr(n, "decorator_list", [])]])
        if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name == name:
            start = first
            for k in range(first - 1, prev, -1):
                s = lines[k - 1].strip()
                if s.startswith("#"):
                    start = k
                elif s:
                    break
            return n, lines[start - 1:n.end_lineno]
        prev = n.end_lineno or n.lineno
    raise KeyError(name)


def dump(node: ast.AST) -> str:
    return ast.dump(node, include_attributes=False)


def check_source() -> list[str]:
    bad = []
    rows: dict[str, list[dict[str, object]]] = {}
    for r in META["rows"]:
        rows.setdefault(str(r["function"]), []).append(r)
    for fn, mod in META["where"].items():
        origin = META["origin"][fn]
        old_src = git("show", f"{BASE}:scripts/{origin}")
        new_src = (ROOT / "scripts" / f"{mod}.py").read_text(encoding="utf-8")
        _, old = item(old_src, fn)
        new_node, new = item(new_src, fn)
        want = list(old)
        inserts: list[dict[str, object]] = []
        formatted = False
        for r in rows.get(fn, []):
            if r["class"] == "formatted":
                formatted = True
            elif int(r["at"]) == -1:   # type: ignore[call-overload]
                inserts.append(r)
            else:
                at = int(r["at"])   # type: ignore[call-overload]
                if want[at] != r["old"]:
                    bad.append(f"{fn}: the table's line {at + 1} is not the hub's")
                want[at] = str(r["new"][0])   # type: ignore[index]
        for r in inserts:
            after = int(r["after"])   # type: ignore[call-overload]
            indent = next((l[:len(l) - len(l.lstrip())] for l in want[after:] if l.strip()), "    ")
            want[after:after] = [indent + str(x) for x in r["new"]]   # type: ignore[union-attr]
        if formatted:
            text = "\n".join(want)
            got = ast.parse(re_indent(text)).body[0]
            if dump(got) != dump(new_node):
                bad.append(f"{fn} ({mod}.py): its ast is not the hub's with the printed rewrites")
        elif mod in T.EXISTING:
            bad.append(f"{fn}: moved into {mod}.py without the formatted line")
        elif want != new:
            bad.append(f"{fn} ({mod}.py): its text is not the hub's with the printed rewrites")
    n = len(META["where"])
    return [f"FAIL {b}" for b in bad] or [f"{n} moved defs: text (new modules) or ast (formatted) is the hub's with the printed rewrites"]


def re_indent(text: str) -> str:
    lines = text.splitlines()
    pad = len(lines[0]) - len(lines[0].lstrip())
    return "\n".join(l[pad:] for l in lines) + "\n"


def base_tree(tmp: Path) -> Path:
    tree = tmp / "base"
    tree.mkdir()
    arch = subprocess.run(["git", "archive", BASE, "scripts"], cwd=ROOT, capture_output=True, check=True).stdout
    subprocess.run(["tar", "-x", "-C", str(tree)], input=arch, check=True)
    return tree


def check_names(tmp: Path) -> list[str]:
    env = {**os.environ, "PYTHONHASHSEED": "0"}
    probe = str(HERE / "probe.py")
    b = subprocess.run([*UV, "python", probe, "base", str(base_tree(tmp))], cwd=ROOT, capture_output=True,
                       text=True, env=env, check=False)
    n = subprocess.run([*UV, "python", probe, "new", str(ROOT)], cwd=ROOT, capture_output=True, text=True, env=env,
                       check=False)
    if b.returncode or n.returncode:
        return [f"FAIL probe failed: {b.stderr[-800:]} {n.stderr[-800:]}"]
    old, new = json.loads(b.stdout), json.loads(n.stdout)
    bad = [f"{fn} reads __file__, __doc__ or sys.argv and is not in the tables" for fn in old["readers"]
           if fn not in ("lanes_dir",)]
    for fn, o in old["names"].items():
        g = new["names"].get(fn, {})
        for k in sorted(set(o) | set(g)):
            if o.get(k) != g.get(k):
                bad.append(f"{fn}: {k}: hub {o.get(k)} != new {g.get(k)}")
    total = sum(len(v) for v in old["names"].values())
    return [f"FAIL {b}" for b in bad] or [f"{total} global reads in {len(old['names'])} moved defs resolve to the same object as in the hub; "
                   "__file__ readers outside the tables: lanes_dir only (its directory, same dir)"]


def check_help() -> list[str]:
    pin, lane = HERE / "pin", str(ROOT / "scripts" / "octo-feather-lane")
    bad = []
    for name, args in (("help", ["--help"]), ("noarg", []), ("start-h", ["start", "-h"])):
        p = subprocess.run([lane, *args], capture_output=True, check=False)
        if p.stdout != (pin / f"{name}.out").read_bytes() or p.stderr != (pin / f"{name}.err").read_bytes():
            bad.append(f"{name}: output differs from the pin")
        if str(p.returncode) != (pin / f"{name}.rc").read_text().strip():
            bad.append(f"{name}: exit {p.returncode}")
    return [f"FAIL {b}" for b in bad] or ["--help, no arguments (stderr, exit 64) and start -h byte-identical to the pin"]


STD = set(sys.stdlib_module_names)
GROUPS = {"lane_ticketing", "lane_reporting", "lane_review", "lane_reflection", "pi_sessions", "ci_start", "post_merge",
          "merge_ask", "start_lane"}


def check_lazy() -> list[str]:
    bad = []
    disp = ast.parse((ROOT / "scripts" / "octo-feather-lane").read_text(encoding="utf-8"))
    for n in disp.body:
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            mods = [a.name for a in n.names] if isinstance(n, ast.Import) else [n.module or ""]
            for m in mods:
                if m.split(".")[0] not in STD and m != "lane_cli":
                    bad.append(f"dispatcher imports {m} at its top")
    code = r"""
import importlib.machinery as im, importlib.util as iu, json, sys
GROUPS = set(sys.argv[2].split(","))
l = im.SourceFileLoader("lane", sys.argv[1]); s = iu.spec_from_loader("lane", l); lane = iu.module_from_spec(s)
l.exec_module(lane)
at_load = sorted(GROUPS & set(sys.modules))
mod, fn = lane.COMMANDS[sys.argv[3]]
getattr(__import__(mod), fn)
print(json.dumps([at_load, sorted(GROUPS & set(sys.modules)), mod]))
"""
    lane, lib = str(ROOT / "scripts" / "octo-feather-lane"), []
    cmds = ast.literal_eval(next(n for n in disp.body if isinstance(n, ast.Assign)
                                 and getattr(n.targets[0], "id", "") == "COMMANDS").value)  # type: ignore[arg-type]
    for c in cmds:
        p = subprocess.run([*UV, "python", "-c", code, lane, ",".join(sorted(GROUPS)), c], cwd=ROOT / "scripts",
                           capture_output=True, text=True, check=False)
        if p.returncode:
            bad.append(f"{c}: {p.stderr[-300:]}")
            continue
        at_load, after, mod = json.loads(p.stdout)
        if at_load:
            bad.append(f"loading the dispatcher loads {at_load}")
        if set(after) - {mod, "merge_ask"}:
            bad.append(f"{c}: loads {after}, not only {mod}")
        elif mod != "merge_ask" and "merge_ask" in after:
            lib.append(c)
    run = ("import runpy, sys\nsys.path.insert(0, sys.argv[1].rsplit('/', 1)[0]); g = set(sys.argv[2].split(','))\n"
           "lane = sys.argv[1]; sys.argv = [lane, 'stale', 'x']\ntry: runpy.run_path(lane, run_name='__main__')\n"
           "finally: print('LOADED', sorted(g & set(sys.modules)), file=sys.stderr)")
    p = subprocess.run([*UV, "python", "-c", run, lane, ",".join(sorted(GROUPS))], cwd=ROOT, capture_output=True,
                       text=True, check=False)
    ran = next((ast.literal_eval(l[7:]) for l in p.stderr.splitlines() if l.startswith("LOADED ")), None)
    if ran != ["post_merge"]:
        bad.append(f"`octo-feather-lane stale x` loaded {ran}")
    return [f"FAIL {b}" for b in bad] or [f"dispatcher imports lane_cli and the stdlib only; each of {len(cmds)} commands loads only its "
                   "module, plus merge_ask.py as a library where its module imports it (design section 6, commit 4: "
                   f"{', '.join(lib)}); `stale x` run loads post_merge alone"]


def check_launch() -> list[str]:
    code = r"""
import os, sys
from pathlib import Path
import post_merge as pm
calls = []
pm.bounded = lambda run, limit: (calls.append(list(run)), ("success", "0"))[1]
pm.unit_end = lambda *a, **k: 0
pm.map_end = lambda *a, **k: 0
pm.transient = lambda unit, run, **k: (calls.append(list(run)), calls.append(list(k["hook"])), calls.append(list(k["fallback"])), "")[-1]
pm.manager = lambda: True
pm.top = lambda: Path("/tmp")
pm.post_merge_top = pm.top
pm.update = lambda *a, **k: None
pm.post_merge_map_end = pm.map_end
pm.post_merge_unit_end = pm.unit_end
pm.records = pm.post_merge_records = lambda lanes: Path("/tmp/records")
pm.lanes_dir = lambda: Path("/tmp/lanes")
pm.pm_unit_run(1, "a" * 40, "gh1", None)
pm.cmd_post_merge(["--map-job", "--unit-run"])
pm.pm_unit_start("gh1", 1, "a" * 40, None)
print("\n".join(c[0] for c in calls))
"""
    p = subprocess.run([*UV, "python", "-c", code], cwd=ROOT / "scripts", capture_output=True, text=True,
                       check=False)
    if p.returncode:
        return [f"FAIL launch run failed: {p.stderr[-500:]}"]
    want = str((ROOT / "scripts" / "octo-feather-lane").resolve())
    got = [l for l in p.stdout.splitlines() if l.startswith("/")]
    if len(got) != 5 or any(g != want for g in got):
        return [f"FAIL launched {got}, not {want}"]
    return [f"pm_unit_run, the --map-job branch and pm_unit_start (unit, stop hook, fallback) launch {want}"]


def ruff_counts(tree: Path, files: list[str]) -> Counter[str]:
    import tomllib
    cfg = tomllib.loads((tree / "pyproject.toml").read_text(encoding="utf-8"))
    cfg["tool"]["ruff"]["lint"].pop("extend-per-file-ignores", None)
    import tomlkit
    with tempfile.NamedTemporaryFile("w", suffix=".toml", delete=False, dir=tree) as f:
        f.write(tomlkit.dumps(cfg["tool"]["ruff"]))   # a --config file not named pyproject.toml is ruff.toml
    try:
        p = subprocess.run([*UV, "--project", str(ROOT), "ruff", "check", "--config", f.name, "--ignore-noqa",
                            "--output-format", "json", *files], cwd=tree, capture_output=True, text=True, check=False)
    finally:
        os.unlink(f.name)
    if p.returncode not in (0, 1):
        raise SystemExit(f"ruff failed in {tree}: {p.stderr[-500:]}")
    return Counter(v["code"] for v in json.loads(p.stdout or "[]"))


def pyright_counts(baseline: dict[str, object], files: list[str]) -> Counter[str]:
    c: Counter[str] = Counter()
    for f in files:
        for e in baseline["files"].get(f"./{f}", []):   # type: ignore[attr-defined]
            c[e["code"]] += 1
    return c


def check_baseline(tmp: Path) -> list[str]:
    old_files = ["scripts/octo-feather-lane", *[f"scripts/{m}.py" for m in T.EXISTING]]
    new_files = [*old_files, *[f"scripts/{m}.py" for m in T.NEW]]
    tree = tmp / "rbase"
    tree.mkdir()
    arch = subprocess.run(["git", "archive", BASE, "scripts", "pyproject.toml"], cwd=ROOT, capture_output=True,
                          check=True).stdout
    subprocess.run(["tar", "-x", "-C", str(tree)], input=arch, check=True)
    r_old, r_new = ruff_counts(tree, old_files), ruff_counts(ROOT, new_files)
    b_old = json.loads(git("show", f"{BASE}:.basedpyright/baseline.json"))
    b_new = json.loads((ROOT / ".basedpyright" / "baseline.json").read_text(encoding="utf-8"))
    p_old, p_new = pyright_counts(b_old, old_files), pyright_counts(b_new, new_files)
    out, bad = [], []
    calls = sum(len(v) for v in META["inserts"].values())   # the call-site imports the design puts where the call is
    for tool, o, n in (("ruff", r_old, r_new), ("basedpyright", p_old, p_new)):
        diff = {k: (o[k], n[k]) for k in sorted(set(o) | set(n)) if o[k] != n[k]}
        out.append(f"{tool}: hub {sum(o.values())} -> split {sum(n.values())}"
                   + (f"; per rule: {', '.join(f'{k} {a}->{b}' for k, (a, b) in diff.items())}" if diff else ", per rule equal"))
        for k, (a, b) in diff.items():
            if b > a and not (tool == "ruff" and k == "PLC0415" and b - a == calls):
                bad.append(f"{tool} {k} rises {a} -> {b}" + (f" (call-site imports: {calls})" if k == "PLC0415" else ""))
    out.append(f"PLC0415 may rise by the {calls} call-site imports only; no other rule may rise")
    others_old = {k: v for k, v in b_old["files"].items() if k.removeprefix("./") not in new_files}
    others_new = {k: v for k, v in b_new["files"].items() if k.removeprefix("./") not in new_files}
    if others_old != others_new:
        bad.append("basedpyright baseline changed outside the split files")
    return [*out, *[f"FAIL {b}" for b in bad]]


def check_tests() -> list[str]:
    files = [l for l in git("diff", BASE, "--name-only", "--", "tests/").splitlines() if l]
    off = [f for f in files if not f.startswith("tests/parity/")]
    return [f"FAIL tests outside tests/parity changed: {off}"] if off else [f"{len(files)} files under tests/, all tests/parity/"]


def main() -> int:
    failed = 0
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        for name, fn in (("source", check_source), ("names", lambda: check_names(tmp)), ("help", check_help),
                         ("lazy", check_lazy), ("launch", check_launch), ("baseline", lambda: check_baseline(tmp)),
                         ("tests", check_tests)):
            lines = fn()
            ok = not any(l.startswith("FAIL") for l in lines)
            failed += not ok
            for l in lines:
                print(f"{name}: {'ok' if ok else 'FAIL'}: {l.removeprefix('FAIL ')}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
