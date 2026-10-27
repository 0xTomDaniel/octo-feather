# evidence

Criteria:

- [quality#acceptance-evidence-record](../../../../docs/specs/quality.spec.html#acceptance-evidence-record)
- [quality#acceptance-evidence-read](../../../../docs/specs/quality.spec.html#acceptance-evidence-read)

Drive criterion: `quality#acceptance-evidence-record`

## Sub-features

- `append-a` append a record at a scratch target's first commit.
- `append-b` append at a second commit: the first record unchanged, the target's git status clean.
- `read-a` read by criterion at the first commit, `--json`: only that commit's record.
- `read-b-text` read at the second commit as text: only its outputs.

## How to get to it (user POV)

- A verify skill's drive runs `append` once per drive. The owner or an agent reads: `octo-feather-evidence read --criterion <spec>#<anchor> --commit <rev>` in the target repo; `octo-feather-evidence --help` for the rest.

## Driving it with verify-octo-feather

Preconditions:

- `verify-octo-feather launch` printed `ready`; `verify-octo-feather doctor` exits 0.

Run all cases: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive evidence`. Evidence: `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/evidence/`.

The drive makes a scratch target (a git repo with two commits) and a scratch store (`XDG_STATE_HOME` under `$VERIFY_OCTO_FEATHER_RUN_DIR/scratch/evidence/state`); the criterion is `qc.toml` `values.scratch_criterion`, its text `values.scratch_criterion_text`.

- **Append** (`append-a`). Run `octo-feather-evidence append --repo <scratch> --criterion <c> --criterion-text <t> --outputs <dir>`. Observe exit 0, one id on stdout, the record naming that id, the first commit and text from caller.
- **Append again** (`append-b`). Commit, change the output, append again. Observe exit 0, the first `record.json` byte-identical, two records, the scratch target's `git status` empty.
- **Read by commit** (`read-a`). Run `read --repo <scratch> --criterion <c> --commit <first> --json`. Observe exactly one record, at the first commit, with its criterion id and text hash, contract and fixture keys, and its output.
- **Read as text** (`read-b-text`). Run `read ... --commit <second>`. Observe the second output's content and revision, not the first's.
- **Side effects.** Every cwd stays empty and the kit's `git status` unchanged; the box's own stores are never written by these cases.

## Gotchas

- The store is keyed by the target's root commit, so every drive's scratch target is a new store; cleanup removes it with the run state.
- This drive's own record (the helper appends one per drive) goes to the kit's real store, not the scratch one: read it with `octo-feather-evidence read --criterion quality#acceptance-evidence-record` in the kit.
