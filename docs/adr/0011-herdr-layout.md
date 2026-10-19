# Herdr layout: a director workspace, then one workspace per issue

Herdr holds one workspace `director` with a single tab for the director. Every issue gets its own workspace named after it (`gh<issue>`): the first tab, `lane`, is the lane owner (octo-lite calls it orchestrator, Exomachina production supervisor), and each worker and the integrator get their own tab in that workspace (`worker-1`, `worker-2`, `integrator`). One agent per tab, one pane per tab: a split pane is never needed because nobody watches two agents at once, and a second pane only makes `herdr-say` targeting ambiguous. Short fresh-context jobs (code reviewer, `correct`, Jev judge) do not get tabs; they run headless as children of the lane owner, if the pi-subagents spike passes, otherwise in their own tab. Layout by Tom, pane rule by Exo, 2026-10-18.

Renamed by ADR 0014: the lane owner (orchestrator) is now the supervisor, and its tab `lane` is now `supervisor`.
