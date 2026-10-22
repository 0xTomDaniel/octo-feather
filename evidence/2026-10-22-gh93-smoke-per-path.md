# Per-path smoke: check-behavior-smoke names each role path no `Smoke:` line covers (correction lane #93)

Correction of finding class `missing-behavior-smoke` (issue #93; rule docs/adr/0008; prior correction #26, PR #27). Owed eval: docs/owed-evals/93.md.

## Evidence (every finding of the class, `$(octo-feather-state)/lanes{,/archive}/*.handoffs.jsonl`)

- 2026-10-19 gh8, gh19, gh26: role change with no evidence at all; merge-skip and deleted-evidence holes in the first gate. Fixed by #26/#27 (presence gate) and its review rounds.
- 2026-10-22T02:52Z gh71 at 0035adc: "director.md:77 typed-call forwarding has no live smoke; evidence covers only the corrector".
- 2026-10-22T20:57Z gh67 at a60d12c: "implementer.md safety-fact hand-in and corrector.md writing-for-agents ship with no recorded live smoke".

Cause: after #26 the gate asked for *an* evidence file in the diff. Both repeats had one, for a different role, so the gate passed and review caught it a round later. `scripts/check-behavior-smoke` on main passes gh67 at a60d12c against its base (`behavior smoke: ok (21 role paths, ...)`). A prose mention is no proxy: a60d12c's `gh67-patch-prunes.md` names `agents/corrector.md` in its Changes list and `gh71-corrector-meaning-smoke.md` names `agents/director.md` in its quoted calls, though neither file ran those roles.

Fix (a fact, not meaning): each non-exempt role path must appear as a token on a `Smoke: <path> ...` line of an evidence file the diff adds or modifies (a token ending in `/` covers paths under it). The check reads the path, never the run; whether the run exercised it is review's (owed eval below).

## Demo: the gh71 and gh67 shapes replayed

Detached worktrees of the real lane heads, base = the lane's merge's first parent. Each existing evidence file gets a `Smoke:` line naming only what its own run exercised (its title and Setup say which role). gh71 also gets a `Removed:` line and an owed-evals file, rules that postdate it, so only the new rule acts. Then the lane's own round-2 fix is added.

```bash
#!/usr/bin/env bash
# Replay the gh71 and gh67 failure shapes through the new check-behavior-smoke.
# Each evidence file gets a Smoke: line naming only the paths its own run exercised.
set -uo pipefail
kit=$HOME/src/octo-feather-corrector-gh93
C=$kit/scripts/check-behavior-smoke
d=$(mktemp -d); trap 'git -C $kit worktree remove --force $d/w >/dev/null 2>&1; rm -rf $d' EXIT
c() { GIT_AUTHOR_NAME=d GIT_AUTHOR_EMAIL=d@d GIT_COMMITTER_NAME=d GIT_COMMITTER_EMAIL=d@d git -C $d/w commit -qam "$1"; }

echo "### gh71 at 0035adc (review: director.md:77 has no live smoke; evidence covers only the corrector)"
git -C $kit worktree add -q --detach $d/w 0035adc
e=$d/w/evidence/2026-10-22-gh71-corrector-meaning-smoke.md
echo 'Smoke: agents/corrector.md .agents/skills/correct/ .agents/skills/principle-encode-lessons-in-structure/ .skillfile/patches/skills/correct/ .skillfile/patches/skills/principle-encode-lessons-in-structure/' >> $e
echo 'Removed: (the Removed: rule postdates gh71)' >> $e
mkdir -p $d/w/docs/owed-evals; echo '- owed (owed-evals/<issue> postdates this lane)' > $d/w/docs/owed-evals/71.md; git -C $d/w add -A; c replay
echo '$ check-behavior-smoke --base 0d78571^1 (gh71 tip, corrector evidence only)'
python3 $C --repo $d/w --base '0d78571^1'; echo "exit $?"
echo; echo '+ evidence/2026-10-22-gh71-director-calls-smoke.md (the round-2 fix, 370aac2) with Smoke: agents/director.md'
git -C $d/w checkout -q 370aac2 -- evidence/2026-10-22-gh71-director-calls-smoke.md
echo 'Smoke: agents/director.md' >> $d/w/evidence/2026-10-22-gh71-director-calls-smoke.md; git -C $d/w add -A; c fix
python3 $C --repo $d/w --base '0d78571^1'; echo "exit $?"
git -C $kit worktree remove --force $d/w

echo; echo "### gh67 at a60d12c (review: implementer.md and corrector.md ship with no live smoke)"
git -C $kit worktree add -q --detach $d/w a60d12c
ev=$d/w/evidence/2026-10-22-gh67
echo 'Smoke: agents/supervisor.md' >> $ev-one-head.md
echo 'Smoke: .skillfile/patches/skills/ .agents/skills/code-review/ .agents/skills/blast-radius/ .agents/skills/implement-spec/ .agents/skills/tdd/ .agents/skills/writing-for-agents/' >> $ev-patch-prunes.md
echo 'Smoke: agents/qc-judge.md' >> $ev-qc-judge-skills.md
echo 'Smoke: agents/code-reviewer.md .agents/skills/interrogate/' >> $ev-reviewer-quality-only.md
c replay
echo '$ check-behavior-smoke --base 2d76eaf^1 (gh67 at a60d12c)'
python3 $C --repo $d/w --base '2d76eaf^1'; echo "exit $?"
echo; echo '+ evidence/2026-10-22-gh67-role-smokes.md (the round-2 fix, d4e2caa) with Smoke: agents/implementer.md agents/corrector.md'
git -C $d/w checkout -q d4e2caa -- evidence/2026-10-22-gh67-role-smokes.md agents/corrector.md
echo 'Smoke: agents/implementer.md agents/corrector.md' >> $ev-role-smokes.md; git -C $d/w add -A; c fix
python3 $C --repo $d/w --base '2d76eaf^1'; echo "exit $?"
```

Output (`bash demo.sh`, 2026-10-22):

```
### gh71 at 0035adc (review: director.md:77 has no live smoke; evidence covers only the corrector)
$ check-behavior-smoke --base 0d78571^1 (gh71 tip, corrector evidence only)
check-behavior-smoke: role paths changed since 40942b2 that no evidence file names on a `Smoke:` line (#93 missing-behavior-smoke: a smoke of one role does not cover another; rule: docs/adr/0008):
  agents/director.md
Fix: run a live smoke that exercises each path above and record it in evidence/<date>-<slug>.md with a line `Smoke: <path> ...` naming the paths that run exercised (a directory like `.agents/skills/<name>/` covers the files under it). Name only paths the recorded run loaded; a path no run exercised needs its own run, or the trailer `Behaviour-neutral: <reason>` when it changes no behaviour (docs/adr/0008).
behavior smoke: opt-out f9f1ec5 Behaviour-neutral: removes a false enforcement claim; every pointer and instruction is unchanged
exit 1

+ evidence/2026-10-22-gh71-director-calls-smoke.md (the round-2 fix, 370aac2) with Smoke: agents/director.md
behavior smoke: opt-out f9f1ec5 Behaviour-neutral: removes a false enforcement claim; every pointer and instruction is unchanged
behavior smoke: ok (6 role paths, evidence evidence/2026-10-22-gh71-corrector-meaning-smoke.md, evidence/2026-10-22-gh71-director-calls-smoke.md, owed evals docs/owed-evals/71.md, 2 opted out)
exit 0

### gh67 at a60d12c (review: implementer.md and corrector.md ship with no live smoke)
$ check-behavior-smoke --base 2d76eaf^1 (gh67 at a60d12c)
check-behavior-smoke: role paths changed since ae9bfb8 that no evidence file names on a `Smoke:` line (#93 missing-behavior-smoke: a smoke of one role does not cover another; rule: docs/adr/0008):
  agents/corrector.md
  agents/implementer.md
Fix: run a live smoke that exercises each path above and record it in evidence/<date>-<slug>.md with a line `Smoke: <path> ...` naming the paths that run exercised (a directory like `.agents/skills/<name>/` covers the files under it). Name only paths the recorded run loaded; a path no run exercised needs its own run, or the trailer `Behaviour-neutral: <reason>` when it changes no behaviour (docs/adr/0008).
exit 1

+ evidence/2026-10-22-gh67-role-smokes.md (the round-2 fix, d4e2caa) with Smoke: agents/implementer.md agents/corrector.md
behavior smoke: ok (21 role paths, evidence evidence/2026-10-22-gh67-one-head.md, evidence/2026-10-22-gh67-patch-prunes.md, evidence/2026-10-22-gh67-qc-judge-skills.md, evidence/2026-10-22-gh67-replay-51.md, evidence/2026-10-22-gh67-reviewer-quality-only.md, evidence/2026-10-22-gh67-role-smokes.md, owed evals docs/owed-evals/67.md, docs/owed-evals/backlog.md)
exit 0
```

Before the change, the same gh67 run with main's script (2d76eaf): `behavior smoke: ok (21 role paths, ...)`, exit 0.

The fixture test `tests/check-behavior-smoke.sh` (in `just check`) holds both shapes: gh71 (two roles, evidence names one; a prose mention of the other does not count) and the directory token.
