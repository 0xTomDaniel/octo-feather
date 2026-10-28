---
name: verify-app
description: "Drive this repo's `app` CLI (a short-lived Python command, no server, no browser) the way a user does and keep the proof: stdout, stderr, exit code and files written per command. Use to prove a CLI change works before handoff, to check a criterion of the app's behavior, or when anything about the installed `app` command looks off."
---

# verify-app

The app's only user surface is the `app` CLI (`app hello <name> [--json]`). There is no server, browser, database or interactive mode; every command is one short-lived process. The helper below runs each command the real user path: the installed `app` console script in this repo's `.venv`, as a subprocess, in its own empty working directory.

Helper (executable, plain bash plus `uv`):

```
.agents/skills/verify-app/scripts/verify-app setup|launch|doctor|drive <feature>|cleanup|run
```

`run` does launch, doctor, `drive hello`, cleanup, then lists the evidence folder to show it survived. Exit 0 means every step passed.

## Run state and evidence

- `VERIFY_APP_RUN_DIR`: run state (the `state` file, scratch working dirs). Default `${TMPDIR:-/tmp}/verify-app.<uid>.<checkout-hash>/run`.
- `VERIFY_APP_EVIDENCE_DIR`: proof. Default `${TMPDIR:-/tmp}/verify-app.<uid>.<checkout-hash>/evidence`.
- Both default outside the git dir, so the helper runs unchanged where HOME and the git dir are read-only and /tmp is private. `launch` prints the resolved paths.
- `launch` exits non-zero naming the folder when it cannot write the run state or evidence folder. It never reports ready without a written state file.
- Isolation: two checkouts get different defaults. Two runs of the same checkout at once must set distinct `VERIFY_APP_RUN_DIR` and `VERIFY_APP_EVIDENCE_DIR`, or they overwrite each other's scratch and proof.

## Launch

`verify-app launch` checks both folders are writable, runs `setup` (`uv sync --locked` in the repo root: the repo's own install, same as `just setup` minus the hook), then records in `$VERIFY_APP_RUN_DIR/state` the `app` command path (`<repo>/.venv/bin/app`), the venv python, the repo root and the git rev. Ready is the line `verify-app: ready: app=<path> rev=<rev>`. No process is left running: each drive case starts its own process and waits for it to exit.

## Doctor

`verify-app doctor` (read-only) answers "is this install worth driving?": the recorded `app` command exists, `app --help` exits 0 and lists `hello`, the installed package version, `app` imports from this checkout's `src/` (not some other install), the checkout is still at the launch rev (WARN means relaunch), the scratch dir exists. Exit non-zero on any FAIL. Run it first whenever a drive result looks wrong.

## Drive

`verify-app drive <feature>` runs every case of one feature from [features/](features/README.md). Each case:

- runs `"$APP" <args>` with cwd an empty `$VERIFY_APP_RUN_DIR/scratch/<case>`;
- writes `<case>.cmd` (argv as typed), `<case>.stdout`, `<case>.stderr`, `<case>.exit`, and `<case>.files` (files the command left in its cwd; must be empty) to `$VERIFY_APP_EVIDENCE_DIR/<feature>/`;
- appends `PASS|FAIL <case>: <cmd>` to `<feature>/summary.txt` and prints it with the case's stdout, stderr and exit code.

To drive one command by hand, the same way: `cd "$(mktemp -d)" && <repo>/.venv/bin/app hello Ada --json; echo "exit $?"`. Use `--json` for assertions; plain text output is for the text path only. No PTY is used: the app has no interactive mode and does not branch on whether stdout is a terminal. If that changes, drive the text cases in a PTY (`script -qec`).

## Evidence

Proof standards:

- Exercise the installed `app` command, never `app.cli.main` in-process or internal functions; tests already cover those.
- Capture the action (`.cmd`) and the resulting state (stdout, stderr, exit code), not just a PASS line.
- Check side effects: the CLI must write no files; `.files` records anything it left.
- No mocks: the app has no external boundary.
- Report a skipped case as skipped, never as proved through a different case.

Evidence lives at `$VERIFY_APP_EVIDENCE_DIR`: `doctor.txt` (from `run`) and one folder per driven feature.

## Cleanup

`verify-app cleanup` removes the scratch dirs and state file, then the run dir if empty. Nothing is killed: the helper never leaves a process running, and never kills by name. Evidence is never removed; cleanup prints where it stays. Run cleanup after every failed attempt too.

## Features

See [features/README.md](features/README.md). The map is the maintained verification source; keep it honest with the `maintain-verification-skill` skill.
