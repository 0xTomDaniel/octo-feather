# QA18 source preparation, partial and unvalidated

Baseline: `0048f0558f87cdc0864f675061d7ea17e8b6b6fd`.
Branch: `gh653-qa18`, private worktree `/home/exedev/src/octo-feather-gh653-qa18`.
Parent: `w62:p2`; worker `w62:p6`; session `3b044a3d-c904-454a-bf92-725b02001a9e`.
Scope: existing #677/#678, quality `#test-kinds` and `#acceptance-test-cpu-budget`.

**This is not an acceptance, green gate, parity receipt or retirement decision.**
There are 15 authored pytest IDs, not 15 converted legacy IDs. All 18 legacy
scripts and their pytest representations remain. Only validation/usage and the
stored-review input contract are authored here. Most actual eval execution
oracles remain unconverted. No runtime, test collection, typecheck, formatter,
model, Pi, network, install, just recipe, gate or parity lever was run.

## Agreed public seams

- `scripts/check-evals EVALS_DIR`: real suite/input validation and diagnostics;
  does not demonstrate a role's behavior, sandbox, grader or classifier accuracy.
- `scripts/octo-feather-qa` usage/selection/reference refusals: real exits and
  no-run output; does not demonstrate passing evals or their artifacts.
- `scripts/octo-feather-qa --review RUN_DIR SUITE/CASE ...`: real reading and
  appending of reviews on explicit stored-document input fixtures. Those
  fixtures are not claimed outputs of an eval. Generating them from a real run
  and showing old verdicts on a subsequent run remain owed.

Each wrapper uses the existing `case` fixture and `testkit.main` command path.
Fixture writers write JSON/fixture input data only. No owned command/function
is stubbed, imported or monkeypatched. No Pi event stream or provider response
is fabricated. No new runner, copier, registry, replay format or shared helper
is added. Fixture-tree copies use `shutil.copytree` on the existing eval inputs;
no template install or runner setup is requested by these shape checks.

## Exact old-ID mapping

Every old ID below has the prefix
`tests/gate/test_gate.py::test_script[tests/` and suffix `]`. This is the frozen
18-ID scope, not a new inventory. The original files at the baseline, including
all embedded Python/JQ/grep assertions, are the exact retained oracle source.
New IDs below are complete literal pytest IDs. An absent replacement is stated
as absent rather than credited to an unrelated modern test.

### 1. `qa-baseline.sh`

New partial: `tests/gate/kit/test_qa_selection.py::test_selection_refusals`.
Maps unknown baseline `no-such-ref` to exit 64, named missing commit and no
`qa: run`; missing `--baseline` to 64.

UNCONVERTED: reads runs 1/2 usage totals `[220,240]`, tokens mean 230/stddev
14.1421, cost mean .002/stddev 0, time mean/stddev, compact facts and summary
mean; one header with both full kit SHAs and short baseline ref; exact
baseline FAIL/current PASS interleaving 1 then 2; case-line SHAs and 2/2 versus
0/2; comparison table pass rate `+1.00`, tokens `+0`, cost `+0.0000`, time row;
per-side run/config/sha and paths; delta and summary passed/total; reverse
comparison exits 1 by current kit only. Requires c1/c2 role-loading response
recordings, not a stored summary manufactured to pass these assertions. The
legacy node_modules link remains untouched.

### 2. `qa-before-tool.sh`

New partial: `tests/gate/kit/test_qa_shape.py::test_before_shape`.
All four shape oracles: empty/absolute edit_under, extra target key, absent tools,
exit 1 and the original `searched fact #1` diagnostics.

UNCONVERTED: searched PASS with search call 2 preceding first lib/x/ edit call 3;
late FAIL with write call 3 before any search; never FAIL target not reached
(including lib/xy not matching lib/x/); readfirst PASS read call 2/3. Requires
actual tool-turn responses for the four scripted briefs and real filesystem
snapshots; a prerecorded result.json would bypass the behavior.

### 3. `qa-bench.sh`

New replacement: **none**. All assertions remain legacy-only.
UNCONVERTED exact groups: 15 cases, 12 train/3 held-out; 12 available classifiers;
3 moving aliases and listed ynr never called; cheap-total unclassified but
benched; unlisted yesno unavailable with complete choice-question provider
error, not inferred/skipped; exact train and held-out tables for token,
cheap-total, cheap-train, first, p/q-1.2, p/q-latest; full broken 400-character
error; kit first versus best token table, threshold `{accuracy_min:.254,
brier_max:1.591}`, held-out accuracy .333/Brier1.333/ECE.667, advisory threshold
and no chosen field; DONE and sandbox isolation proof; all 8 bench artifacts,
no SECRET-REASON leak, 120 model-judgment answers; per-model .042 and total
.126 cost; exact skipped/benched/unclassified/ruling records and yesno first
error; no agent/session/tools/MCP/chat model launch flags, extension prompt;
ledger 120 calls/30 unknown/90 input/90 output with exact model/lane/day rows;
unwritable ledger preserves report and names unrecorded spend; explicit
classifier selection, skipped aliases not called or called unavailable, pinned
-latest accepted, best tie-break uses train cost; kit broken/yesno unscored
FAIL; first partly answering 11/12 scored with named error; dead bench command
exit3/no result fails. Requires recorded classifier catalogue plus each real
choice request/response, usage, refusals, partial refusal and process failure.
The old token-selecting registry stub is not a recording.

### 4. `qa-cap-batch.sh`

New replacement: **none**. Both exact old assertions remain unconverted:
inbatch PASS read at call5/5 after crossing bound3, stop decided; afterbatch
FAIL no read in4 calls, stop max_tool_calls. Requires recorded model/tool-turn
batch responses with real in-flight nested-call lifecycle. No sleep-based
surrogate or replayed grader output is authored.

### 5. `qa-declared.sh`

New replacement: **none**. All six old assertions remain unconverted:
ok PASS rung check and read does not stop before final declaration; out FAIL
vibes outside list; none FAIL zero fenced JSON blocks; two FAIL two blocks;
early FAIL timeout before final; earlyrb FAIL final_message target never
reached, read call2/2 recorded. Requires final-message responses plus real stop
lifecycle. In particular the original timeout oracle is not replaced by a
faster timeout or a synthetic timeout field.

### 6. `qa-field-lines.sh`

New replacement: **none** for transcript grading. Do not credit
`test_field_shape`: that maps qa-shape's input-validation assertions instead.
All old oracles remain unconverted: fnone PASS none/every/Blocked and committed
plus uncommitted src paths; bullet/fenced Check FAIL; fexact valid Check does
not fail while scripts/check-exec path fails untouched; proxy class FAIL;
fowner all three restated paths; fonone empty Blocked fails but Owners:none
does not; fweb skips error and accepts named tool text at call3 with two-word
Prior art; fwebnone error and invalid doubled-space field fail; fwebempty
empty text fails; fwebno unlisted tool fails. Requires recorded responses for
all 11 cases and actual branch/tool outcomes, not an imported grader.

### 7. `qa-history.sh`

New partial: `tests/gate/kit/test_qa_history.py::test_history_shape`.
Maps all four shape refusals: unknown repo nosuch, missing all-zero commit,
short clone SHA and absent commit; same case/field diagnostics, exits1. Valid
history-input acceptance is also driven. The fixture retains real kit commit
711392a and a real scratch clone with deep/er/leaf.txt.

UNCONVERTED: both role runs PASS; kit's whole archived-tree file count and deep
schema file visible; kit case has exactly one fixture commit; clone leaf and
one file visible; input.json records history fixture. Requires recorded role
responses that request these real commands on each exported tree.

### 8. `qa-isolation.sh`

New replacement: **none**. All legacy assertions retained unchanged, especially
Lane576's `forged post record exit 1` and unchanged positive record-line count.
UNCONVERTED exact groups: blocked herdr-say-through-variable and direct herdr
both recorded/refused; lane mask and gh/git credentials recorded/refused; leak
FAIL on delivered call despite later command failure; nocred FAIL no attempt;
tamper FAIL and truncate/overwrite/delete/move/chmod/read-socket all exit1,
forged refusal exit0, post-record forgery exit1, recorder processes reachable0;
actual delivery/forged refusal exits `[0,1]`; pane list is a non-attempt;
overflow FAIL after510 forged refusals with entire511 entries exported; five
history-none proofs and no history-read-only proof; no LIVE/ARCHIVED/SECRET in
transcripts; synchronous herdr/cred/gh records each visible as soon as sender
returns. These require real sandbox actions, not HTTP-only prerecorded result
files. External Herdr replies and provider/tool responses are missing; model
replay alone would not establish recorder isolation.

### 9. `qa-judgment-shape.sh`

Authored input-oracle mapping, runtime/parity still owed:
- `tests/gate/kit/test_qa_judgment_shape.py::test_labels_shape`: missing
  reason/source, invalid label, multiline reason, missing split, label leakage,
  <15 cases, no held-out; valid labelled_by/relabel, blank/multiline/unknown
  labeller fields.
- `tests/gate/kit/test_qa_judgment_shape.py::test_calibration_shape`: valid
  calibration, unknown/missing/wrong-type calibration, evidence missing/outside
  repo; model ban at suite/calibration/held_out/chosen; required nested objects,
  their types/unknown fields, every required child; accuracy .0..1 and Brier
  .0..2 ranges, numeric strings/boolean rejection, nonnegative Brier maximum,
  accepted bool; calibration forbidden on skill-trigger.
- `tests/gate/kit/test_qa_judgment_shape.py::test_model_shape`: missing model
  file and required fields, unknown field, both moving aliases, yes/no-only and
  unclassified kit model refused, pinned -latest and -current accepted, all
  five malformed IDs and missing evidence.
- `tests/gate/kit/test_qa_judgment_shape.py::test_catalogue_shape`: missing
  catalogue/every required key; unknown/blank owner; pinned ID/source/object
  shape; moving-alias list/duplicates; all overlaps; yes/no mapping/ID/record
  shape and each missing/blank ruling/error/evidence plus unknown field.
No threshold value or assertion was weakened. These tests validate input data,
not whether those catalogue rulings describe a real provider. No provider
response is needed to validate the original input-shape contract.

### 10. `qa-kit-ref.sh`

New partial: `tests/gate/kit/test_qa_selection.py::test_selection_refusals`:
unknown kit ref ->64, named missing commit, no run.
UNCONVERTED: c0 role missing named; c1 FAIL before tdd change, c2/head PASS with
full SHAs; readonly extra bind; transcript argv skills from archived qa-kit
only and input/result SHAs; archive cleanup; sibling and head-kit repo masks,
exact bind-back proof/path counts; no sibling secret or head role leak; ENOENT
shows paths actually attempted. Requires c0/c1/c2 role-launch/tool responses
and real sandbox binds/recording. Legacy tracked-only copy and dependency
link remain unchanged; no replacement copier is introduced.

### 11. `qa-ran.sh`

New replacement: **none** for run recording. All oracles remain unconverted:
rpass exit3 recorded with >=7-char head prefix and extra arg; echo/no other
args FAIL with record details; shims-first proof; stdin IN/stdout/exit3 passed
through, unrelated program unshimmed; one non-attempt run record; flag/value
adjacency and positional-prefix pass/fail five cases; fake_qa call intercepted
without real QA recursion, full expected run/compare/analysis output and no
poison/identity disclosure/sandbox; only --runs3 variant passes while --runs1
fails. `fake_qa` is an owned-command simulation in the legacy scenario, so it
cannot be copied into a compliant replacement. Requires a real public route
for the role's nested QA calls plus recorded external responses; any scope or
spec decision about removing that legacy simulation belongs to parent, not
this source change. It is not silently dropped.

### 12. `qa-review.sh`

New partial:
- `tests/gate/kit/test_qa_shape.py::test_review_shape`: no question and graded
  facts on a review case both exit1 with original field diagnostics.
- `tests/gate/kit/test_qa_review.py::test_stored_review`: awaiting show,
  final message, pass/note append, full run and kit provenance, timestamp shape,
  show-after-record, exactly one ledger line, invalid verdict/blank note64,
  graded non-review case64. Input documents are deliberately supplied fixture
  data for this public subcommand, not generated eval artifacts. Added negative
  assertion ensures invalid updates do not append another line.
UNCONVERTED: actual first eval exit1 REVIEW rather than PASS, question/changed
notes.md/stop/tool count, totals0/1, actual review.json/result.json generation;
next two real runs REVIEW0/2 with new output and latest old verdict per run.
Requires two recorded note-writing/final-message response sequences.

### 13. `qa-rt-targets.sh`

New replacement: **none**. All public grading/snapshot assertions remain
unconverted: order FAIL, declared PASS, contract FAIL, fsonly PASS; all seven
before-target fact status/evidence pairs and exact call indices; fs marks
`[edit,test_write],[git_commit],[git_push],[gh_call]`, gh argv log; fsonly first
writes at4/4; declared fixture runner recognizes specs/cli_check.py at5/5, not
tests/README or tests/test_y.py, fs mark sequence; contract edit fail but
kit_contract_edit pass read3 before target4, test_write never reached FAIL.
Requires actual recorded tool requests and tool results with runner snapshots.
No synthetic fs event or imported watcher is introduced.

### 14. `qa-rt.sh`

New replacement: **none**. Original nine cases and all assertions remain
unconverted: partial/roleedit FAIL; setup/incl PASS; full-content skill loads
via cat/dotted/relative reads at original call indices, not ls/grep/head/other
path/limited/truncated reads; fixture-only repoload PASS and reponone FAIL after
rewrite; missing/non-list includes FAIL and exact held entries PASS; no private
grading keys; role/patch versus AGENTS-only fs marks; setup branch work, hb
message and2 commits, tests visible, repo==cwd and head==40-char rev, origin1,
scratch fake-gh path, input retains one literal {repo}. Requires full tool
response recordings (including untruncated skill contents) and actual repo
commands, not snapshots of existing grading output.

### 15. `qa-runs.sh`

New partial: `tests/gate/kit/test_qa_runs.py::test_runs_usage`: counts0/-1/two
exit64 with positive-integer diagnostic/no run; missing count64; help --runs.
UNCONVERTED: alternating alt PASS/FAIL/PASS call facts, 2/3 FAIL exit1 with
rate.67/spread.58 and failed-run fact, total0/1; six artifacts on each of3 run
dirs, run/of/verdict/input.run; exact aggregate rates `.6667/.5774` and
run/dir/verdict list, required provenance fields; summary0/1/runs3/pass_rate;
reads2/2 PASS exit0 with deciding fact; default single run has no repeated-run
lines or run-1 dir/run key, compact runs list and rates1/0. Requires actual
per-run role/tool responses. This old ID is not converted by its usage subset.

### 16. `qa-shape.sh`

Authored validation mapping, runtime/parity still owed:
- `tests/gate/kit/test_qa_shape.py::test_trigger_shape`: task/split/facts/
  unknown fact/skill/missing expectations/ghost ID; skill-path and literal JSON
  leaks including reordered/indented JSON and component paths; adjacent skill
  path/prose/non-fact JSON allowed; trigger-only branch refusal; invalid false
  trigger, attempt kind and declared field/list; missing role and QA's exit2
  with named role/no run.
- `tests/gate/kit/test_qa_shape.py::test_role_shape`: fixture-only skill resolves
  against head fixture; branch/origin/fake_gh and all head fields; prerequisite
  origin/fake_gh; fixture/head test declaration required; invalid before target;
  includes item types/empty/missing field.
- `tests/gate/kit/test_qa_shape.py::test_field_shape`: every original field_lines
  missing/unknown/field/none/includes/every refusal; branch_paths missing,
  wrong-type/relative-path/unknown-field; ran missing/invalid program/args/
  unknown exit; tool list empty/whitespace/missing; doubled-space Prior art.
All original expected diagnostics are literals retained in source. The new
fixtures omit unrelated scripted role tasks because these items only validate
input; they do not claim the transcript facts are evaluated.

### 17. `qa.sh`

New partial:
- `tests/gate/kit/test_qa_selection.py::test_selection_refusals`: unknown
  suite/case and sample0 ->64, additionally asserting no run header.
- `tests/gate/kit/test_qa_coverage.py::test_coverage_gap`: kit's original
  default check-evals success; exact missing implementer pull false/held-out
  diagnostic after removing that quadrant's input cases/expectations.
- `tests/gate/kit/test_qa_coverage.py::test_tracker_coverage`: missing supervisor
  github-issues true/train and exactly one role-skill finding; linear fixture
  expands director/implementer/supervisor coverage, never literal {tracker} or
  unwanted github-issues; jira names fixture field and absent tracker skill.
UNCONVERTED: five actual role results and deciding call indices, linger stop
and original100s bound, pi crash3 FAIL; sandbox no persistent writes; 3/5 and
ordered train2/3/held-out1/2/summary; seven per-case artifacts plus summary,
prompt/input expectation isolation; actual launcher argv mode/session/skills
and model; proof and agents_started, scores; two selected passing cases;
stratified deterministic sample2 of5, flags/splits, seeded header before run,
train1/1; failed Herdr proof never executes role/transcript; gate-marker refusal
exit70/no run. Marker-environment manipulation is not added under this source
scope. Requires recorded model/tool requests, a real sandbox proof-failure
route and later parent-authorized tests. No timing bound is shortened.

### 18. `spend-ledger-qa.sh`

New replacement: **none**. All assertions remain unconverted: seed10; actual
QA look case PASS exit0 via real Pi;11 ledger calls; `(no lane) implementer`
row `.170000/1/0/150/10`; prior gh149 total `.824100/8/1/1357/113` unchanged.
The old seeded ledger inputs and prices cannot substitute for the actual QA
call's extension/writer provenance. Needs a recorded OpenAI-compatible
`POST /v1/chat/completions` request/stream with usage150 input/10 output and
real Pi plus the spend extension. Headless Pi and new recording calls are not
authorized here. No handmade fake-provider response is added.

## Missing strict recordings and existing-data search

Read `tests/lib/qa.sh` and `tests/lib/spend-ledger.sh` completely, and all18
original scripts. Inspected existing testkit docstring/owners and relevant
Pi/provider/gh-recording sources without executing them.

Searches were read-only, within this checkout:
- `find **/*record*` under tests finds gh_recordings scenario/test/helper and
  argv_recorder.sh, not QA provider tapes.
- `find **/*cassette*` across the repo returns none.
- `grep vcr|record_mode|onUnhandledRequest|replay` under testkit finds GH
  mechanisms, not model request/response tapes.
- `tests/gate/fixtures` does not exist at this baseline. Existing fixture owner
  is `tests/fixtures`; no empty alternate directory is introduced.
- `testkit/pi_agent.py` explicitly describes a canned stream selected by
  STUB-* prompt tokens. It is not a recording of an external model response.
- `tests/lib/qa.sh`'s pi-extension defines synthetic catalogue/classify answers
  in a modelRegistry; these are not recorded provider responses.
- `testkit/provider.py` synthesizes SSE deltas, tool calls and usage according
  to request text; its optional log records requests, not strict responses.
- `testkit/gh_recordings.py` is a GH-specific existing owner. Reusing a GH tape
  cannot prove a classifier/model/Pi tool lifecycle. No second replay store,
  missing-response fallback or recording fetch was authored.

Missing data must identify the actual model/API/SDK operation, request body,
response status/headers and complete byte stream, plus every sequential tool
turn for the named cases above. There is no established real-provider endpoint
or recorded request body for the synthetic `stub/*` identities, so this report
does not invent one. A transcript alone replayed in place of owned Pi would
violate the owned-code rule. Real Pi must consume strict provider responses;
local tools/sandbox/recorder/extension/grader still execute for real. This is
precise readiness debt, not a request to run live models now.

## Source validation and safety extent

Performed Python AST parsing as data only on all14 new Python files. A syntax
error in a nested input-dict comprehension was observed and corrected, then
all14 parsed. This does not import, collect or run those files. Git diff
whitespace/path/baseline checks are recorded in the worker's final report.
Ruff, basedpyright, import contracts and runtime remain UNRUN. No TDD red or
green is claimed. Source formatting/typing is not certified by AST parsing.

Safety fact: no product, shared testkit, conftest, dependency, legacy assertion,
spec, skill, duty or marker file is changed. Existing public behavior and old
oracles are retained byte-for-byte. This is a Git/source preservation proof,
not evidence the added tests pass or satisfy CPU budgets. Tests may add gate
work while old/new coexist. Gross setup and waited-descendant CPU must be
measured by parent; no fixture/setup subtraction, readiness sleep, marker
change, threshold change or test skip/xfail is used.

No new user-facing feature is added, so no verify feature-map change is made.
Verify drives and evidence records are unrun under the runtime prohibition.

## Planned commands, NOT RUN

Small parent-authorized smoke first, using the existing public recipe:

`just test -x -rA tests/gate/kit/test_qa_runs.py::test_runs_usage`

Then selected authored inputs only:

`just test -x -rA tests/gate/kit/test_qa_runs.py tests/gate/kit/test_qa_shape.py tests/gate/kit/test_qa_review.py tests/gate/kit/test_qa_history.py tests/gate/kit/test_qa_judgment_shape.py tests/gate/kit/test_qa_selection.py tests/gate/kit/test_qa_coverage.py`

These demonstrate the specific public input/refusal/stored-review facts mapped
above, not the unconverted eval lifecycle. Parent must then authorize the gate
and safe sandbox/model replay routes, measure gross CPU and route independent
review. Neither `just fast` nor `just check` is claimed green here.

Existing parity lever takes exactly one CASE, not pytest flags:
`python3 tests/parity/lever.py qa-shape` and
`python3 tests/parity/lever.py qa-judgment-shape` are future exact invocations
ONLY after their case.toml/seed patches exist and parent authorizes old runs.
No such lever cases are authored here: parity files are outside this worker's
write scope and the old observer/bootstrap side is not safe to execute under
this grant. Planned case data: old_at0048..., original old script plus full
transitive `needs`, new corresponding test file(s), `ran` coverage/exec fact
for each seeded product path. Seed intent: wrong leak component boundary,
dropped required role/fact field, accepted bad before target, admitted model
key at depth, ignored catalogue overlap, numeric bool calibration accepted.
Each must make BOTH old and new fail on the SAME product, with both clean
sides passing first. For split new files, use a case per appropriate file or
parent-owned supported selection, never modify the lever. No seeded parity
or legacy retirement is claimed from source inspection.

Evidence: none
Checks: none
Owners: none
Prior art: none

No infrastructure choice or new dependency was made. Existing pytest9.1.1,
stdlib JSON/AST, testkit and public commands are reused; no web lookup was
permitted or performed. No policy owner text is changed, so no owned rule is
added for a duplicate-rule search to find. Tests quote existing diagnostics,
not new policy.
