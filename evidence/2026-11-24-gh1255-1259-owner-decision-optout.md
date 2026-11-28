# gh1255 / #1259: the review report's owner decision and cleared opt-out lines; merge-ask tiers them

Spec: issue-lifecycle `#gates-tiers` (rows tier-owner-decision, tier-optout-cleared, tier-optout-uncleared), `#acceptance-tier-owner-decision`, `#acceptance-tier-optout-cleared`, `#acceptance-tier-optout-uncleared`. Ticket #1259 and its comment (the owner ruling of 2026-11-24, #1255).

Change: the code-review skill's Verdict step (one patch, `.skillfile/patches/skills/code-review/SKILL.md.patch`, materialized in `.agents/skills/code-review/SKILL.md`) names two more report fields, `Owner decision:` and `Opt-out cleared:`, with when a reviewer writes each and the old owner-gated list as examples. `octo-feather-lane verdict` carries them into the comment header, `fields` prints them, `merge-ask` tiers them (`octo-feather-lane --help`, verdict, fields, merge-ask Reasons).

Smoke: .agents/skills/code-review/ .skillfile/patches/skills/code-review/SKILL.md.patch

Removed: nothing deleted; the Report fields list gains two labels, two paragraphs follow the Range paragraph, and the reader-scope paragraph names the two labels. Incident: #1255 owner ruling 2026-11-24 (comment of 20:25Z, the director's term a): role and skill files are no longer owner-gated by path, so the owner's share of a lane must come from a line the review writes.

## Smoke: one live headless code-reviewer run on a fixture diff (2026-11-24)

Fixture: a scratch repo `/tmp/gh1259/cr` (a sandboxed command runner; AGENTS.md: the owner decides every ADR): main 6020182, lane commits 737d9d5 (`docs(agents): name the ADR the worker points to`, trailer `Behaviour-neutral: a pointer reworded, no instruction changed`) and b9891bf (`feat: allow network inside the sandbox`: drops `--unshare-net` in src/run.py and rewrites ADR 0001's decision). `check-behavior-smoke --base main` prints `behavior smoke: opt-out 737d9d5 ...`. The brief names neither field:

```
$ scripts/pi-role agents/code-reviewer.md -p "Review lane gh9 in this repo: branch lane, main is the base, from main up to HEAD b9891bf82c8764b37d5902a7e97606e251bdf69d. Report as your role requires."     # cwd /tmp/gh1259/cr, this worktree's kit
```

Final message (stdout, exit 0, 1m08s), verbatim:

```
Verdict: clear
Range: 60201824de737a4a671e30875dc4bfd08f28c4b3..b9891bf82c8764b37d5902a7e97606e251bdf69d
Owner decision: Permit network access inside the sandbox. `docs/adr/0001-sandbox.md:3` changes policy; `src/run.py:3` removes `--unshare-net`. `AGENTS.md` reserves ADR decisions to the repository owner. Review does not authorize this change.
Opt-out cleared: 737d9d530e857851ccd6470dc149e6434095f4cd
Checks: none
Prior art: none
Owner: docs/adr/0001-sandbox.md: network allowed inside the sandbox | restated: none

No blocking findings or non-blocking notes. Reviewed all changed files and both commits. The pointer-only commit is behavior-neutral; its opt-out does not cover the subsequent sandbox-policy change.

Validation: `git diff --check` and `check-behavior-smoke` passed. Runtime behavior not exercised.

**Delivery blocked:** `herdr-say --parent` exited 64: no parent recorded for this pane. Report not delivered. Next step: restore parent routing before another send.
```

The report carries one `Owner decision:` line for the ADR decision change and `Opt-out cleared:` for the opt-out's commit, at column 0 in the verdict reader's scope; `octo-feather-lane fields` on it prints `"Decision": {"owner": ["Owner decision: Permit network access ..."], "cleared": ["737d9d530e857851ccd6470dc149e6434095f4cd"], "errors": []}`. (The herdr-say failure is the headless run's: no parent pane.) One observed run, no baseline run, not comparative eval proof: the eval case is owed (docs/owed-evals/1259.md).

## Demo: realcase PRs on 0xTomDaniel/octo-feather-realcase (tests/gate/kit/lane_merge_optout.py)

Verdicts posted by this branch's `octo-feather-lane verdict`; each merge ask run from a clone of the realcase repo, gh recorded (testkit/recordings/merge-tier-1259.json). PR #19 (two opt-outs, the verdict clearing 86fdb97, and an owner decision line), its tier block:

```
$ octo-feather-lane merge-ask 19
Tier: 3
- Owner decision: the demo lane asks the owner to read its notes
- opt-out 86fdb97 cleared by the review verdict: Behaviour-neutral: a new note no role loads
- opt-out fe72f6c not cleared by the review verdict: Behaviour-neutral: a new note no role loads
Waits for: the owner
```

PR #16 (opt-out cleared): `Tier: 2`, `- opt-out 6195f3b cleared by the review verdict: ...`, `Waits for: nobody`. PR #17 (not named): `Tier: 3`, `- opt-out eac74d9 not cleared by the review verdict: ...`, `Waits for: the owner`. PR #18 (owner decision in the verdict, none in the section): `Tier: 3`, `- Owner decision: lib.py adds SANDBOX = False, a change to the sandbox policy (ADR 0022)`, `Waits for: the owner`.
