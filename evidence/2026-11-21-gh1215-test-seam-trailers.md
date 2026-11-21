# gh1215: a worker's test commit declares its seams, refused at hand-off without a ticket record before it (correction lane #1121, class unlisted-test-seam)

Trigger: correction lane #1121 (issue-lifecycle spec #lanes-correction), ticket #1215, after pilot #1214. Class unlisted-test-seam in 8 lanes (#1121 and its comments), latest gh1186 #1210: test commit 646363b8 (03:04:59Z) drove `just check` and `just test`; their `Seam:` records were posted 04:36:25Z, after review caught it. Reflection route (gh987 log): worker-dispatch command with structured seam declarations.

Fix: `octo-feather-lane skills TICKET`, the supervisor's hand-off check, reads the worker's test commits and their `Seam:` trailers against the ticket's records (rules: `octo-feather-lane --help`, skills, Test seams; b98b2141). Rework: its send-back message alone fixes the miss in one step (the exact trailer, the ticket's records, issue-comment, the git commands), and the `tdd` skill's Seams step 1 gains one pointer to that help section (director ruling A on #1215).

Smoke: .agents/skills/tdd/SKILL.md .skillfile/patches/skills/tdd/SKILL.md.patch

The smoke is one headless implementer run with the patched skill (below, review finding unexercised-smoke at ffba6ee7), then the help section the pointer names and the refusal it prepares a worker for, run for real (script /tmp/demo1215/smoke.sh): real gh, the kit repo's real commit 646363b8, lane gh1186's real spawn line (cwd pointed at a scratch worktree), the worker's real Pi session, a scratch state dir. One run, no eval suite: the eval cases stay owed (docs/owed-evals/1215.md).

## Live smoke: a headless implementer with the patched tdd, 2026-11-21

Run: `pi-role agents/implementer.md --mode json -p <brief>` from this branch (be69c051 plus gh1121; its .agents/skills/tdd/SKILL.md the patched one), cwd a scratch git repo of fixture python-app (`check-evals --export`, committed on main, `uv sync --locked`), 11:59:00Z to 12:00:09Z, model anthropic claude-opus-5-5, Pi session 01a1fdf9-5e5b-7759-93ec-feb1f825f234 (transcript kept at $(octo-feather-state)/smoke/gh1215-implementer-01a1fdf9.jsonl, sha256 37e049199d0d46a03034e528ca0a63b1320c732b59d14104d7012e8f77cc72ec). Env: this branch's scripts/ first on PATH, GH_REPO=0xTomDaniel/octo-feather, no Herdr variables (no route to any pane). The ticket: real #1015 (closed scratch issue of lane gh987), whose comment `Seam: app#acceptance-greet: `app greet`` was written 2026-11-18T20:45:00Z, before the run. The brief: evals/seam-record case implementer-rework-new-seam's task word for word, its sandbox line dropped; it names no trailer and no seam.

What the role did (its tool calls, in order): read the github-issues and implement skills; read #1015 with `issue-view 1015 --notes`; read python and tdd SKILL.md; ran `octo-feather-lane seam 1015 app#acceptance-greet 'app greet'` (exit 0; no comment posted: the record was there); wrote the test and the command; `uv run pytest -q`, `just check` green; then, at commit time, `octo-feather-lane --help 2>&1 | grep -n -i 'trailer'` (the pointer's target) and committed:

```
$ git log -1 --format=%B 7d48293 | git interpret-trailers --parse
Seam: app#acceptance-greet: `app greet`
$ octo-feather-lane seam 1015 app#acceptance-greet 'app greet' --before 7d48293
1015: seam app#acceptance-greet `app greet` recorded at 2026-11-18T20:45:00Z (https://github.com/0xTomDaniel/octo-feather/issues/1015#issuecomment-6991114927), before commit 7d48293c
exit=0
```

Result: the test commit (7d48293, src/app/cli.py and tests/test_cli.py) carries the trailer in the ticket record's form, matching #1015's record written before it. One run, so a behaviour seen once, not a rate: the rate is the owed eval's (implementer-test-commit-trailer, against the baseline before the pointer).

Removed: nothing from tdd; the patch adds one pointer sentence to Seams step 1. Incident that justifies it: lane gh1186 #1210, test commit 646363b8 at seams not on the ticket before it (#1121).

## Live smoke, 2026-11-21

```
$ octo-feather-lane --help | sed -n "/^Test seams/,/rung 3)/p"
Test seams (correction lane #1121, ticket #1215; the rule: AGENTS.md Rules, a test's seam written down from the
ticket before any test, docs/adr/0002), after the skills, with or without a `Skills:` line. The worker's result: the
non-merge commits of its worktree's HEAD (the spawn line's `cwd`) that the lane worktree's HEAD lacks (`git rev-list
--no-merges <worker HEAD> --not HEAD`), so run it before integrating them; a worker whose cwd is the lane worktree
itself has no commits apart, said so, none checked. A test commit adds or changes (git diff-tree --diff-filter=AM,
no renames) a test file: a path under the repo's top-level tests/, or one a popular runner collects by its own
default pattern (pytest's test_*.py and *_test.py, Jest's and Vitest's __tests__/ and *.test|spec.{js,jsx,ts,tsx,
mjs,cjs,mts,cts}, go's *_test.go). Its known misses: a test that a runner's own configuration collects elsewhere,
since no repo's runner configuration is read. Each test commit declares the seams its tests drive, one git
trailer per seam in the ticket record's form, `Seam: <spec>#<anchor>: `<seam>`` or `Seam: rule: `<seam>``
(read with `git interpret-trailers --parse`); each one is judged as `seam TICKET <id> <seam> --before <commit>`
judges it (above), printing its line. A miss: a test commit with no `Seam:` trailer, one off the form, or a
declared seam `seam --before` fails (exit 1: unlisted-test-seam, no record or a late one; seam-off-criteria). It
prints `<ticket>: commit <sha8> ...` or seam's line, then `<ticket>: test seams: worker <name>, <n> commits the
lane head lacks, <k> adding or changing a test`. Each miss logs one finding line, in the same write as the
skills' ones: {at, kind: finding, source: skills, class: unlisted-test-seam, blocking, summary, ticket, commit}.
Sent back once, counted by the log as for a skill: the first time for a ticket (no blocking unlisted-test-seam
finding for it in the log) logs blocking true, prints the fix `<ticket>: fix: send <worker> back before integrate:
herdr-say <pane> <message>` and exits 1, the message shell-quoted and enough alone for a worker to fix it in one step:
each miss, the exact trailer, the ticket's records it must match (body or comment, written before the commit), the
tracker skill's issue-comment for a seam not there (and to tell the supervisor), and the git commands that add the
trailers keeping each author time (git rebase -i with git commit --amend --trailer, or git rebase --exec); later misses for that ticket log blocking false and
print `<ticket>: test seams: sent back once already; this miss stands recorded, not blocking`. Exit 2, could not
check, never blocking, recorded as skills-unchecked above, only when no first miss exits 1: a spawn line with no
cwd, a worker worktree or commit git cannot read, or a declared seam `seam --before` leaves unchecked (exit 2).
The limit: it proves a declaration and its record's time, a check on a declaration: whether a commit's tests drive
the seams its trailers declare, and whether every seam they drive is declared, stays with review (docs/adr/0008
rung 3).

$ (lane worktree at 646363b8^, worker at 646363b8) octo-feather-lane skills 1210
1210: commit 646363b8 adds or changes test tests/gate/heavy_slot.py, tests/gate/kit/fast_slot_free.py, tests/gate/kit/gate_recipes_first.py and 1 more with no `Seam:` trailer (form Seam: <spec>#<anchor>: `<seam>` (a rule-only ticket: Seam: rule: `<seam>`), the ticket record's form)
1210: test seams: worker implementer-gh1210, 1 commit the lane head lacks, 1 adding or changing a test
1210: 1 blocking finding line(s) in /tmp/demo1215/s/state/octo-feather/lanes/demo.handoffs.jsonl, class unlisted-test-seam: 646363b8
1210: fix: send implementer-gh1210 back before integrate: herdr-say w93:p3 'Ticket 1210: your test commits are refused: 646363b8: adds or changes test tests/gate/heavy_slot.py, tests/gate/kit/fast_slot_free.py, tests/gate/kit/gate_recipes_first.py and 1 more with no `Seam:` trailer (form Seam: <spec>#<anchor>: `<seam>` (a rule-only ticket: Seam: rule: `<seam>`), the ticket record'"'"'s form). Fix: each commit that adds or changes a test carries one git trailer per seam its tests drive, exactly `Seam: <id>: `<seam>`` (a rule-only ticket: `Seam: rule: `<seam>``), each the same id and seam as a `Seam:` record on ticket 1210 (its body or a comment) written before that commit. Records on 1210 now: Seam: quality#acceptance-fast-slot-free: `just fast` (written 2026-11-21T02:52:25Z); Seam: quality#acceptance-fast-slot-free: `just check` (written 2026-11-21T04:36:25Z); Seam: quality#acceptance-fast-slot-free: `just test` (written 2026-11-21T04:36:25Z). A seam your tests drive that is not there: post `Seam: <id>: `<seam>`` on 1210 with the tracker skill'"'"'s issue-comment and tell me (a record written after the commit is late: I ask the owner). Add the trailers, keeping each author time: git rebase -i 9552080bd55f, mark each test commit edit, at each run git commit --amend --no-edit --trailer '"'"'Seam: <id>: `<seam>`'"'"' (once per seam), then git rebase --continue; or, for every commit since 9552080bd55f: git rebase 9552080bd55f --exec '"'"'git commit --amend --no-edit --trailer "Seam: <id>: \`<seam>\`"'"'"'. Check each with octo-feather-lane seam 1210 <id> '"'"'<seam>'"'"' --before <commit>, then hand off again.'; integrate once octo-feather-lane skills 1210 no longer exits 1
exit=1

the worker's message, as herdr-say delivers it:
Ticket 1210: your test commits are refused: 646363b8: adds or changes test tests/gate/heavy_slot.py, tests/gate/kit/fast_slot_free.py, tests/gate/kit/gate_recipes_first.py and 1 more with no `Seam:` trailer (form Seam: <spec>#<anchor>: `<seam>` (a rule-only ticket: Seam: rule: `<seam>`), the ticket record's form). Fix: each commit that adds or changes a test carries one git trailer per seam its tests drive, exactly `Seam: <id>: `<seam>`` (a rule-only ticket: `Seam: rule: `<seam>``), each the same id and seam as a `Seam:` record on ticket 1210 (its body or a comment) written before that commit. Records on 1210 now: Seam: quality#acceptance-fast-slot-free: `just fast` (written 2026-11-21T02:52:25Z); Seam: quality#acceptance-fast-slot-free: `just check` (written 2026-11-21T04:36:25Z); Seam: quality#acceptance-fast-slot-free: `just test` (written 2026-11-21T04:36:25Z). A seam your tests drive that is not there: post `Seam: <id>: `<seam>`` on 1210 with the tracker skill's issue-comment and tell me (a record written after the commit is late: I ask the owner). Add the trailers, keeping each author time: git rebase -i 9552080bd55f, mark each test commit edit, at each run git commit --amend --no-edit --trailer 'Seam: <id>: `<seam>`' (once per seam), then git rebase --continue; or, for every commit since 9552080bd55f: git rebase 9552080bd55f --exec 'git commit --amend --no-edit --trailer "Seam: <id>: \`<seam>\`"'. Check each with octo-feather-lane seam 1210 <id> '<seam>' --before <commit>, then hand off again.

$ (in the worker worktree, the message's own command, <id> <seam> filled from its records) git rebase 9552080bd55f --exec 'git commit --amend --no-edit --trailer "Seam: quality#acceptance-fast-slot-free: \`just fast\`"'

Successfully rebased and updated detached HEAD.
7748246d author 2026-11-21T03:04:59+00:00
Seam: quality#acceptance-fast-slot-free: `just fast`

$ (fresh log: the send-back line removed) octo-feather-lane skills 1210
1210: seam quality#acceptance-fast-slot-free `just fast` recorded at 2026-11-21T02:52:25Z (https://github.com/0xTomDaniel/octo-feather/issues/1210), before commit 7748246d
1210: test seams: worker implementer-gh1210, 1 commit the lane head lacks, 1 adding or changing a test
exit=0
```

What it shows: 646363b8 as committed (no trailer) is refused, exit 1, the message naming the commit, the exact trailer form, #1210's three records with their times, issue-comment for a missing seam and the git commands. The message's own `git rebase --exec` command, run unchanged but for `<id>` and `<seam>` filled from its records, adds the trailer keeping the author time (03:04:59Z); the same check then passes, exit 0. Its limit, by design: 646363b8 also drove `just check`, recorded late; a commit declaring only `just fast` passes, and whether the declaration is complete stays with review (docs/adr/0008 rung 3; the check is a check on a declaration, a stopgap the owner rules on at merge).

Gate items `tests/gate/kit/test_lane_skills.py`: `seams` (#876 no trailer refused, sent back once; #1214 trailer recorded before, exit 0), `seams_fix` (#1210: the message's parts, its `git rebase --exec` run in the worker worktree makes the commit pass, a later `just check` declaration named late), `seams_unchecked` (worker worktree unreadable, exit 2). Red-checked: `seams_fix`'s assertions fail on b98b2141's script.
