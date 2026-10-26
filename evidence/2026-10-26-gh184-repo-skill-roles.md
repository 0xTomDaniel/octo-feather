# Corrector and qc judge read the declared verify skill (#184)

Smoke: agents/corrector.md (pending: `just qa` case evals/role-transcripts corrector-drives-app, isolated headless run, not run yet)
Smoke: agents/qc-judge.md (pending: `just qa` case evals/role-transcripts qc-judge-drives-app, isolated headless run, not run yet)
Removed: nothing. Incident: skills spec #acceptance-repo-skill-roles; only agents/implementer.md loaded `Repo skills:` by name, so a corrector or qc judge driving the app never read the target's verify skill (issue #184).

## Status: runs pending, no results claimed

Change: agents/corrector.md and agents/qc-judge.md gain the load-by-name rule agents/implementer.md already has for `Repo skills:` (spec `#loading-listed`), naming the verify skill before the first drive of the app, in addition to the role's listed skills. scripts/pi-role and the qc brief in scripts/octo-feather-qc are unchanged.

Fixture: evals/fixtures/python-app-verify, a copy of templates/python (declares `Repo skills: python, verify-app`, holds `.agents/skills/verify-app/`).

Cases (each task drives the app and names no skill; graded on the verify skill's SKILL.md read and the role's listed skills):

- corrector-drives-app: facts skill_read verify-app, correct, principle-encode-lessons-in-structure.
- qc-judge-drives-app: facts skill_read verify-app, skill_read_before principle-prove-it-works final_message, declared_includes criteria hello-json pass, hello-blank pass.

Both need `skill_read` of a repo skill (resolved from the case fixture's `.agents/skills/<name>/SKILL.md` when the kit has no such skill), an extension of scripts/check-evals and scripts/octo-feather-qa sequenced after lane gh167. Until it lands, check-evals refuses them.

Commands the supervisor runs (never the implementer's session):

```
just qa --suite role-transcripts --case corrector-drives-app --kit-ref 8451938   # expect FAIL
just qa --suite role-transcripts --case corrector-drives-app                     # at head, expect PASS
just qa --suite role-transcripts --case qc-judge-drives-app --kit-ref 8451938    # expect FAIL
just qa --suite role-transcripts --case qc-judge-drives-app                      # at head, expect PASS
```

Results and run ids: recorded here in a later commit.
