# The factory runs on any machine that meets its host requirements

The factory (agents, Herdr, toolchains) runs on any machine its user chooses that meets the host requirements of remote spec `#host-vm`, the owner's laptop included. A dedicated machine is recommended, never required: agents run unattended with broad file and process access, up to 10 Pi agents at once. exe.dev is needed only when its review proxy (HTTPS proxy, login and Private sharing for review hosting) and its model proxy are used.

The 10-Pi limit counts real model-calling Pi only (role sessions, nested headless model runs); a stub `pi` and the real pi pointed at a fake loopback provider do not count (owner ruling, 2026-11-03, issue #504 item 4).

History: the first deployment chose a dedicated remote box. Tom, 2026-10-18: "we're not setting any of this up on this box. we'll make a dedicated remote". The owner corrected that choice into this decision on 2026-10-30, at the #480 merge ask (issue #422): (a) "no the factory can run anywhere, it's just that we decided to use a remote box for this exact session"; (b) "those need to be changed too. this factory can run anywhere the user wants it to run"; (c) "it preferrably has it's own server, but doesn't have to". Evidence: a Debian second box, not an exe.dev VM, ran the factory with the full gate green (issue #422, comment 2: "second box (Debian, not an exe.dev VM; owner approved)"; comment 4).

## Considered options

- Require a dedicated machine. Rejected by ruling (c).
- Require an exe.dev VM. Rejected by rulings (a) and (b), and by the Debian box.
