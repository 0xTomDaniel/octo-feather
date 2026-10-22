# The kit runs on a dedicated remote box

Agents, Herdr and toolchains run on one exe.dev VM, `<vm>.exe.xyz` (4 vCPU / 8 GB), never on the owner's Mac, whose clone is for editing docs only. Tom: "we're not setting any of this up on this box. we'll make a dedicated remote", 2026-10-18.

## Considered options

- A shared home server. Rejected: third parties hold admin access.
- The assistant's own host. Rejected: it runs the owner's assistant.
