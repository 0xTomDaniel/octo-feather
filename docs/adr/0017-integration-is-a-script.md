# Integration is a script, not an agent

The supervisor integrates with `just integrate N REF...` (`scripts/octo-feather-integrate`), which finds lane gh<N>'s worktree, merges each named worker branch (`--no-ff`) or cherry-picks each named commit (`-x`), then runs that worktree's `just check`. It is all or nothing: on any conflict or a red gate it resets the lane branch to where it started and exits non-zero (1 conflict, 2 red), and the supervisor hands the problem to an implementer, whose resolved branch is then integrated like any other. It never pushes. `tests/integrate.sh` covers merge, cherry-pick, conflict and red gate inside `just check`. Decided by Tom, 2026-10-18. Every target repo defines `just integrate` calling `octo-feather-integrate`; the templates do, and `check-templates` fails a template without it. Decided by Tom (owner), 2026-10-19.

## Considered options

- An integrator agent (octo-lite's role). Rejected: a model call per merge for work git does deterministically, and a second writer with judgement over conflicts that an implementer resolves better in its own worktree.

## Consequences

- One writer per lane branch: only the supervisor's script writes it.
- Implementers merge the integration tip into their own branch before reporting (implement-spec step 4), so most conflicts never reach the script.
