# gh529: implementer and code reviewer read codebase-design at the seam step

Change (a33a26e): agents/implementer.md and agents/code-reviewer.md list codebase-design with one step line each naming when to read it; the codebase-design description is patched (ADR 0012) to trigger on designing a module's interface, deciding where a test seam goes, and judging a test seam a diff adds or moves. Cases (9bc827b, written before the change): 8 skill-trigger cases graded on codebase-design, fixture evals/fixtures/py-review-seams (py-mini plus four diffs under review/).

Smoke: agents/code-reviewer.md .agents/skills/codebase-design/SKILL.md .skillfile/patches/skills/codebase-design/SKILL.md.patch skill-triggers `rev-design-seam` at a33a26e, run 20261104T180936Z-c18a97 PASS (codebase-design loaded at tool call 8 of 8).
Smoke: agents/implementer.md skill-triggers `impl-design-seam` at a33a26e, run 20261104T181005Z-913bcf current run 1 PASS (codebase-design loaded at tool call 8 of 8).

Removed: codebase-design's upstream description ("Shared vocabulary for designing deep modules. Use when the user wants to ..."), replaced by the patched one; the #520 audit (0 reads of codebase-design in 843 sessions) is the incident.

## Description changed after these runs

PR #531 review (blocks 1, 2): the description's parenthetical dependency prescriptions (in-process, local stand-in, port with an in-memory adapter, mock only true externals) restated DEEPENING.md#dependency-categories and were cut; the description now reads "Designing a module's interface and where its tests cross it: deep modules and seams. Use before ...", the Use clause unchanged. All runs below are against a33a26e's longer description, not the current one. No qa rerun here (box Pi cap): the trigger rerun (`impl-design-seam`, `rev-design-seam`) is owed on lane 479's fixed runner.

## Runner

Lane 479's scripts/octo-feather-qa at gh479 26cfedc, byte-identical (sha256 45e6b64f04c62e55e9c5a3bb07ccd182c7064ab337b1ce7a2b740d8b4b4f731c), copied into a scratch detached worktree of a33a26e (/tmp/gh529-runner, removed after): the gh479 checkout sits at bd018e2, not 26cfedc. Always `--evals` this worktree's evals, `--kit-ref a33a26e`, `--baseline origin/main` (ea7d779: codebase-design unlisted, reachable only through tdd's pointer). Sequential, one run at a time.

## Runs

Should-trigger, `--runs 3`, run 20261104T181005Z-913bcf. Should-not, once per side, run 20261104T182336Z-f16d0d.

| case | split | should | before (ea7d779) | after (a33a26e) |
| --- | --- | --- | --- | --- |
| impl-design-seam | train | read | 0/3 | 2/3 |
| rev-design-seam | train | read | 0/3 | 2/3 |
| impl-design-near-bugfix | train | not read | 1/1 | 1/1 |
| rev-design-near-bugfix | train | not read | 1/1 | 1/1 |
| impl-design-phrasebook | held-out | read | 0/3 | 2/3 |
| rev-design-phrasebook | held-out | read | 0/3 | 2/3 |
| impl-design-near-rename | held-out | not read | 1/1 | 1/1 |
| rev-design-near-rename | held-out | not read | 1/1 | 1/1 |

Totals: should-trigger train before 0/6 runs, after 4/6; held-out before 0/6, after 4/6. Should-not train 2/2 both sides, held-out 2/2 both sides.

## Finding: the 12-call cap cuts reads already issued

Of the 4 failed after runs, 3 issued the codebase-design read: rev-design-seam run 1 (call 10 of 12), rev-design-phrasebook run 1 (call 11 of 12), impl-design-phrasebook run 2 (call 12 of 12). Each read was in a parallel codemode batch whose start events reached the suite's `max_tool_calls` 12, so the run stopped before its result, and no load counts. Only impl-design-seam run 2 issued none in 12 calls (it read implement and tdd, then the code). No before run issued one.

Limit: should-not cases pass at the cap too (12 calls without a read); they show no early read, not none at all.

## Pi dropped codebase-design: invalid YAML frontmatter (lane 557 finding)

The patched description (a33a26e through a84b079) is an unquoted plain scalar holding ": " ("where its tests cross it: deep modules"), invalid YAML, and Pi silently skips a skill whose SKILL.md frontmatter does not parse (~/.local/pi/docs/skills.md: "Malformed SKILL.md files ... are not loaded"). So no role was offered codebase-design; every after run above loaded it only through the role step pointers (agents/implementer.md, agents/code-reviewer.md) naming it by path. Fix: the description is double-quoted in the patch, same words; check-vendored reapplies byte-equal.

Proof by asking Pi: real Pi at the kit pin, launched by `scripts/pi-role agents/<role>.md --model fake/fake --no-session -p "say ok"` from this worktree, headless, against a fake OpenAI-compatible provider on 127.0.0.1 that records each request body (the provider, models.json and credential-free `pienv` of tests/lib/resume-on-error.sh: empty HOME, own PI_CODING_AGENT_DIR, PI_OFFLINE=1; no real model call). Offered = the `<name>` entries of `<available_skills>` in the system prompt Pi sent; listed = the role file's `skills:` plus `externalSkills:` ({tracker} counted as github-issues). Pi printed no skill diagnostic on stderr either side. Harness: /tmp/gh529-pi/offered.sh (scratch, removed after), run as `offered.sh <worktree> implementer code-reviewer shaper`.

Before, a84b079:

```
== implementer: pi-role -p rc=0 answer=fake-answer-ok
offered: principle-prove-it-works principle-encode-lessons-in-structure blast-radius commit create-verification-skill maintain-verification-skill eval-cases github-pr github-issues implement nodejs pnpm pull agent-browser
missing: python tdd codebase-design typescript
== code-reviewer: pi-role -p rc=0 answer=fake-answer-ok
offered: code-review github-pr
missing: tdd codebase-design
== shaper: pi-role -p rc=0 answer=fake-answer-ok
offered: grill-with-docs grilling domain-modeling sharpen improve-codebase-architecture spec-chat-shape spec-chat-review
missing: codebase-design
```

After, description quoted:

```
== implementer: pi-role -p rc=0 answer=fake-answer-ok
offered: principle-prove-it-works principle-encode-lessons-in-structure blast-radius commit create-verification-skill maintain-verification-skill eval-cases github-pr github-issues implement nodejs pnpm pull codebase-design agent-browser
missing: python tdd typescript
== code-reviewer: pi-role -p rc=0 answer=fake-answer-ok
offered: code-review github-pr codebase-design
missing: tdd
== shaper: pi-role -p rc=0 answer=fake-answer-ok
offered: grill-with-docs grilling domain-modeling sharpen codebase-design improve-codebase-architecture spec-chat-shape spec-chat-review
missing: none
```

Other skills a kit role lists that Pi drops the same way, not fixed here (lane 557 owns them): tdd (implementer, code reviewer), python and typescript (implementer). Corrector, director, qc-judge, reflector and supervisor at a84b079: missing none; the director with `tracker = "linear"` in a scratch repo is offered linear.

Limit: the trigger runs above predate the quoting, so they measure the step pointers, not the description; the codebase-design trigger rerun is owed in the eval slot.
