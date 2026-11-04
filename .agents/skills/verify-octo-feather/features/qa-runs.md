# qa-runs

Criteria:

- [quality#acceptance-qa-repeats](../../../../docs/specs/quality.spec.html#acceptance-qa-repeats)

Drive criterion: `quality#acceptance-qa-repeats`

## Sub-features

- `alternating` `octo-feather-qa --runs 4` on a case whose stub role passes on odd runs and fails on even ones: an indented `run k/4` line per run, then the case line `FAIL vq/alt: 2/4 runs passed (pass rate 0.50, stddev 0.58)` naming each failed run's deciding fact, exit 1; each run's artifacts in `<case>/run-<k>/`; the case's `result.json` holds `runs`, `runs_passed`, `pass_rate` and `stddev`.
- `every-run` `octo-feather-qa --runs 2` on a case whose stub role passes every run: `PASS vq/steady: 2/2 runs passed (pass rate 1.00, stddev 0.00)`, exit 0.
- `bad-runs` `octo-feather-qa --runs 0`: exit 64 before any run, naming the option.

## How to get to it (user POV)

- A maintainer runs `just qa --runs N` (or `octo-feather-qa --runs N`, beside the other selection options). What a run of N does, its verdict rule, artifacts and fields: `octo-feather-qa --help`, `--runs`.

## Driving it with verify-octo-feather

Preconditions:

- `verify-octo-feather launch` printed `ready`; `verify-octo-feather doctor` exits 0.
- Unprivileged nested user namespaces (`unshare -rm`): the qa sandbox needs them.

Run all cases: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive qa-runs`. Evidence: `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/qa-runs/`.

The drive writes a scratch eval suite `vq` under `$VERIFY_OCTO_FEATHER_RUN_DIR/scratch/qa-runs/evals` (role `implementer`, a one-file fixture, cases `alt` and `steady`, each graded `skill_read tdd`) and passes it with `--evals`. The role's model is a stub `pi` the drive writes (`QA_STUB_PI` in the helper), first on PATH and on the qa sandbox's PATH (`OCTO_FEATHER_QC_PATH`): it reads the role's tdd SKILL.md on every run, or, for `alt`, on odd runs only (run k from its scratch copy's name, `octo-feather-qa --help`). No real model is called: each run's transcript starts with the stub's `stub_argv` record, which the checks require. Artifacts go to `OCTO_FEATHER_QA_DIR` and box state to `XDG_STATE_HOME`, both under the drive's scratch.

- **Some runs pass** (`alternating`). Observe exit 1; lines `run 1/4: PASS`, `run 2/4: FAIL`, `run 3/4: PASS`, `run 4/4: FAIL`, then `FAIL vq/alt: 2/4 runs passed (pass rate 0.50, stddev 0.58); run 2: skill_read tdd: no load ...; run 4: ...`; `run-1` to `run-4` each with its transcript; `result.json` `pass_rate` 0.5, `stddev` 0.5774.
- **Every run passes** (`every-run`). Observe exit 0 and `PASS vq/steady: 2/2 runs passed (pass rate 1.00, stddev 0.00)`.
- **Bad value** (`bad-runs`). Observe exit 64 and `--runs needs a positive integer`.
- **Side effects.** Every cwd stays empty and the kit's `git status` unchanged; no live lane state, no model spend.

## Gotchas

- The stub proves the counting and the verdict rule, not a role's real variance: a real pass rate comes from `just qa --runs N` against the real model, never from this drive.
- What the spread is: `octo-feather-qa --help` (result.json fields).
