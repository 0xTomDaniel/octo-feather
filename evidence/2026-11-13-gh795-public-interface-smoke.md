# gh795 round 3: public-interface smokes and deepen-first self-check

Smoke: agents/qc-judge.md run once below (b), driving an MCP-only fixture.
Smoke: agents/implementer.md .agents/skills/tdd/SKILL.md .skillfile/patches/skills/tdd/SKILL.md.patch .agents/skills/codebase-design/DEEPENING.md .skillfile/patches/skills/codebase-design/DEEPENING.md.patch run once below (self-check, the implementer-deepen-first task verbatim; the run read the patched tdd SKILL.md at its first wording, before the issue-comment sentence was sharpened).
Smoke: agents/supervisor.md .agents/skills/to-tickets/SKILL.md .skillfile/patches/skills/to-tickets/SKILL.md.patch run once below, (a) round 6 (the supervisor read the patched to-tickets SKILL.md in round 4's run; round 6 reran it on the declared-client route).
Removed: the tdd Seams paragraph's single-sentence deepen-first ("deepen it first as its own step: pin current behavior, deepen the module, then test at the new interface"), replaced by four ordered steps each ending on a done condition; implementer.md's dense seam bullet, replaced by the same order.

Issue #795, ticket #796, branch gh795-796. Review round 3 (`/tmp/gh795/review3.md`): implementer-deepen-first failed 3 of 3 runs (QA run 20261112T234850Z-2ce373).

## Why the old wording did not steer

Transcripts of QA run 20261112T234850Z-2ce373 current/run-1 and run-2: each implementer read `tdd` SKILL.md, then wrote a test at the new interface, saw it red, then created `src/app/pricing.py` with the new behaviour and committed once. The tdd skill put deepen-first as one clause mid-paragraph, while its loop rules said "Red before green" and "Refactoring is not part of the loop": the agent took creating the new module as part of green. `DEEPENING.md` was never read. Run 1 never read the tracker skill, so never posted the comment.

## Fixture: MCP-only target

`/tmp/gh795/mcpfx` (throwaway git repo, head `abf59bf`): Python package `quotemcp`, `mcp` SDK pinned in `uv.lock`, `[project.scripts] quote-mcp` a stdio MCP server with tool `quote(region, subtotal)`. `AGENTS.md`: "Its only public interface is the MCP server `quote-mcp` ... There is no CLI, HTTP API or UI for users." Spec `docs/specs/quote.spec.html`, criteria `acceptance-quote-tax`, `acceptance-quote-de`, each "When an MCP client calls tool `quote` ...".

## (a) Ticket demo through MCP

### Round 3: blocked by the ticket check

The draft demo a supervisor or `to-tickets` would write for the MCP interface, run through the ticket check before any role run:

```
stdin: class: layer-only-ticket: demo runs no surface the repo declares (`npx -y @modelcontextprotocol/inspector@0.17.2 --cli uv run quote-mcp --method tools/call --tool-name quote --tool-arg region=de --tool-arg subtotal=100.00`: @modelcontextprotocol/inspector@0.17.2 is not an executable the repo tracks); fix: make the demo a backticked command through the repo's own public surface (ADR 0009): a program the repo declares (a tracked executable such as scripts/NAME or bin/NAME, a justfile recipe other than check/integrate/qc/qa, a package.json bin or pyproject [project.scripts] entry, e.g. `uv run app hello Ada`, or a tracked script run by its interpreter, e.g. `python harness.py`, only as ADR 0002's fallback), an HTTP request (`curl https://...`), or a UI driver run (`npx playwright test ...`); not printf, echo or another generic tool; or, for a command this ticket creates, declare it exactly with `Creates: `<path>``, form: octo-feather-lane --help (ticket), the demo running that path; or, for one step of a wide refactor, add the line `Expand-contract: expand|migrate|contract`
exit 1
```

The check accepts only a program the repo declares, an HTTP request or a UI driver, so a standard MCP client (the MCP Inspector CLI) is refused. Per the round 3 brief, stopped and reported to the supervisor as a script gap; no supervisor or to-tickets run.

### Round 4: check extended, supervisor run (superseded: that Inspector branch was deleted in round 6, review round 5 proxy-check)

Commit `6705c072` extends `octo-feather-lane ticket`'s demo surface rule: the MCP project's official client, `@modelcontextprotocol/inspector` with `--cli`, passes when its server is an http(s) URL or a command the rule accepts as the repo's own program. The same draft, in a copy of the fixture (`/tmp/gh795/mcpdemo`), with this branch's script:

```
stdin: ok
exit 0
```

Supervisor, one run, from a copy `/tmp/gh795/mcpsup`, PATH first: logging `gh` and `herdr-say` stubs, then this branch's `scripts/`:

```
scripts/pi-role agents/supervisor.md -p "Lane gh30 in this repo (/tmp/gh795/mcpsup, branch main). Draft one ticket, for criterion quote#acceptance-quote-de (docs/specs/quote.spec.html), as you would file it, but do not file it: there is no tracker, no Herdr and no worker in this run, so skip every issue-create, herdr-say and spawn step. Check the draft with octo-feather-lane ticket before you stop. Your final message: the draft verbatim, then the check command you ran and its output verbatim."
```

Pi session `01a1d267-d8f7-779a-a298-710581616527` (`~/.pi/agent/sessions/--tmp-gh795-mcpsup--/`). It read the patched `.agents/skills/to-tickets/SKILL.md`, ran the inspector demo against the server before drafting, and checked the draft with the branch's `octo-feather-lane` (first on PATH). No gh or herdr-say call. Final message, verbatim:

````
Here is the draft ticket. The check passed (exit 0). Nothing was filed, sent or spawned.

Before you file it, two things:
- **The behaviour already works on main.** The server already has a `de` rate. I ran the demo command against the current code and it returned subtotal `100.00`, tax `19.00`, total `119.00`, isError false. So this ticket's job is to prove the criterion and lock it in with a test, not to add the feature.
- **The status file is missing.** `docs/specs/quote.status.json` does not exist, and `just qc` can't mark this criterion built without it. The repo also has no tests yet.

I left out the `## Parent` section because there is no tracker and so no parent key to link to.

**Draft** (saved at `/tmp/gh30-draft/ticket.md`):

```
## What to build

An MCP client calling tool `quote` on the `quote-mcp` server (stdio) with region `de` and subtotal `100.00` gets tax `19.00` and total `119.00` (German VAT 19%). Main already returns this from the `de` rate; this ticket proves it end to end through the MCP interface and locks it in with a regression test that drives the server over stdio as a client would, so the `de` path cannot silently regress. Use the MCP SDK's own client (prefer the existing `mcp` dependency) for the test, not a hand-rolled protocol. Keep the `uk` quote (quote#acceptance-quote-tax) unchanged.

## Acceptance criteria

- [ ] quote#acceptance-quote-de: tool `quote` called over MCP stdio with region `de`, subtotal `100.00` returns tax `19.00` and total `119.00`; a test asserts this through an MCP client session and passes
- [ ] demo: `npx -y @modelcontextprotocol/inspector --cli uv run quote-mcp --method tools/call --tool-name quote --tool-arg region=de --tool-arg subtotal=100.00` prints structuredContent with subtotal `100.00`, tax `19.00`, total `119.00` and isError false

## Blocked by

- None (can start immediately)
```

**Check command** (run from `/tmp/gh795/mcpsup`):

```
octo-feather-lane ticket - < /tmp/gh30-draft/ticket.md; echo "exit=$?"
```

**Output:**

```
stdin: ok
exit=0
```
````

The draft's demo drives the repo's MCP server through the official MCP client, not a CLI, HTTP or UI, and `octo-feather-lane ticket -` passes it.

### Round 6: declared client, supervisor run

Commit `a8af2287` deletes the round 4/5 Inspector branch (docs/adr/0008 stop rule); an MCP demo now runs a client the repo declares, by the existing exact rule. Fixture copy `/tmp/gh795/mcpsup6` adds a tracked `justfile` recipe, the product's MCP client:

```
mcp-call *args:
    npx -y @modelcontextprotocol/inspector@0.17.2 --cli uv run quote-mcp {{args}}
```

and an `AGENTS.md` Commands line naming it. The check on a draft through the recipe, and on a direct Inspector demo:

```
stdin: ok
exit 0
```

```
stdin: class: layer-only-ticket: demo runs no surface the repo declares (`npx -y @modelcontextprotocol/inspector@0.17.2 --cli uv run quote-mcp --method tools/call --tool-name quote --tool-arg region=de --tool-arg subtotal=100.00`: @modelcontextprotocol/inspector@0.17.2 is not an executable the repo tracks); fix: make the demo a backticked command through the repo's own public surface (ADR 0009): a program the repo declares (a tracked executable such as scripts/NAME or bin/NAME, a justfile recipe other than check/integrate/qc/qa, a package.json bin or pyproject [project.scripts] entry, e.g. `uv run app hello Ada`, or a tracked script run by its interpreter, e.g. `python harness.py`, only as ADR 0002's fallback), an HTTP request (`curl https://...`), or a UI driver run (`npx playwright test ...`); a demo through MCP or another public protocol runs a client the repo declares, e.g. a justfile recipe `mcp-call` that runs the protocol's client (for MCP, `npx @modelcontextprotocol/inspector --cli ...`) against the repo's server; not printf, echo or another generic tool; or, for a command this ticket creates, declare it exactly with `Creates: `<path>``, form: octo-feather-lane --help (ticket), the demo running that path; or, for one step of a wide refactor, add the line `Expand-contract: expand|migrate|contract`
exit 1
```

Supervisor, one run, same brief as round 4 with the path `/tmp/gh795/mcpsup6`, PATH first: logging `gh` and `herdr-say` stubs, then this branch's `scripts/`. Pi session `01a1d2b5-a9a6-779d-a8a5-3c8e2f6521a4` (`~/.pi/agent/sessions/--tmp-gh795-mcpsup6--/`). It read `justfile`, ran the recipe against the server, drafted, and ran `octo-feather-lane ticket -` once: `stdin: ok`. It wrote no direct npx demo, so no refusal arose; the fix text was not exercised by the role. No gh or herdr-say call. Final message, verbatim:

````
I drafted the ticket and it passed the check. I filed nothing, sent no messages and started no workers.

Two things to know before it's filed:
- **Main already meets this criterion.** I ran the demo command and the server returned tax `19.00` and total `119.00` for region `de`, subtotal `100.00` (`isError: false`). So this ticket would mostly confirm existing behaviour rather than add any.
- **The lane is missing a required input.** There is no `docs/specs/quote.status.json` on main, and `just qc` needs it to mark criteria as built.

I set the parent to `#30` only because the lane is called gh30; I haven't confirmed that issue exists.

**Draft:**

```
## Parent

#30

## What to build

An MCP client quotes a German order: calling tool `quote` on the `quote-mcp` server (stdio) with region `de` and subtotal `100.00` returns tax `19.00` and total `119.00`, at the same decimal precision as the uk quote. The demo runs through the repo's declared MCP client, `just mcp-call` (the MCP Inspector CLI against `quote-mcp`).

## Acceptance criteria

- [ ] quote#acceptance-quote-de: tool `quote` with region `de`, subtotal `100.00` returns tax `19.00` and total `119.00`
- [ ] demo: `just mcp-call --method tools/call --tool-name quote --tool-arg region=de --tool-arg subtotal=100.00` prints a result with tax `19.00` and total `119.00`

## Blocked by

- None (can start immediately)
```

**Check command** (run from `/tmp/gh795/mcpsup6`, with the draft saved at `/tmp/gh30-draft/ticket.md`):

```
octo-feather-lane ticket - < /tmp/gh30-draft/ticket.md; echo "exit=$?"
```

**Output:**

```
stdin: ok
exit=0
```
````

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
