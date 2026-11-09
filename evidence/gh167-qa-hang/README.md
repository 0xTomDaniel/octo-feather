# Historical QA-hang evidence: source archives, not replay commands

The two former shell launchers in this directory are retired together under
#756, parent #653. This is a historical diagnostic artifact retirement, not a
retired integration test, new diagnostic engine, or new policy. No historical
script was executed for this change. No current test fact is dropped.

**Do not execute, source, eval, or replay either raw archive, including by
passing its text to bash.** The original shebang and comments remain only to
preserve exact historical bytes. They are not current instructions. The
`.txt` suffix and0644 modes alone are not the retirement proof: both old
launcher paths are removed, the executable importer is removed with its
callee, active source references were reviewed, and this README explicitly
replaces replay guidance with the existing public capture workflow below.
Arbitrary explicit execution of archival text is not made safe by its suffix.

## Preserved provenance

Source snapshot: `835f76de2d31f371c3cfb88d523d73b4a4039001`.
Original introduction for both scripts:
`83f259bf0bdbaf4967211d9bcb2c8fcf0963785c`.
The commit containing this README records the paired archival delta.

| Former path in this directory | Raw archive, mode0644 | Bytes | Original Git blob | SHA256 of original and archive |
| --- | --- | ---: | --- | --- |
| loop.sh | loop.sh.txt | 2652 | 0f86258f1d33f3d9261c2ea7d9ac66b9d0dad6d9 | b0dcca8d9a4a9fa12a5cbe4b04efc86386fc7204bb7db6ec4ac2f8bc6cb4bded |
| check-loop.sh | check-loop.sh.txt | 983 | ff149c37833839dc7a5802194846980262d9416d | c7024eeaa20853dc59f14f4b70f3f9ac01a36b570afc8b5a119dceb666bfbe89 |

Both archives are byte-identical to their original Git blobs, including all
original unsafe source and comments. All other historical logs in this
directory, and `../2026-10-27-gh167-qa-hang.md`, remain byte-identical to the
source snapshot. Past timings, counts and observations are preserved as past
observations, not remeasured, corrected, or asserted historically safe.
Historical foreign-read extent remains unknown and is not reconstructed.

## Source reachability and retirement boundary

Before archival, whole tracked-text reference searches for `loop.sh`,
`check-loop`, `gh167-qa-hang`, and the historical artifact names found:

- One real executable importer: `check-loop.sh:7` extracted and evaled
  `loop.sh`'s dump function, then called it at line15. This discovery stopped
  the initial single-file retirement before mutation. Scope was explicitly
  expanded before archiving the paired caller and callee. Archiving only
  loop.sh would have broken a real caller and was not sufficient.
- `../2026-10-27-gh167-qa-hang.md:4,26,45-50` describes historical files and
  completed proof attempts, not a present recipe or launch instruction.
  The note's original paths identify the historical source now archived here;
  the note and raw logs are deliberately not rewritten.
- No active external static caller of either script in the tracked current
  scripts, tests, templates, agents, skills, recipes, CI, or configs. No active
  replay guidance outside the historical pair was found. The entire tracked
  reference result was read, not a truncated subset.

The dynamic gate entry does not collect this evidence directory:
`tests/gate/test_gate.py:31` selects only `tests/*.sh`. The justfile's
`shell-files` recipe excludes `evidence/`; syntax-listing is not a replay
entry point in any case. Neither script is a current integration test or
recipe dependency. With both old paths removed, the former importer route
no longer exists; old-path references inside the archives are historical
data, not a retained executable launch edge.

This is source-reachability evidence for the repository's known current entry
points, not a claim about arbitrary user-composed commands, external clones,
obfuscated dynamic paths or all process observers. The raw archives still
contain unsafe executable-language text. They are not reclassified safe by
filename. Frozen source835 audit annotations and inventories are unchanged;
the canonical audit owner reconciles this actual source delta separately.
No global NONEXEC, full-suite safety or acceptance claim is made.

## Why the old diagnostics are not replayed

`loop.sh.txt:10-22` preserves the old global ps dump and SID-filtered global
ps query, other-PID cmdline/wchan/stack/status/fd/task inspection, optional
py-spy, and host ss. Filtering a host scan by session afterward does not prove
invocation ownership. The former check-loop importer reached that same unsafe
function. The originals also launched repeated QA or full gates with load;
replaying them is not an acceptable baseline or finite replacement.

## Existing finite owned capture workflow, proposed only

Use the existing public no-model QC capture entry, not a new hang recorder:

```sh
scripts/octo-feather-qc --capture-case /tmp/gh653-owned-diagnostic.capture.json -- sleep 1
```

This is the #756 proposed finite workload, **NOT RUN** in this CODEPREP unit.
It is not a replacement for the #751 three-actual-process cleanup witness,
not a surrogate sleeper sensitivity test, and not proof of successful-cleanup
RED equivalence. It intentionally does not reproduce global process trees,
foreign fds/stacks/py-spy/ss, repeated QA batches or historical load timings.

Source entry: `scripts/octo-feather-qc:566-593` runs capture_case through the
existing sandboxed implementation, forwards actual stdout/stderr, writes the
capture note and returns the real case status. `:269-294` waits the directly
launched sandbox command and consumes real producer post records before
returning; sandbox teardown/reaping remains the existing mechanism. These
source anchors identify the intended workflow, not fresh runtime proof of
nested backend ownership or every error path.

Before any later execution the supervisor must consume the exact clean head,
independently close the focused source/backend safety scope, authorize a
bounded run, and obtain any required real native grant/live ACK before START.
The owned driver retains its direct launchers, actual job/hold/cleanup return
codes, capture note/stdout/stderr, and bounded cleanup/EOF waits. Refusal or
missing readiness means no START. This README authorizes no execution, model,
install, old baseline, test batch, full gate, map, or parity run.

## CODEPREP validation and limits

Executed only source/reference/Git metadata and byte comparisons. Both archive
hashes and0644 modes were checked against the original blobs; historical note
and logs were compared to source835. No archived source, reviewed helper,
test, native observer, static check, model, install or gate ran. Commit hooks
explicitly bypassed for this source handoff. The handoff gate is NOT RUN, not
green. The separate supervisor-reported fresh HOLD smoke at f218 is not this
archive change's runtime evidence or broader clearance.

Safety fact: paired removal eliminates the known active importer/callee route
while exact original bytes survive as explicitly non-replayable evidence.
This is a source-level reachability argument, blast-radius2/3; current source
and hashes were directly inspected, but no historical or replacement runtime
safety was exercised. Any additional real caller discovered later blocks a
broader retirement claim until its facts have an authorized retained path.

Declared repo skills loaded: python, verify-octo-feather. TypeScript untouched.
Evidence: none
Checks: none
Owners: none
Prior art: none
Existing QC capture mechanism only; no new infrastructure selection.
Validation: source references, original/archive byte equality, file modes,
unchanged historical note/log bytes and Git diff/status; runtime/gates NOT RUN.
Blockers: replacement capture runtime/backend safety and canonical audit delta
reconciliation remain pending. No acceptance or whole-suite clearance claimed.
