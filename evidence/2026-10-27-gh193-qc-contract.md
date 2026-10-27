# gh193: create-verification-skill reads the app-driver contract (qc.toml)

Smoke: .agents/skills/create-verification-skill/ .skillfile/patches/skills/create-verification-skill/SKILL.md.patch (run as a role: `just qa` case evals/role-transcripts implementer-verify-create, FAIL at --kit-ref 8451938, PASS at df9a7da; section Smoke below, with its caveat)
Removed: nothing; the patch adds one line (the generated skill's **Contract:** item) after its **Run state:** item.

## Change

- One added patch line: a generated verify skill reads the target's `qc.toml` (quality spec `#qc-contract`), invokes only what it declares, documents it without restating its commands, and names `octo-feather-contract` as its validator.
- Vendored folder rebuilt by hand to equal pin plus patch (`skillfile install` never run); the three later hunk headers moved by one line.
- `python3 scripts/check-vendored`: `vendored: ok (20 skills equal authenticated upstream at pin plus patches; skillfile v1.9.2, offline)`.

## Smoke

Run by the supervisor, one at a time, in the qa sandbox (no live Herdr, no GitHub, no creds). Fixture evals/fixtures/python-app-no-verify.

Before, `just qa --suite role-transcripts --case implementer-verify-create --kit-ref 8451938` (log /tmp/gh136-sup/qa-create-before.log, run 20261027T023456Z-97b471, artifacts ~/.local/state/octo-feather/qa/20261027T023456Z-97b471):

```
FAIL role-transcripts/implementer-verify-create: skill_read_before create-verification-skill edit: first edit at tool call 10 of 30 (write /tmp/qa-97b471-1-uwm1lk7r/repo/tests/test_drive.py), no load of create-verification-skill/SKILL.md (its full content in a tool result) in 30 tool calls; branch_paths: changed tests/test_drive.py (untouched: src/, tests/) [stop: exit, 30 tool calls, 157.8 s] [kit 8451938bc467fb18f012228c938869c3fb5c1ecf]
qa: 0/1 passed (run 20261027T023456Z-97b471)
```

After, `just qa --suite role-transcripts --case implementer-verify-create` (kit df9a7da; log /tmp/gh136-sup/qa-create-after.log, run 20261027T023734Z-4621d2, artifacts ~/.local/state/octo-feather/qa/20261027T023734Z-4621d2): PASS. Skill loaded at tool call 1 of 17, first edit at call 11, `commit` loaded at call 15, first git_commit at call 17; branch changed `.agents/skills/verify-app/` (SKILL.md, features/README.md, features/hello.md, scripts/verify-app), `AGENTS.md`, `qc.toml`; nothing under `src/`, `tests/`.

```
qa: 1/1 passed (run 20261027T023734Z-4621d2)
```

Caveat: in the after run the role did not generate verify-app or `qc.toml` from the skill. At call 11 it copied the kit's own `templates/python/.agents` and `templates/python/qc.toml` from a kit checkout (/home/exedev/src/octo-feather-gh136-w193) that the qa sandbox leaves readable, then edited the `Repo skills:` line. Readable kit source trees in the qa sandbox are a known sandbox gap, escalated, not this ticket's. The graded facts held (skill loaded before the first edit, `commit` before the commit, paths), so the PASS stands on what the case grades; it does not show the skill's text producing a verify skill on its own.
