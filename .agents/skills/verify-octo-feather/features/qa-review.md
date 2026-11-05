# qa-review

Criteria:

- [quality#acceptance-qa-review](../../../../docs/specs/quality.spec.html#acceptance-qa-review)

Drive criterion: `quality#acceptance-qa-review`

## Sub-features

- `run` `octo-feather-qa` on a review case: `REVIEW vr/essay: awaiting review: Do the notes answer the brief?; changed files: notes.md`, then `  output: final message: The notes say hi.` and `  latest review: none`; exit 1.
- `awaiting` `octo-feather-qa --review <run dir> vr/essay`: `REVIEW vr/essay: awaiting review (run <id>)` and the kept output.
- `record` `octo-feather-qa --review <run dir> vr/essay pass "Clear and short."`: `REVIEWED vr/essay: pass (run <id>, kit <sha>, <at>): Clear and short.`
- `next-run` the case run again, its stub now saying `The notes say hello.`: the new final message, then `  latest review: pass (run <first id>, ...): Clear and short.`

## How to get to it (user POV)

- A maintainer adds `review` to a role-transcript case (schema: `.agents/skills/eval-cases/references/schema.md`, Case), runs `just qa`, reads the kept output, then records a verdict with `octo-feather-qa --review`. What is kept, where the verdict lives and how the case counts: `octo-feather-qa --help`, Review.

## Driving it with verify-octo-feather

Preconditions:

- `verify-octo-feather launch` printed `ready`; `verify-octo-feather doctor` exits 0.
- Unprivileged nested user namespaces (`unshare -rm`): the qa sandbox needs them.

Run all cases: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive qa-review`. Evidence: `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/qa-review/`.

The drive writes a scratch suite `vr` with one review case, `essay` (role implementer, a one-file fixture), and runs this checkout's `octo-feather-qa` through the contract's entry, its artifacts and the reviews file under `$VERIFY_OCTO_FEATHER_RUN_DIR/scratch/qa-review/out`. The role's model is the stub `pi` (`QA_STUB_PI` in the helper, first on PATH and on the qa sandbox's PATH): for `SAY: TEXT` in the task it writes TEXT to `notes.md` and says it as its final message. No real model is called.

- **Awaiting review** (`run`, `awaiting`). Observe the lines Sub-features names; exit 1 for the run, 0 for `--review`.
- **Recorded** (`record`). Observe the `REVIEWED` line naming the first run.
- **Next run** (`next-run`). Observe the new output beside the latest verdict and note; exit 1 (how a review case counts: `octo-feather-qa --help`, Review).
- **Side effects.** Every cwd stays empty and the kit's `git status` unchanged; no live lane state, no model spend.

## Gotchas

- The stub's output is canned: the drive proves the keeping, recording and showing, not what a maintainer would decide.
