#!/usr/bin/env python3
"""collide.py: how often a merged PR touched a file another PR open at the same time also touched, before the split
and after it (#1334, director's addition). Run from the kit root: `uv run --locked --offline --no-sync python3
evidence/gh1274-split/covers/collide.py ...`; covers.py beside it owns the hub placement (Split).

  collide.py fetch PRS ALL     every PR (any state) whose open interval overlaps one of PRS's (prs.json, the last 60
                               merged): number, state, createdAt, mergedAt, closedAt, merge commit, head; each one's
                               changed files and base: a merged one's `git diff <merge>^1 <merge>`, any other's head
                               fetched (FETCH_HEAD, no ref written) and diffed from its merge base with origin/main.
                               ALL: gzipped JSON, as its file lists hold real tracked paths that check-refs'
                               retired-words scan would read as kit wording (a tests/parity/check-refs/ patch name).
  collide.py report PRS ALL --split REF [--exclude N]...
                               Markdown: of PRS, how many overlapped (a file in common with another PR whose interval
                               overlaps), before (files as recorded) and after (the hub's hunks placed on the split
                               modules of REF: (c'), unplaced to the dispatcher; (c''), by nearest context or dropped);
                               all files and scripts/ only; then per file the top overlapping files. --exclude: a PR left
                               out (an old open PR whose diff from today's merge base is not what it touched then).
Interval: createdAt to mergedAt, else closedAt, else the fetch time (still open).
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import gzip
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import covers  # noqa: E402
import gh_records  # noqa: E402  # the gh PR records, validated at the edge


def fetch(prs_file: Path, out: Path) -> None:
    repo = Path.cwd()
    now = dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    prs = gh_records.merged_list(prs_file.read_text(), str(prs_file))
    first = min(p.merged_at for p in prs)
    every = gh_records.any_list(covers.run(
        ["gh", "pr", "list", "--state", "all", "--limit", "1000", "--json",
         "number,state,createdAt,mergedAt,closedAt,mergeCommit,headRefOid"], repo), "gh pr list --state all")
    # any PR open at some point since the earliest of PRS was opened: its interval can overlap one of PRS's
    ours = {q.number for q in prs}
    start = min(p.created_at for p in every if p.number in ours)
    keep: list[gh_records.AnyPR] = []
    for p in (p for p in every if p.end(now) >= start):
        if p.merged_at and p.merge and not subprocess.run(["git", "cat-file", "-e", p.merge], cwd=repo,
                                                          check=False).returncode:
            base, head = f"{p.merge}^1", p.merge
        else:
            got = subprocess.run(["git", "fetch", "-q", "origin", f"pull/{p.number}/head"], cwd=repo,
                                 check=False).returncode
            head = "" if got else covers.run(["git", "rev-parse", "-q", "--verify", "FETCH_HEAD"], repo,
                                             check=False).strip()
            if not head:
                keep.append(p)
                continue
            base = covers.run(["git", "merge-base", head, "origin/main"], repo, check=False).strip() or f"{head}^1"
        files = tuple(covers.git(repo, "diff", "--name-only", base, head).split())
        keep.append(dataclasses.replace(p, base=base, head=head, files=files))
    text = gh_records.Overlap(now, first, tuple(keep)).dumps()
    out.write_bytes(gzip.compress(text.encode(), mtime=0))
    print(f"collide: {len(keep)} PRs into {out}")


def report(prs_file: Path, all_file: Path, split_ref: str, exclude: list[int]) -> None:
    repo = Path.cwd()
    data = gh_records.overlap(gzip.decompress(all_file.read_bytes()), str(all_file))
    now = data.fetched
    every = {p.number: p for p in data.prs if p.files is not None and p.number not in exclude}
    ours = [p.number for p in gh_records.merged_list(prs_file.read_text(), str(prs_file))]
    split = covers.Split(repo, split_ref)
    views: dict[str, dict[int, set[str]]] = {"before": {}, "c'": {}, "c''": {}}
    for n, p in every.items():
        fs = set(p.files or ())
        views["before"][n] = fs
        ma = "scripts/merge_ask.py"   # #1335: on a tree with the shared modules, merge_ask.py's hunks placed too
        for v, near in (("c'", False), ("c''", True)):
            views[v][n] = ((fs - {covers.HUB}) | split.place(str(p.head), near=near, base=p.base)
                           if covers.HUB in fs else fs)
            if split.helpers and ma in fs:
                views[v][n] = (views[v][n] - {ma}) | split.place(str(p.head), near=near, base=p.base, path=ma)

    def overlap(a: int, b: int) -> bool:
        pa, pb = every[a], every[b]
        return pa.created_at < pb.end(now) and pb.created_at < pa.end(now)

    print(f"PRs measured: the {len(ours)} merged in prs.json; others: every PR whose interval overlaps theirs "
          f"({len(every)} with files, fetched {now}); left out: {exclude or 'none'}.\n")
    print("| files | view | PRs of the 60 that overlapped | median overlapping PRs per PR | overlap pairs (PR, other "
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
        print(f"\nTop overlapping files, {v}: | file | overlap pairs through it | PRs of the 60 overlapping through it "
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
