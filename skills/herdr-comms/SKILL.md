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
(lane records, hand-off logs, `archive/`), `operator.toml`, and
`operator.handoffs.jsonl` (spec `#session-state`). Every spawned tab has the
kit's `skills/herdr-comms/assets` and `scripts` on `PATH`.

## Layout (docs/adr/0011)

- Workspace `director`, one tab `director`: the director (meta-operator),
  started by `octo-feather-start --director` (`just start`).
- One workspace per issue, `gh<n>`: tab `supervisor` is the supervisor,
  started by `octo-feather-start --issue <n> --cwd <worktree>`.
- In that workspace, one tab per worker: `worker-1`, `worker-2`, and the
  per-merge `corrector` and `code-reviewer`. One agent per tab, one pane per tab.

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
`pi-role agents/ROLE.md -p "<brief>"` in the worktree; its stdout is the report. Each agent
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

Any failure closes the tab, so a failed spawn never leaves an orphan.

`--resume SESSION` starts a parked agent with its old `--session-id`, so Pi
keeps its conversation. A supervisor resumes through `octo-feather-start --cwd
WORKTREE --name LANE --resume SESSION`, in a new lane workspace. `herdr-say`
does both for you; see below.

## Close an agent or a lane space

```
herdr-close TAB
herdr-close SPACE
```

The teardown step. An id with a colon (`w5:t2`) is a tab, one without (`w5`) is
a space. Closes it, then sends TERM to every process of the caller's session
whose environ carries `HERDR_TAB_ID=TAB` or `HERDR_WORKSPACE_ID=SPACE`, which
catches detached children that close alone leaves running. Run it from outside
what it closes: the spawner closes a tab, the operator closes a finished lane's
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
operator for a supervisor, the supervisor for a worker. An agent Herdr does not report
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

There is no acknowledgement step. `--wait --until` returns only on a state
change Herdr observed itself, which is stronger evidence than an agent
reporting on its own behalf. There is no deferred inbox and no drain: a message
is either delivered now or reported as not delivered.

Native Herdr refuses to prompt a blocked agent, so an open dialog is never
typed into.

A target Herdr does not find may be parked. The latest parked line naming it,
by pane or name, in any lane hand-off log in `$lanes` decides: a live agent
under the line's name gets the message; otherwise the agent is resumed (an
supervisor, the line named after its log, in a new lane space; a worker in the
caller's `$HERDR_WORKSPACE_ID`), gets the message, and `herdr-say` prints its
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

A `❯` line in a pane may be the CLI's own suggestion, not something a human
typed. Only a real message, or text the operator explicitly quoted, authorizes
submitting anything on someone's behalf.
