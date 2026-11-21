# gh1210: just fast takes no heavy slot, on a capped worker count

Change: tests/gate/heavy_slot.py asks no heavy slot for a run holding no e2e item on no more workers than fast_workers (gate-budget.toml); `just fast` runs on that cap (quality #recipes-static-first, #acceptance-fast-slot-free; owner ruling 2026-11-21 on #1186).

Smoke: .agents/skills/verify-octo-feather/features/run-slots.md (its `just fast` line, run live in lane gh1186's implementer pane, no model run)

## The smoke

In lane gh1186's worktree (implementer pane, lane holding no heavy grant), at e9ca7ef5, the one-script fast set (66 items: `octo-feather-gate select` for a one-line change to scripts/octo-feather-handoff at the map head 19f970a6e8ed, its e2e items at this head dropped) on the cap:

```
GATE_WORKERS=2 just check-tests <66 ids>
heavy slot: not needed: fast tier, 2 workers (cap 2)
```

It started at once, asked no slot. That run stopped on check-behavior-smoke (this file missing). Rerun green at f755d3e6 in a second worktree of it (/tmp/w1210-meas): `heavy slot: not needed: fast tier, 2 workers (cap 2)`, 66 passed in 68.8 s.

## The cap (8 vCPU box, f755d3e6, trend lines of check-runs.jsonl)

Commands: full gate `just check` (8 workers, the lane's heavy grant) in the lane worktree; fast runs `GATE_WORKERS=C just check-tests <ids>` (what `just fast` runs after select) in /tmp/w1210-meas with fast_workers = C, started 40 s after the full gate (past its static checks). One-script set: 66 items (select for a one-line change to scripts/octo-feather-handoff at the map head 19f970a6e8ed, e2e at this head dropped); worst case: 321 items (select at this head: justfile changed, every non-e2e item). Full gates here ran 7 old slot tests red (fixed after: their scratch suites hold no e2e item), the fast worst case 4 of them; timing kept. load1 at start / end.

| run | cap 2 | cap 3 |
| --- | --- | --- |
| one-script fast, alone | 68.3 s (6.76 / 5.70) | 56.5 s (4.08 / 6.31) |
| one-script fast, beside a full gate | 131.9 s (12.73 / 14.42) | 104.6 s (11.88 / 16.34) |
| worst-case fast, alone | 372.1 s (4.29 / 2.23) | 307.8 s (1.60 / 5.92) |
| worst-case fast, beside a full gate | 528.2 s (14.39 / 3.33) | 424.4 s (8.59 / 10.05) |
| full gate beside the one-script fast | 379.9 s (5.68 / 13.48) | 413.4 s (5.01 / 9.95) |
| full gate beside the worst-case fast | 392.4 s (10.9 / 15.27) | 407.4 s (3.15 / 15.98) |

Full gate alone: 412.9 s (3.04 / 6.08). Pick: 3. The full gate's wall time beside either fast run stays within its alone time (356 to 413 s, other lanes' load on the box moving it), so a third worker costs it nothing measurable, while cap 3 cuts the fast tier by 17 to 20 %, alone or beside. Not measured: several fast runs at once beside one full gate.
