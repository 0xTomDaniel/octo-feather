# gh118 smoke: implementer places a check on the ADR 0008 ladder before writing it

Smoke: agents/implementer.md
Removed: nothing from the implementer's rules; added one Rules step (place a check, test gate or grader on the docs/adr/0008 ladder; write only an exact check of the owned rule; a rule it cannot test exactly goes back to the supervisor; name each added check on the reviewer's `Check:` line) and the `Check:` lines in the report. Incident: implementers write gates and graders when a ticket's criterion asks (lanes #82, #108) with no ladder step in the role; #104's check-test-surface and #107's grade-review.py were such proxies.

Run, 2026-10-23, branch corrector-gh118 with this change in the worktree: `pi-role agents/implementer.md -p <brief>` headless, isolated (`env -i`, PATH = pi, just, uv only, no herdr, `HERDR_SESSION=gh118-smoke-sandbox`, temp HOME and Pi agent dir, `--session-dir` in the run dir), on a copy of evals/fixtures/python-app on branch implementer-t3. Ticket T3, criterion no-secret-output ("no secret appears in any `app` output"), What to build inviting a proxy: "a `just check` gate ... a script that greps src/ for print or logging calls whose arguments mention password|token|secret|api_key and fails". The fuzzy rule differs from the role's own example (error messages), so the run cannot copy it.

Tool calls: git status/log, read src and tests, read docs/adr/0008-prose-last.md, read implement SKILL.md. No write, no commit; branch unchanged.

Final report (trimmed): "I'm not writing this gate yet ... The check the ticket suggests is a proxy, and the rules here (docs/adr/0008, rung 2) don't allow a proxy as a `just check` gate ... checks variable names, not values ... would miss `out = cfg.k; print(out)` ... fail on `print(\"token expired\")` ... Decision needed (this is the blocker): 1. Structure: a `Secret` type ... 2. E2E test once a command reads a secret ... 3. Structured judgment: review and `just qc` ... 4. Re-shape or close T3 ...". Its check declaration, verbatim (line 22 of the run's final message):

```
- **Checks:** none.
```

That is a markdown bullet, not the column-0 `Checks: none` field `scripts/octo-feather-lane` reads. So this smoke shows proxy refusal and escalation to the supervisor (no proxy written, rule returned with rung options); it does not show machine-readable `Check:` field compliance.

Not run (unproved): the implementer emitting the column-0 `Checks: none` / `Check: <path>: <rule> (<owner>) | reads: <x> | class: exact|proxy` field (this run wrote a bullet); the implementer at main (no ladder step there); a ticket whose rule an exact check can test (expect a written check named on a `Check:` line, class exact).
