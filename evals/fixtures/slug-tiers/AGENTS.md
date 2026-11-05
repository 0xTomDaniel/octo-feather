# slugger

Turns titles into URL slugs. Library `slugger.rules`, command `slug TEXT` (exit 2 on text with no letters or digits).

Repo skills: python

## Rules

- The gate has two tiers, `just fast` and `just check`: who runs which, octo-feather templates spec #tpl-gate, #tpl-hooks. A red gate blocks handoff.
- Tests drive `slugger.cli.main` in-process (tests/test_slug.py) or the installed `slug` command (tests/test_installed.py, marked `e2e`). No mocks of our own code.
- `slugger.cli` imports `slugger.rules`, never the reverse (import-linter).
- Integrate worker commits with `just integrate TICKET REF...`; keep the recipe.

## Commands

- `just setup` once.
- `just fast`, `just check`: the gate's tiers.
- `uv run slug "Some Title"` the command.
