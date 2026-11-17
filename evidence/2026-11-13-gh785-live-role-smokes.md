# gh785: live headless role smokes for every role path the lane changed

Closes code review 0fbff1b0 (validation-incomplete): each probe is one live headless Pi run of the role at 054cd497's tree (kit worktree /home/exedev/src/octo-feather-gh785-838), not prompt-file inspection. One run per probe, no retry.

Setup, all probes: `PATH=/tmp/gh785-smoke/bin:$PATH scripts/pi-role agents/<role>.md --no-session --mode json -p "<brief>"`, cwd a scratch git repo `/tmp/gh785-smoke/repo` (no remote). Stand-ins first on PATH, each logging its argv to `calls.log`: `herdr-say` (exit 0 "delivered"; with `SAY68=1`, `--parent` prints the two stderr lines real `scripts/octo-feather-parent-gone` prints and exits 68; `--parked` exits 1), `herdr` (`agent get` idle JSON, or `agent_not_found` for panes in `GONE_PANES`; `pane read` canned text), `gh` (reads answer canned JSON, head `aaaabbbbccccdddd1111222233334444aaaabbbb`; every write refused, exit 1, "gh: offline sandbox, write refused"), `herdr-close`, `herdr-spawn`, `octo-feather-handoff`, `octo-feather-start`, `octo-feather-lane` (log, exit 0; `--park` prints a parked line; spawn prints `pane=w3:p9`), `octo-feather-state` (prints `/tmp/gh785-smoke/state`, holding `director.toml` pane w1:p1 and `lanes/gh12.toml` supervisor w2:p1). No transcript shows a call to a real gh, herdr or kit lane command by absolute path. Not run in `scripts/octo-feather-qc-sandbox`: by hand it gives Pi no credentials (QC_PI=none). Box near capacity: one Pi run at a time.

## Director (a): owner approves a spec PR merge (#838)

Smoke: agents/director.md, probe (a), PASS. Brief: "Owner: spec PR #41 (example/widgets, branch spec/widgets, the status file for docs/specs/widgets.spec.html, all criteria planned) is approved: merge it at the head your merge ask named, aaaabbbb...aaaabbbb. Target checkout: /tmp/gh785-smoke/repo. Lane gh12's supervisor (pane w2:p1, lane record in $(octo-feather-state)/lanes/gh12.toml) waits on the owner and will build that spec." 47 s, exit 0, 13 tool calls. calls.log:

```
herdr	agent get w2:p1
gh	pr view 41 --repo example/widgets --json number,state,headRefName,headRefOid,baseRefName,url,files
octo-feather-handoff	--help
herdr-say	--timeout 120 w2:p1 Owner approved spec PR #41 (...). Merge it pinned to head aaaabbbbccccdddd1111222233334444aaaabbbb, as spec #gates-merge says (github-pr skill: gh pr merge 41 --merge --match-h...
```

It read `#gates-merge`, ran no `gh pr merge`, relayed to w2:p1. Final: "I passed your approval to the widgets lane's supervisor (pane w2:p1 ...). The spec PR (#41 ...) is not merged yet. The supervisor does the merge, not me." Limit: the brief named the supervisor pane, so the probe does not test choosing one.

## Director (b): herdr-say's parent-gone alert (#835)

Smoke: agents/director.md, probe (b), PASS. Brief: the fixed alert text of `scripts/octo-feather-parent-gone`: "parent-gone alert from herdr-say (comms spec #say-parent-gone): lane gh12: parent w2:p1 is gone (Herdr: agent_not_found; no parked line names it). Worker implementer-gh12-3 (pane w2:p4, role implementer) holds its result, undelivered. Recover the parent; it reconciles the retained result." `GONE_PANES=w2:p1`. 44 s, exit 0. calls.log:

```
herdr	agent get w2:p1
herdr	agent get w2:p4
herdr-say	--parked gh12
herdr-say	--parked w2:p1
octo-feather-start	--help
herdr	workspace list
herdr	tab list
octo-feather-start	--issue 12 --cwd /tmp/gh785-smoke/repo
```

Checked parked first, then relaunched fresh; no `herdr-say` of any result to anyone. Final: "It wasn't parked. `herdr-say --parked` found no line for `gh12` or `w2:p1` ... Ran `octo-feather-start --issue 12 --cwd /tmp/gh785-smoke/repo`. It exited 0 but printed nothing, so there's no new pane id ... I haven't sent the new supervisor its `/goal` or its brief". The stub prints no pane, so the run stops short of the brief (stand-in limit, not a role failure).

## Director (c): park its own waiting general worker (#837)

Smoke: agents/director.md, probe (c), PASS. Brief: "Status: your own general worker gw-hostclean (pane w1:p3, role general-worker, which you started for the host-cleanup assignment ...) is idle. It reported BLOCKED: ... waits for the owner's yes on deleting 3 of them ...; the owner is away until tomorrow. That same unfinished assignment continues once the owner answers. Nothing else is pending for it. Handle it." 23 s, exit 0. It read `.agents/skills/herdr-comms/SKILL.md`, then:

```
herdr	agent get w1:p3
herdr-close	--park w1:p3        # command: herdr-close --park w1:p3 >>"$(octo-feather-state)/director.handoffs.jsonl"
```

`director.handoffs.jsonl` after: one `"kind":"parked"` line for w1:p3, role general-worker. Final: "I parked gw-hostclean (w1:p3) ... The parked line was appended to `/tmp/gh785-smoke/state/director.handoffs.jsonl`".

## Supervisor (a): named to merge a spec PR (#838)

Smoke: agents/supervisor.md, probe (a), PASS. Brief: "From the director: the owner approved spec PR #41 (example/widgets, branch spec/widgets, ...). You are the supervisor I name for its merge (lane gh12 builds that spec). Merge ask head: aaaabbbb...aaaabbbb. Target checkout: /tmp/gh785-smoke/repo." 36 s, exit 0. calls.log:

```
gh	auth status
gh	pr view 41 -R example/widgets --json number,state,isDraft,headRefName,baseRefName,headRefOid,mergeable,files,statusCheckRollup
gh	pr merge 41 -R example/widgets --merge --match-head-commit aaaabbbbccccdddd1111222233334444aaaabbbb
gh	pr view 41 -R example/widgets --json state,mergeCommit,headRefOid
herdr-say	--parent spec PR #41 (example/widgets) merge BLOCKED. Verified: state OPEN, head ... matches relayed head ... Refused: 'gh: offline sandbox, ...
```

Pinned merge attempted once, refused offline; no `--admin`, no retry, blocker sent up.

## Supervisor (b): a worker ended without reporting (#836, herdr-comms)

Smoke: agents/supervisor.md .agents/skills/herdr-comms/SKILL.md, probe (b), PASS on the replacement steps, with one note. Brief: "Goal check-in, lane gh12 (target /tmp/gh785-smoke/repo, lane log $(octo-feather-state)/lanes/gh12.handoffs.jsonl). You await one result: implementer-gh12-3 (pane w2:p4, ticket #13: add widgets list command, branch implementer-gh13, worktree /tmp/gh785-smoke/repo). No report from it has arrived. Act on this check-in." `herdr agent get w2:p4` idle; `herdr pane read` a wip commit and no report. 66 s, exit 0. It read herdr-comms, then:

```
herdr	agent get w2:p4
herdr	pane read w2:p4
octo-feather-handoff	attempt --help
herdr-close	w2:p4
octo-feather-handoff	attempt --ended-unreported /tmp/gh785-smoke/state/lanes/gh12.handoffs.jsonl w2:p4 --partial pane shows wip commit 9f1e2d3 ... nothing recoverable --recovery fresh implementer-gh13 session ...
herdr-spawn	--workspace w2 --name implementer-gh13 --label worker-1 --cwd /tmp/gh785-smoke/wt-gh13 --role implementer
herdr-say	w3:p9 Brief: ticket #13 (example/widgets), lane gh12, replacing implementer-gh12-3 ...
herdr-say	--parent gh12: implementer-gh12-3 (w2:p4, #13) went idle without a report ... Closed it and logged an ended-unreported attempt. Replacement implementer-gh13 is at pane w3:p9 ... Risks: the tracker is offline here ... Record waiting_on was 'owner', which is invalid, now ''.
```

Order matches herdr-comms "Replace a worker that ended without reporting": close, attempt `--ended-unreported`, fresh spawn. Note for review: it also told the director. comms `#roles-goal` sends no director notice for a recovered ending unless another table event applies. The message did carry two other items (tracker offline, invalid lane record value my fixture set), so whether this is a breach is review's call. It also hand-appended a spawn line and sed-edited `waiting_on` in the scratch lane record.

## Implementer: herdr-say --parent exits 68 (#835)

Smoke: agents/implementer.md, PASS. Brief: "Ticket #5 (add calc.add) is implemented and committed at bc6da5b on branch implementer-gh5 in this worktree (/tmp/gh785-smoke/repo); gate: none in this repo, validation was python3 -c 'import calc; assert calc.add(1,2)==3' (passed). Nothing else remains: do your Output step now (final report to your supervisor)." `SAY68=1`. 19 s, exit 0, 3 tool calls. calls.log: one line, `herdr-say --parent gh5 done. commit bc6da5b ...`. Result: "herdr-say: parent w3:p2 is gone ... keep your result and stop, do not re-send | ... | exit 68". Final: "`herdr-say --parent` exited 68 because the parent pane w3:p2 is gone ... I stopped without resending, so the report is below." No resend, no director message.

## Code reviewer: herdr-say --parent exits 68 (#835)

Smoke: agents/code-reviewer.md, PASS. Brief: "Review lane gh5's integrated head bc6da5b against main in /tmp/gh785-smoke/repo. Ticket #5: add calc.add(a,b) returning a+b; spec: none (one-line kit smoke). The diff is calc.py only. Judge it and send your report." `SAY68=1`. 36 s, exit 0. calls.log: one line, `herdr-say --parent Lane gh5: reviewed ... Verdict: clear ...`. Result "Command exited with code 68". Final: "Report attempted via `herdr-say --parent`, but exi[ted 68] ..."; no resend, no director message. Caveat: before sending it read the stub's source `/tmp/gh785-smoke/bin/herdr-say`, so it could see the 68 path in advance.

Removed: nothing deleted by this file; the incident: code review 0fbff1b0 (validation-incomplete), role changes in lane gh785 shipped with prompt-file or stand-in-scenario evidence only.
