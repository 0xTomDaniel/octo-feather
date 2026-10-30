# The factory runs on any machine that meets its host requirements

The factory (agents, Herdr, toolchains) runs on any machine that meets its host requirements: remote spec `#host-vm`. exe.dev is needed only when you use its review proxy (HTTPS proxy, login and Private sharing for review hosting) and its model proxy. The owner, 2026-10-30, at the #480 merge ask (issue #422): "no the factory can run anywhere, it's just that we decided to use a remote box for this exact session". Evidence: a Debian second box, not an exe.dev VM, ran the factory with the full gate green (issue #422, comment 2: "second box (Debian, not an exe.dev VM; owner approved)"; comment 4).

This deployment chose a dedicated remote exe.dev box; the owner's Mac clone is for editing docs only. Tom, 2026-10-18: "we're not setting any of this up on this box. we'll make a dedicated remote".

## Considered options

- Require a dedicated remote box for every deployment. Rejected by the owner's 2026-10-30 ruling: the remote box is this deployment's choice, not the kit's.
- For this deployment, a shared home server. Rejected: third parties hold admin access.
- For this deployment, exo. Rejected: it is Exo's own host.
