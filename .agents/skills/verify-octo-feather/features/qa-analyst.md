# qa-analyst

Criteria:

- [quality#acceptance-qa-analyst](../../../../docs/specs/quality.spec.html#acceptance-qa-analyst)

Drive criterion: `quality#acceptance-qa-analyst`

## Sub-features

- `compare` `octo-feather-qa --runs 2 --baseline <before>` on a scratch suite holding one case per flag: the `qa: analysis` block names `va/same` a non-discriminating case, `skill_not_read pull` in `va/facts` a non-discriminating fact, `va/alt` high variance on the current kit and `va/costly` a cost tradeoff (tokens mean 115.0 to 460.0); summary.json `analysis` holds the same; exit 1 (`va/alt` fails a run on the current kit).
- `rerun` `octo-feather-qa --analyze <run dir>` on that stored run, a poison `pi` first on PATH: the same block, exit 0, the poison never started, no sandbox.

## How to get to it (user POV)

- A maintainer reads the `qa: analysis` block after `just qa --runs N --baseline <commit>`, or prints it again with `octo-feather-qa --analyze <run dir>`. The flags, threshold and when the block prints: `octo-feather-qa --help`, Analysis.

## Driving it with verify-octo-feather

Preconditions:

- `verify-octo-feather launch` printed `ready`; `verify-octo-feather doctor` exits 0.
- Unprivileged nested user namespaces (`unshare -rm`): the qa sandbox needs them.

Run all cases: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive qa-analyst`. Evidence: `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/qa-analyst/`.

The drive builds the qa-baseline drive's scratch kit repo (before: the implementer not listing tdd; change: as checked out; [qa-baseline.md](qa-baseline.md)) under `$VERIFY_OCTO_FEATHER_RUN_DIR/scratch/qa-analyst/kit` and a scratch suite `va`: `same` (reads nothing, graded `skill_not_read pull`: passes on both), `facts` (graded `skill_read tdd` and `skill_not_read pull`: fails before, passes at the change, pull passing on both), `alt` (`skill_read tdd`, the stub reading on odd runs only: fails before, 1 of 2 at the change) and `costly` (`skill_not_read pull`, the stub spending 3 more messages when the role lists tdd). The role's model is the stub `pi` (`QA_STUB_PI` in the helper, first on PATH and on the qa sandbox's PATH); no real model is called.

- **Four flags** (`compare`). Observe exit 1 and the block, one line per flag, exactly as Sub-features names them.
- **Rerun** (`rerun`). Observe exit 0, the same block, `rerun.obs.poison` `none`.
- **Side effects.** Every cwd stays empty and the kit's `git status` unchanged; no live lane state, no model spend.

## Gotchas

- The stub's runs are canned: the drive proves the rules, not that a real comparison's cases split this way.
- Time is measured, not canned: on a box loaded enough to slow one kit's runs by the threshold, `va/same` could show as a cost tradeoff instead; rerun the drive on a quieter box.
