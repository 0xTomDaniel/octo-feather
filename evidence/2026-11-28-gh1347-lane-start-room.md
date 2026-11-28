# gh1347: lane start refuses at the box's lane limit

Change: `octo-feather-lane start` (scripts/lane_brake.py) checks the box's room before any read: open lane records
against lane_limit in the kit install's gate-budget.toml (`octo-feather-lane --help`, start); at or over it the start
is refused in one line, else it prints the room line before the usage line. The verify skill's lane-start feature
and drive gain the `room` case and the room line in the start, exists, files and sub-issue cases. No role file
changes.

Smoke: .agents/skills/verify-octo-feather/features/lane-start.md (room case, room lines and the verify-session gotcha; the drive below follows it)

## verify-octo-feather run lane-start at head cfb23a2f

`.agents/skills/verify-octo-feather/scripts/verify-octo-feather run --unreachable-exit 77 lane-start` (the qc.toml
demo for each lane-start criterion): every case PASS, `drive lane-start PASS`, `run PASS`, exit 0. Evidence record
20261128T110811Z-af00723c (issue-lifecycle#acceptance-lane-start-room); the other lane-start criteria still PASS
(clear 20261128T110810Z-dd757a28, unread 20261128T110810Z-0892b9bd, usage 20261128T110810Z-60b752be, carried
20261128T110811Z-b8325bc4). Testkit Herdr, systemd and fake gh first on PATH, the brake's route the testkit provider
replaying tests/gate/kit/fixtures/lane-brake, scratch HOME, state, Pi config and target; no live Herdr, GitHub or
model route.

- `start`: stdout `room: 0 of 7 lanes open`, then the usage line (course 62%, under 90%), then `key=gh905 ...`. PASS.
- `exists`, `files`, `sub-issue`: the room line first, `room: 1`, `2` and `3 of 7 lanes open`. PASS.
- `room`: after the carried case (gh905, gh906, gh907, gh909 open in the director's session `verify`), gh920 in the
  top state dir's lanes/ and gh921, gh922 in sessions/s2/lanes/; the route the replaying provider with `--log`;
  `start 910`: exit 1, stdout empty, stderr `octo-feather-lane start: refused (room): 7 of 7 lanes open (lane_limit
  7, <kit-install>/gate-budget.toml): gh920, gh921 (session s2), gh922 (session s2), gh905 (session verify), gh906
  (session verify), gh907 (session verify), gh909 (session verify); nothing made: archive a lane (octo-feather-lane
  archive NAME) or raise lane_limit in <kit-install>/gate-budget.toml, then rerun` (the usage, reserve 0.5 there,
  would refuse too: the room comes first); no provider request logged, no gh call but `repo view`, no Herdr call, no
  worktree, branch or record for gh910. PASS.
