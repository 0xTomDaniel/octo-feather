# Role transcript cases in `just qa` (#116, lane gh108)

Ticket #116 (parent #108 scope 3): lane #107's role probes and the owed evals a transcript can decide run as `kind: role-transcript` cases, graded on structured facts only. Suite: `evals/role-transcripts` (main's `evals/role-skill-loading`, renamed; its `probe/` removed, the qa runner replaces it). Kit at aed92e0 for every run below.

## What the harness grades

- Skill read: a Pi `read` tool call whose path resolves to the kit's `.agents/skills/<skill>/SKILL.md`. A bash `cat`, `ls` or `grep` of it never counts (#107's grade.py counted a bash command naming the path).
- Before-targets from the filesystem, never command text: after each `tool_execution_end` the in-sandbox watcher snapshots the case repo (hash of every file git does not ignore, HEAD, origin's refs, the fake gh's log) and prints a `qa_fs` event; test_write, edit, git_commit, git_push and gh_call are the first call after which that changed. final_message: read at all.
- Verdicts as data: `declared_includes` reads the final message's one json block (the reviewer's `blocking` list by pytest id, the qc judge's `criteria` list by id and verdict). The #107 `labelled_judgment` fact is gone; nothing regex-judges prose.
- Repo setup per case: `branch`, `head` (a second fixture committed over main on its branch), `origin` (bare, in the sandbox's /tmp), `fake_gh` (logs argv), `{repo}`/`{head}` in the task.

## Live runs

Smoke (one case, reported to the supervisor first): run `20261023T052108Z-e294c8`
- PASS reviewer-test-quality: tdd read at call 5 of 17, code-review at 1; `declared_includes blocking` holds `tests/test_cli.py::test_shout_json` and `tests/test_cli.py::test_shout_suffix_is_bang`. 66 s.

Full suite, once: `scripts/octo-feather-qa --suite role-transcripts`, run `20261023T052226Z-3a0aa0`, 6/7 passed:

| case | result | deciding facts |
|---|---|---|
| implementer-python-ticket | PASS | implement 1, tdd 4, python 5 before first test_write 6 (`cat >> tests/test_cli.py`); principle-prove-it-works 12, blast-radius 13, commit 14 before any git_commit (stopped once decided, 14 calls, 51 s) |
| corrector-repeated-class | FAIL | writing-for-agents read only at call 8; first edit at call 5 (`edit pyproject.toml`). correct 1, principle-encode-lessons-in-structure 2 before the edit; commit 9 before any commit |
| reviewer-test-quality | PASS | tdd 5, code-review 1; blocking holds both tests (13 calls, 54 s) |
| qc-judge-demo-path | PASS | principle-prove-it-works at call 1; criteria holds hello-shout pass (7 calls, 19 s) |
| qc-judge-no-reviewer-skills | PASS | no read of code-review, blast-radius or github in 9 calls; criteria holds hello-plain pass, hello-shout pass, hello-wave fail (32 s) |
| director-file-parent | PASS | github read at call 1, before any gh call (stopped once decided, 7 s) |
| supervisor-publish-lane | PASS | push at call 1, github at 2, before any git push or gh call (stopped once decided, 7 s) |

FAIL findings:
- corrector-repeated-class: the corrector's first fix was a check (a ruff per-file rule in `pyproject.toml` banning `app.core` imports in tests) then wrote a test file proving it, and read `writing-for-agents` only at call 8 (the run stopped once decided, at call 9). agents/corrector.md says "`writing-for-agents` before editing a role, skill or patch", and the case's fact is "before the first edit of any file" (#107's design). This is a finding about the role and case together: either the corrector should load it before any edit, or the case's target should be the first edit of a prose file. Not weakened here; the supervisor decides.

Fails before (kit at main 5f8fca3, `--kit-ref 5f8fca3`): run `20261023T053421Z-ed89b7`
- FAIL reviewer-test-quality: tdd never read in 11 calls; `blocking` holds only `test_shout_suffix_is_bang` (class non-public-surface-test), not `test_shout_json`. Matches #107's labelled baseline, now from the reviewer's own data.

New trigger cases (main added code-reviewer `tdd`; skill-triggers coverage): run `20261023T053255Z-d583d8`, 4/4 passed, train 2/2, held-out 2/2
- PASS rev-tdd-shout-tests (tdd at 6 of 6), PASS rev-tdd-would-catch (tdd at 5 of 5), PASS rev-tdd-near-count-tests (no read in 1 call), PASS rev-tdd-near-run-suite (no read in 5 calls).

Not shown live: a git_commit, git_push or gh_call mark deciding a fact (every role read its skill before reaching the target, so the run stopped once decided). tests/qa.sh proves each target from real commands in the sandbox with the stub pi.

## Owed evals converted

Removed from docs/owed-evals (cases now): #107 role skills at their step and reviewer test-quality blocks (role-transcripts), supervisor implement-spec and implementer typescript/nodejs/pnpm (skill-triggers); #67 qc judge loads no reviewer skill (qc-judge-no-reviewer-skills), implementer sees blast-radius (skill-triggers impl-blast-*, implementer-python-ticket), corrector writes for agents (skill-triggers cor-writing-*, corrector-repeated-class). Every remaining entry now says why it is not yet a case (Herdr or a multi-agent chain, a judgment of prose, or a fixture not built).
