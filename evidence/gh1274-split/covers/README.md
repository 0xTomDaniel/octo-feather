# Covers from coverage, and the stale counts (a), (b), (c) (#1334)

The lever is `covers.py` (its docstring owns the rule). Run from the kit root, under the kit's uv venv:

    L="uv run --locked --offline --no-sync python3 evidence/gh1274-split/covers/covers.py"

## Regenerate qc.toml's covers on the current tree (one command; a second run changes nothing)

    just fast-map                 # the coverage map for HEAD, if none from HEAD or an ancestor is current
    $L regen                      # measure (tags, the map, tagged items outside it, demo commands) and write qc.toml

`regen` keeps its measure as `measure-<head12>.json` here; `$L write measure-<head12>.json` rewrites qc.toml from a
kept one without running anything.

## The counts

    $L fetch-prs prs.json         # the last 60 merged PRs as of the run (refetch on a newer main)
    git clone -q --no-checkout <kit clone> /tmp/main-tree && git -C /tmp/main-tree checkout -q --detach <main>
    (cd /tmp/main-tree && uv sync --locked --offline && pnpm install --frozen-lockfile --offline)
    $L measure /tmp/main-tree measure-main-<main12>.json --map <git common dir>/octo-feather/fast-map/<main>.json
    $L counts --main <main> --b measure-main-<main12>.json --split <split head> --c measure-<head12>.json \
        --prs prs.json --pr 1246 > counts.md

- (a) covers as declared in qc.toml at main; (b) covers from coverage on main's tree; (c) covers from coverage on the
  split tree. Built criteria: the status files at each set's ref.
- Stale: a built criterion with a covers entry one of whose paths a PR's changed file equals or sits under (git
  pathspec, as `octo-feather-spec-status` judges it). A PR's files: `git diff --name-only <merge>^1 <merge>`.
- (c') as (c), with each pre-split PR's change to `scripts/octo-feather-lane` placed on the split modules its hunks
  land in (`covers.py`, class Split): the hub's file name alone says nothing on the split tree, where it is a
  dispatcher.
- p90 nearest rank, as /home/exedev/scratch/change2/w1/stale.py.
