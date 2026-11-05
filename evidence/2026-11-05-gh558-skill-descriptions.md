# gh558: tdd, python, typescript reach their roles (#558)

Smoke: .agents/skills/tdd/SKILL.md .agents/skills/python/SKILL.md .agents/skills/typescript/SKILL.md .skillfile/patches/skills/tdd/SKILL.md.patch (skill-triggers tdd-shout-flag, `just qa --suite skill-triggers --case tdd-shout-flag --runs 1 --baseline ea7d779`, run 20261105T005708Z-33ff9e: baseline PASS, current PASS, real transcripts; then the 8 cases below, run 20261105T005735Z-8fc44b; and tests/skills-loaded.sh: real Pi, fake provider, implementer offered exactly its listed skills with tdd, python, typescript, code-reviewer tdd, a broken listed or declared skill refused with zero requests)
Removed: none; each description is double-quoted, its text unchanged as Pi reads it (Pi's get_commands returns the same string as the ea7d779 plain value). The incident: a plain YAML value holding ': ' made Pi drop tdd, python and typescript with no error, so the implementer was offered 14 of its 17 listed skills and the code reviewer no tdd.

## Change

- `.agents/skills/tdd/SKILL.md` (through `.skillfile/patches/skills/tdd/SKILL.md.patch`), `.agents/skills/python/SKILL.md`, `.agents/skills/typescript/SKILL.md`: the frontmatter description double-quoted.
- Offered before and after, from the system prompt of a headless pi-role run against a fake provider (`/tmp/gh557/probe.sh`): at ea7d779 implementer missing python, tdd, typescript, code-reviewer missing tdd; at 6d5ec41 every role (implementer, code-reviewer, corrector, director, supervisor, reflector, qc-judge) missing none.

## Real runs

`just qa --suite skill-triggers --case tdd-shout-flag --case impl-python-name-length --case impl-ts-precise-type --case rev-tdd-shout-tests --case tdd-tab-in-name --case impl-python-ruff-config --case impl-ts-shout --case rev-tdd-would-catch --runs 3 --baseline ea7d779`, run 20261105T005735Z-8fc44b, kit 8d2a7de (177bc2d merged with gh557 45aca96):

- Train 4/4: tdd-shout-flag, impl-python-name-length, impl-ts-precise-type, rev-tdd-shout-tests each 3/3 runs, baseline 3/3.
- Held-out 4/4: tdd-tab-in-name, impl-python-ruff-config, rev-tdd-would-catch each 3/3, baseline 3/3; impl-ts-shout 3/3, baseline 2/3.
- Analysis: 7 of 8 non-discriminating. At ea7d779 the roles still read the skill by path (the role body names it). The measurable change: the load comes at tool call 2 to 5 (current) against 5 to 12 (baseline).
