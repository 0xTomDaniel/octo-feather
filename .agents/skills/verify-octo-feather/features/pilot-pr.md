# pilot-pr

Criteria:

- [issue-lifecycle#acceptance-pilot-pr](../../../../docs/specs/issue-lifecycle.spec.html#acceptance-pilot-pr)

Drive criterion: `issue-lifecycle#acceptance-pilot-pr`

## Sub-features

- `integrate` `octo-feather-integrate 12 gh12-pilot` lands the pilot's worker branch on lane gh12, its gate green: the judged head J.
- `pr-create` `gh pr create --draft` on the pushed lane: the draft PR's URL.
- `qc` `just qc docs/specs/demo.status.json <PR> acceptance-a acceptance-b` at J: one status-only commit after J, acceptance-a built in that PR, acceptance-b (its demo fails) planned.
- `verdict` `octo-feather-lane verdict <PR> <J> <report>` after qc's commit is pushed, the report's `Range: <main>..<J>` (a full round): the review verdict posted for J.
- `pr-view` `gh pr view <PR> --json isDraft,headRefOid,comments`: still a draft, its head qc's commit, its one verdict comment naming J under that PR head.

## How to get to it (user POV)

- The pilot's path is the supervisor's (rule: [issue-lifecycle#lanes](../../../../docs/specs/issue-lifecycle.spec.html#lanes), its pilot paragraph): `just integrate`, push and open the draft PR (`github-pr` skill), then `just qc` and the code review on that head, the verdict posted with `octo-feather-lane verdict` (its usage: `octo-feather-lane` with no arguments).

## Driving it with verify-octo-feather

Preconditions:

- `verify-octo-feather launch` printed `ready`; `verify-octo-feather doctor` exits 0.
- Unprivileged nested user namespaces (`unshare -rm`): the qc sandbox needs them.

Run all cases: `.agents/skills/verify-octo-feather/scripts/verify-octo-feather drive pilot-pr`. Evidence: `$VERIFY_OCTO_FEATHER_EVIDENCE_DIR/pilot-pr/`.

- **Scratch target.** `$VERIFY_OCTO_FEATHER_RUN_DIR/scratch/pilot-pr/repo`: the kit's `tests/fixtures/spec-status/good/demo.spec.html` and its status file, a `qc.toml` whose demos are `qc.toml` `values.qc_demo_pass` (acceptance-a) and `values.qc_demo_fail` (acceptance-b), a justfile with only `check`; a bare `origin.git` beside it; lane worktree `lane` on `gh12`, worker worktree `pilot` on `gh12-pilot` with one commit.
- **GitHub.** The kit's offline fake gh (`tests/fixtures/tracker-gh`, first on PATH, its store `scratch/pilot-pr/gh.json`, repo `o/r`): a PR's head is its branch on the bare origin, so the drive's `git push` moves it. The classifier faked (SKILL.md).
- The drive prints `pilot-pr: PR #<n> status commit <H> (...); verdict head <J>, the status commit's parent`.
- **Side effects.** Every cwd stays empty and the kit's `git status` unchanged; the scratch target, origin and fake store go with cleanup.

## Gotchas

- `just qc` exits 1 here by design: acceptance-b's demo fails, which proves only passed criteria are built.
