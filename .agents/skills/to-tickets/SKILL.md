---
name: to-tickets
description: Break a plan, spec, or the current conversation into a set of tracer-bullet tickets, each declaring its blocking edges, published to the configured tracker (edges as text in one file per ticket locally, or native blocking links on a real tracker).
---

# To Tickets

Break a plan, spec, or conversation into a set of **tickets**: tracer-bullet vertical slices, each declaring the tickets that **block** it.

The issue tracker is the target's: read, file and close tickets only through the tracker skill's scripts.

## Process

### 1. Gather context

Work from whatever is already in the conversation context. If the user passes a reference (a spec path, an issue number or URL) as an argument, fetch it and read its full body and comments.

### 2. Explore the codebase (optional)

If you have not already explored the codebase, do so to understand the current state of the code. Ticket titles and descriptions should use the project's domain glossary vocabulary, and respect ADRs in the area you're touching.

Look for opportunities to prefactor the code to make the implementation easier. "Make the change easy, then make the easy change."

### 3. Draft vertical slices

Break the work into **tracer bullet** tickets.

<vertical-slice-rules>

- Each slice cuts a narrow but COMPLETE path through every layer (schema, API, UI, tests): vertical, NOT a horizontal slice of one layer
- A completed slice is demoable or verifiable on its own
- Each slice is sized to fit in a single fresh context window
- Any prefactoring should be done first

</vertical-slice-rules>

Give each ticket its **blocking edges**: the other tickets that must complete before it can start. A ticket with no blockers can start immediately.

**Wide refactors are the exception to vertical slicing.** A **wide refactor** is one mechanical change (rename a column, retype a shared symbol) whose **blast radius** fans across the whole codebase, so a single edit breaks thousands of call sites at once and no vertical slice can land green. Don't force it into a tracer bullet; sequence it as **expand–contract**. First expand: add the new form beside the old so nothing breaks. Then migrate the call sites over in batches sized by blast radius (per package, per directory), each batch its own ticket blocked by the expand, keeping CI green batch to batch because the old form still exists. Finally contract: delete the old form once no caller remains, in a ticket blocked by every migrate batch. When even the batches can't stay green alone, keep the sequence but let them share an integration branch that all block a final integrate-and-verify ticket; green is promised only there. Each ticket of the sequence carries the line `Expand-contract: expand`, `Expand-contract: migrate` or `Expand-contract: contract`: the only tickets allowed to end without a demo.

### 4. Quiz the user

Present the proposed breakdown as a numbered list. For each ticket, show:

- **Title**: short descriptive name
- **Blocked by**: which other tickets (if any) must complete first
- **What it delivers**: the end-to-end behaviour this ticket makes work

Ask the user:

- Does the granularity feel right? (too coarse / too fine)
- Are the blocking edges correct: does each ticket only depend on tickets that genuinely gate it?
- Should any tickets be merged or split further?

Iterate until the user approves the breakdown.

### 5. Publish the tickets to the configured tracker

Before publishing, check each drafted issue body with `octo-feather-lane ticket -` (the draft on stdin) from the target repo. It fails a draft that breaks a rule `octo-feather-lane --help` states for `ticket` (its criterion ids or owned rule, its demo, an `Expand-contract:` line), printing the class and the fix. It checks facts, not meaning: you judge that the demo shows the behavior What to build describes and that the ticket is a real vertical slice. Fix the draft as it says and rerun until it exits 0; never publish a draft that fails. A failure you cannot fix inside the approved breakdown (no criterion fits, no demo path exists) goes back to step 4.

Publish the approved tickets. **How** depends on the tracker; the tickets are the same either way, only the shape of the blocking edges changes:

- **Local files** → write one file per ticket under `.scratch/<feature-slug>/issues/<NN>-<slug>.md`, numbered from `01` in dependency order (blockers first). Each file's "Blocked by" lists the numbers/titles it depends on. Use the per-ticket file template below: one ticket per file, never a single combined file.
- **A real issue tracker (the tracker skill)** → publish one issue per ticket in dependency order (blockers first) so each ticket's blocking edges can reference real identifiers: the tracker skill's `issue-create`, with `--blocked-by` for each blocking ticket and `--parent` the lane's parent ticket, so each ticket is its sub-issue. No label: tracker writes are a ticket filed, commented on and moved to done; the tickets are agent-grabbable by construction.

After publishing sub-issues of a parent, run `octo-feather-lane tickets <parent key>`; it must exit 0.

Work the **frontier**: any ticket whose blockers are all done. For a purely linear chain that means top to bottom.

Do NOT close or modify any parent issue.

<local-ticket-template>

# <NN>: <Ticket title>

**What to build:** the end-to-end behaviour this ticket makes work, from the user's perspective, not a layer-by-layer implementation list.

**Blocked by:** the numbers/titles of the tickets that gate this one, or "None (can start immediately)".

**Status:** ready-for-agent

- [ ] Acceptance criterion 1
- [ ] Acceptance criterion 2

</local-ticket-template>

<issue-template>

## Parent

A reference to the parent issue on the tracker (if the source was an existing issue, otherwise omit this section).

## What to build

The end-to-end behaviour this ticket makes work, from the user's perspective, not layer-by-layer implementation. Name the command, URL or page the demo runs.

## Acceptance criteria

- [ ] <spec slug>#<anchor>: what proves the criterion this ticket serves (the anchor from the accepted spec, docs/specs/<spec slug>.spec.html)
- [ ] <spec slug>#<anchor>: another criterion it serves, if any
- [ ] demo: `<command>` and what it shows: the behaviour run through a public interface the product offers its users (its CLI, HTTP, UI, MCP or another public protocol) (a program the repo declares, or its runnable script when it has none), never the gate alone (`just check`) or a generic tool (`printf`, `echo`)

For one step of a wide refactor, replace the demo item with the line `Expand-contract: expand`, `migrate` or `contract`.

## Seams

Seam: <spec slug>#<anchor>: `<seam>` one line per seam a criterion's tests go at, set before any test (form and check: `octo-feather-lane --help`, seam); a seam set later: agents/supervisor.md, Briefs

## Blocked by

- A reference to each blocking ticket, or "None (can start immediately)". Omit this section when blockers were set as native edges.

</issue-template>

In either form, a ticket that needs infrastructure (the `code-review` skill, Verdict step, **Prior art**) names the capability and asks for prior art: "provide YAML config reading (prefer an existing library)", not "write a YAML parser".

In either form, avoid specific file paths or code snippets: they go stale fast. Exception: if a prototype produced a snippet that encodes a decision more precisely than prose can (state machine, reducer, schema, type shape), inline it and note briefly that it came from a prototype. Trim to the decision-rich parts, not a working demo, just the important bits.
