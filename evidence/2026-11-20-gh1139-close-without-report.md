# gh1139: the roles drop the hand-run post-merge and the close report

Change: agents/supervisor.md merges with `octo-feather-lane merge`, keeps its own pre-archive teardown, archives and
sends no merge or close report (issue-lifecycle #gates-main-moved); agents/director.md's Post-merge paragraph runs no
post-merge on a merge, holds or releases no archive, tears nothing down, resolves a stop and reruns it; github-pr's
Merge And Issue Sync names `octo-feather-lane merge` (a spec PR keeps `gh pr merge`); correction-lane.md and the
director's Correction lanes point at the routine's message; post-merge step 7's pending line and `--help` say the
archive starts it.

Removed: agents/supervisor.md's hand-run `octo-feather-lane done`, "the director removes it after your close report",
the close report and its content (findings count, correction lane keys, proof nothing is left) and the space-or-tab
rule (`post-merge` step 7 does each, #1134); agents/director.md's "on a supervisor's merge report, run post-merge ...
rerun it on that supervisor's close report" and "No hook runs it" (`octo-feather-lane merge` and `archive` run it,
#1133, #1134); github-pr's `gh pr merge` then `octo-feather-lane done` for a lane PR.

Smoke: agents/supervisor.md .agents/skills/github-pr/SKILL.md (headless supervisor, below)
Smoke: agents/director.md .agents/skills/verify-octo-feather/features/correction-lane.md (headless director, below)

## Headless supervisor at this branch (uncommitted edit, 2026-11-20)

`scripts/pi-role agents/supervisor.md -p "<read-only smoke: lane gh12, director relays owner approval of PR #12 at
head abc1234def, every worker closed; reply with each command to the lane's end, any message to the director after
the merge, what tears down your worktree, space or tab, and the lines read>"`, exit 0. Reply, abridged:

```
1. octo-feather-lane merge 12 abc1234def ... runs gh pr merge 12 --merge --match-head-commit <full head>, then done
   <parent> ..., and the post-merge routine's steps 1 to 6.
2. Remove my own /tmp scratch files.
3. Tear down: review rows, every worktree except my own, workers (already closed).
4. octo-feather-lane archive gh12 --director-source <director pane> <session file> ... Last, it starts the teardown
   (post-merge step 7). If it names a stopped post-merge step, that is the director's to fix; I rerun when the
   director says it's resolved.
5. Terminate.
Message to the director after the merge: None. I send no merge report and no close report. When the routine
finishes, it sends the director one message that covers both ...
What tears down my worktree, space and tab: Post-merge step 7 ... I never remove my own worktree, space or tab.
Sources: agents/supervisor.md:106, :111; .agents/skills/github-pr/SKILL.md:73-79; octo-feather-lane --help ...
```

It also noted the live kit install's `octo-feather-lane` (5d9af8dc) has no `merge` yet; it would report that as a
blocker, never fall back to `gh pr merge`. The install gets `merge` when gh1075 merges (post-merge step 3).

## Headless director at this branch (uncommitted edit, 2026-11-20)

`scripts/pi-role agents/director.md -p "<read-only smoke: lane gh12 merged; then the message 'post-merge gh12 PR #12
stopped: step 4 checkout stopped: checkout /home/u/src/hello is dirty (M README.md); fix it, then rerun ...'; reply
what you run after a merge with no message, what you do with this one, whether you wait for a close report, hold or
release the archive or tear anything down>"`, exit 0. Reply, abridged:

```
1. If no message came, I run nothing after the merge. ... "Run no post-merge on a merge."
2. ... This is not a red main CI, so it does not need a fix lane. I resolve it myself. ... Rerun in the target repo,
   in the background with a self-callback: octo-feather-lane post-merge 12 abc1234def --lane gh12 ...
3. Close report: I don't wait for one. The supervisor sends none. ... Archive: I don't hold or release it. ...
   Teardown: I tear nothing down by hand.
Sources: agents/director.md:99; agents/supervisor.md:24; docs/specs/comms.spec.html:47; octo-feather-lane --help.
```

Correction lanes: the director reads the keys from the routine's message (director.md Correction lanes,
correction-lane.md), which `post-merge` sends with "correction lanes" (`octo-feather-lane --help`, post-merge).

## Eval case

`supervisor-notifications/merge-approved-lane-merge-archive` (docs/owed-evals/1139.md). Not run here: it needs the
lane's eval slot. Command for the slot holder:

`scripts/octo-feather-qa --suite supervisor-notifications --case merge-approved-lane-merge-archive --runs 3 --baseline 13191f3f`

Expected at base 13191f3f: FAIL on `ran gh pr merge` count 0 (github-pr named `gh pr merge`), `ran octo-feather-lane
done` count 0 and `ran herdr-say --parent` count 0 (the close report). `scripts/check-evals`: `evals: ok (20 suites,
533 cases)`.
