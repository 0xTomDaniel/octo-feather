# role-launch

Criteria:

- [roles#acceptance-web-roles](../../../../docs/specs/roles.spec.html#acceptance-web-roles)
- [roles#acceptance-director-tools](../../../../docs/specs/roles.spec.html#acceptance-director-tools)
- [roles#acceptance-web-no-other-mcp](../../../../docs/specs/roles.spec.html#acceptance-web-no-other-mcp)
- [roles#acceptance-web-list-once](../../../../docs/specs/roles.spec.html#acceptance-web-list-once)

Drive criterion: `roles#acceptance-web-roles`
Drive criterion: `roles#acceptance-director-tools`
Drive criterion: `roles#acceptance-web-no-other-mcp`
Drive criterion: `roles#acceptance-web-list-once`

## Sub-features

- `<role>` each role's launch: `director`, `supervisor`, `implementer`, `general-worker`, `corrector`, `code-reviewer`, `qc-judge`, `shaper`.
- `other-mcp-<role>` the implementer's and the supervisor's launch in a target whose user and project Pi config each name another MCP server.
- `list-once-<role>` each role's launch from a scratch copy of the kit whose web server list has one more server, no role file changed.
- `identity-unset`, `identity-unset-general-worker`, `identity-set`, `identity-applied` the factory commit identity every launch applies (#665; `pi-role --help`, Commit identity), in scratch state dirs.

## How to get to it (user POV)

- `pi-role --json agents/<role>.md` prints the launch Pi gets: what `herdr-spawn --role <role>` hands a tab, and the same args a headless `pi-role agents/<role>.md -p` runs Pi with. The launch rule: [roles#launch-web](../../../../docs/specs/roles.spec.html#launch-web).

## Driving it with verify-octo-feather

Preconditions:

- `verify-octo-feather launch` printed `ready`; `verify-octo-feather doctor` exits 0.

Run: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive role-launch` (or `run role-launch`). Evidence: `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/role-launch/`. Records: [features/README.md#feature-entry-contract](./README.md#feature-entry-contract), the same folder as outputs. `qc.toml` `values.web_roles` names the roles listing web, `values.web_servers` the kit list's servers. `XDG_CACHE_HOME` (where `--json` writes the role body) is under the run state.

- **Each role** (`<role>`). Run `pi-role --json <kit>/agents/<role>.md`. Observe exit 0 and, in its `args`, `--tools`, `--no-mcp`, `--octo-feather-web-servers` and the `-e` extensions, against [roles#launch-web](../../../../docs/specs/roles.spec.html#launch-web) and [roles#acceptance-director-tools](../../../../docs/specs/roles.spec.html#acceptance-director-tools).
- **Other MCP servers** (`other-mcp-implementer`, `other-mcp-supervisor`). With `HOME` and `PI_CODING_AGENT_DIR` scratch, `mcp.json` there naming `userother`, a scratch git target whose `.pi/mcp.json` names `projother`, run `env -C <target> pi-role --json <kit>/agents/<role>.md`. Observe stdout byte-identical to the role's own case and naming neither server.
- **List once** (`list-once-<role>`). A scratch copy of the kit (`scripts`, `agents`, `extensions`, a skills link) whose `web-mcp.json` adds `added`; `diff -r` of its `agents/` to the kit's is empty. Run `<copy>/scripts/pi-role --json <copy>/agents/<role>.md`. Observe each role's `--tools` against [roles#acceptance-web-list-once](../../../../docs/specs/roles.spec.html#acceptance-web-list-once).
- **Commit identity** (`identity-unset`, `identity-unset-general-worker`, `identity-set`, `identity-applied`). With `XDG_STATE_HOME` a scratch dir holding no onboarding file, run `pi-role --print-env <kit>/agents/implementer.md`: observe exit 1, no stdout, stderr naming `[identity] name and email in the box onboarding file` and `--set-identity`. In the same dir, `pi-role --print-env <kit>/agents/general-worker.md` (edits and writes, never commits): observe exit 0, no stdout. With another scratch `XDG_STATE_HOME`, run `pi-role --set-identity 'Verify Identity' verify@octo-feather.invalid` (exit 0), then `--print-env` again: observe exit 0 and exactly `GIT_AUTHOR_NAME`, `GIT_AUTHOR_EMAIL`, `GIT_COMMITTER_NAME`, `GIT_COMMITTER_EMAIL` with those values.
- **Side effects.** Every cwd stays empty and the kit's `git status` unchanged.

## Gotchas

- The commit identity cases prove the env a launch applies; that a commit carries it (a headless launch whose stand-in pi commits in a repo with no user config) and that a pane's tab gets it (herdr-spawn) are proven by `tests/gate/kit/commit_identity.py`.

- Offline and no model turn: a pass proves the launch Pi is given (the tool allowlist, whether MCP is on, the web extension and list), not that a server answered. That a search returns results and a codemode script reaches no edit or write is a live run, outside this drive: Pi started with the exact director launch, `-p --mode json`, network on, its transcript appended by hand with `octo-feather-evidence append --criterion <c> --outputs <dir>`.
- Pi still reads the other servers' configs; what keeps them out is the launch ([roles#launch-web](../../../../docs/specs/roles.spec.html#launch-web)), so this drive observes the unchanged `--json` output, not Pi's config reads.
