# Future improvements

Not for the Martell take-home. Each item names what it would replace and what is still unverified.

## A2A instead of lane records and handoffs.jsonl

Replace octo-lite's lane record plus `<lane>.handoffs.jsonl` and the `herdr-say` text protocol with the A2A (Agent2Agent) protocol. Exo's working assumption, from memory of the spec and not checked on 2026-10-18: an A2A Task (id, status history, messages, artifacts) is roughly a lane record and its handoff log done properly, and A2A messages replace `herdr-say`. Verify against the current spec before designing. See ADR 0003.

## Spec Chat wake provider registration

octo-lite's installer registered `herdr-wake` as Spec Chat's `wake` provider (`providers/wake.toml`). The port dropped the installer, so a spec review hand-off cannot wake a supervisor until that registration is done by hand or by a `just` recipe. Needed once spec-chat review hosting runs on the remote.

## octo-feather's own spec

`spec/domains/octo-lite.spec.html` is octo-lite's spec, still Claude and Linear. The role contracts cite its anchors (`#lane-record`, `#acceptance-receipt`, `#transport-*`). Rewrite it as `octo-feather.spec.html` once the rehearsal shows which parts survive.

## `just qc` and `just qa`

Names decided by Tom (round 8): `just qc` runs the Jev product judge on a target's product, `just qa` runs factory evals of the kit's own agents and loop. Both are stubs that exit 2. Neither runs inside `just check`, which stays deterministic and free; check-refs fails if a gate recipe calls them.

## Reviewer scope drift (gpt-6.1-sol)

Tom's caution: sol models tend to over-engineer and over-correct. The code reviewer must judge only against the ticket's acceptance criteria and the spec. `agents/code-reviewer.md` already covers part of this ("judge against the shaped scope and the spec, not against preference"; "block only on broken behavior or clearly over-built work"; "a finding that cannot name a consequence is a note"). Risk: Matt's `code-review` Standards axis asks for baseline smells, which invites findings outside the criteria. To verify: a rehearsal check, plus an eval case where an out-of-criteria finding must not block. Flagged only, not fixed.

## Finding lines in the specs branch

ADR 0020 adds a handoffs line `{"kind": "finding", "source", "class", "blocking", "summary"}` and the code reviewer's `class` tag. `spec/` on main is octo-lite's reference spec and stays untouched; the specs-v1 rewrite should define the finding line under `#handoff-fields`.
