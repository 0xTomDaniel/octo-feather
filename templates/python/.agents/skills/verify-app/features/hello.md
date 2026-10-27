# hello

`app hello <name>` greets a user by name, as text or as JSON with `--json`, and refuses a blank name with an error and a non-zero exit.

Criteria (kit templates spec, until this repo has its own specs, whose criteria then replace these links):

- [acceptance-cli-json](https://github.com/0xTomDaniel/octo-feather/blob/main/docs/specs/templates.spec.html#acceptance-cli-json)
- [acceptance-starter-verify](https://github.com/0xTomDaniel/octo-feather/blob/main/docs/specs/templates.spec.html#acceptance-starter-verify)

## Sub-features

- `hello-json` greets with `--json`.
- `hello-text` greets as plain text.
- `hello-trim` trims surrounding spaces from the name.
- `hello-empty-json` blank name with `--json`: JSON error, exit 2.
- `hello-empty-text` blank name without `--json`: error on stderr, exit 2.

## How to get to it (user POV)

- Run `app hello <name>` or `app hello <name> --json` in a terminal (inside the repo after `just setup`: `uv run app hello <name> --json`).
- `app --help` and `app hello --help` list the command.

## Driving it with verify-app

Preconditions:

- `verify-app launch` printed `ready`; `verify-app doctor` exits 0.

Run all cases: `.agents/skills/verify-app/scripts/verify-app drive hello`. Evidence: `$VERIFY_APP_EVIDENCE_DIR/hello/<case>.{cmd,stdout,stderr,exit,files}` and `summary.txt`.

- **JSON greeting** (`json`). Run `app hello <name> --json`, the name `values.name` in `qc.toml`. Observe exit code, stdout JSON, stderr.
- **Text greeting** (`text`). Run `app hello <name>`. Observe exit code and the stdout line.
- **Trimmed name** (`trimmed`). Run `app hello "  <name>  " --json`. Observe the `name` field.
- **Blank name, JSON** (`empty-json`). Run `app hello "  " --json`. Observe exit code 2, an `error` object on stdout, empty stderr.
- **Blank name, text** (`empty-text`). Run `app hello "  "`. Observe exit code 2, empty stdout, `error: ` on stderr.
- **Side effects.** Every case's `.files` is empty: the command writes nothing where it runs.

## Gotchas

- An unquoted blank name never reaches the app: the shell drops it and argparse exits 2 with usage on stderr. That is not the empty-name path; quote it (`"  "`).
- argparse usage errors also exit 2. Tell them apart from the empty-name error by stdout (JSON `error` object) and stderr (`usage:`).
- `uv run app ...` may sync the venv first; use the launched `bin/app` (the contract's entry) for evidence so no install step mixes into the transcript.
