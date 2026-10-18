# A director that never edits code, over one lane owner per issue

Lane owner is octo-lite's orchestrator and Exomachina's production supervisor.

One director (octo-lite's meta-operator) owns the program: it files issues, starts one lane owner (orchestrator) per issue, handles escalations and asks the human only at gates; it writes no repo files. Each lane owner spawns its own workers, integrator and reviewer. Tom: "we MUST have the director... stands in for the human. I expect this take home to have several issues ongoing in parallel", 2026-10-18.

Every issue gets a lane owner, even when it is the only one running: a fixed rule beats a judgment the director can get wrong, at the cost of one extra context per issue. Workers run `just check` and must be green before they report, but never review or accept their own work; the lane owner spawns a fresh code-reviewer for every merge, and Matt's `implement` step that calls `code-review` in the worker's own context is patched out. Approved by Tom, 2026-10-18.
