# gh992: an eval-backed criterion judged from pinned stored eval runs

Change: `octo-feather-qa --verdict RUN_ID/SUITE/CASE...` reads a stored run's grading and judges it fresh or stale against HEAD (rule: `octo-feather-qa --help`, Verdict); a declared demo's qc sandbox sees the qa runs dir read-only (docs/adr/0022, sandbox paragraph). The verify skill gains the qc-eval-verdict feature and its drive.

Smoke: .agents/skills/verify-octo-feather/ (the qc-eval-verdict feature file, its listing in SKILL.md and features/README.md, and the drive they name; no model run)

## The drive

`.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive qc-eval-verdict` at 21d23561 (clean): PASS fresh, second-head, stale; evidence record 20261118T190219Z-33af0302 (criterion quality#acceptance-qc-eval-verdict). The fresh case's demo output, from its qc report, and its sandbox proof line:

```
PASS s1/c1: stored PASS, run 20260101T000000Z-abc123, kit a6c33412119f, runs 2/2 passed; fresh at HEAD bb1a196124ee
qc sandbox: ok   qa runs read-only: <run dir>/scratch/qc-eval-verdict/state/octo-feather/qa at /tmp/.qc-<session>/state/octo-feather/sessions/<session>/qa (1 run dirs; OCTO_FEATHER_QA_DIR names it)
```

## Demo (this kit at 7cda4f20, the real stored run)

```
$ scripts/octo-feather-qa --verdict 20261117T151829Z-60554a/supervisor-general-worker/implementer-result-integrated-not-candidate; echo "exit $?"
INSUFFICIENT supervisor-general-worker/implementer-result-integrated-not-candidate: stored PASS, run 20261117T151829Z-60554a, kit 4c7e24336981, runs 3/3 passed; stale at HEAD 7cda4f20d501: .agents/skills/eval-cases/references/schema.md changed; ... agents/supervisor.md changed; ... evals/supervisor-general-worker/cases.json has no case implementer-result-integrated-not-candidate; evals/supervisor-general-worker/reference/expectations.json has no facts for implementer-result-integrated-not-candidate
exit 77
```
