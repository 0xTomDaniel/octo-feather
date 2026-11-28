#!/usr/bin/env python3
"""why.py: why covers from coverage (b) make more criteria stale than declared covers (a) (#1334, director's
addition). Run under the kit's uv venv: `uv run --locked --offline --no-sync python3 evidence/gh1274-split/covers/why.py
...`; covers.py beside it owns the covers rule (computed) and the stale rule (hit).

  why.py probe TREE MEASURE OUT [--main REF]
      For each file (b) adds over (a), up to PROBES criteria that gained it: run that criterion's proof (its first
      tagged item through pytest, or its demo command, as covers.py runs them) in TREE under the fast map's coverage
      configuration, keeping line data, and record per (criterion, file) whether any line of work in that file ran
      (called: a function or method body, or a script's top-level code; work_lines) or only its loading (imports,
      defs, classes, assignments, import guards, the docstring: loaded only). OUT: JSON.
  why.py report MEASURE PROBE --prs FILE --main REF
      Markdown: per file, the criteria (b) adds it to, the criteria it drops from, the extra stale (PR, criterion)
      pairs it brings over the 60 PRs, and the probe's verdict: a real dependency the declared covers missed (its
      functions run in the proof), or an incidental load (imported, nothing in it called); then the full list.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path
from typing import Any, cast

sys.path.insert(0, str(Path(__file__).resolve().parent))
import covers  # noqa: E402
import gh_records  # noqa: E402

PROBES = 3


DEFINING = (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Assign, ast.AnnAssign,
            ast.Try)


def work_lines(src: str) -> set[int]:
    """The lines of SRC whose running is work, not loading: any line inside a function or method body, and any
    top-level statement but an import, a def or class, an assignment, a try (an import guard) or a bare constant
    (the docstring). A script with top-level code (no functions) counts that code; a module only imported counts
    nothing."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return set()
    out: set[int] = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.body:
            out |= set(range(n.body[0].lineno, (n.end_lineno or n.body[0].lineno) + 1))
    for n in tree.body:
        constant = isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)
        if not isinstance(n, DEFINING) and not constant:
            out |= set(range(n.lineno, (n.end_lineno or n.lineno) + 1))
    return out


def added(m: covers.Measure, qc: dict[str, Any], b: set[str], seen: covers.Seen) -> dict[str, tuple[set[str], set[str]]]:
    """criterion -> (files (b) adds over (a), declared files (b) drops), built criteria only."""
    out: dict[str, tuple[set[str], set[str]]] = {}
    for c, (cov, _how) in covers.computed(m, qc, seen).items():
        if c in b:
            d = {str(x) for x in qc[c]["covers"]}
            out[c] = (set(cov) - d, d - set(cov))
    return out


def lines_by_file(g: Any, tracked: Any, d: Path) -> dict[str, set[int]]:
    import coverage  # noqa: PLC0415  # the kit venv's

    out: dict[str, set[int]] = {}
    for f in list(d.glob("cov*")) if d.is_dir() else list[Path]():
        cd = coverage.CoverageData(basename=str(f))
        cd.read()
        for mf in cd.measured_files():
            for t in tracked.source(mf):
                out.setdefault(t, set()).update(cd.lines(mf) or [])
    return out


def probe(tree: Path, measure: Path, out: Path, ref: str) -> None:
    tree = tree.resolve()
    os.chdir(tree)
    m = cast("covers.Measure", json.loads(measure.read_text()))
    qc = tomllib.loads(covers.git(tree, "show", f"{ref}:qc.toml"))["demo"]
    adds = added(m, qc, covers.built(tree, ref), covers.Seen(tree, ref))
    g = covers.gate(tree)
    tracked = g.Tracked()
    want: dict[str, list[str]] = {}
    for c, (plus, _minus) in sorted(adds.items()):
        for f in sorted(plus):
            if len(want.setdefault(f, [])) < PROBES:
                want[f].append(c)
    proof: dict[str, str] = {}   # criterion -> its proof: a node id, or "demo:<command>"
    for c in {c for cs in want.values() for c in cs}:
        items = m["tags"].get(c)
        proof[c] = items[0] if items else f"demo:{qc[c]['command']}"
    runs: dict[str, dict[str, set[int]]] = {}
    with tempfile.TemporaryDirectory(prefix="why-probe-") as d:
        data = Path(d, "data")
        nodes = sorted({p for p in proof.values() if not p.startswith("demo:")})
        env = covers.cov_env(tree, data) | {"GATE_WORKERS": "3"}
        r = subprocess.run(["nice", "-n", "19", "just", "check-tests", "-p", "no:cpu-shown",
                            *[covers.node_of(i) for i in nodes]], cwd=tree, env=env, capture_output=True, text=True,
                           stdin=subprocess.DEVNULL, check=False)
        sys.stderr.write(f"why: {len(nodes)} probe items: exit {r.returncode}\n{r.stdout[-400:]}")
        for i in nodes:
            runs[i] = lines_by_file(g, tracked, data / i)
        for k, p in enumerate(sorted({p for p in proof.values() if p.startswith("demo:")})):
            dd = Path(d, f"demo{k}")
            env = covers.cov_env(tree, dd) | {"GATE_ITEM": "demo", "QC_REPO": str(tree),
                                               "VERIFY_OCTO_FEATHER_RUN_DIR": f"{dd}/run",
                                               "VERIFY_OCTO_FEATHER_EVIDENCE_DIR": f"{dd}/evidence"}
            env["PATH"] = f"{tree / '.venv/bin'}:{env['PATH']}"
            r = subprocess.run(["nice", "-n", "19", "sh", "-c", 'cd "$QC_REPO" || exit 127; exec sh -c "$1"',
                                "qc-demo", p.removeprefix("demo:")], cwd=tree, env=env, capture_output=True,
                               text=True, stdin=subprocess.DEVNULL, check=False)
            sys.stderr.write(f"why: demo exit {r.returncode}: {p}\n")
            runs[p] = lines_by_file(g, tracked, dd / "demo")
    work = {f: work_lines((tree / f).read_text(errors="replace")) for f in want if (tree / f).is_file()}
    verdict: dict[str, dict[str, str]] = {}
    for f, cs in sorted(want.items()):
        for c in cs:
            ran = runs.get(proof[c], {}).get(f)
            verdict.setdefault(f, {})[c] = ("not measured" if ran is None else
                                            "called" if ran & work.get(f, set()) else "loaded only")
    out.write_text(json.dumps({"tree": covers.run(["git", "rev-parse", "HEAD"], tree).strip(), "proof": proof,
                               "verdict": verdict}, indent=1, sort_keys=True) + "\n")
    print(f"why: probe written: {out}")


def report(measure: Path, probe_file: Path, prs_file: Path, ref: str) -> None:
    repo = Path.cwd()
    m = cast("covers.Measure", json.loads(measure.read_text()))
    qc = tomllib.loads(covers.git(repo, "show", f"{ref}:qc.toml"))["demo"]
    b = covers.built(repo, ref)
    adds = added(m, qc, b, covers.Seen(repo, ref))
    verdict = cast("dict[str, dict[str, str]]", json.loads(probe_file.read_text())["verdict"])
    prs = gh_records.merged_list(prs_file.read_text(), str(prs_file))
    cov_b = {c: v[0] for c, v in covers.computed(m, qc, covers.Seen(repo, ref)).items() if c in b}
    cov_a = {c: [str(x) for x in e["covers"]] for c, e in qc.items() if "covers" in e and c in b}
    extra: dict[str, int] = {}
    lost: dict[str, int] = {}
    pairs_b = pairs_a = 0
    for p in prs:
        files = covers.changed(repo, p.merge)
        for c in cov_b:
            hb, ha = covers.hits(cov_b[c], files), covers.hits(cov_a[c], files)
            pairs_b += bool(hb)
            pairs_a += bool(ha)
            if hb and not ha:
                for f in hb:
                    extra[f] = extra.get(f, 0) + 1
            if ha and not hb:
                for f in ha:
                    lost[f] = lost.get(f, 0) + 1
    by_add: dict[str, list[str]] = {}
    by_drop: dict[str, list[str]] = {}
    for c, (plus, minus) in adds.items():
        for f in plus:
            by_add.setdefault(f, []).append(c)
        for f in minus:
            by_drop.setdefault(f, []).append(c)

    def kind(f: str) -> str:
        v = list(verdict.get(f, {}).values())
        if not v:
            return "not probed"
        called, loaded = v.count("called"), v.count("loaded only")
        what = ("mixed" if called and loaded else "real dependency" if called else "incidental load" if loaded
                else "not measured")
        rest = len(v) - called - loaded
        return f"{what} ({called} called, {loaded} loaded only" + (f", {rest} not run" if rest else "") + \
            f", of {len(v)} probes)"

    print(f"Stale (PR, criterion) pairs over the {len(prs)} PRs: (a) {pairs_a}, (b) {pairs_b}.\n")
    print("Files (b) adds, by the extra stale pairs they bring (pairs stale in (b), not in (a), that file among the "
          "changed files reaching the covers; a pair with two such files counts for each).\n")
    print("| file | criteria (b) adds it to | extra stale pairs | probe verdict |\n|---|---|---|---|")
    for f in sorted(by_add, key=lambda f: (-extra.get(f, 0), -len(by_add[f]), f)):
        if extra.get(f, 0) or len(by_add[f]) >= 5:
            print(f"| {f} | {len(by_add[f])} | {extra.get(f, 0)} | {kind(f)} |")
    print("\nDeclared Python paths (b) drops (coverage does not run them in the proof), by the stale pairs they no "
          "longer bring:\n\n| file | criteria | stale pairs only (a) had |\n|---|---|---|")
    for f in sorted(by_drop, key=lambda f: (-lost.get(f, 0), -len(by_drop[f]), f)):
        print(f"| {f} | {len(by_drop[f])} | {lost.get(f, 0)} |")
    print("\nFull list, per criterion: + added, - dropped; per added file probed, its verdict for this criterion.\n")
    for c in sorted(adds):
        plus, minus = adds[c]
        if not plus and not minus:
            continue
        print(f"- {c}")
        for f in sorted(plus):
            v = verdict.get(f, {}).get(c)
            print(f"  + {f}" + (f" ({v})" if v else ""))
        for f in sorted(minus):
            print(f"  - {f}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("probe")
    s.add_argument("tree", type=Path)
    s.add_argument("measure", type=Path)
    s.add_argument("out", type=Path)
    s.add_argument("--main", required=True)
    s = sub.add_parser("report")
    s.add_argument("measure", type=Path)
    s.add_argument("probe", type=Path)
    s.add_argument("--prs", type=Path, required=True)
    s.add_argument("--main", required=True)
    a = ap.parse_args()
    if a.cmd == "probe":
        probe(a.tree, a.measure.resolve(), a.out.resolve(), a.main)
    else:
        report(a.measure, a.probe, a.prs, a.main)


if __name__ == "__main__":
    main()
