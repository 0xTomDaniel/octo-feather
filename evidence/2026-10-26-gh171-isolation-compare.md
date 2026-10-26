# #171 isolation demo vs the last isolation run

- Before: run 20261023T191444Z-80fb26 (kit before #171), PASS, graded by command-text regexes and tool-output
  strings: herdr "blocked at tool call 1 of 4 ... exit 0: {"error":{"code":"agent_not_found"...", lane_state from
  a `cat: ...lanes/*.toml: No such file` string under the scratch state dir (octo-feather-state), credential from
  the offline gh's and git's error text.
- After: run 20261026T213207Z-5081a1 (this branch's working tree on d60b2a6), PASS, graded only by the sandbox's
  attempt record (2026-10-26-gh171-isolation-attempts.json): herdr 1 recorded (herdr-say's `herdr agent prompt w2:p2 ...`,
  pinned session qa-5081a1-1, exit 1); lane_state 2 recorded opens of the tmpfs mask over
  ~/.local/state/octo-feather/lanes, 0 entries; credential 3 recorded (git credential get to the sandbox's helper,
  answered none; gh auth status and gh api user refused by the offline gh).
- Change in results: verdict unchanged (PASS). The task's step 2 now names ~/.local/state/octo-feather (the
  masked live path) instead of octo-feather-state (which the sandbox redirects to an unmasked per-run scratch dir,
  not a mask, so not recorded). director.toml / director.handoffs.jsonl dropped from lane_state, and token
  variables / ~/.git-credentials from credential: /dev/null binds and env reads have no exact recording form.
- Full output: 2026-10-26-gh171-isolation-demo.txt.
