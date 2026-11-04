# gh530: principle-build-the-lever read at the moment it applies

Change: the skill's description (via `.skillfile/patches/skills/principle-build-the-lever/SKILL.md.patch`) names the repeat moment; the skill-load step line of agents/director.md, agents/supervisor.md and agents/corrector.md names that role's repeat moment. No skill text inlined (owner ruling 2026-11-04, #520).

Smoke: .agents/skills/principle-build-the-lever/SKILL.md agents/director.md agents/supervisor.md agents/corrector.md, skill-triggers `dir-lever-teardown-again`: run 20261104T194613Z-140cfb, baseline origin/main ea7d779 FAIL, kit 780ea97 (cases only, before the change) FAIL. After-change runs: below.

Removed: nothing.

## Held-out cases (frozen before any run of them)

- dir-lever-event-lines
- dir-lever-near-verify-sha
- sup-lever-status-rows
- sup-lever-near-finding-logged
- cor-lever-restated-comments
- cor-lever-near-owner

Train: dir-lever-teardown-again, dir-lever-near-one-ruling, sup-lever-record-merge-ask, sup-lever-near-set-waiting, cor-lever-restated-sites, cor-lever-near-one-pointer.

## Real moments the cases come from

- dir-lever-teardown-again: director.handoffs.jsonl:812,817,840, lanes gh206, gh421, gh436 torn down by hand in two days while post-merge step 5 was blocked (#439).
- dir-lever-event-lines: director.handoffs.jsonl:961, manual-director-event-recording: hand-written appends, one timestamp the report could not read.
- dir-lever-near-one-ruling: director.handoffs.jsonl:875, issue 127: one owner ruling recorded once.
- dir-lever-near-verify-sha: director.handoffs.jsonl:218, finding 57: one reported sha verified at source.
- sup-lever-record-merge-ask: gh436.handoffs.jsonl:27, manual-lane-bookkeeping: JSONL events hand-built, waiting_on and last_handoff_at edited apart.
- sup-lever-status-rows: gh127.handoffs.jsonl:15, status-tool-gap: eight planned criteria added to a status file by hand.
- sup-lever-near-set-waiting: gh436.handoffs.jsonl:27: the single waiting_on edit.
- sup-lever-near-finding-logged: gh439.handoffs.jsonl:13: whether a round 1 finding was already caught.
- cor-lever-restated-sites: gh118.handoffs.jsonl:74-83, review rounds 6-7: corrector-gh118 pointed restatements site by site, round 7 found more.
- cor-lever-restated-comments: gh121.handoffs.jsonl:25-44, PR 140 rounds 461779c, 6101554, 083a2f5: comments, docstrings, test headers restating owned rules, missed sites each round (fixer an implementer; the same fix-round moment a corrector meets).
- cor-lever-near-one-pointer: gh127.handoffs.jsonl:94, final review c5da94e: one restatement, one pointer.
- cor-lever-near-owner: gh160.handoffs.jsonl:5-16, duplicated-rule rounds: which file owns the rule, a read only.

Fixture `rules-restated-sites`: no existing fixture holds more than 2 restatements; the real moments had 4 to 6 files.
