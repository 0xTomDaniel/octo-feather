# gh977: the slot queue passes over a holder that never runs; manual grant and revoke stay consistent

Change: `octo-feather-slot` (rule: its --help, the queue; owner ruling 2026-11-14 #906). A holder no run started under by its grant's since + slot_bound_seconds (gate-budget.toml, default 1200) is passed over while the queue is non-empty: the head granted, the head's supervisor, the passed-over lane's supervisor and the director told; with the queue empty nothing is written. `revoke LANE` drops LANE's grant and queue place; a slot it frees (or one a check first sees free) goes to the head only after the grace, so a grant by hand inside the grace wins and the head stays queued. Every command settles both kinds first; `queue` settles again after appending. One-shot checks start at grant (queue non-empty, after the bound), at queue behind an unrun holder (at its since + bound), at a revoke freeing a slot (after the grace). Review findings on cd05e4a9 fixed here: notices sent in the session the head was queued from (each queue entry records its HERDR_SESSION; test `two_sessions`), and run-slots.md's Gotchas point to --help instead of restating it.

Smoke: .agents/skills/verify-octo-feather/features/run-slots.md (the recipe the drive below follows; no model run)
Smoke: .agents/skills/verify-octo-feather/SKILL.md (its stand-in list names the drive's stand-in `herdr`; the same drive)

## The drive

`.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive run-slots` at a6b96375: PASS, 22 cases, record 20261118T044043Z-da119200. New cases: queue-behind, revoke, revoke-status, freed-handed, requeue, revoke-again, grant-by-hand, grant-wins, passed-over. The stand-in `herdr`'s record of the real herdr-say's prompts, `freed-handed` (a revoke's free slot, granted a grace later) then `passed-over` (gh6, granted by hand inside the grace, starts no run within the 6 s bound):

```
agent prompt w9:p1 octo-feather-slot: the heavy slot is granted to lane gh7 until 2026-11-18T06:40:35Z (the slot free for the 2 s grace); run your heavy run now. --wait --until working --until idle --timeout 60000
agent prompt w1:p1 octo-feather-slot: heavy slot free for the 2 s grace, granted to lane gh7; queue left: none. --wait --until working --until idle --timeout 60000
agent prompt w8:p1 octo-feather-slot: the heavy slot is granted to lane gh8 until 2026-11-18T06:40:43Z (lane gh6 started no heavy run within the 6 s bound); run your heavy run now. --wait --until working --until idle --timeout 60000
agent prompt w6:p1 octo-feather-slot: lane gh6's heavy grant passed to lane gh8: no heavy run started under it within the 6 s bound; to run, ask the director: octo-feather-slot queue gh6 --kind heavy. --wait --until working --until idle --timeout 60000
agent prompt w1:p1 octo-feather-slot: heavy slot passed over lane gh6 (no run within the 6 s bound) to lane gh8; queue left: none. --wait --until working --until idle --timeout 60000
```

`grant-wins`: past the grace after `revoke-again` and `grant-by-hand`, status showed gh6 the holder, gh8 still queued, no prompt sent.

## Tests

`just check-tests tests/gate/kit/test_slot.py` (scratch XDG_STATE_HOME): 14 passed. New: passed_over, unused_alone (queue empty: heavy.json's bytes and mtime unchanged, no queue file), revoked, queued_late (the queue command hands over at once; a status hands over whose one-shot is far off), two_sessions; old_reads_new and new_reads_old extended (main's 53dacfca command reads the freed marker's and the pass-over's state, grants inside a free slot's grace and wins). Against cd05e4a9's command the new scenarios fail (two_sessions: both notices recorded in session `default`, not `sb`).

## Demo (scratch XDG_STATE_HOME with lane records gh7, gh8 and director.toml; a stand-in herdr-say first on PATH; OCTO_FEATHER_SLOT_GRACE=3; no Herdr variables)

```
$ OCTO_FEATHER_ROLE=director scripts/octo-feather-slot grant gh7 --kind heavy
granted: heavy slot to lane gh7 (granted 2026-11-18T04:40:03Z by director, expires 2026-11-18T06:40:03Z)
$ OCTO_FEATHER_ROLE=director scripts/octo-feather-slot queue gh8 --kind heavy
queued: lane gh8 for the heavy slot, position 1
$ OCTO_FEATHER_ROLE=director scripts/octo-feather-slot revoke gh7 --kind heavy
revoked: heavy slot of lane gh7
the heavy slot passes to lane gh8 after the 3 s grace
$ scripts/octo-feather-slot status
heavy (1 slot(s), over heavy_items 30 items; gate runs over heavy_items items, fast-map, timing):
  holder: none
  run holding it now: none
  queue: 1. gh8 (queued 2026-11-18T04:40:03Z by director)
  free since 2026-11-18T04:40:03.888074Z: to the queue's head after the 3 s grace
eval (1 slot(s); model evals through octo-feather-qa):
  holder: none
  run holding it now: none
  queue: none
$ sleep 4; scripts/octo-feather-slot status
heavy (1 slot(s), over heavy_items 30 items; gate runs over heavy_items items, fast-map, timing):
  holder: gh8 (granted 2026-11-18T04:40:06Z by queue, expires 2026-11-18T06:40:06Z)
  run holding it now: none
  queue: none
eval (1 slot(s); model evals through octo-feather-qa):
  holder: none
  run holding it now: none
  queue: none
$ cat "$DEMO/said"   # the stand-in herdr-say's record
--timeout 60 w8:p1 octo-feather-slot: the heavy slot is granted to lane gh8 until 2026-11-18T06:40:06Z (the slot free for the 3 s grace); run your heavy run now.
--timeout 60 w1:p1 octo-feather-slot: heavy slot free for the 3 s grace, granted to lane gh8; queue left: none.
```
