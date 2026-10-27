# Corrector and qc judge read the declared verify skill (#184)

Smoke: agents/corrector.md (pending: `just qa` case evals/role-transcripts corrector-drives-app, isolated headless run, not run yet)
Smoke: agents/qc-judge.md (pending: `just qa` case evals/role-transcripts qc-judge-drives-app, isolated headless run, not run yet)
Smoke: .agents/skills/eval-cases/ (pending: references/schema.md now lets a skill fact name a skill only the case fixture holds; its run record is the same two `just qa` runs above, the first cases authored under the new text, which grade verify-app from the fixture; not run yet)
Removed: nothing. Incident: skills spec #acceptance-repo-skill-roles; only agents/implementer.md loaded `Repo skills:` by name, so a corrector or qc judge driving the app never read the target's verify skill (issue #184).

## Status: runs pending, no results claimed

Change: agents/corrector.md and agents/qc-judge.md gain the load-by-name rule agents/implementer.md already has for `Repo skills:` (spec `#loading-listed`), naming the verify skill before the first drive of the app, in addition to the role's listed skills. scripts/pi-role and the qc brief in scripts/octo-feather-qc are unchanged.

Fixture: evals/fixtures/python-app-verify, a copy of templates/python (declares `Repo skills: python, verify-app`, holds `.agents/skills/verify-app/`).

Cases (each task drives the app and names no skill; graded on the verify skill's SKILL.md read and the role's listed skills):

- corrector-drives-app: facts skill_read verify-app, correct, principle-encode-lessons-in-structure.
- qc-judge-drives-app: facts skill_read verify-app, skill_read_before principle-prove-it-works final_message, declared_includes criteria hello-json pass, hello-blank pass.

Both grade `skill_read` of a repo skill: a skill fact resolves to the kit's `.agents/skills/<name>/SKILL.md`, else the case fixture's (schema: .agents/skills/eval-cases/references/schema.md, Facts and Skill load; scripts/check-evals and scripts/octo-feather-qa, tested by stub runs in tests/qa.sh: rt/repoload PASS on a cat of a fixture-only skill, rt/reponone FAIL on an ls and on a cat after the agent rewrote it).

Commands the supervisor runs (never the implementer's session):

```
just qa --suite role-transcripts --case corrector-drives-app --kit-ref 8451938   # expect FAIL
just qa --suite role-transcripts --case corrector-drives-app                     # at head, expect PASS
just qa --suite role-transcripts --case qc-judge-drives-app --kit-ref 8451938    # expect FAIL
just qa --suite role-transcripts --case qc-judge-drives-app                      # at head, expect PASS
```

Results and run ids: recorded here in a later commit.
