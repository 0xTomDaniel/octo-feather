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
- During shaping, `.octo-feather/drafts/<slug>.md` is canonical until the
  operator approves the GitHub mutation; after finalization, the GitHub issue
  body and `octo-feather:ready` label are the issue source of truth.
- The evolving draft PR is the durable shaping and delivery surface.
- Specs under `spec/` own behavior and ADRs under `spec/adr/` own decisions;
  both outrank stale GitHub issue or PR text.

## Required Reads

Use `gh` for issue and PR context:

```sh
gh auth status
gh repo view
gh issue view <issue> --json number,title,labels,url,body,state
gh pr view <pr> --json number,title,url,body,state,headRefName,baseRefName,files,reviews,comments
```

Read target repo `AGENTS.md`, its declared canonical index (`spec/index.md` or
`spec/index.spec.html`), relevant specs, ADRs, and repo docs before changing
durable workflow artifacts.

## Shaping Mutations

Do not mutate GitHub issues during shaping until the operator
approves the final mutation. After approval:

1. Create or update exactly one GitHub issue with the approved draft body
   (`gh issue create` / `gh issue edit`).
2. Create `octo-feather:ready` if missing.
3. Apply `octo-feather:ready`.
4. Delete the local draft.

Do not create extra workflow labels unless the operator explicitly asks.

## Implementer Mutations

- Work on one branch for the tracked unit of work: the target repo's branch
  convention, else `octo-feather/gh<issue-number>-<slug>`.
- Continue the shaped unit's existing draft PR. Open it only when shaping did
  not already create it. Never create a second implementation PR for the unit.
- The PR body starts with `Closes #<issue-number>` and
  includes `## Summary` and `## Validation`.
- Post or update a compact `## octo-feather handoff` PR comment.
- Do not merge.
- Do not approve as the human reviewer.

## Verdict Mutations

- The reviewer returns a clear or blocking finding set for the diff.
- A deterministic helper creates or updates one machine-readable PR verdict
  comment for code review.
- The comment records inputs, findings, and reviewer receipt.
- Do not depend on the formal Review API, reviewer identity, checks, or labels.
- Never merge or approve as the human reviewer.

## Merge And Issue Sync

- Merge to the main branch is the active owning agent's mechanical execution of
  an accepted PR, bound to explicit human instruction. Acceptance follows the
  worklane. An explicit instruction to merge a named PR accepts that exact head
  unless the human says otherwise. Mechanical rebases onto accepted main do not
  require renewed acceptance when behavior and scope are unchanged. A
  human statement assigning the current lane ownership is sufficient for this
  action. Record acceptance as the receipt comment on the PR
  (spec `#acceptance-receipt`), verify required checks, then merge. No worker merges, no agent decides acceptance, and no agent merges
  unaccepted work. Required failed checks remain blockers until fixed or
  durably waived through a repository-approved path.
- The merge completes the worklane. `Closes #<n>` closes the primary GitHub
  issue; if it is still open, close it with `gh issue close <n> --comment` and
  stop the lane. Do not assume deployment-named labels exist.
- Verify the state change landed, whether performed by repository automation
  or by the owning agent. Do not claim a hook succeeded without readback.
- Record merge and deployment evidence separately. A completion state does
  not establish which environment serves the code. Do not regress completed
  issues or create workflow states merely to match stale instructions.

## Boundaries

- Do not create workflow labels beyond `octo-feather:ready` unless the operator
  explicitly asks.
- Do not create extra PRs for the same issue.
- No worker or reviewer role merges or approves as the human reviewer.
- Only the active owning agent receiving explicit human acceptance and merge
  instruction executes the merge, per Merge And Issue Sync above; no agent
  merges unaccepted work or decides acceptance itself.
