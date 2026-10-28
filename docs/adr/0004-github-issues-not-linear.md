# The tracker is chosen per target: GitHub Issues or Linear

Each target repository names its tracker in `.octo-feather.toml`, `tracker = "github"` or `tracker = "linear"`, `github` when unset. Work items are tickets in that tracker: each lane has one parent ticket, and its tickets are sub-issues of it (ADR 0019). Pull requests, review and merge stay on GitHub for every target. Decided by the owner, 2026-10-22, issue #82: the kit works with Linear directly, so it can run on a Linear-first repository that forbids GitHub issues for its work. This corrects in place the owner's choice of 2026-10-18, GitHub Issues only, to keep things simple.

Tracker work lives only in packaged skills, never in the kit's general scripts or role prose: `github-pr` (branches, pull requests, merge; every role that needs GitHub loads it, whatever the tracker), and one tracker skill per tracker, `github-issues` and `linear`, each implementing the same fixed script names (spec `skills#tracker-scripts`). A role's `skills:` line names `{tracker}`, and `pi-role` loads the target's tracker skill in its place, so an agent never holds a second tracker's instructions. Linear is driven through the `linear` CLI (schpet/linear-cli, ISC), as octo-lite does (varelaseb/octo-lite@f735731): the `linear` tracker skill's scripts are thin wrappers over it, and its own agent skill, `linear-cli`, is vendored but loaded by no role: the `linear` skill sends agents to its references by path for any read the scripts do not cover. Its key lives only in the environment (spec `remote#host-tracker-key`).

## Considered options

- GitHub Issues only (the 2026-10-18 choice). Rejected: the kit cannot run on a Linear-first repository.
- Mirror Linear tickets into GitHub issues. Rejected: a Linear-first repository forbids creating or editing GitHub issues for its work, and two records drift.
- Tracker branches inside the general scripts (`if linear ... else gh ...`). Rejected: every script would carry both trackers, and a third tracker would touch them all; a skill per tracker behind fixed script names keeps each self-contained.
- Linear through an MCP server. Rejected: a domain capability is a CLI plus a skill, never a tool (ADR 0016); the `linear` CLI is what octo-lite proved.
