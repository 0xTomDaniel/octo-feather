# gh644 / #1094: supervisor lists and loads codebase-design and tdd

Change: agents/supervisor.md `skills:` adds `codebase-design` and `tdd`; its Delivery load list gains one entry: before cutting tickets or writing a brief whose work places or moves a test (a test port, a review fix that moves one), both. No new prose block (owner ruling 2026-11-19 #644). Cases in evals/skill-triggers, every task worded as a real lane ticket or brief, none naming design, seam, interface or module boundary (#644: the implementer's design-worded cases passed 3/3 while real reach was 0 of 19):

- train: sup-design-port-test (brief for a test port), sup-tdd-port-test (cut tickets for a test port), sup-testplace-near-docs (near miss: brief for a docs-only ticket).
- held-out: sup-design-review-fix (fix brief: a test asserts on a private cli helper), sup-tdd-review-fix (fix brief: the only test sits in e2e and monkeypatches the read), sup-testplace-near-status (near miss: a status read of notes/handoffs.jsonl).
- Should cases graded skill_read of their named skill; near misses skill_not_read of both.

Smoke: agents/supervisor.md (sup-design-*, sup-tdd-*, sup-testplace-near-* below)
Removed: nothing; the change adds two skills and one load-step entry. Incident: #644 (supervisor offered neither skill though it writes the tickets and agrees the `Seam:` lines), owner ruling 2026-11-19.

Base: origin/main 1b21f8da. Current: a045ee45 (role edit and cases). Runs serial in lane gh644's eval slot, runs=1 per case (pilot; pinned reruns later by the supervisor).

## Runs

Pending the eval grant (first attempt refused, exit 75: lane gh644 held no grant, holder gh901).

1. Smoke, `scripts/octo-feather-qa --suite skill-triggers --case sup-design-port-test --baseline origin/main`: pending.
2. The other five, once each, `--baseline origin/main`: pending.
3. Demo, `scripts/octo-feather-qa --suite skill-triggers --case sup-design-port-test --case sup-tdd-port-test`: pending.
