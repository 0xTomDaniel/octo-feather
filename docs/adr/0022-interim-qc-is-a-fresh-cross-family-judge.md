# Until Jev, `just qc` is a fresh cross-family judge that runs each claimed criterion

`just qc STATUS PR ID...` (`scripts/octo-feather-qc`) is the product judge until Jev replaces it. In the lane worktree, at the integrated head, it starts a fresh code reviewer headless (`pi-role agents/code-reviewer.md -p`, ADR 0016; `openai/gpt-6.1-sol` high, read-only tools) with its own QC brief: judge the whole lane head against every criterion the lane claims (the ids given, their text read from the spec), find and run each criterion's demo path through the app's public surface (ADR 0009), and report one pass or fail per criterion with the command it ran and the output. The script, not the judge, then writes the status file (ADR 0021): each passed criterion becomes `built` with the lane's PR, each failed one stays `planned`, and only that file is committed. The judge's model family must differ from the implementer's, and the script refuses one that does not; it also refuses a dirty worktree, a report that does not name exactly the claimed ids, and a judge that changed the worktree. It is never part of `just check`. Decided by Tom (owner), 2026-10-19.

Order in a lane, the pilot included: integrate, then `just qc` on that head (its status commit is the only change it adds), then a fresh code review of the resulting head, then the merge ask, which names the head, each criterion's QC verdict and the review verdict. A failed criterion is a blocking finding (`source: qc`) for an implementer; any code change after QC means QC again. Decided by Tom (owner), 2026-10-19.

## Considered options

- Record QC as not run while `just qc` is a stub, and let the code reviewer's Spec pass stand in. Rejected: the Spec pass reads the diff and runs nothing, so a criterion can be claimed built without anyone having seen it work.
- Block every merge until Jev exists. Rejected: nothing could ship before Thursday.
- Let the supervisor or the implementer flip criteria to built. Rejected: the writer of the claim would be the party it judges.
- A judge from the implementer's family. Rejected: it shares the implementer's blind spots (ADR 0013's reviewer rule).

## Consequences

- Built means a fresh judge saw it pass at that head, not that Jev verified it. Jev replaces the judge behind the same recipe (docs/future.md).
- Each run leaves its report, with the judge's raw output, in `$(octo-feather-state)/qc/<head>.json`.
- Every target repo defines a `qc` recipe calling `octo-feather-qc`, as it does `integrate`; the templates do.
