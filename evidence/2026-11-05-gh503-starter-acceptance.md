# gh503: a template-born repo's starter criterion from its tagged acceptance test; verify-octo-feather drives it (starter-acceptance)

Change: the verify-octo-feather skill gains the `starter-acceptance` feature (ticket #555, lane gh503): features/starter-acceptance.md (Drive criterion `templates#acceptance-starter-acceptance-test`), its features/README.md index line, the SKILL.md Drive list and values line, the drive in scripts/verify-octo-feather, and the kit qc.toml demo running it; both templates' verify-app skills gain an Acceptance section and read qc.toml format 2, as the kit's helper does (commit fb3021c).

Smoke: .agents/skills/verify-octo-feather/SKILL.md (Drive list, values line, format 2, the demo key; runs below)
Smoke: .agents/skills/verify-octo-feather/features/README.md (index line; runs below)
Smoke: .agents/skills/verify-octo-feather/features/starter-acceptance.md (the recipe the first run follows)
Smoke: .agents/skills/verify-octo-feather/features/contract.md (kit contract ok (format 2); the second run)
Smoke: templates/python/.agents/skills/verify-app/SKILL.md (Acceptance: the commands the first run's python cases type)
Smoke: templates/typescript/.agents/skills/verify-app/SKILL.md (Acceptance: the commands the first run's typescript cases type)
Removed: nothing.

## Recorded live runs at head fb3021c

Clean tree at fb3021c, run and evidence folders the helper's defaults under /tmp, drive records to the kit's real store; no model (the kit's stub classifier on the qc sandbox's PATH), no network (MISE_OFFLINE=1, packages from the box's caches), no live lane. Commands, the qc.toml demo's form:

```
.agents/skills/verify-octo-feather/scripts/verify-octo-feather run --unreachable-exit 77 starter-acceptance
.agents/skills/verify-octo-feather/scripts/verify-octo-feather run --unreachable-exit 77 contract
.agents/skills/verify-octo-feather/scripts/verify-octo-feather run --unreachable-exit 77 new-repo
```

Exit 0 in 75 s, 2 s and 4 s, each `verify-octo-feather: run PASS`; starter-acceptance's summary `PASS <lang>-new-repo`, `PASS <lang>-gate`, `PASS <lang>-qc` for python and typescript.

- python `gate`: `OCTO_FEATHER_QC_CLAIMS=app#acceptance-hello-json just check`: exit 0, `qc capture: app#acceptance-hello-json: record 20261105T023238Z-9e6f337f, 1 case(s): tests/e2e/test_cli_e2e.py passed`.
- python `qc`: `just qc docs/specs/app.status.json 7 acceptance-hello-json`: exit 0, `PASS acceptance-hello-json`, `1/1 tagged cases passed in the gate's run at 12986e8784c1, not rerun`, `evidence complete; decision tagged test assertions; record 20261105T023238Z-9e6f337f`, stderr `judged from the gate's record 20261105T023238Z-9e6f337f at 12986e8784c1, not rerun`; still one record, no capture in the report, built with that record, its commit and `tests/e2e/test_cli_e2e.py`.
- typescript `gate`: exit 0, `qc capture: app#acceptance-hello-json: record 20261105T023320Z-b754d14c, 1 case(s): tests/cli.e2e.test.ts passed`.
- typescript `qc`: exit 0, `PASS acceptance-hello-json`, `1/1 tagged cases passed in the gate's run at 89db8860a54b, not rerun`, `decision tagged test assertions; record 20261105T023320Z-b754d14c`; built naming `tests/cli.e2e.test.ts`.

Evidence records (kit store), read with `octo-feather-evidence read --criterion <id> --commit fb3021c`:

- 20261105T023331Z-6f75de70 templates#acceptance-starter-acceptance-test
- 20261105T023334Z-ad335425 quality#acceptance-qc-contract
- 20261105T023345Z-08f51916 templates#acceptance-starter-verify

Owed eval: docs/owed-evals/503.md.
