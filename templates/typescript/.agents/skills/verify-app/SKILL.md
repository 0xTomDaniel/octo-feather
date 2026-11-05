---
name: verify-app
description: "Drive this repo's `app` CLI (a short-lived Node command running `src/cli.ts`, no build, no server, no browser) the way a user does and keep the proof: stdout, stderr, exit code and files written per command. Use to prove a CLI change works before handoff, to check a criterion of the app's behavior, or when anything about the `app` command looks off."
---

# verify-app

The app's only user surface is the `app` CLI (`app hello <name> [--json]`). There is no server, browser, database or interactive mode; every command is one short-lived process. `package.json` maps the `app` bin to `src/cli.ts`, which Node runs directly (type stripping, no build step). The helper below runs each command the real user path: the `app` command the contract's entry declares, as a package manager's bin shim runs it, as a subprocess, in its own empty working directory.

## Helpers

One helper, [`scripts/verify-app`](scripts/verify-app), executable: a thin `sh` launcher that runs [`scripts/verify-app.ts`](scripts/verify-app.ts) with `node` (type stripping, no build). It needs Node and this repo's packages installed (`just setup`), no `python3`: the contract is read with the TOML package `smol-toml` (a dev dependency in `package.json`). Without the install, every command that reads the contract (`setup`, `launch`, `run`) exits 1 naming `smol-toml` and `just setup`. `tsconfig.json` includes the script, so `just check` types and lints it. Run it from anywhere; it finds the repo from its own path:

```
.agents/skills/verify-app/scripts/verify-app setup             # the contract's setup only
.agents/skills/verify-app/scripts/verify-app launch            # see Launch
.agents/skills/verify-app/scripts/verify-app doctor            # see Doctor
.agents/skills/verify-app/scripts/verify-app drive <feature>   # see Drive; features: hello
.agents/skills/verify-app/scripts/verify-app cleanup           # see Cleanup
.agents/skills/verify-app/scripts/verify-app run               # all of the above, end to end
```

`run` does launch, doctor, `drive hello`, cleanup, then lists the evidence folder to show it survived. Exit 0 means every step passed. Any other argument prints the usage line and exits 1.

## Contract

[`qc.toml`](../../../qc.toml) at the repo root is this app's driver contract (octo-feather quality spec `#qc-contract`); what it declares is that spec section's, not repeated here. The helper invokes only what it declares; edit the contract, never the helper, to change any of it. How the helper uses each key:

- `format`: the helper reads format 2.
- `setup`: `setup` and `launch` run it.
- `entry.command`: `launch` writes it as `bin/app` in the run state; every case runs that with its arguments.
- `services`: none for this CLI. The helper starts no service: `launch` fails naming any declared one.
- `fixture`: none for this app. `drive` runs each declared `reset` before its cases.
- `demo`: not read by the helper: per-criterion metadata for `just qc` (see Acceptance).
- `tags`: the command `just qc` collects the tagged tests with (`tests/qc-tags.ts`, Vitest's own collection). The helper does not read it.
- `values`: the hello drive greets `values.name` and expects the greeting `values.greeting`, a worked example the helper compares against, never rebuilds.

What each key means and how its commands run: the kit's `schemas/qc.v2.schema.json`. Validate the contract with the kit's `octo-feather-contract` (prints ok, or names the missing or wrong key).

## Run state and evidence

- `VERIFY_APP_RUN_DIR`: run state (the `state` file, the `bin/app` command, scratch working dirs). Default `${TMPDIR:-/tmp}/verify-app.<uid>.<checkout-hash>/run`.
- `VERIFY_APP_EVIDENCE_DIR`: proof. Default `${TMPDIR:-/tmp}/verify-app.<uid>.<checkout-hash>/evidence`.
- Both default outside the git dir, so the helper runs unchanged where HOME and the git dir are read-only and /tmp is private. `launch` prints the resolved paths.
- `launch` exits non-zero naming the folder when it cannot write the run state or evidence folder. It never reports ready without a written state file.
- Isolation: two checkouts get different defaults. Two runs of the same checkout at once must set distinct `VERIFY_APP_RUN_DIR` and `VERIFY_APP_EVIDENCE_DIR`, or they overwrite each other's scratch and proof.

## Launch

`verify-app launch` needs the repo's packages installed (`just setup`; see Helpers). It checks both folders are writable, reads the contract (fails on any declared service), runs its `setup`, writes the `app` command (the contract's entry) to `$VERIFY_APP_RUN_DIR/bin/app`, then records in `$VERIFY_APP_RUN_DIR/state` the contract as read, that command, the `node` path, the repo root and the git rev. Ready is the line `verify-app: ready: app=<path> entry=<entry.command> rev=<rev>`. No process is left running: each drive case starts its own process and waits for it to exit.

## Doctor

`verify-app doctor` (read-only) answers "is this install worth driving?": the recorded `app` command exists, the contract's entry it runs, `node` meets `package.json` `engines.node` (older Node cannot strip types), `app` with no command exits 64 with the usage line naming `hello`, the package version, the checkout is still at the launch rev (WARN means relaunch), the scratch dir exists. Exit non-zero on any FAIL. Run it first whenever a drive result looks wrong.

## Drive

`verify-app drive <feature>` resets the contract's fixtures, then runs every case of one feature from [features/](features/README.md) with the contract's values. Each case:

- runs `"$APP" <args>` with cwd an empty `$VERIFY_APP_RUN_DIR/scratch/<case>`;
- writes `<case>.cmd` (argv as typed), `<case>.stdout`, `<case>.stderr`, `<case>.exit`, and `<case>.files` (files the command left in its cwd; must be empty) to `$VERIFY_APP_EVIDENCE_DIR/<feature>/`;
- appends `PASS|FAIL <case>: <cmd>` to `<feature>/summary.txt` and prints it with the case's stdout, stderr and exit code.

To drive one command by hand, the same way: after `launch`, `cd "$(mktemp -d)" && <run state>/bin/app hello <name> --json; echo "exit $?"` (`launch` prints the run state folder). Use `--json` for assertions; plain text output is for the text path only. No PTY is used: the app has no interactive mode and does not branch on whether stdout is a terminal. If that changes, drive the text cases in a PTY (`script -qec`).

## Evidence

Proof standards:

- Exercise the `app` command as a process, never `main` from `src/cli.ts` in-process or `src/core.ts` functions; tests already cover those.
- Capture the action (`.cmd`) and the resulting state (stdout, stderr, exit code), not just a PASS line.
- Check side effects: the CLI must write no files; `.files` records anything it left.
- No mocks: the app has no external boundary.
- Report a skipped case as skipped, never as proved through a different case.

Evidence lives at `$VERIFY_APP_EVIDENCE_DIR`: `doctor.txt` (from `run`) and one folder per driven feature. That folder is scratch: the next drive of the feature replaces it.

The kept record is this repo's evidence store (octo-feather quality spec `#evidence-store`), outside the repo and both folders above: every `drive`, passed or failed, appends one record through the kit's `octo-feather-evidence` (on PATH with the kit's `scripts/`; a drive fails without it) and prints `verify-app: evidence record <id> (criterion <spec>#<anchor>; ...)`. The record holds the feature folder's files as outputs and names the commit, the criterion, the contract and fixture versions:

- The criterion is the one the feature file's `Drive criterion:` line names; `octo-feather-evidence` hashes its text from this repo's spec (`docs/specs/<spec>.spec.html`, the element with that anchor). With no such element the drive fails naming the criterion, and no record is kept.
- Read a criterion's records at a commit: `octo-feather-evidence read --criterion <spec>#<anchor> --commit <rev>` (`--json` for data). Where the store lives and the record format: `octo-feather-evidence --help`.

## Acceptance

The starter criterion `app#acceptance-hello-json` is proven by its acceptance test, the end-to-end test in `tests/cli.e2e.test.ts` tagged with it through a Vitest tag (`{ tags: ["<spec>#<anchor>"] }`), its command run through `qcCommand` (`tests/qc-capture.ts`) (octo-feather quality spec `#qc-capture`). The lane's final full gate, told the claims, runs it once in the qc sandbox and stores its record; `just qc` judges the criterion from that record by the test's own assertions, with no separate demo (`qc.toml` declares none for it):

```
OCTO_FEATHER_QC_CLAIMS=app#acceptance-hello-json just check          # prints: qc capture: app#acceptance-hello-json: record <id>, 1 case(s): ... passed
just qc docs/specs/app.status.json <PR> acceptance-hello-json        # PASS ...; evidence complete; decision tagged test assertions; record <id>
```

What a claims run refuses and when a record is complete: quality spec `#qc-capture`, `#qc-judgment`. `just qc` needs the spec's status file (`octo-feather-spec-status init docs/specs/app.spec.html <accepted commit>`, committed). A new criterion's acceptance test is tagged the same way. The drives below are this skill's own proof of a change, apart from that record.

## Cleanup

`verify-app cleanup` removes the scratch dirs, the `bin/app` command and the state file, then the run dir if empty. Nothing is killed: the helper never leaves a process running, and never kills by name. Evidence is never removed, and the evidence store is never touched; cleanup prints where the evidence folder stays. Run cleanup after every failed attempt too.

## Features

See [features/README.md](features/README.md). The map is the maintained verification source; keep it honest with the `maintain-verification-skill` skill.
