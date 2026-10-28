---
name: reflect
description: Review the records a reflection brief names through three lenses and a synthesis, and return each durable gap as a finding routed to where its fix goes. Use when a reflection brief starts you.
---

# Reflect

Mine the records your brief names for durable gaps, then route each to where its fix goes.

You are one headless agent: you apply every lens and the synthesis yourself, in turn. You change no file, start no agent and ask no one for approval. One-offs are not learnings.

## 1. Read the records the brief names

The brief names the records to read: a lane's record and hand-off log, the director log's lines about it, the factory report's lines, and the transcripts (Pi session JSONL files) of the agents involved. Read only those, and what they cite inside the repository. A transcript is long: read it in slices (offset and limit), and grep it for the moments a lens asks about. Do not list or read other sessions' transcripts.

## 2. Apply the three lenses in turn

Read each lens template and apply it yourself to the records: `references/judgment-reviewer.md`, `references/tooling-reviewer.md`, `references/divergent-reviewer.md`. Where a template says transcript, read the records of step 1. Its parts about subagents, MCP lookups and skill catalogs do not apply: you have only read, grep, find and ls. Keep each lens's notes to yourself; they are inputs to step 3.

Answer each question of the brief's question list through the lenses: a question is a lens of its own, and every question gets an answer, a gap or none.

## 3. Synthesize

Apply the criteria of `references/synthesizer.md` to every note from step 2 (durability, specificity, existing-home-first, convergence, decision-changing, structural mechanism, already covered). What it would reject, drop. What it would accept or backlog is a finding.

## 4. Structural enforcement check

Route a finding that a command, check, metadata flag or runtime check would enforce more reliably to that structure, not to more prose or more review. See the **encode-lessons-in-structure** principle.

## 5. Output

Return the findings in the exact form your brief gives, and nothing the brief's parser would misread. Each finding names its class, the question it answers, its route (the role, skill, template, command or structure where its fix goes) and a summary citing its evidence (the file and line, or the transcript moment). No edit is proposed for approval and none is applied: the command that started you appends the findings.
