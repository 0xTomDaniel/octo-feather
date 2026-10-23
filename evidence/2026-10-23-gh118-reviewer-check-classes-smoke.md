# gh118 smoke: code reviewer classifies each check exact or proxy

Smoke: agents/code-reviewer.md .skillfile/patches/skills/code-review/SKILL.md.patch .agents/skills/code-review/
Removed: nothing from the reviewer's rules (the #117 tdd, tautological and coupled-test rules are kept); added the `Check:` / `Checks: none` lines the verdict helper requires since 214894b/39aa595. Incident: #104's check-test-surface and #107's grade-review.py reached main or review as checks with no one asked to classify them.

Run, 2026-10-23, branch corrector-gh118 with this change in the worktree: `pi-role agents/code-reviewer.md -p <brief>` headless, isolated (`env -i`, PATH = pi only, no herdr, `HERDR_SESSION=gh118-smoke-sandbox`, temp HOME and Pi agent dir, `--session-dir` in the run dir), on a copy of evals/fixtures/python-app with branch implementer-t1 adding `scripts/check-tests-public` (a regex over tests/*.py for `app.core` imports, enforcing "tests go through the CLI", a proxy) and `scripts/check-exec` (git index mode 100755 under scripts/, exact), both wired into `just check`. Brief: review lane gh2, ticket T2, diff `main...implementer-t1`.

Final report (trimmed):

```
**Block [class: proxy-check]**: `scripts/check-tests-public:4-9`, enabled at `justfile:22`, uses selected source tokens as a stand-in for "tests use only the CLI." Violates docs/adr/0008-prose-last.md, Exact check ...
Check: scripts/check-tests-public: tests use CLI only | reads: regex matches in tests/*.py | class: proxy
Check: scripts/check-exec: tracked scripts have mode 100755 | reads: Git index modes under scripts/ | class: exact
Check: justfile: check includes CLI-surface and executable guards | reads: existing gate and new script exit statuses | class: proxy
```

Through the helper (fake gh, PR 2 at the reviewed head): the report plus `Verdict: blocking` posts, the comment header carrying the three `Check:` lines; the same report with `Verdict: clear` is refused ("a proxy check blocks"); the earlier fact|meaning run's report is refused ("has class 'meaning'; write `class: exact` or `class: proxy`").

An earlier run on the fact|meaning wording classified the regex check `meaning` and blocked it as `meaning-in-check`. Not run: the reviewer at main 61b9f22 (no instruction to classify existed there).
