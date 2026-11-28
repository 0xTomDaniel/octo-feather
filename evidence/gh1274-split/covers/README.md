# Covers from coverage, and the stale counts (a), (b), (c) (#1334)

The lever is `covers.py` (its docstring owns the rule: covers = the Python files coverage names plus every declared
path coverage cannot see). Run from the kit root, under the kit's uv venv:

    L="uv run --locked --offline --no-sync python3 evidence/gh1274-split/covers"

## Regenerate qc.toml's covers on the current tree (one command; a second run changes nothing)

    just fast-map                 # the coverage map for HEAD, if none from HEAD or an ancestor is current
    $L/covers.py regen            # measure (tags, the map, tagged items outside it, demo commands), write qc.toml, check

`regen` keeps its measure as `measure-<head12>.json` here; `$L/covers.py write measure-<head12>.json` rewrites qc.toml
from a kept one without running anything. Both end with `check`, which exits 1 naming each criterion that lost a
declared path coverage cannot see (`$L/covers.py check [--declared REF]` alone). This ticket's run took the declared
covers from the tree before 91d3c2a8 had replaced them:

    $L/covers.py write measure-e9e16e570896.json --declared e9e16e570896c680abe3ceb76bcd177eb1f5d432

check-before.txt: that check on 91d3c2a8's qc.toml, exit 1 (171 paths lost, 63 criteria).

## The counts (counts.md)

    $L/covers.py fetch-prs prs.json   # the last 60 merged PRs as of the run (refetch on a newer main)
    git clone -q --no-checkout <kit clone> /tmp/main-tree && git -C /tmp/main-tree checkout -q --detach <main>
    (cd /tmp/main-tree && uv sync --locked --offline && pnpm install --frozen-lockfile --offline)
    $L/covers.py measure /tmp/main-tree measure-main-<main12>.json --map <git common dir>/octo-feather/fast-map/<main>.json
    $L/covers.py counts --main <main> --b measure-main-<main12>.json --split <split head> --c measure-<head12>.json \
        --prs prs.json --pr 1246

- (a) covers as declared in qc.toml at main; (b) covers from coverage on main's tree; (c) from coverage on the split
  tree; (b) and (c) keep each declared path coverage cannot see. Built criteria: the status files at each set's ref.
- Stale: a built criterion with a covers entry one of whose paths a PR's changed file equals or sits under (git
  pathspec, as `octo-feather-spec-status` judges it). A PR's files: `git diff --name-only <merge>^1 <merge>`.
- (c') as (c), each pre-split PR's change to `scripts/octo-feather-lane` placed on the split modules its hunks land in
  (covers.py, class Split): a hunk none of whose lines is placed goes to the dispatcher. (c'') the same, such a hunk
  placed by the nearest unchanged line around it that one split file holds (its module header or help chunk), else
  dropped.
- Lane-command files and the pairs stale through them alone, the top triggers per set: printed by `counts`.
- p90 nearest rank, as /home/exedev/scratch/change2/w1/stale.py.

## Why (b) exceeds (a) (why.md)

    $L/why.py probe /tmp/main-tree measure-main-<main12>.json probe-main-<main12>.json --main <main>
    $L/why.py report measure-main-<main12>.json probe-main-<main12>.json --prs prs.json --main <main>

## Collisions (collide.md)

    $L/collide.py fetch prs.json prs-overlap.json.gz
    $L/collide.py report prs.json prs-overlap.json.gz --split <split head> --exclude 79

## Before and after #1335 (counts.md, its last section)

    $L/covers.py counts --main f7f16367 --b measure-main-f7f163676186.json --split e9e16e57 --c measure-e9e16e570896.json \
        --prs prs.json --pr 1246      # before: the table above, reproduced
    $L/covers.py counts --main f7f16367 --b measure-main-f7f163676186.json --split <#1335 head> \
        --c measure-<#1335 head12>.json --prs prs.json --pr 1246      # after: counts-after-1335.md
    $L/collide.py report prs.json prs-overlap.json.gz --split <#1335 head> --exclude 79   # collide-after-1335.md

On a split tree holding #1335's shared modules (../tables.py SHARED), Split places merge_ask.py's hunks too, among
merge_ask.py and those modules alone.
