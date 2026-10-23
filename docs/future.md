# Future improvements

Not for the take-home. Each item names what it would replace and what is still unverified.

## A2A instead of lane records and handoffs.jsonl

Replace octo-lite's lane record plus `<lane>.handoffs.jsonl` and the `herdr-say` text protocol with the A2A (Agent2Agent) protocol. Exo's working assumption, from memory of the spec and not checked on 2026-10-18: an A2A Task (id, status history, messages, artifacts) is roughly a lane record and its handoff log done properly, and A2A messages replace `herdr-say`. Verify against the current spec before designing. See ADR 0003.

## Spec Chat wake provider registration

octo-lite's installer registered `herdr-wake` as Spec Chat's `wake` provider (`providers/wake.toml`). The port dropped the installer, so a spec review hand-off cannot wake a supervisor until that registration is done by hand or by a `just` recipe. Needed once spec-chat review hosting runs on the remote.

## `just qc` and `just qa`

Names decided by Tom (round 8): `just qc` runs the Jev product judge on a target's product, `just qa` runs factory evals of the kit's own agents and loop. `just qc` is the interim product judge (docs/adr/0022). `just qa` runs a pilot: the skill-triggers suite (evals/, scripts/octo-feather-qa, #110); role transcript cases and trigger cases for every skill a role lists are still to come (#108). Neither runs inside `just check`, which stays deterministic and free; the gate's guard is check-gate-free (`scripts/check-gate-free`).

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

## Jev judges call evidence

Later `just qc` asks Jev one yes or no per logged spec call: does the cited evidence show the accepted criterion cannot pass as written? Trigger: about 10 calls the owner approved or denied, used as labels. Use Spec Chat's jev-contract (the question set as data, its own adapter). Build nothing now; until then `just check` only fails a call with no evidence and the owner judges the rest at merge (Tom, 2026-10-21, issue #58).

## Jev shadow on one question

Jev shadow on one question, "Does this ticket change something a user can see or run, end to end?", advice-only next to review, seeded from #49's layer-wording fixtures and the #40 phrasings; gate only after it matches about 10 of the owner's labels. Owed, build nothing (issue #71). Until then code review and the `just qc` judge own it (docs/adr/0008); a case they miss becomes a Jev eval in docs/owed-evals/, never a new check.

## Landing agent

A dedicated landing role that takes an approved head to main: rebases, reruns gates, queues merges across lanes, as scaling-octo-engine's Symphony landing role does. Today the lane's supervisor runs the merge itself, per spec `#gates-merge` (ADR 0007). Trigger: post-approval conflicts become common, or parallel lanes need merge queueing.

## Criterion status on the spec page

Later, not now: show each criterion's planned or built status on its spec page in Spec Chat, read from the status file, without the spec HTML or Spec Chat learning this workflow.

## Status check in target repos

After Thursday 10-22, copy `octo-feather-spec-status` into each template (`templates/python`, `templates/typescript`) and call it from their `just check`, so the pre-commit hook and CI gate run it too. CI there has no kit scripts on `PATH`, so today only the kit's own `just check` checks status files (ADR 0021).

## `octo-feather-spec-status reaccept`

After Thursday 10-22: `octo-feather-spec-status reaccept STATUS COMMIT --reset ID...` applies an accepted revision mechanically (reset the listed ids to `planned`, add new ids as `planned`, drop removed ones, move `accepted_commit`), so the supervisor stops editing the status file by hand (audit F03). The affected ids stay the revision's explicit list: comparing criterion text cannot find a requirement changed through a governing clause.

## Status file deleted beside its spec

After Thursday 10-22, with the target wiring above: `octo-feather-spec-status check` fails when `<slug>.status.json` exists at the merge-base with main (`git ls-tree`) but is missing from the work tree while `<slug>.spec.html` remains, naming the file. A draft spec without a status file stays legal; retiring a spec deletes both files. One test case (audit F04).

## Effect pilot

Effect pilot after Thu 10-22: one small project tries Effect v4 (Schema in core `effect`); decide on adoption from the result. Not for the first factory run. Until then the typescript skill says: the repo's existing schema library, Zod 4 in a new repo (Tom, 2026-10-19).

## TypeScript 7 in templates/typescript

Move templates/typescript to TypeScript 7 when 7.1 ships its programmatic API and typescript-eslint, knip and dependency-cruiser support it (7.0 GA 2026-07-08 has no API; the npm-alias bridge was rejected because it puts two compilers in every repo). Until then it stays on `typescript ~6.0.3` (Tom, 2026-10-19).

## Lessons from the pilot 1 run (2026-10-19/20)

Full list with Tom's guidelines: the take-home's notes (private, not in repo). Kit items:

- Accept was not recorded: `octo-feather-accepted` waited for a registry `accepted = true` nothing writes, and Exo hand-wrote it twice (canary, pilot 1 `06af3f4`). It now reads the review page's Accept hand-off for the spec at the registered commit and ignores the registry key (ADR 0021, `tests/accepted.sh`).
- Director merged spec PR #1 itself despite the never-merge rule. Now a Merges section at the top of agents/director.md and the MERGES field of the kickoff brief (`docs/kickoff-brief.md`); owed eval case in docs/owed-evals/backlog.md.
- Supervisor moved the head after its report (1887d52 → f14e2d8) and reworded commit bodies unasked. The merge ask must name the final head; owed eval case.
- Orders sent during cliproxy 503 outages were lost; `herdr-say` exit 0 does not mean the order was read.
- implement-spec and the python skill assumed uv/pyproject. The python skill now follows the project's own tooling, and the kickoff brief's TOOLING field names it for every lane.
- Unit tests were written because the spec said "proven by a unit test". shape-spec must default to "a test through a public entry point" and add a minimal-change rule for brownfield targets (keep original lines and order; no test-only code in production files).
- macOS: `just start` works without a hand-patched PATH: the kit justfile puts GNU coreutils and util-linux (`realpath -m`, `readlink -f`, `setsid`, `timeout`), Homebrew's bash 5 (`mapfile`) and mise ahead of the system's, panes inherit it, and octo-feather-start sets HERDR_SESSION from the project. Still Linux-only, and saying so: `just qc` (exit 69) and `herdr-close --park` (exit 69); a closed tab's detached children are not swept on macOS.
- Re-registering a spec on a new commit changes its review port; old link dies and stale review-serve processes keep running. Resolved by `review-host` (issue #65, `tests/review-host.sh`): the cause was review-host.py reading liveness from `/proc`, which macOS lacks, so it never saw its own server and started another on a new port. The kit command stops this state's review-serve processes that review-host.py would not see as its own before `register` (so the recorded port is reused) and any the registry does not own after it. Not reproduced on Linux, service or loopback. The lasting fix is in Spec Chat: `process_cmdline` falling back to `ps -o command= -p PID` where there is no `/proc`.

## Lessons from the pilot 2 run (2026-10-20/21)

- Accept went stale twice: amending the spec after registration (rich output 51d4fa7; B2 amend) moved its hash, so `octo-feather-accepted` rejected Tom's real Accept ("Accept spec pressed on version …, not on spec at registered commit …"). Re-register and re-press each time. A spec edit after Accept should re-register automatically and tell Tom. Resolved by the spec-call rule (issue-lifecycle `#gates-spec-calls`, issue #63): an edit after Accept no longer re-registers or voids the Accept; it is a logged call the owner approves or denies at merge, and a weakening reaches Tom at once.
- `octo-feather-accepted` needs SPEC_PATH; without it rc=1 even when Accept was recorded.
- `herdr-say` and `octo-feather-accepted` aren't on PATH on the Mac (`herdr-say` lives in `.agents/skills/herdr-comms/assets/`).
- Registering on macOS reports wake=unavailable, so the director can't be woken; orders went through herdr-say by hand.
- A spec without the `.viz` assets and `<script>` renders no Spec Chat UI. Preflight should fail on that. Resolved: `review-host register` refuses such a page, naming the missing `<script>` or `runtime.js` and the fix (Spec Chat's `preflight.py`); nothing is registered (issue #65).
