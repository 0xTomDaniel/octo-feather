# gh503 #550: the fast tier's map survives a red item; just fast-list (gate-tiers)

Change: `scripts/octo-feather-gate map` maps only the items the run's junit reports passed, naming the rest `not_passed`; `just fast-map` writes the map whatever the run's result and exits as the run did; `just fast-list` prints the selection with a count, running nothing (commit dca08f6). The verify skill's gate-tiers drive gains cases fast-list, fast-map-red, fast-list-red (commit 3cc305d).

Smoke: .agents/skills/verify-octo-feather/features/gate-tiers.md (the three new sub-features; run below)
Smoke: .agents/skills/verify-octo-feather/features/README.md (index line; run below)
Removed: nothing.

## Recorded live run at head 3cc305d

Clean tree at 3cc305d (gh503-t5), helper defaults under /tmp, no model, no network:

```
.agents/skills/verify-octo-feather/scripts/verify-octo-feather run --unreachable-exit 77 gate-tiers
```

Exit 0, `verify-octo-feather: run PASS`; every case PASS: pilot, checkpoint, fast, fast-map, fast-one-script, fast-list, fast-map-red, fast-list-red. Evidence records: 20261104T221326Z-c6199f34 (quality#acceptance-fast-affected), 20261104T221326Z-95434a92, 20261104T221326Z-8385cbee, 20261104T221326Z-350145ef.

What the new cases showed:

- fast-list, after a change to scripts/fixture-a: `fast: tests/a.sh: recorded coverage reaches scripts/fixture-a`, `fast: tests/d.sh: no recorded coverage in the map at 0a943ae6f8cf: always selected`, `fast: selected 3 of 5 gate items (1 static, 2 of 4 test items)`; FAST_RAN empty: nothing ran.
- fast-map-red, with tests/e.sh red: `1 failed, 4 passed`, then `fast-map: 3 test items mapped at 3f2fc5067154` and `fast-map: tests/e.sh did not pass: left out of the map, always selected`; exit 1.
- fast-list-red, nothing changed: `fast: tests/e.sh: did not pass the mapping run at 3f2fc5067154, so unmapped: always selected`, `fast: selected 3 of 6 gate items (1 static, 2 of 5 test items)`.
