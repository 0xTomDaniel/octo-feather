---
name: implement-spec
description: "Implement the result of /to-spec and /to-tickets in code."
---

You have been provided a spec. This spec should have tickets associated with it, describing how to implement the spec.

The issue tracker is the target's: read, file and close tickets only through the tracker skill's scripts.

The goal is the lane's criteria of the spec (your brief names them) implemented on a single **integration branch**, with every ticket resolved the way the issue tracker closes work.

The tickets are not a list of steps. They are a **task graph** with blocking relationships between them. This means there is always a **frontier** of tickets which are ready to be grabbed.

Communication to and from subagents should be sparse. Communicate primarily through **context pointers**: to the spec, tickets, research notes, and previous commits. Don't duplicate information already available via pointers.

**Implementer subagents** should be run in the background where possible for maximum concurrency.

## Steps

1. Read the spec and tickets to understand the task graph.

2. (optional) Use an **exploration subagent** to conduct any exploration required by the tickets - relevant codebase files or external documentation. Ensure the exploration subagent can save files - it should save its markdown notes in a directory outside the repo, accessible by all future subagents. This lets **implementer subagents** focus on implementation rather than exploration.

3. Create the integration branch. If the issue tracker closes work through PRs, or the user asks for one, open a draft PR after the first merge in step 5 (a branch with no commits ahead of main can't open one), its body starting with the line the tracker skill's `pr-line <parent key>` prints.

4. Pilot first (docs/adr/0019): run the lane's first ticket alone through steps 4, 5 and 7, then fix the brief template and re-cut the remaining tickets before fanning out. Use **implementer subagents** to implement each ticket, each in its own worktree on its own branch: a Herdr worker, `herdr-spawn --role implementer` in tab `worker-<k>`. Each implementer subagent:
   - confirms its worktree is based on the integration branch before starting, and resets onto it if not;
   - builds the ticket with the `tdd` skill (`../tdd/SKILL.md`);
   - merges the integration branch tip into its own branch before reporting done, on its hand-off gate green (quality spec `#acceptance-gate-green`)

5. Once an **implementer subagent** completes, merge its work to the integration branch yourself: run `just integrate <parent key> <worker branch or commit>` (docs/adr/0017). It runs the gate tier issue-lifecycle spec `#lanes-checkpoints` names for that head (`--full` forces the full tier), exits non-zero on a conflict or a red gate and leaves the branch as it was; hand that to an implementer, then integrate its result.

6. If this changes the **frontier** of available tickets, kick off more **implementer subagents** to work on the new tickets. This allows for maximum concurrency.

7. Once all tickets are complete and the lane's final head passed the full gate, the lane's claims named in `OCTO_FEATHER_QC_CLAIMS` (issue-lifecycle spec `#lanes-checkpoints`, quality spec `#qc-capture`), run `just qc` and a fresh `code-reviewer` pane as spec `#lanes-one-head` and `#gates-merge` say (docs/adr/0022); read them there, never restate them. As they start on that final head, push it and run `gh pr ready <PR>`, which starts CI on it alongside them; the pilot's head stays a draft. Log each QC and review finding with its `class` in the lane's handoffs log (docs/adr/0020). Fix every blocking finding in a single **implementer subagent**; put notes in the PR body.

8. If a PR exists (step 7 marked it ready), send the merge ask to the director with `herdr-say --parent`: post the review verdict with `octo-feather-lane verdict <PR> <head> <report>`, write the merge ask (the head, each criterion's QC verdict, the review verdict link, the criterion ids flipped to built, each failed criterion with its triage) as the PR body's `## Merge ask` section, and send what `octo-feather-lane merge-ask <PR> --status <status file>` prints once it passes. Otherwise, resolve each ticket the way the issue tracker closes work, and report the integration branch.

9. Clean up all **implementer subagent** worktrees.
