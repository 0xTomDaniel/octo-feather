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
- [issue-lifecycle#acceptance-merge-digest](../../../../docs/specs/issue-lifecycle.spec.html#acceptance-merge-digest)

Drive criterion: `issue-lifecycle#acceptance-merge-guard-owner`
Drive criterion: `issue-lifecycle#acceptance-merge-digest`

The director's reply to a tier 3 ask (issue-lifecycle#acceptance-tier-three-waits) is no case here: qc.toml's demo for it, a pinned eval run (evals/director-tier-relay), is its proof.

The rules: [issue-lifecycle#gates-tiers](../../../../docs/specs/issue-lifecycle.spec.html#gates-tiers), [#gates-tier-relay](../../../../docs/specs/issue-lifecycle.spec.html#gates-tier-relay), [#gates-merge-guard](../../../../docs/specs/issue-lifecycle.spec.html#gates-merge-guard), [#gates-digest](../../../../docs/specs/issue-lifecycle.spec.html#gates-digest). The tier block's form, each reason, Waits for, the incomplete block, merge's refusals and relay, the ask merge records and the digest's lines: `octo-feather-lane --help` (merge-ask, merge, relay, digest).

## Sub-features

Each case replays one recorded run of the realcase (0xTomDaniel/octo-feather-realcase, public), named by its PR.

- **merge-ask tier block**, one case per reason kind or wait: `tier-one` (#1), `tier-spec-pr` (#2), `tier-failed` (#1, Failed listing a criterion), `tier-order-waits` (#1, #3 conflicting), `tier-clarify`, `tier-adds`, `tier-weakens`, `tier-ruled`, `tier-ruling-unconfirmed`, `tier-denied` (#21 to #26, spec calls), `tier-highest` (#21 with a Failed list), `tier-optout-cleared`, `tier-optout-uncleared`, `tier-owner-decision-verdict` (#16 to #18), `tier-owner-decision-section` (kit PR #1184), `tier-code-owner` (#27), `tier-code-owner-base` (#42, the line only the merge base holds). Each checks the tier, each reason line by its kind's prefix and Waits for.
- **incomplete block**: `incomplete` (#1, its Head stale) and `code-owners-refused` (#29, three lines git reads otherwise than GitHub): exit 1, stdout empty, the block on stderr after the incomplete mark, before the items.
- **relay, director only**: `relay-not-director` (#36, from the supervisor's pane): refused, nothing recorded, no gh call; `relay`, `relay-head`, `relay-carry` from the director's pane: one relay line on record.
- **merge digest**: `digest-merge-tier1` (#51, tier 1, on 2026-11-28: no digest told, today is never due) and `digest-merge-tier2` (#52, tier 2, one clarifies call, the next day: the director told once `merge digest due for 2026-11-28: ...`), each merged through `merge` from its own supervisor's pane, then `digest` (`octo-feather-lane digest 2026-11-28 --repo <realcase>`): only the recorded digest's two gh reads, #51 in one line, #52 in full with the call's fields, #53 (merged with plain `gh pr merge`) `tier not recorded`, then `sha256 <12 hex>`. `digest-due` (`digest --repo <realcase>`, no DAY): the same text and sha, the due day alone. `digest-sent-refused` (`--sent` from the supervisor's pane): refused, no gh call, nothing recorded; `digest-sent` (the director's pane): one sent `digest` line in the director log; `digest-none`: `No merge digest due`, no gh call.
- **merge by tier and relay**: `merge-owner`, `merge-owner-after` (#36, tier 3, no relay: waits for the owner), `merge-order` (#34, tier 1, #35 conflicting: waits for the director's order), `merge-self` (#39, tier 2, nobody: merges, no relay), `relayed-refused` then `relayed-merge` (#40: refused, then merged on the director's relay), `merge-head` (#36 at a fix past the relayed head: refused naming both), `merge-carry` (#36, the relay carried over a clean merge of the base: merges).

## How to get to it (user POV)

- A supervisor runs `octo-feather-lane merge-ask PR --status FILE` in its lane worktree, reads the tier block, and either runs `octo-feather-lane merge PR HEAD` itself (Waits for: nobody) or sends the ask up (agents/supervisor.md).
- The director runs the digest on a `merge digest due` line: agents/director.md, Merges (the merge digest step).
- The director reads a sent-up ask and replies; it relays a merge with `octo-feather-lane relay PR HEAD` from its own pane (agents/director.md).

## Driving it with verify-octo-feather

Preconditions: `verify-octo-feather launch` printed `ready`; `verify-octo-feather doctor` exits 0.

Run all cases: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive merge-tiers`. Evidence: `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/merge-tiers/`.

- **GitHub.** The testkit's gh (`tests/gate/kit/testkit/gh.py`) first on PATH, its `tape.json` one scenario of `tests/gate/kit/testkit/recordings/merge-tier-*.json` or `merge-guard-1266.json` (real gh's answers), its call log reset with each tape; the digest cases one tape of `lane-merge-digest-51.json`, `lane-merge-digest-52.json` and `lane-digest-1339.json`, in that order.
- **Repos.** Tier cases: one clone of `recordings/realcase-tiers.bundle` (the realcase's gh1255-1257 to -1260 branches as pushed), each case's lane branch checked out, a full gate pass recorded (`octo-feather-gate record`) at each head the recordings had one. `tier-owner-decision-section`: a scratch repo borrowing the kit checkout's objects at PR #1184's merged head. Merge cases: one world per recorded run, as `tests/gate/kit/lane_merge_guard.py`'s World builds it (a clone of `recordings/realcase-1266.bundle`, the lane worktree, a scratch state dir with the lane record and director.toml, a scratch kit install, the testkit Herdr). Digest cases: `tests/gate/kit/lane_digest.py`'s world (a bare origin from `recordings/realcase-gh1337.bundle`, its main moved to each merge commit before that merge, the director's checkout at the first merge's parent, lane records gh49 and gh50 with their PRs); the digest's two reads replayed once per digest made (3).
- **Time.** Digest cases: the testkit's clock (`tests/gate/kit/testkit/clock/sitecustomize.py`, on PYTHONPATH with TESTKIT_NOW) sets each command's day: #51's merge on 2026-11-28, every later case on 2026-11-29. `start`'s due line is no case here (a start's kit check fetches the install's origin, here GitHub's): tests/gate/kit/lane_digest.py due_until_sent proves it.
- **Panes.** The supervisor is `HERDR_PANE_ID=zs1:p1`, the director `zd1:p1` (director.toml).
- **Side effects.** Every cwd stays empty and the kit's `git status` unchanged; merges happen only on the fake gh.

## Gotchas

- `tier-owner-decision-section` needs PR #1184's head in the kit checkout: missing, it is `UNREACHABLE` (fix: `git fetch origin main` in the kit).
- The tapes replay calls in order: a merge-ask change that asks gh something new fails the case with `fake gh: no recording for call ...` on stderr; record the scenario again (the recording test's docstring names its world).
