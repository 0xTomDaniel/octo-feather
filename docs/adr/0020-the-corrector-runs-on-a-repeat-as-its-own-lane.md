# The corrector runs on a repeat, as its own lane

`correct` is a factory QA process (`just qa` territory), not product QC (`just qc`), so it never runs inside a product lane. The director starts a correction lane against the target repo in two cases: (a) the owner corrects something at a gate (spec, QA evidence, merge), or (b) a code-review or QC finding falls into a class seen before, two or more occurrences in any lane. A correction lane is an ordinary lane (ADR 0019): parent issue, supervisor, one `corrector`, code review and its own small merge ask, so product lanes never wait on it. To make repeats countable, the code reviewer tags every finding with a short `class`, the supervisor writes each finding with its class as a `"kind": "finding"` line in the lane's hand-off log, and the director counts classes across lanes after each merge ask. A class that already has a correction-lane issue, open or closed, retriggers only on a finding line of that class dated after that issue closed. Decided by Tom (owner), 2026-10-19.

Baseline qc failures never trigger a correction lane. A baseline run (`just qc` on criteria already on main, outside a product lane's own diff) that fails a criterion has found a product gap, not an agent mistake: it opens a gap lane for that criterion, and the baseline lane logs it as `"kind": "gap"` (`spec`, `id`, `why`), never `"kind": "finding"`, so the director's class count (agents/director.md, Correction lanes) never sees it. Decided by Tom (owner), 2026-10-19 (finding 21).

## Considered options

- A corrector in every lane before code review. Rejected: it delays every product merge for factory work, and it runs blind, without a repeated mistake to aim at.

## Consequences

- implement-spec step 7 runs only the code reviewer; the `corrector` tab exists only in a correction lane; `agents/corrector.md` names its trigger and evidence.
- The hand-off log fields (spec `#handoff-fields`) include the finding line: `kind`, `source`, `class`, `blocking`, `summary`.
