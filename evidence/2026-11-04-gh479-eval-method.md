# gh479 (#542): eval-cases teaches the measuring method

Smoke: .agents/skills/eval-cases/ (case role-transcripts implementer-wording-proof, `scripts/octo-feather-qa --case implementer-wording-proof --baseline 6f261fd`, run 20261104T212756Z-de8875: baseline 6f261fd FAIL, current 5151022 PASS; R3 final below)
Removed: eval-cases section 4's two single runs (`--kit-ref BASE` FAIL, then head PASS) as the proof; it now asks for repeated runs beside the baseline kit in one evaluation and the analysis.

## Change

- `.agents/skills/eval-cases/SKILL.md`: the owner split stated (this skill: how a case measures; `writing-for-agents`: how the instruction under test is worded); the harness's owners named (`octo-feather-qa --help`: runs, baseline, analysis, review); section 2 gains review questions and history replays (pointers to schema.md, Case); section 3 grades outcomes, never proxies (`ran` real runs, a dependency by what the branch uses, a free-form class tag a proxy: docs/owed-evals/541.md); section 4 rewritten: `--runs N --baseline BASE`, read pass rates side by side and the analysis.

## Case

evals/role-transcripts implementer-wording-proof: role implementer, fixture python-app-skill-evals (python-app-skill plus `evals/changelog`, a skill-trigger suite of the repo's changelog skill, and a `just qa` recipe), branch implementer-t6, the ticket: reword the changelog skill's description. Graded `ran octo-feather-qa ["--runs", "3", "--baseline"]` (schema.md, Run record): the proof run of section 4, 3 runs per kit beside the baseline; the smoke (`--runs 1`) does not pass it. `fake_qa: true` (schema.md, Case): the role's own octo-feather-qa call is recorded by the ran shim and answered by a fake that runs no case, sandbox or model, so the nested run never reaches a model (harness commit 28d3018; tests/qa-ran.sh proves a poison octo-feather-qa further down PATH never runs).

Expected: at the kit before this change (6f261fd) section 4 asks for `--kit-ref BASE` then a plain run: FAIL; at the change: PASS once the role runs the proof.

## Stub run (no model)

A stub pi in the case repo ran `git branch --show-current; ls evals evals/changelog` and `octo-feather-qa --case changelog-new-flag --runs 2 --baseline main`, run 20261104T202805Z-fd2b3e (on the first fact form; tests/qa-ran.sh now proves the current one: `--runs 1 --baseline main` FAIL, `--runs 3 --baseline main` PASS):
`PASS role-transcripts/implementer-wording-proof: ran octo-feather-qa --baseline: recorded run octo-feather-qa --case changelog-new-flag --runs 2 --baseline main (exit 0); ran octo-feather-qa --runs: recorded run ... (exit 0) [stop: decided, 2 tool calls, 7.5 s]`
The tool output was the first fake's (canned lines naming itself, since replaced: Real runs below), no `qc sandbox` line: nothing real ran. `just` has no version in the sandbox for this fixture (mise), so the fixture's AGENTS.md also names `octo-feather-qa --case ID` on PATH.

## Real runs (R3)

1. First evaluation, run 20261104T204716Z-86c666 (`--baseline 6f261fd`, one run per kit, by the supervisor), graded on the first fact form (`["--baseline"]`, `["--runs"]` apart):
   - baseline kit 6f261fd: FAIL. Its run record holds only `octo-feather-qa --help`, `--case X` and `--case X --kit-ref main`: it also fails the current fact.
   - current kit: PASS, decided on the role's smoke, `--runs 1 --baseline main`. Finding (director agreed): a flag alone let the smoke pass; section 4 now states the smoke (`--runs 1`) and the proof (`--runs 3`) apart, and the fact grades the proof, `["--runs", "3", "--baseline"]`. This PASS is superseded by the rerun below.
2. Rerun at the current kit, run 20261104T210630Z-1350a6: FAIL. The implementer read eval-cases, ran `octo-feather-qa --case X` twice and reported that it was talking to a stand-in that proves nothing (the fake then printed `qa (fake, ...)` and `passed (fake)`), and skipped `--runs 3 --baseline`.

Neither evaluation counts: both ran under a fake that announced itself, so the role could tell its proof was not real. The fake now answers in the real tool's output form, copied from real runs, and never names itself (commit 127de22; schema.md Case, fake_qa; tests/qa-ran.sh). The proof is the next evaluation.

3. Final evaluation, run 20261104T212756Z-de8875, `scripts/octo-feather-qa --case implementer-wording-proof --baseline 6f261fd1e4a12a52ca591d5ad8ef4dc000ec1293` (one run per kit, by the supervisor). It separates:

```
  baseline run 1/1: FAIL role-transcripts/implementer-wording-proof: ran octo-feather-qa --runs 3 --baseline: no run of octo-feather-qa with these arguments in the sandbox's record (5 entries; runs of octo-feather-qa: octo-feather-qa --help (exit 0); octo-feather-qa --help (exit 0); octo-feather-qa --evals evals --case changelog-new-flag (exit 1); octo-feather-qa --evals evals --suite changelog --baseline main (exit 1); octo-feather-qa --evals evals --suite changelog --baseline main (exit 120))
  current run 1/1: PASS role-transcripts/implementer-wording-proof: ran octo-feather-qa --runs 3 --baseline: recorded run octo-feather-qa --evals evals --suite changelog --runs 3 --baseline main (exit 1) [stop: decided, 16 tool calls, 63.3 s] [kit 515102201eaeef9d08b61a935426645f94d99a31]
PASS role-transcripts/implementer-wording-proof: 1/1 runs passed (pass rate 1.00, stddev 0.00)
  baseline FAIL role-transcripts/implementer-wording-proof: 0/1 runs passed (pass rate 0.00, stddev 0.00)
  compare role-transcripts/implementer-wording-proof: baseline kit 6f261fd1e4a1 beside current kit 515102201eae
               baseline             current              difference
    pass rate  0.00 +/- 0.00        1.00 +/- 0.00        +1.00
    time s     141.6 +/- 0.0        63.3 +/- 0.0         -78.3
    tokens     497952 +/- 0         285734 +/- 0         -212218
    cost usd   0.5397 +/- 0.0000    0.3540 +/- 0.0000    -0.1857
qa: analysis (deterministic, no model; rules: octo-feather-qa --help, --analyze):
  no flags
```

   - Baseline 6f261fd: $0.540, 31 calls: `--help` twice, `--case changelog-new-flag`, `--suite changelog --baseline main` twice, never `--runs 3`.
   - Current 5151022: $0.354, 16 calls: `--suite changelog --runs 3 --baseline main`.
   - Single samples (one run per kit, the approved R3 budget), no variance claim. The stand-in's exits 1 and 120 above: it wrote its summary.json under the sandbox's read-only state dir (a traceback, exit 1) and a pipe closed early (120); the fact grades the call, never its exit. The stand-in now skips summary.json where it cannot write it (commit after 5151022).
