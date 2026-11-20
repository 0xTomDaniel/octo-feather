# The owner gates decisions, not merges

Every merge was the owner's gate. Of 15 merge asks on 18 and 19 November 2026, 7 held nothing only the owner could decide, and the owner's approval of PR #1023 (review, CI and the gate all green) did not stop it killing an agent: reading a green merge ask adds no proof. So a merge waits for the owner only when its merge ask holds something only the owner can decide, and the merge ask check sorts that from the lane's own records, never an agent: see [gates-list](../specs/issue-lifecycle.spec.html#gates-list) and [gates-tiers](../specs/issue-lifecycle.spec.html#gates-tiers). Everything else merges and reaches the owner in a daily digest he can veto. With the owner no longer the brake on model use, lane start reads the Claude account's own weekly usage and refuses a new lane before the week can run out: [lanes-start](../specs/issue-lifecycle.spec.html#lanes-start). Decided by Tom (owner), 2026-11-19 and 2026-11-20. This supersedes ADR [0021](0021-the-accepted-spec-is-the-handoff.md) where it has the owner approve every merge and every spec call at merge, and ADR [0031](0031-a-spec-pr-merges-like-a-lane-pr.md) where it keeps the spec PR's merge gate the owner's.

## Considered options

- The director sorts each ask by reading it. Rejected: the director's reading is prose nothing checks, and on 19 November it sent two asks to the owner that held only his own ruling written down and a one-line pointer.
- Paths of the kit that always wait for the owner (agent launch, shared state, the gate). Rejected by the owner: he would catch nothing there, as #1023 showed; a risky change is proven by the gate and the product judge. A repository can still name paths in its code owners file where the question is the owner's, such as billing.
- A weekly dollar budget the owner names, counted from the spend ledger. Rejected by the owner: the ledger's dollars are not the account's allowance; the provider reports the share of the weekly limit used, and the factory keeps a reserve of it.
- A model deciding the tier or the brake. Rejected: both are facts the records and the provider already state.

## Consequences

- A merge ask the owner never saw can land a mistake; the digest and the veto, which opens a lane, are how he reaches it within a day.
- A ruling the owner gives must be written where a call can link it, or the call waits for him again.
- Lane start depends on the model route passing the provider's usage headers through; without one the brake runs on the week's last reading carried forward, and with none this week it is off.
- Until the kit's watchdog exists, nothing resumes lane starts after the weekly reset by itself.
