# gh407: qc-fallback and qc-advisory drives read the report path qc prints

Change (d68ce32, scripts/verify-octo-feather only; no role or skill text): `qc_report(f, case)` reads the report at the last `report <path>` the case's `just qc` printed, `{}` when none. The qc-fallback and qc-advisory drives use it in place of a glob of `$XDG_STATE_HOME/octo-feather/qc/<head>-*.json`.

Cause: the lane's final qc at c5da94e failed both demo drives (records quality#acceptance-qc-fallback 20261030T023437Z-d8b8b353, quality#acceptance-qc-advisory 20261030T023423Z-dd9e6c94). Inside the qc sandbox `HERDR_SESSION` names the sandbox session, so octo-feather-state answers `.../octo-feather/sessions/<session>`, the nested qc wrote its report there, and the glob found none. Any named Herdr session does the same outside the sandbox, so the proof below sets `HERDR_SESSION=verify-scratch-s1`.

Other drives checked: lane-archive, director-reflection, correction-lane and factory-report pin `HERDR_SESSION=""` and glob the default state they seed (consistent). The evidence drive's `rglob("record.json")` reads the evidence store, which is not session-scoped (octo-feather-evidence --help). No other drive globs a qc state path.

## Runs

Env for every run: `mise exec -- env HERDR_SESSION=<s> VERIFY_OCTO_FEATHER_RUN_DIR=<tmp>/run VERIFY_OCTO_FEATHER_EVIDENCE_DIR=<tmp>/ev`, then `.agents/skills/verify-octo-feather/scripts/verify-octo-feather run <feature>`. `mise exec` puts mise's tool dirs (node, just) on PATH as `just` does for the gate: run bare from a pane, the sandbox's `node` is mise's shim, the stub classifier fails ("advisory unavailable"), and the advisory drive fails for that unrelated reason. Stubs only (qc judge stub, classify stub): no model ran.

RED at c5da94e's script (swapped in uncommitted, then restored), `HERDR_SESSION=verify-scratch-s1`, scratch `XDG_STATE_HOME` (`MISE_STATE_DIR` pinned to the box's):

```
qc-fallback rc 1: FAIL qc PASS read run FAIL
  nested qc: passed at a078e76f84cd; ... report <run>/scratch/qc-fallback/state/octo-feather/sessions/verify-scratch-s1/qc/a078e76f84cd...-20261030T024215Z-134383.json
  qc.obs.report: {}
qc-advisory rc 1: FAIL qc run FAIL
  nested qc: passed at 44c257717780; ... report <run>/scratch/qc-advisory/state/octo-feather/sessions/verify-scratch-s1/qc/44c257717780...-20261030T024222Z-9013c7.json
  advisory answered: does-not-show, confidence 0.910; qc.obs.results: null
```

GREEN with the fix (uncommitted tree, same env), both sessions:

```
session=verify-scratch-s1 qc-fallback rc 0: PASS qc PASS read run PASS
session=verify-scratch-s1 qc-advisory rc 0: PASS qc run PASS
session=default           qc-fallback rc 0: PASS qc PASS read run PASS
session=default           qc-advisory rc 0: PASS qc run PASS
```

GREEN at committed head d68ce32, `HERDR_SESSION=verify-scratch-s1`, records to the kit's real store:

```
qc-fallback rc 0: PASS qc PASS read run PASS
  verify-octo-feather: evidence record 20261030T024425Z-5ea8c2da (criterion quality#acceptance-qc-fallback; ... --commit d68ce32)
  nested qc report <state>/sessions/verify-scratch-s1/qc/93014fdbf08c...-20261030T024419Z-ec0155.json
qc-advisory rc 0: PASS qc run PASS
  verify-octo-feather: evidence record 20261030T024430Z-02e61d4b (criterion quality#acceptance-qc-advisory; ... --commit d68ce32)
  nested qc report <state>/sessions/verify-scratch-s1/qc/7644fa9c57f0...-20261030T024426Z-45b29b.json
```

Subsets: `just test -k "qc-insufficient or qc-fallback or qc-advisory or check-lint or check-types or check-scripts or check-refs or check-dashes or check-behavior-smoke"`: 13 passed.
