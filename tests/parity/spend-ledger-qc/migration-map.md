# #675 remaining QC ledger facts, source map FIRST

New distinct SOURCE unit06:17:40-06:37:40. Base1bcb2487818d53a8e32354a52ce40b03ac1d51c0,
branch gh653-675-ledger. Ticket675: qc tests rewritten light, part2 (creds, sandbox env,
spend ledger). Legacy scripts retained. No runtime, source-cost estimate, retirement or acceptance.
Canonical criteria quality#acceptance-test-cpu-budget and #acceptance-gate-time-targets:
actual serial matched old/new gross CPU and seeded same-product failures remain owed.

Read COMPLETE tests/spend-ledger-qc.sh, spend-ledger-qc-unwritable.sh and shared
lib/spend-ledger.sh. The qc helper's comment says just qc, but ACTUAL argv calls
scripts/octo-feather-qc directly, not just. Do not claim recipe parity from that comment.
Their headers have no criterion tags. Both skip Darwin with exit0 before setup; the new
scenario command preserves that branch without adding a pytest marker. On Linux they fail rather than skip on missing
or wrong pinned Pi. Setup starts real Pi against existing finite loopback provider, never a
real model. Provider price input1000/output2000 per million yields150in/10out/$0.17.

Named genuine comparator tests/gate/kit/test_spend_ledger.py::test_spend_ledger_agents
runs actual pinned Pi and actual extension with shared provider; asserts tool/model usage,
agent/role/headless attribution and real public ledger totals. Its test_spend_ledger_later
covers unknown-cost and directory-at-ledger non-gating AGENT write failure. Neither drives
QC's sandbox-local spend -> outer public writer relay or QC's verdict under outer write failure.
test_lane_judge.py::test_judge_posts and test_lane_judge.py::test_rerun_in_place cover
classifier public ledger and
non-gating comment behavior, not QC fallback accounting. No whole-item redundancy established.

| Old exact fact | Shared versus unique | Planned new public assertion |
| --- | --- | --- |
| Pinned actual Pi version, real spend-ledger extension, shared fake provider150/10/$0.17 | Real-Pi/extension compatibility shared with spend_ledger_agents; QC relay unique | Reuse existing spend_ledger.world/World, not a new fake; actual public QC fallback against provider, report-to-public-ledger joins |
| Empty HOME/environment, only approved PATH/mise-data plus own Pi/state/cache/tmp, PI_OFFLINE/versioncheck/telemetry flags | Harness isolation, not model credentials from box | Existing World.pienv/go env-i-equivalent whitelist; copy only generated fake agent config to private HOME as legacy; no new host credential fallback |
| lane gh149 supervisor w37:p2; QC invoked with workspacew37 and fake/fake | QC parent space relay unique; role resolution shared | Same actual lane file, workspace and model on public QC command; real report pass at independently known target head |
| Eight prior calls: gh149 implementer6/unknown1/707in/63out/$0.654; two no-lane calls | Public seed setup, not claimed model observations | Feed same literal GH149/NO_LANE fixtures plus free150/10/null through public spend record; no direct ledger writes |
| Separate judge500in/40out/$0.0001 underw37 | Public seed and cross-purpose coexistence | Public spend record with workspacew37, same literal payload before QC |
| QC exit0 and PASS acceptance-a | Unique actual public QC behavior | One QC call per scenario, actual report fallback PASS/record/head; built status optional strengthening |
| Accounting calls10 globally | Unique aggregate includes both no-lane seeds | One public spend read after real QC return counts10; no polling loop; real QC return happens after sandbox spend collection and synchronous outer writer |
| lane+purpose gh149 qc-judge $0.170000 calls1 unknown0 in150 out10 | QC relay/attribution unique | Existing tests/spend-out public row tool checks same exact tuple |
| lane+purpose gh149 implementer $0.654000 calls6 unknown1 in707 out63 | Preservation alongside QC | Same exact tuple from SAME final spend read |
| lane+purpose gh149 judge $0.000100 calls1 unknown0 in500 out40 | Cross-purpose classifier record preservation | Same exact tuple from SAME final spend read |
| lane gh149 $0.824100 calls8 unknown1 in1357 out113 | Exact accounting sum, not whole-ledger count | Same exact tuple from SAME final spend read |
| Ledger pathname is a DIRECTORY, not chmod or synthetic error | Native supported IsADirectoryError, unique QC outer write failure | mkdir actual own ledger path before QC; never replace writer or inject a fake outcome |
| Unwritable still exit0/PASS acceptance-a | QC non-gating failure unique | Separate scenario one actual QC call; same actual fallback report/pass checked |
| stderr exact substring spend unrecorded (1 call(s), $0.170000): cannot write | Same error class as later but unique QC relay context | Literal prefix from real public writer stderr; no fabricated failure JSON |
| Default advisory behavior | Legacy has no opt-out; unavailable kit classifier has no provider credential | No advisory bypass or new model/provider config; same existing provider catalog. Any additional calls must be diagnosed, not silently subtracted |
| Cleanup provider after case; scratch discarded | Existing provider/World fixture mechanism | Existing ExitStack/provider context and scenario main cleanup; no new server/controller |

Seams: public QC/evidence/status/Git and lane spend record/read; real extension plus existing
provider at external model boundary only. Existing fake Pi judge/credential fixtures DO NOT
execute spend-ledger.ts, so having them write sandbox spend.jsonl or reproducing extension
recording would fabricate owned outcomes. No such fake is introduced. Existing real-Pi
provider mechanism is the available honest seam; it is not a proven CPU reduction. If the
scope requires removing that runtime while retaining extension facts, supervisor must shape
another existing supported external seam; no helper/role/extension changes authorized here.

Source-only parity plan: existing lever, same invoking fixed product for old/new, old_at835
restores only exact old script+its shared lib/provider/spec/nested fixture needs. Separate
accounting and unwritable case directories select their exact new pytest node. Never restore
unsafe historical product. One general defect per old script: drop real QC sandbox spend
relay; propagate native spend writer failure into QC result. Seeds are definitions only, not
applied/executed. Current source graphs/native/error/backend UNKNOWNs remain runtime blockers,
owned by B/A where assigned. No duplicated B/A work. Prepared copy dependencies/strace remain
unproved; no install. Actual complete parity and gross matched CPU needed before retirement.
