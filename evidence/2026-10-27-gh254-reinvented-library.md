# gh254: review blocks unexplained reinvention (issue #254)

Change, round 1 (01cff03): agents/code-reviewer.md Rules gains a block, class `reinvented-library`: hand-written infrastructure (parser, test runner, protocol, file format, scheduler) with no stated reason where a maintained library or the real tool does the job, a hand-written replacement for a broken library included (fix: a committed patch). AGENTS.md (kit) and templates/python, templates/typescript AGENTS.md gain the writer rule. Round 2 (owner addenda 2 and 3): the review block moves to code-review step 4, **Prior art** (the `Prior art:` report field with release, activity, adoption, license, pinned version; reviewer checks it); agents/implementer.md gains the dependency path (lockfile adds with network in the worktree, gate offline, no system-wide installs) and the Prior art field in Output; to-tickets asks infrastructure tickets for prior art; the pnpm skill's stop on dependency changes goes. Case: evals/role-transcripts reviewer-reinvented-parser (base fixture python-app, head python-app-yaml-names).

Smoke: agents/code-reviewer.md .agents/skills/code-review/ .skillfile/patches/skills/code-review/SKILL.md.patch (code-reviewer runs below, base 8255ab9 and head)
Smoke: agents/implementer.md .agents/skills/pnpm/ .agents/skills/to-tickets/ .skillfile/patches/skills/to-tickets/SKILL.md.patch (no run: not gradable from transcript facts today; each owed in docs/owed-evals/254.md)
Removed: agents/code-reviewer.md's own reinvention bullet (round 1) became a pointer to code-review step 4, **Prior art**, its one owner; the pnpm skill's "Stop for clarification when the issue requires dependency or package-manager changes without an observable acceptance need", the line that sent library adds to the supervisor. Incident: owner caught templates/typescript toml.ts, a hand-written TOML parser that cleared review (#136, merge ask #181); same class in #204/#208 (custom test runner), #121 (hand-written ECMA regex and Markdown parsers), #203 (modelling just's command line). Director log class owner-caught-reinvented-library.

Runs (`scripts/octo-feather-qa --case reviewer-reinvented-parser`, `--kit-ref 8255ab9` for base). Single samples, no variance claim.

Round 1, first fixture cut (YAML in general, three tests), base run 20261027T234241Z-87d101:
`PASS role-transcripts/reviewer-reinvented-parser: field_lines Verdict: 1 line(s) [{"text": "blocking"}]; holds {"text": "blocking"} [stop: exit, 29 tool calls, 147.7 s] [kit 8255ab90dfd1ccaea29bc97653e1db35128b4e31]`
Base blocked on the parser's bugs against valid YAML (class ad-hoc-parser) and a third test per criterion: exactness, not reinvention. Fixture re-cut: the ticket fixes the file's subset, the parser is exact for it, two tests.

Round 2, re-cut fixture:

1. base, run 20261027T234556Z-8be92a:
   `FAIL role-transcripts/reviewer-reinvented-parser: field_lines Verdict: no line with {"text": "blocking"} in [{"text": "clear"}] [stop: exit, 26 tool calls, 89.7 s] [kit 8255ab90dfd1ccaea29bc97653e1db35128b4e31]`
2. head (working tree on 8255ab9, uncommitted; the result line's kit sha is HEAD's), run 20261027T234731Z-44c72d:
   `PASS role-transcripts/reviewer-reinvented-parser: field_lines Verdict: 1 line(s) [{"text": "blocking"}]; holds {"text": "blocking"} [stop: exit, 22 tool calls, 65.5 s] [kit 8255ab90dfd1ccaea29bc97653e1db35128b4e31]`
   Finding: `class: reinvented-library`, src/app/names.py hand-written YAML parser, use PyYAML `safe_load`.

Result: separates, base FAIL (clear), head PASS (blocking, reinvented-library).
