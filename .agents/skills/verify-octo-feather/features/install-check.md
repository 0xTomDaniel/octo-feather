# install-check

Criteria:

- [remote#acceptance-install-browser](../../../../docs/specs/remote.spec.html#acceptance-install-browser)
- [remote#acceptance-install-agent-browser](../../../../docs/specs/remote.spec.html#acceptance-install-agent-browser)

Drive criterion: `remote#acceptance-install-browser`
Drive criterion: `remote#acceptance-install-agent-browser`

## Sub-features

- `offline` the install check run for the kit as target with no network.
- `models-offline` the model check (`just install-check-models`) with no network.

## How to get to it (user POV)

- On a fresh box: the README's bootstrap, which runs it and each fix it prints until it exits 0 (#463).
- In the kit checkout: `just install-check` (target: the invocation directory), or in a target repo `just -f <kit>/justfile install-check`.
- At box setup and after a model key change: `just install-check-models` (what it checks and when: spec remote#host-models).

## Driving it with verify-octo-feather

Preconditions:

- `verify-octo-feather launch` printed `ready`; `verify-octo-feather doctor` exits 0 with no `unshare` WARN.

Run: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive install-check`. Evidence: `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/install-check/`.

- **Offline** (`offline`). Run `unshare -Un --map-current-user just --justfile <kit>/justfile install-check <kit>` from an empty cwd. Observe exit 1; one line per tool (`herdr pi gh jq git just python3 node`), each `ok  <path>` or `MISSING; <install command>`; the box fact lines (#461), each ok or its gap with the fix: `kernel` (6.6 or later), `userns` (`unshare -rm true`), `state` (the session state folder's `lanes/`), `kit` (the live kit install a clone on main), `agent-browser browser` (its Chrome outside the cache folder the qc sandbox masks), `ffmpeg` (ok or OPTIONAL, never a failure); `identity` (the factory commit identity every role launch applies: ok naming it and the box onboarding file, or MISSING naming `[identity] name and email` and `pi-role --set-identity`, #665); the one manual step `sharing MANUAL ... ssh exe.dev share set-private <vm>`; the review service line (`review ok  spec-chat-review.service active, enabled ...`, or `NOT RUNNING`/`MISSING` naming `install-spec-chat --review <spec> --public <vm>.exe.xyz --service`); `models MANUAL ... just install-check-models` (no model call); a Pi version line (ok or WRONG VERSION); an agent-browser line (version ok, WRONG VERSION or MISSING); `gh NOT authenticated (gh auth login)`; `tracker <skill> (target <kit>)`.
- **Models offline** (`models-offline`). Run `unshare -Un --map-current-user just --justfile <kit>/justfile install-check-models` from an empty cwd. Observe exit 1; `models pi <path> (...)`; one `model  <provider/id> UNREACHABLE (...) for roles <roles>; the model proxy for provider <p> did not answer: ...` line per model the role files name and one for the judgment model (`for judgment model (evals/judgment-model.json): ...`), none ok, REJECTED or FAILED; `models spend 0.0000 USD (<n> calls, ...)`. No network, so no model is called and no key is spent.
- **Side effects.** The cwd stays empty and the kit's `git status` unchanged.

## Gotchas

- The install-check drive reaches no network (SKILL.md), so the case runs in a network namespace (`unshare -Un`): `gh auth status` cannot reach GitHub and reports not authenticated, so exit 1 is the expected result here, not a box fault. A box without user namespaces fails the case naming `unshare`; run `just install-check` by hand there.
- The kit drives no browser (its `qc.toml` has no `[browser]`), so this case prints no browser line and a PASS proves the tool listing only, not the criterion's browser line. The browser line (MISSING naming the Playwright pin, the box folder and the install command; ok when the headless shell is in the folder) is proven by `tests/install-check-browser.sh` on a fixture target whose `qc.toml` declares `[browser] playwright = "<pin>"`.
- The agent-browser line shows this box's state only; the other states are proven by `tests/install-check-browser.sh` (a stub, and a PATH without agent-browser).
- The drive never proves a key: ok and REJECTED (a key with trailing terminal characters) are proven by `tests/install-check-models.sh` with the stub `tests/fixtures/install-check/pi` first on PATH; a real ok run costs a few tiny model calls, so it is run by hand only.
- Tool lines depend on the box: the case checks each tool has a line, not that it is installed.
- pi and agent-browser installed by their npm fix lines land in mise's node bin dir; how their `path` lines judge them: the justfile's install-check (#463). The drive shows this box's layout only; `tests/install-check-mise.sh` proves that case with a `path:` node version.
- The srt host dependency lines come from the existing `just install-check` dependency loop. `tests/install-check-box.sh` proves `rg` present, absent with its actionable host-package fix, and restored through that public command; `tests/gate/kit/testkit/install_check.py` supplies a fixture executable and removes host `rg` from the fixture PATH. The box integration cases passed the supervisor's frozen dirty-tree diagnostic; the live verify drive and final exact-head CI provisioning proof remain PENDING (evidence/2026-11-08-gh576-ci-prerequisites.md).
- The box fact lines show this box's state only (the `kit` line is ok in a clone on main or a worktree detached at main, a gap on a branch, off main or in a copy that is no clone); each ok and gap state is proven by `tests/install-check-box.sh` with stub probes (`uname -r`, `unshare`, `agent-browser doctor`, `ffmpeg`) and scratch folders (`XDG_STATE_HOME`, `OCTO_FEATHER_KIT_INSTALL`).
