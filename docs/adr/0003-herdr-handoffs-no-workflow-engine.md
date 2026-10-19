# Agents hand off through Herdr, with no workflow engine

The director, lane owners and workers are Pi sessions in Herdr panes that message each other through `herdr-comms` (`herdr-spawn`, `herdr-say`, `herdr-close`, `herdr-wake`); there is no daemon, scheduler or tracker-driven state machine. Rejected for now: scaling-octo-engine's Symphony plus Linear control plane (too many moving parts for one person) and A2A (deferred until after the Martell take-home). Decided by Tom, 2026-10-18.

Renamed by ADR 0014: lane owner is now supervisor.
