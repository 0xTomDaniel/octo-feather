# Future improvements

Not for the Martell take-home. Each item names what it would replace and what is still unverified.

## A2A instead of lane records and handoffs.jsonl

Replace octo-lite's lane record plus `<lane>.handoffs.jsonl` and the `herdr-say` text protocol with the A2A (Agent2Agent) protocol. Exo's working assumption, from memory of the spec and not checked on 2026-10-18: an A2A Task (id, status history, messages, artifacts) is roughly a lane record and its handoff log done properly, and A2A messages replace `herdr-say`. Verify against the current spec before designing. See ADR 0003.

## Spec Chat wake provider registration

octo-lite's installer registered `herdr-wake` as Spec Chat's `wake` provider (`providers/wake.toml`). The port dropped the installer, so a spec review hand-off cannot wake a supervisor until that registration is done by hand or by a `just` recipe. Needed once spec-chat review hosting runs on the remote.

## octo-feather's own spec

`spec/domains/octo-lite.spec.html` is octo-lite's spec, still Claude and Linear. The role contracts cite its anchors (`#lane-record`, `#transport-*`). Rewrite it as `octo-feather.spec.html` once the rehearsal shows which parts survive.

## `just qc` and `just qa`

Names decided by Tom (round 8): `just qc` runs the Jev product judge on a target's product, `just qa` runs factory evals of the kit's own agents and loop. Both are stubs that exit 2. Neither runs inside `just check`, which stays deterministic and free; check-refs fails if a gate recipe calls them.

## Reviewer scope drift (gpt-6.1-sol)

Tom's caution: sol models tend to over-engineer and over-correct. The code reviewer must judge only against the ticket's acceptance criteria and the spec. `agents/code-reviewer.md` already covers part of this ("judge against the shaped scope and the spec, not against preference"; "block only on broken behavior or clearly over-built work"; "a finding that cannot name a consequence is a note"). Risk: Matt's `code-review` Standards axis asks for baseline smells, which invites findings outside the criteria. To verify: a rehearsal check, plus an eval case where an out-of-criteria finding must not block. Flagged only, not fixed.

## Finding lines in the specs branch

ADR 0020 adds a handoffs line `{"kind": "finding", "source", "class", "blocking", "summary"}` and the code reviewer's `class` tag. `spec/` on main is octo-lite's reference spec and stays untouched; the specs-v1 rewrite should define the finding line under `#handoff-fields`.

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
<!-- owed-evals-end -->

## `octo-feather-spec-status reaccept`

After Thursday 10-22: `octo-feather-spec-status reaccept STATUS COMMIT --reset ID...` applies an accepted revision mechanically (reset the listed ids to `planned`, add new ids as `planned`, drop removed ones, move `accepted_commit`), so the supervisor stops editing the status file by hand (audit F03). The affected ids stay the revision's explicit list: comparing criterion text cannot find a requirement changed through a governing clause.

## Status file deleted beside its spec

After Thursday 10-22, with the target wiring above: `octo-feather-spec-status check` fails when `<slug>.status.json` exists at the merge-base with main (`git ls-tree`) but is missing from the work tree while `<slug>.spec.html` remains, naming the file. A draft spec without a status file stays legal; retiring a spec deletes both files. One test case (audit F04).
