# gh976: the slot queue, the slot passing to the head when the holder's run ends

Change: `octo-feather-slot queue LANE --kind K` (director only), `status` listing each kind's queue, and the hand-over: when `hold` releases its lock it records the run's end on the lane's grant and starts one detached `settle --kind K --after GRACE`, which passes a grant whose run ended a grace ago (its lane not running now) to the queue's head and tells the head's supervisor and the director through herdr-say (rule: `octo-feather-slot --help`, owner ruling 2026-11-14 #906). A lane refused for want of a grant is told `queue` when the kind is full, `grant` when free. gate-budget.toml gains slot_grace_seconds (octo-feather-lane's budget check reads it as a slot key).

Smoke: .agents/skills/verify-octo-feather/features/run-slots.md (the recipe the drive below follows; no model run)

## The drive

`.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive run-slots` at 00bc2047: PASS, 13 cases (grant-not-director, refused, grant, status, queue-not-director, queue, queue-status, not-before-run, granted, released, handed, refused-queue, queue-free); evidence record 20261118T033023Z-1cb54a. Its `handed` observation, the stand-in `herdr`'s record of the real herdr-say's two prompts:

```
agent prompt w8:p1 octo-feather-slot: the heavy slot is granted to lane gh8 until 2026-11-18T05:30:17Z (lane gh7's run ended, no run within the 2 s grace); run your heavy run now. --wait --until working --until idle --timeout 60000
agent prompt w1:p1 octo-feather-slot: heavy slot passed from lane gh7 to lane gh8; queue left: none. --wait --until working --until idle --timeout 60000
```

A first drive attempt had a stand-in `herdr-say` only; the detached check, started under `just` (whose PATH puts the kit's herdr-say first), ran the real herdr-say against live Herdr: both prompts answered `agent_not_found` for w8:p1 and w1:p1, nothing delivered. The drive now stands in at `herdr`.

## Demo (scratch XDG_STATE_HOME with lane records gh7, gh8 and director.toml; a stand-in herdr-say first on PATH; OCTO_FEATHER_SLOT_GRACE=3)

```
$ OCTO_FEATHER_ROLE=director scripts/octo-feather-slot grant gh7 --kind heavy
granted: heavy slot to lane gh7 (granted 2026-11-18T03:54:19Z by w1:p1, expires 2026-11-18T05:54:19Z)
$ OCTO_FEATHER_ROLE=director scripts/octo-feather-slot queue gh8 --kind heavy
queued: lane gh8 for the heavy slot, position 1
$ scripts/octo-feather-slot status
heavy (1 slot(s), over heavy_items 30 items; gate runs over heavy_items items, fast-map, timing):
  holder: gh7 (granted 2026-11-18T03:54:19Z by w1:p1, expires 2026-11-18T05:54:19Z)
  run holding it now: none
  queue: 1. gh8 (queued 2026-11-18T03:54:20Z by w1:p1)
eval (1 slot(s); model evals through octo-feather-qa):
  holder: none
  run holding it now: none
  queue: none
$ (echo; sleep 1) | OCTO_FEATHER_ROLE=implementer HERDR_PANE_ID=w9:p3 OCTO_FEATHER_PARENT=w9:p1 scripts/octo-feather-slot hold --kind heavy --items 31   # gh7's run, its stdin then closing
held: the heavy slot for lane gh7, run pid 1099537 of lane gh7 since 2026-11-18T03:54:20Z, 31 items
$ sleep 5; scripts/octo-feather-slot status
heavy (1 slot(s), over heavy_items 30 items; gate runs over heavy_items items, fast-map, timing):
  holder: gh8 (granted 2026-11-18T03:54:24Z by queue, expires 2026-11-18T05:54:24Z)
  run holding it now: none
  queue: none
eval (1 slot(s); model evals through octo-feather-qa):
  holder: none
  run holding it now: none
  queue: none
$ cat said   # the stand-in herdr-say's record
--timeout 60 w8:p1 octo-feather-slot: the heavy slot is granted to lane gh8 until 2026-11-18T05:54:24Z (lane gh7's run ended, no run within the 3 s grace); run your heavy run now.
--timeout 60 w1:p1 octo-feather-slot: heavy slot passed from lane gh7 to lane gh8; queue left: none.
```
