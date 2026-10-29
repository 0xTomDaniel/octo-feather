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

1. base, `octo-feather-qa --suite role-transcripts --case director-merge-report-post-merge --kit-ref 0ae818d`:
   pending (run by the supervisor)
2. head, `octo-feather-qa --suite role-transcripts --case director-merge-report-post-merge`:
   pending (run by the supervisor)
