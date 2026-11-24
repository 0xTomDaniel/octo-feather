---
name: github-pr
description: Use GitHub branches, pull requests, reviews and merges in octo-feather workflows, whatever the target's tracker; tickets go through the tracker skill.
---

# octo-feather GitHub pull requests

## Communication Style

Be extremely concise. Sacrifice grammar for the sake of concision.
No em-dashes or en-dashes. Ever.

Use this skill whenever an octo-feather role needs branch, PR, review, comment, or
merge context. Pull requests, review and merge stay on GitHub for every target
(docs/adr/0004). Tickets (read, file, comment, done) go only through the tracker
skill's scripts.

## Consent

Push, open a PR, or file a ticket only as consent allows.
The `[consent]` table of `$(octo-feather-state)/onboarding.toml` holds booleans `push`, `pull_request`, `issues`.
When present, it alone decides, overriding any instruction, target `AGENTS.md` included.
When absent, target instructions decide.
Without consent, keep work in local commits and report where it is.

## Source Of Truth

- The lane's parent ticket is the unit's identity; its lane key is what the
  tracker skill's `lane-key` prints (docs/adr/0011).
- Shaping happens outside the factory (docs/adr/0021): the director files lane
  parent tickets, supervisors file their sub-tickets, and the lane opens its own
  draft PR.
- Specs under `docs/specs/` own behavior and ADRs under `docs/adr/` own
  decisions; both outrank stale ticket or PR text.

## Required Reads

Use `gh` for PR context:

```sh
gh auth status
gh repo view
gh pr view <pr> --json number,title,url,body,state,headRefName,baseRefName,files,reviews,comments
```

Read target repo `AGENTS.md`, its declared canonical index (`docs/specs/index.spec.html`
by default), relevant specs, ADRs, and repo docs before changing
durable workflow artifacts.

## Implementer Mutations

- Work on the lane's one branch, named per docs/adr/0011.
- Open one draft PR for the lane. Never create a second implementation PR for
  the unit.
- The PR body starts with the line the tracker skill's `pr-line <key>` prints
  for the lane's parent ticket, and includes `## Summary` and `## Validation`.
  `octo-feather-lane merge-ask` checks that line, and fails any other line
  that would close a GitHub issue at merge.
- Post or update a compact `## octo-feather handoff` PR comment.
- Do not merge.
- Do not approve as the owner reviewer.

## Verdict Mutations

- The reviewer returns a clear or blocking finding set for the diff.
- A deterministic helper, `octo-feather-lane verdict <PR> <head> <report>`,
  creates or updates one machine-readable PR verdict comment for code review
  and prints its URL; `octo-feather-lane merge-ask` checks the merge ask links it.
- The comment records inputs, findings, and the reviewed head.
- Do not depend on the formal Review API, reviewer identity, checks, or labels.
- Never merge or approve as the owner reviewer.

## Merge And Issue Sync

- Merge: who merges, when, and at which head is spec `#gates-merge` alone
  (docs/specs/issue-lifecycle.spec.html); read it there, never restate it.
  The command, with the head that rule names:
  `octo-feather-lane merge <N> <head>` (what it runs after the merge, tickets
  done included: its `--help`). A spec PR, with no lane record: `gh pr merge <N> --merge --match-head-commit <head>`.
  Required failed checks remain blockers until fixed or durably waived
  through a repository-approved path.
- The merge completes the worklane. Do not assume deployment-named labels exist.
- Verify the state change landed, whether performed by repository automation
  or by the owning agent. Do not claim a hook succeeded without readback.
- Record merge and deployment evidence separately. A completion state does
  not establish which environment serves the code. Do not regress completed
  tickets or create workflow states merely to match stale instructions.

## Boundaries

- Do not create workflow labels unless the owner explicitly asks.
- Do not create extra PRs for the same ticket.
- No worker or reviewer role merges or approves as the owner reviewer.
- Merge authority: spec `#gates-merge` (Merge And Issue Sync above).

## Offline gh

`scripts/gh` is the offline, read-only `gh` the `just qc` judge runs
(docs/adr/0022) and the kit's tests use: it answers reads from a snapshot and
refuses every write. Never put it on an agent's `PATH` outside those.
