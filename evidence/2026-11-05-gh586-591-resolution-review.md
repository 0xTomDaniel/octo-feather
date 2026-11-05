# gh586 #591: review of a main merge's resolution alone (remerge-diff)

Change: `octo-feather-lane resolution MERGE` prints a merge's resolution files and what `git show --remerge-diff` prints for it. `verdict PR MERGE REPORT --resolution` posts one comment per merge, naming the merge and only those files. merge-ask keeps an earlier review verdict across such a merge when a clear resolution verdict names it, through head_proof, and the section then needs `Reviewed: <proof>`. Without that verdict, the refusal names the merge. agents/code-reviewer.md and agents/supervisor.md name the commands.

Smoke: agents/code-reviewer.md (run (a) below: the role, headless, briefed with `octo-feather-lane resolution 159ab8b`)
Smoke: agents/supervisor.md (no headless supervisor run; the commands its pointer names are driven by tests/lane-review-resolution.sh; owed case: docs/owed-evals/591.md)
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
