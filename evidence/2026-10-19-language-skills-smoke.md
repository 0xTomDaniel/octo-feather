# Language skills smoke (python, typescript), 2026-10-19

Smoke for the language skills (ADR 0008, until `just qa` exists): no unit-test content, basedpyright strict for Python, and Zod 4 as the TypeScript default.

Setup: one headless implementer per language, `pi-role agents/implementer.md --model anthropic/claude-sonnet-5-5 --thinking off -p "<ticket>"`, run in a fresh copy of `templates/<lang>` (after `just setup`, one commit). The ticket was to add `app bye NAME` (JSON on `--json`, exit 0; a blank name gives a JSON error and exit 2), working test-first and keeping `just check` green.

| | python | typescript |
|---|---|---|
| Result | commit `e9796b9`, `just check` green | commit `d045221`, `just check` green |
| Files | `src/app/core.py`, `src/app/cli.py`, `tests/test_cli.py` | `src/core.ts`, `src/cli.ts`, `tests/cli.test.ts` |
| Tests added | 3: in-process CLI x2, installed `app` subprocess x1 | 3: in-process `main` x2, `node src/cli.ts` process x1 |
| Unit tests or `*.unit.test.*` | none | none |
| Red first | yes (`SystemExit: 2`, unknown command) | yes (3 failed, 3 passed) |
| Demo path run by hand | `uv run app bye Ada --json` | `node src/cli.ts bye Ada --json` |
| Language skill read | yes (`python`) | no: it said "declared in AGENTS.md but not opened" |
| Time, cost | 21 s, $0.059 | 35 s, $0.073 |

Code review of the TypeScript change: real reviewer (`openai/gpt-6.1-sol` high, the new `blast-radius` skill), headless.
- Verdict: clear.
- Blast radius: it named the one safety fact (the shared name cleaning in `src/core.ts:6` keeps the earlier trim-and-reject behaviour) and proved it by running the CLI. Its parent/head `hello` comparisons (22) all matched, along with 22 `bye` checks and 4 usage checks. It ran `just check` in a disposable copy and left the checkout unchanged.
- Cost: $0.066.

Findings:
- The TypeScript implementer did not open the `typescript` skill. Nothing in the ticket touched schemas or MSW, so no rule was broken, but the skill's guidance was never read. This is owed as an eval case in `docs/future.md`.
- Both implementers verified through the real demo path, as `principle-prove-it-works` asks, without naming the skill.
