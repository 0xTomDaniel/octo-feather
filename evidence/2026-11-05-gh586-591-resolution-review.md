# gh586 #591: review of a main merge's resolution alone (remerge-diff)

Change: `octo-feather-lane resolution MERGE` prints a merge's resolution files and what `git show --remerge-diff` prints for it. `verdict PR MERGE REPORT --resolution` posts one comment per merge, naming the merge and only those files. merge-ask keeps an earlier review verdict across such a merge when a clear resolution verdict names it, through head_proof, and the section then needs `Reviewed: <proof>`. Without that verdict, the refusal names the merge. agents/code-reviewer.md and agents/supervisor.md name the commands.

Smoke: agents/code-reviewer.md (run (a) below: the role, headless, briefed with `octo-feather-lane resolution 159ab8b`)
Smoke: agents/supervisor.md (two headless supervisor runs below: after a conflicted main merge, and after a fix commit; owed case: docs/owed-evals/591.md)
Removed: nothing deleted. Incident: issue #586 item 2, where the delta review after a main merge re-read main's already-reviewed content (#503).

## Measured: resolution-only review vs full delta review on a real redo

Case: lane 557's merge of main 159ab8b (branch implementer-gh558; first parent 504e5e1, the last reviewed lane head). Both runs used `pi-role agents/code-reviewer.md -p` from this worktree with the role's own model, openai/gpt-6.1-sol at thinking high, no override. They ran one after the other with a 30 min cap (coreutils timeout), on 2026-11-05.

| run | brief | input size | wall | turns / tool calls | tokens in / cache read / out | cost | verdict |
|---|---|---|---|---|---|---|---|
| (a) resolution | `octo-feather-lane resolution 159ab8b` output | 81 lines, 4 files | 86 s | 8 / 7 | 26,236 / 136,192 / 2,448 | $0.091 | clear |
| (b) full delta | `git diff 504e5e1 159ab8b` | 11,675 diff lines, 205 files | 206 s | 20 / 19 | 140,232 / 1,665,280 / 6,272 | $0.510 | blocking (2 findings, both on main: #613) |

Result: the resolution review took 0.42x the wall time, 0.18x the cost and 0.10x the input plus cache tokens.

Caveats:
- Lane 593's full integrate ran on the box beside both runs, so the wall times are loaded. Tokens and cost do not depend on load.
- Run (a)'s wall time is inflated. With no parent route, it made 3 failed `herdr-say --parent` sends and then one send to the director, as the role's Output says.
- Run (b) was restarted once, after 39 s, to add a "print your report on stdout; do not herdr-say anyone" line to its brief. The table counts only the restarted run. Run (b) still reported to the director.
- Run (b) said it was not exhaustive: "Remaining hunks and dependency release/adoption claims were not exhaustively verified". A complete delta review costs more than this run.
- This is one case on one model.

## Supervisor, headless: resolution review after a conflicted merge, full review after a fix

Setup: `/tmp/w591-smoke/setup.sh a|b` builds a scratch lane gh9 (PR #9 of o/r, base main, no criterion) with a bare origin. Its judged head J has a clear review verdict (comment 1001). In scenario a, main then changes the lane's line of app.py plus notes.txt, and the lane's merge of main resolves that conflict. In scenario b, a fix commit lands on the lane instead. Either way, the new commit is HEAD and is pushed. Stubs record gh, just, herdr, herdr-spawn and herdr-say; a send to the spawned reviewer pane drops a clear report in inbox/. A logging wrapper runs the real `octo-feather-lane`.

`/tmp/w591-smoke/run.sh` ran both scenarios one after the other from this worktree at 8ee8902, each through `pi-role agents/supervisor.md -p` with the role's own model (claude-opus-5-5) and a 30 min cap. The brief does not name the resolution review, remerge-diff, or which review to run: "Do the lane's next review step now, running the real commands: start the code review this head needs ..., then post its verdict. ... print your report as your final message on stdout; do not herdr-say anyone but the reviewer you spawn."

| scenario | wall | turns | tokens in / cache read / cache write / out | cost | outcome |
|---|---|---|---|---|---|
| a, conflicted merge | 30 s | 8 | 15 / 137,061 / 19,682 / 2,577 | $0.236 | resolution review, verdict posted with --resolution |
| b, fix commit | 41 s | 8 | 15 / 144,184 / 24,519 / 2,991 | $0.285 | full review of main..head, plain verdict |

Scenario a's calls.log, in order (the reviewer brief is cut to its first line and its CONTEXT):

```
octo-feather-lane --help
octo-feather-lane --help
octo-feather-lane resolution 461a0b0
herdr-spawn --workspace w9 --name code-reviewer-gh9 --label code-reviewer --cwd .../lane --role code-reviewer
herdr-say w9:p3 GOAL        Review the conflict resolution of main-merge 461a0b033a1d on PR #9 (o/r, lane gh9) and return a verdict.
  CONTEXT     Prior head 38e50aa6e70f reviewed clear: ...#issuecomment-1001. Since then origin/main merged in, conflict resolved. Review only the resolution below (issue-lifecycle #lanes-one-head):
  [the full output of octo-feather-lane resolution: Files: app.py, then the remerge diff]
octo-feather-lane verdict 9 461a0b033a1d .../inbox/reviewer-report.md --resolution
gh pr view 9 --json headRefOid,baseRefName,comments
gh api -X POST repos/{owner}/{repo}/issues/9/comments --input ... --jq .html_url
```

Scenario b's calls.log, in order:

```
octo-feather-lane --help
octo-feather-lane --help
herdr-spawn --workspace w9 --name code-reviewer-gh9 --label code-reviewer --cwd .../lane --role code-reviewer
herdr-say w9:p3 GOAL        Fresh code review of PR #9 (o/r, base main) at head bd2f99d699ff...; report verdict.
  ACCEPTANCE  Review covers whole lane diff main..bd2f99d, fix commit included; ...
  VERIFY      git diff main...bd2f99d; just fast; just check.
octo-feather-lane verdict 9 bd2f99d699ff6a064f4c671e22b6535115a357b4 .../inbox/reviewer-report.md --repo o/r
gh pr view 9 --json headRefOid,baseRefName,comments -R o/r
gh api -X PATCH repos/o/r/issues/comments/1001 --input ... --jq .html_url
```

Final messages (out.txt):
- a: "I ran the review the new merge head needed and posted its verdict: clear ... What was reviewed: only the conflict resolution in app.py ... Brief: built with `octo-feather-lane resolution 461a0b0` ... `octo-feather-lane verdict 9 461a0b033a1d <report> --resolution` exited 0 and created the PR's verdict comment for this merge."
- b: "I ran a fresh code review of PR #9 at the new head (bd2f99d) ... Its brief asked for a read-only review of the whole lane diff from main to bd2f99d, including the fix commit ... updated the PR's single verdict comment (it was #1001) with head bd2f99d699ff, verdict clear."

Caveats:
- Each scenario ran once, on a toy lane.
- The reviewer is a stub that replies at once, so each run measures the supervisor's choice and calls, not a review.
- Both runs said they found no lane record to log the spawn in. The scratch state dir has no lanes/ directory.
- The repeated before-and-after case is still owed: docs/owed-evals/591.md.
