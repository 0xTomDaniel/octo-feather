# Integration is a script, not an agent

The supervisor integrates with `just integrate N REF...` (`scripts/octo-feather-integrate`), which finds lane gh<N>'s worktree, merges each named worker branch (`--no-ff`) or cherry-picks each named commit (`-x`), then runs that worktree's `just check`. It is all or nothing: on any conflict or a red gate it resets the lane branch to where it started and exits non-zero (1 conflict, 2 red), and the supervisor hands the problem to an implementer, whose resolved branch is then integrated like any other. It never pushes. `tests/integrate.sh` covers merge, cherry-pick, conflict and red gate inside `just check`. Decided by Tom, 2026-10-18. The templates define `just integrate` calling `octo-feather-integrate` (and `just qc` calling `octo-feather-qc`), and `check-templates` fails a template without them, so a repo the kit creates has both. A repo the kit did not create, such as a brownfield or take-home hand-in repo, never gains them: the supervisor runs the kit's command itself, `octo-feather-integrate` or `octo-feather-qc` on its PATH, with the same arguments. `octo-feather-integrate` refuses (exit 3, rolled back) a worker commit that adds either recipe to the target's justfile or adds Spec Chat review state (`*.review/`, which `octo-feather-exclude` keeps in the repo's git info/exclude at start, shaping and Spec Chat install), so the hand-in's tracked tree holds only the product and its specs. Decided by Tom (owner), 2026-10-19; recipes and review state kept out of repos the kit did not create by Tom (owner), 2026-10-20 (pilot 1 run).

## Considered options

- An integrator agent. Rejected: a model call per merge for work git does deterministically, and a second writer with judgement over conflicts that an implementer resolves better in its own worktree.

## Consequences

- One writer per lane branch: only the supervisor's script writes it.
- Integration is not the merge: it never pushes; the lane's pull request reaches main only by the merge spec `#gates-merge` owns (ADR 0007).
- Implementers merge the integration tip into their own branch before reporting (implement-spec step 4), so most conflicts never reach the script.
