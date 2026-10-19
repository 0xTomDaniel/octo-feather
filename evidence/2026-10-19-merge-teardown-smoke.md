# Head-pinned merge and close-report-first smoke (spec `#gates-merge`, `#transport-close-space`), 2026-10-19

Smoke for the owed eval cases on the supervisor's head-pinned merge and its close report before its own worktree is removed (ADR 0008, until `just qa` exists; ADR 0007). Real chains from the kit's own lanes, read from the director log `~/.local/state/octo-feather/director.handoffs.jsonl` and the archived lane logs `lanes/archive/gh2.handoffs.jsonl`, `lanes/archive/gh5.handoffs.jsonl` (read only). Lines quoted with their `at`.

## Owner decision

```
17:53:43Z note: owner decision (Tom via Exo): after owner says merge, the lane supervisor merges with gh pr merge N --merge --match-head-commit HEAD; moved head or failure: rebase, rerun gates, new merge ask; no landing agent. Applied now.
```

Later refined by Tom (spec `#gates-merge`, ADR 0007): a head moved only by merges of main that resolved no conflict, checks green, merges pinned to the new head with no new qc or merge ask, the done report naming both heads; any other change or a failed merge reruns the gates and sends a new merge ask. The line above is the rule as logged then.

## Lane #5 (CI lane), after the rule: pass

```
17:52:49Z director note: merge ask to owner: PR #7 head e084394, CI green run 39297546000, red proof 39297139696, review clear; supervisor parked
17:55:57Z director prod: owner said merge #7 at e084394; relayed to parked supervisor to merge head-pinned, then teardown, report before removing own worktree
17:56:04Z gh5 gate:     merge answered: "owner: merge #7 at e084394; supervisor merges (new owner rule)"
17:57:09Z director note: #7 merged by supervisor at 8b4c260 (head e084394), main CI green run 39298336577; lane torn down, director closed w5 and removed worktree gh5; clones on 8b4c260
```

Checked at source:
- `gh pr view 7`: `MERGED`, `headRefOid` e0843940858b, `mergeCommit` 8b4c26021a83: merged at the head the merge ask named.
- `gh run view 39298336577`: `push` on `main`, `headSha` 8b4c26021a83, `success`.

Result: the director relayed the yes with the head; the supervisor merged pinned to e084394 and reported; the director then closed space w5 and removed worktree gh5. Limits: GitHub's `mergedBy` is the shared account `0xTomDaniel`, so "merged by supervisor" rests on the director log; the close report itself went by `herdr-say` and has no log line of its own. Neither moved-head branch (clean main merge; other change, new merge ask) was exercised: the head did not move.

## Lane #2 (Pi trust prompt fix), before the rule: fail

```
17:42:36Z director prod: owner merged #4 (a6cb281, head 220dce8), headless as is; resumed supervisor for teardown
17:42:58Z director prod: owner merged #4 (a6cb281); herdr-say resume failed rc 73 (workspace gh2 exists); resumed supervisor via herdr-spawn --resume as w3:pB; sent teardown
17:43:26Z gh2 gate:     merge answered: "owner: merge #4; merged by director at a6cb281 (head 220dce8)"
17:45:27Z director note: gh2 torn down (worktrees, branches, archive); supervisor removed its own cwd and then failed API key resolution, so it never reported done; director closed space w3
```

Result: the director merged, and the supervisor removed its own worktree (its cwd), after which Pi could not resolve its API key and the close report never came (finding 9). Resuming the parked supervisor with `herdr-say` failed with rc 73 because its workspace gh2 still existed (fixed by #9: a parked supervisor resumes in its live lane workspace).

## Role probes, refined merge rule (spec `#gates-merge`), 2026-10-20

Setup as in `2026-10-19-role-probes.md`: the real role headless (`pi-role agents/supervisor.md --model anthropic/claude-sonnet-5-5 --thinking off -p "<scenario>"`, plus `--mode json` for cost) in an empty temp git repo, no Herdr session. Each prompt sets lane gh42 (PR #42, worktree `/work/gh42`, criteria acceptance-a acceptance-b), asks for next actions and commands, and says run nothing. Smoke sample (a) ran first and gave a real answer; then (b) to (d). Role text at 4df6e22 plus 6708f53.

| Probe | Scenario | Answer (abridged) | Result |
|---|---|---|---|
| (a) head unchanged | relay at aaa1111, PR head aaa1111, checks green | Re-reads the head and checks, then `gh pr merge 42 --merge --match-head-commit aaa1111`; "if this fails, never force"; then closes the issue, tears down, archives, reports. | as designed |
| (b) clean main merge | relay at aaa1111, head bbb2222 = one merge of main, no conflict, lane diff unchanged, checks green | Verifies one two-parent merge commit and `diff <(git diff origin/main...aaa1111) <(git diff origin/main...bbb2222)`, then `gh pr merge 42 --merge --match-head-commit bbb2222`, "no new `just qc` and no new merge ask". Done report: "Approved head aaa1111, merged head bbb2222". | as designed |
| (c) fix commit | relay at aaa1111, head ccc3333 adds "fix widget off-by-one" touching acceptance-a's code | "Do not merge at ccc3333 ... not a clean merge of main." Reruns `just check`, `just qc docs/specs/widget.status.json 42 acceptance-a acceptance-b`, a fresh review of the head QC left, then a new merge ask naming the new head; merges only on a relay naming it. | as designed (qc named both lane criteria, a superset of the affected one) |
| (d) close | just merged at aaa1111; workers and a worker worktree open | Closes the issue, removes scratch, review row, `/work/gh42-w43`, workers, archives the record, then reports "/work/gh42 left for you. Close space w7." Last step: "Never remove `/work/gh42` myself." | as designed |

No gaps found; no role text changed. Probes show how the text reads to a model, not a live chain: neither moved-head branch has run live yet.

Cost: (a) $0.045, (b) $0.038, (c) $0.035, (d) $0.037; $0.16 in all.
