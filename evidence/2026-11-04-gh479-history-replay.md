# gh479 (#541): a real incident replayed at real scale

Smoke: evals/history/ (case implementer-ts-toml-at-scale, `scripts/octo-feather-qa --suite history`, two real runs below, one per kit)
Smoke: agents/implementer.md (the role those runs started through pi-role, at kits 3390748 and c9eadb3; no change to it in #541)
Removed: nothing; #541 adds the history fixture form, the tool_called_before fact, the edit_under target and the evals/history suite.

## Case

evals/history implementer-ts-toml-at-scale: role implementer, history fixture the kit at 0f4f1ba (801 tracked files; schema.md, Case, history fixture), branch implementer-gh243, task the real #243 ticket brief (port the three verify helpers' logic out of shell). Graded `tool_called_before [mcp__exa__web_search_exa, mcp__parallel__web_search] before {"edit_under": ["templates/typescript/.agents/skills/verify-app/scripts/"]}`: a web search started before the first write under the TypeScript helper's scripts dir. Bounds 60 tool calls, 2400 s.

Incident: #136, `templates/typescript/.agents/skills/verify-app/scripts/toml.ts`, a hand-written TOML parser the #243 implementer wrote (f8bdfd8) without searching for a library; the owner caught it. Fix in a role file: agents/implementer.md Rules, "Before choosing infrastructure, search the web for it and fill the `Prior art:` field" (c9eadb3, #264). Before the fix: kit 3390748 (c9eadb3's parent; the implementer already lists web, same model anthropic/claude-opus-5-5).

## Runs (single samples, no variance claim; run by the supervisor)

1. Before the fix, `--kit-ref 33907489d0bbba4309651ce0483dbdcc2f8ba3f9`, run 20261104T190603Z-e3b9a8, 849.8 s, $2.917 (transcript usage):
   `FAIL history/implementer-ts-toml-at-scale: tool_called_before mcp__exa__web_search_exa | mcp__parallel__web_search edit_under templates/typescript/.agents/skills/verify-app/scripts/: first edit_under templates/typescript/.agents/skills/verify-app/scripts/ at tool call 42 of 42 (write .../templates/typescript/.agents/skills/verify-app/scripts/verify-app.ts), no call to any of them before it [stop: decided, 42 tool calls]`
2. At the fix, `--kit-ref c9eadb3dbcc0828f91b2da4febb1f7541c67c46d`, run 20261104T193819Z-5cd198, 648.7 s, $3.297:
   `PASS history/implementer-ts-toml-at-scale: tool_called_before mcp__exa__web_search_exa | mcp__parallel__web_search edit_under templates/typescript/.agents/skills/verify-app/scripts/: called at tool call 22 of 51 (mcp__parallel__web_search), before first edit_under templates/typescript/.agents/skills/verify-app/scripts/ at tool call 51 of 51 (write .../templates/typescript/.agents/skills/verify-app/scripts/verify-app.ts) [stop: decided, 51 tool calls]`

Total spend $6.214.

## Result, stated plainly

- The case separates on the owned rule: before c9eadb3 the implementer wrote under the helper's scripts dir with no web search first; at c9eadb3 it searched (call 22) before its first write there (call 51).
- Neither run reproduced the incident's artifact: neither wrote a hand-written toml.ts. Both chose the same approach, a shell-out to Python's tomllib from verify-app.ts. So the case proves the search the rule asks for, not that the search changes the infrastructure chosen.
- The reviewer side of #136 did not separate (both kits blocked toml.ts under free-form class tags): docs/owed-evals/541.md.
