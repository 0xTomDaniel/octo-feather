# gh243: verify-octo-feather new-repo drive without the Spec Chat installer

Smoke: .agents/skills/verify-octo-feather/ (the helper's live runs on the box, by the implementer, section Smoke below; no role run: owed, docs/owed-evals/136.md)
Removed: the new-repo Gotcha "never drive with `--no-spec-chat` to make it pass"; a `--no-spec-chat` create is now its own labelled case beside an UNREACHABLE spec-chat-link step, never a proof of the links.

## Change

- `scripts/verify-octo-feather`: installer absent at `$SPEC_CHAT_CLONE/scripts/install-spec-chat` (default `~/src/spec-chat`): case `spec-chat-link` attempts the plain create (the route; must refuse, create nothing), then the drive prints and records `UNREACHABLE spec-chat-link: <prerequisite>; route attempted: <cmd> -> exit 1: <refusal>`; case `create-no-spec-chat` runs `new-repo LANG DEST --no-spec-chat` with every create check plus `, no Spec Chat (--no-spec-chat)` in the summary line. Result `PASS-with-unreachable` only when every other case passes. Installer present: unchanged.
- `features/new-repo.md`, `SKILL.md`: the new case, the result line. kit-mini fixture: byte copy.
- Commit 94f5f12. Why: qc at 4eb2150 failed templates#acceptance-starter-verify, the qc sandbox hiding the installer (#227).

## Smoke

Not a role run: the implementer ran `verify-octo-feather run new-repo` on the box at 7279bae plus the uncommitted change (no Pi process), run and evidence folders under `<tmp>`. Each run appended one record to the kit's evidence store.

Installer absent (`SPEC_CHAT_CLONE=<tmp>/empty`), exit 0:

```
WARN     no Spec Chat installer at <tmp>/empty/scripts/install-spec-chat: the new-repo drive creates with --no-spec-chat and reports the Spec Chat link step unreachable (features/new-repo.md Gotchas)
UNREACHABLE spec-chat-link: Spec Chat installer not at $SPEC_CHAT_CLONE/scripts/install-spec-chat (<tmp>/empty/scripts/install-spec-chat; SPEC_CHAT_CLONE defaults to ~/src/spec-chat); prerequisite: a Spec Chat clone there or SPEC_CHAT_CLONE set to one; route attempted: XDG_STATE_HOME=<tmp>/run/scratch/state just --justfile <kit>/justfile new-repo python <tmp>/run/scratch/new-repo/python -> exit 1: octo-feather-new-repo: no Spec Chat installer at <tmp>/empty/scripts/install-spec-chat; clone Spec Chat there, set SPEC_CHAT_CLONE to its clone, or pass --no-spec-chat
PASS create-no-spec-chat: XDG_STATE_HOME=<tmp>/run/scratch/state just --justfile <kit>/justfile new-repo python <tmp>/run/scratch/new-repo/python --no-spec-chat
    stdout: octo-feather-new-repo: <tmp>/run/scratch/new-repo/python from templates/python @ 7279bae, one commit on main by ..., no Spec Chat (--no-spec-chat)
PASS refuse-nonempty / PASS refuse-lang
verify-octo-feather: drive new-repo PASS-with-unreachable (unreachable: spec-chat-link)
verify-octo-feather: evidence record 20261028T002043Z-bef0c43d (criterion templates#acceptance-starter-verify; read: octo-feather-evidence read --criterion templates#acceptance-starter-verify --commit 7279bae)
verify-octo-feather: run PASS-with-unreachable
```

Installer present (default `~/src/spec-chat`), exit 0, unchanged:

```
ok       Spec Chat installer ~/src/spec-chat/scripts/install-spec-chat (new-repo links it)
PASS create: XDG_STATE_HOME=<tmp>/run/scratch/state just --justfile <kit>/justfile new-repo python <tmp>/run/scratch/new-repo/python
    stdout: octo-feather-spec-chat: 3 Spec Chat skill links in <tmp>/run/scratch/new-repo/python/.agents/skills, ignored in <tmp>/run/scratch/new-repo/python/.git/info/exclude
PASS refuse-nonempty / PASS refuse-lang
verify-octo-feather: drive new-repo PASS
verify-octo-feather: evidence record 20261028T002050Z-9898f37b (criterion templates#acceptance-starter-verify; read: octo-feather-evidence read --criterion templates#acceptance-starter-verify --commit 7279bae)
verify-octo-feather: run PASS
```

Gate: `OCTO_FEATHER_BASE=7279bae just check`, 47 passed, at 94f5f12's tree.
