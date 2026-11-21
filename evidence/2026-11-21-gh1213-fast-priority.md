# gh1213: a fast-tier run at the lowest processor and disk priority

Change: tests/gate/heavy_slot.py sets each process running a fast-tier run's items (quality #recipes-static-first) to nice 19 and ionice(1)'s idle class, every thread, before its first item; a full run keeps its priority.

Smoke: .agents/skills/verify-octo-feather/features/run-slots.md (its pointer to the rule; `just fast` run live in the implementer pane of lane gh1186, no model run)

## The smoke

`just fast` at the change (worst case, 321 items, uncommitted edits): `heavy slot: not needed: fast tier, 3 workers (cap 3), at the lowest priority (nice 19, disk idle)`, 321 passed in 343.8 s. During it, `ps` showed its three xdist workers at NI 19 and `ionice -p` on each thread of one `idle`; the controller at NI 0 (it runs no item).
