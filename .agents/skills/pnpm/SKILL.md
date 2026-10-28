---
name: pnpm
description: pnpm package-management policy for octo-feather implementer work when durable repo signals show pnpm is the selected package manager.
---

# pnpm

## Communication Style

Be extremely concise. Sacrifice grammar for the sake of concision.
No em-dashes or en-dashes. Ever.

Use this skill only when the repo already selects pnpm through `pnpm-lock.yaml`,
`pnpm-workspace.yaml`, a `packageManager` field, `.npmrc`, or repo docs.

## Rules

- Use pnpm for installs, scripts, and lockfile updates in pnpm repos.
- Do not switch package managers as part of unrelated issue work.
- Keep lockfile changes scoped to dependency changes required by the issue.
- Prefer repo scripts over ad hoc commands.
- Preserve workspace boundaries and existing `.npmrc` behavior.
- Record exact pnpm validation commands in the PR or handoff.

Adding a dependency: agents/implementer.md Rules. Stop for clarification before
switching package managers.
