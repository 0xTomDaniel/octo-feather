# gh503: merge ask full proof and brownfield full gate; verify-octo-feather drives them (merge-ask-proof)

Change: the verify-octo-feather skill gains the `merge-ask-proof` feature (ticket #534, lane gh503): features/merge-ask-proof.md (Drive criterion lines `issue-lifecycle#acceptance-merge-ask-full-proof`, `issue-lifecycle#acceptance-brownfield-full`), its features/README.md index line, the SKILL.md description, Drive list, values line and offline-gh sentence, the drive in scripts/verify-octo-feather, and the two kit qc.toml demos running it (commit 385bf97).

Smoke: .agents/skills/verify-octo-feather/SKILL.md (description, Drive list and offline gh name merge-ask-proof; run below)
Smoke: .agents/skills/verify-octo-feather/features/README.md (index line for merge-ask-proof; run below)
Smoke: .agents/skills/verify-octo-feather/features/merge-ask-proof.md (the recipe the run below follows)
Removed: nothing.

## Recorded live run at head 8b3a18e

Clean tree at 8b3a18e (385bf97 merged with gh503 f106536), run and evidence folders the helper's defaults under /tmp, drive records to the kit's real store; no model, no network (the kit's offline read-only gh, scratch snapshot), no live lane. Command, as SKILL.md and features/merge-ask-proof.md give it (the qc.toml demos' form):

```
.agents/skills/verify-octo-feather/scripts/verify-octo-feather run --unreachable-exit 77 merge-ask-proof
```

Exit 0 in 9 s, `verify-octo-feather: run PASS`. summary.txt verdicts:

```
PASS full-proof-no-pass
PASS brownfield-full-1
PASS brownfield-full-2
PASS full-proof-after-integrate
PASS merge-ask-proof
```

What each case showed:

- `full-proof-no-pass`: `octo-feather-lane merge-ask 9 --status docs/specs/demo.status.json --base main` in the scratch lane gh534 at a commit no gate ran on: exit 1, `PR #9 merge ask incomplete (1 item), head <h>:` / `- Full pass: head <h> has no current recorded full gate pass for that head and its gate configuration (none recorded on <h> or the lane commits before it): run the full gate, just check, on <h> and record its pass (...)`.
- `brownfield-full-1`: `octo-feather-integrate 534 w1` in the scratch target with only `check`: `tier: full (no fast recipe in this repo: its one gate is the full tier; pilot: no full pass recorded on gh534)`, `own-gate ran`, `recorded: full pass of <head>`; `octo-feather-gate passed` exit 0 for the lane head; `just --summary` still `check`.
- `brownfield-full-2`: the second integration, past the pilot: `tier: full (no fast recipe in this repo: its one gate is the full tier)`, `own-gate ran`, recorded; recipes still `check`.
- `full-proof-after-integrate`: the same merge ask on the integrated head: exit 0, the section printed.

Evidence records (kit store, one per Drive criterion line), read with `octo-feather-evidence read --criterion <id> --commit 8b3a18e`:

- 20261104T185007Z-3d2ade69 issue-lifecycle#acceptance-merge-ask-full-proof
- 20261104T185007Z-ac444148 issue-lifecycle#acceptance-brownfield-full

Owed eval: docs/owed-evals/503.md.
