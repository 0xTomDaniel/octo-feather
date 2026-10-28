# Corrector and qc judge read the declared verify skill (#184)

Smoke: agents/corrector.md (run: `just qa` case evals/role-transcripts corrector-drives-app, before 20261027T143153Z-62a559 PASS, head 20261027T143226Z-ece3ae PASS; the case does not discriminate, result pending a case change, see below)
Smoke: agents/qc-judge.md (run: `just qa` case evals/role-transcripts qc-judge-drives-app, before 20261027T143236Z-c01868 FAIL, head 20261027T143329Z-c59f76 PASS)
Smoke: .agents/skills/eval-cases/ (covered by these runs: references/schema.md lets a skill fact name a skill only the case fixture holds; all four runs above graded verify-app from the fixture python-app-verify, loads found at the calls below, a missing load reported "no load")
Removed: nothing. Incident: skills spec #acceptance-repo-skill-roles; only agents/implementer.md loaded `Repo skills:` by name, so a corrector or qc judge driving the app never read the target's verify skill (issue #184).

## Status

- qc-judge-drives-app: fails before, passes after. Done.
- corrector-drives-app: pending. Both runs PASS; no fact in the closed list separates them (below). Not weakened, not tightened; case change proposed to the supervisor.

Change: agents/corrector.md and agents/qc-judge.md gain the load-by-name rule agents/implementer.md already has for `Repo skills:` (spec `#loading-listed`), naming the verify skill before the first drive of the app, in addition to the role's listed skills. scripts/pi-role and the qc brief in scripts/octo-feather-qc are unchanged.

Fixture: evals/fixtures/python-app-verify, a copy of templates/python (declares `Repo skills: python, verify-app`, holds `.agents/skills/verify-app/`).

Cases (each task drives the app and names no skill):

- corrector-drives-app: facts skill_read verify-app, correct, principle-encode-lessons-in-structure.
- qc-judge-drives-app: facts skill_read verify-app, skill_read_before principle-prove-it-works final_message, declared_includes criteria hello-json pass, hello-blank pass.

Both grade `skill_read` of a repo skill: a skill fact resolves to the kit's `.agents/skills/<name>/SKILL.md`, else the case fixture's (schema: .agents/skills/eval-cases/references/schema.md, Facts and Skill load; scripts/check-evals and scripts/octo-feather-qa, tested by stub runs in tests/qa.sh).

## Runs (supervisor, qc sandbox, one at a time, case at 0b92019)

1. corrector-drives-app --kit-ref 8451938, run 20261027T143153Z-62a559:
   `PASS role-transcripts/corrector-drives-app: skill_read verify-app: loaded at tool call 8 of 8 (bash cd .../repo/.agents/skills/verify-app && cat SKILL.md features/hello.md; ...); skill_read correct: loaded at tool call 1 of 8; skill_read principle-encode-lessons-in-structure: loaded at tool call 2 of 8 [stop: decided, 8 tool calls, 32.1 s] [kit 8451938]`
   The old corrector read correct (1) and principle-encode-lessons-in-structure (2), drove the app at call 4 (`uv run app hello '  '`, `--json`) and call 5 (`.venv/bin/app hello '  '`), read the kit's ADRs 0020 and 0008 (6, 7), then cat'ed verify-app/SKILL.md at call 8 while browsing `.agents`. No file changed (branch paths none). Stopped "decided" once every fact was seen. Expected FAIL: it drove before loading the skill, which the case does not grade.
2. corrector-drives-app at head, run 20261027T143226Z-ece3ae:
   `PASS role-transcripts/corrector-drives-app: skill_read verify-app: loaded at tool call 9 of 9 (bash find .agents src tests .github .githooks -type f | xargs ... cat {}; cat pyproject.toml); skill_read correct: loaded at tool call 1 of 9 (codemode); skill_read principle-encode-lessons-in-structure: loaded at tool call 1 of 9 (codemode) [stop: decided, 9 tool calls]`
   Read correct, principle-encode-lessons-in-structure, writing-for-agents, commit, code-review in one codemode call, listed the repo, then a find|cat of every file under `.agents src tests ...` loaded verify-app at call 9. It had not driven the app yet. No file changed.
3. qc-judge-drives-app --kit-ref 8451938, run 20261027T143236Z-c01868:
   `FAIL role-transcripts/qc-judge-drives-app: skill_read verify-app: no load of verify-app/SKILL.md (its full content in a tool result) in 10 tool calls; skill_read_before principle-prove-it-works final_message: loaded at tool call 1 of 10, before the final message; declared_includes criteria: holds hello-json pass, hello-blank pass`
   Read principle-prove-it-works, AGENTS.md, ADR 0022, ran `.venv/bin/app --help` (8) and drove both criteria through a python subprocess (9, 10), never opening `.agents/skills/verify-app/`.
4. qc-judge-drives-app at head, run 20261027T143329Z-c59f76:
   `PASS role-transcripts/qc-judge-drives-app: skill_read verify-app: loaded at tool call 4 of 16 (read .agents/skills/verify-app/SKILL.md); skill_read_before principle-prove-it-works final_message: loaded at tool call 1 of 16, before the final message; declared_includes criteria: holds hello-json pass, hello-blank pass`
   Read principle-prove-it-works (1), then AGENTS.md, verify-app/SKILL.md (4) and the python skill in one codemode call, the helper script and feature map (11, 12, 15), and drove both criteria the helper's way, cwd an empty scratch dir, with its run and evidence dirs set (16).

## Why the corrector case does not discriminate, and the case change proposed

The owned rule (agents/corrector.md): load the verify skill "before you first drive the app". The case grades `skill_read verify-app`, a load anywhere, which the old corrector also makes by browsing `.agents` (run 1, call 8).

Tightening to `skill_read_before verify-app T` needs a target the drive reaches. Before targets are decided from snapshots of files git does not ignore, HEAD, origin and the fake gh (schema: Before targets), and a drive changes none of them: run 1 drove at calls 4 and 5 and its branch paths stayed empty (`uv run` touches only `.venv`, ignored). The fix targets do not separate either: in run 1 the load (call 8) came before any `edit`, `test_write` or `git_commit`, so `skill_read_before verify-app edit` (or test_write, git_commit) grades run 1 PASS whatever it did after. No exact fact in the closed list separates the runs.

Rejected: a fixture app that writes a file on each run, so the drive reaches `edit`. The fixture's verify skill states the CLI writes no files (its drive records `.files` and expects it empty), and its AGENTS.md forbids test detail in product code; the sensor would make the head run's own verify drive report a failure.

Proposed (outside this ticket's scope: schema, scripts/check-evals, scripts/octo-feather-qa, tests/qa.sh): a before target `app_run`, the case repo's declared console script (`[project.scripts]` in the fixture's `pyproject.toml`) started as a process, recorded setup-side like the attempt record (for example a `.pth` hook the qa setup puts in the case venv, writing to the sandbox record the judge cannot rewrite), never from command text. Then corrector-drives-app grades `skill_read_before verify-app app_run`: run 1 reaches it at call 4 with no load, FAIL; run 2 loads at call 9 before any drive. The same target would let qc-judge-drives-app grade the load before the drive rather than before the final message.

Commands for the corrector case (run by the supervisor once the case changes):

```
just qa --suite role-transcripts --case corrector-drives-app --kit-ref 8451938   # expect FAIL
just qa --suite role-transcripts --case corrector-drives-app                     # at head, expect PASS
```
