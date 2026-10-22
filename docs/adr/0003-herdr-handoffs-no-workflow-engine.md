# Agents hand off through Herdr, with no workflow engine

The director, supervisors and workers are Pi sessions in Herdr panes that message each other through `herdr-comms` (`herdr-spawn`, `herdr-say`, `herdr-close`, `herdr-wake`); there is no daemon, scheduler or tracker-driven state machine. Decided by Tom, 2026-10-18.

## Considered options

- scaling-octo-engine's Symphony plus Linear control plane. Rejected: too many moving parts for one person.
- A2A between agents. Deferred until after the take-home (docs/future.md).
