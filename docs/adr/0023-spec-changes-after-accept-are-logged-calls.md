# Spec changes after Accept are logged calls the owner approves at merge

Supersedes the freeze and wording-only paragraphs of ADR 0021.

Specs are not perfect up front, and spec and code must never diverge. When a build teaches the factory that an accepted spec must change, the spec and the code change together in the lane and the work does not pause for a new Accept: the owner's original Accept stays the baseline. Every spec edit after Accept is a logged judgement call that the owner approves or denies at merge, with louder notice for a call that adds scope or weakens a criterion. The rules a call must pass, its loudness and the owner's decision are spec `#gates-spec-calls` (issue-lifecycle); the guard is criterion `issue-lifecycle#acceptance-call-guard`. Decided by Tom (owner), 2026-10-21, issue #58.

The guard is the gate, not the agents: `just check` diffs each spec against its status file's accepted commit and fails on any change no logged call names, so the record never rests on an agent reporting its own edit. The call log is a file beside the spec in the repo, so the owner reviews it in the pull request and its history is git's.

A spec with a live review row still gets spec-chat-review's reconnect scan before any edit (ADR 0021, finding 20): a pending hand-off is reconciled first.

## Considered options

- Accept freezes the spec, and a behavior change goes back to the owner for a fresh Accept (ADR 0021). Rejected: lanes stalled on re-review, and in the Quorum run every amend after registration voided the owner's real Accept.
- Agents report their own spec edits in the merge ask. Rejected: an edit nobody reported reaches main unseen.
- The call log in the lane's state directory. Rejected: the owner cannot review it in the pull request, and it is gone when the lane is archived.

## Consequences

- Only the supervisor edits a spec and logs the call; implementers and correctors ask it, and the code reviewer checks each call against the call rules.
- An owner denial is recorded with the role that made the call, so a role that overreaches gets its prompt fixed.
