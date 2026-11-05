# gh503: one execution for suite and QC; verify-octo-feather drives it (one-execution, one-execution-incomplete)

Change: the verify-octo-feather skill gains the `one-execution` and `one-execution-incomplete` features (ticket #553, lane gh503): features/one-execution.md (Drive criterion `quality#acceptance-one-execution`), features/one-execution-incomplete.md (Drive criterion `quality#acceptance-one-execution-incomplete`), their features/README.md index lines, the SKILL.md description, Drive list and values line, the drives in scripts/verify-octo-feather, and the two kit qc.toml demos running them (commit c77bf18).

Smoke: .agents/skills/verify-octo-feather/SKILL.md (description, Drive list and values line name the one-execution drives; runs below)
Smoke: .agents/skills/verify-octo-feather/features/README.md (index lines; runs below)
Smoke: .agents/skills/verify-octo-feather/features/one-execution.md (the recipe the first run follows)
Smoke: .agents/skills/verify-octo-feather/features/one-execution-incomplete.md (the recipe the second run follows)
Removed: nothing.

## Recorded live runs at head c77bf18

Clean tree at c77bf18, run and evidence folders the helper's defaults under /tmp, drive records to the kit's real store; no model (the kit's stub classifier on the qc sandbox's PATH), no network, no live lane. Commands, the qc.toml demos' form:

```
.agents/skills/verify-octo-feather/scripts/verify-octo-feather run --unreachable-exit 77 one-execution
.agents/skills/verify-octo-feather/scripts/verify-octo-feather run --unreachable-exit 77 one-execution-incomplete
```

Exit 0 in 21 s and 17 s, each `verify-octo-feather: run PASS`; summary verdicts `PASS gate`, `PASS qc` for each.

- one-execution `gate`: `OCTO_FEATHER_QC_CLAIMS=demo#acceptance-a just check` in the scratch target: exit 0, `qc capture: demo#acceptance-a: record 20261104T203328Z-31d2b5a0, 1 case(s): tests/accept.sh passed`; the record's test.output holds `RAN-accept` once, its case carries the qc sandbox's proof.
- one-execution `qc`: `just qc docs/specs/demo.status.json 7 acceptance-a`: exit 0, `PASS acceptance-a`, `1/1 tagged cases passed in the gate's run at fdd980e7dc24, not rerun`, `evidence complete; decision tagged test assertions; record 20261104T203328Z-31d2b5a0`; still one record, no capture in the report, built with that record and `tests/accept.sh`.
- one-execution-incomplete `gate`: `qc capture: demo#acceptance-b: record 20261104T203350Z-b4178f00, 1 case(s): tests/skip.sh skipped`, exit 0.
- one-execution-incomplete `qc`: exit 2, `INSUFFICIENT EVIDENCE acceptance-b`, `missing: case tests/skip.sh (tests/gate/test_gate.py::test_script[tests/skip.sh]) skipped: skip: needs a GPU, none here`, `evidence incomplete; decision tagged test assertions; record 20261104T203350Z-b4178f00`; no agent fallback, planned.

Evidence records (kit store), read with `octo-feather-evidence read --criterion <id> --commit c77bf18`:

- 20261104T203338Z-34b6c67a quality#acceptance-one-execution
- 20261104T203355Z-4f5dbc60 quality#acceptance-one-execution-incomplete

Owed eval: docs/owed-evals/503.md.
