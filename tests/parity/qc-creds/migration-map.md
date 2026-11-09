# #675 qc-creds tracer fact map

Old: `tests/qc-creds.sh` at fixed `835f76de2d31f371c3cfb88d523d73b4a4039001`.
Its Git blob `dbc6c85789c95e9660747ca0bd3692994977f95f` is byte-identical to the
historical398 script. This does NOT authorize running the398 product.
New: `tests/gate/kit/test_qc_creds.py`, scenarios in `qc_creds.py`.
Public surfaces: real `octo-feather-qc` (the command `just qc` invokes),
`octo-feather-evidence read`, spec-status initialization and Git in a scratch target.
External seams: shared `testkit/herdr.py`, `testkit/credential_pi.py` and existing
`tests/fixtures/classify-stub` Pi classifier harness. No owned QC or sandbox substitution.

| Old case / assertion | New item / assertion |
| --- | --- |
| Fake Pi is first on the real recipe PATH before QC | Every item's `world`: real `just --evaluate PATH`; both Pi and Herdr resolve to the scratch links, their resolved shared stand-ins mode 0755 |
| OAuth auth.json explicitly mode0600 and provider models.json; qcrun compares both files' bytes with initial copies after every run. cp -p does NOT make cmp a mode assertion | Every item snapshots exact bytes AND modes before QC and asserts both unchanged; explicit models.json0644 and post-run mode checks are modern strengthening, not an old assertion |
| Demo alone, exit 0, PASS acceptance-a, complete/demo checks/record ID | `test_qc_creds_demo_only`: exact output block, report decision/head/verdict/evidence, RID syntax and report-to-store ID equality |
| Demo output exactly `neither readable\n`, exit `0\n`, both cat errors name absent files | Demo-only and mixed: actual stored demo.exit/stdout/stderr read and checked, both absent-file messages |
| No SECRET-pi anywhere in the demo record or demo proof | Demo-only and mixed: every stored file read as bytes; capture proof checked independently for no credential values |
| Demo sandbox proof says no Pi credentials and both files absent | All three items assert the original exact proof prefix from the real sandbox |
| Demo-only advisory shows answer shows, confidence .910, kit judgment model | Demo-only: default external fake Pi requires both credential copies before exec of existing classifier harness; exact advice output plus report answer/confidence/model |
| Demo-only one OAuth warning | Demo-only: exact warning line count 1 |
| Mixed demo + fallback + advice, exit 0; same demo isolation facts | `test_qc_creds_mixed`: one QC invocation with both criterion IDs; same complete demo output/store/proof assertions |
| Fallback acceptance-b PASS `$ judge b`, complete/agent fallback/record ID | Mixed: exact output block and report fields, record ID present in real evidence store and equal to fallback capture's ID |
| Fallback and advice each require both credential files to reach the model | Shared Pi checks source-marker presence in both files before either response; fallback reply fixed from scenario-known head and legacy response, validates brief head and criterion; classifier delegates unchanged harness |
| Fallback proof says both files are per-run hidden tmpfs copies, never written back | Mixed: exact original credential-copy proof line, real fallback exit 0 |
| Both mixed criteria get expected advisory output; one OAuth warning total | Mixed: both exact output blocks and report answers, exact warning line count 1 |
| No secret printed in mixed stdout/stderr | All three items check returned stdout and stderr |
| Incomplete demo exits 77; QC exit 2; INSUFFICIENT EVIDENCE acceptance-a | `test_qc_creds_incomplete`: QC expected exit 2, result incomplete/insufficient evidence at known head; stored demo exit 77, stdout empty, both absent-file errors |
| Incomplete-only: no advisory stderr, no OAuth warning | Incomplete: no advisory stderr or result field, warning count 0, no fallback capture, target HEAD unchanged |
| Old criterion tags | None: old header contains no `# criterion:` lines; none invented. All items remain integration tests, no e2e exemption added |

Additional report assertions retain exact claimed criterion IDs, per-result source heads,
record IDs joined to actual evidence, and built status for passing criteria. Each of the three
old paths remains its own item with one QC invocation. Target preparation is shared through
existing Scratch.prepare; all preparation CPU remains gross item CPU.

## Transition and deferred proof

The legacy script is intentionally retained. Normal gate discovery temporarily collects both
it and the three new items. This is code preparation, not a full gate handoff; remove legacy
only after authorized parity. Do not treat temporary duplicate gate cost as final calibration.
No user-facing behavior or verify feature drive changed, so no feature-map edit is needed.

`case.toml` now pins835 for legacy test/needs restoration and selects the new test file
from the invoking committed head. The earlier `/tmp/gh653/report-675-creds.md` is historical
tracer evidence, not proof of this source-preparation tranche. The exact invoking head must
be recorded by a future authorized run, avoiding a self-referential hash here.

Seed definitions, not yet executed:

1. `demo-gets-model-credentials.patch`: pass Pi credentials into declared-demo sandbox.
   Both old and new must reject the demo outcome, unreadable-file evidence or absence proof.
2. `oauth-warning-lost.patch`: suppress the OAuth refresh warning. Both must reject the
   demo-only run's exact warning count.

The lever must later show clean old/new passing and both failing on each seed. No parity,
matched CPU, savings, per-item budget pass or overall gate pass is claimed by this map.

## Current exact-fact review and source-only changes

Source frame: product835, legacy blob above, modern `qc_creds.py:world/run`, wrapper
`test_qc_creds.py`, `testkit/credential_pi.py`, and shared `testkit/qc.py:qc`.
D = `tests/gate/kit/test_qc_creds.py::test_qc_creds_demo_only`;
M = `tests/gate/kit/test_qc_creds.py::test_qc_creds_mixed`;
I = `tests/gate/kit/test_qc_creds.py::test_qc_creds_incomplete`.
These aliases name the existing three public scenarios, not new cases or exemptions.

| Exact predicate / old source | Modern source and retention | Difference or sensitivity owed |
| --- | --- | --- |
| Recipe PATH resolves scratch Pi before any QC, legacy rp check | world evaluates actual kit just PATH; validates BOTH scratch Pi and Herdr and executable target paths | Additional Herdr/mode guard is modern strengthening; no host Pi fallback |
| Actual timeout180 just --justfile KIT/justfile qc STATUS9 IDS, qcrun | D/M/I now call existing qc helper with recipe=True, same180 cap and literal argv; default helper callers stay direct CLI | Previously835 modern cases only called QC directly. New recipe route is SOURCE ONLY, requires fresh focused proof |
| Supplied OAuth refresh/access/provider markers, legacy credential setup | world writes the same independently known JSON bytes | models0644 explicit and both post-run mode assertions are stronger; legacy models mode followed umask |
| qcrun cmp auth/models bytes against initial copies after EACH of3 runs | Every D/M/I compares both exact byte snapshots after its own run | Never claim legacy cmp verified modes or separate inode copies |
| Demo attempts auth then models cat, returns1 if either readable, otherwise exact neither-readable output | Same literal DEMO command in D/M | Real sandbox/evidence retained, no credential-copy simulator |
| qcrun defaults0; demo-only PASS a from demo checks, complete and RID syntax, demo helper | D block exact command/evidence/decision/RID and report fields | Additional exact IDs/head/report/store joins are modern strengthening |
| Stored demo.exit=0 newline, stdout=neither readable newline, both absent-file stderr strings, demo helper | D/M read actual evidence outputs and compare those literals | No output recomputed from product implementation |
| Every file under actual demo record lacks SECRET-pi bytes, demo helper walk | D/M scan actual stored files bytewise | I also scans its incomplete record, stronger than legacy |
| First demo capture proof has exact no-Pi credential prefix and no secret, demo helper | D/M/I assert same real capture proof prefix and absent secret | I proof/store assertions are stronger; legacy did not invoke demo helper for I |
| Demo-only advisory exact shows/.910/modelM/uncalibrated line | D exact block plus answer/confidence/model report assertions | Model constant from same judgment-model fixture, not QC output |
| Fake Pi refuses unless BOTH credential files contain marker before classification or fallback | Same external credential_pi precondition, classifier delegates original classify-stub | Finite one-request recording is stricter than permissive legacy stub; no new invented provider response |
| Demo-only exact warning line count1 | D exact WARN line count1 | Proves occurrence count, not independent source of which sandbox emitted it |
| Mixed single QC invocation has a and b, qcrun acceptance-a acceptance-b | M one real just qc invocation with both literal IDs | Independent scenario retained, not replaced by two separate commands |
| Mixed a has same complete stored isolation facts | M same demo output/proof/store checks | No retirement merely from overlap with generic sandbox by_hand |
| Mixed b exact PASS / dollar judge b / complete / agent fallback / valid RID | M exact block, b result and fallback capture/store join, exit0 | Store join/exit0 exact field assertions strengthen legacy block check |
| Mixed fallback proof exact COPIES hidden-tmpfs/never-written-back line | M checks that same proof in actual fallback sandbox | A proof string alone is not inode/refresh isolation; separate qc_copies facts are NOT retired |
| Both mixed criteria get exact advisory output byM | M each result block plus report advisory fields | No advisory opt-out, sprint substitution or real model request |
| Mixed warning exact count1 for whole run | M exact count1, despite fallback+advisory sandboxes | per-sandbox warning defect targets this shared exact fact |
| Mixed stdout plus stderr contains no SECRET-pi | M checks both streams; D/I also check, stronger | Does not claim every possible host-side artifact is scanned |
| Incomplete contract substitutes exit77 for echo, qcrun want2; insufficient-a stdout | I same contract substitution/expected QC2/INSUFFICIENT block | I additionally asserts missing evidence, stored77/empty stdout/absent files, no fallback and unchanged head |
| Incomplete stderr has no advisory substring | I exact same substring exclusion plus no result advisory | Result-field assertion is stronger |
| Incomplete stderr has NO occurrence of WARN text, legacy !grep -qF (not anchored) | I now also asserts WARN not in stderr, retaining earlier exact-line count0 | Previous modern exact-line count0 missed prefixed notices. New assertion SOURCE ONLY, no RED/GREEN claim |
| Legacy exit124/137 fails rather than hanging accepted | qc helper keeps timeout -k5/180 and want0/2 via Scratch.run | Outer scenario bound remains; no allowance/fixture CPU subtraction |
| Old fixture uses scratch HOME/state/TMPDIR and fake Herdr/Pi, no live Herdr/model | Modern Scratch plus private mise state, existing tool_homes reuse, same external seams | Do not restore host HOME/credentials/XDG; installed data is not live state |

There is NO whole-item redundancy or retirement proof here. Modern assertions beyond the
old predicates are identified as strengthening, not retroactive legacy coverage. Three
normal cases were proved at historical2a/835-compatible source; changing the route to real
just and the incomplete warning assertion requires a NEW exact-head proof. That historical
GREEN is not relabeled to this commit. No new case, marker or budget exemption is added.

## Genuine defect definitions and named detectors, NOT executed sensitivity

All six patch files are source definitions against the fixed product. No patch was applied
or checked by executing git apply, no source under review imported, no helper/test run.

| Patch | Genuine product defect | Required old/new response and exact fact |
| --- | --- | --- |
| demo-gets-model-credentials.patch | Declared demo sandbox pi=False becomes True | Old first demo helper and D reject readable credential outcome or missing no-Pi proof; inspect actual refusal/evidence, not preflight failure |
| oauth-warning-lost.patch | OAuth helper returns no warning | Old demo-only and D reject count0 instead of1 |
| fallback-without-model-credentials.patch | Actual agent fallback sandbox gets pi=False | Old mixed and M reject missing usable PASS b / fallback capture; both credential files are required at external Pi seam |
| oauth-warning-per-sandbox.patch | Dedup condition removed, warning per Pi sandbox | Old mixed and M reject count2 instead of1; demo-only alone is not this detector |
| no-pi-context-warning.patch | Every no-Pi sandbox wrongly emits contextual OAuth notice, retaining normal Pi warning | Old D/M exact counts still1; legacy I substring exclusion and modern I new assertion reject contextual WARN. Previous modern exact-line count0 alone would not detect it; this is the narrow source-derived preservation gap |
| recipe-drops-status.patch | Actual just qc recipe shifts away first CLI argument | Old qcrun and modern recipe=True D both reject changed status/PR/ID vector before valid QC result |

`ran` now requires both actual QC coverage and actual `just qc` execution for justfile
mutation (`run just qc`, existing strace trace format). These are owed observed facts, not
assertions that source definition proves execution. Missing strace/prepared tools is a
future runtime blocker, never permission to install globally or weaken ran.

## Same-product baseline, launch plan and unresolved prerequisites

The EXISTING lever copies invoking kit files into one scratch Git tree, then restores ONLY
legacy test+needs for old runs. It resets that SAME product before new runs and before each
seed. old_at is NOT a product checkout. Pinning835 here makes legacy/blob provenance
explicit; compare needs (classify-stub and good demo spec) unchanged at398..835 by Git diff.
Do not ever execute398 product or an unsafe old observer to obtain a baseline. Do not merge
A/B/runtime changes into this audit tree: future source delta is reconciled separately.

A future grant must name a clean committed invoking ref whose product/runtime scripts equal
835 (or a separately reviewed later safe source), plus exact test/helper delta. Check full
source safety of selected paths and indirect native observer boundaries first; unresolved
751/review-host/739/694 and UNKNOWNs are NOT cleared by this family source plan. No full/map
or unrelated test selection is implied by any later scoped parity permission.

Future launch proposals, NOT commands executed here:

1. Prepared-only focused smoke: actual just PATH/GATE_RECIPES, CI=true FORCE_COLOR=1,
   GATE_WORKERS=0, private mise state, fresh canonical live HOLD ACK, serial -n0/-x.
   Run D first; report launch/child/hold/callback before any expansion. Then independently
   authorize all3 modern cases and legacy test_script[tests/qc-creds.sh] baseline. NO old
   qc-escapes or directory-wide selection. No model, advisory bypass, install or fake srt.
2. One-seed pipeline smoke using existing `tests/parity/lever.py ABSOLUTE_CASE_DIR`: a
   temporary case containing SAME case.toml and ONLY no-pi-context-warning.patch. Its existing
   public interface supports absolute case dirs. Expect clean old/new both0, seeded old/new
   both nonzero from the named incomplete warning assertions, not setup errors. Report smoke
   before asking for full six-seed run. No new runner/config format or permanent case registry.
3. Separately authorized full `tests/parity/lever.py qc-creds`:2 clean children plus12 seeded
   children, real old coverage/just trace facts, exact paired failures and restored checks.
   Finite Pi/classifier seam and scratch privacy preserved. Keep legacy until full criterion
   evidence, gross waited-descendant CPU and handoff gate are separately established.

Source prerequisites still UNKNOWN/unproved, not a request to silently patch beyond scope:

- Lever.copy copies Git-visible files, not ignored .venv/node_modules. Its just test path uses
  uv --offline --no-sync; copy has no automatic prepared-env/SRT propagation in lever source.
  Establish an existing supported prepared dependency arrangement for that copy before GO,
  or supervisor shapes extension of existing parity lever. Do NOT install/sync to discover it,
  duplicate runner or assume UV_OFFLINE supplies packages. tests/parity/lever.py is outside
  this tranche's write scope and is unchanged.
- Legacy scratch HOME lacks modern world tool_homes reuse. Future caller must preserve only
  approved installed/cache/Python paths (not host HOME/XDG/credentials), with private mise
  state; preflight failure is not a semantic baseline or genuine seed failure.
- Legacy I starts after mixed status commits; modern I uses independent planned target.
  Legacy output predicates are mapped, but fixture-state equivalence/any relevant stale-status
  behavior is NOT proved. No extra speculative scenario or fake product state is introduced.
- Unresolved native marker/ancestor/OS/backend source boundaries remain routed in canonical
  audit. Passing the focused credential smoke alone would not clear them or the whole suite.

