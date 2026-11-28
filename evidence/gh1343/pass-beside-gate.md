# Parity pass beside a full gate (#1363): measurement, partial

Ticket #1363 asked for one `just check` alone and one beside a running parity pass. Each needs its wall time,
CPU time, the box load (uptime) and the pass's own CPU. Box: 8 vCPU. Head: gh1343-1363, 15c587a7 (alone) and
3d2d63e4 (beside). The heavy slot was granted to lane gh1343 until 14:47Z.

## `just check` alone (no pass running)

- 2026-11-28T12:54:36Z to 13:07:32Z.
- Load before: 17.73, 20.52, 25.28 (1, 5, 15 min). Load after: 27.64, 33.86, 31.46.
- Other runs on the box: the #1362 survey's two lever runs at nice 19 (check-dashes, check-decision-log, live
  through the whole run), and another lane's basedpyright at nice 19.
- `just check`: 776.22 s wall, 1876.28 s user + 699.57 s sys = 2575.85 s CPU (331%), exit 1. 590 passed,
  1 failed, 5 skipped.
- The one failure: test_post_merge_pass_capped. Owed cases were judged by second-resolution times. 3d2d63e4
  fixes it: owed is now judged by the pass each case ran in.

## `just check` beside a pass: not measured

- 13:09:14Z: a full pass (115 cases) started in a scratch clone of this head (`octo-feather-lane post-merge`,
  real `systemd-run --user` unit, nice 19, ionice idle). Unit octo-feather-parity-pass-ef35cae321e3.
- 13:09:39Z to 13:10:41Z: `just check` ran 61.64 s, then octo-feather-slot refused it (exit 75), nothing run
  past the static checks. The heavy slot had passed from gh1343 to gh1229 by the queue's grace rule (granted
  13:08:28Z) in the gap after the first run. The fix commit took over the 60 s grace.
- Load: 29.06, 31.53, 30.84 before; 55.79, 38.35, 33.21 after.
- The pass's own CPU (systemd CPUUsageNSec): 10.27 s at 13:09:39Z, 16.57 s at 13:10:41Z. That is 6.3 s of CPU
  in 62 s of wall, about 0.1 vCPU, with load near 30 on 8 vCPU. Its first case, accepted, had not finished
  after 100 s. The 3-case pass earlier the same day took 188 s wall and 170 s CPU on a quieter box.
- The pass was then stopped (`systemctl --user stop`). Its stop hook recorded it failed with all 115 cases
  owed and removed its worktree. The lever killed by TERM left its kit copy (parity-kit-*) under the clone's
  .git/octo-feather.

## What the numbers support

There is no beside-a-pass gate time yet, so no delta to report. What the numbers do show: on a box already at
load about 30, the pass at nice 19 and ionice idle got about 0.1 vCPU. 'Keeps its time' needs the second run,
with a heavy slot held through both runs back to back, so the queue's 60 s grace does not pass it on. Until
then no limit is supported by measurement. The supervisor owns any spec clarification.
