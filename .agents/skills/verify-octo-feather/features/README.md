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
- [correction-intake](./correction-intake.md) covers which findings make a correction lane due and the read-only intake report of the open ones (`octo-feather-lane intake`).
- [factory-report](./factory-report.md) covers the factory report (`octo-feather-lane report`): its director reflection line, its owner-caught headline and a repository's full gate time against its gate-time budget.
- [role-launch](./role-launch.md) covers each role's launch as Pi gets it (`pi-role --json`): tools, MCP and the web list.
- [skill-loading](./skill-loading.md) covers which skills Pi loads for a role: a launch refused naming each skill Pi did not load, the listed skills offered exactly, and the gate's `check-skills` (criteria: skills#acceptance-launch-refuses-unloaded, skills#acceptance-only-listed, skills#acceptance-skill-frontmatter).
- [shape](./shape.md) covers the owner starting the shaper with `just shape` in a target with Spec Chat linked (`just spec-chat`): Pi offered exactly the role file's skills, Spec Chat's from the target, none from home (criterion: roles#acceptance-shaper-launch).
- [qc-capture](./qc-capture.md) covers `just qc` capturing each declared demo into the evidence store and deciding from its checks.
- [qc-insufficient](./qc-insufficient.md) covers `just qc` giving insufficient evidence when a declared demo cannot run to its end, and `octo-feather-lane merge-ask` failing naming it.
- [qc-browser](./qc-browser.md) covers `just qc` running a declared browser demo in the qc sandbox and storing its screenshots in the record.
- [qc-sandbox](./qc-sandbox.md) covers the qc sandbox run by hand (`scripts/octo-feather-qc-sandbox -- CMD`) on srt: its proof and its refused escapes.
- [qc-sandbox-cost](./qc-sandbox-cost.md) covers the qc sandbox's CPU per run around a judge that does nothing, run after run.
- [qc-advisory](./qc-advisory.md) covers `just qc` showing the judgment model's advisory answer beside each recorded result, the result unchanged by it.
- [qc-fallback](./qc-fallback.md) covers `just qc` sending a criterion with no declared demo to the agent fallback: a fresh, time-capped qc judge whose report becomes that criterion's record.
- [qc-stale](./qc-stale.md) covers `just qc` linking each built criterion to its evidence record, capture commit and tests, and `octo-feather-spec-status show` naming a built criterion current or stale.
- [starter-acceptance](./starter-acceptance.md) covers a template-born repo's starter criterion judged by `just qc` from the record its tagged acceptance test left in the claims gate, with no demo.
- [gate-tiers](./gate-tiers.md) covers the gate's two tiers: `octo-feather-integrate` running the full gate at a checkpoint (pilot, listed path) and the fast tier otherwise, `just fast` selecting tests from recorded coverage, `just fast-list` its dry run, and a map written past a red item.
- [template-tiers](./template-tiers.md) covers a template-born repo's two tiers: `just check` showing each test kind and the shared fixture prepared once, `just fast` picking tests with the stack's own tool, the git hook on `just fast`, each run's trend line and the factory report's gate budget block from it.
- [merge-ask-proof](./merge-ask-proof.md) covers `octo-feather-lane merge-ask` refusing a lane head with no current recorded full gate pass, and `octo-feather-integrate` running a brownfield target's own gate in full at every integration with no recipe added, and the merge ask's gate time against the target's gate-time budget, shown, never decided on.
- [one-execution](./one-execution.md) covers a target's final full gate, given the lane's claims, running a tagged acceptance test once in the qc sandbox into one evidence record, and one `just qc` naming every spec's status file judging each criterion from its record without rerunning it, in one status-only commit.
- [one-execution-incomplete](./one-execution-incomplete.md) covers `just qc` giving insufficient evidence, never the agent fallback, for a claimed criterion whose tagged test the gate skipped.
- [qa-runs](./qa-runs.md) covers the factory evals running each case several times (`octo-feather-qa --runs N`; criterion: quality#acceptance-qa-repeats).
- [qa-baseline](./qa-baseline.md) covers a case's time and tokens over several runs and a baseline kit compared beside the current one (`octo-feather-qa --runs N --baseline COMMIT`; criteria: quality#acceptance-qa-cost, quality#acceptance-qa-baseline).
- [qa-analyst](./qa-analyst.md) covers the deterministic analysis of a baseline comparison and its rerun on a stored run (`octo-feather-qa --analyze`; criterion: quality#acceptance-qa-analyst).
- [qa-review](./qa-review.md) covers an eval case a maintainer reviews: its kept output, a recorded verdict and note, and the next run showing them (`octo-feather-qa --review`; criterion: quality#acceptance-qa-review).
- [qa-history](./qa-history.md) covers a regression case whose fixture is a real repository at a commit (the kit's own history or a local clone; criterion: quality#acceptance-qa-history).
- [run-slots](./run-slots.md) covers the box's heavy-run slot: a lane's `just test` over more than heavy_items items refused without its grant, the director's grant (`octo-feather-slot grant`), `octo-feather-slot status`, and the granted run holding the slot.
