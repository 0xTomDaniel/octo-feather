# gh791 / PR #800 review round 1: refactoring playbook fixes

Change (head c22aa438, fix 96abf9f0): `.skillfile/patches/skills/refactoring.patch` and the `.agents/skills/refactoring/SKILL.md` it deploys.

- role-boundary: large or cross-cutting structural work now escalates to the parent (`herdr-say --parent`, docs/adr/0015), not "back to the user".
- duplicated-rule: the description drops "Load it before the first edit"; it keeps applicability (restructuring with behaviour unchanged, not a feature or bug fix). When to load stays with the roles (agents/implementer.md, supervisor.md, code-reviewer.md Rules).
- reinvented-library: no runner or dependency change; the fixtures' pytest is the pin the kit and templates/python already hold (uv.lock 9.1.1). Its Prior art line is in the hand-off report.
- note: tests/check-vendored.sh single-file comment points at scripts/check-vendored's docstring.

Patch reason line unchanged. Runs serial in the eval slot of lane gh791.

1. `just check-vendored`: `vendored: ok (27 skills equal authenticated upstream at pin plus patches; skillfile v1.9.2, offline)`. `bash tests/check-vendored.sh`: ok.
2. Skill-trigger cases, once each, impl-, sup- and rev-refactor-* (12 cases), run 20261113T010005Z-798354, kit 96abf9f0: `qa: 12/12 passed`. Should-read cases load refactoring/SKILL.md (tool calls 2 to 7); the near misses (near-wave, near-binary, near-inner-space) read no refactoring skill.
3. Demo smoke, one run each, run 20261113T010727Z-90d47a, kit 96abf9f0: `PASS role-transcripts/implementer-refactor-ticket`, `PASS role-transcripts/supervisor-refactor-lane`, `PASS role-transcripts/reviewer-refactor-diff` (`qa: 3/3 passed`): each loads all four skills before its first edit or final message.
4. Demo proof, `--runs 3`, run 20261113T012438Z-f5e7b2, kit 22e00e07: `PASS role-transcripts/implementer-refactor-ticket: 3/3 runs passed (pass rate 1.00, stddev 0.00)`, `PASS role-transcripts/supervisor-refactor-lane: 3/3 runs passed (pass rate 1.00, stddev 0.00)`, `PASS role-transcripts/reviewer-refactor-diff: 3/3 runs passed (pass rate 1.00, stddev 0.00)`.
