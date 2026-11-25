# merge-tiers

Criteria:

- [issue-lifecycle#acceptance-tier-one](../../../../docs/specs/issue-lifecycle.spec.html#acceptance-tier-one)
- [issue-lifecycle#acceptance-tier-spec-pr](../../../../docs/specs/issue-lifecycle.spec.html#acceptance-tier-spec-pr)
- [issue-lifecycle#acceptance-tier-failed](../../../../docs/specs/issue-lifecycle.spec.html#acceptance-tier-failed)
- [issue-lifecycle#acceptance-tier-order-waits](../../../../docs/specs/issue-lifecycle.spec.html#acceptance-tier-order-waits)
- [issue-lifecycle#acceptance-tier-clarify](../../../../docs/specs/issue-lifecycle.spec.html#acceptance-tier-clarify)
- [issue-lifecycle#acceptance-tier-adds](../../../../docs/specs/issue-lifecycle.spec.html#acceptance-tier-adds)
- [issue-lifecycle#acceptance-tier-weakens](../../../../docs/specs/issue-lifecycle.spec.html#acceptance-tier-weakens)
- [issue-lifecycle#acceptance-tier-ruled](../../../../docs/specs/issue-lifecycle.spec.html#acceptance-tier-ruled)
- [issue-lifecycle#acceptance-tier-ruling-unconfirmed](../../../../docs/specs/issue-lifecycle.spec.html#acceptance-tier-ruling-unconfirmed)
- [issue-lifecycle#acceptance-tier-highest](../../../../docs/specs/issue-lifecycle.spec.html#acceptance-tier-highest)
- [issue-lifecycle#acceptance-tier-optout-cleared](../../../../docs/specs/issue-lifecycle.spec.html#acceptance-tier-optout-cleared)
- [issue-lifecycle#acceptance-tier-optout-uncleared](../../../../docs/specs/issue-lifecycle.spec.html#acceptance-tier-optout-uncleared)
- [issue-lifecycle#acceptance-tier-owner-decision](../../../../docs/specs/issue-lifecycle.spec.html#acceptance-tier-owner-decision)
- [issue-lifecycle#acceptance-tier-code-owner](../../../../docs/specs/issue-lifecycle.spec.html#acceptance-tier-code-owner)
- [issue-lifecycle#acceptance-tier-self-merge](../../../../docs/specs/issue-lifecycle.spec.html#acceptance-tier-self-merge)
- [issue-lifecycle#acceptance-tier-relayed](../../../../docs/specs/issue-lifecycle.spec.html#acceptance-tier-relayed)
- [issue-lifecycle#acceptance-tier-three-waits](../../../../docs/specs/issue-lifecycle.spec.html#acceptance-tier-three-waits)
- [issue-lifecycle#acceptance-merge-guard-owner](../../../../docs/specs/issue-lifecycle.spec.html#acceptance-merge-guard-owner)
- [issue-lifecycle#acceptance-merge-guard-order](../../../../docs/specs/issue-lifecycle.spec.html#acceptance-merge-guard-order)
- [issue-lifecycle#acceptance-merge-guard-head](../../../../docs/specs/issue-lifecycle.spec.html#acceptance-merge-guard-head)
- [issue-lifecycle#acceptance-merge-relay-director-only](../../../../docs/specs/issue-lifecycle.spec.html#acceptance-merge-relay-director-only)

Drive criterion: `issue-lifecycle#acceptance-tier-three-waits`

The rules: [issue-lifecycle#gates-tiers](../../../../docs/specs/issue-lifecycle.spec.html#gates-tiers), [#gates-tier-relay](../../../../docs/specs/issue-lifecycle.spec.html#gates-tier-relay), [#gates-merge-guard](../../../../docs/specs/issue-lifecycle.spec.html#gates-merge-guard). The tier block's form, each reason, Waits for, the incomplete block, merge's refusals and relay: `octo-feather-lane --help` (merge-ask, merge, relay).

## Sub-features

Each case replays one recorded run of the realcase (0xTomDaniel/octo-feather-realcase, public), named by its PR.

- **merge-ask tier block**, one case per reason kind or wait: `tier-one` (#1), `tier-spec-pr` (#2), `tier-failed` (#1, Failed listing a criterion), `tier-order-waits` (#1, #3 conflicting), `tier-clarify`, `tier-adds`, `tier-weakens`, `tier-ruled`, `tier-ruling-unconfirmed`, `tier-denied` (#21 to #26, spec calls), `tier-highest` (#21 with a Failed list), `tier-optout-cleared`, `tier-optout-uncleared`, `tier-owner-decision-verdict` (#16 to #18), `tier-owner-decision-section` (kit PR #1184), `tier-code-owner` (#27), `tier-code-owner-base` (#42, the line only the merge base holds). Each checks the tier, each reason line by its kind's prefix and Waits for.
- **incomplete block**: `incomplete` (#1, its Head stale) and `code-owners-refused` (#29, three lines git reads otherwise than GitHub): exit 1, stdout empty, the block on stderr after the incomplete mark, before the items.
- **relay, director only**: `relay-not-director` (#36, from the supervisor's pane): refused, nothing recorded, no gh call; `relay`, `relay-head`, `relay-carry` from the director's pane: one relay line on record.
- **merge by tier and relay**: `merge-owner`, `merge-owner-after` (#36, tier 3, no relay: waits for the owner), `merge-order` (#34, tier 1, #35 conflicting: waits for the director's order), `merge-self` (#39, tier 2, nobody: merges, no relay), `relayed-refused` then `relayed-merge` (#40: refused, then merged on the director's relay), `merge-head` (#36 at a fix past the relayed head: refused naming both), `merge-carry` (#36, the relay carried over a clean merge of the base: merges).
- **the director's reply to a tier 3 ask**: `director-reply`: a headless director (`pi-role agents/director.md -p`, its real model) handed `tier-failed`'s stdout as the supervisor of lane gh1255-1257-tier sends it up; its final message is its reply. Checked: it says the ask waits for the owner, names the failed criterion, no relay line is on record and its Pi session ran no `octo-feather-lane relay`.

## How to get to it (user POV)

- A supervisor runs `octo-feather-lane merge-ask PR --status FILE` in its lane worktree, reads the tier block, and either runs `octo-feather-lane merge PR HEAD` itself (Waits for: nobody) or sends the ask up (agents/supervisor.md).
- The director reads a sent-up ask and replies; it relays a merge with `octo-feather-lane relay PR HEAD` from its own pane (agents/director.md).

## Driving it with verify-octo-feather

Preconditions: `verify-octo-feather launch` printed `ready`; `verify-octo-feather doctor` exits 0; Pi and its model route for `director-reply` (else that step is `UNREACHABLE`).

Run all cases: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive merge-tiers`. Evidence: `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/merge-tiers/` (the director's brief as `director-reply.brief`).

- **GitHub.** The testkit's gh (`tests/gate/kit/testkit/gh.py`) first on PATH, its `tape.json` one scenario of `tests/gate/kit/testkit/recordings/merge-tier-*.json` or `merge-guard-1266.json` (real gh's answers), its call log reset with each tape; `director-reply` gets an empty tape, so any gh call it makes is refused.
- **Repos.** Tier cases: one clone of `recordings/realcase-tiers.bundle` (the realcase's gh1255-1257 to -1260 branches as pushed), each case's lane branch checked out, a full gate pass recorded (`octo-feather-gate record`) at each head the recordings had one. `tier-owner-decision-section`: a scratch repo borrowing the kit checkout's objects at PR #1184's merged head. Merge cases: one world per recorded run, as `tests/gate/kit/lane_merge_guard.py`'s World builds it (a clone of `recordings/realcase-1266.bundle`, the lane worktree, a scratch state dir with the lane record and director.toml, a scratch kit install, the testkit Herdr).
- **Panes.** The supervisor is `HERDR_PANE_ID=zs1:p1`, the director `zd1:p1` (director.toml).
- **Side effects.** Every cwd stays empty and the kit's `git status` unchanged; merges happen only on the fake gh.

## Gotchas

- `tier-owner-decision-section` needs PR #1184's head in the kit checkout: missing, it is `UNREACHABLE` (fix: `git fetch origin main` in the kit).
- `director-reply` runs with `--exclude-tools mcp__*` (no web search) and a scratch `XDG_STATE_HOME` whose commit identity the drive sets; it costs one director model run. The qc sandbox has no Pi, so `just qc` sees it unreachable (exit 77): drive it on the box.
- The tapes replay calls in order: a merge-ask change that asks gh something new fails the case with `fake gh: no recording for call ...` on stderr; record the scenario again (the recording test's docstring names its world).
