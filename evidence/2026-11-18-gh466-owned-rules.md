# gh466 / #640: a role step owns its role duty

Smoke: .agents/skills/code-review/ .skillfile/patches/skills/code-review/SKILL.md.patch
Removed: nothing deleted; incident: lane gh593 blocked agents/shaper.md step 3 twice as restating roles `#acceptance-shaper-repair` (finding lines 2026-11-06T06:17:31Z, 06:56:43Z), false by owner ruling 2026-11-06.

Suite: evals/owned-rules (cases and grading: its suite.json). Base: ee42108a.

## Runs

- Smoke 20261118T190043Z-b637e2 (1 run, head 93439b81): reviewer-role-step-own-duty FAIL both kits; the head dropped the worker.md restatement and blocked only on a fixture criterion that duplicated AGENTS.md (fixture fixed, 82741171). reviewer-role-restates-skill PASS both.
- 20261118T191648Z-33762c (3 runs, head 82741171): reviewer-role-step-own-duty base 0/3 (each run: `Owner:` docs/specs/roles.md `restated: agents/worker.md`, `Verdict: blocking`), head 2/3; the failed head run blocked only as `prose-duty` (the step was a mechanical changelog duty) and named the role-duty exception for the duplicated-rule. Case caused it: the train fixture's step is now a judgment duty (ask the supervisor before breaking a command's output). reviewer-role-restates-skill (held-out) base 2/3, head 3/3.
- Re-measure on the fixed fixture: pending.
