# gh576 call8 advisory suspension

Scope: explicit invocation configuration of the existing QC advice/report path. Owner: quality#qc-advisory-sprint. No model replacement, canonical model edit, sandbox or accounting change. Existing f1e356e cost/ADR work remains intact. Supervisor seed 8a70fca merged normally as a8e065b.

Smoke: .agents/skills/verify-octo-feather/features/qc-advisory.md `.agents/skills/verify-octo-feather/scripts/verify-octo-feather run qc-advisory` exited 0, default `qc` and authorized `sprint` passed; evidence record 20261108T214516Z-c29610f6. Dirty merge head a8e065b, before this documentation update. Log /tmp/gh576-eval/call8-drive-final.log. Real scratch sandbox demo, evidence append and built status commit in both variants, classifier stand-in only. No live model or real lane QC.

Focused regression: `just test tests/gate/kit/test_qc_advisory.py` exited 0, 12 passed in 7.46s; log /tmp/gh576-eval/call8-focused-final.log. Dirty working tree tests. Covers ordinary answers/unavailability, passing/failing authorized demos, incomplete demo exit 77 staying planned, invalid authority/scope/missing scope and fallback refusal. The initial sprint-only red exited 1, 1 failed in 4.73s against ordinary advice (call8-red.log). An intermediate batch failed because the new test wrote through its scratch pi symlink; restored the worktree fixture and changed the test to unlink its scratch symlink first. Next batch had one fixture-selection failure, corrected to a real criterion without a declared demo. Neither intermediate run is claimed green.

Safety fact: suspension changes only advisory metadata; real CLI regressions prove demo pass/fail and status commits unchanged, incomplete evidence never built, and unsupported fallback rejected before judgment. Default classifier behavior remains separately covered. Proof stops at scratch CLI integration, not final acceptance. No full gate, evaluations, final QC or review run in this batch.

Checks: focused ruff lint/format, repo check-types, diff whitespace, normal commit hooks and committed-head behavior-smoke are reported in the handoff with their actual outcomes. Full integration gate remains supervisor-owned. Only existing sandbox-maintained and sandbox-cost lane claims remain; this patch does not mark another criterion built.

Prior art: none. No infrastructure chosen or added; existing invocation configuration, advice/report path and public regression/verify seams extended. Planned infrastructure investigation remains deferred to #708. #713 job-launch integrity remains file-only, unimplemented here.
