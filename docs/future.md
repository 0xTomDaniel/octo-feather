# Future improvements

Not for the Martell take-home. Each item names what it would replace and what is still unverified.

## A2A instead of lane records and handoffs.jsonl

Replace octo-lite's lane record plus `<lane>.handoffs.jsonl` and the `herdr-say` text protocol with the A2A (Agent2Agent) protocol. Exo's working assumption, from memory of the spec and not checked on 2026-10-18: an A2A Task (id, status history, messages, artifacts) is roughly a lane record and its handoff log done properly, and A2A messages replace `herdr-say`. Verify against the current spec before designing. See ADR 0003.

## Spec Chat wake provider registration

octo-lite's installer registered `herdr-wake` as Spec Chat's `wake` provider (`providers/wake.toml`). The port dropped the installer, so a spec review hand-off cannot wake a supervisor until that registration is done by hand or by a `just` recipe. Needed once spec-chat review hosting runs on the remote.

## `just qc` and `just qa`

Names decided by Tom (round 8): `just qc` runs the Jev product judge on a target's product, `just qa` runs factory evals of the kit's own agents and loop. Both are stubs that exit 2. Neither runs inside `just check`, which stays deterministic and free; check-refs fails if a gate recipe calls them.

## Reviewer scope drift (gpt-6.1-sol)

Tom's caution: sol models tend to over-engineer and over-correct. The code reviewer must judge only against the ticket's acceptance criteria and the spec. `agents/code-reviewer.md` already covers part of this ("judge against the shaped scope and the spec, not against preference"; "block only on broken behavior or clearly over-built work"; "a finding that cannot name a consequence is a note"). Risk: Matt's `code-review` Standards axis asks for baseline smells, which invites findings outside the criteria. To verify: a rehearsal check, plus an eval case where an out-of-criteria finding must not block. Flagged only, not fixed.

## Spec Chat assumes a lane-key workflow

Spec Chat should not be tied to one workflow; today it is. Unverified beyond reading the code, and not for Thursday. Do not patch Spec Chat from here.

Evidence (spec-chat 0f4e0fa):
- `skill/review-spec/assets/review-serve.py` `_lane_label` (l560) treats only issue-key slugs (`[a-z]+-?[0-9]+`) as lanes, so `gh1` shows as `GH-1`; `_index` (l944) makes only those slugs open lanes, and every other slug goes under Settled.
- The review service and its registries are keyed by `${HERDR_SESSION:-default}` (`session_state`, l698-700), so each Herdr session has its own registry.
- Wake goes through Herdr pane ids (`skill/review-spec/SKILL.md` l29, l76).

What it breaks for octo-feather (ADR 0021):
- A spec in shaping is registered under its own slug, which is not a lane key, so the index shows it under Settled while it is still under review.
- A lane revising its spec registers it under the spec's own slug, never `gh<N>` (one row per spec), so the lane's work never shows as a lane card. Registering under `gh<N>` would make a second row with its own id, threads cursor and `accepted` flag, and the acceptance would not carry over.
- Jev's cross-lane checks pair rows with different slugs in one project, so a spec registered under both slugs may be compared with itself.

Direction: a lane or stage should be explicit registry data supplied by the caller at `register`, not inferred from the slug's shape.

## Jev replaces the interim `just qc`

Until Jev, `just qc` is a fresh cross-family judge that runs each claimed criterion's demo path (ADR 0022). Jev replaces it behind the same recipe and must verify every `built` criterion and only those, and report any it cannot confirm.

## Landing agent

A dedicated landing role that takes an approved head to main: rebases, reruns gates, queues merges across lanes, as scaling-octo-engine's Symphony landing role does. Today the lane's supervisor runs the merge itself, per spec `#gates-merge` (ADR 0007). Trigger: post-approval conflicts become common, or parallel lanes need merge queueing.

## Criterion status on the spec page

Later, not now: show each criterion's planned or built status on its spec page in Spec Chat, read from the status file, without the spec HTML or Spec Chat learning this workflow.

## Status check in target repos

After Thursday 10-22, copy `octo-feather-spec-status` into each template (`templates/python`, `templates/typescript`) and call it from their `just check`, so the pre-commit hook and CI gate run it too. CI there has no kit scripts on `PATH`, so today only the kit's own `just check` checks status files (ADR 0021).

## Owed eval cases

Each behaviour change shipped before `just qa` exists (ADR 0008) owes an eval case that fails before it and passes after it. Its smoke run is in `evidence/`.

- Director, chat acceptance (docs/adr/0021): the owner says "spec accepted" in chat; the director records nothing and sends the review link. Smoke: `evidence/2026-10-19-role-probes.md`.
- Supervisor and code reviewer, interim QC (docs/adr/0022): a lane head where one claimed criterion's demo path fails; only the passing one is built, and the failure goes to an implementer as a `qc` finding. Smoke: `evidence/2026-10-19-qc-smoke.md`.
- Supervisor, lane scope (implement-spec patch, audit F05): a two-lane spec; the lane builds only its brief's criteria, runs `just integrate` itself, fixes blocking findings only and lists notes in the PR body. Smoke: `evidence/2026-10-19-role-probes.md`.
- Supervisor, QC then review on one head (audit F02, docs/adr/0022): after the pilot's integration the supervisor opens the draft PR, runs `just qc`, then reviews the head QC left; a code fix after QC reruns both. Smoke: `evidence/2026-10-19-role-probes.md`.
- Supervisor, spec revision (one review row per spec): a behaviour revision is registered under the spec's own slug, not `gh<N>`. Smoke: `evidence/2026-10-19-role-probes.md`.
- Supervisor, behaviour revision (audit F03): a revision changes a clause governing a built criterion; the review link lists that criterion and its acceptance resets it to planned. Smoke: `evidence/2026-10-19-role-probes.md`.
- Director, repeat trigger (audit F08): a class with a closed correction issue and no newer finding line starts no lane; a newer one does. Smoke: `evidence/2026-10-19-role-probes.md`.
- Supervisor, fan-out (Tom's spec comment): after the pilot, two independent tickets get two implementers at once. Smoke: `evidence/2026-10-19-role-probes.md`.
- Implementer and code reviewer, new pstack skills (principle-prove-it-works, blast-radius): the implementer reports with a re-runnable proof; the reviewer names the one safety fact and how far it was proven. Smoke: `evidence/2026-10-19-role-probes.md`.
- Owner shaping chat (`just shape`): asked to change factory code, it shapes a spec instead, using only the shaping skills. Smoke: `evidence/2026-10-19-role-probes.md`.
- Implementer, language skills (python, typescript from scaling-octo-engine@ef11d2b9): in a template copy, a new CLI command gets integration/E2E tests only (no unit tier), `just check` as the gate, basedpyright strict in Python, Zod 4 `z.strictObject` only where a new TS repo validates wire input. Smoke: `evidence/2026-10-19-language-skills-smoke.md`.
- Supervisor, head-pinned merge (spec `#gates-merge`, docs/adr/0007): one eval per case the rule names, each judged against its criterion: (a) head unchanged (spec `#acceptance-merge-approved-head`), (b) lane head took a merge of main after the ask (spec `#acceptance-merge-main-merged`), (c) a fix commit after the ask (spec `#acceptance-merge-head-moved`). Smoke: `evidence/2026-10-19-merge-teardown-smoke.md` (lane #5 chain; role probes (a) to (c), refined merge rule).
- Supervisor and director, close report first (spec `#transport-close-space`, docs/adr/0007): the supervisor reports with its worktree intact and never removes it; the director closes the space, then removes it. Smoke: `evidence/2026-10-19-merge-teardown-smoke.md` (lane #5 chain; role probe (d), refined merge rule).
- Supervisor, Accept freezes a spec (docs/adr/0021, finding 20): with a live review row on an accepted spec, a wording fix is asked of the owner through the director and the spool is scanned (`watch-specs.sh <spec dir> .cursor-owner 0 3`) before any edit; no commit before the relayed yes. Smoke: `evidence/2026-10-20-spec-freeze-baseline-gap-probes.md` (probe (a)).
- Implementer and code reviewer, spec freeze (docs/adr/0021): the implementer never edits an accepted spec and escalates; the reviewer blocks an accepted-spec edit with no owner yes in the PR body, class `spec-edit-during-open-review`. Smoke: `evidence/2026-10-20-spec-freeze-baseline-gap-probes.md` (probes (c), (d)).
- Director, baseline gap routing (docs/adr/0020, finding 21): a baseline qc failure is logged `"kind": "gap"` and opens a gap lane, never a correction lane, however often its cause repeats. Smoke: `evidence/2026-10-20-spec-freeze-baseline-gap-probes.md` (probe (b)).
- Supervisor, opt-outs in the merge ask (docs/adr/0008, correction lane #26): a lane whose commits carry a `Behaviour-neutral: <reason>` trailer sends a merge ask that names each such commit with its reason for the owner to judge. Smoke: `evidence/2026-10-20-behavior-smoke-check.md`.
<!-- owed-evals-end -->

## `octo-feather-spec-status reaccept`

After Thursday 10-22: `octo-feather-spec-status reaccept STATUS COMMIT --reset ID...` applies an accepted revision mechanically (reset the listed ids to `planned`, add new ids as `planned`, drop removed ones, move `accepted_commit`), so the supervisor stops editing the status file by hand (audit F03). The affected ids stay the revision's explicit list: comparing criterion text cannot find a requirement changed through a governing clause.

## Status file deleted beside its spec

After Thursday 10-22, with the target wiring above: `octo-feather-spec-status check` fails when `<slug>.status.json` exists at the merge-base with main (`git ls-tree`) but is missing from the work tree while `<slug>.spec.html` remains, naming the file. A draft spec without a status file stays legal; retiring a spec deletes both files. One test case (audit F04).

## Effect pilot

Effect pilot after Thu 10-22: one small project tries Effect v4 (Schema in core `effect`); decide on adoption from the result. Not for the first factory run. Until then the typescript skill says: the repo's existing schema library, Zod 4 in a new repo (Tom, 2026-10-19).

## TypeScript 7 in templates/typescript

Move templates/typescript to TypeScript 7 when 7.1 ships its programmatic API and typescript-eslint, knip and dependency-cruiser support it (7.0 GA 2026-07-08 has no API; the npm-alias bridge was rejected because it puts two compilers in every repo). Until then it stays on `typescript ~6.0.3` (Tom, 2026-10-19).
