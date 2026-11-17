# gh891: a template-born repo's starter edge; verify-octo-feather drives it (template-edge)

Change: the verify-octo-feather skill gains the `template-edge` feature (ticket #893, lane gh891): features/template-edge.md (Drive criterion `templates#acceptance-edge-rejects`), its features/README.md index line, the SKILL.md Drive list and values line, the drive in scripts/verify-octo-feather, and the kit qc.toml demo running it. templates/python's `app hello --request` validates its JSON request with a strict Pydantic v2 model (commit d146135).

Smoke: .agents/skills/verify-octo-feather/SKILL.md (Drive list, values line; run below)
Smoke: .agents/skills/verify-octo-feather/features/README.md (index line; run below)
Smoke: .agents/skills/verify-octo-feather/features/template-edge.md (the recipe the run follows)
Removed: nothing.

## Recorded live run at head d146135

Clean tree at d146135, run and evidence folders the helper's defaults under /tmp, the drive's record to the kit's real store; no model, no network (the Python template's packages offline from the box's uv cache), no live lane. Command, the qc.toml demo's form without `--unreachable-exit`:

```
.agents/skills/verify-octo-feather/scripts/verify-octo-feather run template-edge
```

Exit 0, `verify-octo-feather: run PASS`; summary (`template-edge @ rev d1461350, 2026-11-13T22:23:07Z`):

```
PASS python-new-repo: ... just --justfile <kit>/justfile new-repo python <run>/scratch/template-edge/python --no-spec-chat
PASS python-unknown-field: ... <run>/scratch/template-edge/python/.venv/bin/app hello --request '{"name": "Ada", "mood": "glad"}' --json
    stdout: {"error":"invalid request","issues":[{"field":"mood","problem":"Extra inputs are not permitted"}]}
    exit: 2
PASS python-valid: ... <run>/scratch/template-edge/python/.venv/bin/app hello --request '{"name": "Ada"}' --json
    stdout: {"name":"Ada","text":"Hello, Ada"}
    exit: 0
PASS template-edge
```

(`...`: the drive's scratch env, the git identity `verify-octo-feather` and `MISE_STATE_DIR` under the run's scratch.)

Evidence record (kit store), read with `octo-feather-evidence read --criterion templates#acceptance-edge-rejects --commit d1461350`:

- 20261113T222308Z-dc742739 templates#acceptance-edge-rejects

Owed eval: docs/owed-evals/891.md.
