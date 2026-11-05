# contract

Criteria:

- [quality#acceptance-qc-contract](../../../../docs/specs/quality.spec.html#acceptance-qc-contract)

Drive criterion: `quality#acceptance-qc-contract`

## Sub-features

- `kit` the kit's own `qc.toml`: ok.
- `missing-entry` a contract without `[entry]`: names it.
- `no-contract` a folder with no `qc.toml`: names it.

## How to get to it (user POV)

- In any repo with the kit's `scripts/` on PATH: `octo-feather-contract .`, or `octo-feather-contract path/to/qc.toml`.

## Driving it with verify-octo-feather

Preconditions:

- `verify-octo-feather launch` printed `ready`; `verify-octo-feather doctor` exits 0.

Run all cases: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive contract`. Evidence: `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/contract/`. Scratch contracts are written under `$VERIFY_OCTO_FEATHER_RUN_DIR/scratch/contract/`.

- **Kit contract** (`kit`). Run `octo-feather-contract <kit>`. Observe exit 0 and exactly `octo-feather-contract: <kit>/qc.toml: ok (format 2)`.
- **Missing key** (`missing-entry`). Run it on a scratch `qc.toml` with format, services, fixture and values but no entry. Observe exit 1 and `missing entry`.
- **No contract** (`no-contract`). Run it on an empty scratch folder. Observe exit 1 and `no qc.toml at`.
- **Side effects.** Every cwd stays empty and the kit's `git status` unchanged.

## Gotchas

- The argument is a repo folder or a `qc.toml` path; with none it reads `./qc.toml`, so a case's empty cwd would read as no contract.
