# gh607: the shaper offers a repair of brownfield specs and ADRs

Change: `agents/shaper.md` lists Spec Chat's `repair-specs` under `externalSkills` and its step 3, Repair, names when it is read: a spec or ADR the shaper reads misses Spec Chat's shaping contract; the shaper offers the owner the repair before writing the change's spec and runs it only on the owner's yes (roles `#acceptance-shaper-repair`, owner decision #557 item 3).

Smoke: agents/shaper.md, suite `shaper-repair` case `repair-moment-bye`: run 20261106T051355Z-f4740e, baseline 745795c FAIL (no read in 18 calls, ended on its own), head 4d57d2f PASS (repair-specs read at call 9).
Smoke: .agents/skills/verify-octo-feather/features/shape.md, `verify-octo-feather drive shape` at de2a895 PASS: offered = agents/shaper.md skills from the kit, spec-chat-shape, spec-chat-review, repair-specs from the target, none from home; evidence record 20261106T015640Z-ff670531.

Removed: nothing deleted; the incident: carry/gh557 findings, `repair-specs` read twice ever (exosurface shaping chat 10-19, director 10-19), orphaned: no role listed it.

## Runs

Fixtures: `shape-brownfield` (new: change-named spec, status and history sections, ticket links, criteria not Given/When/Then, an ADR with rules and a decision log) and `shape-mini` (conforming), each with a `repair-specs` stand-in. Read index: the tool call at which `repair-specs/SKILL.md` was loaded; INC: a run stopped at the cap or timeout, never a pass.

### skill-triggers (cap 12): run 20261106T044940Z-3fa81d, baseline 745795c beside head de2a895, 3 runs each

| case | split | baseline | head (read at) |
| --- | --- | --- | --- |
| shaper-repair-multi-name | train | 0/3 (1 INC) | 3/3 (9, 10, 8) |
| shaper-repair-lang | held-out | 0/3 (3 INC) | 1/3 (11; 2 INC, no read) |
| shaper-repair-near-clean-repo | train | 3/3 (2 INC) | 3/3 (3 INC) |
| shaper-repair-near-clean-version | held-out | 3/3 (1 INC) | 3/3 (1 INC) |
| shaper-repair-near-question-exit | train | 3/3 | 3/3 |
| shaper-repair-near-question-json | held-out | 3/3 | 3/3 |

Train 3/3, held-out 2/3. The 12-call cap stops the shaper before its Repair decision: it reads its step skills (5 calls) and then the repo first. Director's ruling (option d): a suite of its own with a measured bound and new cases; these cases stay as they are.

### shaper-repair (cap 20, derivation in its suite.json): run 20261106T051606Z-a12ae8, baseline 745795c beside head 4d57d2f, 3 runs each

| case | split | baseline | head (read at) |
| --- | --- | --- | --- |
| repair-moment-bye | train | 0/3 (1 INC) | 3/3 (10, 9, 9) |
| repair-moment-verbose | train | 0/3 | 3/3 (9, 8, 17) |
| repair-moment-near-clean-from | train | 3/3 | 3/3 |
| repair-moment-near-question-owner | train | 3/3 | 3/3 |
| repair-moment-emoji | held-out | 0/3 (1 INC) | 3/3 (10, 10, 10) |
| repair-moment-inner-space | held-out | 0/3 | 2/3 (9, 9; run 2 FAIL) |
| repair-moment-near-clean-formal | held-out | 3/3 | 3/3 |
| repair-moment-near-question-adr | held-out | 3/3 | 3/3 |
| repair-moment-near-typo | held-out | 3/3 | 3/3 |

Train 4/4, held-out 4/5. No head run hit the cap or timeout; no should-not run read repair-specs (30 head runs). Finding: inner-space run 2 read every spec and the ADR in one command, then wrote and committed the change's spec with no repair read and no offer, 14 calls, ended on its own: a real miss, not the bound. Held-out cases not reworded. Near-miss cases pass on both kits by design (non-discriminating). verbose run 3 read at call 17 of 20: the margin as derived.
