# Future improvements

Not for the Martell take-home. Each item names what it would replace and what is still unverified.

## A2A instead of lane records and handoffs.jsonl

Replace octo-lite's lane record plus `<lane>.handoffs.jsonl` and the `herdr-say` text protocol with the A2A (Agent2Agent) protocol. Exo's working assumption, from memory of the spec and not checked on 2026-10-18: an A2A Task (id, status history, messages, artifacts) is roughly a lane record and its handoff log done properly, and A2A messages replace `herdr-say`. Verify against the current spec before designing. See ADR 0003.

## Spec Chat wake provider registration

octo-lite's installer registered `herdr-wake` as Spec Chat's `wake` provider (`providers/wake.toml`). The port dropped the installer, so a spec review hand-off cannot wake a supervisor until that registration is done by hand or by a `just` recipe. Needed once spec-chat review hosting runs on the remote.

## octo-feather's own spec

`spec/domains/octo-lite.spec.html` is octo-lite's spec, still Claude and Linear. The role contracts cite its anchors (`#lane-record`, `#acceptance-receipt`, `#transport-*`). Rewrite it as `octo-feather.spec.html` once the rehearsal shows which parts survive.

## Hard limit on which agents a supervisor pane may launch

`allowedAgents: code-reviewer` binds only when a role runs as a pi-subagents child. In a pane the supervisor could launch a builtin (scout, worker, delegate, the claude/codex runners). Options: a pi-subagents setting such as `subagents.disableBuiltins` passed to pane sessions, or a small patch. See docs/adr/0013.

## Spec Chat skills for the supervisor

octo-lite's supervisor listed `spec-chat-shape` and `spec-chat-review`, which live in the Spec Chat peer repo. They were dropped from `agents/supervisor.md` because nothing provides them on the remote; add them to its `skills` and `skillPath` once Spec Chat is installed there.

## Jev QA recipe (name pending)

Jev capture, replay and judging stay out of `just check`, which runs only deterministic checks (Tom, 2026-10-18). They get their own `just` recipe, name not chosen yet, run by the supervisor before a merge ask. `just check` fails if the justfile mentions it.

## Integrator model

Tom has not chosen the integrator's model yet; `agents/integrator.md` still carries the earlier proposal (gpt-6.1-sol medium).

## Reviewer scope drift (gpt-6.1-sol)

Tom's caution: sol models tend to over-engineer and over-correct. The code reviewer must judge only against the ticket's acceptance criteria and the spec. `agents/code-reviewer.md` already covers part of this ("judge against the shaped scope and the spec, not against preference"; "block only on broken behavior or clearly over-built work"; "a finding that cannot name a consequence is a note"). Risk: Matt's `code-review` Standards axis asks for baseline smells, which invites findings outside the criteria. To verify: a rehearsal check, plus an eval case where an out-of-criteria finding must not block. Flagged only, not fixed.

## pi-subagents weight

v0.79.1 is 15 MB with about 114k lines of JS, around 14 subsystems (missions, workflows, watchdog, intercom, tui, inspectors, policy, profiles and others) and 5 runtime dependencies. It released 0.57 to 0.79 in about 7 weeks (two releases on 10-17). It runs in-process, adds 2 skills and 6 prompts to every session that loads it, and ships claude/codex/cursor runner agents. Its Herdr placement cannot target our workspaces or tabs. Option: keep the frontmatter format (docs/adr/0013) and replace the package with `pi-role` plus a small child launcher. Revisit after Thursday.

## Headless children through pi-role (test after Thursday)

Test whether  (or ) can stand in for pi-subagents as the launcher for headless children: the code reviewer,  and a judge. Pass if the child gets its role's model, thinking, tool allowlist and skills, its final message comes back to the supervisor intact, cost is visible, and a supervisor can run it from a pane with no extension loaded. If it passes, remove the pinned pi-subagents package (, , the  tool and  in role files) and keep the frontmatter format (docs/adr/0013).

## tdd pin bump to Matt 49dd158

Blocked: octo-lite's seam-gate patch does not apply to Matt's 49dd158  (hunk 1 fails at line 19). Upstream rewrote that paragraph (asks for a note per seam and calls a design skill when the interface is in question) and replaced em dashes. The pin stays at ed37663 until the patch is rewritten against 49dd158, which belongs with the block 6 tdd patch (integration/E2E seams only).
