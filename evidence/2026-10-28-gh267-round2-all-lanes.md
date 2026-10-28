# gh267 round 2: file every due correction subject, whichever lane reflects (2026-10-28)

Review round 2 B1: `file_corrections` filtered due subjects to the current lane/director, so a class whose findings sit only in other lanes never filed. Fix: `scripts/octo-feather-lane` `file_corrections(lanes)` walks every owner of every due subject (owner rule unchanged: the latest lane finding's record repository, else the kit's).

## Deterministic proof

`tests/lane-correction.sh` (stub pi, offline fake gh), new cases, red before the fix, green after:

- archived gh1, gh2 one `dup-rule` finding each; `archive gh3` (unrelated) prints `correction lane: filed 901 in github-issues o/t for dup-rule (2 findings; ...)`, the issue in o/t quotes both; a further `archive gh4` files nothing.
- archived gh1, gh2 one `stale-check` each; `reflect --director` routing it files 901 in o/t, body `Route: agents/code-reviewer.md Rules`.

## Demo (stub pi, fake gh first on PATH)

Seed /tmp/gh230-demo6: archive/gh1, archive/gh2 (repository o/t, one dup-rule finding each), gh3 open, no log. `XDG_STATE_HOME=/tmp/gh230-demo6 scripts/octo-feather-lane archive gh3`:

```
correction lane: filed 901 in github-issues o/t for dup-rule (2 findings; route: none given by a reflection)
archived: /tmp/gh230-demo6/octo-feather/lanes/archive/gh3.toml sha256=...
exit 0
```

## Stub-pi drive (not live)

`verify-octo-feather drive correction-lane` (now the reviewer's case: gh900, gh901 archived, gh902 archived by the drive) with stub pi first on PATH, pre-commit tree: PASS file-live, `filed 901 in github-issues scratch/target for duplicated-rule (2 findings ...)`. Its record 20261028T060704Z-3f5c68fb landed in the box's evidence store against 768726f: a stub-pi record, not live evidence; do not count it.

## Live runs owed

1. `verify-octo-feather launch && verify-octo-feather drive correction-lane` (live reflectors, tracker faked).
