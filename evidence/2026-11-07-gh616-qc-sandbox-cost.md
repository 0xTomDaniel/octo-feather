# gh616: the qc sandbox's CPU per run, a checked number

Change: the verify-octo-feather drive `qc-sandbox-cost` runs the qc sandbox around a judge that does nothing (`octo-feather-qc-sandbox -- true`), 5 runs one after another, each run's CPU (getrusage of all its waited-for processes) printed with the median, a run at or over 0.8 s failing (quality spec `#acceptance-qc-sandbox-cost`); `qc.toml` declares it as that criterion's demo.

Smoke: .agents/skills/verify-octo-feather/features/qc-sandbox-cost.md (the recipe the drives below follow)
Smoke: .agents/skills/verify-octo-feather/features/README.md (index line for qc-sandbox-cost; its drives below)

## Commands at head 923ff1b, implementer pane of lane gh576, the heavy slot held, no model run

By hand, `.agents/skills/verify-octo-feather/scripts/verify-octo-feather run qc-sandbox-cost`, exit 0:

```
verify-octo-feather: qc-sandbox-cost: 0.412 0.396 0.313 0.367 0.355 s CPU per run; median 0.367 s, each under 0.8 s: True
verify-octo-feather: drive qc-sandbox-cost PASS
verify-octo-feather: evidence record 20261107T030123Z-2471b405 (criterion quality#acceptance-qc-sandbox-cost)
```

Nested, as `just qc` runs the demo: `scripts/octo-feather-qc-sandbox -- .agents/skills/verify-octo-feather/scripts/verify-octo-feather run --unreachable-exit 77 qc-sandbox-cost`, exit 0:

```
verify-octo-feather: qc-sandbox-cost: 0.407 0.402 0.420 0.404 0.377 s CPU per run; median 0.404 s, each under 0.8 s: True
verify-octo-feather: drive qc-sandbox-cost PASS
verify-octo-feather: evidence record 20261107T030149Z-50798f0c (criterion quality#acceptance-qc-sandbox-cost)
```

`tests/gate/kit/test_qc_sandbox_cost.py::test_cost` (e2e) alone: 1 passed.

Before (the hand-built Bash sandbox, gh576 0ff742f, serial, real herdr): median 2.02 s CPU per run (#576).
