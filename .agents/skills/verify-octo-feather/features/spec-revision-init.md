# spec-revision-init

Criteria:

- [issue-lifecycle#acceptance-revision-preserve](../../../../docs/specs/issue-lifecycle.spec.html#acceptance-revision-preserve)
- [issue-lifecycle#acceptance-revision-remove](../../../../docs/specs/issue-lifecycle.spec.html#acceptance-revision-remove)
- [issue-lifecycle#acceptance-revision-repeat](../../../../docs/specs/issue-lifecycle.spec.html#acceptance-revision-repeat)
- [issue-lifecycle#acceptance-revision-invalid](../../../../docs/specs/issue-lifecycle.spec.html#acceptance-revision-invalid)

Drive criterion: `issue-lifecycle#acceptance-revision-preserve`
Drive criterion: `issue-lifecycle#acceptance-revision-remove`
Drive criterion: `issue-lifecycle#acceptance-revision-repeat`
Drive criterion: `issue-lifecycle#acceptance-revision-invalid`

## Sub-features

- `fresh` `octo-feather-spec-status init` on a spec with no status file yet.
- `revision` the same init on an owner-accepted revision over the existing status file (what it does: issue-lifecycle spec `#spec-status-file`).
- `check` `octo-feather-spec-status check` after it, a call logged before the revision naming the dropped criterion.
- `repeat` the same init again after a lane built the new criterion.
- `invalid` the same init over a status file holding a partial evidence link.

## How to get to it (user POV)

- The director, in the Spec PR step (`agents/director.md`), runs `octo-feather-spec-status init docs/specs/<slug>.spec.html <commit>` at the accepted commit. What init does over an existing status file: issue-lifecycle spec `#spec-status-file`; when it refuses: `octo-feather-spec-status` usage, the `init` paragraph.

## Driving it with verify-octo-feather

Preconditions: `verify-octo-feather launch` printed `ready`; `verify-octo-feather doctor` exits 0.

Run all cases: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive spec-revision-init`. Evidence: `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/spec-revision-init/`; each case's status file before and after as `<case>.obs.before` and `<case>.obs.after`. The run's stdout shows each case's command, exit, stdout and stderr (a refusal's message), and the status file before and after it in full.

The drive makes a scratch git repo under `$VERIFY_OCTO_FEATHER_RUN_DIR/scratch/spec-revision-init/repo`, its spec the kit's `tests/fixtures/spec-status/revision/accepted.spec.html` (criteria a, b, c), later `revised.spec.html` (a, b, d), each committed; every case runs in that repo (`env -C`).

- **Fresh** (`fresh`). `init docs/specs/demo.spec.html <accepted>`. Observe exit 0 and a, b, c each `{"status": "planned", "pr": null}`.
- Between cases the drive runs `octo-feather-spec-status built` as a lane would: a built in PR 7 with an evidence link, b in PR 8 with none, and logs a call naming c, then commits the revision.
- **Revision** (`revision`). `init docs/specs/demo.spec.html <revised>`. Observe exit 0; a's and b's rows byte-identical to before; criteria exactly a, b, d, d planned; accepted_commit the revised commit.
- **Check** (`check`). After the drive commits the status, `check docs/specs`. Observe exit 0, `spec-status: ok (1 status files)`: the call naming the dropped c was in the log at the accepted commit.
- **Repeat** (`repeat`). The drive builds d with `--record`, `--commit` and `--test`; the same init. Observe exit 0 and the file byte-identical, d's evidence link in it.
- **Invalid** (`invalid`). The drive strips a's `commit` and `tests`; the same init. Observe a non-zero exit, stderr naming `acceptance-a: names record without commit, tests`, and the file byte-identical.
- **Side effects.** Every cwd stays empty and the kit's `git status` unchanged.

## Gotchas

- What a kept row's bytes are kept as: `octo-feather-spec-status` usage, the `init` paragraph.
