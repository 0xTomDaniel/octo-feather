# gh503: gate-time budget in the factory report and the merge ask; verify-octo-feather drives it (#536)

Change: the verify-octo-feather skill's `factory-report` and `merge-ask-proof` features gain a `gate-budget-over` case each (ticket #536, lane gh503): features/factory-report.md (Drive criterion `comms#acceptance-report-gate-budget`, case, fake gh note), features/merge-ask-proof.md (Drive criterion `issue-lifecycle#acceptance-merge-ask-gate-budget`, case, trend note), their features/README.md index lines, the SKILL.md description and fake gh sentence, the drives in scripts/verify-octo-feather, and the two kit qc.toml demos running them (commits 8944697, 9b511b8).

Smoke: .agents/skills/verify-octo-feather/SKILL.md (description and the fake gh sentence name the gate budget cases; runs below)
Smoke: .agents/skills/verify-octo-feather/features/README.md (index lines for factory-report and merge-ask-proof; runs below)
Smoke: .agents/skills/verify-octo-feather/features/factory-report.md (the recipe the first run below follows)
Smoke: .agents/skills/verify-octo-feather/features/merge-ask-proof.md (the recipe the second run below follows)
Smoke: .agents/skills/verify-octo-feather/scripts/verify-octo-feather (both drives, runs below)
Removed: nothing.

## Recorded live runs at head 9b511b8

Clean tree at 9b511b8, run and evidence folders the helper's defaults under /tmp, drive records to the kit's real store; no model, no network (factory-report: the kit's fake gh over a scratch store; merge-ask-proof: the kit's offline read-only gh), no live lane. Commands, as the feature files give them (the qc.toml demos' form):

```
.agents/skills/verify-octo-feather/scripts/verify-octo-feather run --unreachable-exit 77 factory-report
.agents/skills/verify-octo-feather/scripts/verify-octo-feather run --unreachable-exit 77 merge-ask-proof
```

factory-report: exit 0 in 5 s, `run PASS`: PASS reflection-never, reflection-two-days, gate-budget-over. The gate-budget-over case's report block:

```
gate budget o/r: the latest passed full gate run against gate-budget.toml on o/r's default branch
  full gate: 330s, head 444444444444, started 2026-10-04T10:00:00Z (31d10h42m ago): OVER BUDGET by 30s (budget 300s)
  growth: +57.1% over the trend's median 210s (the 3 passed full runs before it); set share 20%: GROWN
  trend: 200s 111111111111 2026-10-01T10:00:00Z, 220s 222222222222 2026-10-02T10:00:00Z, 210s 333333333333 2026-10-03T10:00:00Z, 330s 444444444444 2026-10-04T10:00:00Z (passed full runs, oldest first)
  slowest: tests/slow.sh 270s, tests/mid.sh 40s, check-lint 2.5s
```

merge-ask-proof: exit 0 in 8 s, `run PASS`: PASS full-proof-no-pass, brownfield-full-1, brownfield-full-2, full-proof-after-integrate, gate-budget-over. The gate-budget-over case's merge ask (exit 0, its output otherwise equal to full-proof-after-integrate's) ends:

```
Gate time (the full gate on the final head against gate-budget.toml at 8b62b62ade06; the code reviewer judges it, no gate reads it: issue-lifecycle #lanes-checkpoints):
  full gate: 75.5s, head 8b62b62ade06, started 2026-10-04T10:00:00Z (31d10h42m ago): OVER BUDGET by 15.5s (budget 60s)
  growth: +79.8% over the trend's median 42s (the 3 passed full runs before it); set share 25%: GROWN
  trend: 40s 04bda2896d05 2026-10-01T10:00:00Z, 44s 04bda2896d05 2026-10-02T10:00:00Z, 42s 04bda2896d05 2026-10-03T10:00:00Z, 75.5s 8b62b62ade06 2026-10-04T10:00:00Z (passed full runs, oldest first)
  slowest: tests/e2e.sh 65.5s, check-lint 4s
```

Evidence records (kit store, one per Drive criterion line), read with `octo-feather-evidence read --criterion <id> --commit 9b511b8`:

- 20261104T204249Z-c4c04fee comms#acceptance-report-reflection
- 20261104T204249Z-f3c5ecf4 comms#acceptance-report-gate-budget
- 20261104T204257Z-2b3a4148 issue-lifecycle#acceptance-merge-ask-full-proof
- 20261104T204258Z-ae0b5577 issue-lifecycle#acceptance-brownfield-full
- 20261104T204258Z-2c324b28 issue-lifecycle#acceptance-merge-ask-gate-budget

Owed eval: docs/owed-evals/503.md.
