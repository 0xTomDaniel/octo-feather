# new-repo

Criteria:

- [templates#acceptance-starter-verify](../../../../docs/specs/templates.spec.html#acceptance-starter-verify)

Drive criterion: `templates#acceptance-starter-verify`

## Sub-features

- `create` a repo from `qc.toml` `values.lang` at a new DEST.
- `refuse-nonempty` DEST already holds a repo: refused, that repo untouched.
- `refuse-lang` an unknown LANG: refused, DEST not created.

## How to get to it (user POV)

- In the kit checkout: `just new-repo python ~/src/NAME` (or `typescript`), then `cd` there, `just setup`, `just check`.
- `just --list` names the recipe; `octo-feather-new-repo --help` prints its usage.

## Driving it with verify-octo-feather

Preconditions:

- `verify-octo-feather launch` printed `ready`; `verify-octo-feather doctor` exits 0 with no Spec Chat WARN.
- DEST: `VERIFY_OCTO_FEATHER_NEW_REPO_DEST` ([SKILL.md](../SKILL.md), Run state and evidence).

Run all cases: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive new-repo`. Evidence: `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/new-repo/`.

- **Create** (`create`). Run `just --justfile <kit>/justfile new-repo <lang> <dest>` from an empty cwd. Observe exit 0 and the summary line naming DEST and the template; in DEST: one commit on `main` from the template, a clean `git status`, exactly the template's tracked files, a `Repo skills:` line naming a `verify-*` skill whose `SKILL.md` exists, and `octo-feather-contract DEST` ok.
- **Non-empty DEST** (`refuse-nonempty`). Run the same command again. Observe exit 1, `exists and is not empty` on stderr, DEST's HEAD unchanged.
- **Unknown LANG** (`refuse-lang`). Run `just --justfile <kit>/justfile new-repo no-such-lang <new path>`. Observe exit 1, `unknown LANG` on stderr, the path not created.
- **Side effects.** Every case leaves its cwd empty and the kit's `git status` unchanged. Cleanup removes DEST and every other path the drive created; the evidence folder stays.

## Gotchas

- Spec Chat: new-repo links Spec Chat's skills from `$SPEC_CHAT_CLONE` (default `~/src/spec-chat`); without its installer the create case fails. That is the command's real behavior, not a drive bug: clone Spec Chat, never drive with `--no-spec-chat` to make it pass.
- The starter's own verify skill run (the rest of `#acceptance-starter-verify`) needs the new repo's `just setup`, which installs from the network; this drive stops at the repo's files. Drive that from inside the new repo with its own `verify-app` skill, on a box where the network is allowed.
- new-repo refuses a DEST inside any git work tree: the default DEST under `/tmp` is outside the kit checkout.
