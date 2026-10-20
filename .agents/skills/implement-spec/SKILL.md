---
name: implement-spec
description: "Implement the result of /to-spec and /to-tickets in code."
---

You have been provided a spec. This spec should have tickets associated with it, describing how to implement the spec.

The issue tracker is GitHub Issues, through the `github` skill.

The goal is the lane's criteria of the spec (your brief names them) implemented on a single **integration branch**, with every ticket resolved the way the issue tracker closes work.

The tickets are not a list of steps. They are a **task graph** with blocking relationships between them. This means there is always a **frontier** of tickets which are ready to be grabbed.

Communication to and from subagents should be sparse. Communicate primarily through **context pointers**: to the spec, tickets, research notes, and previous commits. Don't duplicate information already available via pointers.

**Implementer subagents** should be run in the background where possible for maximum concurrency.

## Steps

1. Read the spec and tickets to understand the task graph.

2. (optional) Use an **exploration subagent** to conduct any exploration required by the tickets - relevant codebase files or external documentation. Ensure the exploration subagent can save files - it should save its markdown notes in a directory outside the repo, accessible by all future subagents. This lets **implementer subagents** focus on implementation rather than exploration.

3. Create the integration branch. If the issue tracker closes work through PRs, or the user asks for one, open a draft PR after the first merge in step 5 (a branch with no commits ahead of main can't open one), marked as closing the spec and tickets.

4. Pilot first (docs/adr/0019): run the lane's first ticket alone through steps 4, 5 and 7 (one implementer, `just integrate`, the draft PR, `just qc` on the pilot's criteria, code review of the head QC left), then fix the brief template and re-cut the remaining tickets before fanning out. Use **implementer subagents** to implement each ticket, each in its own worktree on its own branch: a Herdr worker, `herdr-spawn --role implementer` in tab `worker-<k>`. Each implementer subagent:
   - confirms its worktree is based on the integration branch before starting, and resets onto it if not;
   - calls the Skill tool with `tdd` to build the ticket;
   - merges the integration branch tip into its own branch before reporting done

5. Once an **implementer subagent** completes, merge its work to the integration branch yourself: run `just integrate <issue> <worker branch or commit>` (docs/adr/0017). It exits non-zero on a conflict or a red `just check` and leaves the branch as it was; hand that to an implementer, then integrate its result.

6. If this changes the **frontier** of available tickets, kick off more **implementer subagents** to work on the new tickets. This allows for maximum concurrency.

7. Once all tickets are complete and `just check` is green, run `just qc <status file> <PR> <the lane's criterion ids>` on the integration head (docs/adr/0022): it flips the passed criteria to built in a status-only commit, and a failed one is a blocking finding. Then spawn a fresh `code-reviewer` pane on the head QC left. Never review in your own context. Which later changes to the head need `just qc` and a fresh review again is spec `#lanes-one-head` and `#gates-merge` (docs/adr/0022); read it there, never restate it. Log each QC and review finding with its `class` in the lane's handoffs log (docs/adr/0020). Fix every blocking finding in a single **implementer subagent**; put notes in the PR body.

8. If a draft PR exists, mark it ready for review and send the merge ask to the director with `herdr-say --parent`: post the review verdict with `octo-feather-lane verdict <PR> <head> <report>`, write the merge ask (the head, each criterion's QC verdict, the review verdict link, the criterion ids flipped to built, each failed criterion with its triage) as the PR body's `## Merge ask` section, and send what `octo-feather-lane merge-ask <PR> --status <status file>` prints once it passes. Otherwise, resolve each ticket the way the issue tracker closes work, and report the integration branch.

9. Clean up all **implementer subagent** worktrees.
