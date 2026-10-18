# Future improvements

Not for the Martell take-home. Each item names what it would replace and what is still unverified.

## A2A instead of lane records and handoffs.jsonl

Replace octo-lite's lane record plus `<lane>.handoffs.jsonl` and the `herdr-say` text protocol with the A2A (Agent2Agent) protocol. Exo's working assumption, from memory of the spec and not checked on 2026-10-18: an A2A Task (id, status history, messages, artifacts) is roughly a lane record and its handoff log done properly, and A2A messages replace `herdr-say`. Verify against the current spec before designing. See ADR 0003.

## Spec Chat wake provider registration

octo-lite's installer registered `herdr-wake` as Spec Chat's `wake` provider (`providers/wake.toml`). The port dropped the installer, so a spec review hand-off cannot wake an owner until that registration is done by hand or by a `just` recipe. Needed once spec-chat review hosting runs on the remote.

## octo-feather's own spec

`spec/domains/octo-lite.spec.html` is octo-lite's spec, still Claude and Linear. The role contracts cite its anchors (`#lane-record`, `#acceptance-receipt`, `#transport-*`). Rewrite it as `octo-feather.spec.html` once the rehearsal shows which parts survive.
