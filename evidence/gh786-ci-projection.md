# gh786 current CI projection

Basis: director-authorized continuation of factory repair #786, existing
issue-lifecycle `#lanes-one-head`. No criterion, spec or family eligibility change.

## Observed failure and correction

On head `b10eb4c1f2e9e7dc36b56eab1c538960b0649dc0`, actual GitHub run
43090374120 completed successfully for scope and check. Older draft run
43089848429 still contributed SKIPPED rows to the GraphQL rollup. The public
`octo-feather-lane merge-ask 788` refused those historical skips despite the
same-head eligible success. Active and archived finding logs were searched for
CI-projection classes; this continuation follows the explicit owner correction,
not an inferred two-lane repeat. ADR0010 and recent commits were inspected.

Routing: all edited files are tracked in this kit worktree, ADR0020. Ladder:
ADR0008 rung 1, one in-memory current projection shared by the existing failure,
pending and skipped-carry decisions. The decisions themselves remain exact:
actual GitHub head, app, workflow and check identities, never name-only matching.
No new ledger, client or background service.

## Authoritative sources

The existing gh helper reads REST commit check runs. Their check_suite.id and
app.id are joined to actual Actions runs' check_suite_id and workflow_id on the
exact head. Latest workflow run and latest check-run IDs select current facts.
A context absent from that workflow's current suite stays pending. Wrong heads,
incomplete API lists and missing identity metadata refuse the projection. Legacy
StatusContext rows remain in the same rollup and retain their original decisions.

- https://docs.github.com/en/rest/checks/runs#list-check-runs-for-a-git-reference
- https://docs.github.com/en/rest/actions/workflow-runs#list-workflow-runs-for-a-repository
- Installed `gh` 2.103.3, release date reported by `gh --version`: 2026-10-26.
- Official gh `pr checks` implementation inspected at
  https://github.com/cli/cli/blob/trunk/pkg/cmd/pr/checks/aggregate.go . Its
  name/workflow/event projection does not retain app identity, so it was not used
  to collapse app-distinct checks here. Existing real gh/API transport is reused.

## Public proof

Before the production edit, the generated same-head draft-skip plus eligible-success
scenario in `bash tests/lane-merge-ask.sh` exited 1 with a stale skipped scope
refusal. No other merge-ask item failed. After the projection, the whole public
script passed, including all original skipped-carry cases and ten added negative
variants: latest failure, pending, cancelled, unknown conclusion, missing current
context, wrong head, app collision, workflow collision, missing app metadata and a
failing legacy required/security StatusContext. Tests invoke commands, never load
or inspect production source.

One extra oracle written during development, the new loop `variant=skipped`, was
removed: it demanded status-only H fail even with an existing valid Judged carry
proof from J. That was stricter than `#lanes-one-head`, which permits this carry.
All original carry oracles remain untouched; no production exception was added.

The small real public pipeline was exercised before any costly batch. Baseline
GitHub reads confirmed the four historical/current rows and reproduced the
canonical refusal. With the fix, this worktree's published command
`scripts/octo-feather-lane merge-ask 788` exited 0 on the same H. This establishes
the engineering repair only, not acceptance, build status or reviewer-family
eligibility or validation of a newly committed final head. No GitHub write was
made and no merge ask was published as ready. `just check-lint` also passed.

Affected consumers `qc-carry.sh` and `lane-ci-start.sh` then passed through the
canonical selected public gate: 2 passed in 32.46 seconds, exit 0. qc-carry used
21.223 CPU seconds against the report-only 10-second item budget. That timing is
reported for review; no budget, gate or assertion was changed or waived.

The first full gate returned 227 passed and one failing static type recipe.
The projection now carries typed string/object dictionaries and validates external
workflow objects, positive integer identities, nonempty text fields and nullable
conclusions at its API boundary. No ignores or baseline expansion were used.
`just check-types` then passed across 101 files. The public regression was rerun
after this stronger boundary validation and exited 0 with all original and added
cases passing.

Final recovery full-gate outcome is reported separately. This file is fixed before
that run. The proven offline gate setup uses real socat/rg in a namespace-local
/usr/bin overlay, uid1000 with inheritable/permitted/effective/ambient capabilities
zero, no /tmp bind, GOMAXPROCS=2 and Node heap1536. Only the offline fake-provider
gate PATH excludes the GPT wrapper; actual agents and real QA keep it first.

Check: scripts/octo-feather-lane: current exact-head checks retain app/workflow/context identity and fail closed on unavailable current evidence (issue-lifecycle #lanes-one-head) | reads: GitHub PR rollup, commit check runs and Actions workflow runs | class: exact
