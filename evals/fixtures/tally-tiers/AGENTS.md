# tally

Word-count CLI built with the octo-feather kit: `tally PATH` prints a file's word count, `--json` prints it as JSON.

Repo skills: python

## Rules

- The gate has two tiers, `just fast` and `just check`: who runs which, octo-feather templates spec #tpl-gate, #tpl-hooks. A red gate blocks handoff.
- Tests are integration and end-to-end only, each kind as octo-feather quality spec #test-kinds says: integration in `tests/integration/`, end-to-end in `tests/e2e/` (its conftest.py marks each `e2e`). No mocks of our own code. One or two tests per acceptance criterion.
- `tally.cli` may import `tally.count`; `tally.count` never imports `tally.cli` (import-linter enforces it).
- Integrate worker commits with `just integrate TICKET REF...` (the kit's `octo-feather-integrate`); keep the recipe.

## Commands

- `just setup` once: `uv sync`.
- `just fast` and `just check` the gate's tiers.
- `uv run tally README.md --json` the app.
