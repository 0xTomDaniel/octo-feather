# app verification map

This directory is the maintained source for verifying the user-facing behavior of the `app` CLI. Read the index before driving the app, then use the matching feature file as the recipe.

## Baseline preconditions

- `node` (at least `package.json` `engines.node`), `python3` 3.11+ and what the contract's `setup` needs on PATH; `verify-app launch` has run and printed `ready`.
- `verify-app doctor` exits 0 for this checkout.
- Each case runs in its own empty working directory under `$VERIFY_APP_RUN_DIR/scratch`.
- Never drive an `app` other than this checkout's `src/cli.ts` (doctor checks it).

## Driving conventions

- Drive through the helper: `.agents/skills/verify-app/scripts/verify-app drive <feature>`.
- Treat every command as literal; keep quoted names, spaces and flags unchanged.
- Assert on `--json` output; check text output only for the text path.

## Proof and skip reporting

- CLI proof is the command, stdout, stderr, exit code, and the files it left (none expected), per case, under `$VERIFY_APP_EVIDENCE_DIR/<feature>/`.
- Report an unreachable case with the attempted command and the unmet precondition.
- Do not report a skipped entry point as verified through a different path.

## Acceptance criteria

What each feature must do lives in this repo's specs, `docs/specs/<name>.spec.html` (the starter one: [app.spec.html](../../../../docs/specs/app.spec.html)). Feature files link their criteria by anchor.

## Feature entry contract

Each feature file has an H1 title, its criteria links, then exactly four H2s in order: `Sub-features`, `How to get to it (user POV)`, `Driving it with verify-app`, `Gotchas`. Criteria are linked by anchor, never restated. One line, ``Drive criterion: `<spec>#<anchor>` ``, after the criteria links names the criterion the feature's drive serves, its evidence record's criterion id.

## Features

- [hello](./hello.md) covers greeting by name, JSON and text output, the empty-name error, and the usage error.
