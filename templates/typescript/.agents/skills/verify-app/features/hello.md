# hello

Criteria:

- [app#acceptance-hello-json](../../../../docs/specs/app.spec.html#acceptance-hello-json)

Drive criterion: `app#acceptance-hello-json`

## Sub-features

- `hello-json` greets with `--json`.
- `hello-text` greets as plain text.
- `hello-trim` trims surrounding spaces from the name.
- `hello-empty-json` blank name with `--json`: JSON error, exit 2.
- `hello-empty-text` blank name without `--json`: error on stderr, exit 2.
- `hello-no-name` missing name: usage line on stderr, exit 64.

## How to get to it (user POV)

- Run `app hello <name>` or `app hello <name> --json` in a terminal (inside the repo: `node src/cli.ts hello <name> --json`).
- `app` with no command prints the usage line `usage: app hello NAME [--json]`. There is no `--help`.

## Driving it with verify-app

Preconditions:

- `verify-app launch` printed `ready`; `verify-app doctor` exits 0.

Run all cases: `.agents/skills/verify-app/scripts/verify-app drive hello`. Evidence: `$VERIFY_APP_EVIDENCE_DIR/hello/<case>.{cmd,stdout,stderr,exit,files}` and `summary.txt`.

- **JSON greeting** (`json`). Run `app hello <name> --json`, the name `values.name` in `qc.toml`. Observe exit code, stdout JSON (its `text` the contract's `values.greeting`), stderr.
- **Text greeting** (`text`). Run `app hello <name>`. Observe exit code and the stdout line.
- **Trimmed name** (`trimmed`). Run `app hello "  <name>  " --json`. Observe the `name` field.
- **Blank name, JSON** (`empty-json`). Run `app hello "  " --json`. Observe exit code 2, an `error` object on stdout, empty stderr.
- **Blank name, text** (`empty-text`). Run `app hello "  "`. Observe exit code 2, empty stdout, `error: ` on stderr.
- **Missing name** (`no-name`). Run `app hello`. Observe exit code 64, empty stdout, `usage: app hello` on stderr.
- **Side effects.** Every case's `.files` is empty: the command writes nothing where it runs.

## Gotchas

- An unquoted blank name never reaches the app: the shell drops it and the app sees a missing name (usage, exit 64). That is not the empty-name path; quote it (`"  "`).
- `--help` or any unknown flag is not handled: Node's `parseArgs` throws, and the process exits 1 with a stack trace on stderr. Doctor uses `app` with no command (exit 64) instead.
- The missing-name usage error is text on stderr even with `--json`; only the empty-name error is JSON.
- Node below `package.json` `engines.node` cannot run `src/cli.ts` (no type stripping); doctor fails on it.
