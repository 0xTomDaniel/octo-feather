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
