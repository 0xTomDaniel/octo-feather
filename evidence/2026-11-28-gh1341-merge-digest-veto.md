# gh1341: the owner's veto of a digest-listed merge files a repair lane's parent issue

Change: `octo-feather-lane veto PR --said WORDS [--repo O/R]` (the director's pane only; check class declaration)
files a top-level repair issue through the tracker skill's issue-create naming the vetoed PR, its merge commit, the
recorded tier block and each spec call it added in full, marked DENIED with the `denied` field the repair lane sets;
appends a director-log `veto` line; prints the lane start for the issue. It refuses a PR not merged, one no sent
digest lists, and one already vetoed (naming its issue), nothing filed or recorded. agents/director.md gets the step:
on the owner's veto run `veto`, then the start it prints (issue-lifecycle #gates-digest, #gates-call-decision,
#acceptance-merge-digest-veto; issue 1341). The command: `octo-feather-lane --help`, veto; tests:
tests/gate/kit/lane_veto.py.

Smoke: agents/director.md, live director run in a scratch world (review round 2, unexercised-smoke), started 20261128T100206Z at 46d5fd40 (agents/director.md as committed there, unchanged since), exit 0: on the owner's "veto #52: gh1337 demo veto" the director really ran `HERDR_PANE_ID=w9:p99 octo-feather-lane veto 52 --said "veto #52: gh1337 demo veto" --repo 0xTomDaniel/octo-feather-realcase` (exit 0), which filed issue 54 on the stand-in and appended the veto line below; it ended with the start line it would run, `octo-feather-lane start 54 --goal 'Veto repair: PR #52' --outcome ... --brief-file <scratch>/state/octo-feather/veto/54.brief.md`, left unrun as the brief asked (no supervisor in a smoke). It reverted nothing and wrote no issue by hand (Live run, below).
Smoke: .agents/skills/verify-octo-feather/ `verify-octo-feather drive merge-tiers` on the same tree: every case PASS, the new veto cases among them (veto-refused, veto-not-merged, veto, veto-again); the committed head's records are in the commit message.

Removed: nothing from the role: the director had no veto step, so a veto had no written route (no hand-written repair issue rule to delete).

Demo (the ticket's): realcase issue https://github.com/0xTomDaniel/octo-feather-realcase/issues/54, filed by the real
`veto 52` from a scratch director pane in tests/gate/kit/lane_veto.py's world, its gh calls recorded as
tests/gate/kit/testkit/recordings/lane-veto-1341.json.

## Live run

World: tests/gate/kit/lane_veto.py's world, built by its own helpers in a kept scratch dir: both merges and the
digest of 2026-11-28 sent from the director's pane, every gh answer replayed from the testkit recordings; then the
fake gh's tape held only lane-veto-1341.json. XDG_STATE_HOME the world's state (director.toml pane w9:p99, its commit
identity `smoke`), cwd the world's director checkout, PATH first a stand-in gh dir and this worktree's scripts. The
stand-in gh passes every call to the testkit gh in tape mode, except `issue create` with the recorded title and repo,
which it answers with the recorded URL (issue 54) whatever the body, since the owner's words in --said may differ
from the recording's; it keeps that call's argv and body. Nothing reached GitHub, Herdr or the live state. A -p run
gets no HERDR_PANE_ID (scripts/pi-role, Headless), so the brief names the pane, as the director's pane would carry it.
Run: `pi-role agents/director.md --session-dir <scratch>/sessions -p "<brief>"` from the checkout.

Brief (verbatim):

```
Smoke run in a scratch state: everything you run here touches only scratch, so act as you would in your pane. This headless run has no HERDR_PANE_ID; your pane is w9:p99 (director.toml), so set HERDR_PANE_ID=w9:p99 on any command that checks your pane. Your working directory is your checkout of 0xTomDaniel/octo-feather-realcase.
Yesterday you sent the owner the merge digest of 2026-11-28 for 0xTomDaniel/octo-feather-realcase and recorded it sent. It listed PR #52, a tier 2 merge with one clarifying spec call, merged by lane gh50's supervisor without the owner.
The owner now writes to you: "veto #52: gh1337 demo veto".
Handle it. One limit for this smoke only: do not run any `octo-feather-lane start` (no supervisor may be started here); end with the exact start line you would run next, and every command you ran.
```

Commands the director ran (its session's bash calls, in order):

```
pwd; git remote -v; octo-feather-lane --help 2>&1 | sed -n '/veto/,/^$/p'; echo ---; octo-feather-lane veto --help 2>&1
S=$(octo-feather-state); echo $S; ls $S; cat $S/director.toml; tail -5 $S/director.handoffs.jsonl 2>/dev/null; which gh
cd <scratch>/director && HERDR_PANE_ID=w9:p99 octo-feather-lane veto 52 --said "veto #52: gh1337 demo veto" --repo 0xTomDaniel/octo-feather-realcase 2>&1; echo "exit $?"
tail -1 <scratch>/state/octo-feather/director.handoffs.jsonl; head -30 <scratch>/state/octo-feather/veto/54.brief.md
```

The first call's `veto --help` was refused by the pane check (pane unset): nothing filed or recorded.

gh calls (the testkit gh's log; `issue create` answered by the stand-in):

```
pr view 52 --json state,title,url,mergedAt,mergeCommit -R 0xTomDaniel/octo-feather-realcase
issue create --title Veto: revert or repair PR #52 [gh1337] digest recording: a tier 2 merge, one clarifies call (#1339) --body-file -   (GH_REPO=0xTomDaniel/octo-feather-realcase, no --parent)
```

Director log, the line the veto appended:

```
{"at": "2026-11-28T10:02:21Z", "kind": "veto", "repo": "0xTomDaniel/octo-feather-realcase", "pr": 52, "merge": "54fd326c27d4d5629a7a6edc5efb834f92df814d", "issue": "54", "said": "veto #52: gh1337 demo veto"}
```

Final reply (verbatim, scratch paths shortened):

```
I recorded the veto of PR #52 (the digest-recording change) and filed its repair ticket. Nothing has been reverted yet, and no supervisor was started, as this smoke run requires.

- **Repair ticket:** issue 54, "Veto: revert or repair PR #52". Its body records the merge commit `54fd326c27d4`, your words, how the merge was allowed (tier 2, waited for nobody), and the work: revert or repair that merge. The same text is in the lane brief at `<scratch>/state/octo-feather/veto/54.brief.md`.
- **Spec call:** lane gh50's supervisor made one clarifying call on the gh1337-demo spec: that "a day" means a UTC calendar day. The ticket quotes it in full and marks it denied by this veto. The repair lane writes the denial into the call log in the commit that reverts or repairs the merge.
- **Log:** I added one `veto` line (PR 52, merge, issue 54, your words) to `director.handoffs.jsonl`.

The next step is to run the start line below from this checkout.

**Next start line (not run):**
```
octo-feather-lane start 54 --goal 'Veto repair: PR #52' --outcome 'merge 54fd326c27d4 of PR #52, vetoed by the owner, reverted or repaired, each vetoed spec call marked denied' --brief-file <scratch>/state/octo-feather/veto/54.brief.md
```

**Commands run (all in `<scratch>/director`):**
1. `pwd; git remote -v; octo-feather-lane --help 2>&1 | sed -n '/veto/,/^$/p'; echo ---; octo-feather-lane veto --help 2>&1`. Exit 1: without `HERDR_PANE_ID`, `veto --help` refused because the pane was unset. Nothing was filed.
2. `S=$(octo-feather-state); echo $S; ls $S; cat $S/director.toml; tail -5 $S/director.handoffs.jsonl 2>/dev/null; which gh`
3. `cd <scratch>/director && HERDR_PANE_ID=w9:p99 octo-feather-lane veto 52 --said "veto #52: gh1337 demo veto" --repo 0xTomDaniel/octo-feather-realcase 2>&1; echo "exit $?"`. Exit 0.
4. `tail -1 <scratch>/state/octo-feather/director.handoffs.jsonl; head -30 <scratch>/state/octo-feather/veto/54.brief.md`
```

## Explanation run (earlier, not a smoke)

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
