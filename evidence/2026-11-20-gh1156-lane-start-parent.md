# gh1156: octo-feather-lane start files a top-level parent or refuses a sub-issue

Change: `octo-feather-lane start` takes `--new TITLE --body-file FILE` in TICKET's place (files the parent with the
tracker skill's issue-create, never --parent, prints `filed=<key>` at once, starts the lane under its key) and refuses a
ticket issue-view shows with a parent, naming it (scripts/start_lane.py; `octo-feather-lane --help`, start). Kit test
tests/gate/kit/test_lane_start.py; the verify skill's lane-start feature and drive gain `files` and `sub-issue`. No
role file changes.

Smoke: .agents/skills/verify-octo-feather/features/lane-start.md (the recipe the drive below follows, files and sub-issue cases)
Smoke: .agents/skills/verify-octo-feather/features/README.md (index line for lane-start; its drive below)

## verify-octo-feather run lane-start at head 07424a05

`.agents/skills/verify-octo-feather/scripts/verify-octo-feather run --unreachable-exit 77 lane-start` (the qc.toml demo
for the three lane-start criteria): PASS start, supervisor, worktree, record, messages, director-log, files, sub-issue;
`run PASS`, exit 0. Evidence records 20261120T040724Z-c4db07c6 (issue-lifecycle#acceptance-lane-start),
20261120T040724Z-f421e20d (issue-lifecycle#acceptance-lane-start-files), 20261120T040724Z-b4bdedc7
(issue-lifecycle#acceptance-lane-start-sub-issue). Testkit Herdr, systemd and fake gh first on PATH, scratch HOME, state
and target; no live Herdr or GitHub.

```
files:     filed=906
           key=gh906 pane=w2:p5 issue=906
gh log:    issue create --title Scratch lane --body-file body.md
issue-view 906: title "Scratch lane", body as body.md, parent null; src/target-gh906 on branch gh906
sub-issue: exit 1, octo-feather-lane start: step read: ticket 907 is a sub-issue of 905 (issue-view's parent): a lane's parent ticket is a top-level issue; name one, or file one with --new TITLE --body-file FILE
           made for gh907: nothing (no worktree, branch, record, workspace, tab or prompt)
```

## Kit test

`just test tests/gate/kit/test_lane_start.py`: 6 passed. files, filed_stopped and sub_issue red on 947b3158's
start_lane.py (3 failed, 3 passed).
