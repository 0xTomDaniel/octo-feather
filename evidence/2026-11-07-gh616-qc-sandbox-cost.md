# gh616: the qc sandbox's CPU per run, a checked number

Change: the verify-octo-feather drive `qc-sandbox-cost` runs the qc sandbox around a judge that does nothing (`octo-feather-qc-sandbox -- true`), 5 runs one after another, each run's CPU (getrusage of all its waited-for processes) printed with the median, a run at or over 0.8 s failing (quality spec `#acceptance-qc-sandbox-cost`); `qc.toml` declares it as that criterion's demo.

Smoke: .agents/skills/verify-octo-feather/features/qc-sandbox-cost.md (the recipe the drives below follow)
Smoke: .agents/skills/verify-octo-feather/features/README.md (index line for qc-sandbox-cost; its drives below)

## Correction: the first figures were undercounted

The runs at head 923ff1b below (medians 0.367 s and 0.404 s, runs 0.31 to 0.42 s) counted only part of each run: bubblewrap's monitor exits before the sandbox's init is reaped, so that init (the inner, the proof, the per-run Herdr server, the judge) was orphaned to the box's init, and srt's socat bridge, killed in Node's exit handler and never waited for, was too; neither's CPU reached the caller's getrusage. The final review of cb7a415 found the socat branch; the init was found measuring it. Fixed at d70a411 (the launcher a child subreaper reaping every orphan, srt's reset() awaited before exit; tests/gate/kit/test_qc_sandbox.py::test_reaped) and 7b2e0ad (the drive measures the case command alone, not its own kit git status). With every process counted the cost was about 0.85 s per run under load; cut at d70a411 (per-run Herdr server without background update checks, Node's compile cache for srt's library) and 3a41195 (the mise tools proof loads the install helper in-process).

## Final: head 3a41195, quiet box (load 0.88 before, 0.82 after), the heavy slot held, no model run

Every run's CPU counted completely: the caller a child subreaper, every orphan reaped (0 left in every run).

A/B through octo-feather-qc sandboxed() (judge `true`, no Pi, real herdr), interleaved:

```
old 0ff742f (hand-built Bash sandbox): 2.067 2.087 2.524 2.335 2.452  median 2.335 s
new 3a41195 (srt):                     0.777 0.770 0.729 0.720 0.760  median 0.760 s
```

By hand, `.agents/skills/verify-octo-feather/scripts/verify-octo-feather run qc-sandbox-cost`, exit 0:

```
verify-octo-feather: qc-sandbox-cost: 0.729 0.720 0.758 0.697 0.703 s CPU per run; median 0.720 s, each under 0.8 s: True
verify-octo-feather: drive qc-sandbox-cost PASS
verify-octo-feather: evidence record 20261108T161715Z-9c45f371 (criterion quality#acceptance-qc-sandbox-cost)
```

Nested, `scripts/octo-feather-qc-sandbox -- .agents/skills/verify-octo-feather/scripts/verify-octo-feather run --unreachable-exit 77 qc-sandbox-cost`, exit 0:

```
verify-octo-feather: qc-sandbox-cost: 0.666 0.653 0.642 0.701 0.655 s CPU per run; median 0.655 s, each under 0.8 s: True
verify-octo-feather: drive qc-sandbox-cost PASS
verify-octo-feather: evidence record 20261108T161723Z-cba18408 (criterion quality#acceptance-qc-sandbox-cost)
```

Margin is thin on qc's own path (highest run 0.777 s).

## Superseded: commands at head 923ff1b (undercounted, above)

, implementer pane of lane gh576, the heavy slot held, no model run

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

Before (the hand-built Bash sandbox, gh576 0ff742f, serial, real herdr): median 2.02 s CPU per run (#576); re-measured with the same complete accounting above: median 2.335 s, nothing of it orphaned.
