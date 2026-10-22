## What to build

A target with no CLI, HTTP or UI (ADR 0002): `harness.py score` prints each case's score.

## Acceptance criteria

- [ ] demo#acceptance-a: every case scored
- [ ] demo: `uv run python harness.py score --json` prints the scores
