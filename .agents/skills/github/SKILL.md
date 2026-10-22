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

- Work on the lane's one branch, named per docs/adr/0011.
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

- Merge: who merges, when, and at which head is spec `#gates-merge` alone
  (docs/specs/issue-lifecycle.spec.html); read it there, never restate it.
  The command, with the head that rule names:
  `gh pr merge <N> --merge --match-head-commit <head>`.
  Required failed checks remain blockers until fixed or durably waived
  through a repository-approved path.
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
- Merge authority: spec `#gates-merge` (Merge And Issue Sync above).
