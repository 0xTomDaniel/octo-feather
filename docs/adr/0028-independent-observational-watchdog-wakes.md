# Independent observational watchdog wakes alongside Herdr handoffs

Event-only observation can miss a completed job's lost callback while the factory is idle. Use the existing maintained systemd scheduler for the narrow observational watchdog wake exception defined by [watchdog acceptance-wake-only](../specs/watchdog.spec.html#acceptance-wake-only), rather than making the director responsible for delivering its own backstop.

This supersedes ADR 0003 only on its blanket scheduler exclusion. Herdr remains the agent handoff mechanism; the rejection of a workflow engine and tracker-driven state machine is unchanged. A director sweep launcher is not part of this decision.

## Considered options

- Director-relayed events alone: cannot provide coverage when the director is idle or awaiting a lost callback.
- A custom polling daemon or workflow engine: adds coordination machinery where the maintained scheduler already supplies independent wakes.
