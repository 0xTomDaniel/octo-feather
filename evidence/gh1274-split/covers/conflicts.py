#!/usr/bin/env python3
"""conflicts.py: real merge conflicts when main is merged into a lane, replayed with git merge-tree, and the hub's
conflicts replayed against the split (#1334, the architecture shaper's addition; reuses its
/home/exedev/scratch/arch-lane-split-20261128/conflicts2.py). Run from the kit root, after `git fetch origin`:
`uv run --locked --offline --no-sync python3 evidence/gh1274-split/covers/conflicts.py --since 2026-11-12 --split REF`.

Merges: every merge commit in origin/main's history since --since that is not on main's first-parent line; a merge of
main into a lane has one parent on that line (the shaper's `main` kind), any other is a lane integrating a worker
(`integrate`). Each is replayed as `git merge-tree --write-tree --name-only` of its two parents; exit 1 is a real
conflict, its conflicted files the names printed.

The split replay maps hunks to split modules by function (covers.py Split.hunks), it does not run the codemod on old
trees: the codemod (../split.py) checks its tables against main 95353ff3 and refuses defs it does not know, which older
hubs have. For a conflict in scripts/octo-feather-lane: each side's hunks from the merge base (ours: the lane parent,
theirs: the main parent), each placed on the split files of REF; two hunks conflict as git's merge does, when their
pre-image ranges overlap or touch. A pair whose two sides land in no common split file would not have conflicted after
the split (functions move whole, so lines that collide inside one function still collide in its module). Two
placements: (c') a hunk no line of which places goes to the dispatcher; (c'') by its nearest context, else nowhere.
A conflict in another scripts/ file the split leaves as it is (merge_ask.py gains functions but keeps its own; the gate
and qa scripts are not touched) stands.
It reads no GitHub data (git only), so it has no gh edge to validate (gh_records.py).
"""

from __future__ import annotations

import argparse
import collections
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import covers  # noqa: E402

REPO = Path.cwd()
CP, CPP = "c'", "c''"


def g(*a: str) -> tuple[int, str]:
    p = subprocess.run(["git", *a], cwd=REPO, capture_output=True, text=True, check=False)
    return p.returncode, p.stdout


def bucket(f: str) -> str:
    if f.endswith(".calls.jsonl"):
        return "*.calls.jsonl"
    if f.endswith(".status.json"):
        return "status"
    if f in ("qc.toml", ".basedpyright/baseline.json"):
        return f
    if f.startswith("docs/specs/"):
        return "specs"
    if f.startswith(".agents/skills/verify-octo-feather/"):
        return "verify skill"
    for top in ("tests/", "scripts/"):
        if f.startswith(top):
            return top
    return "other"


def gaps(a: int, an: int) -> tuple[int, int]:
    """A -U0 hunk's pre-image as a range of gaps between lines: an insertion after line A is (A, A)."""
    return (a, a) if an == 0 else (a - 1, a + an - 1)


def hub_pairs(split: covers.Split, base: str, ours: str, theirs: str, near: bool) -> list[tuple[str, set[str], set[str]]]:
    """Each pair of hunks, ours and theirs from BASE, whose ranges overlap or touch: (where, ours' files, theirs')."""
    mine, other = split.hunks(ours, near, base), split.hunks(theirs, near, base)
    out: list[tuple[str, set[str], set[str]]] = []
    for a, an, so in mine:
        for b, bn, st in other:
            (s1, e1), (s2, e2) = gaps(a, an), gaps(b, bn)
            if s1 <= e2 and s2 <= e1:
                out.append((f"base lines {a}+{an} / {b}+{bn}", so, st))
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--since", default="2026-11-12")
    ap.add_argument("--split", required=True)
    a = ap.parse_args()
    mainline = set(g("log", "--first-parent", "--format=%H", "origin/main")[1].split())
    merges = [ln.split()[:3] for ln in g("log", "--merges", f"--since={a.since}", "--format=%H %P", "origin/main")[1]
              .splitlines()]
    stats = {k: collections.Counter[str]() for k in ("main", "integrate")}
    files = {k: collections.Counter[str]() for k in ("main", "integrate")}
    scripts: list[tuple[str, str, str, str]] = []   # (merge, lane parent, main parent, file)
    for h, p1, p2 in merges:
        if h in mainline:
            continue
        kind = "main" if (p1 in mainline or p2 in mainline) else "integrate"
        rc, out = g("merge-tree", "--write-tree", "--name-only", "--no-messages", p1, p2)
        stats[kind]["merges"] += 1
        if rc != 1:
            continue
        stats[kind]["conflicted"] += 1
        for f in [x for x in out.splitlines()[1:] if x.strip()]:
            files[kind][f] += 1
            if kind == "main" and f.startswith("scripts/"):
                lane, mp = (p2, p1) if p1 in mainline else (p1, p2)
                scripts.append((h, lane, mp, f))
    print("### Merge conflicts (git merge-tree replay)\n")
    print(f"Merges since {a.since} in origin/main's history off its first-parent line, replayed from their parents.\n")
    print("| kind | merges | with a real conflict | conflicted files |\n|---|---|---|---|")
    for k in stats:
        n, c = stats[k]["merges"], stats[k]["conflicted"]
        print(f"| {k} | {n} | {c} ({100 * c / max(1, n):.0f}%) | {sum(files[k].values())} |")
    for k in stats:
        by = collections.Counter[str]()
        for f, n in files[k].items():
            by[bucket(f)] += n
        print(f"\nConflicted files, {k} merges, by kind: " + ", ".join(f"{b} {n}" for b, n in by.most_common()))
    print("\nscripts/ conflicts in merges of main into a lane, replayed against the split "
          f"({a.split[:12]}; hunks placed by function, as the docstring says):\n")
    print("| merge | file | conflicting hunk pairs | split files ours / theirs, (c') | avoided, (c') | avoided, (c'') |")
    print("|---|---|---|---|---|---|")
    split = covers.Split(REPO, a.split)
    avoided = {CP: 0, CPP: 0}
    for h, lane, mp, f in scripts:
        if f != covers.HUB:
            print(f"| {h[:12]} | {f} | - | file unchanged by the split | no | no |")
            continue
        base = g("merge-base", lane, mp)[1].strip()
        res: dict[str, str] = {}
        shown, count = "", 0
        for mode, near in ((CP, False), (CPP, True)):
            pairs = hub_pairs(split, base, lane, mp, near)
            left = [p for p in pairs if p[1] & p[2]]
            ok = bool(pairs) and not left
            avoided[mode] += ok
            res[mode] = ("yes" if ok else "no: " + "; ".join(sorted({", ".join(sorted(m.removeprefix("scripts/")
                         for m in p[1] & p[2])) for p in left})) if pairs else "unexplained: no touching hunks")
            if not near:
                shown = "; ".join(f"{' '.join(sorted(x.removeprefix('scripts/') for x in so))} / "
                                  f"{' '.join(sorted(x.removeprefix('scripts/') for x in st))}" for _w, so, st in pairs)
                count = len(pairs)
        print(f"| {h[:12]} | {f} | {count} | {shown} | {res[CP]} | {res[CPP]} |")
    hub = sum(1 for s in scripts if s[3] == covers.HUB)
    print(f"\nOf {len(scripts)} scripts/ conflicts, {hub} in the hub; the split would have avoided {avoided[CP]}"
          f" with (c') placement, {avoided[CPP]} with (c'').")


if __name__ == "__main__":
    main()
