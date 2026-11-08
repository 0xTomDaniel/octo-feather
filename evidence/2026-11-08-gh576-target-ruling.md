# gh576 report-only sandbox CPU target

Authority: supervisor spec-call base `1d434ceb9aa6d76dece58f5093ff71c5dbf3c3a5`, quality.calls.jsonl calls 5/6/7, owner-delegated sprint ruling of 2026-11-08. Only the 0.8-second sandbox optimization target becomes report-only on factory and generic CI. Overall budgets and calibration are unchanged.

Actual implementer provenance: session `4524feae-8bd6-4962-8a09-07e845c978d1`, assistant event `4974e26c`, provider `openai`, model `gpt-6.1-sol`. Verified the actual session JSONL before reading the brief; metadata saved at `/tmp/gh576-eval/gpt-target-ruling-model.json`. No other model invoked. This is implementation, not independent review or acceptance.

## Scoped public-surface validation

First direct pytest attempt exited 4 because GATE_RECIPES was unset. Retried through the repository's `just test` entry. Red test: `just test tests/gate/kit/test_qc_sandbox_cost.py -n 0 -q`, 1 failed/1 passed: old drive lacked the required per-run report-only target comparisons. Log `/tmp/gh576-eval/target-red.log`.

Smoke: .agents/skills/verify-octo-feather/features/qc-sandbox-cost.md exercised by the real public `verify-octo-feather run qc-sandbox-cost` through its existing pytest fixture, with real installed Herdr 0.9.5 and cold scratch HOME/cache. Five serial no-op sandbox commands completed. Record `20261108T195753Z-897a9091` names base `1d434ce` with a dirty implementation tree, not a final integrated head. The fixture's scratch evidence store is temporary; the run output is retained in `/tmp/gh576-eval/target-focused.log`.

Command: `just test tests/gate/kit/test_qc_sandbox_cost.py tests/gate/kit/test_qc_sandbox.py::test_blocking_stdio tests/gate/kit/test_qc_sandbox.py::test_reaped -n 0 -q -s`. Exit 0, 4 passed in 12.64 seconds. CPU seconds: 0.722, 0.682, 0.657, 0.675, 0.648; median 0.675. Every measured comparison with `< 0.8` was True. No target miss was induced or fabricated. This proves the reporting path on these real observations, not a measured target-miss execution. Existing real stdio and reaping scenarios passed unchanged. Shared Feature.run waited-child CPU measurement, sandbox launcher, security and reset/reaping machinery remain unchanged; finite nonnegative CPU and command/proof failures remain fatal in the cost drive.

## Historical result and limits

Historical CI run 42510118634 at `363fbf8157dad429618504964bb927d449bba60d` was red: five CPU measurements 1.070, 1.021, 1.002, 1.013, 1.041 exceeded the old hard bound despite command/proof exits 0. The new local observations do not turn that CI green. No new CI, final factory acceptance demo, profiling, full gate or model/eval run was launched here. Final integrated-head demo and fresh independent verdict remain supervisor-owned and need separate authorization. Historical same-family blocking reviews remain blocking, not relabelled.

ADR0013/0022 now point to the owning bounded sprint policy, with separate fresh sessions, actual-model/authority evidence and expiry intact. No launcher/provenance guard repair is claimed (#707 separate). Prior-art criterion remains planned and deferred to standalone #708; existing reviewer rule and its three cases are untouched.

Final focused rerun after preserving full-precision CPU observations: exit 0, 4 passed in 12.79 seconds. CPU 0.673, 0.663, 0.685, 0.643, 0.663; median 0.663; comparisons all True. Evidence record `20261108T200735Z-33689d54` (dirty base head), log `/tmp/gh576-eval/target-focused-final.log`.

`just check-lint check-format check-types check-dashes check-decision-log`: exit 0 after fixing a loop-capture lint and test line length. `git diff --check`: exit 0. `just fast` selected 200/220 items; first attempt timed out at 240 seconds with one failure (lint, fixed). Retry also timed out at 240 seconds, after 193 progress dots without a displayed failure. Neither is a completed green hand-off gate. Logs `/tmp/gh576-eval/target-fast.log` and `target-fast-retry.log`. No surviving pytest/just-fast process observed afterward. Gate completion remains a blocker; no acceptance claim. Normal git commit, without bypass, requested; commit and committed-head smoke check results are in completion output.
