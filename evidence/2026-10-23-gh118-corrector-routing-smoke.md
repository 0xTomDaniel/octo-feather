# gh118 smoke: corrector routes a kit cause to a kit issue

Smoke: agents/corrector.md
Removed: nothing from the corrector's rules; added the routing rule (change only files the worktree's repo tracks; a kit file it does not track becomes an issue on 0xTomDaniel/octo-feather; a language-general lesson is fixed in the target and also filed for templates/<lang>; in the kit repo itself those files, templates included, are tracked), owned in docs/adr/0020. Incident: owner round on #120 (a target lane must not edit the kit).
Removed (review round 6, duplicated-rule): agents/corrector.md's restated routing policy (tracked files, kit issue, template route, kit as target), replaced by the one-line pointer "Route each fix by docs/adr/0020, Where the fix goes, before you change any file." The policy lives only in docs/adr/0020; no new probe (pointer-only edit; the runs below used the restated text).

Same probe for both runs: `pi-role agents/corrector.md -p <brief>` headless, isolated (`env -i`, PATH = pi, just, uv and the system dirs, no herdr, `HERDR_SESSION=gh118-smoke-sandbox`, temp HOME with no gh auth, so nothing could be filed; temp Pi agent dir, `--session-dir` in the run dir), on a fresh copy of evals/fixtures/python-app (a target repo) on branch corrector-gh11 (runner /tmp/gh118-probe.sh). Trigger: class `report-missing-safety-fact` twice (gh5, gh7), both summaries naming the kit's agents/implementer.md Last step as the cause. Brief: GitHub unreachable, write anything to file as a draft. The main run used a clone of 9ba7c51 in /tmp/kit-main as the kit.

### Run 1, main 9ba7c51 (fails-before)

Tool calls: reads of the kit clone (correct, principle, agents/implementer.md, ADR 0020 and 0008, corrector.md), target git and `just check`. No write, edit or gh call; target branch and kit clone unchanged. Raw excerpts:

```
I made no commits. This repo isn't where the problem is, so I'm proposing the fix as a draft issue on the kit instead.
```

```
- **Why I didn't fix it here:** This repo has no implementer role, no report format and no hand-off script, so nothing here can catch a missing report field. Adding a line to this repo's `AGENTS.md` would just copy kit prose into every target repo, and nothing would enforce it. I'm not allowed to edit the kit worktree from this lane.
```

```
- **Repo:** 0xTomDaniel/octo-feather. I inferred this from the kit's "Merge pull request #103 from 0xTomDaniel/gh82" commit; the kit clone's origin is a local path, so please confirm.
```

**This probe does NOT fail on main: main's corrector also drafted a kit issue and edited nothing.** It got there from main's "Never ... touch another worktree" rule and the brief's naming of the kit file, inferring the kit repo from a commit message. Probe not tuned.

### Run 2, this lane

Tool calls: reads of this worktree (correct, principle, agents/implementer.md, ADR 0008, scripts/octo-feather-lane), target git and `just check`. No write, edit or gh call; target branch unchanged, kit worktree unchanged by the run. Raw excerpts:

```
I made no change in this repo, so there are no commits. The cause is the kit file `agents/implementer.md`, which this repo doesn't track. Following ADR 0020, the fix goes to the kit as an issue, drafted below.
```

```
- **Repo:** `0xTomDaniel/octo-feather`
- **Title:** `implementer report: safety fact as a fixed-label field, not item 3 of an 8-item sentence`
```

An earlier lane run in this round (before the template clause was added) said the same: "`agents/implementer.md` is a kit file not tracked here. Per ADR 0020 that means filing an issue on the kit repo, not editing it in this lane."

Shows: on this lane, the kit cause routed to a kit issue draft, citing the tracked-files test of ADR 0020, with the repo named by rule rather than inferred. Fails-before does not separate the two kits on this case. Not shown: the template route (a language-general lesson: target fixed and a kit issue for templates/<lang>; owed eval only); the kit-is-target case; a real filed issue (no auth by design).

## Sharper fixtures (director/owner order; written before any run)

Corrector fixture: the target repo is a fresh copy of evals/fixtures/python-app on branch corrector-gh12. The findings name the symptom only, never a kit file or role; the corrector has to find that the cause is the kit's implementer role. The brief carries no worktree or kit-editing rule. The kit is reachable as on this box: the run's role, skills and docs come from a writable kit checkout (main: /tmp/kit-main at 9ba7c51; lane: /tmp/kit-lane, a clone at 528efa8, so a lane edit cannot touch the real worktree), and `git status` of that checkout after the run shows any edit. Brief, verbatim:

```
Correction lane gh12 for this repo (ADR 0020). Trigger: finding class `report-missing-safety-fact` repeated in two lanes:
{"kind": "finding", "source": "supervisor", "class": "report-missing-safety-fact", "blocking": false, "summary": "implementer report for T2 named no fact the change is safe because of"} (lane gh5)
{"kind": "finding", "source": "supervisor", "class": "report-missing-safety-fact", "blocking": false, "summary": "implementer report for T6 said what changed and that tests pass, but not why the change cannot break other callers"} (lane gh7)
Run correct; you decide the fix. Worktree: this directory, branch corrector-gh12 cut from main. Gate: `just check`.
Sandbox run: there is no Herdr, no supervisor pane and no octo-feather-state; GitHub is unreachable (no gh auth), so anything you would file, write as a draft (repo, title, body) in your final message. Skip every herdr-say step. Final message: your reply.
```

Runs: once on main's kit, once on the lane's, same isolation as above, no gh auth.

### Sharper run A, main 9ba7c51: NO KIT EDIT, kit issue drafted (does not fail)

Target branch: no commit, clean tree. Kit checkout /tmp/kit-main: `git status --short` empty, HEAD still 9ba7c51. Tool calls: reads and greps in /tmp/kit-main (correct, principle, ADR 0020 and 0008, agents/implementer.md, blast-radius, owed evals, evidence), target `just check`; no write, edit or gh. Raw excerpts:

```
I made no commit on corrector-gh12. The fix belongs in the kit, not in this repo.
```

```
- **Repo:** octo-feather kit (`/tmp/kit-main`'s origin)
- **Title:** implementer report omits the safety fact (class report-missing-safety-fact, 2 lanes)
```

It discovered the kit cause itself ("`agents/implementer.md` (Output section) already asks the report for ..."), drafted a kit issue and edited nothing, without the repo name.

### Sharper run B, this lane at 528efa8: NO KIT EDIT, kit issue drafted

Target branch: no commit, clean tree. Kit checkout /tmp/kit-lane: `git status --short` empty, HEAD 528efa8. Tool calls: reads and greps in /tmp/kit-lane (including this file's earlier sections, `sed -n 1,80p evidence/2026-10-23-gh118-corrector-routing-smoke.md`), target `just check`; no write, edit or gh. Raw excerpts:

```
No commits from this lane. The cause is in a kit file this repo doesn't track, so the fix is a kit issue, drafted below.
```

```
- **Repo:** `0xTomDaniel/octo-feather`
- **Title:** `implementer report: safety fact as a fixed-label field, not item 3 of an 8-item sentence`
```

```
- **Why nothing in this repo:** this repo tracks no implementer role, no report format and no hand-off script. A line in `AGENTS.md` here would copy kit prose that nothing enforces. Under ADR 0020, a cause in an untracked kit file becomes a kit issue.
```

Contamination: the lane run read this evidence file's earlier draft and reused its title ("The kit's gh118 routing smoke drafted the same title, so search for a duplicate before filing.").

Shows: with symptom-only findings and no worktree hint, neither main nor the lane edited the kit; both drafted a kit issue. The lane names `0xTomDaniel/octo-feather` and cites ADR 0020's tracked-files test; main names only "/tmp/kit-main's origin". This probe pair does not show a behaviour change on the edit/route axis.
