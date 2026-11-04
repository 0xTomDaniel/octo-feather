# gh479 (#542): eval-cases teaches the measuring method

Smoke: .agents/skills/eval-cases/ (case role-transcripts implementer-wording-proof; stub run below; real runs R3 pending, run by the supervisor)
Removed: eval-cases section 4's two single runs (`--kit-ref BASE` FAIL, then head PASS) as the proof; it now asks for repeated runs beside the baseline kit in one evaluation and the analysis.

## Change

- `.agents/skills/eval-cases/SKILL.md`: the owner split stated (this skill: how a case measures; `writing-for-agents`: how the instruction under test is worded); the harness's owners named (`octo-feather-qa --help`: runs, baseline, analysis, review); section 2 gains review questions and history replays (pointers to schema.md, Case); section 3 grades outcomes, never proxies (`ran` real runs, a dependency by what the branch uses, a free-form class tag a proxy: docs/owed-evals/541.md); section 4 rewritten: `--runs N --baseline BASE`, read pass rates side by side and the analysis.

## Case

evals/role-transcripts implementer-wording-proof: role implementer, fixture python-app-skill-evals (python-app-skill plus `evals/changelog`, a skill-trigger suite of the repo's changelog skill, and a `just qa` recipe), branch implementer-t6, the ticket: reword the changelog skill's description. Graded `ran octo-feather-qa ["--runs", "3", "--baseline"]` (schema.md, Run record): the proof run of section 4, 3 runs per kit beside the baseline; the smoke (`--runs 1`) does not pass it. `fake_qa: true` (schema.md, Case): the role's own octo-feather-qa call is recorded by the ran shim and answered by a fake that runs no case, sandbox or model, so the nested run never reaches a model (harness commit 28d3018; tests/qa-ran.sh proves a poison octo-feather-qa further down PATH never runs).

Expected: at the kit before this change (6f261fd) section 4 asks for `--kit-ref BASE` then a plain run: FAIL; at the change: PASS once the role runs the proof.

## Stub run (no model)

A stub pi in the case repo ran `git branch --show-current; ls evals evals/changelog` and `octo-feather-qa --case changelog-new-flag --runs 2 --baseline main`, run 20261104T202805Z-fd2b3e (on the first fact form; tests/qa-ran.sh now proves the current one: `--runs 1 --baseline main` FAIL, `--runs 3 --baseline main` PASS):
`PASS role-transcripts/implementer-wording-proof: ran octo-feather-qa --baseline: recorded run octo-feather-qa --case changelog-new-flag --runs 2 --baseline main (exit 0); ran octo-feather-qa --runs: recorded run ... (exit 0) [stop: decided, 2 tool calls, 7.5 s]`
The tool output was the fake's (`qa (fake, factory eval: no case runs): octo-feather-qa --case changelog-new-flag --runs 2 --baseline main`, canned PASS and baseline FAIL lines, `qa: 1/1 passed (fake)`), no `qa: run` header and no `qc sandbox` line: nothing real ran. `just` has no version in the sandbox for this fixture (mise), so the fixture's AGENTS.md also names `octo-feather-qa --case ID` on PATH.

## Real runs (R3)

1. First evaluation, run 20261104T204716Z-86c666 (`--baseline 6f261fd`, one run per kit, by the supervisor), graded on the first fact form (`["--baseline"]`, `["--runs"]` apart):
   - baseline kit 6f261fd: FAIL. Its run record holds only `octo-feather-qa --help`, `--case X` and `--case X --kit-ref main`: it also fails the current fact.
   - current kit: PASS, decided on the role's smoke, `--runs 1 --baseline main`. Finding (director agreed): a flag alone let the smoke pass; section 4 now states the smoke (`--runs 1`) and the proof (`--runs 3`) apart, and the fact grades the proof, `["--runs", "3", "--baseline"]`. This PASS is superseded by the rerun below.
2. Rerun at the current kit: pending, by the supervisor.
