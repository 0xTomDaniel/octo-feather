# qa-evidence

Criteria:

- [quality#acceptance-qa-evidence-block](../../../../docs/specs/quality.spec.html#acceptance-qa-evidence-block)

Drive criterion: `quality#acceptance-qa-evidence-block`

## Sub-features

- `block` `octo-feather-qa --analyze <run dir> --evidence` on a scratch stored `--baseline` run of `s1/c1`: exit 0, the markdown block with `- current kit: <sha> (kit ref HEAD)`, `- baseline kit: <sha> (--baseline <sha>)`, the pin `` Pin: `octo-feather-qa --verdict <run>/s1/c1` ``, each run's `ran herdr-say --parent` fact cited `<run>/s1/c1/<kit>/run-1` with its status and the matched recorded argv whole as JSON (newline escaped, its triple backticks inside a four-backtick fence) or `no matching recorded run`, and the `Smoke:` and `Removed:` stubs.
- `again` the same command a second time: exit 0, stdout byte-identical to `block`'s.
- `pin` `octo-feather-qa --verdict <the pin>` in the scratch target: `PASS s1/c1: stored PASS, run <run>, kit <sha>, runs 1/1 passed; fresh at HEAD`; exit 0.

## How to get to it (user POV)

- After an eval proof run (`just qa --runs 3 --baseline <commit>`), the maintainer prints `octo-feather-qa --analyze <run dir> --evidence` and puts it in the change's `evidence/` file, filling its `Smoke:` and `Removed:` stubs (eval-cases skill, step 4). What the block holds: `octo-feather-qa --help`, Evidence.

## Driving it with verify-octo-feather

Preconditions:

- `verify-octo-feather launch` printed `ready`; `verify-octo-feather doctor` exits 0.

Run all cases: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive qa-evidence`. Evidence: `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/qa-evidence/`.

The drive makes a scratch target (a role, its launcher a link to the kit's real `scripts/pi-role` as in [qc-eval-verdict](./qc-eval-verdict.md), suite `s1` with case `c1`, fixture `fx`) under `$VERIFY_OCTO_FEATHER_RUN_DIR/scratch/qa-evidence/repo` and, in `scratch/qa-evidence/qa/`, a stored run of `s1/c1` in `octo-feather-qa`'s layout: baseline (sha `b` x 40) failing, its recorded `herdr-say` run not matching the fact; current (the target's commit) passing, its recorded `herdr-say --parent` message holding a newline and triple backticks. No case, sandbox or model runs.

- **Block** (`block`, `again`). Observe the lines Sub-features names and `again.stdout` equal to `block.stdout` (`again.obs.block`).
- **Pin** (`pin`). Observe exit 0 and the PASS line naming the same run and case.
- **Side effects.** Every cwd stays empty and the kit's `git status` unchanged; the real qa runs dir is never read.

## Gotchas

- The stored run is canned: the drive proves the block is read from what a run stores, not that a real run's facts hold.
