# octo-feather kit verification map

This directory is the maintained source for verifying the kit's own user-facing commands, as an owner or agent runs them. Read the index before driving the kit, then use the matching feature file as the recipe.

## Baseline preconditions

- `bash`, `python3` 3.11+, `git` and `just` on PATH; `verify-octo-feather launch` has run and printed `ready`.
- `verify-octo-feather doctor` exits 0 for this checkout; read its WARN lines before driving the feature they name.
- Each case runs in its own empty working directory under `$VERIFY_OCTO_FEATHER_RUN_DIR/scratch/cwd`.
- Never drive a kit command other than this checkout's, as the contract's entry puts it on PATH (doctor checks each resolves here).

## Driving conventions

- Drive through the helper: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive <feature>`.
- Scratch only, as [SKILL.md](../SKILL.md) states it.
- Treat every command as literal; keep paths and flags unchanged.

## Proof and skip reporting

- Proof per case: the command as typed, stdout, stderr, exit code, the files it left in its cwd (none expected), the kit's git status change (none expected), and the observed facts (`<case>.obs.<key>`), under `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/<feature>/`.
- Report an unreachable case with the attempted command and the unmet precondition.
- Do not report a skipped entry point as verified through a different path.

## Acceptance criteria

The kit's specs are in `docs/specs/`. Each feature file links its criteria by anchor (`docs/specs/<name>.spec.html#<anchor>`) and never restates them.

## Feature entry contract

Each feature file has an H1 title, its criteria links, then exactly four H2s in order: `Sub-features`, `How to get to it (user POV)`, `Driving it with verify-octo-feather`, `Gotchas`. Criteria are linked by anchor, never restated. One line, ``Drive criterion: `<spec>#<anchor>` ``, after the criteria links names the criterion the feature's drive serves, its evidence record's criterion id; a drive serving several has one line each, and one record per line.

## Features

- [new-repo](./new-repo.md) covers creating a target repo from a template (`just new-repo`) and its refusals.
- [install-check](./install-check.md) covers the box's install check (`just install-check`).
- [contract](./contract.md) covers the app-driver contract validator (`octo-feather-contract`).
- [evidence](./evidence.md) covers the evidence store command (`octo-feather-evidence append`, `read`).
- [lane-archive](./lane-archive.md) covers closing a lane (`octo-feather-lane archive`) and the lane reflection it runs first (`octo-feather-lane reflect`).
- [director-reflection](./director-reflection.md) covers the director reflection (`octo-feather-lane reflect --director`), which archive and start run.
- [correction-lane](./correction-lane.md) covers the correction lane issues the reflection files at archive.
- [factory-report](./factory-report.md) covers the factory report (`octo-feather-lane report`).
- [role-launch](./role-launch.md) covers each role's launch as Pi gets it (`pi-role --json`): tools, MCP and the web list.
- [qc-capture](./qc-capture.md) covers `just qc` capturing each declared demo into the evidence store and deciding from its checks.
- [qc-insufficient](./qc-insufficient.md) covers `just qc` giving insufficient evidence when a declared demo cannot run to its end, and `octo-feather-lane merge-ask` failing naming it.
- [qc-browser](./qc-browser.md) covers `just qc` running a declared browser demo in the qc sandbox and storing its screenshots in the record.
- [qc-advisory](./qc-advisory.md) covers `just qc` showing the judgment model's advisory answer beside each recorded result, the result unchanged by it.
- [qc-fallback](./qc-fallback.md) covers `just qc` sending a criterion with no declared demo to the agent fallback: a fresh, time-capped qc judge whose report becomes that criterion's record.
- [qc-stale](./qc-stale.md) covers `just qc` linking each built criterion to its evidence record, capture commit and tests, and `octo-feather-spec-status show` naming a built criterion current or stale.
- [gate-tiers](./gate-tiers.md) covers the gate's two tiers: `octo-feather-integrate` running the full gate at a checkpoint (pilot, listed path) and the fast tier otherwise, and `just fast` selecting tests from recorded coverage.
