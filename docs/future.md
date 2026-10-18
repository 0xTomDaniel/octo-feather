# Future improvements

Not for the Martell take-home. Each item names what it would replace and what is still unverified.

## A2A instead of lane records and handoffs.jsonl

Replace octo-lite's lane record plus `<lane>.handoffs.jsonl` and the `herdr-say` text protocol with the A2A (Agent2Agent) protocol. Exo's working assumption, from memory of the spec and not checked on 2026-10-18: an A2A Task (id, status history, messages, artifacts) is roughly a lane record and its handoff log done properly, and A2A messages replace `herdr-say`. Verify against the current spec before designing. See ADR 0003.
