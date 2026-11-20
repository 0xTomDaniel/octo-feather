# gh1157: lane start refuses an existing lane, a rerun finishes a stopped start

Change: `octo-feather-lane start` (scripts/start_lane.py) refuses a lane whose record, worktree, branch or Herdr
workspace exists that no stopped start left, and keeps lanes/<key>.start.json so the same start run again continues
from the step that stopped (`octo-feather-lane --help`, start). The testkit Herdr answers `workspace list` and fails
one prompt on a file `prompt-down`. The verify skill's lane-start feature and drive gain the cases. No role file
changes.

Smoke: .agents/skills/verify-octo-feather/features/lane-start.md (exists and rerun cases; the drive below follows it)
Smoke: .agents/skills/verify-octo-feather/features/README.md (index line names both criteria; its drive below)

## verify-octo-feather run lane-start at head c8baf758

`.agents/skills/verify-octo-feather/scripts/verify-octo-feather run --unreachable-exit 77 lane-start` (the qc.toml
demo for each lane-start criterion): PASS start, supervisor, worktree, record, messages, director-log, exists,
rerun-stopped, rerun, rerun-refused; `drive lane-start PASS`, `run PASS`, exit 0. Evidence records:
20261120T041925Z-6b3629c3 (issue-lifecycle#acceptance-lane-start), 20261120T041926Z-f51cc345
(issue-lifecycle#acceptance-lane-start-exists), 20261120T041926Z-1c1d7fe7 (issue-lifecycle#acceptance-lane-start-rerun).
Testkit Herdr, systemd and fake gh first on PATH, scratch HOME, state and target; no live Herdr or GitHub.

```
exists:        step exists: lane gh905 exists: lane record <state>/lanes/gh905.toml, worktree <scratch>/src/target-gh905,
               branch gh905, Herdr workspace gh905 (w1); nothing changed, no supervisor started (...)   exit 1
rerun-stopped: step goal (made so far: worktree <scratch>/src/target-gh906 on branch gh906, supervisor w2:p5 in
               workspace w2, record <state>/lanes/gh906.toml): herdr-say w2:p5 exit 1 (herdr: server not reachable)
rerun:         key=gh906 pane=w2:p5 issue=906; one worktree target-gh906, one agent gh906, lanes/ gh906.toml only,
               w2:p5 got the goal then the brief, director log gh906 lines: spawn prod
rerun-refused: step exists: lane gh906 exists: lane record <state>/lanes/gh906.toml, ...   exit 1
```

## Kit test

`just test tests/gate/kit/test_lane_start.py`: 5 passed; `exists` and `rerun` red on the pilot's start_lane.py
(947b3158: with the record there the start went on to spawn a supervisor; the rerun's second run exit 1).
