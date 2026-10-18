# Matt's workflow skills are model-invoked

mattpocock/skills marks implement, implement-spec, to-spec, to-tickets, grill-with-docs, improve-codebase-architecture and handoff `disable-model-invocation: true`, so only a human slash command can start them. In octo-feather the agents run the workflow, so each of those gets a one-line patch removing that flag, recorded in `skills.lock`. Pollution is contained because every role loads only the skills its role file lists. triage stays human-invoked. Decided by Tom, 2026-10-18.
