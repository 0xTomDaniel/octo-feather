# template-edge

Criteria:

- [templates#acceptance-edge-rejects](../../../../docs/specs/templates.spec.html#acceptance-edge-rejects)

Drive criterion: `templates#acceptance-edge-rejects`

## Sub-features

Each case runs once per template, `python-<case>` and `typescript-<case>`:

- `new-repo` `just new-repo LANG DEST --no-spec-chat`, then its packages installed offline (observed as `install`).
- `unknown-field` the repo's `app hello --request '{"name": "Ada", "mood": "glad"}' --json`: nonzero exit, stdout one JSON document naming `mood` as one of its string values, no greeting.
- `valid` the same request without `mood`: exit 0, stdout one JSON document `{"name": "Ada", "text": "Hello, Ada"}`.

## How to get to it (user POV)

- In a repo from either template, after `just setup`: `uv run app hello --request '{"name": "Ada"}' --json` (Python), `node src/cli.ts hello --request '{"name": "Ada"}' --json` (TypeScript). The created repo's verify-app feature map (`hello`, `request-json`, `request-unknown`) drives the same cases from inside it.

## Driving it with verify-octo-feather

Preconditions:

- `verify-octo-feather launch` printed `ready`; `verify-octo-feather doctor` exits 0.
- The uv cache holds the Python template's locked packages (`uv sync --locked` in `templates/python`, once with network), and the pnpm store the TypeScript template's (`pnpm fetch` in `templates/typescript`): the drive installs offline.

Run all cases: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive template-edge`. Evidence: `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/template-edge/`.

- **Scratch repos.** One repo per template under `$VERIFY_OCTO_FEATHER_RUN_DIR/scratch/template-edge/<lang>`; its `app` run by path from the repo's own install (Python `.venv/bin/app`; TypeScript `node src/cli.ts`, package.json's bin), no install step in the transcript.
- **Side effects.** `MISE_STATE_DIR` under the scratch. Every cwd stays empty and the kit's `git status` unchanged.

## Gotchas

- The request is one argument: the drive passes it as argv, no shell quoting involved. By hand, quote the JSON.
