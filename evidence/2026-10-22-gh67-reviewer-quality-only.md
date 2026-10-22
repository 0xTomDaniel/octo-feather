# Code reviewer judges code quality only (issue #67 items 2 and 3, ticket #86)

Live smoke of the role change (docs/adr/0008): `agents/code-reviewer.md` drops `blast-radius`, the Spec axis and the "run the changed behavior" line, and points to pstack `interrogate`'s `references/code-quality-review.md` and `references/lead-judgment.md`; `blast-radius` moves to `agents/implementer.md`. Owed eval: docs/owed-evals/67.md.

## Setup

- Kit: worktree on `implementer-gh86`, uncommitted role change as committed with this file.
- Fixture: a fresh copy of `templates/python` at `/tmp/gh86-fixture`, own git repo, base commit plus one commit for ticket #1 (`app hello NAME --template-file PATH`). The diff adds `load_template` (reads the file, `.strip()`), `format_greeting` (one `replace`), `render` (pure pass-through to `format_greeting`), a `--template-file` flag and one test whose `tmp_path` parameter lacks a type annotation.
- Probe: a throwaway `pi` wrapper first on PATH (not committed): logs model, skills offered (`--skill`), the role prompt's first line and every read of a SKILL.md or an `interrogate` or `blast-radius` path, runs the real pi with `--mode json`, prints the final message.
- Box: 3 live Pi, 7 GB available. `OCTO_FEATHER_PARENT` and `HERDR_*` stripped; one run, 76 s, rc 0:

```
cd /tmp/gh86-fixture && env -u OCTO_FEATHER_PARENT -u HERDR_... PATH=<probe>:$PATH \
  <kit>/scripts/pi-role <kit>/agents/code-reviewer.md -p "Review ticket #1 ... the diff main~1...HEAD ... print your verdict"
```

## Skills offered and read

```
probe: model ['openai/gpt-6.1-sol'] thinking ['high'] tools ['read,grep,find,ls,bash']
probe: skills offered ['code-review', 'github']
probe: role prompt first line: # Code reviewer
probe: skill or reference read <kit>/.agents/skills/code-review/SKILL.md
probe: skill or reference read <kit>/.agents/skills/interrogate/references
probe: skill or reference read <kit>/.agents/skills/interrogate/references/code-quality-review.md
probe: skill or reference read <kit>/.agents/skills/interrogate/references/lead-judgment.md
probe: tool calls 20, pi exit 0
```

`blast-radius` was neither offered nor read. Before this change the reviewer was offered `blast-radius, code-review, github` (main's frontmatter; the qc smoke `evidence/2026-10-22-gh67-qc-judge-skills.md` shows the same list).

## Verdict (final message, quoted)

```
## Verdict: BLOCKED
### Standards
- Block | class: red-gate | tests/test_cli.py:31
  just check fails Ruff ANN001: tmp_path lacks a type annotation. AGENTS.md, Rules: a red gate blocks handoff. Annotate it as Path.
- Block | class: redundant-wrapper | src/app/core.py:15-20
  render delegates to format_greeting, which merely calls replace. Inline template.replace("{name}", clean) into greet and
  delete lines 15-20, removing both unnecessary call layers. Basis: interrogate/references/code-quality-review.md,
  dimensions 0 and 4, structural simplification and pass-through helpers.
### Spec
- Block | class: template-content-loss | src/app/core.py:12
  The ticket requires greeting with the file text, replacing {name}. .strip() additionally removes file content.
  Reproduced through the installed CLI: file "  Hi {name}!\n" produces "Hi Ada!", not "  Hi Ada!\n". Remove .strip().
Summary: Standards: 2 blockers. Spec: 1 blocker. No non-blocking notes.
```

## Judgment against the new bar

- Block 1 (red-gate): a documented standards breach, cited (fixture `AGENTS.md` Rules: a red gate blocks handoff). In the bar.
- Block 2 (redundant-wrapper): a named simplification listing the lines it deletes (15-20). In the bar.
- Block 3 (template-content-loss): not a documented standards breach and not a simplification. It is a behaviour block from a Spec pass, proven with a file the reviewer built itself in a temp dir; no criterion or user case in the ticket has leading whitespace, so it is the hypothetical case lead-judgment dismisses. The new bar should have dismissed it (at most a note). Cause: the vendored `code-review` skill still runs its Spec pass and its patch still carries the "broken behaviour (with the failing case)" block; the role's "Standards pass" wording did not override the skill. The patch is ticket #87's scope; the upstream two-axis process stays after that prune unless the role or patch says to skip the Spec pass.
- So the demo half "blocks only under the new bar" is not met by this run: 2 of 3 blocks are in the bar, 1 is a self-proven behaviour block.

## Harness incident

The headless run had no parent route (`OCTO_FEATHER_PARENT` and Herdr ids stripped), but `herdr` was still on PATH with a live session: after three failed `herdr-say --parent` sends, the reviewer followed its Output rule's fallback, read the director pane from `$(octo-feather-state)/director.toml` and sent its verdict there, despite the brief saying not to message anyone. Any further probe must make live Herdr unreachable (a sandbox `HERDR_SESSION`, or `herdr` off PATH), not only unset the parent route.
