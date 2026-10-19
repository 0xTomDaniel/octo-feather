# The accepted spec is the handoff

Brainstorming and shaping happen outside the factory. An owner chat (Exo or a fresh session) loads `spec-chat-shape` in the target repo, commits the spec on branch `spec/<slug>`, pushes it, and registers it with the review service under `--slug <spec slug>`; no issue exists yet. The owner presses Accept spec, and review-host's accepted registration (row `accepted = true`, `base` = the exact commit) is the only record. Kickoff: the owner tells the director "build <spec path>" (one spec or several); the director runs `octo-feather-accepted`, which reads every session's review-host registry, and refuses any spec not accepted at a commit present in the target repo, saying why. The director then cuts lanes (ADR 0019), files each lane's parent issue, branches each lane from the accepted commit, and records the acceptance receipt itself on each lane PR when it opens (owner action, date, spec path, commit, "Recorded by director"). The spec reaches main with the first lane that merges. The supervisor never shapes; a wording-only fix rides on the acceptance, and a behavior change gets a spec revision (`spec-chat-shape`, its only use there) whose review link goes up through the director before any merge ask. A work item whose behavior the spec on main already states goes straight to a lane. Decided by Tom (owner): the workflow on 2026-10-18, the handoff mechanics on 2026-10-19.

## Considered options

- The supervisor shapes inside its lane (octo-lite). Rejected: shaping is a conversation with the owner, and only the director talks to the owner (ADR 0015); a lane would exist before anyone knows how to cut it (ADR 0019).
- The spec PR merges to main first, carrying the receipt. Open on Tom's page; the default is a receipt on each lane PR.

## Consequences

- The supervisor's role file has no shaping, spec-issue publishing or receipt recording, and loads no shaping skills; the director's has the kickoff check and the receipt.
- `octo-feather-accepted` (tested in `just check`) reads Spec Chat's registry files directly, since review-host has no query command; a registry format change breaks it loudly.
- Spec Chat infers lanes from slug shape (docs/future.md, "Spec Chat assumes a lane-key workflow").
