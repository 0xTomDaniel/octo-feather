# The role under the director is the supervisor

The agent that owns one work item under the director is called the **supervisor**: the role file is `agents/supervisor.md`, its Herdr tab is `supervisor` in workspace `gh<n>`, and `just supervise N` starts it. The supervisor owns its work item until it merges, and directs workers without doing their work. The word is a factory term that is not tied to software, because these factories will eventually do any kind of work. "Lane" stays as the name of the running state of one work item (record, hand-off log, workspace, integration branch), defined in GLOSSARY.md. Decided by Tom, 2026-10-18.

## Considered options

- **Lane owner**: describes plumbing (a lane is state, not a job) and reads as a component, not an accountable role.
- **Orchestrator** (octo-lite's name): describes plumbing too, and invites the agent to do the work itself, which ADR 0007 forbids.
- **Production supervisor** (Exomachina) and **issue supervisor**: tied to software production and to GitHub's word for a work item.

## Consequences

- Clash: in LangGraph, "supervisor" means a central router agent that hands each turn to a sub-agent. Here a supervisor is accountable for one work item and runs its workers through Herdr. Read GLOSSARY.md, not LangGraph, for the meaning.
- `spec/` (octo-lite's spec, to be rewritten) still says orchestrator and lane owner. The role files cite its anchors (`#lane-record`, `#transport-*`), so its terms stay until that rewrite.
- External protocol names stay: Spec Chat's `--owner` flag and `OWNER` argument, and spec anchors such as `#session-wake-owner`.
