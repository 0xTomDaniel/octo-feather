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

`check` with no flag compares with qc.toml at HEAD's merge base with the default branch (`octo-feather-gate base`);
`write` and `regen` also compare the written file with the declarations they read before writing. check-before.txt:
`check`, no flags, in a clone at 91d3c2a8: exit 1 (171 paths lost, 63 criteria).

gh PR JSON (`gh pr list`, `gh pr view`, prs.json, prs-overlap.json.gz) is read only through gh_records.py: validated
with the pinned jsonschema, unknown fields rejected, into typed records.

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

## Overlap and conflicts (collide.md)

    $L/collide.py fetch prs.json prs-overlap.json.gz
    $L/collide.py report prs.json prs-overlap.json.gz --split <split head> --exclude 79
    $L/conflicts.py --since 2026-11-12 --split <split head>    # after git fetch origin
