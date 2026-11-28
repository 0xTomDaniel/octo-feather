#!/usr/bin/env python3
"""collide.py: how often a merged PR touched a file another PR open at the same time also touched, before the split
and after it (#1334, director's addition). Run from the kit root: `uv run --locked --offline --no-sync python3
evidence/gh1274-split/covers/collide.py ...`; covers.py beside it owns the hub placement (Split).

  collide.py fetch PRS ALL     every PR (any state) whose open interval overlaps one of PRS's (prs.json, the last 60
                               merged): number, state, createdAt, mergedAt, closedAt, merge commit, head; each one's
                               changed files and base: a merged one's `git diff <merge>^1 <merge>`, any other's head
                               fetched (refs/collide/<n>) and diffed from its merge base with origin/main. ALL: JSON.
  collide.py report PRS ALL --split REF [--exclude N]...
                               Markdown: of PRS, how many collided (a file in common with another PR whose interval
                               overlaps), before (files as recorded) and after (the hub's hunks placed on the split
                               modules of REF: (c'), unplaced to the dispatcher; (c''), by nearest context or dropped);
                               all files and scripts/ only; then per file the top colliders. --exclude: a PR left
                               out (an old open PR whose diff from today's merge base is not what it touched then).
Interval: createdAt to mergedAt, else closedAt, else the fetch time (still open).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, cast

sys.path.insert(0, str(Path(__file__).resolve().parent))
import covers  # noqa: E402


def end(p: dict[str, Any], now: str) -> str:
    return str(p.get("mergedAt") or p.get("closedAt") or now)


def fetch(prs_file: Path, out: Path) -> None:
    repo = Path.cwd()
    now = dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    prs = cast("list[dict[str, Any]]", json.loads(prs_file.read_text()))
    first = min(str(p["mergedAt"]) for p in prs)
    every = cast("list[dict[str, Any]]", json.loads(covers.run(
        ["gh", "pr", "list", "--state", "all", "--limit", "1000", "--json",
         "number,state,createdAt,mergedAt,closedAt,mergeCommit,headRefOid"], repo)))
    # any PR open at some point since the earliest of PRS was opened: its interval can overlap one of PRS's
    start = min(str(p["createdAt"]) for p in every if p["number"] in {q["number"] for q in prs})
    keep = [p for p in every if end(p, now) >= start]
    for p in keep:
        n = p["number"]
        oid = str(cast("dict[str, Any]", p.get("mergeCommit") or {}).get("oid") or "")
        if p.get("mergedAt") and oid and not subprocess.run(["git", "cat-file", "-e", oid], cwd=repo,
                                                             check=False).returncode:
            p["base"], p["head"] = f"{oid}^1", oid
        else:
            got = subprocess.run(["git", "fetch", "-q", "origin", f"pull/{n}/head"], cwd=repo, check=False).returncode
            head = "" if got else covers.run(["git", "rev-parse", "-q", "--verify", "FETCH_HEAD"], repo, check=False).strip()
            if not head:
                p["files"] = None
                continue
            p["base"] = covers.run(["git", "merge-base", head, "origin/main"], repo, check=False).strip() or f"{head}^1"
            p["head"] = head
        p["files"] = covers.git(repo, "diff", "--name-only", str(p["base"]), str(p["head"])).split()
    out.write_text(json.dumps({"fetched": now, "first_merged": first, "prs": keep}, indent=1) + "\n")
    print(f"collide: {len(keep)} PRs into {out}")


def report(prs_file: Path, all_file: Path, split_ref: str, exclude: list[int]) -> None:
    repo = Path.cwd()
    data = cast("dict[str, Any]", json.loads(all_file.read_text()))
    now = str(data["fetched"])
    every = {int(p["number"]): p for p in cast("list[dict[str, Any]]", data["prs"])
             if p.get("files") is not None and int(p["number"]) not in exclude}
    ours = [int(p["number"]) for p in cast("list[dict[str, Any]]", json.loads(prs_file.read_text()))]
    split = covers.Split(repo, split_ref)
    views: dict[str, dict[int, set[str]]] = {"before": {}, "c'": {}, "c''": {}}
    for n, p in every.items():
        fs = set(cast("list[str]", p["files"]))
        views["before"][n] = fs
        for v, near in (("c'", False), ("c''", True)):
            views[v][n] = ((fs - {covers.HUB}) | split.place(p["head"], near=near, base=p["base"])
                           if covers.HUB in fs else fs)

    def overlap(a: int, b: int) -> bool:
        pa, pb = every[a], every[b]
        return str(pa["createdAt"]) < end(pb, now) and str(pb["createdAt"]) < end(pa, now)

    print(f"PRs measured: the {len(ours)} merged in prs.json; others: every PR whose interval overlaps theirs "
          f"({len(every)} with files, fetched {now}); left out: {exclude or 'none'}.\n")
    print("| files | view | PRs of the 60 that collided | median colliding PRs per PR | collision pairs (PR, other "
          "PR) |\n|---|---|---|---|---|")
    tops: dict[tuple[str, str], dict[str, set[tuple[int, int]]]] = {}
    for scope in ("all", "scripts/"):
        for v, f in views.items():
            per_file: dict[str, set[tuple[int, int]]] = {}
            hit_prs = 0
            counts: list[int] = []
            pairs = 0
            for n in ours:
                if n not in f:
                    continue
                mine = {x for x in f[n] if scope == "all" or x.startswith(scope)}
                others = 0
                for m in every:
                    if m == n or not overlap(n, m):
                        continue
                    common = mine & f[m]
                    if common:
                        others += 1
                        for x in common:
                            per_file.setdefault(x, set[tuple[int, int]]()).add((n, m))
                hit_prs += others > 0
                counts.append(others)
                pairs += others
            counts.sort()
            med = counts[len(counts) // 2] if counts else 0
            print(f"| {scope} | {v} | {hit_prs} | {med} | {pairs} |")
            tops[(scope, v)] = per_file
    for v in views:
        per_file = tops[("all", v)]
        print(f"\nTop colliding files, {v}: | file | collision pairs through it | PRs of the 60 colliding through it "
              "|\n|---|---|---|")
        for x, s in sorted(per_file.items(), key=lambda kv: (-len(kv[1]), kv[0]))[:20]:
            print(f"| {x} | {len(s)} | {len({a for a, _b in s})} |")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("fetch")
    s.add_argument("prs", type=Path)
    s.add_argument("all", type=Path)
    s = sub.add_parser("report")
    s.add_argument("prs", type=Path)
    s.add_argument("all", type=Path)
    s.add_argument("--split", required=True)
    s.add_argument("--exclude", type=int, action="append", default=[])
    a = ap.parse_args()
    if a.cmd == "fetch":
        fetch(a.prs, a.all)
    else:
        report(a.prs, a.all, a.split, a.exclude)


if __name__ == "__main__":
    main()
