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

Each feature file has an H1 title, its criteria links, then exactly four H2s in order: `Sub-features`, `How to get to it (user POV)`, `Driving it with verify-octo-feather`, `Gotchas`. Criteria are linked by anchor, never restated. One line, ``Drive criterion: `<spec>#<anchor>` ``, after the criteria links names the criterion the feature's drive serves, its evidence record's criterion id.

## Features

- [new-repo](./new-repo.md) covers creating a target repo from a template (`just new-repo`) and its refusals.
- [install-check](./install-check.md) covers the box's install check (`just install-check`).
- [contract](./contract.md) covers the app-driver contract validator (`octo-feather-contract`).
- [evidence](./evidence.md) covers the evidence store command (`octo-feather-evidence append`, `read`).
