# qc-insufficient

Criteria:

- [quality#acceptance-qc-insufficient](../../../../docs/specs/quality.spec.html#acceptance-qc-insufficient)

Drive criterion: `quality#acceptance-qc-insufficient`

## Sub-features

- `qc` `just qc` on a scratch target whose declared demo needs a step the qc sandbox cannot run (GitHub: the sandbox's offline gh refuses it, and the demo says so with exit 77): the result insufficient evidence naming what is missing, no FAIL, exit 2, the criterion still planned, no status commit.
- `merge-ask` `octo-feather-lane merge-ask` on that head, its merge ask listing the criterion as a triaged failure: the check fails naming it as insufficient evidence, with what is missing and its qc report.

## How to get to it (user POV)

- A supervisor runs `just qc docs/specs/<slug>.status.json <PR> <id>...` on the lane's integrated head, then `octo-feather-lane merge-ask <PR> --status <status file>`. A demo that stops before its end (exit 77 for a step it needs that could not run, 126 or 127 for a command the shell could not run, above 128 for a signal) leaves its criterion insufficient evidence; `octo-feather-qc` and `octo-feather-lane` with no arguments print their usage, which owns the rest.

## Driving it with verify-octo-feather

Preconditions:

- `verify-octo-feather launch` printed `ready`; `verify-octo-feather doctor` exits 0.
- Unprivileged nested user namespaces (`unshare -rm`): the qc sandbox needs them.

Run all cases: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive qc-insufficient`. Evidence: `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/qc-insufficient/`.

The drive makes a scratch target (the kit's `tests/fixtures/spec-status/good/demo.spec.html`, its status file, a `qc.toml` whose one demo is `qc.toml` `values.qc_demo_insufficient`), scratch box state (`XDG_STATE_HOME` under `$VERIFY_OCTO_FEATHER_RUN_DIR/scratch/qc-insufficient/state`) and a scratch GitHub snapshot of PR #7 there, which the kit's offline gh (`.agents/skills/github-pr/scripts/gh`) serves to merge-ask.

- **qc** (`qc`). In the scratch target (`env -C <scratch>`), run `just --justfile <kit>/justfile qc docs/specs/demo.status.json 7 acceptance-a`. Observe exit 2; `INSUFFICIENT EVIDENCE acceptance-a`, then `missing: demo did not run to its end (exit 77, a step it needs could not run here): needs GitHub...`, then `evidence incomplete; decision demo checks; record <id>`; no `FAIL` line; the line `qc: insufficient evidence, never a failure to triage: acceptance-a`; the head unchanged, `acceptance-a` planned, the worktree clean.
- **Merge ask** (`merge-ask`). With `OCTO_FEATHER_GHSNAP` at the snapshot and the offline gh first on PATH, run `octo-feather-lane merge-ask 7 --status docs/specs/demo.status.json`. Observe exit 1, nothing on stdout, and on stderr `criterion demo#acceptance-a: insufficient evidence at the judged head <head12> (demo did not run to its end (exit 77, ...): needs GitHub...; qc report <file>): never triaged`.
- **Side effects.** Every cwd stays empty and the kit's `git status` unchanged; no live lane state or box store is written.

## Gotchas

- The merge ask in the snapshot is incomplete on purpose (no review verdict): the case checks only that the check fails naming the criterion, beside the other items it lists.
- The drive's own record (its Drive criterion line) goes to the kit's real store; the scratch target's records stay in the scratch store and go with cleanup.
- Run inside a qc sandbox (the kit's own `just qc` on this criterion), the nested qc sandbox must pass its proof, as for qc-capture.
