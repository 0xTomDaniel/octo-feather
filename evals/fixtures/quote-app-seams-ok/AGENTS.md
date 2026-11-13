# app

Order quotes for the shop. Its CLI, `app quote`, prints a quote for an order; `--json` prints it as JSON. The package's public library API is what `app/__init__.py` exports.

Repo skills: python

## Rules

- `just check` is the only gate: lint, types, import boundaries, tests. Agents, the git hook and CI run the same command. A red gate blocks handoff.
- Tests are pytest, under `tests/`. One or two tests per acceptance criterion; keep the suite small.
- `app.cli` may import `app.pricing`, which may import `app.rates`; never the other way (import-linter enforces it).
- Integrate worker commits with `just integrate N REF...` (the kit's `octo-feather-integrate`); keep the recipe.

## Commands

- `just setup` once: `uv sync` and the git hook.
- `just check` the gate.
- `uv run app quote uk 60.00:2 --json` the app.
