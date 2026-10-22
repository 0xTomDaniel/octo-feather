# Kit polish after the Fieldnote run (2026-10-20)

Branch `kit-polish`. Role paths changed: `agents/director.md` (Merges section, kickoff brief), `agents/supervisor.md` (hand-in repo line). Approved by Tom, 2026-10-20 ~11:50 MDT.

## What was run

Deterministic only. No model smoke was run for the role changes: the behaviour they ask for (director asks for a missing brief field, copies it into lane briefs, merges nothing; supervisor uses `octo-feather-integrate` in a repo without the recipe) is listed as owed eval cases in `docs/owed-evals/backlog.md`.

- `tests/accepted.sh`: register, then the review page's Accept hand-off alone, exits 0; a hand-written registry `accepted = true` with no hand-off, a newer comment hand-off, a stale Accept (base moved to an edited spec), an agent-actor hand-off and a missing commit exit 1. The pinned versions were computed by Spec Chat's `review-serve.py` `_spec_page` at spec-chat 183f3ee and recrossed with a local clone.
- Real Fieldnote state (`~/.local/state/spec-chat/hosting/fieldnote/registry.toml` copied with its hand-written `accepted = true` removed, spool in `/private/tmp/fn-spec`): the old `octo-feather-accepted` exits 1 ("no row is accepted; press Accept spec"); the new one exits 0, `accepted 06af3f4d2b2b... handoff=hmvgtzi7g5ri1`; with the row base set to `803ccd8` it exits 1 (Accept was for `06af3f4`'s text).
- `tests/integrate.sh`: `octo-feather-exclude` leaves `*.review/` out of `git status`; a worker commit adding review state, or adding an `integrate` recipe to the justfile, exits 3 with the lane head unchanged; a spec alone integrates.
- `just check` on macOS (this Mac) and in CI.
