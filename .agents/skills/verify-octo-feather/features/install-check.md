# install-check

Criteria:

- [remote#acceptance-install-browser](../../../../docs/specs/remote.spec.html#acceptance-install-browser)

Drive criterion: `remote#acceptance-install-browser`

## Sub-features

- `offline` the install check run for the kit as target with no network.

## How to get to it (user POV)

- In the kit checkout: `just install-check` (target: the invocation directory), or in a target repo `just -f <kit>/justfile install-check`.

## Driving it with verify-octo-feather

Preconditions:

- `verify-octo-feather launch` printed `ready`; `verify-octo-feather doctor` exits 0 with no `unshare` WARN.

Run: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive install-check`. Evidence: `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/install-check/`.

- **Offline** (`offline`). Run `unshare -Un --map-current-user just --justfile <kit>/justfile install-check <kit>` from an empty cwd. Observe exit 1; one line per tool (`herdr pi gh jq git just python3 node`), each `ok  <path>` or `MISSING`; a Pi version line (ok or WRONG VERSION); `gh NOT authenticated (gh auth login)`; `tracker <skill> (target <kit>)`.
- **Side effects.** The cwd stays empty and the kit's `git status` unchanged.

## Gotchas

- The install-check drive reaches no network (SKILL.md), so the case runs in a network namespace (`unshare -Un`): `gh auth status` cannot reach GitHub and reports not authenticated, so exit 1 is the expected result here, not a box fault. A box without user namespaces fails the case naming `unshare`; run `just install-check` by hand there.
- The kit drives no browser (its `qc.toml` has no `[browser]`), so this case prints no browser line and a PASS proves the tool listing only, not the criterion's browser line. The browser line (MISSING naming the Playwright pin, the box folder and the install command; ok when the headless shell is in the folder) is proven by `tests/install-check.sh` on a fixture target whose `qc.toml` declares `[browser] playwright = "<pin>"`.
- Tool lines depend on the box: the case checks each tool has a line, not that it is installed.
