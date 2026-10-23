# Skill-trigger cases for every role skill (#113 of lane #108): live runs, 2026-10-23

`evals/skill-triggers` now holds 108 cases: for each of the 27 role-skill pairs the kit roles list (`skills:` in agents/*.md), a should-trigger case and a near-miss should-not case in split train, and one of each in held-out. Graded only by `skill_read` / `skill_not_read` from the Pi JSON event stream. Fixtures: `py-mini` (existing), `ts-mini` (TypeScript on Node.js with pnpm, `Repo skills: typescript, nodejs, pnpm`), `lane-mini` (py-mini plus an accepted spec, a status file, lane notes and two diffs under review), used by supervisor, director, corrector, code-reviewer and qc-judge cases. `scripts/check-evals` fails naming the role and skill when the suite (`"covers": "role-skills"`) lacks one of the four cases for a pair.

Skipped: the supervisor's `externalSkills` (spec-chat-shape, spec-chat-review). pi-role looks them up in the target repo's `.agents/skills` (the case's fixture copy), where they are not installed, so it skips them with a warning inside the sandbox; they are not kit skills, so no fact can name them (check-evals requires a kit SKILL.md).

Box: exe.dev VM; before each run free -m available 6329 / 6402 MB, swap used 0 MB. Worktree head 3ed17c5 (implementer-gh113). Sequential, one case at a time, each in the qc sandbox (every proof line ok, `qc sandbox: FAIL` count 0 in the full run). Models: the roles' frontmatter models, read back from the transcripts: anthropic/claude-opus-5-5 (implementer, supervisor, director, corrector), openai/gpt-6.1-sol (code-reviewer, qc-judge). One trial per case, no retries.

## Smoke: `scripts/octo-feather-qa --suite skill-triggers --sample 4`, exit 0

Run id `20261023T021047Z-f35fe0` (sandbox proof lines elided):

```
evals: ok (1 suites, 108 cases)
qa: sample 4 of 108 (seed 'octo-feather-qa', stratified by should_trigger and split): skill-triggers/impl-prove-near-read-only (should_trigger false, train), skill-triggers/impl-prove-near-test-command (should_trigger false, held-out), skill-triggers/sup-herdr-tell-worker (should_trigger true, train), skill-triggers/sup-tickets-slice-criteria (should_trigger true, held-out)
qa: run 20261023T021047Z-f35fe0: 4 case(s); artifacts /home/exedev/.local/state/octo-feather/qa/20261023T021047Z-f35fe0
PASS skill-triggers/impl-prove-near-read-only: skill_not_read principle-prove-it-works: no read of principle-prove-it-works/SKILL.md in 1 tool calls [stop: exit, 1 tool calls, 7.7 s]
PASS skill-triggers/impl-prove-near-test-command: skill_not_read principle-prove-it-works: no read of principle-prove-it-works/SKILL.md in 0 tool calls [stop: exit, 0 tool calls, 6.0 s]
PASS skill-triggers/sup-herdr-tell-worker: skill_read herdr-comms: read at tool call 1 of 1 (read /home/exedev/src/octo-feather-gh108-impl113/.agents/skills/herdr-comms/SKILL.md) [stop: decided, 1 tool calls, 7.4 s]
PASS skill-triggers/sup-tickets-slice-criteria: skill_read to-tickets: read at tool call 1 of 1 (read /home/exedev/src/octo-feather-gh108-impl113/.agents/skills/to-tickets/SKILL.md) [stop: decided, 1 tool calls, 8.8 s]
qa: train score 2/2 passed
qa: held-out score 2/2 passed
qa: 4/4 passed (run 20261023T021047Z-f35fe0); artifacts /home/exedev/.local/state/octo-feather/qa/20261023T021047Z-f35fe0
```

## Full suite: `scripts/octo-feather-qa --suite skill-triggers`, exit 1

Run id `20261023T021134Z-a7e060`, 108 cases, 1379.8 s (summary.json). Artifacts `~/.local/state/octo-feather/qa/20261023T021134Z-a7e060/`.

```
qa: train score 49/54 passed
qa: held-out score 46/54 passed
qa: 95/108 passed (run 20261023T021134Z-a7e060)
```

Per role (from summary.json):

| role | train | held-out |
|---|---|---|
| implementer | 20/22 | 18/22 |
| supervisor | 11/12 | 11/12 |
| director | 4/4 | 3/4 |
| corrector | 8/10 | 8/10 |
| code-reviewer | 4/4 | 4/4 |
| qc-judge | 2/2 | 2/2 |

Every failing case (13). Each is a finding about the skill's description or the role, not a case to weaken; no case was tuned or rerun.

| case | role, skill | split | should | what the transcript shows |
|---|---|---|---|---|
| impl-prove-json-claim | implementer, principle-prove-it-works | train | true | verified the claim by running `uv run app hello ...` (3 bash calls) without reading the skill: the behaviour holds, the skill is not loaded |
| impl-prove-empty-name-claim | implementer, principle-prove-it-works | held-out | true | same: ran the app to check the claim, no read in 3 calls |
| impl-github-pr-status | implementer, github | held-out | true | went straight to `gh pr view` (1 call); the description ("in octo-feather workflows") did not pull it in |
| impl-implement-shout-ticket | implementer, implement | train | true | built the ticket (worktree, test, code, commit, herdr-say) in 11 calls reading only python; the role body's "Build the ticket with the implement skill" did not trigger the read. tdd also unread before the first test write |
| impl-implement-two-tickets | implementer, implement | held-out | true | same pattern, stopped at max_tool_calls 12 with no read |
| tdd-tab-in-name | implementer, tdd | held-out | true | a bug fix with a regression test, method words absent from the task: wrote the test (bash `cat >> tests/test_cli.py`) without reading tdd. The explicit train case (tdd-shout-flag) passed |
| sup-commit-pr-body | supervisor, commit | train | true | read implement-spec first, wrote notes/pr-body.md, ended at 4 calls without committing or reading commit |
| sup-commit-call-line | supervisor, commit | held-out | true | ended in 4 calls without a commit skill read |
| dir-github-main-ci | director, github | held-out | true | ran `gh pr view 31 ...` directly (2 calls), no github read |
| cor-commit-remove-scratch | corrector, commit | train | true | `git rm` and `git commit` by hand in 3 calls, no commit read |
| cor-commit-agents-line | corrector, commit | held-out | true | committed without reading commit, 5 calls |
| cor-commit-near-draft-msg | corrector, commit | held-out | false | near miss (draft a commit subject in the reply, run no git): read commit at call 1 |
| cor-github-issue-comments | corrector, github | train | true | `gh issue view 12 --comments` directly, no github read |

Patterns: `commit` and `github` are under-triggered across roles (agents run git and gh by hand; the descriptions read as workflow policy, not "use before any git commit / gh call"), and `commit`'s description over-triggers on drafting a message. The implementer does not load `implement` or `principle-prove-it-works` on its own, despite its body naming them; `tdd` loads only when the task names test-first. Should-not cases otherwise held: 53 of 54 near misses passed.

Not shown: stability across trials (one trial per case), and the supervisor's externalSkills (skipped above).
