# new-repo

Criteria:

- [templates#acceptance-starter-verify](../../../../docs/specs/templates.spec.html#acceptance-starter-verify)

Drive criterion: `templates#acceptance-starter-verify`

## Sub-features

- `create` a repo from `qc.toml` `values.lang` at a new DEST, Spec Chat linked (needs Spec Chat's installer).
- `spec-chat-link` and `create-no-spec-chat`, in place of `create` where the installer is absent: the Spec Chat link step reported unreachable, the rest created with `--no-spec-chat`.
- `refuse-nonempty` DEST already holds a repo: refused, that repo untouched.
- `refuse-lang` an unknown LANG: refused, DEST not created.

## How to get to it (user POV)

- In the kit checkout: `just new-repo python ~/src/NAME` (or `typescript`), then `cd` there, `just setup`, `just check`.
- `just --list` names the recipe; `octo-feather-new-repo --help` prints its usage.

## Driving it with verify-octo-feather

Preconditions:

- `verify-octo-feather launch` printed `ready`; `verify-octo-feather doctor` exits 0. Its Spec Chat WARN means the drive takes the no-installer route below.
- DEST: `VERIFY_OCTO_FEATHER_NEW_REPO_DEST` ([SKILL.md](../SKILL.md), Run state and evidence).

Run all cases: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive new-repo`. Evidence: `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/new-repo/`.

- **Create** (`create`). Run `just --justfile <kit>/justfile new-repo <lang> <dest>` from an empty cwd. Observe exit 0 and the summary line naming DEST and the template; in DEST: one commit on `main` from the template, a clean `git status`, exactly the template's tracked files, a `Repo skills:` line naming a `verify-*` skill whose `SKILL.md` exists, and `octo-feather-contract DEST` ok.
- **No Spec Chat installer** (`spec-chat-link`, `create-no-spec-chat`; only when `$SPEC_CHAT_CLONE/scripts/install-spec-chat`, default `~/src/spec-chat`, is not executable). First the plain create, the route: observe exit 1, `no Spec Chat installer at` on stderr, DEST not created; the drive prints and records `UNREACHABLE spec-chat-link: Spec Chat installer not at $SPEC_CHAT_CLONE/scripts/install-spec-chat (<path>; ...); prerequisite: ...; route attempted: ...`. Then `create-no-spec-chat` runs `new-repo <lang> <dest> --no-spec-chat` and observes all of Create plus `, no Spec Chat (--no-spec-chat)` in the summary line. The drive's result is `PASS-with-unreachable new-repo (unreachable: spec-chat-link)` only when every other case passes; it never claims the Spec Chat links were made.
- **Non-empty DEST** (`refuse-nonempty`). Run the same command again. Observe exit 1, `exists and is not empty` on stderr, DEST's HEAD unchanged.
- **Unknown LANG** (`refuse-lang`). Run `just --justfile <kit>/justfile new-repo no-such-lang <new path>`. Observe exit 1, `unknown LANG` on stderr, the path not created.
- **Side effects.** Every case leaves its cwd empty and the kit's `git status` unchanged. Cleanup removes DEST and every other path the drive created; the evidence folder stays.

## Gotchas

- Spec Chat: new-repo links Spec Chat's skills from `$SPEC_CHAT_CLONE` (default `~/src/spec-chat`); without its installer plain new-repo refuses. That is the command's real behavior: where the installer is not visible (the qc sandbox hides other repos), the drive reports the link step unreachable with that prerequisite and proves the rest with `--no-spec-chat`, labelled so in the case name and evidence. A `--no-spec-chat` create never proves the links: to prove them, drive where Spec Chat is cloned (result `PASS`).
- The starter's own verify skill run (the rest of `#acceptance-starter-verify`) needs the new repo's `just setup`, which installs from the network; this drive stops at the repo's files. Drive that from inside the new repo with its own `verify-app` skill, on a box where the network is allowed.
- new-repo refuses a DEST inside any git work tree: the default DEST under `/tmp` is outside the kit checkout.
