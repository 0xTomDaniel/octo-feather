# qc-browser

Criteria:

- [quality#acceptance-qc-capture-browser](../../../../docs/specs/quality.spec.html#acceptance-qc-capture-browser)

Drive criterion: `quality#acceptance-qc-capture-browser`

## Sub-features

- `qc` `just qc` on a scratch target whose `qc.toml` pins Playwright (`[browser] playwright`) and declares a demo with `browser = true`: the demo screenshots a page in the box's headless Chromium shell inside the qc sandbox, and its new evidence record holds the screenshot.
- `read` that record read back with `octo-feather-evidence read`, `screenshots/page.png` among its outputs.

## How to get to it (user POV)

- A supervisor runs `just qc docs/specs/<slug>.status.json <PR> <id>...` on the lane's integrated head. A claimed criterion whose `[demo."<spec>#<id>"]` has `browser = true` runs as a browser demo. Keys: `schemas/qc.v2.schema.json`; what a browser demo gets and what its record stores: `octo-feather-qc` with no arguments.

## Driving it with verify-octo-feather

Preconditions:

- `verify-octo-feather launch` printed `ready`; `verify-octo-feather doctor` exits 0.
- Unprivileged nested user namespaces (`unshare -rm`): the qc sandbox needs them.
- The box's headless shell at the kit's `qc.toml` `[browser] playwright` pin, where `just install-check` names it (its `browser ok` line). Missing: the `qc` case fails with qc's exit 66 naming the install command.

Run all cases: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive qc-browser`. Evidence: `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/qc-browser/`.

The drive makes a scratch target (the kit's `tests/fixtures/spec-status/good/demo.spec.html`, its status file, a `page.html`, a `qc.toml` with the kit's `[browser]` pin and one browser demo, `values.qc_demo_browser`) and scratch box state (`XDG_STATE_HOME` under `$VERIFY_OCTO_FEATHER_RUN_DIR/scratch/qc-browser/state`); the classifier faked (SKILL.md), so the advisory line says unavailable.

- **Capture** (`qc`). In the scratch target, run `just --justfile <kit>/justfile qc docs/specs/demo.status.json 7 acceptance-a`. Observe exit 0, `PASS acceptance-a` with `evidence complete; decision demo checks; record <id>`, no `qc sandbox: FAIL` line, the proof line `browser: PLAYWRIGHT_BROWSERS_PATH=<folder> read-only, headless shell <dir>`, and the record at the head holding `screenshots/page.png`, a PNG.
- **Read** (`read`). Run `octo-feather-evidence read --repo <scratch> --criterion demo#acceptance-a --commit <head>`. Observe one record listing `screenshots/page.png`.
- **Side effects.** Every cwd stays empty and the kit's `git status` unchanged; the browser folder is never written.

## Gotchas

- The shell must sit where `just install-check` names it (its `browser` line): the qc sandbox masks the cache dir.
- The demo drives the headless shell itself (`--screenshot`); a target's demo may drive it through Playwright from its own dependencies, which finds it by `PLAYWRIGHT_BROWSERS_PATH`.
