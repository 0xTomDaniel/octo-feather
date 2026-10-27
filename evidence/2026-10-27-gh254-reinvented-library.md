# gh254: review blocks unexplained reinvention (issue #254)

Change: agents/code-reviewer.md Rules gains a block, class `reinvented-library`: hand-written infrastructure (parser, test runner, protocol, file format, scheduler) with no stated reason where a maintained library or the real tool does the job, a hand-written replacement for a broken library included (fix: a committed patch). AGENTS.md (kit) and templates/python, templates/typescript AGENTS.md gain the writer rule. Case: evals/role-transcripts reviewer-reinvented-parser (base fixture python-app, head python-app-yaml-names).

Smoke: agents/code-reviewer.md (code-reviewer runs below, base 8255ab9 and head)
Removed: nothing deleted. Incident: owner caught templates/typescript toml.ts, a hand-written TOML parser that cleared review (#136, merge ask #181); same class in #204/#208 (custom test runner), #121 (hand-written ECMA regex and Markdown parsers), #203 (modelling just's command line). Director log class owner-caught-reinvented-library.

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
