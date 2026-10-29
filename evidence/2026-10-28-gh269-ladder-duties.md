# gh269: the ladder governs duties; prose-duty blocks in review; build-the-lever and encode-lessons as design habits

Change: docs/adr/0008 corrected in place (Duties: the mechanical-duty rule and its three tiers, owner ruling #269); code-review skill Verdict step blocks class `prose-duty` (patch + materialized); pstack principle-build-the-lever vendored (cursor/plugins@0b8e952, Pi patch) and listed for director, supervisor, corrector; principle-encode-lessons-in-structure listed for director, supervisor, implementer, each role saying when to load it (writing or changing a duty, role or skill).

Smoke: .agents/skills/code-review/ .skillfile/patches/skills/code-review/SKILL.md.patch (reviewer-prose-duty-blocks below)
Smoke: agents/director.md (dir-encode-route-ruling below)
Smoke: agents/supervisor.md (sup-encode-brief-demo below)
Smoke: agents/implementer.md (impl-encode-release-duty below)
Smoke: agents/corrector.md .agents/skills/principle-build-the-lever/ .skillfile/patches/skills/principle-build-the-lever/SKILL.md.patch (cor-lever-call-sites below)
Removed: nothing deleted. Incident (#269, owner correction 2026-10-28): mechanical duties (teardown order, review registration slug/base, load quotas, lane-log writes, main-moved broadcasts, waking parked lanes) stayed role prose and failed quietly (owner-caught findings, director workarounds #205, #206, #253).

Base: 2b2fab5 (`--kit-ref 2b2fab5`). One run per case per commit; single samples, no variance claim. Runs serial, `just qa --case <id>`; artifacts under the qa state dir, by run id.

1. reviewer-prose-duty-blocks, base, run 20261028T024253Z-442fa0 (smoke, first run):
   `FAIL role-transcripts/reviewer-prose-duty-blocks: declared_includes blocking: no entry with {"path": "agents/worker.md", "class": "prose-duty"} in [{"path": "agents/worker.md", "class": "misplaced-rule"}] [stop: exit, 19 tool calls, 53.5 s] [kit 2b2fab5ca2b336adc7d6c0aa8d35f65ca534231a]`
2. reviewer-prose-duty-blocks, head (uncommitted working tree over 2b2fab5), run 20261028T024354Z-7c65a1:
   `PASS role-transcripts/reviewer-prose-duty-blocks: declared_includes blocking: holds {"path": "agents/worker.md", "class": "prose-duty"} [stop: exit, 22 tool calls, 50.9 s] [kit 2b2fab5ca2b336adc7d6c0aa8d35f65ca534231a]`
3. reviewer-prose-duty-blocks, head e2ab7d8 (committed), run 20261028T025550Z-cd05b3:
   `PASS role-transcripts/reviewer-prose-duty-blocks: declared_includes blocking: holds {"path": "agents/worker.md", "class": "prose-duty"} [stop: exit, 22 tool calls, 56.8 s] [kit e2ab7d8da5b1c58ae97ccdb4ddbb5ab382a678b4]`

Role skill loads, one should-trigger train case per changed role, base 2b2fab5 then head e2ab7d8:

4. dir-encode-route-ruling (agents/director.md): base run 20261028T025108Z-c4f983 `FAIL ... skill_read principle-encode-lessons-in-structure: no load ... in 12 tool calls [stop: max_tool_calls]`; head run 20261028T025205Z-ef926d `PASS ... loaded at tool call 2 of 4 [stop: decided, 4 tool calls, 12.0 s]`.
5. sup-encode-brief-demo (agents/supervisor.md): base run 20261028T025218Z-286bed `FAIL ... no load ... in 7 tool calls [stop: exit]`; head run 20261028T025304Z-d9f2fa `PASS ... loaded at tool call 3 of 5 [stop: decided, 5 tool calls, 8.8 s]`.
6. impl-encode-release-duty (agents/implementer.md): base run 20261028T025313Z-f4df99 `FAIL ... no load ... in 8 tool calls [stop: exit]`; head run 20261028T025404Z-83d510 `PASS ... loaded at tool call 2 of 2 [stop: decided, 2 tool calls, 9.3 s]`.
7. cor-lever-call-sites (agents/corrector.md, principle-build-the-lever): base run 20261028T025414Z-8786ea `FAIL skill_read principle-build-the-lever: no load ... in 12 tool calls [stop: max_tool_calls]`; head run 20261028T025537Z-ec58d3 `PASS ... loaded at tool call 3 of 5 [stop: decided, 5 tool calls, 12.0 s]`.

8. sup-lever-finding-lines (agents/supervisor.md, principle-build-the-lever), review round 1 at ab15095: base run 20261028T032654Z-ce4bf5 `FAIL skill_read principle-build-the-lever: no load ... in 12 tool calls [stop: max_tool_calls, 12 tool calls, 43.3 s] [kit 2b2fab5]`; head run 20261028T032738Z-93bb73 `PASS ... loaded at tool call 4 of 4 [stop: decided, 4 tool calls, 9.0 s] [kit ab15095]`. Its first wording, sup-lever-reformat-drafts (train), failed at base (20261028T032458Z-552f4a) and at head (20261028T032541Z-29f608): the supervisor found notes/tickets.md holds no drafts, so the task had no work; reworded to a task the fixture supports (notes/handoffs.jsonl finding lines) before its next run.

Director build-the-lever: no dedicated director case ran (dir-lever-* owed). Observed incidentally: head run 20261028T025205Z-ef926d (dir-encode-route-ruling, run 4) holds a complete read tool result of .agents/skills/principle-build-the-lever/SKILL.md at its patched content (the docs/adr/0008 Duties line included), alongside encode-lessons.

Caveat: every held-out and near-miss case, and dir-lever-*, are owed (docs/owed-evals/269.md), unrun. The code-reviewer role file is unchanged; its skill change is smoked by runs 1 to 3.
