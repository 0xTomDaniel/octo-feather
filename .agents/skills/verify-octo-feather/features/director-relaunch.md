# director-relaunch

Criteria:

- [comms#acceptance-director-relaunch-busy](../../../../docs/specs/comms.spec.html#acceptance-director-relaunch-busy)
- [comms#acceptance-director-relaunch-own-scope](../../../../docs/specs/comms.spec.html#acceptance-director-relaunch-own-scope)
- [comms#acceptance-director-relaunch-same-session](../../../../docs/specs/comms.spec.html#acceptance-director-relaunch-same-session)
- [comms#acceptance-director-replace-outgoing](../../../../docs/specs/comms.spec.html#acceptance-director-replace-outgoing)
- [comms#acceptance-director-relaunch](../../../../docs/specs/comms.spec.html#acceptance-director-relaunch)
- [comms#acceptance-director-replace](../../../../docs/specs/comms.spec.html#acceptance-director-replace)
- [comms#director-relaunch](../../../../docs/specs/comms.spec.html#director-relaunch) (the relaunch and the replace themselves, the park refusal)

Drive criterion: `comms#acceptance-director-relaunch-busy`
Drive criterion: `comms#acceptance-director-relaunch-own-scope`
Drive criterion: `comms#acceptance-director-relaunch-same-session`
Drive criterion: `comms#acceptance-director-replace-outgoing`
Drive criterion: `comms#acceptance-director-relaunch`
Drive criterion: `comms#acceptance-director-replace`

## Sub-features

- `start` `octo-feather-start --director` starts a real Pi director; it writes director.toml naming its pane.
- `supervisor` a supervisor the director starts: `octo-feather-start --issue 7` (the launch `octo-feather-lane start` runs) typed into its Pi; Herdr names it `gh7`; director unchanged.
- `busy` the director mid-turn (its model never answers): `--director --relaunch --wait 20` refused, exit 75, naming the busy director's pane; the director still working, still named by Herdr and director.toml.
- `own-scope` a detached job typed into the director's Pi, with no HERDR_PANE_ID, runs the relaunch: refused, exit 64, naming the director's pane and its agent scope; director unchanged.
- `own-pane` the relaunch with HERDR_PANE_ID equal to the director's pane: refused, exit 64; director unchanged.
- `same-session` `--director --resume SESSION` beside the director on that session: refused, exit 73, naming the pane and the session; director unchanged.
- `bare` `--director` with workspace `director` present: exit 73, naming `--relaunch` and `--replace`; director unchanged.
- `park-refused` a background job in the director's scope: the relaunch stops with park's refusal, exit 75, no plain close; director unchanged.
- `relaunch` the job ended: `--relaunch --wait 120` prints the new `pane=`; `herdr agent get director` and director.toml name it, one Pi on the session, the new pane received one message naming the old pane, the session and the director log.
- `relaunch-report` `herdr-say --parent hello` typed into the supervisor's Pi, nothing run between: exit 0, the relaunched pane's Pi received `hello` once.
- `replace-busy` the relaunched director mid-turn: `--director --replace --wait 20` refused, exit 75, naming it; director unchanged.
- `replace-own-scope` the same detached job as `own-scope`, running `--replace`: refused, exit 64; director unchanged.
- `replace-own-pane` `--replace` with HERDR_PANE_ID the director's pane: refused, exit 64; director unchanged.
- `replace` `--replace --wait 120` prints a fresh `pane=` and the kickoff line; `herdr agent get director` and director.toml name it; the old pane found under `director-outgoing-<UTC>`, its Pi still on its session; the old Pi received one message that it is no longer the director, the fresh one one naming the old pane, its session and the director log.
- `replace-report` the supervisor's `herdr-say --parent hello` again: exit 0, the fresh director's Pi received `hello` once, the outgoing Pi's session still holds only the one from `relaunch-report`.

## How to get to it (user POV)

- `octo-feather-start --director --relaunch [--wait SECONDS] [--resume SESSION]`, `octo-feather-start --director --replace [--wait SECONDS]`; who runs it and from where: [comms#director-relaunch](../../../../docs/specs/comms.spec.html#director-relaunch); its steps, refusals and exits: `scripts/director_relaunch.py`, its docstring.

## Driving it with verify-octo-feather

Preconditions: `verify-octo-feather launch` printed `ready`; `verify-octo-feather doctor` exits 0; `herdr` and Pi on PATH, `~/.pi/agent/models.json`, a reachable systemd user manager (else the drive reports `UNREACHABLE director-relaunch` naming what is missing).

Run all cases: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive director-relaunch`. Evidence: `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/director-relaunch/`. About 5 minutes: the relaunch waits for 4 idle reads 15 s apart, twice, and the replace once more.

Real Herdr, Pi and systemd, all scratch: the drive starts its own Herdr server (`herdr --session verify-relaunch server`, XDG_CONFIG_HOME a short `/tmp/vof-*` dir of its own, linked as `xdg-config` in `$VERIFY_OCTO_FEATHER_RUN_DIR/scratch/director-relaunch/` and removed at the end: Herdr's socket path must fit 108 bytes; no call reaches the box's sessions), Pi with PI_CODING_AGENT_DIR in that scratch dir, its models.json the box's with every provider pointed at a local socket that accepts and never answers, and the state dir (XDG_STATE_HOME) there. Both background processes are started setsid with pid files in that dir's `pids/` and stopped through them, pass or fail, after its workspaces are closed. Steps inside the director are typed into its Pi as `!!bash FILE` (no model turn).

- Each refusal: observe its exit code and stderr, `.obs.director` (the pane `herdr agent get director` answers) still the first pane and `.obs.toml` unchanged.
- **Own scope** (`own-scope`): the case's command shows the step typed; `.obs.job` holds the job's cgroup (`octo-feather-agent-<pane>-<hex>.scope`), its refusal and `rc=64`.
- **Relaunch** (`relaunch`): exit 0, a new `pane=`; `.obs.director` and `.obs.toml` name it; `.obs.pi` is `1`; `.obs.received` the one `Relaunched (replacing pane ..., session ...)` message naming the director log, read from the session's Pi session file.
- **Replace** (`replace`): exit 0, a fresh `pane=`; `.obs.director` and `.obs.toml` name it; `.obs.outgoing` the old pane's new name and the pane `herdr agent get` answers for it; `.obs.pi` is `1` (the old Pi on its session); `.obs.bye` the old Pi's one `Replaced by a fresh director` message and `.obs.received` the fresh Pi's one `Fresh director (replacing pane ..., session ...)` message, each read from its Pi session file.
- **Supervisor report** (`relaunch-report`, `replace-report`): the case's stdout is the supervisor's `herdr-say --parent hello` log ending `rc=0`; `.obs.director` the new director; `.obs.hello` the count of user messages `hello` in the new director's Pi session file (`1`); `.obs.screen` its pane (`herdr pane read`), evidence only; `replace-report`'s `.obs.outgoing` that count in the outgoing director's session (`1`, the relaunch-report's).
- **Side effects.** Every cwd stays empty and the kit's `git status` unchanged.

## Gotchas

- The model socket never answers, so the `busy` turn lasts until the drive sends Escape; nothing reaches a provider.
- The park closes the director's only tab with its workspace, so the relaunched director lands in a new workspace labelled `director`.
- `--wait` under 45 s never succeeds (4 reads 15 s apart).
