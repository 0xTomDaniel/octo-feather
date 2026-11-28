# gh1341: the owner's veto of a digest-listed merge files a repair lane's parent issue

Change: `octo-feather-lane veto PR --said WORDS [--repo O/R]` (the director's pane only; check class declaration)
files a top-level repair issue through the tracker skill's issue-create naming the vetoed PR, its merge commit, the
recorded tier block and each spec call it added in full, marked DENIED with the `denied` field the repair lane sets;
appends a director-log `veto` line; prints the lane start for the issue. It refuses a PR not merged, one no sent
digest lists, and one already vetoed (naming its issue), nothing filed or recorded. agents/director.md gets the step:
on the owner's veto run `veto`, then the start it prints (issue-lifecycle #gates-digest, #gates-call-decision,
#acceptance-merge-digest-veto; issue 1341). The command: `octo-feather-lane --help`, veto; tests:
tests/gate/kit/lane_veto.py.

Smoke: agents/director.md, headless director run (pi-role agents/director.md -p) on this lane's uncommitted tree over 4ad488f8, started 20261128T091755Z, exit 0: on the owner's "veto #52" it runs `octo-feather-lane veto 52 --said "<his words>" --repo <realcase>`, then the `octo-feather-lane start` line veto prints last, from its checkout of that repo; it reverts nothing and writes no repair issue itself, citing "Revert nothing yourself and write no repair issue by hand".
Smoke: .agents/skills/verify-octo-feather/ `verify-octo-feather drive merge-tiers` on the same tree: every case PASS, the new veto cases among them (veto-refused, veto-not-merged, veto, veto-again); the committed head's records are in the commit message.

Removed: nothing from the role: the director had no veto step, so a veto had no written route (no hand-written repair issue rule to delete).

Demo (the ticket's): realcase issue https://github.com/0xTomDaniel/octo-feather-realcase/issues/54, filed by the real
`veto 52` from a scratch director pane in tests/gate/kit/lane_veto.py's world, its gh calls recorded as
tests/gate/kit/testkit/recordings/lane-veto-1341.json.

The smoke run had a scratch state dir (its commit identity `smoke`) and no route to any pane (-p); the brief forbids
every write, message, octo-feather-lane and gh command.

## Director run

Brief (verbatim):

```
Smoke check, read-only. Do not edit any file, commit, spawn, close or message any agent or pane; run no octo-feather-lane command and no gh command.
Yesterday you sent the owner the merge digest of 2026-11-28 for 0xTomDaniel/octo-feather-realcase and recorded it sent. It listed PR #52, a tier 2 merge with one clarifying spec call, merged by lane gh50's supervisor without the owner.
The owner now writes to you: "veto #52, that clarification reads the rule wrong".

From your role file only, answer in at most 6 lines:
1. Each command you run, in order, with its arguments.
2. Do you revert the merge or write the repair issue yourself? Why or why not?
```

Answer (verbatim):

```
1. `octo-feather-lane veto 52 --said "veto #52, that clarification reads the rule wrong" --repo 0xTomDaniel/octo-feather-realcase`
2. Then the `octo-feather-lane start ...` line that veto prints last, run exactly as printed from my checkout of 0xTomDaniel/octo-feather-realcase.
3. I would not revert the merge or write the repair issue myself. The role file's Veto section says "Revert nothing yourself and write no repair issue by hand." The veto command records the veto, and the start line it prints opens the repair lane.
4. I also merge nothing and edit no files, so a revert or hand-written fix would be outside my role. The repair goes to a supervisor's lane.
5. I ran nothing here, since this is a read-only check. Both commands come only from the role file's Veto section.
```
