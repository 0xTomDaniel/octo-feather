# gh503: a template-born repo's gate tiers; verify-octo-feather drives them (template-tiers)

Change: the verify-octo-feather skill gains the `template-tiers` feature (ticket #535, lane gh503): features/template-tiers.md (Drive criterion lines `templates#acceptance-fresh-fast`, `templates#acceptance-test-kinds`, `templates#acceptance-shared-fixture`, `templates#acceptance-same-gate`), its features/README.md index line, the SKILL.md description, Drive list and values line naming it, the drive in scripts/verify-octo-feather, and the four kit qc.toml demos running it (commit 536b8b7).

Smoke: .agents/skills/verify-octo-feather/SKILL.md (description, Drive list and values line name template-tiers; run below)
Smoke: .agents/skills/verify-octo-feather/features/README.md (index line for template-tiers; run below)
Smoke: .agents/skills/verify-octo-feather/features/template-tiers.md (the recipe the run below follows)
Removed: nothing.

## Recorded live run at head 536b8b7

Clean tree at 536b8b7 (gh503-t3 on gh503 f106536), run and evidence folders under /tmp/gh503-t3s/vo, drive records to the kit's real store; no model, no network (packages from the uv cache and pnpm store), no live lane. Command, the qc.toml demos' form:

```
.agents/skills/verify-octo-feather/scripts/verify-octo-feather run --unreachable-exit 77 template-tiers
```

Exit 0 in 244 s (box load ~20 on 4 vCPU), `verify-octo-feather: run PASS`. summary.txt verdicts: PASS for python- and typescript- `new-repo`, `check`, `fast-one-file`, `hook-core`, `fast-residual`; `PASS template-tiers`. Evidence records: 20261104T195023Z-d1b130e2 (fresh-fast), 20261104T195023Z-4730f27a (test-kinds), 20261104T195023Z-2e4e03aa (shared-fixture), 20261104T195024Z-c8883c1f (same-gate).

Excerpts (python): `just check` names `tests/integration/...` and `tests/e2e/test_cli_e2e.py::test_installed_command_end_to_end`, `shared fixture greetings.json: prepared once for this run by gw1` once; `just fast` after `src/app/other.py` changed: six `PASSED tests/test_gate.py::test_recipe[...]`, then `fast: the integration tests pytest-testmon picks from its recorded coverage`, `PASSED tests/integration/test_other.py::test_double`, `1 passed`; after a justfile change: `fast: every integration test: justfile changed since main, on shared-machinery.txt`, four integration tests, no e2e. (typescript): `just check` lists `|integration|` and `|e2e|` tests and the fixture line once; `just fast` after `src/other.ts`: `Affected 1 of 2 test files`, `✓ |integration| tests/other.test.ts > doubles`. The hook commit ran `just fast` (the core's three tests, no e2e); CI's workflow step `- run: just check`.
