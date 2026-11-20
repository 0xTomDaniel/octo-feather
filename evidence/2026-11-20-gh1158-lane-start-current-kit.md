# gh1158: lane start refuses a kit install behind main

Change: `octo-feather-lane start` first fetches its kit install's origin and refuses an install behind main there
(scripts/start_lane.py current_kit, run by cmd_start on kit_install()); tests/gate/kit/test_lane_start.py's
behind_kit; the verify skill's lane-start current-kit case. No role file changes.

Smoke: .agents/skills/verify-octo-feather/features/lane-start.md (current-kit case and its Drive criterion; its drive below)

## verify-octo-feather run lane-start at head 35c15513

`.agents/skills/verify-octo-feather/scripts/verify-octo-feather run --unreachable-exit 77 lane-start` (the qc.toml demo
for issue-lifecycle#acceptance-lane-start-current-kit and #acceptance-lane-start): PASS current-kit, start, supervisor,
worktree, record, messages, director-log; run PASS, exit 0; evidence records 20261120T040537Z-0716b576 (criterion
issue-lifecycle#acceptance-lane-start-current-kit) and 20261120T040537Z-ab3f75b5 (#acceptance-lane-start). Testkit
Herdr, systemd and fake gh first on PATH; OCTO_FEATHER_KIT_INSTALL a scratch kit clone one commit behind its origin;
no live Herdr, GitHub or real kit origin.

```
octo-feather-lane start: step kit: kit install <scratch>/kit-install at 6853cec2... is behind main on its origin
(138479d5..., 1 commit(s) it lacks); nothing made: refresh it (octo-feather-lane post-merge step 3, the kit refresh)
or fast-forward it (git -C <scratch>/kit-install merge --ff-only origin/main), then rerun
```

Then the install fast-forwarded as named, and the start ran (`key=gh905 pane=... issue=905`).

## Kit test

`just test tests/gate/kit/test_lane_start.py`: 4 passed. behind_kit red with the cmd_start call removed (exit 0,
want 1).
