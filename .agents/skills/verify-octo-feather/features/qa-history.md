# qa-history

Criteria:

- [quality#acceptance-qa-history](../../../../docs/specs/quality.spec.html#acceptance-qa-history)

Drive criterion: `quality#acceptance-qa-history`

## Sub-features

- `whole-tree` `octo-feather-qa` on a case whose fixture is the kit's own repository at the checkout's HEAD commit: `PASS vh/tree`, and the role's final message `files=<the commit's tracked files> commits=1 deep=ok`, so it ran on that whole tree, one commit on main.
- `unknown-commit` `check-evals` on the same case at a commit the kit lacks: exit 1, `vh/cases.json case tree: field fixture.commit: no commit 000...0 in <kit>`.

## How to get to it (user POV)

- A maintainer writes a regression case whose `fixture` is `{"repo", "commit"}` (the form: `.agents/skills/eval-cases/references/schema.md`, Case) and runs it with `just qa`, before the fix with `--kit-ref <commit before>` and at it.

## Driving it with verify-octo-feather

Preconditions:

- `verify-octo-feather launch` printed `ready`; `verify-octo-feather doctor` exits 0.
- Unprivileged nested user namespaces (`unshare -rm`): the qa sandbox needs them.
- The checkout's HEAD is a commit (the drive reads its tree, not the working tree).

Run all cases: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive qa-history`. Evidence: `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/qa-history/`.

The drive writes a scratch suite `vh` with one case, `tree` (role implementer, `fixture` `{"repo": "kit", "commit": <HEAD>}`), and runs this checkout's `octo-feather-qa` and `check-evals` through the contract's entry, artifacts under `$VERIFY_OCTO_FEATHER_RUN_DIR/scratch/qa-history/out`. The role's model is the stub `pi` (`QA_STUB_PI` in the helper, first on PATH and on the qa sandbox's PATH): with `TREE` in the task it reports the case repo's tracked file count, its commit count and whether a deep kit path is there. No real model is called.

- **Whole tree** (`whole-tree`). Observe exit 0, `PASS vh/tree`, and `whole-tree.obs.said` equal to `whole-tree.obs.want`.
- **Unknown commit** (`unknown-commit`). Observe exit 1 naming the case and `fixture.commit`.
- **Side effects.** Every cwd stays empty and the kit's `git status` unchanged; no live lane state, no model spend.

## Gotchas

- The kit's tree holds a uv.lock, so the case repo's setup syncs it (`octo-feather-qa --help`): a box without the kit's packages in its uv cache fails the setup, naming uv.
