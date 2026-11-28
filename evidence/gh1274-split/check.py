#!/usr/bin/env python3
"""The split's checks (ticket #1333; design section 4), each by machine on the real tree. One command runs them all:

  uv run --locked --offline python evidence/gh1274-split/check.py [--base REV]

REV (default: the merge base of HEAD with origin/main) is the commit holding the hub before the split. Prints one line per check, `ok` or `FAIL`
with what failed; exit 0 only when every check holds.

  source    every moved function is the hub's text with exactly the printed rewrites (rewrites.json); in post_merge.py,
            merge_ask.py and start_lane.py, where moved code is formatted, the same compared as ast (no positions)
  names     every global a moved function reads resolves in its new module to what it resolved to in the hub (probe.py,
            run on the hub at REV and on this tree); no moved function reads __file__, __doc__ or sys.argv outside
            the tables
  help      octo-feather-lane --help, no arguments (stderr, exit 64) and start -h byte-identical to the pin taken on
            REV before the move (pin/)
  lazy      the dispatcher's import rule: scripts/check-lane-dispatch (check_rules.py check_lane_dispatch), run; each
            command loads, of the command modules, only its own (a run per command, its modules read from
            sys.modules), merge_ask.py included once the helpers moved (#1335)
  launch    pm_unit_start, pm_unit_run and the --map-job branch launch scripts/octo-feather-lane (a run, the systemd
            and process calls recorded instead of made)
  baseline  per rule, as many ruff and basedpyright violations in the split files as in the hub at REV
  tests     the split's own commits (#1333, #1335) touch, under tests/, only tests/parity/
  helpers   ticket #1335, against the split of REV before the helpers step (split.py --no-helpers, a scratch copy):
            each moved statement's text is merge_ask.py's, unchanged; every other changed line of the files the step
            rewrote is a printed rewrite (rewrites.json, helpers.lines) or in a top import block; each name a moved
            statement reads, and each name the command groups read from merge_ask.py, resolves to the same object
            (probe.py helpers-base, helpers-new); no command group imports merge_ask.py, and merge_ask.py imports
            no lane_reporting.py
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
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import tables as T  # noqa: E402

ROOT = Path(subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True,
                           cwd=HERE).stdout.strip())
# The hub before the split: --base, else the merge base with origin/main (the split reruns on each new main, #1336).
BASE = (sys.argv[sys.argv.index("--base") + 1] if "--base" in sys.argv else
        subprocess.run(["git", "merge-base", "HEAD", "origin/main"], cwd=ROOT, capture_output=True, text=True,
                       check=True).stdout.strip())
META = json.loads((HERE / "rewrites.json").read_text(encoding="utf-8"))
HELPERS: dict[str, Any] = META.get("helpers", {})
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
        pairs = HELPERS.get("lines", {}).get(f"{mod}.py", [])
        one = {o.rstrip("\n"): n.rstrip("\n").split("\n") for o, n in pairs if o.count("\n") <= 1}
        one |= {o: [] for o0, n in pairs if not n for o in o0.splitlines() if o.strip()}   # a line cut   # the helpers step's printed line rewrites (#1335); in formatted code, by
        code = {o.split("#")[0].strip(): n for o, n in one.items()}   # their code alone (the hub's line, unformatted)
        want = [x for l in want for x in one.get(l, code.get(l.split("#")[0].strip(), [l]) if formatted else [l])]
        if formatted:   # the hub's lines join what the formatter split: a rewrite inside one, as a fragment
            for o, n in one.items():
                if len(n) == 1 and o.split("#")[0].strip():
                    want = [l.replace(o.split("#")[0].strip(), n[0].split("#")[0].strip()) for l in want]
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
    bad = [f"{fn} reads __file__, __doc__ or sys.argv and is not in the tables" for fn in old["readers"]]
    # #1335: a moved def's read of the module merge_ask became its read of the shared modules its uses moved to (each
    # use's object: check helpers); the TREND edits (tables.py TREND_EDITS) add the names their new side reads
    trend_new = {T.TREND_LINE.split()[0], "gate_time"}   # TREND, read bare, and its module
    for fn, o in old["names"].items():
        g = new["names"].get(fn, {})
        if HELPERS and o.get("merge_ask") == ["module", "merge_ask"]:
            shared = {k for k in g if k in T.SHARED and g[k] == ["module", k]}
            if shared or "merge_ask" in g:
                o, g = {k: v for k, v in o.items() if k != "merge_ask"}, {k: v for k, v in g.items()
                                                                          if k not in (shared | {"merge_ask"})}
        for k in sorted(set(o) | set(g)):
            if o.get(k) != g.get(k) and not (HELPERS and k not in o and k in trend_new):
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


GROUPS = {"lane_ticketing", "lane_reporting", "lane_review", "lane_reflection", "pi_sessions", "ci_start", "post_merge",
          "merge_ask", "start_lane"}


def check_lazy() -> list[str]:
    bad = []
    disp = ast.parse((ROOT / "scripts" / "octo-feather-lane").read_text(encoding="utf-8"))
    rule = subprocess.run([str(ROOT / "scripts" / "check-lane-dispatch")], capture_output=True, text=True, check=False)
    if rule.returncode:
        bad.append(f"check-lane-dispatch: exit {rule.returncode}: {(rule.stdout + rule.stderr).strip()}")
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
        if set(after) - {mod, *([] if HELPERS else ["merge_ask"])}:
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
    lib_says = (f"plus merge_ask.py as a library where its module imports it (design section 6, commit 4: {', '.join(lib)})"
                if lib else "merge_ask.py by merge-ask alone (#1335)")
    return [f"FAIL {b}" for b in bad] or [f"{rule.stdout.strip()}; each of {len(cmds)} commands loads only its module, "
                                          f"{lib_says}; `stale x` run loads post_merge alone"]


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
    """Every ruff violation in FILES, noqa and the baseline table ignored: pyproject.toml minus that table, copied
    as pyproject.toml (requires-python sets the target version), as octo-feather-lint reads it."""
    import tomlkit
    doc = tomlkit.parse((tree / "pyproject.toml").read_text(encoding="utf-8"))
    del doc["tool"]["ruff"]["lint"]["extend-per-file-ignores"]  # type: ignore[union-attr,index]
    with tempfile.TemporaryDirectory() as t:
        cfg = Path(t) / "pyproject.toml"
        cfg.write_text(tomlkit.dumps(doc), encoding="utf-8")
        p = subprocess.run([*UV, "--project", str(ROOT), "ruff", "check", "--config", str(cfg), "--ignore-noqa",
                            "--output-format", "json", *files], cwd=tree, capture_output=True, text=True, check=False)
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
    new_files = [*old_files, *[f"scripts/{m}.py" for m in (*T.NEW, *(T.SHARED if HELPERS else ()))]]
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
    calls = sum(1 for v in META["inserts"].values() for l in v if l.startswith(("import ", "from ")))   # the call-site imports the design puts where the call is
    for tool, o, n in (("ruff", r_old, r_new), ("basedpyright", p_old, p_new)):
        diff = {k: (o[k], n[k]) for k in sorted(set(o) | set(n)) if o[k] != n[k]}
        out.append(f"{tool}: hub {sum(o.values())} -> split {sum(n.values())}"
                   + (f"; per rule: {', '.join(f'{k} {a}->{b}' for k, (a, b) in diff.items())}" if diff else ", per rule equal"))
        for k, (a, b) in diff.items():
            if b > a and not (tool == "ruff" and k == "PLC0415" and b - a <= calls):
                bad.append(f"{tool} {k} rises {a} -> {b}" + (f" (call-site imports: {calls})" if k == "PLC0415" else ""))
    out.append(f"PLC0415 may rise by the {calls} call-site imports only; no other rule may rise")
    others_old = {k: v for k, v in b_old["files"].items() if k.removeprefix("./") not in new_files}
    others_new = {k: v for k, v in b_new["files"].items() if k.removeprefix("./") not in new_files}
    if others_old != others_new:
        bad.append("basedpyright baseline changed outside the split files")
    return [*out, *[f"FAIL {b}" for b in bad]]


def check_tests() -> list[str]:
    files = sorted({l for l in git("log", "--no-merges", "--format=", "--name-only", "-E", "--grep", r"\(#13(33|35)[,)]",
                                   f"{BASE}..HEAD", "--", "tests/").splitlines() if l})   # the split's own commits
    off = [f for f in files if not f.startswith("tests/parity/")]
    return [f"FAIL tests outside tests/parity changed: {off}"] if off else [
        f"{len(files)} files under tests/ in the split's commits (#1333, #1335), all tests/parity/"]


def check_helpers(tmp: Path) -> list[str]:  # noqa: C901
    """Ticket #1335's step against the split of BASE before it (see the module docstring, helpers)."""
    from split import tops   # the step's own statement reader: a statement and the comment lines right above it
    if not HELPERS:
        return ["FAIL rewrites.json has no helpers rows: the step has not run"]
    pre = tmp / "pre"
    pre.mkdir()
    arch = subprocess.run(["git", "archive", BASE, "scripts", "pyproject.toml", "justfile"], cwd=ROOT,
                          capture_output=True, check=True).stdout
    subprocess.run(["tar", "-x", "-C", str(pre)], input=arch, check=True)
    p = subprocess.run([*UV, "python", str(HERE / "split.py"), "--tree", str(pre), "--no-baselines", "--no-helpers",
                        "--meta", str(tmp / "pre.json")], cwd=ROOT, capture_output=True, text=True, check=False)
    if p.returncode:
        return [f"FAIL split.py --no-helpers on {BASE}: {p.stderr[-500:]}"]
    bad: list[str] = []
    where: dict[str, str] = HELPERS["where"]
    ma_pre = (pre / "scripts" / "merge_ask.py").read_text(encoding="utf-8")
    pre_tops = tops(ma_pre)
    moved_lines: set[str] = set()
    pre_lines = ma_pre.splitlines()
    for name, home in sorted(where.items()):
        t = next(t for t in pre_tops if name in t.names)
        text = pre_lines[t.start - 1:t.end]
        moved_lines |= set(text)
        if t.header:
            moved_lines |= set(pre_lines[t.header[0] - 1:t.header[1]])
        new_src = (ROOT / "scripts" / f"{home}.py").read_text(encoding="utf-8")
        u = next((u for u in tops(new_src) if name in u.names), None)
        if u is None or new_src.splitlines()[u.start - 1:u.end] != text:
            bad.append(f"{name}: not merge_ask.py's text in {home}.py")
    # every other changed line: a printed rewrite, or a top import block's
    lines: dict[str, list[list[str]]] = HELPERS["lines"]

    def import_block(src: str) -> set[str]:
        body = ast.parse(src).body
        imps = [n for n in body if isinstance(n, (ast.Import, ast.ImportFrom))]
        if not imps:
            return set()
        ls = src.splitlines()
        return set(ls[imps[0].lineno - 1:max(n.end_lineno or n.lineno for n in imps if n.lineno < 400)])
    import difflib
    for f in HELPERS["rewritten"]:
        old, new = (pre / "scripts" / f).read_text(encoding="utf-8"), (ROOT / "scripts" / f).read_text(encoding="utf-8")
        olds = {l for o, _ in lines.get(f, []) for l in o.splitlines()} | import_block(old)
        news = {l for _, n in lines.get(f, []) for l in n.splitlines()} | import_block(new)
        if f == "merge_ask.py":
            olds |= moved_lines
        for d in difflib.ndiff(old.splitlines(), new.splitlines()):
            if d[:2] == "- " and d[2:].strip() and d[2:] not in olds:
                bad.append(f"{f}: line dropped, not printed: {d[2:].strip()[:80]}")
            elif d[:2] == "+ " and d[2:].strip() and d[2:] not in news:
                bad.append(f"{f}: line added, not printed: {d[2:].strip()[:80]}")
    for m in T.SHARED:
        src = (ROOT / "scripts" / f"{m}.py").read_text(encoding="utf-8")
        tree = ast.parse(src)
        own = {*import_block(src), T.TREND_LINE, "#!/usr/bin/env python3"}
        for n in tree.body[:2]:   # the docstring and __all__
            own |= set(src.splitlines()[n.lineno - 1:n.end_lineno])
        own |= {l for n in tree.body if isinstance(n, ast.If) for l in src.splitlines()[n.lineno - 1:n.end_lineno]}
        if extra := [l for l in src.splitlines() if l.strip() and l not in own and l not in moved_lines]:
            bad.append(f"{m}.py: lines neither moved nor its header: {extra[:3]}")
    # names
    env = {**os.environ, "PYTHONHASHSEED": "0"}
    probe = str(HERE / "probe.py")
    b = subprocess.run([*UV, "python", probe, "helpers-base", str(pre)], cwd=ROOT, capture_output=True, text=True,
                       env=env, check=False)
    n = subprocess.run([*UV, "python", probe, "helpers-new", str(ROOT)], cwd=ROOT, capture_output=True, text=True,
                       env=env, check=False)
    if b.returncode or n.returncode:
        return [f"FAIL probe failed: {b.stderr[-800:]} {n.stderr[-800:]}"]
    old_n, new_n = json.loads(b.stdout)["names"], json.loads(n.stdout)["names"]
    total = 0
    for k in sorted(set(old_n) | set(new_n)):
        o, g = old_n.get(k, {}), new_n.get(k, {})
        for x in sorted(set(o) | set(g)):
            total += 1
            if o.get(x) != g.get(x):
                bad.append(f"{k}: {x}: before {o.get(x)} != after {g.get(x)}")
    # who imports merge_ask
    for g in T.HELPER_GROUPS:
        tree = ast.parse((ROOT / "scripts" / f"{g}.py").read_text(encoding="utf-8"))
        if any((isinstance(x, ast.ImportFrom) and x.module == "merge_ask")
               or (isinstance(x, ast.Import) and any(a.name == "merge_ask" for a in x.names)) for x in ast.walk(tree)):
            bad.append(f"{g}.py imports merge_ask")
    tree = ast.parse((ROOT / "scripts" / "merge_ask.py").read_text(encoding="utf-8"))
    if any((isinstance(x, ast.ImportFrom) and x.module == "lane_reporting")
           or (isinstance(x, ast.Import) and any(a.name == "lane_reporting" for a in x.names)) for x in ast.walk(tree)):
        bad.append("merge_ask.py imports lane_reporting")
    return [f"FAIL {x}" for x in bad] or [
        f"{len(where)} moved statements, merge_ask.py's text unchanged; every other changed line of "
        f"{', '.join(HELPERS['rewritten'])} printed or in a top import block; {total} names resolve to the same object "
        f"before and after; {', '.join(T.HELPER_GROUPS)} import no merge_ask; merge_ask.py imports no lane_reporting"]


def main() -> int:
    failed = 0
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        for name, fn in (("source", check_source), ("names", lambda: check_names(tmp)), ("help", check_help),
                         ("lazy", check_lazy), ("launch", check_launch), ("baseline", lambda: check_baseline(tmp)),
                         ("tests", check_tests), ("helpers", lambda: check_helpers(tmp))):
            lines = fn()
            ok = not any(l.startswith("FAIL") for l in lines)
            failed += not ok
            for l in lines:
                print(f"{name}: {'ok' if ok else 'FAIL'}: {l.removeprefix('FAIL ')}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
