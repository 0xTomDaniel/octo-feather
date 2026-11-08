# #675 qc-creds tracer fact map

Old: `tests/qc-creds.sh` at `398f936e07ebdc2ce0be6b3d49e093b903bd5f1f`.
New: `tests/gate/kit/test_qc_creds.py`, scenarios in `qc_creds.py`.
Public surfaces: real `octo-feather-qc` (the command `just qc` invokes),
`octo-feather-evidence read`, spec-status initialization and Git in a scratch target.
External seams: shared `testkit/herdr.py`, `testkit/credential_pi.py` and existing
`tests/fixtures/classify-stub` Pi classifier harness. No owned QC or sandbox substitution.

| Old case / assertion | New item / assertion |
| --- | --- |
| Fake Pi is first on the real recipe PATH before QC | Every item's `world`: real `just --evaluate PATH`; both Pi and Herdr resolve to the scratch links, their resolved shared stand-ins mode 0755 |
| OAuth auth.json mode 0600 and provider models.json; both unchanged after every run | Every item snapshots exact file bytes and modes before QC and asserts both unchanged afterward; source models.json explicitly 0644 |
| Demo alone, exit 0, PASS acceptance-a, complete/demo checks/record ID | `test_qc_creds_demo_only`: exact output block, report decision/head/verdict/evidence, RID syntax and report-to-store ID equality |
| Demo output exactly `neither readable\n`, exit `0\n`, both cat errors name absent files | Demo-only and mixed: actual stored demo.exit/stdout/stderr read and checked, both absent-file messages |
| No SECRET-pi anywhere in the demo record or demo proof | Demo-only and mixed: every stored file read as bytes; capture proof checked independently for no credential values |
| Demo sandbox proof says no Pi credentials and both files absent | All three items assert the original exact proof prefix from the real sandbox |
| Demo-only advisory shows answer shows, confidence .910, kit judgment model | Demo-only: default external fake Pi requires both credential copies before exec of existing classifier harness; exact advice output plus report answer/confidence/model |
| Demo-only one OAuth warning | Demo-only: exact warning line count 1 |
| Mixed demo + fallback + advice, exit 0; same demo isolation facts | `test_qc_creds_mixed`: one QC invocation with both criterion IDs; same complete demo output/store/proof assertions |
| Fallback acceptance-b PASS `$ judge b`, complete/agent fallback/record ID | Mixed: exact output block and report fields, record ID present in real evidence store and equal to fallback capture's ID |
| Fallback and advice each require both credential files to reach the model | Shared Pi checks source-marker presence in both files before either response; fallback reply fixed from scenario-known head and legacy response, validates brief head and criterion; classifier delegates unchanged harness |
| Fallback proof says both files are per-run hidden tmpfs copies, never written back | Mixed: exact original credential-copy proof line, real fallback exit 0 |
| Both mixed criteria get expected advisory output; one OAuth warning total | Mixed: both exact output blocks and report answers, exact warning line count 1 |
| No secret printed in mixed stdout/stderr | All three items check returned stdout and stderr |
| Incomplete demo exits 77; QC exit 2; INSUFFICIENT EVIDENCE acceptance-a | `test_qc_creds_incomplete`: QC expected exit 2, result incomplete/insufficient evidence at known head; stored demo exit 77, stdout empty, both absent-file errors |
| Incomplete-only: no advisory stderr, no OAuth warning | Incomplete: no advisory stderr or result field, warning count 0, no fallback capture, target HEAD unchanged |
| Old criterion tags | None: old header contains no `# criterion:` lines; none invented. All items remain integration tests, no e2e exemption added |

Additional report assertions retain exact claimed criterion IDs, per-result source heads,
record IDs joined to actual evidence, and built status for passing criteria. Each of the three
old paths remains its own item with one QC invocation. Target preparation is shared through
existing Scratch.prepare; all preparation CPU remains gross item CPU.

## Transition and deferred proof

The legacy script is intentionally retained. Normal gate discovery temporarily collects both
it and the three new items. This is code preparation, not a full gate handoff; remove legacy
only after authorized parity. Do not treat temporary duplicate gate cost as final calibration.
No user-facing behavior or verify feature drive changed, so no feature-map edit is needed.

`case.toml` pins the old ref above and selects the new test file from the invoking committed
head. Exact new ref is recorded in `/tmp/gh653/report-675-creds.md` after commit, avoiding a
self-referential commit hash in tracked metadata.

Seed definitions, not yet executed:

1. `demo-gets-model-credentials.patch`: pass Pi credentials into declared-demo sandbox.
   Both old and new must reject the demo outcome, unreadable-file evidence or absence proof.
2. `oauth-warning-lost.patch`: suppress the OAuth refresh warning. Both must reject the
   demo-only run's exact warning count.

The lever must later show clean old/new passing and both failing on each seed. No parity,
matched CPU, savings, per-item budget pass or overall gate pass is claimed by this map.
