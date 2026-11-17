# gh891: the TypeScript template's starter edge; verify-octo-feather drives both templates (template-edge)

Change: templates/typescript's `app hello --request` validates its JSON request with a Zod 4 `z.strictObject` at the CLI edge (ticket #894, lane gh891, commit 4bc5a424). The verify-octo-feather `template-edge` drive gains the TypeScript template: features/template-edge.md (each case per template, the TypeScript app command and pnpm store precondition), the drive in scripts/verify-octo-feather, and the kit qc.toml demo's covers. The template's verify-app feature map gains the `request-json` and `request-unknown` cases (features/hello.md, scripts/verify-app.ts).

Smoke: .agents/skills/verify-octo-feather/features/template-edge.md (the recipe the kit run below follows)
Smoke: templates/typescript/.agents/skills/verify-app/features/hello.md (the verify-app run below)
Removed: nothing.

## Recorded live run at head 4bc5a424

Clean tree at 4bc5a424, run and evidence folders the helper's defaults under /tmp, the drive's record to the kit's real store; no model, no network (each template's packages offline from the box's uv cache and pnpm store), no live lane. Command, the qc.toml demo's form without `--unreachable-exit`:

```
.agents/skills/verify-octo-feather/scripts/verify-octo-feather run template-edge
```

Exit 0, `verify-octo-feather: run PASS`:

```
PASS python-new-repo: ... just --justfile <kit>/justfile new-repo python <run>/scratch/template-edge/python --no-spec-chat
PASS python-unknown-field: ... <run>/scratch/template-edge/python/.venv/bin/app hello --request '{"name": "Ada", "mood": "glad"}' --json
    stdout: {"error":"invalid request","issues":[{"field":"mood","problem":"Extra inputs are not permitted"}]}
    exit: 2
PASS python-valid: ... <run>/scratch/template-edge/python/.venv/bin/app hello --request '{"name": "Ada"}' --json
    stdout: {"name":"Ada","text":"Hello, Ada"}
    exit: 0
PASS typescript-new-repo: ... just --justfile <kit>/justfile new-repo typescript <run>/scratch/template-edge/typescript --no-spec-chat
PASS typescript-unknown-field: ... node <run>/scratch/template-edge/typescript/src/cli.ts hello --request '{"name": "Ada", "mood": "glad"}' --json
    stdout: {"error":"invalid request","issues":[{"field":"mood","problem":"Unrecognized key: \"mood\""}]}
    exit: 2
PASS typescript-valid: ... node <run>/scratch/template-edge/typescript/src/cli.ts hello --request '{"name": "Ada"}' --json
    stdout: {"name":"Ada","text":"Hello, Ada"}
    exit: 0
```

(`...`: the drive's scratch env, the git identity `verify-octo-feather` and `MISE_STATE_DIR` under the run's scratch.)

Evidence record (kit store), read with `octo-feather-evidence read --criterion templates#acceptance-edge-rejects --commit 4bc5a424`:

- 20261113T225049Z-c9f4963d templates#acceptance-edge-rejects

## verify-app in a repo from the template

`just new-repo typescript /tmp/gh894-ts --no-spec-chat`, `pnpm install --offline --frozen-lockfile`, then `.agents/skills/verify-app/scripts/verify-app run` (scratch run, evidence and state dirs): exit 0, `verify-app: run PASS`, every hello case PASS, among them:

```
PASS request-json: app hello --request '{"name":"Ada"}' --json
    stdout: {"name":"Ada","text":"Hello, Ada"}
PASS request-unknown: app hello --request '{"name":"Ada","mood":"glad"}' --json
    stdout: {"error":"invalid request","issues":[{"field":"mood","problem":"Unrecognized key: \"mood\""}]}
```

The same repo's `just check`: 11 passed (tsc, eslint, dependency-cruiser, knip, Vitest integration and e2e).

Owed eval: docs/owed-evals/891.md.
