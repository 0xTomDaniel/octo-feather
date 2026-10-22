---
name: push
description: Push the current octo-feather branch and create or update the linked GitHub PR using the target repo's conventions and validation evidence.
---

# Push

## Communication Style

Be extremely concise. Sacrifice grammar for the sake of concision.
No em-dashes or en-dashes. Ever.

Use this skill when an implementer needs to publish branch changes and open or
update the PR for a shaped GitHub issue.

## Prerequisites

- Push and open a PR only as [consent](../github-pr/SKILL.md#consent) allows. Otherwise stop at local commits and report.
- `gh auth status` succeeds.
- `git remote -v` shows the intended target repo.
- Target repo validation has run or the failure is recorded with rationale.

## Workflow

1. Identify the branch with `git branch --show-current`.
2. Verify the branch is the lane's, named per docs/adr/0011.
3. Push with upstream tracking, naming the branch, as its own command (never
   `HEAD`, never chained): `git push -u origin <branch>`.
4. If push is rejected because the branch is stale, use the `pull` skill, rerun
   validation, then push again.
5. Use `--force-with-lease` only when history was deliberately rewritten.
6. Create or update exactly one PR for the issue.
7. PR title should match the GitHub issue title unless the
   target repo has a stronger convention.
8. PR body must start with `Closes #<issue-number>` and include `## Summary`
   and `## Validation`.
9. Return the PR URL.

Do not merge. Surface auth, permissions, branch protection, and workflow errors
directly instead of changing remotes or bypassing policy.
