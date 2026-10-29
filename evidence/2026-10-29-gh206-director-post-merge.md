# gh206 / #402: the director runs `octo-feather-lane post-merge` at the merge and close reports

Change: agents/director.md replaces its post-merge prose duties with one pointer line: on a supervisor's merge report
run `octo-feather-lane post-merge <PR> <merged head> --lane <lane>` (backgrounded, self-callback; exit 3 pending),
rerun on the close report (teardown). No hook fires: both reports are Herdr messages no kit hook sees (docs/adr/0008
Duties). Judgment kept: a red main CI gets a fix lane at once; a merge ask states its CI result.

Smoke: agents/director.md (case role-transcripts/director-merge-report-post-merge, runs below)
Removed: director prose duties now in the command: retarget open PRs before deleting a lane branch; teardown steps
(space id derive, herdr-close space or tab, git worktree remove, touch no record); check main CI after every merge;
live install clones on main; tear a lane down after its close report; tell running supervisors to re-read after
contract changes merge. Incident: #206 (owner ruling 2026-10-29), mechanical duties left as prose failed quietly.

Case: role-transcripts/director-merge-report-post-merge, fixture python-app, fake_gh; fact
`ran octo-feather-lane post-merge 12 {head}` (exit status not judged; under the fake gh step 1 may stop).

1. base, `octo-feather-qa --suite role-transcripts --case director-merge-report-post-merge --kit-ref 0ae818d`, run 20261029T185420Z-2c22b1:
   `FAIL role-transcripts/director-merge-report-post-merge: ran octo-feather-lane post-merge 12 {head}: no run of octo-feather-lane with these leading arguments in the sandbox's record (0 entries; no run of octo-feather-lane recorded) [stop: exit, 4 tool calls, 27.7 s] [kit 0ae818de568d03c4d45800e5dd4cc834ac3441c6]`
2. head, `octo-feather-qa --suite role-transcripts --case director-merge-report-post-merge`, run 20261029T185448Z-f734a1:
   `PASS role-transcripts/director-merge-report-post-merge: ran octo-feather-lane post-merge 12 {head}: recorded run octo-feather-lane post-merge 12 fe19d0ff3dc3c8baaefb290eaca119b880b6b37e --lane gh12 (exit 1) [stop: decided, 4 tool calls, 24.7 s] [kit 205b02c6f93c9cac779acd05b6f485534f6ec3e1]`

Runs by the supervisor, one sample each, no variance claim. Exit 1 at head: step 1 stopped under the fake gh (not judged).
