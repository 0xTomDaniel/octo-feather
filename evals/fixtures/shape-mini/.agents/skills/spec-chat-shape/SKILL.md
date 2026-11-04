---
name: spec-chat-shape
description: Shape a feature prompt into a canonical Spec Chat HTML spec and any needed ADRs, committed locally. Also use for any existing-spec review that materially changes behavior or information architecture. Use spec-chat-review alone only for questions and atomic corrections.
---

# Spec Chat Shape

(A stand-in of Spec Chat's skill for the octo-feather kit's evals: its steps, without Spec Chat's runtime.)

1. List every spec in `docs/specs/` and ADR in `docs/adr/`, and read the ones that own the behavior.
2. Put the behavior in the spec that owns it; a new spec only for a new part of the system, never one named after a change.
3. Write what the result must do: stories (`data-user-story`), behavior paragraphs with a `data-anchor` each, and one `data-acceptance-criterion` per observable outcome, Given/When/Then. Nothing outdated: no current state, history or ticket links. A real design choice left to the human is an open `TBD` paragraph naming the options.
4. A hard-to-reverse decision gets an ADR in `docs/adr/`.
5. On branch `spec/<slug>`, commit the spec and ADRs locally. Never push, open a pull request or touch a ticket.
