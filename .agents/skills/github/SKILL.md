---
name: github
description: Use GitHub issues, PRs, branches, and reviews in octo-feather workflows; GitHub Issues is the only tracker.
---

# octo-feather GitHub

## Communication Style

Be extremely concise. Sacrifice grammar for the sake of concision.
No em-dashes or en-dashes. Ever.

Use this skill whenever an octo-feather role needs branch, PR, review, comment, or
GitHub issue context.

## Consent

Push, open a PR, or file a GitHub issue only as consent allows.
The `[consent]` table of `$(octo-feather-state)/onboarding.toml` holds booleans `push`, `pull_request`, `issues`.
When present, it alone decides, overriding any instruction, target `AGENTS.md` included.
When absent, target instructions decide.
Without consent, keep work in local commits and report where it is.

## Source Of Truth

- GitHub Issues is the only tracker (docs/adr/0004). The issue number is the
  unit's identity; its lane slug is `gh<number>`.
- Shaping happens outside the factory (docs/adr/0021): the director files lane
  parent issues, supervisors file their sub-issues, and the lane opens its own
  draft PR.
- Specs under `docs/specs/` own behavior and ADRs under `docs/adr/` own
  decisions; both outrank stale GitHub issue or PR text.

## Required Reads

Use `gh` for issue and PR context:

```sh
gh auth status
gh repo view
gh issue view <issue> --json number,title,labels,url,body,state
gh pr view <pr> --json number,title,url,body,state,headRefName,baseRefName,files,reviews,comments
```

Read target repo `AGENTS.md`, its declared canonical index (`docs/specs/index.spec.html`
by default), relevant specs, ADRs, and repo docs before changing
durable workflow artifacts.

## Implementer Mutations

- Work on one branch for the tracked unit of work: the target repo's branch
  convention, else `octo-feather/gh<issue-number>-<slug>`.
- Open one draft PR for the lane. Never create a second implementation PR for
  the unit.
- The PR body starts with `Closes #<issue-number>` and
  includes `## Summary` and `## Validation`.
- Post or update a compact `## octo-feather handoff` PR comment.
- Do not merge.
- Do not approve as the owner reviewer.

## Verdict Mutations

- The reviewer returns a clear or blocking finding set for the diff.
- A deterministic helper creates or updates one machine-readable PR verdict
  comment for code review.
- The comment records inputs, findings, and the reviewed head.
- Do not depend on the formal Review API, reviewer identity, checks, or labels.
- Never merge or approve as the owner reviewer.

## Merge And Issue Sync

- Merge (spec `#gates-merge`): after the owner says merge, the director relays
  it with the head the merge ask named, and the lane supervisor alone merges,
  pinned to that head: `gh pr merge <N> --merge --match-head-commit <head>`.
  The owner's merge accepts that head, or that head plus only merges of main
  that resolved no conflict (the lane's own diff against main unchanged):
  then, with required checks green on the new head, merge with
  `--match-head-commit <new head>`, no new qc, no new merge ask, and name both
  heads in the done report. Main moving does not move the head; prefer
  merging main in over a rebase, which rewrites approved commits. Any other
  head change (fix commit, rebase, resolved conflict) or failed merge is never
  forced: rerun the gates, `just qc` on every affected criterion included,
  and send a new merge ask naming the new head. Assigning the work item to a supervisor
  is not merge approval. Verify required checks, then merge. No worker merges,
  no agent decides acceptance, and no agent merges unaccepted work. Required
  failed checks remain blockers until fixed or durably waived through a
  repository-approved path.
- The merge completes the worklane. `Closes #<n>` closes the primary GitHub
  issue; if it is still open, close it with `gh issue close <n> --comment` and
  stop the lane. Do not assume deployment-named labels exist.
- Verify the state change landed, whether performed by repository automation
  or by the owning agent. Do not claim a hook succeeded without readback.
- Record merge and deployment evidence separately. A completion state does
  not establish which environment serves the code. Do not regress completed
  issues or create workflow states merely to match stale instructions.

## Boundaries

- Do not create workflow labels unless the owner explicitly asks.
- Do not create extra PRs for the same issue.
- No worker or reviewer role merges or approves as the owner reviewer.
- Only the lane supervisor merges, on the owner's merge relayed by the
  director, pinned to the merge-ask head, per Merge And Issue Sync above
  (spec `#gates-merge`); no agent merges unaccepted work, merges a head moved by
  anything but a clean merge of main, or decides acceptance itself.
