# Prose last: structure, then checks, then Jev, then prompts

An agent mistake is fixed as high on this ladder as it will go: first the codebase's structure and types make it impossible; then lint and `just check` reject it with an error that names the fix; then Jev judges what is fuzzy and in between (does the UI match the spec, does a report answer its question); prose in a role file or skill comes last, only for process behaviour nothing above can catch (messaging the wrong pane, skipping a report). A clean, protected codebase is how we encourage good behaviour. Any change to a prompt, role file or vendored-skill patch ships with an eval case that fails before the change and passes after it, shaped like scaling-octo-engine's `evals/role-workflows/<case>/` (`cases.json`, `harness.py`, `graders/`), run by `just qa`. This follows pstack. Decided by Tom, 2026-10-18.

Until `just qa` exists, an edit to a prompt, role file or skill patch that changes behaviour ships with a recorded live smoke run in `evidence/` (as `evidence/block3-comms-smoke.md` records a real chain), and its eval case is listed as owed in `docs/future.md`. A path repair or the deletion of a dead trigger changes no behaviour and needs only `check-refs`. Decided by Tom (owner), 2026-10-19.

## Considered options

- annotateanything's rule: fix agent behaviour only in prompts, never with blocking guardrails. Rejected: prose is the rung nothing enforces.
