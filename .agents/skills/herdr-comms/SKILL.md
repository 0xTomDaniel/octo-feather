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
- One workspace per issue, `gh<n>`: tab `supervisor` is the supervisor,
  started by `octo-feather-start --issue <n> --cwd <worktree>`.
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
`OCTO_FEATHER_SESSION_ID` into it.

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

Any failure closes the tab, so a failed spawn never leaves an orphan.

`--resume SESSION` starts a parked agent with its old `--session-id`, so Pi
keeps its conversation. A supervisor resumes through `octo-feather-start --cwd
WORKTREE --name LANE --resume SESSION`: in a new tab of workspace LANE when it
still exists, else in a new lane workspace (without `--resume`, an existing
workspace exits 73). `herdr-say`
does both for you; see below.

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
Closes it, then sends TERM to every process of the caller's session
whose environ carries `HERDR_TAB_ID=TAB` or `HERDR_WORKSPACE_ID=SPACE`, which
catches detached children that close alone leaves running. Run it from outside
what it closes: the spawner closes a tab, the director closes a finished lane's
own space, or only its supervisor tab when the lane started in a shared space.
Prints `tab= tab_close_rc= killed=` or `space= space_close_rc= killed=` and
exits with the close status.

## Park an idle agent

```
herdr-close --park PANE >>"$lanes/<lane>.handoffs.jsonl"
```

`$lanes` is `$(octo-feather-state)/lanes`. Reads the Pi session id and role
`herdr-spawn` exported into PANE's tab, closes its tab, or its whole space when
that tab is the space's only one (a supervisor in its own space), and prints
one parked line (`at kind pane name role cwd session`) on stdout, even when the
close fails; the close report goes to stderr. The parker appends the line: the
director for a supervisor, the supervisor for a worker. An agent Herdr does not report
idle is refused with exit 75, one not spawned by `herdr-spawn` with 65; nothing
is closed.

## Send a message

```
herdr-say TARGET MESSAGE
```

Wraps `herdr agent prompt TARGET TEXT --wait --until working --until idle`.

Exit codes are the contract:

| code | meaning |
|---|---|
| 0 | delivered, and Herdr observed the agent change state |
| 75 | target is blocked on interactive input; retry when it frees |
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

A target Herdr does not find may be parked. The latest parked line naming it,
by pane or name, in any lane hand-off log in `$lanes` decides: a live agent
under the line's name gets the message; otherwise the agent is resumed (a
supervisor, the line named after its log, in its lane space when that still
exists, else a new one; a worker in the caller's `$HERDR_WORKSPACE_ID`), gets the
message prefixed `Resumed from park as pane=PANE. `, and `herdr-say` prints its
new `pane=`. `herdr-say --parked TARGET` prints that line, or exits 1.
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
