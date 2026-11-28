# gh1348: lane start refuses on the usage course and on the carried reading

Change: `octo-feather-lane start` (scripts/lane_brake.py, scripts/start_lane.py) refuses a new lane when a weekly
window's course passes the reserve line, and, with the usage unread, when the week's last stored reading carried
forward does; OCTO_FEATHER_NOW sets now on the unread and carried paths, said in the line (`octo-feather-lane
--help`, start). The verify skill's lane-start feature and drive gain the `usage` and `carried` cases. No role file
changes.

Smoke: .agents/skills/verify-octo-feather/features/lane-start.md (usage and carried cases, and the carried gotcha; the drive below follows it)

## verify-octo-feather run lane-start at head e4127f9d

`.agents/skills/verify-octo-feather/scripts/verify-octo-feather run --unreachable-exit 77 lane-start` (the qc.toml
demo for each lane-start criterion): every case PASS, `drive lane-start PASS`, `run PASS`, exit 0. Evidence records:
20261128T094833Z-3f2bb498 (issue-lifecycle#acceptance-lane-start-usage), 20261128T094834Z-d376a0e4
(issue-lifecycle#acceptance-lane-start-carried), and the pilot's criteria (clear 20261128T094833Z-fbc708d6, unread
20261128T094833Z-4a63e3d1) still PASS. Testkit Herdr, systemd and fake gh first on PATH, the brake's route the testkit
provider replaying tests/gate/kit/fixtures/lane-brake, scratch HOME, state, Pi config and target; no live Herdr,
GitHub or model route.

- `usage`: `usage_reserve = 0.5` in the scratch kit install's gate-budget.toml, the box's readings removed, `start
  910`: exit 1, stdout empty, stderr `octo-feather-lane start: refused (usage): 7d 19% used at 2026-11-28T06:19:36Z
  (127.0.0.1:43119), burn 0.37%/h (week average 0.37%/h, last 6h none), reset 2026-12-03T03:00:00Z, course 62% at
  reset, over 50% (reserve 50%, usage_reserve in <kit-install>/gate-budget.toml); no lane started, nothing made: wait
  for the reset at 2026-12-03T03:00:00Z, or change usage_reserve in <kit-install>/gate-budget.toml`; readings exactly
  the one line `{"at": "2026-11-28T06:19:36Z", "windows": {"7d": {"used": 0.19, "reset": "2026-12-03T03:00:00Z"}}}`;
  nothing made (no worktree, branch, record, workspace, tab, agent, prompt or `issue` gh call). PASS.
- `carried`: the route at a closed port, `env OCTO_FEATHER_NOW=2026-11-28T07:19:36Z`, the same start: exit 1, stdout
  empty, stderr `octo-feather-lane start: clock overridden: OCTO_FEATHER_NOW=2026-11-28T07:19:36Z; refused (usage,
  carried): usage not read now (GET 127.0.0.1:38891/v1/models: [Errno 111] Connection refused); last reading 7d 19% at
  2026-11-28T06:19:36Z, carried at its burn then: burn 0.37%/h (week average 0.37%/h, last 6h none), reset
  2026-12-03T03:00:00Z, course 62% at reset, over 50% (...)` with the same wait and change; readings unchanged;
  nothing made. PASS.
