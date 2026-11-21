# gh1210: just fast takes no heavy slot, on a capped worker count

Change: tests/gate/heavy_slot.py asks no heavy slot for a run holding no e2e item on no more workers than fast_workers (gate-budget.toml); `just fast` runs on that cap (quality #recipes-static-first, #acceptance-fast-slot-free; owner ruling 2026-11-21 on #1186).

Smoke: .agents/skills/verify-octo-feather/features/run-slots.md (its `just fast` line, run live in lane gh1186's implementer pane, no model run)

## The smoke

In lane gh1186's worktree (implementer pane, lane holding no heavy grant), at e9ca7ef5, the one-script fast set (66 items: `octo-feather-gate select` for a one-line change to scripts/octo-feather-handoff at the map head 19f970a6e8ed, its e2e items at this head dropped) on the cap:

```
GATE_WORKERS=2 just check-tests <66 ids>
heavy slot: not needed: fast tier, 2 workers (cap 2)
```

It started at once, asked no slot. That run stopped on check-behavior-smoke (this file missing); the green rerun and the cap's measurements: the #1210 PR's Validation.
