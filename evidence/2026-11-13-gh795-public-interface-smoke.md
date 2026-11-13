# gh795 round 3: public-interface smokes and deepen-first self-check

Smoke: agents/qc-judge.md run once below (b), driving an MCP-only fixture.
Smoke: agents/implementer.md .agents/skills/tdd/SKILL.md .skillfile/patches/skills/tdd/SKILL.md.patch .agents/skills/codebase-design/DEEPENING.md .skillfile/patches/skills/codebase-design/DEEPENING.md.patch run once below (self-check, the implementer-deepen-first task verbatim; the run read the patched tdd SKILL.md at its first wording, before the issue-comment sentence was sharpened).
Smoke: agents/supervisor.md .agents/skills/to-tickets/SKILL.md .skillfile/patches/skills/to-tickets/SKILL.md.patch not run: (a) stopped at its precondition, `octo-feather-lane ticket -` refuses an MCP-client demo (probe below), a script gap for the supervisor.
Removed: the tdd Seams paragraph's single-sentence deepen-first ("deepen it first as its own step: pin current behavior, deepen the module, then test at the new interface"), replaced by four ordered steps each ending on a done condition; implementer.md's dense seam bullet, replaced by the same order.

Issue #795, ticket #796, branch gh795-796. Review round 3 (`/tmp/gh795/review3.md`): implementer-deepen-first failed 3 of 3 runs (QA run 20261112T234850Z-2ce373).

## Why the old wording did not steer

Transcripts of QA run 20261112T234850Z-2ce373 current/run-1 and run-2: each implementer read `tdd` SKILL.md, then wrote a test at the new interface, saw it red, then created `src/app/pricing.py` with the new behaviour and committed once. The tdd skill put deepen-first as one clause mid-paragraph, while its loop rules said "Red before green" and "Refactoring is not part of the loop": the agent took creating the new module as part of green. `DEEPENING.md` was never read. Run 1 never read the tracker skill, so never posted the comment.

## Fixture: MCP-only target

`/tmp/gh795/mcpfx` (throwaway git repo, head `abf59bf`): Python package `quotemcp`, `mcp` SDK pinned in `uv.lock`, `[project.scripts] quote-mcp` a stdio MCP server with tool `quote(region, subtotal)`. `AGENTS.md`: "Its only public interface is the MCP server `quote-mcp` ... There is no CLI, HTTP API or UI for users." Spec `docs/specs/quote.spec.html`, criteria `acceptance-quote-tax`, `acceptance-quote-de`, each "When an MCP client calls tool `quote` ...".

## (a) Ticket demo through MCP: blocked by the ticket check

The draft demo a supervisor or `to-tickets` would write for the MCP interface, run through the ticket check before any role run:

```
stdin: class: layer-only-ticket: demo runs no surface the repo declares (`npx -y @modelcontextprotocol/inspector@0.17.2 --cli uv run quote-mcp --method tools/call --tool-name quote --tool-arg region=de --tool-arg subtotal=100.00`: @modelcontextprotocol/inspector@0.17.2 is not an executable the repo tracks); fix: make the demo a backticked command through the repo's own public surface (ADR 0009): a program the repo declares (a tracked executable such as scripts/NAME or bin/NAME, a justfile recipe other than check/integrate/qc/qa, a package.json bin or pyproject [project.scripts] entry, e.g. `uv run app hello Ada`, or a tracked script run by its interpreter, e.g. `python harness.py`, only as ADR 0002's fallback), an HTTP request (`curl https://...`), or a UI driver run (`npx playwright test ...`); not printf, echo or another generic tool; or, for a command this ticket creates, declare it exactly with `Creates: `<path>``, form: octo-feather-lane --help (ticket), the demo running that path; or, for one step of a wide refactor, add the line `Expand-contract: expand|migrate|contract`
exit 1
```

The check accepts only a program the repo declares, an HTTP request or a UI driver, so a standard MCP client (the MCP Inspector CLI) is refused. Per the round 3 brief, stopped and reported to the supervisor as a script gap; no supervisor or to-tickets run.

## (b) QC judge drives the MCP interface

From `/tmp/gh795/mcpfx`, kit at this branch's working tree, PATH with a logging `herdr-say` stub first:

```
scripts/pi-role agents/qc-judge.md -p "Judge head abf59bf of this repo (/tmp/gh795/mcpfx, branch main) against criteria quote#acceptance-quote-tax and quote#acceptance-quote-de (docs/specs/quote.spec.html). Report, per criterion, one line `<criterion>: pass|fail`, then the exact command you ran and its output."
```

Pi session `01a1d262-826b-74ea-833f-91bfcbec3942` (`~/.pi/agent/sessions/--tmp-gh795-mcpfx--/`). Final message, verbatim:

````
quote#acceptance-quote-tax: pass
quote#acceptance-quote-de: pass

Exact command, exercising both criteria through MCP stdio:
```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python - <<'PY'
import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    server = StdioServerParameters(command="/tmp/gh795/mcpfx/.venv/bin/quote-mcp", env={"PYTHONDONTWRITEBYTECODE": "1"})
    with open('/tmp/quote-qc-stderr.log', 'w') as log:
        async with stdio_client(server, errlog=log) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                for criterion, args in [
                    ('quote#acceptance-quote-tax', {'region': 'uk', 'subtotal': 10.00}),
                    ('quote#acceptance-quote-de', {'region': 'de', 'subtotal': 100.00}),
                ]:
                    result = await session.call_tool('quote', args)
                    print(criterion)
                    print(json.dumps(result.model_dump(mode='json', exclude_none=True), sort_keys=True))

asyncio.run(main())
PY
```

Output:
```text
quote#acceptance-quote-tax
{"content": [{"text": "{\n  \"subtotal\": \"10.00\",\n  \"tax\": \"2.00\",\n  \"total\": \"12.00\"\n}", "type": "text"}], "isError": false, "structuredContent": {"subtotal": "10.00", "tax": "2.00", "total": "12.00"}}
quote#acceptance-quote-de
{"content": [{"text": "{\n  \"subtotal\": \"100.00\",\n  \"tax\": \"19.00\",\n  \"total\": \"119.00\"\n}", "type": "text"}], "isError": false, "structuredContent": {"subtotal": "100.00", "tax": "19.00", "total": "119.00"}}
```
````

It drove the server through an MCP client session (`mcp.client.stdio`, `ClientSession.call_tool`), not a CLI; both criteria judged from the tool results.

## Self-check: implementer-deepen-first task, one run

Scratch copy of `evals/fixtures/quote-app-inline` at `/tmp/gh795/selfcheck`, committed on main, branch `implementer-t23`; PATH first: a `gh` stub logging argv (`issue view` fails as "issue not found", `issue comment` answers a URL) and a logging `herdr-say` stub. Task: `evals/role-transcripts/cases.json` `implementer-deepen-first`, verbatim. Command: `scripts/pi-role agents/implementer.md -p "<task>"`.

Commits, oldest first (`git log --reverse main..implementer-t23`):

```
3ab32c9 test(quote): pin discount-before-tax at the CLI
5c4fc9a refactor(rates): extract discount rule into app.rates
4a0d091 feat(rates): discount tiers 5/10/15% over 50/100/500 (#23)
```

1. `3ab32c9` touches only `tests/test_cli.py`: a pin of current behaviour at the CLI.
2. `5c4fc9a` touches only `src/`: the extract refactor, no behaviour change.
3. `4a0d091` adds the tiers and the tests at the new interface (`tests/test_discount.py` through `app.discount`).

gh log: one `gh issue view 23 ...` call, no `gh issue comment`. The implementer skipped the comment: "I couldn't add the seam list as a comment on #23 because the repo has no remote" (its report, below). Fix after this run: tdd Seams step 1 now says to run `issue-comment` even when reading the issue failed or the repo has no git remote, and to report only a comment that itself fails. Not rerun (the brief allows one run); the supervisor's eval run decides it.

Final message, verbatim:

````
Discount tiers for `app quote` (#23, quote-tiers) are done on branch `implementer-t23`, ending at commit 4a0d091. `just check` passes (lint, format, types, import contract, 11 tests).

Three commits, in order:
- **3ab32c9:** pins the current quote at the CLI: `uk 200.00:1 --json` gives discount 20.00, tax 36.00, total 216.00. This result is the same before and after the change.
- **5c4fc9a:** moves the discount rule unchanged into `app/rates.py` as `discount(subtotal)` and exports it from `app/__init__.py` so checkout can use it.
- **4a0d091:** adds the tier table `DISCOUNT_TIERS` (over 500 → 15%, over 100 → 10%, over 50 → 5%). The subtotal must be strictly over a threshold and the highest match wins. Adding a tier means adding a row. New tests cover the boundaries through `app.discount` (50.00 → 0, 100.00 → 5.00, 500.00 → 50.00, 600.00 → 90.00) and the ticket's two examples through `app quote`.

Running the real CLI:
- `uv run app quote uk 60.00:1 --json` shows discount "3.00", tax 11.40, total 68.40.
- `uk 600.00:1` shows discount "90.00", tax 102.00, total 612.00.
- `uk 50.00:1` shows discount "0", unchanged.
- `de 30.00:2` gives total 67.83.

**Why it's safe:** `discount()` in `app/rates.py` is the only place a discount is worked out. A repo-wide search for `DISCOUNT`, the rates and "tier" found nothing else. Quotes over 100.00 up to 500.00 come out the same as before, and the pin test proves it. I checked this by running the gate, the CLI and a script calling `app.discount` (150.00 → 15.00, 50.10 → 2.50, 500.01 → 75.00).

**Rounding:** The ticket doesn't say how to round, so I kept the existing rule. The discount rounds half to even, while tax rounds half up. So 5% of 50.10 is 2.50, not 2.51.

**Seam list not posted:** I couldn't add the seam list as a comment on #23 because the repo has no remote. The issue lookup returned "issue not found", so the ticket text in the brief was the only source. The two seams were:
1. **`app quote … --json`:** checks the wiring and that the discount comes off before tax; it doesn't check tier boundaries.
2. **`app.discount`:** checks the tier boundaries; it doesn't check the CLI wiring.

Declared repo skills loaded: python.
Evidence: none
Checks: none
Owner: src/app/rates.py: discount tiers (DISCOUNT_TIERS) | restated: none
Prior art: none
Validation: `just check` passed (11 tests); the git hook ran it again on each commit.
Blockers: none. No verify skill exists in this repo, so there was no feature map to update or drive. I did not push.
````
