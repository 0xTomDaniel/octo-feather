# gh730: invocation-owned sandbox cleanup

Smoke: .agents/skills/verify-octo-feather/features/qc-sandbox.md followed for the real public drive at fec279f8232e7056ef0439bd696e244dbfec3db1, recorded below.
Removed: host-wide process enumeration in launcher survivor inspection and host `pgrep -f` in the verify drive.

Issue #730, implementation child #738. This records actual completed runs, not acceptance of a later documentation or color-control commit. No model ran.

## Instrumented sensitivity baseline

At test-only commit `1a9394225211703b7364bb340e4cb0781d1f33b9`, the launcher blob was unchanged from `95ba85642587801f855582a20eccb563fa78ce99`.

Command with `CI=true FORCE_COLOR=1 GATE_WORKERS=0`:

```
just check-tests tests/gate/kit/test_qc_sandbox.py::test_live_survivor -x
```

Actual test exit 1: live owned child 1875290, launcher 1875233, product launcher exit 0 despite its survivor diagnostic. The regression expected 66. Fixture cleanup separately recorded SIGKILL through its retained pidfd, launcher wait 0, child 1875290 reaped with status 9, then ECHILD. This is a genuine product RED with successful fixture cleanup, not a product pass.

Source artifacts: worker git directory `gh738/instrumented-red.start` and `gh738/instrumented-red.log`.

The earlier uninstrumented RED has structural cleanup evidence only. It is not an independent historical gone/ECHILD certificate or a complete CPU measurement.

## Final behavior head

Commit `fec279f8232e7056ef0439bd696e244dbfec3db1`, clean `gh730-worker`, actual START 2026-11-09T00:35:41Z:

```
CI=true FORCE_COLOR=1 GATE_WORKERS=0 just check-tests tests/gate/kit/test_qc_sandbox.py::test_live_survivor tests/gate/kit/test_qc_sandbox.py::test_reaped tests/gate/kit/test_qc_sandbox.py::test_by_hand -x -rP
```

Actual exit 0, three passed. Live owned child 1880680 was observed through its retained pidfd before launcher 1880623 exited. Product exit 66 and `orphans_left` identified that exact survivor. Fixture cleanup recorded pidfd already exited, launcher wait 66, final ECHILD with no adopted child. Normal cleanup and by-hand isolation also passed. No host process scan was used to establish cleanup.

Source artifacts: worker git directory `gh738/fec279f/final-smoke.start`, `.end`, `.log`.

## Real verify feature drive

Same clean commit, actual START 2026-11-09T00:36:00Z:

```
CI=true FORCE_COLOR=1 QC_PI=none VERIFY_OCTO_FEATHER_RUN_DIR=/tmp/gh738-fec279f-run VERIFY_OCTO_FEATHER_EVIDENCE_DIR=/tmp/gh738-fec279f-evidence .agents/skills/verify-octo-feather/scripts/verify-octo-feather run qc-sandbox
```

Actual exit 0. Child-origin output was `owned-child-start 70 71711881080`. The same invocation's private PID namespace cleanup record contained `70 sleep 71711881080`, with `left_after_kill` zero. The real capture pipe reached EOF. All other existing escape assertions passed. The helper removed run state and retained evidence.

Evidence record: `20261109T003602Z-4fa5c16a`, criterion `quality#acceptance-qc-sandbox-maintained`, commit `fec279f8232e7056ef0439bd696e244dbfec3db1`.

Source artifacts: worker git directory `gh738/fec279f/final-verify.start`, `.end`, `.log`; kept feature outputs `/tmp/gh738-fec279f-evidence/qc-sandbox/` and the kit evidence store. EXIT callbacks recorded actual exit 0 and transport exit 0 for both final commands. Earlier evidence at `5f1b486` was not relabelled.

## Limitations and downstream gate

The observation-error branch is source-audited but not publicly induced. No observation-error runtime proof, CPU savings, complete CPU measurement, model evaluation, or product acceptance is claimed here. Owed evaluation: `docs/owed-evals/730.md`.

The supervisor's full integration candidate `3f60bf242d491dca061439273938690189f37477` failed: 16 failed, 212 passed, actual integrate exit 2. The lane rolled back to `95ba85642587801f855582a20eccb563fa78ce99`; the worker remained at `fec279f`. One failure was this missing smoke/owed record, fifteen were color-sensitive machine-path or nested summary consumers. Native tool-query probing subsequently confirmed colored `uv python dir` and `uv cache dir` under `CI=true FORCE_COLOR=1`, and plain paths with supported `uv --color never`. The worker's `uv python find --system` probe was plain in both modes, so the install-check failures' relative contributions remain unresolved: a colored exported install root and a raw executable query were both machine-path consumers. Query probing is not a gate rerun or a baseline test.
