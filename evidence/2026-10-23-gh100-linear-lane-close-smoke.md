# Linear lane merges on GitHub and finishes in Linear: smoke, issue #100 (lane gh82), 2026-10-23

ADR 0008; owed evals in docs/owed-evals/100.md. Spec issue-lifecycle #gates-pr-line, #acceptance-pr-tracks,
#acceptance-merge-linear, #acceptance-no-github-issue, #acceptance-merge-approved-head; skills #tracker-role-line,
#tracker-scripts, #tracker-writes; comms #octo-lane-record-tickets.

## Supervisor close and PR line, real headless runs

Smoke: agents/supervisor.md .agents/skills/github-pr/SKILL.md .agents/skills/push/SKILL.md .agents/skills/to-tickets/SKILL.md .agents/skills/implement-spec/SKILL.md .agents/skills/linear/SKILL.md .agents/skills/commit/SKILL.md .skillfile/patches/skills/to-tickets/SKILL.md.patch .skillfile/patches/skills/implement-spec/SKILL.md.patch

Real pi, `scripts/pi-role agents/supervisor.md -p "<prompt>"` in a throwaway git target with `tracker = "linear"`
(the supervisor got commit, github-pr, linear, herdr-comms, implement-spec, push, to-tickets). Before: a copy of
the kit at 3fb3b0c (`git archive`); after: this change. Prompt (sample 1 forbade reading files, sample 2 allowed
reading its own skill files; no command, no message):

> Smoke probe, no task. Run no command except reading your own skill files, and message no one. From your role and
> skills: this target's tracker is the one its .octo-feather.toml names (linear); your lane's parent ticket is
> ENG-123 and the owner said merge. Answer in exactly four lines: pr_first_line=..., file_ticket=..., close=...,
> github_issue=...

Sample 1, no reads, before (00:19:39 to 00:19:50 UTC), final message verbatim:

```
pr_first_line=Not known without reading files. The linear skill's lane-key script prints the line that links the PR to ENG-123, and the github-pr skill's push flow puts it first in the PR body. I don't know the exact line or script name, so I won't make one up.
file_ticket=I'd use the to-tickets skill, which files tickets in the configured tracker (Linear) through the linear skill's scripts, with each ticket set as a sub-issue of ENG-123 and `Blocked by` added only where order matters. I'd need to read the skill to get the exact script and flag.
close=After my head-pinned merge, I'd follow github-pr's "Merge And Issue Sync" steps, then mark each ticket and ENG-123 done with the linear skill's finish script. I don't know the exact command lines without reading those skills.
github_issue=No. This target's tracker is Linear, and github-pr says tickets go through the tracker skill, so GitHub is only for the branch, PR, reviews and merge. My role text says GitHub issues, but the target's own config takes priority here.
```

Sample 1, no reads, after (00:19:39 to 00:19:50 UTC):

```
pr_first_line=Not verified, since I read no file: my guess is a line naming parent ENG-123 for Linear, not a GitHub `Closes #N`, printed by a script in the linear skill; I don't know that script's exact name or output without reading `linear/SKILL.md`.
file_ticket=Run the `to-tickets` skill, which files each ticket through the linear skill's scripts as a sub-issue of ENG-123, setting `Blocked by` only where order matters.
close=`octo-feather-lane done ENG-123` (runs the linear skill's `issue-done` on the parent and every sub-issue and reads each back; on a failure I do the fix it names and rerun), then `octo-feather-lane archive <lane record name>` before the close report.
github_issue=no: the tracker is Linear, so tickets are read and written only through the linear skill; `github-pr` covers only the branch, the PR and the head-pinned merge.
```

Sample 2, reads allowed, before (00:20:34 to 00:20:48 UTC):

```
pr_first_line=`Tracks ENG-123`, printed by `<base>/.agents/skills/linear/scripts/pr-line ENG-123`
file_ticket=Check the draft with `octo-feather-lane ticket - < draft.md` until it exits 0, then run `<base>/.agents/skills/linear/scripts/issue-create --title "<T>" --body-file draft.md --parent ENG-123 [--blocked-by ENG-<n>]` (no label, since Linear writes allow none), then `octo-feather-lane tickets ENG-123` must exit 0
close=After `gh pr merge <N> --merge --match-head-commit <head>`, run `<base>/.agents/skills/linear/scripts/issue-done ENG-<sub>` for each sub-ticket, then `<base>/.agents/skills/linear/scripts/issue-done ENG-123`, then check each with `.../scripts/issue-view <KEY>` until state=done
github_issue=no, because the tracker is Linear and the linear skill says never file a GitHub issue for a Linear target; only the PR and merge stay on GitHub, and the "close primary GitHub issue" step means closing ENG-123 in Linear
```

Sample 2, reads allowed, after (00:20:34 to 00:20:46 UTC):

```
pr_first_line=`Tracks ENG-123`, printed by the linear skill's `pr-line ENG-123` (`<kit>/.agents/skills/linear/scripts/pr-line ENG-123`)
file_ticket=`<kit>/.agents/skills/linear/scripts/issue-create --title "<T>" --body-file <F> --parent ENG-123 [--blocked-by <KEY>]...` (draft first passes `octo-feather-lane ticket -`; after publishing, `octo-feather-lane tickets ENG-123` must exit 0)
close=`octo-feather-lane done ENG-123` (runs `issue-done` on each sub-issue in ENG-123's `issue-view`, then on ENG-123, and reads each back; on failure do the fix it names and rerun), after the merge `gh pr merge <N> --merge --match-head-commit <head>`
github_issue=no: tracker is linear, and the linear skill says never file a GitHub issue for a Linear target; tickets close only via `issue-done`, and `merge-ask` fails any PR line that would close a GitHub issue at merge
```

Before, the role text said "GitHub issues" and "reconcile the primary GitHub issue to closed": sample 1 named the
contradiction ("My role text says GitHub issues"), sample 2 reinterpreted it ("the close primary GitHub issue step
means closing ENG-123 in Linear") and hand-rolled the close loop. After: one command, `octo-feather-lane done
ENG-123`, from the role text alone (sample 1), and no GitHub issue.

Same prompt on a `tracker = "github"` target, parent 82, after only (00:22:06 to 00:22:18 UTC):

```
pr_first_line=`Closes #82`, printed by the github-issues tracker skill's `scripts/pr-line 82` (`octo-feather-lane merge-ask` checks this line)
file_ticket=`<github-issues>/scripts/issue-create --title T --body-file F --parent 82 [--blocked-by KEY]...` (draft must pass `octo-feather-lane ticket -` first; after filing, run `octo-feather-lane tickets 82`, must exit 0)
close=`octo-feather-lane done 82` (runs `issue-done` on each sub-issue `issue-view 82` lists, then on 82, and reads each back; on failure do the fix it names and rerun)
github_issue=yes: the tracker is github, so the lane's tickets are GitHub issues. I file the sub-issues of #82 and close them and #82 through the tracker skill's scripts, if `[consent] issues` allows. `Closes #82` may also close #82 at merge, and `done` still reads it back.
```

Result: pass, one sample per side, no live lane. `commit/SKILL.md` (one input line) was loaded but not asked about.

## Director lane start, real headless runs

Smoke: agents/director.md .agents/skills/herdr-comms/SKILL.md .agents/skills/github-issues/SKILL.md

`scripts/pi-role agents/director.md -p` in the same kind of Linear target; prompt: parent=how you file the lane's
parent ticket, start=the octo-feather-start command for parent ENG-123 and worktree /w and its workspace,
record_issue=the lane record's issue value. Reading its own skill files allowed.

Before (00:20:48 to 00:21:07 UTC):

```
parent=`<linear skill folder>/scripts/issue-create --title "CSV export" --body-file F`, which prints the new key. Not `gh issue create`, since a Linear target never gets a GitHub issue.
start=`octo-feather-start --issue ENG-123 --cwd /w`, which creates workspace `eng-123` with the supervisor in tab `supervisor`.
record_issue=`issue = "ENG-123"`. This one is my inference: no skill file says what goes in the record for Linear, so I used the key the way the tracker writes it.
```

After (00:20:48 to 00:20:55 UTC):

```
parent=<kit>/.agents/skills/linear/scripts/issue-create --title "CSV export" --body-file <brief file>
start=octo-feather-start --issue eng-123 --cwd /w (creates Herdr workspace eng-123, supervisor in tab supervisor)
record_issue=eng-123
```

Before, the lane record's `issue` was an inference the role example (`issue = 114  # primary GitHub issue
number`) did not support; after, it is the lane key, as spec comms #octo-lane-record-example writes it (`gh12`).
`github-issues/SKILL.md` changed only its issue-view row (children); the GitHub sample above read it through the
github-issues tracker skill, and tests/tracker.sh runs the script.

Removed: agents/director.md "files GitHub issues, starts one supervisor per issue", "create the lane's parent GitHub issue (`gh issue create`)", "creates the lane workspace `gh<n>`", "registers it again under `gh<N>`", "issue = 114 # primary GitHub issue number"
Removed: agents/supervisor.md "(a GitHub issue)", "Ticket state lives in GitHub issues only", "one parent GitHub issue", "reconcile the primary GitHub issue to closed"
Removed: to-tickets patch "The issue tracker is GitHub Issues", "A real issue tracker (GitHub Issues)", "Apply the `ready-for-agent` triage label unless instructed otherwise" (a label is no tracker write, skills #tracker-writes)
Removed: implement-spec patch "The issue tracker is GitHub Issues", "marked as closing the spec and tickets", "just integrate <issue>"

## Demo: merge-ask, tickets and done in a Linear target, offline

A throwaway git target with `tracker = "linear"`, lane branch eng-123 (base, a code commit J, qc's status commit H).
PR 7 is a snapshot served by the qc judge's offline gh (`github-pr/scripts/gh`, `OCTO_FEATHER_GHSNAP`), branch
`eng-123`, body starting `Tracks ENG-123`, no Closes line. Tickets are in the fake linear's store
(`OCTO_FEATHER_LINEAR_STORE`): ENG-123 with sub-issues ENG-124 (a tracer ticket) and ENG-125 (no demo). No network,
no herdr.

```
# gh: .agents/skills/github-pr/scripts/gh; linear: .agents/skills/linear/scripts/linear; target tracker: tracker = "linear"
$ <kit>/scripts/octo-feather-lane merge-ask 7 --status docs/specs/demo.status.json
## Merge ask

Head: 3c8269b8445a
Checks: check pass on 3c8269b8445a
Judged: 3c8269b8445a is the PR head
| criterion | qc verdict | judged | evidence |
|---|---|---|---|
| demo#acceptance-a | pass | judged 3c8269b84 | qc report r.json, `bin/demo` |
Review verdict: https://github.com/o/r/pull/7#issuecomment-1001
Built: demo#acceptance-a
Failed: none
exit=0
# the same PR with 'Closes #5' in place of 'Tracks ENG-123':
$ <kit>/scripts/octo-feather-lane merge-ask 7 --status docs/specs/demo.status.json
octo-feather-lane merge-ask: PR #7 merge ask incomplete (2 items), head 3c8269b8445a:
  - parent line: missing; add the line `Tracks ENG-123` (the tracker skill's pr-line ENG-123) to the PR body
  - parent line: `Closes #5` closes GitHub issue #5, not the lane's parent line `Tracks ENG-123`; remove it (the supervisor's close moves each ticket to done with the tracker skill's issue-done)
exit=1
$ <kit>/scripts/octo-feather-lane tickets ENG-123
ENG-124: ok
ENG-125: class: layer-only-ticket: last acceptance item is not a `demo: ` line; fix: end the acceptance list on `demo: ` with a backticked command that shows the behavior through the app's CLI, HTTP or UI (e.g. demo: `app cmd ARGS` prints X), not the gate alone; or, for one step of a wide refactor, add the line `Expand-contract: expand|migrate|contract`
ENG-123: 1 of 2 tickets pass, 1 fail
exit=1
$ <kit>/scripts/octo-feather-lane done ENG-123
ENG-124: done
ENG-125: done
ENG-123: done
ENG-123: parent and 2 tickets done
exit=0
# store states after done: {"ENG-123":"Done","ENG-124":"Done","ENG-125":"Done"}
```
