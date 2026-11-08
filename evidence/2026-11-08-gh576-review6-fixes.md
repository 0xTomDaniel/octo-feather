# Review 6 correction evidence

Scope: findings 1 and 2 of review6-report.txt, based on 9467c9a, preserving the supervisor seed. No production measurement, reporter, launcher, gate, role, model or budget changes.

Actual writer: openai/gpt-6.1-sol, session 545b3c1e-dd86-4c50-9016-03515cf9d817, assistant event de23bd37. Certificate: /tmp/gh576-eval/review6-fix-model.json, checked before reading the permitted brief.

## Public seam and independent oracle

The existing verify CLI reads entry.command from a scratch qc.toml. An unchanged driver executable is hardlinked into that fixture, never imported or inspected by the test. Its entry spends at least 1.1 seconds of real process CPU before exec of the real sandbox CLI with `-- true`. Python process_time controls actual work, not reported measurements. The same five serial no-ops, real installed Herdr, sandbox proof and cleanup run afterward. The expected per-run reports are the literal five False values and aggregate False. The observed command CPU must include the entry's 1.1 seconds as well. Baseline outcomes have no host-dependent True assertion or mirrored threshold arithmetic.

Each case checks actual exit artifacts, finite nonnegative CPU, srt proof, Herdr session isolation and stopped/deleted session cleanup with left_after_kill zero. No CPU/time/accounting data is synthesized, and no owned measurement is patched.

Smoke: `just test -k installed_herdr` exited 0, 1 passed. Real Herdr 0.9.5 at /home/exedev/.local/bin/herdr. The subsequent baseline-only public selection passed before adding the controlled case.

## Red and green, accurately characterized

An initial fixture smoke failed doctor because the entry resolved scripts outside its fixture. Using the fixture's existing QC_REPO/scripts entry fixed that configuration error.

The deliberate oracle-sensitivity red used the actual controlled workload but temporarily expected five True reports. `just test -k 'test_qc_sandbox_cost and test_over_target'` exited 1. All five sandbox runs themselves exited 0 and the drive printed run PASS, with measured CPU 1.782, 1.773, 1.779, 1.744, 1.806 seconds and five False reports. Only the intentionally wrong assertion failed. This is a test-adequacy correction: no natural failure of the current correct reporter is claimed. An old hard gate would instead fail the public command; an undercount omitting the entry would fail the workload accounting assertion. Neither mutation was made to production.

After installing the correct literal False oracle, `just test -k test_qc_sandbox_cost` exited 0: 3 passed. Final serial dirty-tree capture: `just test -n 0 -rP -k test_qc_sandbox_cost`, exit 0, 3 passed, 224 deselected in 20.67 seconds.

Controlled actual CPUs: 1.748, 1.810, 1.744, 1.780, 1.768 seconds; median 1.768. Five False reports, aggregate False, five exits 0, proof and cleanup printed for every run. Baseline actual CPUs: 0.690, 0.626, 0.640, 0.690, 0.657 seconds; median 0.657. Five observed True reports, aggregate True, five exits 0. These baseline values are observations, not portable expected outcomes.

Evidence: qc-sandbox-cost 20261108T221322Z-8cd1f74d
Evidence: qc-sandbox-cost 20261108T221330Z-66c39510

The first record names the scratch entry fixture revision 86feef2, not a clean product head. The second names base 9467c9a with the correction tree dirty. Test scratch is removed normally; retained public capture includes commands, raw CPU, proof, cleanup, exit and record ids. Clean committed-head behavior smoke follows in the handoff report.

Retained raw logs under /tmp/gh576-eval:

- review6-oracle-red.log SHA256 0ba3aff09ed08773143976814972aa0679c3f8d10f56b74a2cbb574b39b7c5a7
- review6-public-green.log SHA256 c345c65f9174643f897450ca0af45bb56bb18d8d5c56c715b872bccbe155e057
- review6-statics-final.log SHA256 3fffbea29edaead8300d99871ac7e9a00564b4780b73d878d225bd87a61db843

## Ownership and safety

ADR 0013 and ADR 0022 retain their in-place amendments and link the canonical quality-reviewer owner rather than copying scope, expiry, session and historical-verdict policy. The feature map links acceptance-qc-sandbox-cost and documents the executable controlled case instead of copying fatal/non-gating policy. Existing qc-advisory-sprint ownership remains linked. The feature-map edit documents CLI regression coverage, not an agent instruction change; no eval contract changes.

Owner search: review6-owner-full.log searches GPT-only, separate sessions, blocked report, sprint pause, report-only and accounting failures across docs, roles, skills, scripts and tests. Policy statements remain at the canonical spec owners. Nonblocking explanatory reporter comments remain at driver lines 1577 and 1586; reporter output strings and executable assertions are not additional normative owners.

Safety fact: production execution and accounting are unchanged, and the real public baseline plus controlled entry both complete all five sandbox runs with full proof and cleanup. Proven through running commands, not compilation alone. The new controlled case costs about 9.4 CPU seconds and is e2e-marked.

Validation: lint, format, types, dashes, skills, refs and behavior-smoke all passed. Import ordering and formatting findings from preliminary statics were corrected. git diff --check passed. Normal commit hooks are required. No full/near-full gate, QC, model advice, eval, push or CI operation was run. Final integration gates and fresh review remain separately scheduled, not claimed here.

Removed: mirrored expected-value threshold arithmetic and the duplicated policy prose identified by review 6.
