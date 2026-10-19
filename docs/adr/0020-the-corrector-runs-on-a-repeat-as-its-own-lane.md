# The corrector runs on a repeat, as its own lane

`correct` is a factory QA process (`just qa` territory), not product QC (`just qc`), so it never runs inside a product lane. The director starts a correction lane against the target repo in two cases: (a) the owner corrects something at a gate (spec, QA evidence, merge), or (b) a code-review or QC finding falls into a class seen before, two or more occurrences in any lane. A correction lane is an ordinary lane (ADR 0019): parent issue, supervisor, one `corrector`, code review and its own small merge ask, so product lanes never wait on it. To make repeats countable, the code reviewer tags every finding with a short `class`, the supervisor writes each finding with its class as a `"kind": "finding"` line in the lane's hand-off log, and the director counts classes across lanes after each merge ask. Decided by Tom (owner), 2026-10-19.

## Considered options

- A corrector in every lane before code review. Rejected: it delays every product merge for factory work, and it runs blind, without a repeated mistake to aim at.

## Consequences

- implement-spec step 7 runs only the code reviewer; the `corrector` tab exists only in a correction lane; `agents/corrector.md` names its trigger and evidence.
- The hand-off log fields (spec `#handoff-fields`) include the finding line: `kind`, `source`, `class`, `blocking`, `summary`.
