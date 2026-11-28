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
Coverage sees Python only, so covers = the Python files coverage names plus every declared path it cannot see (any
non-Python file or a directory: bash scripts, role, skill and feature md, justfile, toml), kept as declared; a declared
Python file coverage does not name is dropped. write ends with check, which fails loud if a criterion lost one.

Subcommands:
  measure TREE OUT [--map FILE]   TREE's coverage per tagged item and per demo command into OUT (JSON). The map: FILE,
                                  else the newest fast map from TREE's HEAD or an ancestor (octo-feather-gate select's).
  write MEASURE [--qc FILE] [--declared REF]
                                  rewrite FILE's (default ./qc.toml) covers lines from MEASURE, the declared covers
                                  read before the write from qc.toml at REF (default: FILE as it stands); prints each
                                  change; then fails loud on a loss against those declarations, and check.
  check [--qc FILE] [--declared REF]
                                  exit 1 naming each declared path coverage cannot see (any non-Python file or dir:
                                  bash, md, justfile, toml) in qc.toml at REF, default HEAD's merge base with the
                                  default branch (octo-feather-gate base), that a criterion's covers in FILE no longer
                                  name. On the default branch itself that base is HEAD: pass --declared then.
  regen [--map FILE] [--declared REF]
                                  measure on this tree into covers/measure-<head12>.json, then write ./qc.toml: the one
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
from typing import Any, TypedDict, cast


class Extra(TypedDict):
    """A tagged item run outside the map: whether it passed, the tracked files its coverage names."""

    passed: bool
    files: list[str] | None


class Demo(TypedDict):
    """A demo command run under coverage: its exit, the tracked files, the output tail of a failed run."""

    exit: int
    files: list[str] | None
    tail: str


class Measure(TypedDict):
    """measure's output: the tree, its map's head, criterion -> tagged items, and each item's and demo's files."""

    tree: str
    map: str
    tags: dict[str, list[str]]
    map_items: dict[str, list[str]]
    extra_items: dict[str, Extra]
    demos: dict[str, Demo]

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gh_records  # noqa: E402  # the gh PR records, validated at the edge

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


def run_items(tree: Path, items: list[str], g: Any, tracked: Any) -> dict[str, Extra]:
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
        ran = cast("dict[str, bool]", g.outcomes(junit)) if junit.is_file() else {}
        out: dict[str, Extra] = {}
        for i in items:
            good = bool(ran.get(g.junit_key(i)))
            files = read_data(g, tracked, data / i) if good else None
            out[i] = {"passed": good, "files": files}
        return out


def run_demo(tree: Path, n: int, command: str, g: Any, tracked: Any) -> Demo:
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
        runs = [pool.submit(run_demo, tree, n, c, g, tracked) for n, c in enumerate(commands)]
        demos = {c: r.result() for c, r in zip(commands, runs, strict=True)}
    out.write_text(json.dumps({"tree": head, "map": fmap["head"], "tags": {c: by[c] for c in sorted(by) if c in qc},
                               "map_items": {i: mapped[i] for i in sorted({i for c in qc if c in by for i in by[c]})
                                             if i in mapped},
                               "extra_items": extra, "demos": demos}, indent=1, sort_keys=True) + "\n")
    print(f"covers: measured {head[:12]} (map {str(fmap['head'])[:12]}): {out}")


class Seen:
    """Whether coverage can see a path: a Python file (*.py, or a python shebang) at REF in REPO, or in the working
    tree with no REF. A directory, a missing path or any other file (bash, md, justfile, toml) it cannot see: such a
    declared path stays in covers."""

    def __init__(self, repo: Path, ref: str | None = None) -> None:
        self.repo, self.ref, self.memo = repo, ref, dict[str, bool]()

    def head(self, path: str) -> str | None:
        if self.ref is None:
            f = self.repo / path
            return f.read_text(errors="replace")[:200] if f.is_file() else None
        kind = subprocess.run(["git", "cat-file", "-t", f"{self.ref}:{path}"], cwd=self.repo, capture_output=True,
                              text=True, check=False).stdout.strip()
        return git(self.repo, "show", f"{self.ref}:{path}")[:200] if kind == "blob" else None

    def __call__(self, path: str) -> bool:
        if path not in self.memo:
            top = self.head(path)
            first = top.splitlines()[0] if top else ""
            self.memo[path] = top is not None and (path.endswith(".py") or (first.startswith("#!") and "python" in first))
        return self.memo[path]


def computed(m: Measure, qc: dict[str, Any], seen: Seen) -> dict[str, tuple[list[str], str]]:
    """criterion -> (covers, how) for each [demo] entry of QC with covers, from measure M: the Python files coverage
    names, plus every declared path coverage cannot see (SEEN)."""
    res: dict[str, tuple[list[str], str]] = {}
    for c, e in qc.items():
        if "covers" not in e:
            continue
        declared = [str(x) for x in e["covers"]]
        unseen = {x for x in declared if not seen(x)}
        if c in m["tags"]:
            items = m["tags"][c]
            got: list[list[str] | None] = []
            for i in items:
                extra = m["extra_items"].get(i)
                got.append(m["map_items"].get(i) or (extra["files"] if extra else None))
            files = {f for x in got if x for f in x}
            res[c] = (sorted(files | unseen), f"tests {' '.join(items)}") if files else (declared, "kept: no tagged item measured")
        elif "command" in e:
            d = m["demos"].get(str(e["command"]))
            if d is not None and d["exit"] in (0, 77) and d["files"]:
                res[c] = (sorted(set(d["files"]) | unseen), f"demo exit {d['exit']}")
            else:
                res[c] = (declared, "kept: demo run failed")
        else:
            res[c] = (declared, "kept: no command, no tagged test (a model eval)")
    return res


def lost(declared: dict[str, Any], now: dict[str, Any], seen: Seen) -> list[str]:
    """Each declared path coverage cannot see (SEEN) that a criterion's covers in NOW no longer name."""
    out: list[str] = []
    for c, e in declared.items():
        have = {str(x) for x in now.get(c, {}).get("covers", [])}
        out += [f"{c}: {x}" for x in e.get("covers", []) if not seen(str(x)) and str(x) not in have]
    return out


def declared_qc(root: Path, ref: str) -> dict[str, Any]:
    """qc.toml's [demo] table at REF in ROOT."""
    return cast("dict[str, Any]", tomllib.loads(git(root, "show", f"{ref}:qc.toml"))["demo"])


def baseline(root: Path, ref: str | None) -> str:
    """The commit whose qc.toml holds the declarations a check compares with: REF, else HEAD's merge base with the
    default branch as octo-feather-gate base finds it (the gate's own rule), an independent file, never the one
    checked. None found: exit 2, naming --declared."""
    if ref:
        return ref
    p = subprocess.run([sys.executable, str(root / "scripts/octo-feather-gate"), "base"], cwd=root,
                       capture_output=True, text=True, check=False)
    if p.returncode or not p.stdout.split():
        sys.stderr.write(f"covers: no baseline: {p.stderr.strip()}; pass --declared REF\n")
        sys.exit(2)
    return p.stdout.split()[0]


def fail_lost(bad: list[str], against: str) -> None:
    if bad:
        sys.exit(f"covers: FAIL: declared paths coverage cannot see, lost from covers (against {against}):\n  "
                 + "\n  ".join(bad))


def check(root: Path, ref: str | None, qc_file: Path) -> None:
    """Fail loud (exit 1) when a criterion's covers in QC_FILE lost a declared path coverage cannot see, compared
    with qc.toml at baseline(REF)."""
    base = baseline(root, ref)
    fail_lost(lost(declared_qc(root, base), tomllib.loads(qc_file.read_text())["demo"], Seen(root)), base[:12])
    print(f"covers: check ok: no criterion lost a declared path coverage cannot see (against {base[:12]})")


def write(measure_file: Path, qc_file: Path, ref: str | None = None) -> None:
    """Rewrite QC_FILE's covers lines from MEASURE_FILE, the declarations read before the write (from qc.toml at REF,
    else QC_FILE as it stands); then fail loud if the written file lost one of those declarations, or one declared at
    baseline(REF)."""
    m = cast("Measure", json.loads(measure_file.read_text()))
    root = qc_file.resolve().parent
    text = qc_file.read_text()
    before = declared_qc(root, ref) if ref else cast("dict[str, Any]", tomllib.loads(text)["demo"])
    res = computed(m, before, Seen(root))
    lines, cur, changed = text.splitlines(keepends=True), None, 0
    for n, ln in enumerate(lines):
        if hit := COVERS.match(ln.rstrip("\n")):
            cur = hit.group(1)
        elif ln.startswith("["):
            cur = None
        elif cur and ln.startswith("covers = ") and cur in res:
            new = "covers = " + json.dumps(res[cur][0]) + "\n"
            if new != ln:
                changed += 1
                lines[n] = new
            print(f"{cur}: {len(res[cur][0])} files ({res[cur][1]}){'' if new == ln else ' CHANGED'}")
    qc_file.write_text("".join(lines))
    print(f"covers: {changed} covers lines changed in {qc_file}")
    after = cast("dict[str, Any]", tomllib.loads(qc_file.read_text())["demo"])
    fail_lost(lost(before, after, Seen(root)), "the declarations read before the write")
    check(root, ref, qc_file)


# ---- counts ----

def git(repo: Path, *a: str) -> str:
    return run(["git", *a], repo)


def hit(path: str, cov: str) -> bool:   # git pathspec as octo-feather-spec-status _changes uses it
    return path == cov or path.startswith(cov.rstrip("/") + "/")


def built(repo: Path, ref: str) -> set[str]:
    out: set[str] = set()
    for f in git(repo, "ls-tree", "--name-only", ref, "docs/specs/").split():
        if f.endswith(".status.json"):
            slug = f.split("/")[-1].removesuffix(".status.json")
            for k, v in json.loads(git(repo, "show", f"{ref}:{f}"))["criteria"].items():
                if v.get("status") == "built":
                    out.add(f"{slug}#{k}")
    return out


HUB = "scripts/octo-feather-lane"
NEAR_LINES = 40


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

    def place(self, commit: str, near: bool = False, base: str | None = None) -> set[str]:
        """The split files COMMIT's change to the hub (BASE, default commit^1, ..commit) lands in: the union of
        hunks()."""
        out: set[str] = set()
        for _a, _an, placed in self.hunks(commit, near, base):
            out |= placed
        return out if near else (out or {HUB})

    def hunks(self, commit: str, near: bool = False, base: str | None = None) -> list[tuple[int, int, set[str]]]:
        """Each hunk of the hub's diff BASE (default commit^1)..COMMIT: its pre-image start and length, and the split
        files it lands in. A hunk none of whose lines is placed goes to the dispatcher; with NEAR (c''), instead to
        the file holding the nearest unchanged line around it in the pre-image (up to NEAR_LINES each way) that
        exactly one split file holds: the module header or help chunk it sits in; none found, it lands nowhere."""
        base = base or f"{commit}^1"
        old = run(["git", "show", f"{base}:{HUB}"], self.repo, check=False)
        new = run(["git", "show", f"{commit}:{HUB}"], self.repo, check=False)
        od, nd = self.defs(old), self.defs(new)
        ol, nl = old.splitlines(), new.splitlines()
        diff = git(self.repo, "diff", "-U0", base, commit, "--", HUB)
        out: list[tuple[int, int, set[str]]] = []

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
            placed: set[str] = set[str]().union(*(put(od, ol, k) for k in range(a, a + an)),
                                 *(put(nd, nl, k) for k in range(b, b + bn)))
            if placed or not near:
                out.append((a, an, placed or {HUB}))
                continue
            found: set[str] = set()
            for d in range(1, NEAR_LINES + 1):
                hold = [self.lines.get(ol[k - 1].strip(), set()) for k in (a - d, a + an - 1 + d)
                        if 0 < k <= len(ol) and len(ol[k - 1].strip()) > 3]
                one = [x for x in hold if len(x) == 1]
                if one:
                    found = one[0]
                    break
            out.append((a, an, found))
        return out


def changed(repo: Path, commit: str) -> list[str]:
    return git(repo, "diff", "--name-only", f"{commit}^1", commit).split()


def stale(covers: dict[str, list[str]], files: list[str]) -> int:
    return sum(any(hit(f, c) for f in files for c in cov) for cov in covers.values())


def q(xs: list[int], p: float) -> int:   # nearest rank, as the w1 survey's
    xs = sorted(xs)
    return xs[min(len(xs) - 1, max(0, round(p * (len(xs) - 1))))]


LANE_BEFORE = {HUB, "scripts/post_merge.py", "scripts/merge_ask.py", "scripts/start_lane.py"}


def hits(cov: list[str], files: list[str]) -> list[str]:
    return [f for f in files if any(hit(f, c) for c in cov)]


def counts(a: argparse.Namespace) -> None:
    repo = Path.cwd()
    prs = gh_records.merged_list(Path(a.prs).read_text(), str(a.prs))
    pr = gh_records.view(run(["gh", "pr", "view", str(a.pr), "--json", "number,mergeCommit"], repo), "gh pr view")
    qc_main = tomllib.loads(git(repo, "show", f"{a.main}:qc.toml"))["demo"]
    sets: dict[str, dict[str, list[str]]] = {}
    for name, ref, mfile in (("a", a.main, None), ("b", a.main, a.b), ("c", a.split, a.c)):
        qc = qc_main if ref == a.main else tomllib.loads(git(repo, "show", f"{ref}:qc.toml"))["demo"]
        b = built(repo, ref)
        if mfile is None:
            cov = {c: [str(x) for x in e["covers"]] for c, e in qc.items() if "covers" in e}
        else:
            m = cast("Measure", json.loads(Path(mfile).read_text()))
            cov = {c: v[0] for c, v in computed(m, qc, Seen(repo, ref)).items()}
        sets[name] = {c: v for c, v in cov.items() if c in b}
    split = Split(repo, a.split)
    lane_after = {HUB, *[f"scripts/{m}.py" for m in split.modules()]}

    def files_of(commit: str, mode: str) -> list[str]:
        fs = changed(repo, commit)
        if mode == "raw" or HUB not in fs:
            return fs
        return sorted({x for f in fs for x in (split.place(commit, near=mode == "near") if f == HUB else {f})})

    cols = [("(a) declared, main", "a", "raw", LANE_BEFORE), ("(b) coverage, main tree", "b", "raw", LANE_BEFORE),
            ("(c) coverage, split tree", "c", "raw", lane_after),
            ("(c') split tree, hub hunks placed, unplaced to the dispatcher", "c", "placed", lane_after),
            ("(c'') split tree, hub hunks placed, unplaced by nearest context or dropped", "c", "near", lane_after)]
    every = [pr, *prs]
    rows: list[list[int]] = [[p.number] for p in every]
    per_col: list[dict[str, Any]] = []
    for _h, s, mode, lane in cols:
        pairs = alone = 0
        trig: dict[str, int] = {}
        sole: dict[str, int] = {}
        changes: dict[str, int] = {}
        for n, p in enumerate(every):
            files = files_of(p.merge, mode)
            if n:
                for f in files:
                    changes[f] = changes.get(f, 0) + 1
            k = 0
            for cov in sets[s].values():
                h = hits(cov, files)
                if not h:
                    continue
                k += 1
                if n:
                    pairs += 1
                    alone += set(h) <= lane
                    for f in h:
                        trig[f] = trig.get(f, 0) + 1
                    if len(h) == 1:
                        sole[h[0]] = sole.get(h[0], 0) + 1
            rows[n].append(k)
        per_col.append({"pairs": pairs, "alone": alone, "trig": trig, "sole": sole, "changes": changes, "set": s})
    print(f"Built criteria with covers: (a) {len(sets['a'])}, (b) {len(sets['b'])}, (c) {len(sets['c'])}. "
          f"PRs: {len(prs)} merged, #{prs[-1].number}..#{prs[0].number}, "
          f"{prs[-1].merged_at[:10]}..{prs[0].merged_at[:10]}.\n")
    print(f"| covers set | PR #{a.pr} (lane gh1234) | median | p90 | max | stale (PR, criterion) pairs | "
          "of them through lane-command files alone |")
    print("|---|---|---|---|---|---|---|")
    for k, (h, *_x) in enumerate(cols, 1):
        xs = [r[k] for r in rows[1:]]
        c = per_col[k - 1]
        share = f"{c['alone']} ({100 * c['alone'] / c['pairs']:.0f}%)" if c["pairs"] else "0"
        print(f"| {h} | {rows[0][k]} | {statistics.median(xs):g} | {q(xs, .9)} | {max(xs)} | {c['pairs']} | {share} |")
    print(f"\nLane-command files: before the split {', '.join(sorted(LANE_BEFORE))}; after it the hub and "
          f"{', '.join(sorted(lane_after - {HUB}))}. A pair counts when every changed file reaching its covers is one.")
    for k, (h, s, _m, _l) in enumerate(cols):
        c = per_col[k]
        ncrit: dict[str, int] = {}
        for cov in sets[s].values():
            for f in set(cov):
                ncrit[f] = ncrit.get(f, 0) + 1
        top = sorted(c["trig"].items(), key=lambda kv: (-kv[1], kv[0]))[:15]
        print(f"\n{h}: top triggers. | file | criteria listing it | PRs changing it (of {len(prs)}) | stale pairs it "
              "reaches | pairs it alone reaches |\n|---|---|---|---|---|")
        for f, n in top:
            print(f"| {f} | {ncrit.get(f, 0)} | {c['changes'].get(f, 0)} | {n} | {c['sole'].get(f, 0)} |")
    print("\nPer PR: number, " + ", ".join(h.split(" ")[0] for h, *_x in cols))
    for r in rows:
        print(" ".join(map(str, r)))


def fetch(out: Path, repo: Path) -> None:
    prs = gh_records.merged_list(run(["gh", "pr", "list", "--state", "merged", "--limit", "60", "--json",
                                      "number,mergedAt,mergeCommit"], repo), "gh pr list")
    prs.sort(key=lambda p: p.merged_at, reverse=True)
    out.write_text(json.dumps([p.raw() for p in prs], indent=1, sort_keys=True) + "\n")
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
    s.add_argument("--declared")
    s = sub.add_parser("check")
    s.add_argument("--qc", type=Path, default=Path("qc.toml"))
    s.add_argument("--declared")
    s = sub.add_parser("regen")
    s.add_argument("--declared")
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
        write(a.measure, a.qc, a.declared)
    elif a.cmd == "check":
        check(a.qc.resolve().parent, a.declared, a.qc)
    elif a.cmd == "regen":
        root = Path(run(["git", "rev-parse", "--show-toplevel"], Path.cwd()).strip())
        head = run(["git", "rev-parse", "HEAD"], root).strip()
        out = HERE / f"measure-{head[:12]}.json"
        measure(root, out, a.map)
        write(out, root / "qc.toml", a.declared)
    elif a.cmd == "fetch-prs":
        fetch(a.out, a.repo)
    else:
        counts(a)


if __name__ == "__main__":
    main()
