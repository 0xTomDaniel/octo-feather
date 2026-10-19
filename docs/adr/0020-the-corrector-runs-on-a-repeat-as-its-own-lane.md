# The corrector runs on a repeat, as its own lane

`correct` is a factory QA process (`just qa` territory), not product QC (`just qc`), so it no longer runs inside every lane before code review. The director starts a correction lane against the target repo in two cases: (a) the owner corrects something at a gate (spec, QA evidence, merge), or (b) a code-review or QC finding falls into a class seen before, two or more occurrences in any lane. A correction lane is an ordinary lane (ADR 0019): parent issue, supervisor, one `corrector`, code review and its own small merge ask, so product lanes never wait on it. To make repeats countable, the code reviewer tags every finding with a short `class`, the supervisor writes each finding with its class as a `"kind": "finding"` line in the lane's handoffs JSONL, and the director counts classes across lanes after each merge ask. Decided by Tom (owner), 2026-10-19 08:15 MDT; recorded 2026-10-19 08:20 MDT.

## Considered options

- A corrector in every lane before review (the block of 2026-10-18). Rejected: it delays every product merge for factory work, and it runs blind, without a repeated mistake to aim at.

## Consequences

- Removed from implement-spec step 7 (patch), `agents/supervisor.md` and the per-merge tab list; `agents/corrector.md` now names its trigger and evidence.
- `spec/` (octo-lite's reference spec) is unchanged; the finding line belongs under `#handoff-fields` in the specs-v1 rewrite (docs/future.md).
