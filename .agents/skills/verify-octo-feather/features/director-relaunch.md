# director-relaunch

Criteria:

- [comms#acceptance-director-relaunch-busy](../../../../docs/specs/comms.spec.html#acceptance-director-relaunch-busy)
- [comms#acceptance-director-relaunch-own-scope](../../../../docs/specs/comms.spec.html#acceptance-director-relaunch-own-scope)
- [comms#acceptance-director-relaunch-same-session](../../../../docs/specs/comms.spec.html#acceptance-director-relaunch-same-session)
- [comms#director-relaunch](../../../../docs/specs/comms.spec.html#director-relaunch) (the relaunch itself, the park refusal)

Drive criterion: `comms#acceptance-director-relaunch-busy`
Drive criterion: `comms#acceptance-director-relaunch-own-scope`
Drive criterion: `comms#acceptance-director-relaunch-same-session`

## Sub-features

- `start` `octo-feather-start --director` starts a real Pi director; it writes director.toml naming its pane.
- `busy` the director mid-turn (its model never answers): `--director --relaunch --wait 20` refused, exit 75, naming the busy director's pane; the director still working, still named by Herdr and director.toml.
- `own-scope` a detached job typed into the director's Pi, with no HERDR_PANE_ID, runs the relaunch: refused, exit 64, naming the director's pane and its agent scope; director unchanged.
- `own-pane` the relaunch with HERDR_PANE_ID equal to the director's pane: refused, exit 64; director unchanged.
- `same-session` `--director --resume SESSION` beside the director on that session: refused, exit 73, naming the pane and the session; director unchanged.
- `bare` `--director` with workspace `director` present: exit 73, naming `--relaunch` and `--replace`; director unchanged.
- `park-refused` a background job in the director's scope: the relaunch stops with park's refusal, exit 75, no plain close; director unchanged.
- `relaunch` the job ended: `--relaunch --wait 120` prints the new `pane=`; `herdr agent get director` and director.toml name it, one Pi on the session, the new pane received one message naming the old pane, the session and the director log.

## How to get to it (user POV)

- The owner, from a shell outside the director's pane (or an agent, in the background from its own pane), runs `octo-feather-start --director --relaunch [--wait SECONDS] [--resume SESSION]`; its steps, refusals and exits: `scripts/director_relaunch.py`, its docstring.

## Driving it with verify-octo-feather

Preconditions: `verify-octo-feather launch` printed `ready`; `verify-octo-feather doctor` exits 0; `herdr` and Pi on PATH, `~/.pi/agent/models.json`, a reachable systemd user manager (else the drive reports `UNREACHABLE director-relaunch` naming what is missing).

Run all cases: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive director-relaunch`. Evidence: `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/director-relaunch/`. About 3 minutes: the relaunch waits for 4 idle reads 15 s apart, twice.

Real Herdr, Pi and systemd, all scratch: the drive starts its own Herdr server (`herdr --session verify-relaunch server`, XDG_CONFIG_HOME a short `/tmp/vof-*` dir of its own, linked as `xdg-config` in `$VERIFY_OCTO_FEATHER_RUN_DIR/scratch/director-relaunch/` and removed at the end: Herdr's socket path must fit 108 bytes; no call reaches the box's sessions), Pi with PI_CODING_AGENT_DIR in that scratch dir, its models.json the box's with every provider pointed at a local socket that accepts and never answers, and the state dir (XDG_STATE_HOME) there. Both background processes are started setsid with pid files in that dir's `pids/` and stopped through them, pass or fail, after its workspaces are closed. Steps inside the director are typed into its Pi as `!!bash FILE` (no model turn).

- Each refusal: observe its exit code and stderr, `.obs.director` (the pane `herdr agent get director` answers) still the first pane and `.obs.toml` unchanged.
- **Own scope** (`own-scope`): the case's command shows the step typed; `.obs.job` holds the job's cgroup (`octo-feather-agent-<pane>-<hex>.scope`), its refusal and `rc=64`.
- **Relaunch** (`relaunch`): exit 0, a new `pane=`; `.obs.director` and `.obs.toml` name it; `.obs.pi` is `1`; `.obs.received` the one `Relaunched (replacing pane ..., session ...)` message naming the director log, read from the session's Pi session file.
- **Side effects.** Every cwd stays empty and the kit's `git status` unchanged.

## Gotchas

- The model socket never answers, so the `busy` turn lasts until the drive sends Escape; nothing reaches a provider.
- The park closes the director's only tab with its workspace, so the relaunched director lands in a new workspace labelled `director`.
- `--wait` under 45 s never succeeds (4 reads 15 s apart).
