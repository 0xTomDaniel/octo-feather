# Patch prunes, writing-for-agents, pruning habit (issue #67 items 4, 5 and 6, ticket #87)

Live smoke of the patch changes (docs/adr/0008). Owed eval: docs/owed-evals/67.md.

Removed: the `code-review` Spec axis and Spec pass (description, axis list, parallel sub-agents, spec-source step, Spec prompt, two-report aggregate, "Why two axes") and the patch's "broken behaviour (with the failing case)" Spec block line and its duplicate "Never a block" bullet (94 to 89 patch lines); the `blast-radius` patch's old reason "the code reviewer runs it"; `implement-spec` step 7's restated qc-then-review order (`just qc ...` flips criteria in a status-only commit, then review "on the head QC left", "Never review in your own context") and step 4's matching parenthetical; upstream `writing-for-agents`' two `CLAUDE.md` mentions; the `tdd` seam sentence's restatement of ADR 0002 (surface list, real data files, "integration or end-to-end, never a unit test of internals").

## Changes

- `code-review` patch: first line `# reason: ADR 0007 fresh reviewer; ADR 0015 escalate with --parent; block only on a documented standards breach or a named simplification, so one Standards pass, no Spec pass`. The skill is now one Standards review: pin the fixed point, standards sources plus smell baseline, run the review, verdict. Verdict bullets: **Block** (documented hard standard breach, or a named simplification that lists the lines it deletes) and one **Never a block** (baseline smells, preferences, no named consequence). `wc -l`: 94 before, 89 after.
- `blast-radius` patch: kept (supervisor's choice A, spec call gh67 72c31e1), one change dropping `disable-model-invocation`. Its old lines, as the patch lost them:

  ```
  # reason: ADR 0012 model-invoked: the code reviewer runs it
  ```

  now `# reason: ADR 0012 model-invoked: the implementer runs it`. Why kept: Pi hides a `disable-model-invocation: true` skill from the prompt even when passed with `--skill` (Pi source: `visibleSkills = skills.filter((s) => !s.disableModelInvocation)`). Probe with no model call (an extension dumps the system prompt at `before_agent_start`, then exits): `pi --no-skills --skill <upstream blast-radius> --skill tdd` listed only `tdd` (`[["blast-radius",true],["tdd",false]]`); with the patched folder both were listed. Dropping the patch would have left the implementer's skills line naming a skill it cannot see.
- `implement-spec` step 7: `run just qc and a fresh code-reviewer pane as spec #lanes-one-head and #gates-merge say (docs/adr/0022); read them there, never restate them.` Logging (ADR 0020), one fixer, notes to the PR stay. Step 4's pilot path now reads "through steps 4, 5 and 7". 42 lines before and after.
- `tdd`: seam sentence now `public surfaces only (docs/adr/0002), taken from the ticket's acceptance criteria, one or two tests per criterion`; reason line matches spec skills#skill-tdd. 20 lines before and after.
- `writing-for-agents` vendored at `mattpocock/skills@49dd158` (`skills/productivity/writing-for-agents`; upstream sets no `disable-model-invocation`), Skillfile, Skillfile.lock, NOTICE, `agents/corrector.md` skills line. Patch `# reason: ADR 0001 Pi only: CLAUDE.md mentions removed` (spec call gh67 15a518d): check-refs failed on upstream's two `CLAUDE.md` mentions (description, first line), as interrogate's did (e04f384).
- ADR 0008 carries the eval question and the `Removed:` fact; ADR 0012 gives blast-radius to the implementer, writing-for-agents to the corrector.
- Pruning habit: `scripts/check-behavior-smoke` fails a range changing `agents/*.md` or `.skillfile/patches/**` (not opted out) unless an added or modified `evidence/*.md` holds a `Removed: <text>` line, naming the fix; tested in `tests/check-behavior-smoke.sh`.

## Demo

```
$ scripts/check-vendored
vendored: ok (17 skills equal authenticated upstream at pin plus patches; skillfile v1.9.2, offline)
```

The cache already held both pins, so `just vendored-fetch` was not needed.

## Live smoke: patched reviewer on the #86 fixture

- Fixture: `<fixture>` from `evidence/2026-10-22-gh67-reviewer-quality-only.md` (template app, base 3a24e66, ticket #1 commit 14d48b4: `.strip()` in `load_template`, pass-through `render`, a `tmp_path` without annotation).
- Box: 3 live Pi, 7013 MB available. Sandbox: `env -i`, PATH holding only a `pi` link plus system dirs (`herdr` and `herdr-say` not on PATH, checked), `HERDR_SESSION=gh87-sandbox`, no `HERDR_*` or `OCTO_FEATHER_PARENT`. One run, 54 s, rc 0:

```
cd <fixture> && env -i HOME=... PATH=<probe-bin>:/usr/local/bin:/usr/bin:/bin HERDR_SESSION=gh87-sandbox \
  python3 <kit>/scripts/pi-role <kit>/agents/code-reviewer.md --no-session --mode json -p "Review ticket #1 of this repo
  (no GitHub issue; its text): 'app hello NAME --template-file PATH greets NAME using the file's text as the template,
  replacing {name}.' Review the diff 3a24e66...HEAD. No supervisor exists in this run: message no one; print your verdict
  as your final message."
```

Tool calls, in order: read `code-review/SKILL.md` (patched); `git diff`; read `interrogate/references/code-quality-review.md` and `lead-judgment.md`; read fixture files; `just check`; a `uv run python` script writing `  Hi {name}!\n` to a `tempfile.TemporaryDirectory()` and running the CLI on it; then the Output rule's send: `herdr-say: command not found` three times, `octo-feather-state: command not found`, so nothing left the sandbox (#86's leak to the director did not recur).

Verdict (final message, condensed): BLOCKED. Block `redundant-wrapper` core.py:15-20 (delete lines 14-21; code-quality-review.md dimensions 0 and 4). Block `template-content-loss` core.py:12 (`.strip()`, reproduced through the CLI). Block `red-validation-gate` tests/test_cli.py:31 (Ruff ANN001; AGENTS.md: a red gate blocks handoff). Notes: none.

## Result

- No Spec pass: the skill has none, and the report has no Spec section or axis summary (before: `### Standards` and `### Spec`).
- Behaviour block: **still there.** `template-content-loss` is the same self-built repro as #86's smoke, now with no skill text asking for it. What still points at it: `agents/code-reviewer.md` Required inputs ("The ticket, and the canonical spec section it derives from") and a brief that quotes the ticket, so the model checks the diff against the ticket on its own. The role file is out of this ticket's scope (#86); the patch half of the owed eval is done, the "no behaviour block" half is not met. One smoke, as briefed; no rerun.
