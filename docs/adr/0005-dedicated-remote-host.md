# The kit runs on a dedicated remote box

Agents, Herdr and toolchains run on a dedicated remote box, never on the owner's Mac, whose clone is for editing docs only. Tom: "we're not setting any of this up on this box. we'll make a dedicated remote", 2026-10-18. The exe.dev VM `<vm>.exe.xyz` (Personal plan, 4 vCPU / 8 GB) is the reference box, and exe.dev is needed only for review hosting (its HTTPS proxy, login and Private sharing) and the model proxy; the rest runs on any dedicated Linux box that meets remote spec `#host-vm`. Corrected in place, 2026-10-30, by the owner's approval of a Debian second box (issue #422, comment 2: "second box (Debian, not an exe.dev VM; owner approved)"), where the full gate ran green (comment 4).

## Considered options

- A shared home server. Rejected: third parties hold admin access.
- exo. Rejected: it is Exo's own host.
- Only an exe.dev VM. Rejected: only review hosting and the model proxy need exe.dev; a Debian box ran the factory with a green gate (issue #422).
