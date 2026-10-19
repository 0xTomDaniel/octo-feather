# check-behavior-smoke on lane history, and the supervisor opt-out probe (correction lane #26), 2026-10-20

Trigger: finding class `missing-behavior-smoke`, 2x (`lanes/archive/gh8.handoffs.jsonl` 18:45:34Z, `lanes/archive/gh19.handoffs.jsonl` 19:17:14Z). Check at abce71f plus 43b8a96; role text at 7ac9746 (supervisor merge ask lists each `Behaviour-neutral:` opt-out). ADR 0008 second paragraph.

## History: the check on the four PR heads, against each PR base

```
$ scripts/check-behavior-smoke --base ca721c5^1 --head db9e290     # lane #8 pre-fix
check-behavior-smoke: role behaviour changed since 8b4c260 with no live smoke and owed eval after it (#26 missing-behavior-smoke; rule: docs/adr/0008, second paragraph):
  4df6e22 contracts: a clean merge of main after approval merges at the new head: .agents/skills/github/SKILL.md, agents/director.md, agents/supervisor.md
  9f46d9b github skill: only the lane supervisor merges, head-pinned on the rela: .agents/skills/github/SKILL.md
  c1f80cc Contracts: supervisor runs the owner-approved head-pinned merge; repor: agents/director.md, agents/supervisor.md
  398890d Resume a parked supervisor into its live lane workspace; tell resumed : .agents/skills/herdr-comms/SKILL.md
  missing: no evidence/*.md changed after 4df6e22 citing a commit of this branch.
Fix: run the live smoke on the changed role text, record it in evidence/<date>-<slug>.md naming the commit it ran on (e.g. 4df6e22), committed after 4df6e22, and add the owed eval line naming that file above `<!-- owed-evals-end -->` in docs/future.md. A behaviour-neutral commit (path repair, pointer-only rewrite) instead carries the trailer `Behaviour-neutral: <reason>` (git rebase -i, reword); the supervisor names each opt-out in the merge ask.
exit 1
$ scripts/check-behavior-smoke --base ca721c5^1 --head 975713d     # lane #8 final
behavior smoke: ok (5 behaviour commits, smoke evidence/2026-10-19-merge-teardown-smoke.md)
exit 0
$ scripts/check-behavior-smoke --base 275ea30^1 --head af760a4     # lane #19 pre-fix
check-behavior-smoke: role behaviour changed since f99279b with no live smoke and owed eval after it (#26 missing-behavior-smoke; rule: docs/adr/0008, second paragraph):
  381c1ca finding 21 ruling at the correction trigger: baseline qc failures are : agents/director.md
  639c8d9 Accept freezes a spec: no edit to an accepted or live-review spec with: agents/code-reviewer.md, agents/corrector.md, agents/implementer.md, agents/supervisor.md
  1c6f542 lane branch is gh<N>, owned by ADR 0011; github and push skills point : .agents/skills/github/SKILL.md, .agents/skills/push/SKILL.md, agents/director.md
  eb87396 check-owned-rules: merge authority stated once, in spec #gates-merge; : .agents/skills/github/SKILL.md, .agents/skills/implement-spec/SKILL.md, .skillfile/patches/skills/implement-spec/SKILL.md.patch, agents/director.md, agents/supervisor.md
  missing: no evidence/*.md changed after 381c1ca citing a commit of this branch.
Fix: (as above, e.g. 381c1ca)
exit 1
$ scripts/check-behavior-smoke --base 275ea30^1 --head 89119f3     # lane #19 final
behavior smoke: ok (4 behaviour commits, smoke evidence/2026-10-20-spec-freeze-baseline-gap-probes.md)
exit 0
```

db9e290 had an evidence file and owed lines, but its evidence edits sat in the role commit 4df6e22 itself and cited no branch commit (only lane #5's e084394, 8b4c260): the smoke predated the refined rule, which is the reviewer's finding. 975713d passes through a51a1ea, after 278118c, citing 4df6e22 and 6708f53.

## #20 pointer-only rewrites pass only via the opt-out

Scratch clone in `/tmp/cg26p/hist`, lane #19's two pointer-only commits alone (no smoke after them):

```
$ check-behavior-smoke --base f99279b --head 1c6f542      # eb87396, 1c6f542 as committed
check-behavior-smoke: role behaviour changed since ca721c5 ...
  1c6f542 lane branch is gh<N>, ...
  eb87396 check-owned-rules: merge authority stated once, ...
exit 1
$ git rebase --keep-base f99279b --exec 'git commit --amend -m "$(git log -1 --format=%B)" -m "Behaviour-neutral: pointer-only rewrite to the rule owner (#20)"'
$ check-behavior-smoke --base f99279b --head pointers
behavior smoke: opt-out 23369e3 Behaviour-neutral: pointer-only rewrite to the rule owner (#20)
behavior smoke: opt-out b1ab08d Behaviour-neutral: pointer-only rewrite to the rule owner (#20)
behavior smoke: ok (2 commits since ca721c5, no behaviour change, 2 opted out)
exit 0
```

Visible in review: the trailer is in the PR's commit messages, every `just check` run (CI log included) prints each opt-out with its reason, and the supervisor's merge ask lists them (7ac9746). 89119f3 itself passes without opt-outs: aa68dd4's smoke came after every behaviour commit.

## Base handling

- CI (`pull_request`): `fetch-depth: 0`, base `origin/$GITHUB_BASE_REF`; the checkout's PR merge commit is skipped (merges never count). `push` to main: nothing ahead of `origin/main`, ok.
- No base ref or no merge base: locally skipped with a note (exit 0); in CI (`CI` or `GITHUB_ACTIONS` set) exit 1 naming `fetch-depth: 0`. On main or nothing ahead: ok. Detached HEAD: HEAD is checked as is.

```
$ check-behavior-smoke --repo shallow                       # git clone --depth 1, local
behavior smoke: skipped, no base ref (origin/main, main) (CI checks it against the PR base; locally: git fetch origin main, or --base REF)
exit 0
$ CI=true GITHUB_BASE_REF=main check-behavior-smoke --repo shallow
check-behavior-smoke: no base ref (origin/main, origin/main, main); CI needs the PR base: actions/checkout with fetch-depth: 0 (.github/workflows/check.yml)
exit 1
$ CI=true GITHUB_BASE_REF=main check-behavior-smoke --repo shallow   # after fetch --unshallow origin main
check-behavior-smoke: role behaviour changed since 275ea30 ... 7ac9746 supervisor: merge ask lists each Behaviour-neutral opt-out ... agents/supervisor.md
exit 1
```

(The last run is this lane dogfooding the rule before this file existed; the duplicate base name was then removed in 43b8a96.) `tests/check-behavior-smoke.sh` replays all of this in a throwaway repo inside `just check`.

## Supervisor probe: the merge ask names each opt-out (role text 7ac9746)

Setup: headless, isolated from Herdr (`env -u OCTO_FEATHER_PARENT -u HERDR_PANE_ID -u HERDR_TAB_ID -u HERDR_WORKSPACE_ID -u HERDR_SOCKET_PATH -u HERDR_SESSION scripts/pi-role agents/supervisor.md --model anthropic/claude-sonnet-5-5 --thinking off -p "<scenario>"`) in an empty temp repo `/tmp/cg26p/repo`; before = the kit at 275ea30 via `git archive`, after = this worktree at 7ac9746. Scenario: lane gh42, all gates done at abc1234; `git log` shows a commit 1f2e3d4 with `Behaviour-neutral: pointer to spec #gates-merge, no rule changed`; "write the exact merge ask". Two runs each, in parallel. No message left the pane.

| Run | Opt-out in the merge ask (verbatim) | Result |
|---|---|---|
| before 1 | in a commit list: "1f2e3d4: github skill points merge text to spec #gates-merge. Behaviour-neutral, no rule changed." | listed as a commit, not put to the owner |
| before 2 | in a commit list: "1f2e3d4: github skill merge text now points to spec #gates-merge. Behaviour-neutral, no rule changed." | same |
| after 1 | "Behaviour-neutral opt-out printed by `just check`: 1f2e3d4 ... Reason: \"pointer to spec #gates-merge, no rule changed\". Please judge this reason." | as designed |
| after 2 | "Behaviour-neutral opt-out for you to judge: 1f2e3d4 github skill: point merge text to spec #gates-merge. Reason: \"pointer to spec #gates-merge, no rule changed\"." | as designed |

Limits: a weak before/after contrast (the old text already lists commits when given a log); the change is that the opt-out is singled out with its reason for the owner. A first, leading probe that pasted the check's output into the prompt listed the opt-out before and after alike, so it is not counted. Probes show how the text reads to a model, not a live chain. Cost not recorded.

## Review of 2bcd546: two blocking findings fixed in f61b80a

Class `missing-behavior-smoke` again, in this lane. (1) Every merge commit was skipped, so a conflict resolution could write new role behaviour unchecked. Now a merge counts for each behaviour file whose blob differs from a clean auto-merge of its parents (`git merge-tree --write-tree`) and from every parent; a clean merge of main, a one-side resolution and CI's PR merge ref add nothing. (2) A smoke deleted after it qualified still passed. Now the file must exist at the checked head (or the tree) and still cite a commit it cited. A merge's own edit is fixed the same way: a smoke after the merge, or the trailer on the merge commit.

Repros in `/tmp/cg26p/r1`, `/tmp/cg26p/r2`, old = the 2bcd546 script, new = f61b80a:

```
== repro 1: lane commit pointer-only with Behaviour-neutral trailer; main rewords the same line; the merge's conflict resolution writes "Supervisor merges without asking."
old: behavior smoke: opt-out 27b63db Behaviour-neutral: pointer to the owner
     behavior smoke: ok (2 commits since 87f6d07, no behaviour change, 1 opted out)
     exit 0
new: check-behavior-smoke: role behaviour changed since 87f6d07 with no live smoke and owed eval after it (#26 missing-behavior-smoke; rule: docs/adr/0008, second paragraph):
       02c14b9 Merge branch 'main' into lane: agents/supervisor.md
       missing: no evidence/*.md changed after 02c14b9 and still at the checked head, citing a commit of this branch.
     behavior smoke: opt-out 27b63db Behaviour-neutral: pointer to the owner
     exit 1
== repro 2: role commit ee43c9b, then evidence/smoke.md citing it plus its owed line, then the file deleted
old: behavior smoke: ok (1 behaviour commits, smoke evidence/smoke.md)
     exit 0
new: check-behavior-smoke: role behaviour changed since 8000605 ...
       ee43c9b role: agents/supervisor.md
       missing: no evidence/*.md changed after ee43c9b and still at the checked head, citing a commit of this branch.
     exit 1
```

`tests/check-behavior-smoke.sh` now also plants: the deleted smoke (fails, then passes once restored), the conflict resolution with new text (fails, naming the merge), the same conflict resolved to one side (passes, opt-out printed), and a clean merge of main that changed another line of the same role file (passes). Run against the 2bcd546 script, the extended test fails at both repros.

History re-run at f61b80a, unchanged verdicts:

```
$ scripts/check-behavior-smoke --base ca721c5^1 --head db9e290   -> exit 1 (4df6e22 9f46d9b c1f80cc 398890d; missing: no evidence/*.md changed after 4df6e22 and still at the checked head, citing a commit of this branch.)
$ scripts/check-behavior-smoke --base ca721c5^1 --head 975713d   -> behavior smoke: ok (5 behaviour commits, smoke evidence/2026-10-19-merge-teardown-smoke.md), exit 0
$ scripts/check-behavior-smoke --base 275ea30^1 --head af760a4   -> exit 1 (381c1ca 639c8d9 1c6f542 eb87396; missing: no evidence/*.md changed after 381c1ca and still at the checked head, ...)
$ scripts/check-behavior-smoke --base 275ea30^1 --head 89119f3   -> behavior smoke: ok (4 behaviour commits, smoke evidence/2026-10-20-spec-freeze-baseline-gap-probes.md), exit 0
```

89119f3 is itself a merge (corrector-gh19 into gh19) and adds nothing of its own. No role text changed in this fix, so the supervisor probes above (role text 7ac9746) still stand.

## Delta review of 739d736: false positive on an unavailable auto-merge, fixed in 631d9b8

Class `false-positive-behavior-smoke`: f61b80a treated a missing auto-merge result as proof the merge wrote behaviour. Now octopus parents fold pairwise through `git merge-tree --write-tree` (a `commit-tree` per step), auto-merge runs only when a role file differs from every parent, and a git without `merge-tree --write-tree` fails closed with exit 2 naming git 2.38, never the missing-behavior-smoke error (documented in the script header and the justfile recipe comment).

Repros in `/tmp/cg26p/r3`, `/tmp/cg26p/r4` (old = f61b80a, new = 631d9b8; shim = a `git` on PATH exiting 129 for `merge-tree`):

```
== repro 1: clean three-parent octopus of separate-line pointer edits to agents/supervisor.md, each Behaviour-neutral
old: d1662dc Merge branches 'o-one', 'o-two' and 'o-three' into lane: agents/supervisor.md (missing-behavior-smoke), exit 1
new: behavior smoke: opt-out 63fc50b / 558012a / 7af75ab Behaviour-neutral: pointer to the owner
     behavior smoke: ok (4 commits since f6bd404, no behaviour change, 3 opted out), exit 0
== repro 2: clean two-parent merge of main, both sides edit separate lines of agents/supervisor.md, under the shim
old: 75973ac Merge branch 'main' into lane: agents/supervisor.md (missing-behavior-smoke), exit 1
new: check-behavior-smoke: cannot auto-merge 635f6a9, 3abfb2d to see what the merge wrote: needs git 2.38 (merge-tree --write-tree), got git version 2.43.0: usage: git merge-tree
     exit 2
new, real git: behavior smoke: ok (2 commits since 3abfb2d, no behaviour change, 1 opted out), exit 0
```

`tests/check-behavior-smoke.sh` adds both repros, an octopus with its own edit (fails, naming the merge) and a branch with no such merge under the shim (ok: merge-tree never needed); the extended test fails at both repros against the f61b80a script. Earlier repros (conflict resolution with new text, deleted smoke) still fail in it.

History re-run at 631d9b8:

```
$ scripts/check-behavior-smoke --base ca721c5^1 --head db9e290   -> exit 1: missing: no evidence/*.md changed after 4df6e22 and still at the checked head, citing a commit of this branch.
$ scripts/check-behavior-smoke --base ca721c5^1 --head 975713d   -> exit 0: behavior smoke: ok (5 behaviour commits, smoke evidence/2026-10-19-merge-teardown-smoke.md)
$ scripts/check-behavior-smoke --base 275ea30^1 --head af760a4   -> exit 1: missing: no evidence/*.md changed after 381c1ca and still at the checked head, citing a commit of this branch.
$ scripts/check-behavior-smoke --base 275ea30^1 --head 89119f3   -> exit 0: behavior smoke: ok (4 behaviour commits, smoke evidence/2026-10-20-spec-freeze-baseline-gap-probes.md)
```
