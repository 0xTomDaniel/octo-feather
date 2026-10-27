# gh195: the kit's own verify skill, verify-octo-feather, and qc.toml

Smoke: .agents/skills/verify-octo-feather/ (the helper's live run on the box, by the implementer, section Smoke below; an isolated role run is pending, docs/owed-evals/136.md)
Removed: nothing; a new skill folder, the kit's `qc.toml` and the `Repo skills:` line in `AGENTS.md`.

## Change

- `.agents/skills/verify-octo-feather/`: made by following `create-verification-skill` (loaded by path). SKILL.md with Contract, Run state and evidence, Launch, Doctor, Drive, Evidence, Cleanup, Helpers; feature map `features/` with `new-repo`, `install-check`, `contract`, `evidence`, each linking its criteria by anchor; helper `scripts/verify-octo-feather`.
- `qc.toml` at the kit root, format 1: the entry is the kit's commands on PATH; no setup, services or fixtures; values for the drives. `octo-feather-contract .` prints `./qc.toml: ok (format 1)`.
- `AGENTS.md`: `Repo skills: verify-octo-feather`, and the skill and `qc.toml` in Layout.

## Smoke

Not a role run: the implementer ran the helper on the box (no Pi process), with `XDG_STATE_HOME`, `VERIFY_OCTO_FEATHER_RUN_DIR`, `VERIFY_OCTO_FEATHER_EVIDENCE_DIR` under /tmp so the iterations wrote no record to the kit's real store. `launch`, `doctor` (all ok), then each feature, then `cleanup` (run dir gone, evidence kept), at 2a47730 plus the uncommitted change:

```
PASS kit / missing-entry / no-contract, PASS contract
PASS append-a / append-b / read-a / read-b-text, PASS evidence
PASS offline, PASS install-check
PASS create / refuse-nonempty / refuse-lang, PASS new-repo
```

Induced failures: `VERIFY_OCTO_FEATHER_RUN_DIR` under a mode 555 folder: `launch` exits 1, `cannot write run state folder: /tmp/w195-ro/run`. `SPEC_CHAT_CLONE=/nonexistent`: `create` and `refuse-nonempty` FAIL, the drive exits 1 and still appends its record.

The demo (`just new-repo python /tmp/gh136-demo-kit` through `verify-octo-feather run new-repo` at the committed head, its record read back by commit) is in the implementer's report to the supervisor.

Pending: an isolated role run (an implementer in the qa sandbox loading the skill from the kit's `Repo skills:` line and driving it), docs/owed-evals/136.md.
