# gh479 (#542): eval-cases teaches the measuring method

Smoke: .agents/skills/eval-cases/ (case role-transcripts implementer-wording-proof; stub run below; real runs R3 pending, run by the supervisor)
Removed: eval-cases section 4's two single runs (`--kit-ref BASE` FAIL, then head PASS) as the proof; it now asks for repeated runs beside the baseline kit in one evaluation and the analysis.

## Change

- `.agents/skills/eval-cases/SKILL.md`: the owner split stated (this skill: how a case measures; `writing-for-agents`: how the instruction under test is worded); the harness's owners named (`octo-feather-qa --help`: runs, baseline, analysis, review); section 2 gains review questions and history replays (pointers to schema.md, Case); section 3 grades outcomes, never proxies (`ran` real runs, a dependency by what the branch uses, a free-form class tag a proxy: docs/owed-evals/541.md); section 4 rewritten: `--runs N --baseline BASE`, read pass rates side by side and the analysis.

## Case

evals/role-transcripts implementer-wording-proof: role implementer, fixture python-app-skill-evals (python-app-skill plus `evals/changelog`, a skill-trigger suite of the repo's changelog skill, and a `just qa` recipe), branch implementer-t6, the ticket: reword the changelog skill's description. Graded `ran octo-feather-qa ["--baseline"]` and `ran octo-feather-qa ["--runs"]` (schema.md, Run record: a flag alone matches with any value). `fake_qa: true` (schema.md, Case): the role's own octo-feather-qa call is recorded by the ran shim and answered by a fake that runs no case, sandbox or model, so the nested run never reaches a model (harness commit 28d3018; tests/qa-ran.sh proves a poison octo-feather-qa further down PATH never runs).

Expected: at the kit before this change (6f261fd) section 4 asks for `--kit-ref BASE` then a plain run: FAIL (no --runs, no --baseline); at the change: PASS.

## Stub run (no model)

A stub pi in the case repo ran `git branch --show-current; ls evals evals/changelog` and `octo-feather-qa --case changelog-new-flag --runs 2 --baseline main`, run 20261104T202805Z-fd2b3e:
`PASS role-transcripts/implementer-wording-proof: ran octo-feather-qa --baseline: recorded run octo-feather-qa --case changelog-new-flag --runs 2 --baseline main (exit 0); ran octo-feather-qa --runs: recorded run ... (exit 0) [stop: decided, 2 tool calls, 7.5 s]`
The tool output was the fake's (`qa (fake, factory eval: no case runs): octo-feather-qa --case changelog-new-flag --runs 2 --baseline main`, canned PASS and baseline FAIL lines, `qa: 1/1 passed (fake)`), no `qa: run` header and no `qc sandbox` line: nothing real ran. `just` has no version in the sandbox for this fixture (mise), so the fixture's AGENTS.md also names `octo-feather-qa --case ID` on PATH.

## Real runs (R3)

Pending: before `--kit-ref 6f261fd`, then at the change, one run each, by the supervisor.
