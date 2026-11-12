# #754 actual smoke and authority diagnosis

Current resource authority: director.handoffs.jsonl:1916,
resource_epoch754-current-462-576-6, effective15:31:46.111235Z.
Earlier old-floor failures retain their historical contract, not current
breaches. No retrospective admission or acceptance.

## Existing authority versus an unused mechanism

The slot incident is failure to use the existing lever, not evidence a new
scheduler or grant protocol is missing. Public octo-feather-slot already
provides director-only grant and enforces grant presence at QA entry. Verbal
and durable resource authorization did not populate slots/eval.json. This
lane's actual first smoke attempt exited75 before setup/model, naming missing
gh754 eval grant. Later status/store reads still showed grants:[]; no further
model attempt was made during that interval. Director recorded eval/heavy
at15:34:49, both expiry17:34:49. Corrector observed actual stored grants at
15:35:55 and the subsequent QA path acquired the eval lock at15:36:32.

The repeated temporary renewals and routine-decision waits described in
tracker6799375972 and gh653 records1085/1108 implicate the same authority
confusion: execution limits were escalated into owner-like gates. Existing
director.md:47 already delegates every non-owner decision to the director;
supervisor Rules already delegate end-to-end continuation under prior intent.
No new authority boundary is established by this diagnosis. Cross-lane
allocation and real owner gates remain director responsibilities; practical
task decomposition and return consumption remain supervisor work. Existing
pilot, shared-writer, changed-input and actual capacity stops are valid.

For slot admission specifically, tool75 behaved correctly. The corrective
action was to run the existing grant command, not weaken its refusal, bypass
identity, add another framework or ask another owner approval. Existing policy
is sufficient for that incident; the evidence does not justify a new mechanism
or generic autonomy sentence. The inactive candidate prose in the feasibility
report remains only a candidate, not an approved or proven change.

## Real finite pipeline smoke

Run20261111T153633Z-23e3c3, selected supervisor-nov9-ready-work, runs1,
baseline644fad70c88eef2210d135167cc305388731729a plus identical unchanged
current HEAD, explicit model openai/gpt-6.1-sol. Native unit
 gh754-smoke-20261111t1538.service actually started15:36:32 after stored grant.
Systemd enrolled MemoryMax1073741824/MemorySwapMax805306368 before execution,
RuntimeMax1200s; QA timeout1050s and kill-after15s. Native Pi VAS uncapped.
No UV_LINK_MODE override. Normal host fixture uv sync wrote to new lane cache,
environment and temporary directories. Existing node_modules reuse remained
read-only under real sandbox proof. No foreign venv or host uv cache reused.

Public sandbox proof succeeded: namespaces, cap0, no_new_privs, credential and
live-state masking, read-only dependency root, discard overlays, private Pi
copies, mise offline, history none. Actual result model on BOTH sides is
openai/gpt-6.1-sol, not merely the requested model string.

The smoke TERMINATED before15:40:55, client/nativeQA rc1. Unit result exit-code,
ExecMainStatus1, no timeout/OOM reported. Retained unit metrics:
MemoryPeak730816512B, MemorySwapPeak0, final CPUUsageNSec26185676000.
The prefinal metric file separately records CPU26183381000ns, not substituted
for final. One observed in-flight local-data point was352040779B including
both worktrees; NOT a measured filesystem peak. Terminal local-data point
319299881B, tmpfs used372686848/free459313152. Root2635190272 >=current floor.
No quota or root-floor failure observed during this smoke. Actual data peak
not sampled continuously, so no exact filesystem peak claim.

## Outcome is incomplete, not RED or GREEN

Both kept result.json files say REVIEW; both review.json final_message fields
are EMPTY. Baseline stopped max_tool_calls24 after26.5s; identical current
stopped max_tool_calls25 after41.2s (an in-flight nested batch drained). The
transcripts show real skill/spec/source reads and inventory searches, ending
before an offline handoff. No role behavior outcome was produced for independent
maintainer judgment. Empty output is NOT proof of serial scheduling, nor a
baseline authority defect. QA's REVIEW label and rc1 are not behavioral RED.

Artifacts:
.qa-data/results/20261111T153633Z-23e3c3/gh754-practical-parallelism/
supervisor-nov9-ready-work/{baseline,current}/run-1/
Each keeps transcript.jsonl, result.json and review.json. Unit log and metrics
are .qa-data/logs/smoke.log and smoke-prefinal-metrics.txt; client rc retained.
All kept for independent maintainer/owner QA, not self-awarded pass/fail.

This is a real setup/sandbox/model pipeline smoke, but not a completed outcome
smoke. No role edits or larger runs3 launched. All six frozen cases and their
bounds remain unchanged; no held-out tuning, fake RED, autopass or stricter
proxy. Before any behavior delivery, independent maintainer judgment must
establish meaningful baseline failure and corrected output with legitimate
serialization counterexamples. The present result does not justify a prompt
patch. No new authorityboundary owner call made.

Evidence: none
Checks: none
Owners: none
Prior art: none
Commits: none
