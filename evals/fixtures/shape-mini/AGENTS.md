# app

Small Python app (an eval fixture of the octo-feather kit). Everything it does is reachable through its CLI, `app`, and every command prints JSON with `--json`.

## Rules

- Behavior lives in Spec Chat specs, `docs/specs/*.spec.html`; decisions in `docs/adr/`; terms in `GLOSSARY.md`.
- Tests are integration and end-to-end only, through the CLI: `tests/test_cli.py` calls `app.cli.main` in-process and runs `app` as a subprocess.
- `app.cli` may import `app.core`; `app.core` never imports `app.cli`.

## Commands

- `uv run pytest -q` the tests.
- `uv run app hello Ada --json` the app.
