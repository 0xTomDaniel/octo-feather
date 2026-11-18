---
name: herdr-comms
description: Spawn Herdr agents and send them messages, over native Herdr.
---

# herdr-comms

Thin wrappers over native Herdr, ported from octo-lite
(`varelaseb/octo-lite@cc6fa4e`, Apache-2.0) and cut to Pi only. Herdr itself
owns the transport; these exist only for the failure modes it leaves to the
caller, and for parking an idle Pi agent so it holds no memory while it waits.

Every wrapper acts only in the caller's Herdr session,
`${HERDR_SESSION:-default}`: pane, tab, and space ids repeat across sessions.
`octo-feather-state` prints the caller's session state directory, holding `lanes/`
(lane records, hand-off logs, `archive/`), `director.toml`, and
`director.handoffs.jsonl` (spec `#session-state`). Every spawned tab has the
kit's `.agents/skills/herdr-comms/assets` and `scripts` on `PATH`.

## Layout (docs/adr/0011)

- Workspace `director`, one tab `director`: the director,
  started by `octo-feather-start --director` (`just start`).
- One workspace per lane, named by its lane key, what the tracker skill's
  `lane-key` prints (`gh12` for ticket 12, `eng-123` for ticket ENG-123): tab `supervisor` is the supervisor, started by
  `octo-feather-start --issue <ticket> --cwd <worktree>`, the ticket as the
  tracker writes it (`12`, `ENG-123`).
- In that workspace, one tab per worker: `worker-1`, `worker-2`, and the
  per-merge `code-reviewer`; a correction lane has a `corrector` tab instead of
  workers. One agent per tab, one pane per tab.

## Spawn an agent

```
herdr-spawn --workspace ID --name NAME --label LABEL --cwd DIR --role ROLE [-- pi]
```

A lane worker spawns into its lane workspace, `--workspace "$HERDR_WORKSPACE_ID"`,
named `<role>-<ticket>` lowercase (`implementer-gh64`), labelled `worker-<k>`
or the role name. A pane never moves between spaces: Herdr rewrites its ids.

Spawn bare, then send the brief with `herdr-say`. Nothing follows the runtime:
with an inline prompt, `herdr agent start` times out waiting for readiness.

One tab, one pane, one agent, at an explicit worktree. Prints:

```
name= role= tab= pane= cwd= contract= provider_session_id=
```

`--role` is not just a label: `herdr-spawn` launches Pi through
`scripts/pi-role agents/ROLE.md` (docs/adr/0016): the role's model, thinking,
tool allowlist and listed skills (`--skill DIR`), and its body appended to Pi's
system prompt. Pi loads the target's `AGENTS.md` from `--cwd`. Nothing is
installed into the user's Pi profile. A one-shot run with no pane is
`pi-role agents/ROLE.md -p "<brief>"` in the worktree; its stdout is the report. It has
no route to any pane: pi-role drops `OCTO_FEATHER_PARENT` and `HERDR_PANE_ID`, `HERDR_TAB_ID`,
`HERDR_WORKSPACE_ID` for it, so it cannot `herdr-say`. Each agent
gets a fresh `--session-id`, reported as `provider_session_id=`.

`--operating-model FILE` is optional. It is appended to Pi's system prompt
ahead of the contract. It defaults to `$OCTO_FEATHER_OPERATING_MODEL`, and the
spawn exports that path into the new tab, so every child inherits the model
without passing the flag.

A new tab gets the Herdr server's environment, so the spawn always exports the
caller's `HOME`, the kit `PATH`, `OCTO_FEATHER_ROLE` and
`OCTO_FEATHER_SESSION_ID` into it, and `LINEAR_API_KEY` when the caller has
it set (unset in the caller, unset in the tab). The key comes only from the
environment that starts the factory: never write it into a file, brief,
message, lane record or log.

Each agent runs in its own systemd user scope (#1000): before `agent start`,
the spawn adopts the new pane's shell (`herdr pane process-info`, `shell_pid`)
into `octo-feather-agent-PANE-N.scope` through systemd's D-Bus
`StartTransientUnit` (`busctl --user`; `systemd-run` cannot adopt a running
pid), so Pi and all it starts, detached or not, are that scope's members, and
`herdr-close` ends them from it. On Linux with no reachable systemd user
manager the spawn refuses: exit 69, tab closed, busctl's own error and the need
named (on a server: `loginctl enable-linger $USER`, `XDG_RUNTIME_DIR=/run/user/$(id -u)`).
macOS has no systemd: agents launch unscoped there, and `herdr-close` sweeps
nothing of theirs (the stated limit).

It wraps `herdr tab create` and `herdr agent start`, and handles three things
those leave to the caller:

- A freshly created pane is not yet at a shell prompt. Herdr reports
  `agent_pane_busy`; only that code is retried, with backoff.
- An agent that opens a trust dialog makes `agent start` report
  `agent_not_ready`. That is a started agent waiting on a keystroke, not a
  failure.
- The dialog is answered at the **pane**, never blindly. The highlighted row
  may be the refusal, where a bare Enter kills the agent being spawned. The
  selection is moved onto the trust option and verified before confirming.
- Pi's "Trust project folder?" dialog is never answered: `pi-role` launches
  with `--approve`, so it should not open. If it does, no key is sent and the
  spawn fails closed (exit 69, tab closed, pane text on stderr).
- A cleared dialog is not readiness: a booting agent reads `unknown`, and a
  prompt sent then is typed but never submitted (`agent_prompt_stalled`, #585).
  Nor is `idle` alone: Herdr reads Pi's screen only, and reads a booting Pi
  `idle` (its fallback) before Pi takes input (#871). So the spawn loads
  Herdr's own Pi integration (`herdr integration install pi`, written to
  `~/.cache/octo-feather/herdr-pi/`, never the user's Pi profile), which
  reports from inside Pi once its TUI runs. The spawn returns only once
  `herdr agent get` shows that report (`agent_session`, source `herdr:pi`),
  `herdr agent wait PANE --until idle` matches, and `herdr agent get` finds the
  agent by name and by pane, so a `herdr-say` right after it is delivered;
  `herdr-say`'s resume and `octo-feather-start` go through it. A failed install
  exits 69 before any tab; no report or not idle within
  `HERDR_SPAWN_READY_TIMEOUT` seconds (default 120, one bound for the whole
  wait; `assets/herdr_ready.py` waits): exit 69, tab closed, the cause named.

Any failure closes the tab, so a failed spawn never leaves an orphan.

`--resume SESSION` starts a parked agent with its old `--session-id`, so Pi
keeps its conversation. A supervisor resumes through `octo-feather-start --cwd
WORKTREE --name LANE --resume SESSION`: in a new tab of workspace LANE when it
still exists, else in a new lane workspace (without `--resume`, an existing
workspace exits 73). `herdr-say`
does both for you; see below.

### Start the shaper for the owner

The director's spawn for an owner's shaping ask (roles spec `#role-shaper`):
in its own workspace, at the target repo, bare.

```
herdr-spawn --role shaper --workspace "$HERDR_WORKSPACE_ID" --name shaper --label shaper --cwd <target repo>
```

Send it no brief; tell the owner its `tab=`, where the owner shapes with it.

## Close an agent or a lane space

```
herdr-close TAB
herdr-close SPACE
herdr-close PANE
```

The teardown step. An id with a colon (`w5:t2`) is a tab, one without (`w5`) is
a space. A pane id (`w5:p3`) is mapped to its tab through `herdr agent get`
(as `--park` does) and closed as that tab; a pane with no Herdr agent cannot be
mapped and fails with exit 65 naming the `TAB|SPACE|PANE` form, nothing closed.
Before closing, it finds each closed pane's agent scope from Herdr's own
handles only (`herdr pane list --workspace`, each pane's `shell_pid` from
`herdr pane process-info`, that pid's `/proc/PID/cgroup`); after the close it
stops each one (`systemctl --user stop`: TERM, KILL 10 s on), which ends the
detached children close alone leaves running, also when the agent's Pi already
exited. It reads no other process: one elsewhere tagged with the closed tab's
`HERDR_TAB_ID` is untouched. A pane outside any agent scope (an agent spawned
before scopes, a hand-started director, macOS) is unowned: closed, nothing
swept, named in the report. A Herdr answer that fails or breaks the shape
Herdr states for it stops the close before anything is closed (Herdr's exit, or
76 for a malformed one, the field named; `assets/herdr_scope.py`). Run it from outside
what it closes: the spawner closes a tab, the director closes a finished lane's
own space, or only its supervisor tab when the lane started in a shared space.
Prints `tab= tab_close_rc= killed=` or `space= space_close_rc= killed=`
(`killed=` the scopes' members when stopped), plus `unowned=PANE[,PANE...]`
when any, and exits with the close status.

## Park an idle agent

```
herdr-close --park PANE >>"$lanes/<lane>.handoffs.jsonl"
herdr-close --park PANE >>"$(octo-feather-state)/director.handoffs.jsonl"   # the director's own general worker
```

`$lanes` is `$(octo-feather-state)/lanes`. Reads the Pi session id and role
`herdr-spawn` exported into PANE's tab, closes its tab, or its whole space when
that tab is the space's only one (a supervisor in its own space), and prints
one parked line (`at kind pane name role cwd session label parent`) on stdout, even when the
close fails; the close report goes to stderr. The parker appends the line to the
log comms spec `#roles-park` names (the two commands above). An agent Herdr does not report
idle is refused with exit 75, one not spawned by `herdr-spawn` with 65; nothing
is closed.

## Replace a worker that ended without reporting

A worker whose pane holds no finished result (comms spec `#roles-goal`):

```
herdr-close PANE                       # when herdr agent get PANE still finds it
octo-feather-handoff attempt --ended-unreported "$lanes/<lane>.handoffs.jsonl" PANE \
  --partial "<commit, branch, what it left>" --recovery "<what replaces it>" [--commit C] \
  >>"$lanes/<lane>.handoffs.jsonl"
herdr-spawn ...                        # the replacement, a fresh session
```

The attempt reads the old session from the spawn line `herdr-spawn` recorded
(`herdr-spawn --help`); its refusals: `octo-feather-handoff --help`. The
line's fields: comms spec `#handoff-fields`.

## Send a message

```
herdr-say [--timeout SECONDS] TARGET MESSAGE
```

Wraps `herdr agent prompt TARGET TEXT --wait --until working --until idle
--timeout MS`. A send never hangs or fails silently (#666): the wait is bounded
by `--timeout` (default 900 s); a prompt Herdr reports stalled
(`agent_prompt_stalled`: typed, never seen to land) or still unconfirmed at the
bound (a busy target that stays `working`) exits 1 or 124, Herdr's error kept,
the last line naming the target's pane and its state. Either one while the
target's pane shows the message queued during compaction is never resent: it
waits, within the bound, and exits 0 once Pi took it, else its 1 or 124 says
queued, not resent (comms spec `#delivery-recovery`).

Exit codes are the contract:

| code | meaning |
|---|---|
| 0 | delivered, and Herdr observed the agent change state |
| 75 | target is blocked on interactive input; retry when it frees |
| 124 | not confirmed within `--timeout` (still not seen to start or finish a turn); named |
| 68 | comms spec `#say-parent-gone` |
| 69 | the up-chain guard's `herdr agent get TARGET` lookup failed; named, nothing sent (one answering `agent_not_found` is an answer: 77, the lookup named) |
| other | anything else |

Never hold your turn in a shell sleep or blocking wait over ~60 s. While one
runs, every message sent to you queues unread as "Steering" (issue #29, block 3
smoke). After a brief, end your turn: the result arrives as a new message in
your pane. Run any long job (`just qc`, a CI watch, a worker) in the background
or in a pane, end your turn, and resume on its completion message or a
`herdr-say` wake. A supervisor's or the director's background job wakes it
itself (the up-chain guard refuses a worker's message to its own pane):

```
(just qc ... >/tmp/qc.log 2>&1; herdr-say "$HERDR_PANE_ID" "qc done rc=$? log /tmp/qc.log") >/dev/null 2>&1 &
```

Or poll in short bounded steps, 60 s at most each:
`herdr pane wait-output PANE --match TEXT --timeout 60000`. A finished agent's
`agent_status` is `done`, not `idle`.

There is no acknowledgement step. `--wait --until` returns only on a state
change Herdr observed itself, which is stronger evidence than an agent
reporting on its own behalf. There is no deferred inbox and no drain: a message
is either delivered now or reported as not delivered.

Native Herdr refuses to prompt a blocked agent, so an open dialog is never
typed into.

A target Herdr does not find may be parked (comms spec `#roles-park`): which
parked line counts, `octo-feather-handoff --help` (parked); where the agent
resumes, `herdr-say`'s header. A resumed agent gets the message prefixed
`Resumed from park as pane=PANE. `, and `herdr-say` prints its new `pane=`.
`herdr-say --parked TARGET` prints that line, or exits 1.
`herdr-wake check` counts a parked supervisor as present, so a spec review hand-off
resumes it.

The review service may run in another Herdr session, so register a review row
with `--owner "${HERDR_SESSION:-default}/$HERDR_PANE_ID"`: `herdr-wake` checks
and wakes a `SESSION/PANE` supervisor in that session, a bare pane in its caller's.

## Reading a pane

`herdr pane read` returns raw text. `herdr agent get` returns JSON. Use the
agent view for state and the pane view only for what is literally on screen.

## Never submit text you did not write

A `❯` line in a pane may be the CLI's own suggestion, not something an owner
typed. Only a real message, or text the owner explicitly quoted, authorizes
submitting anything on someone's behalf.
