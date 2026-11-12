# #754 train-only execution recovery

No role edit. Frozen six semantic cases unchanged. Prior incomplete run
20261111T153633Z-23e3c3 and all its artifacts retained.

Kept transcripts establish actual stop, not assumed cap: baseline24 starts
and24 ends; current25 starts and25 ends; both qa_watch stop=max_tool_calls,
exit143. Both have a failed guessed source-path read (items.toml versus
test_scripts.py) and its enclosing codemode error; no model API failure was
reported. Those recoverable tool errors consumed budget, but the watcher
actually terminated both at its bound before final output. No claim more
budget necessarily fixes model behavior.

Delegated execution-budget authority used only on suite execution fields:
max_tool_calls24 ->128; timeout_s420 ->600. Reason: allow complete source
inspection and concrete offline handoff, with a finite bound. No semantic
task/question/fact/fixture change; no held-out run or tuning. Selected only
training supervisor-nov9-ready-work, same baseline644fad7 and unchanged current,
same explicit modelopenai/gpt-6.1-sol, runs1. No full proof or three-run claim.

Preserved old suite at .qa-data/logs/suite-before-execution-recovery.json,
SHA3664487ffcb9fb79fb9fec7be6b91d78933b40848c870e2c208a7621a5a7b6f7.
New suite SHA33272e1448811d1d0157eb479106db51fc3c093c9427aca2580916c792ccaf13.
cases.json SHA remains067a3941a5741e32b56eed295ec79fba88473416623f441bb839c850ac6ad539.
expectations SHA remainsf61c255f1940bfdfb695f32e333322136eb19eb00783f541f2494e6c29d3a0c0.
check-evals exit0,12 suites455 cases. Review remains independent maintainer
judgment, never automatic RED/GREEN from schema, exit status or REVIEW.

Re-admission15:42:43: root2635018240 >=floor2632974336, including1MiB
prospective margin leaves root2633969664 above floor. Both worktrees/localdata
319305579B <603979776, tmpfsfree459300864. RAMavailable4604465152,
swapfree3926425600. Protect2147483648 +whole832000000 counted once
+outside536870912 +jobM939524096 =4455878656, below observed RAM by148586496.
No additional reader. Job swap805306368 within current1024MiB maximum;
M+S1744830464 within1792MiB total envelope. No new quota/mount claimed.
Normal Pi VAS; no UV_LINK_MODE shortcut or foreign venv/cache write.

Background unitgh754-train-recovery-20261111t1543 launched with enrolled
M939524096/S805306368, RuntimeMax1680s, QA timeout1500s/kill-after15s,
KillModecontrol-group/stop20s; same owned cache/temp and RO runtime reuse.
Previous unit terminal and eval run lock free before new launch. Public stored
gh754 grant expiry17:34:49 remains effective. Completion selfcallback configured.
Log .qa-data/logs/train-recovery.log, prefinal metrics captured separately.
Actual terminal output and peak consumption remain pending at this writing.

Evidence: none
Checks: none
Owners: none
Prior art: none
