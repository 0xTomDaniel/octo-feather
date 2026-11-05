# qa-baseline

Criteria:

- [quality#acceptance-qa-cost](../../../../docs/specs/quality.spec.html#acceptance-qa-cost)
- [quality#acceptance-qa-baseline](../../../../docs/specs/quality.spec.html#acceptance-qa-baseline)

Drive criterion: `quality#acceptance-qa-cost`
Drive criterion: `quality#acceptance-qa-baseline`

## Sub-features

- `cost` `octo-feather-qa --runs 2` on a case: under its case line, `  cost vb/build: time s <mean> +/- <sd>; tokens 115 +/- 7`; result.json `time` and `tokens`, each {mean, stddev}.
- `baseline` `octo-feather-qa --runs 2 --baseline <before>` on the same case: one run id, runs interleaved (`baseline run 1/2: FAIL`, `current run 1/2: PASS`, ...), the current kit's case line, the baseline's indented under it, then the `compare vb/build` table (pass rate, time s, tokens, cost usd: baseline, current, difference); exit 0 by the current kit.
- `bad-baseline` `--baseline no-such-ref`: exit 64 before any run.

## How to get to it (user POV)

- A maintainer runs `just qa --runs N --baseline <commit>` (with `--kit-ref` for a change side other than the head). Option, layout, fields and exit: `octo-feather-qa --help`, `--runs` and `--baseline`.

## Driving it with verify-octo-feather

Preconditions:

- `verify-octo-feather launch` printed `ready`; `verify-octo-feather doctor` exits 0.
- Unprivileged nested user namespaces (`unshare -rm`): the qa sandbox needs them.

Run all cases: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive qa-baseline`. Evidence: `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/qa-baseline/`.

The drive needs two kit commits where one case fails before and passes at the change, and never writes the checkout's repo: it copies this checkout's tracked files (as they are in the working tree) into a scratch kit repo under `$VERIFY_OCTO_FEATHER_RUN_DIR/scratch/qa-baseline/kit`, commits them with `agents/implementer.md` not listing tdd (before), then as they are (change), and runs that scratch kit's `scripts/octo-feather-qa`. The scratch eval suite `vb` holds one case, `build` (role implementer, graded `skill_read tdd`). The role's model is the qa-runs drive's stub `pi` (`QA_STUB_PI` in the helper; first on PATH and on the qa sandbox's PATH through `OCTO_FEATHER_QC_PATH`): it reads tdd when the role lists it and reports usage on each assistant message (run k: 100 input and 10k output tokens, cost 0.001). No real model is called: each run's transcript starts with the stub's `stub_argv` record, which the checks require.

- **Cost** (`cost`). Observe exit 0 and the cost line with tokens `115 +/- 7` (runs 1 and 2: 110 and 120).
- **Side by side** (`baseline`). Observe exit 0, one `qa: run` line naming the baseline kit, the interleaved run lines, `PASS vb/build: 2/2 runs passed`, `  baseline FAIL vb/build: 0/2 runs passed`, and the table rows pass rate `0.00 +/- 0.00`, `1.00 +/- 0.00`, `+1.00`; tokens `115 +/- 7` on both, `+0`; result.json `baseline` and `delta`.
- **Bad ref** (`bad-baseline`). Observe exit 64 and `--baseline no-such-ref: no such commit`.
- **Side effects.** Every cwd stays empty and the kit's `git status` unchanged; no live lane state, no model spend.

## Gotchas

- The stub's usage is canned: the drive proves the measuring and the table, not a real role's cost.
- The scratch kit copies the working tree: a drive on a dirty checkout compares that dirty tree, not a commit.
