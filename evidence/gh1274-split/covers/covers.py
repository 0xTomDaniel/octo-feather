#!/usr/bin/env python3
"""covers.py: qc.toml `covers` from coverage, and the stale counts (a), (b), (c) (ticket #1334, design #1274
comment 7232729794 sections 5 and 6, commit 3). Run under the kit's uv venv (coverage): `uv run --locked --offline
--no-sync python3 evidence/gh1274-split/covers/covers.py ...`. README.md beside it: the commands, in order.

One mechanism: the coverage is the fast map's (`just fast-map`, `octo-feather-gate map`). Per criterion with a
[demo] entry in qc.toml:
  - a criterion a test carries (pytest's `criterion` marker or a tests/*.sh `# criterion:` header, collected the way
    `octo-feather-qc` collects them: `just check-tests --collect-only` writing OCTO_FEATHER_QC_TAGS): the files the
    coverage map entries of those test items name, as qc proves it from those tests. A tagged item the map lacks (an
    e2e item, which the mapping run leaves out, or one that did not pass there) is run here under the same coverage
    configuration (tests/gate/coverage.toml) through `just check-tests`, and read the way `octo-feather-gate map`
    reads it (its Tracked, outcomes and junit_key, loaded from the tree measured);
  - else its demo `command`, run as `just qc` runs it (sh in the repo, QC_REPO set), under that configuration, read
    likewise;
  - else (a model eval, no command, no test) or when no run passed: its covers stay as declared, and say so.
Coverage sees Python only: what it reports is the covers, nothing named by hand.

Subcommands:
  measure TREE OUT [--map FILE]   TREE's coverage per tagged item and per demo command into OUT (JSON). The map: FILE,
                                  else the newest fast map from TREE's HEAD or an ancestor (octo-feather-gate select's).
  write MEASURE [--qc FILE]       rewrite FILE's (default ./qc.toml) covers lines from MEASURE; prints each change.
  regen [--map FILE]              measure on this tree into covers/measure-<head12>.json, then write ./qc.toml: the one
                                  command; a second run changes nothing.
  fetch-prs OUT [--repo DIR]      the last 60 merged PRs as of now: number, mergedAt, merge commit.
  counts --main REF --b MEASURE --c MEASURE --split REF --prs FILE --pr N
                                  the table (a)/(b)/(c) x (PR N, median, p90, max over FILE's PRs), markdown, stdout.
"""

from __future__ import annotations

import argparse
import ast
import concurrent.futures
import importlib.machinery
import importlib.util
import json
import os
import re
import statistics
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
SCRIPT = "tests/gate/test_gate.py::test_script["
COVERS = re.compile(r'^\[demo\."([^"]+)"\]$')


def run(cmd: list[str], cwd: Path, env: dict[str, str] | None = None, check: bool = True) -> str:
    p = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, stdin=subprocess.DEVNULL)
    if check and p.returncode:
        sys.exit(f"covers: {' '.join(cmd)} in {cwd}: exit {p.returncode}\n{(p.stdout + p.stderr)[-3000:]}")
    return p.stdout


def gate(tree: Path) -> Any:
    """TREE's scripts/octo-feather-gate as a module (its Tracked, newest_map, outcomes, junit_key: the map's reading).
    Its git calls read the cwd, so callers chdir into TREE first."""
    loader = importlib.machinery.SourceFileLoader("octo_feather_gate", str(tree / "scripts/octo-feather-gate"))
    spec = importlib.util.spec_from_loader("octo_feather_gate", loader)
    assert spec is not None
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


def item_of(node: str) -> str:
    """A collected node id as the map keys it: a tests/*.sh item by its path."""
    return node[len(SCRIPT):-1] if node.startswith(SCRIPT) and node.endswith("]") else node


def node_of(item: str) -> str:
    return f"{SCRIPT}{item}]" if "::" not in item else item


def tags(tree: Path) -> dict[str, list[str]]:
    """criterion id -> the map items carrying it, collected as octo-feather-qc tagged_cases collects them."""
    with tempfile.TemporaryDirectory(prefix="covers-tags-") as d:
        out = Path(d, "tags.json")
        env = {k: v for k, v in os.environ.items() if k != "OCTO_FEATHER_QC_CLAIMS"} | {
            "OCTO_FEATHER_QC_TAGS": str(out), "PYTHONDONTWRITEBYTECODE": "1"}
        run(["just", "check-tests", "--collect-only", "-q", "-n", "0", "-p", "no:cacheprovider"], tree, env)
        cases: dict[str, list[str]] = json.loads(out.read_text())
    by: dict[str, list[str]] = {}
    for n, cids in sorted(cases.items()):
        for c in cids:
            by.setdefault(c, []).append(item_of(n))
    return by


def cov_env(tree: Path, data: Path) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k not in ("GATE_ITEM", "VIRTUAL_ENV")}
    return env | {"COV_MAP_DIR": str(data), "COVERAGE_PROCESS_START": str(tree / "tests/gate/coverage.toml")}


def read_data(g: Any, tracked: Any, d: Path) -> list[str] | None:
    """The tracked files one item's coverage data dir D names, as octo-feather-gate map reads them; None: no data."""
    import coverage  # noqa: PLC0415  # the kit venv's, as the map's

    runs = list(d.glob("cov*")) if d.is_dir() else []
    if not runs:
        return None
    files: set[str] = set()
    for f in runs:
        cd = coverage.CoverageData(basename=str(f))
        cd.read()
        for m in cd.measured_files():
            files |= tracked.source(m)
    return sorted(files)


def run_items(tree: Path, items: list[str], g: Any, tracked: Any) -> dict[str, Any]:
    """Each tagged item the map lacks, run under the mapping run's configuration (just fast-map's command line, e2e
    allowed): item -> {passed, files}."""
    if not items:
        return {}
    with tempfile.TemporaryDirectory(prefix="covers-items-") as d:
        data, junit = Path(d, "data"), Path(d, "junit.xml")
        cap = tomllib.loads((tree / "gate-budget.toml").read_text())["fast_workers"]
        env = cov_env(tree, data) | {"GATE_WORKERS": str(cap)}
        p = subprocess.run(["nice", "-n", "19", "just", "check-tests", f"--junitxml={junit}", "-p", "no:cpu-shown",
                            *[node_of(i) for i in items]], cwd=tree, env=env, capture_output=True, text=True,
                           stdin=subprocess.DEVNULL)
        sys.stderr.write(f"covers: {len(items)} tagged items outside the map ran: exit {p.returncode}\n")
        ran = g.outcomes(junit) if junit.is_file() else {}
        out: dict[str, Any] = {}
        for i in items:
            good = bool(ran.get(g.junit_key(i)))
            files = read_data(g, tracked, data / i) if good else None
            out[i] = {"passed": good, "files": files}
        return out


def run_demo(tree: Path, n: int, command: str, g: Any, tracked: Any) -> dict[str, Any]:
    """One demo command as `just qc` runs it (sh in the repo, QC_REPO set) under coverage: {exit, files}."""
    with tempfile.TemporaryDirectory(prefix=f"covers-demo{n}-") as d:
        data = Path(d, "data")
        env = cov_env(tree, data) | {"GATE_ITEM": "demo", "QC_REPO": str(tree),
                                     "VERIFY_OCTO_FEATHER_RUN_DIR": f"{d}/run",
                                     "VERIFY_OCTO_FEATHER_EVIDENCE_DIR": f"{d}/evidence"}
        venv = tree / ".venv/bin"
        env["PATH"] = f"{venv}:{env['PATH']}"
        p = subprocess.run(["nice", "-n", "19", "sh", "-c", 'cd "$QC_REPO" || exit 127; exec sh -c "$1"', "qc-demo",
                            command], cwd=tree, env=env, capture_output=True, text=True, stdin=subprocess.DEVNULL)
        files = read_data(g, tracked, data / "demo")
        sys.stderr.write(f"covers: demo exit {p.returncode}, {len(files or [])} files: {command}\n")
        return {"exit": p.returncode, "files": files, "tail": (p.stdout + p.stderr)[-600:] if p.returncode not in (0, 77) else ""}


def measure(tree: Path, out: Path, map_file: Path | None) -> None:
    tree = tree.resolve()
    os.chdir(tree)
    if not (tree / ".venv/bin/python3").exists():
        run(["uv", "sync", "--locked", "--offline"], tree)
    g = gate(tree)
    tracked = g.Tracked()
    head = run(["git", "rev-parse", "HEAD"], tree).strip()
    fmap = json.loads(map_file.read_text()) if map_file else g.newest_map(head)
    if fmap is None:
        sys.exit("covers: no fast map from HEAD or an ancestor: run `just fast-map` first")
    qc = tomllib.loads((tree / "qc.toml").read_text())["demo"]
    by = tags(tree)
    mapped: dict[str, list[str]] = fmap["items"]
    wanted = sorted({i for c in qc if c in by for i in by[c]} - set(mapped))
    extra = run_items(tree, wanted, g, tracked)
    commands = sorted({str(e["command"]) for c, e in qc.items() if "command" in e and c not in by})
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        demos = dict(zip(commands, pool.map(lambda nc: run_demo(tree, nc[0], nc[1], g, tracked), enumerate(commands))))
    out.write_text(json.dumps({"tree": head, "map": fmap["head"], "tags": {c: by[c] for c in sorted(by) if c in qc},
                               "map_items": {i: mapped[i] for i in sorted({i for c in qc if c in by for i in by[c]})
                                             if i in mapped},
                               "extra_items": extra, "demos": demos}, indent=1, sort_keys=True) + "\n")
    print(f"covers: measured {head[:12]} (map {str(fmap['head'])[:12]}): {out}")


def computed(m: dict[str, Any], qc: dict[str, Any]) -> dict[str, tuple[list[str], str]]:
    """criterion -> (covers, how) for each [demo] entry of QC with covers, from measure M."""
    res: dict[str, tuple[list[str], str]] = {}
    for c, e in qc.items():
        if "covers" not in e:
            continue
        declared = [str(x) for x in e["covers"]]
        if c in m["tags"]:
            items = m["tags"][c]
            got = [m["map_items"].get(i) or (m["extra_items"].get(i) or {}).get("files") for i in items]
            files = sorted({f for x in got if x for f in x})
            res[c] = (files, f"tests {' '.join(items)}") if files else (declared, "kept: no tagged item measured")
        elif "command" in e:
            d = m["demos"].get(str(e["command"]))
            ok = d is not None and d["exit"] in (0, 77) and d["files"]
            res[c] = (sorted(d["files"]), f"demo exit {d['exit']}") if ok else (declared, "kept: demo run failed")
        else:
            res[c] = (declared, "kept: no command, no tagged test (a model eval)")
    return res


def write(measure_file: Path, qc_file: Path) -> None:
    m = json.loads(measure_file.read_text())
    text = qc_file.read_text()
    res = computed(m, tomllib.loads(text)["demo"])
    lines, cur, changed = text.splitlines(keepends=True), None, 0
    for n, ln in enumerate(lines):
        if hit := COVERS.match(ln.rstrip("\n")):
            cur = hit.group(1)
        elif ln.startswith("[") :
            cur = None
        elif cur and ln.startswith("covers = ") and cur in res:
            new = "covers = " + json.dumps(res[cur][0]) + "\n"
            if new != ln:
                changed += 1
                lines[n] = new
            print(f"{cur}: {len(res[cur][0])} files ({res[cur][1]}){'' if new == ln else ' CHANGED'}")
    qc_file.write_text("".join(lines))
    print(f"covers: {changed} covers lines changed in {qc_file}")


# ---- counts ----

def git(repo: Path, *a: str) -> str:
    return run(["git", *a], repo)


def hit(path: str, cov: str) -> bool:   # git pathspec as octo-feather-spec-status _changes uses it
    return path == cov or path.startswith(cov.rstrip("/") + "/")


def built(repo: Path, ref: str) -> set[str]:
    out = set()
    for f in git(repo, "ls-tree", "--name-only", ref, "docs/specs/").split():
        if f.endswith(".status.json"):
            slug = f.split("/")[-1].removesuffix(".status.json")
            for k, v in json.loads(git(repo, "show", f"{ref}:{f}"))["criteria"].items():
                if v.get("status") == "built":
                    out.add(f"{slug}#{k}")
    return out


HUB = "scripts/octo-feather-lane"


class Split:
    """The hub's changed lines on a pre-split diff, placed on the split tree (REF), among the hub and the modules the
    split moved its code into (../tables.py CUT, the codemod's table): a line inside a top-level def goes to the module
    defining that name; any other non-blank line (help text, imports, constants) to each of those files holding that
    exact line (a line no file holds today, edited since, places nothing); a hunk none of whose lines is placed goes
    to the dispatcher."""

    @staticmethod
    def modules() -> list[str]:
        ns: dict[str, Any] = {}
        exec((HERE.parent / "tables.py").read_text(), ns)  # noqa: S102  # the split's own table
        return sorted(ns["CUT"])

    def __init__(self, repo: Path, ref: str) -> None:
        self.repo, self.ref = repo, ref
        self.owner: dict[str, str] = {}
        self.lines: dict[str, set[str]] = {}
        files = [HUB, *[f"scripts/{m}.py" for m in self.modules()]]
        for f in files:
            src = git(repo, "show", f"{ref}:{f}")
            for s in src.splitlines():
                if len(s.strip()) > 3:
                    self.lines.setdefault(s.strip(), set()).add(f)
            if f == HUB:
                continue
            try:
                tree = ast.parse(src)
            except SyntaxError:
                continue
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    self.owner.setdefault(node.name, f)

    @staticmethod
    def defs(src: str) -> list[tuple[int, int, str]]:
        try:
            body = ast.parse(src).body
        except SyntaxError:
            return []
        return [(n.lineno - len(n.decorator_list), n.end_lineno or n.lineno, n.name) for n in body
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]

    def place(self, commit: str) -> set[str]:
        """The split files COMMIT's change to the hub (commit^1..commit) lands in."""
        old = run(["git", "show", f"{commit}^1:{HUB}"], self.repo, check=False)
        new = run(["git", "show", f"{commit}:{HUB}"], self.repo, check=False)
        od, nd = self.defs(old), self.defs(new)
        ol, nl = old.splitlines(), new.splitlines()
        diff = git(self.repo, "diff", "-U0", f"{commit}^1", commit, "--", HUB)
        out: set[str] = set()

        def at(defs: list[tuple[int, int, str]], line: int) -> str | None:
            return next((name for a, b, name in defs if a <= line <= b), None)

        def put(defs: list[tuple[int, int, str]], src: list[str], line: int) -> set[str]:
            name = at(defs, line)
            if name and name in self.owner:
                return {self.owner[name]}
            text = src[line - 1].strip() if 0 < line <= len(src) else ""
            return self.lines.get(text, set()) if len(text) > 3 else set()

        for h in re.finditer(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", diff, re.M):
            a, an, b, bn = int(h[1]), int(h[2] or 1), int(h[3]), int(h[4] or 1)
            placed = set().union(*(put(od, ol, k) for k in range(a, a + an)),
                                 *(put(nd, nl, k) for k in range(b, b + bn)))
            out |= placed or {HUB}
        return out or {HUB}


def changed(repo: Path, commit: str) -> list[str]:
    return git(repo, "diff", "--name-only", f"{commit}^1", commit).split()


def stale(covers: dict[str, list[str]], files: list[str]) -> int:
    return sum(any(hit(f, c) for f in files for c in cov) for cov in covers.values())


def q(xs: list[int], p: float) -> int:   # nearest rank, as the w1 survey's
    xs = sorted(xs)
    return xs[min(len(xs) - 1, max(0, round(p * (len(xs) - 1))))]


def counts(a: argparse.Namespace) -> None:
    repo = Path.cwd()
    prs = json.loads(Path(a.prs).read_text())
    pr = json.loads(run(["gh", "pr", "view", str(a.pr), "--json", "number,mergeCommit"], repo))
    qc_main = tomllib.loads(git(repo, "show", f"{a.main}:qc.toml"))["demo"]
    sets: dict[str, dict[str, list[str]]] = {}
    for name, ref, mfile in (("a", a.main, None), ("b", a.main, a.b), ("c", a.split, a.c)):
        qc = qc_main if ref == a.main else tomllib.loads(git(repo, "show", f"{ref}:qc.toml"))["demo"]
        b = built(repo, ref)
        if mfile is None:
            cov = {c: [str(x) for x in e["covers"]] for c, e in qc.items() if "covers" in e}
        else:
            cov = {c: v[0] for c, v in computed(json.loads(Path(mfile).read_text()), qc).items()}
        sets[name] = {c: v for c, v in cov.items() if c in b}
    split = Split(repo, a.split)

    def files_of(commit: str, translate: bool) -> list[str]:
        fs = changed(repo, commit)
        return sorted({x for f in fs for x in (split.place(commit) if translate and f == HUB else {f})})

    rows = []
    cols = [("a", False), ("b", False), ("c", False), ("c", True)]
    for p in [pr, *prs]:
        oid = p["mergeCommit"]["oid"]
        rows.append([p["number"]] + [stale(sets[s], files_of(oid, t)) for s, t in cols])
    head = ["(a) declared, main", "(b) coverage, main tree", "(c) coverage, split tree",
            "(c') coverage, split tree, hub hunks placed"]
    print(f"Built criteria with covers: (a) {len(sets['a'])}, (b) {len(sets['b'])}, (c) {len(sets['c'])}. "
          f"PRs: {len(prs)} merged, #{prs[-1]['number']}..#{prs[0]['number']}, "
          f"{prs[-1]['mergedAt'][:10]}..{prs[0]['mergedAt'][:10]}.\n")
    print(f"| covers set | PR #{a.pr} (lane gh1234) | median | p90 | max |")
    print("|---|---|---|---|---|")
    for k, h in enumerate(head, 1):
        xs = [r[k] for r in rows[1:]]
        print(f"| {h} | {rows[0][k]} | {statistics.median(xs):g} | {q(xs, .9)} | {max(xs)} |")
    for s in ("a", "b", "c"):
        per: dict[str, int] = {}
        for cov in sets[s].values():
            for f in set(cov):
                per[f] = per.get(f, 0) + 1
        top = sorted(per.items(), key=lambda kv: (-kv[1], kv[0]))[:12]
        print(f"\nPaths in the most built criteria's covers, ({s}): " + ", ".join(f"{f} {n}" for f, n in top))
    print("\nPer PR: number, (a), (b), (c), (c')")
    for r in rows:
        print(" ".join(map(str, r)))


def fetch(out: Path, repo: Path) -> None:
    prs = json.loads(run(["gh", "pr", "list", "--state", "merged", "--limit", "60", "--json",
                          "number,mergedAt,mergeCommit"], repo))
    prs.sort(key=lambda p: p["mergedAt"], reverse=True)
    out.write_text(json.dumps(prs, indent=1) + "\n")
    print(f"covers: {len(prs)} PRs into {out}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("measure")
    s.add_argument("tree", type=Path)
    s.add_argument("out", type=Path)
    s.add_argument("--map", type=Path)
    s = sub.add_parser("write")
    s.add_argument("measure", type=Path)
    s.add_argument("--qc", type=Path, default=Path("qc.toml"))
    s = sub.add_parser("regen")
    s.add_argument("--map", type=Path)
    s = sub.add_parser("fetch-prs")
    s.add_argument("out", type=Path)
    s.add_argument("--repo", type=Path, default=Path.cwd())
    s = sub.add_parser("counts")
    for k in ("main", "b", "c", "split", "prs"):
        s.add_argument(f"--{k}", required=True)
    s.add_argument("--pr", type=int, required=True)
    a = ap.parse_args()
    if a.cmd == "measure":
        measure(a.tree, a.out.resolve(), a.map)
    elif a.cmd == "write":
        write(a.measure, a.qc)
    elif a.cmd == "regen":
        root = Path(run(["git", "rev-parse", "--show-toplevel"], Path.cwd()).strip())
        head = run(["git", "rev-parse", "HEAD"], root).strip()
        out = HERE / f"measure-{head[:12]}.json"
        measure(root, out, a.map)
        write(out, root / "qc.toml")
    elif a.cmd == "fetch-prs":
        fetch(a.out, a.repo)
    else:
        counts(a)


if __name__ == "__main__":
    main()
