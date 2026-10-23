# Role skills load as designed: per-role probes (correction lane #107)

Correction of: owner correction at the #105 merge (test quality rests on skills agents do not read; the reviewer does not review tests) and findings 60, 61, 62 (#107). Owed evals: docs/owed-evals/107.md. Cases for `just qa` (#108): evals/role-skill-loading/.

## Cause

- Finding 60/62 (Pi session logs): skills a role names as an explicit step get read; listed-only skills mostly do not. Implementer 76 sessions: tdd 1, python 0, blast-radius 0, principle-prove-it-works 0. Code reviewer: tdd 0 (not listed). Supervisor commit 0/44, push 4/44. qc-judge principle-prove-it-works 1/6. Director github 0.
- The implementer role said "kit skills you were given (available, not mandatory)": an explicit licence to skip them.
- Finding 61: 8 vendored lines (5 skills) said "Call the Skill tool", a tool Pi lacks, and supervisor.md said "the `implement-spec` Skill call". tdd's description triggered on "the user wants", not on writing a test.
- No reviewer rule named a tautological test; no tautological finding was ever logged.

## Fix (progressive disclosure, no forcing; owner ruled out preload and /skill:name)

- Each role names when each listed skill applies, at its step ("Load each skill when its step comes: ..."), in all six role files.
- Descriptions trigger on the role's real work: tdd, correct, implement, blast-radius, principle-prove-it-works (patches); commit, push, python, typescript (local).
- Dead Skill-tool lines become working references (`read the X skill (../X/SKILL.md)`), and `just check-refs` fails on the literal `Skill tool` / `Skill call` in `.agents/skills` or `agents/`.
- code-reviewer lists `tdd` and blocks a tautological and an implementation-coupled test (instruction with examples).
- AGENTS.md: #105 call 2 (source-read sentence restating tdd) deleted.

Removed: AGENTS.md tests line's "Reading a script's or the justfile's source is the same coupling..." sentence (#105 corrector call 2, denied by the owner).
Removed: agents/implementer.md "(available, not mandatory)" on the kit skills line, and the separate "Build the ticket with the `implement` skill" line (now a step in the skills line).
Removed: agents/supervisor.md "the `implement-spec` Skill call" (Pi has no Skill tool).
Removed: 8 "Call the Skill tool" lines in implement, implement-spec, tdd, improve-codebase-architecture, grill-with-docs.

## Probe setup (isolated)

`evals/role-skill-loading/probe/probe.sh KIT ROLE FIXTURE BRIEF OUT`: `env -i`; PATH = a bin with only `pi` (plus the fake `gh` when given), then `/usr/local/bin:/usr/bin:/bin` (no herdr, herdr-say or kit scripts); `HERDR_SESSION=gh107-probe-sandbox`; temp HOME and `PI_CODING_AGENT_DIR` (copied auth, models, settings, extensions); `--session-dir` under OUT, so no session file lands in `~/.pi/agent/sessions` (checked: no `--tmp-gh107*` dir there). Waits for `free -m` available >= 2500 MB and swap < 500 MB. One probe at a time. Headless `pi-role agents/<role>.md -p <brief>`.

Graders (facts from the session jsonl toolCalls, no model): `grade.py SESSION SKILL TARGET` = the first `read` of `<skill>/SKILL.md` (or a bash naming it) comes before the first TARGET call (`test`: write/edit/bash-write into tests/; `edit`; `cmd:REGEX`). Whether the reviewer blocks each test is a labelled judgment, not a script: I read each final report and quote its blocking line (docs/adr/0008; the prose grader grade-review.py was deleted at review round 1, class regex-judging-meaning). Baselines run the same probe with the role files and skills at main 5f8fca3 (`git archive 5f8fca3`).

Fixtures: evals/fixtures/python-app (templates/python), evals/fixtures/python-app-shout (the same plus a `--shout` change with one tautological test, `test_shout_json`, and one implementation-coupled test, `test_shout_suffix_is_bang`).

## Results (2026-10-23, n=1 each)

| case | role files | result |
|---|---|---|
| implementer-python-ticket | lane | PASS: read implement (0), python (2), tdd (3) before first test write (7); commit (12), blast-radius (13), principle-prove-it-works (14) before `git commit` (15) |
| implementer-python-ticket | main 5f8fca3 | FAIL: tdd never read; python (1), implement (2) read; commit, blast-radius, principle-prove-it-works never read |
| corrector-repeated-class | lane | PASS: correct (0), principle-encode (1), writing-for-agents (4), commit (5) before first edit (6) and commit |
| reviewer-test-quality | lane, first wording | FAIL: tdd read; blocked the coupled test, missed the tautological one (expected built with the code's own `.upper() + "!"` through the CLI). Rule reworded once: "an expected value computed with the code's own operations is tautological, even through a public surface" |
| reviewer-test-quality | lane | PASS: tdd and code-review read; labelled: verdict BLOCKED, `test_shout_json` (tautological-test) and `test_shout_suffix_is_bang` (implementation-coupled-test) both block |
| reviewer-test-quality | main 5f8fca3 | FAIL: tdd never read; labelled: blocks the coupled test ("Block | class: test-internals | `tests/test_cli.py:39-41`"), not the tautological one |
| qc-judge-demo-path | lane | PASS: principle-prove-it-works (0) before the demo run (6); verdict pass with the command and output |
| director-file-parent | lane | PASS: github (0) before first gh call (2); filed the issue on the fake gh |
| supervisor-publish-lane | lane | PASS: push (0) before `git push` (8); github (1) before first gh call (4); draft PR on the fake gh |

Smoke: agents/implementer.md .agents/skills/tdd/ .agents/skills/implement/ .agents/skills/python/ .agents/skills/commit/ .agents/skills/blast-radius/ .agents/skills/principle-prove-it-works/ .skillfile/patches/skills/tdd/ .skillfile/patches/skills/implement/ .skillfile/patches/skills/blast-radius/ .skillfile/patches/skills/principle-prove-it-works/ implementer-python-ticket PASS (each loaded before its step; main: tdd, commit, blast-radius, principle-prove-it-works unread)
Smoke: agents/code-reviewer.md reviewer-test-quality PASS (tdd read; tautological and coupled tests both blocked; main: tdd unread, tautological missed)
Smoke: agents/corrector.md .agents/skills/correct/ .skillfile/patches/skills/correct/ corrector-repeated-class PASS (correct read first, before any edit)
Smoke: agents/qc-judge.md qc-judge-demo-path PASS (principle-prove-it-works read before the demo run)
Smoke: agents/director.md director-file-parent PASS (github read before the first gh call)
Smoke: agents/supervisor.md .agents/skills/push/ supervisor-publish-lane PASS (push before git push, github before gh)
Smoke: .agents/skills/implement-spec/ .agents/skills/improve-codebase-architecture/ .agents/skills/grill-with-docs/ .agents/skills/typescript/ .skillfile/patches/skills/implement-spec/ .skillfile/patches/skills/improve-codebase-architecture/ .skillfile/patches/skills/grill-with-docs/ not run live: the Skill-tool lines are literal reference fixes and typescript a description fix; `just check-refs` on main's tree with this lane's justfile lists all 8 lines and exits 1 (below); live cases owed (docs/owed-evals/107.md)

## Check proof: `Skill tool` on main fails check-refs

`git archive 5f8fca3` into a temp repo, this lane's justfile copied in, `just check-refs`:

```
.agents/skills/grill-with-docs/SKILL.md:6:Call the Skill tool twice, for "grilling" and "domain-modeling".
.agents/skills/implement-spec/SKILL.md:28:   - calls the Skill tool with `tdd` to build the ticket;
.agents/skills/implement/SKILL.md:10:Call the Skill tool with "tdd" where possible, at pre-agreed seams.
.agents/skills/improve-codebase-architecture/SKILL.md:12:- Call the Skill tool with "codebase-design" for the architecture vocabulary ...
.agents/skills/improve-codebase-architecture/SKILL.md:63:Once the user picks a candidate, call the Skill tool with "grilling" ...
.agents/skills/improve-codebase-architecture/SKILL.md:65:Side effects happen inline as decisions crystallize; call the Skill tool with "domain-modeling" ...
.agents/skills/improve-codebase-architecture/SKILL.md:70:- **Want to explore alternative interfaces for the deepened module?** Call the Skill tool with "codebase-design" ...
.agents/skills/tdd/SKILL.md:26:When the shape of that interface is itself in question (...), call the Skill tool with "codebase-design" for the vocabulary. ...
check-refs: Skill tool named above; Pi has none: write 'read the `<name>` skill (`../<name>/SKILL.md`)', vendored skills through .skillfile/patches (#107)
error: Recipe `check-refs` failed with exit code 1
```

(The run predates widening the scan to `agents/`; main's agents/supervisor.md:64 `Skill call` is caught by the same grep.)

## Rates: x3 on committed text (649faad) vs main (5f8fca3)

Runner (lane scratch, /tmp/gh107/rates.sh): `git archive` of each commit as the kit; per run a fresh copy of evals/fixtures/python-app (reviewer: plus python-app-shout committed on branch implementer-t1), `git init`, `uv sync`; `probe.sh` (isolated, free -m gate), one probe Pi at a time, lane and main interleaved. Task text from evals/role-skill-loading/cases.json. Skill reads graded with the committed `grade.py`; reviewer blocks are a labelled judgment (quoted lines below), relabelled at review round 1: main-rev-2 now blocks the coupled test (by line), the counts are unchanged. Positions are tool-call indexes: `skill=load<step@index`, `None` = never read.

grade.py fix in this commit: a bash test write is now a `>`, `>>`, `tee` or `sed -i` whose target is under tests/; the old pattern counted any command naming tests/ with any `>` (`2>&1`), so main runs showed `test@0` on a read-only `find`. No lane result changed.

| case | 649faad | 5f8fca3 |
|---|---|---|
| implementer-python-ticket, full case (tdd, python, implement before first test write; principle-prove-it-works, blast-radius, commit before git commit) | 2/3 | 0/3 |
| implementer: tdd read before first test write | 3/3 | 0/3 |
| reviewer-test-quality, labelled judgment: blocks both tests | 3/3 | 0/3 |
| reviewer, labelled: blocks the coupled test | 3/3 | 3/3 |
| reviewer, labelled: blocks the tautological test | 3/3 | 0/3 |
| reviewer: tdd read | 3/3 | 0/3 |

Smoke: agents/implementer.md lane-impl-1 PASS: implement=0 tdd=2 python=2 < test write @4; principle-prove-it-works=9 blast-radius=9 commit=9 < git commit @10
Smoke: agents/implementer.md lane-impl-2 PASS: implement=0 tdd=2 python=3 < test write @5; principle-prove-it-works=12 blast-radius=13 commit=14 < git commit @15
Smoke: agents/implementer.md lane-impl-3 FAIL: implement=0 tdd=6 python=7 < test write @8; blast-radius=14 commit=15 < git commit @16; principle-prove-it-works never read
Smoke: agents/implementer.md main-impl-1 FAIL (baseline): python=1 < test write @2; tdd, implement never read; run ended on a provider 503 (auth_unavailable) after 7 calls, before any commit, so principle-prove-it-works, blast-radius, commit never read
Smoke: agents/implementer.md main-impl-2 FAIL (baseline): python=1 < test write @2; tdd, implement, principle-prove-it-works, blast-radius, commit never read (git commit @7)
Smoke: agents/implementer.md main-impl-3 FAIL (baseline): python=1 < test write @2; tdd, implement, principle-prove-it-works, blast-radius, commit never read (git commit @7)
Smoke: agents/code-reviewer.md lane-rev-1 PASS: tdd=4; labelled: taut yes ("1. **class: tautological-test** `tests/test_cli.py:35-36`, `test_shout_json`"), coupled yes ("2. **class: implementation-coupled-test** `tests/test_cli.py:39-41`, `test_shout_suffix_is_bang`"), both under "### Blocking findings"
Smoke: agents/code-reviewer.md lane-rev-2 PASS: tdd=2; labelled: taut yes ("2. **class: tautological-test** `tests/test_cli.py:35-36`, `test_shout_json`"), coupled yes ("1. **class: implementation-coupled-test** `tests/test_cli.py:40-42`, `test_shout_suffix_is_bang`"), both under "### Blocking findings"
Smoke: agents/code-reviewer.md lane-rev-3 PASS: tdd=4; labelled: taut yes ("1. **`tests/test_cli.py:35-36`** · `class: tautological-test`"), coupled yes ("2. **`tests/test_cli.py:39-41`** · `class: implementation-coupled-test`"), both under "### Blocking findings"
Smoke: agents/code-reviewer.md main-rev-1 FAIL (baseline): tdd never read; labelled: coupled yes ("**Block | class: `internal-test-coupling`** `tests/test_cli.py:40-42`, `test_shout_suffix_is_bang`"), taut no (test_shout_json not mentioned)
Smoke: agents/code-reviewer.md main-rev-2 FAIL (baseline): tdd never read; labelled: coupled yes ("**Block | class: `non-public-surface-test`** `tests/test_cli.py:39-41` reads `src/app/core.py`"), taut no ("Keep the existing JSON test.")
Smoke: agents/code-reviewer.md main-rev-3 FAIL (baseline): tdd never read; labelled: coupled yes ("### Blocking finding ... **class: test-reaches-internals** `tests/test_cli.py:39-41`: `test_shout_suffix_is_bang`"), taut no (test_shout_json not mentioned)

## Review round 1 (6c3a001): grader deleted, report-step wording anchored to the commit

- Finding class regex-judging-meaning: grade-review.py decided "blocked" from report prose. Deleted (docs/adr/0008 stop rule); reviewer blocks are a labelled judgment above; expectations.json fact `labelled_judgment`.
- Director rerun at 6c3a001: implementer read implement, tdd, python before the first test edit and commit before `git commit`, but not principle-prove-it-works or blast-radius (report-step skills 2 of 4 runs). Cause: the step line said "before reporting" while the implementer commits before it reports. One wording attempt: "once the code works and before the commit, in order: `principle-prove-it-works`, `blast-radius`, then `commit`".

Removed: agents/implementer.md "before reporting, `principle-prove-it-works`, then `blast-radius` for the safety fact; before committing, `commit`".
