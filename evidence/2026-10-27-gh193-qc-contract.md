# gh193: create-verification-skill reads the app-driver contract (qc.toml)

Smoke: .agents/skills/create-verification-skill/ .skillfile/patches/skills/create-verification-skill/SKILL.md.patch (pending: the supervisor runs its isolated smoke; owed case in docs/owed-evals/136.md)
Removed: nothing; the patch adds one line (the generated skill's **Contract:** item) after its **Run state:** item.

## Change

- One added patch line: a generated verify skill reads the target's `qc.toml` (quality spec `#qc-contract`), invokes only what it declares, documents it without restating its commands, and names `octo-feather-contract` as its validator.
- Vendored folder rebuilt by hand to equal pin plus patch (`skillfile install` never run); the three later hunk headers moved by one line.
- `python3 scripts/check-vendored`: `vendored: ok (20 skills equal authenticated upstream at pin plus patches; skillfile v1.9.2, offline)`.

## Smoke

Pending. No Pi process launched in this lane (box load); the supervisor runs it.
