# Lever runs of the 8 parity cases whose old side fails clean (ticket #1333)

Commands, exact. At 67ce2d7b: in a scratch git repo of 67ce2d7b's files (`git archive 67ce2d7b | tar -x`, committed, this worktree fetched as its origin for the kit history the lever reads), with the kit venv:

    GATE_WORKERS=4 uv run --project /home/exedev/src/octo-feather-gh1274-1333 --locked --offline python tests/parity/lever.py CASE

At the split (d52c6e79; the split commit on this branch differs from it in post_merge.py's docstring interface line only): the same command in this worktree.

Each section: the cause, then the lever's output at each commit and the clean old run's failing lines (from the lever's none.old.log).

## lane-judge

Changed on purpose: the old side posts a verdict from a report with no `Range:` line, which `octo-feather-lane verdict` now refuses ("report names no Range"): e00e89b3, PR #1223 (#1220), review rounds with Range. Retired in this branch (commit `test(parity): retire the six lane-judge cases`), no retargeted patch.

At 67ce2d7b, lever output:

```
lever: refused: (a) on the clean tree the old test did not run scripts/octo-feather-lane (coverage) (exit 2, log /tmp/parity-lane-judge-hrsuxe6d/none.old.log)
restored from cc7f6b7: tests/lane-judge.sh tests/spend-out
```

Clean old run fails with:

```
/tmp/cpchk/.git/octo-feather/parity-kit-rdkm8b8h/tests/lane-judge.sh exited 1 (its output: Captured stdout/stderr below)
lane-judge test: 'verdict 7 64adf7d /tmp/gate.N3Q8aN/tmp.riaFSpsiiJ/report' want exit 0, got 1:  octo-feather-lane verdict: report names no Range: add `Range: <from>..<to>`, the commit the review diffed from and the head it reviewed (scope: .agents/skills/code-review/SKILL.md (Verdict step)), then rerun
```

At the split (d52c6e79), lever output:

```
lever: refused: (a) on the clean tree the old test did not run scripts/lane_review.py (coverage) (exit 2, log /tmp/parity-lane-judge-4w1ij6r_/none.old.log)
restored from cc7f6b7: tests/lane-judge.sh tests/spend-out
```

Clean old run fails with:

```
/home/exedev/src/octo-feather/.git/octo-feather/parity-kit-fzhdbstx/tests/lane-judge.sh exited 1 (its output: Captured stdout/stderr below)
lane-judge test: 'verdict 7 01db278 /tmp/gate.Vuy9Iz/tmp.LOTlXXsaVO/report' want exit 0, got 1:  octo-feather-lane verdict: report names no Range: add `Range: <from>..<to>`, the commit the review diffed from and the head it reviewed (scope: .agents/skills/code-review/SKILL.md (Verdict step)), then rerun
```

## lane-judge-real-call-evidence

Changed on purpose: the old side posts a verdict from a report with no `Range:` line, which `octo-feather-lane verdict` now refuses ("report names no Range"): e00e89b3, PR #1223 (#1220), review rounds with Range. Retired in this branch (commit `test(parity): retire the six lane-judge cases`), no retargeted patch.

At 67ce2d7b, lever output:

```
restored from a00d2e09: tests/gate/kit/lane_judge.py tests/gate/kit/test_lane_judge.py
  old ran (clean tree): scripts/octo-feather-lane (exec scripts/octo-feather-lane)
defect: none  old: FAIL (exit 2)  new: pass (exit 0)
defect: first-question-dropped  old: FAIL (exit 2)  new: FAIL (exit 2)  (Seeded defect: judge drops the first judgment question by name (call-evidence) from those it answers.)
parity FAILS: want both pass with no defect, both fail on each; logs: /tmp/parity-lane-judge-real-call-evidence-fhd6ba4f
```

Clean old run fails with:

```
/tmp/cpchk/.git/octo-feather/parity-kit-ynb32tu0/.venv/bin/python /tmp/cpchk/.git/octo-feather/parity-kit-ynb32tu0/tests/gate/kit/lane_judge.py real_suite call-evidence exited 1 (its output: Captured stdout/stderr below)
    assert p.returncode == want, said
AssertionError: /tmp/cpchk/.git/octo-feather/parity-kit-ynb32tu0/scripts/octo-feather-lane verdict 7 50c4725 /tmp/gate.0wtDvW/pytest-of-exedev/pytest-0/prepared-base/report: exit 1, want 0
octo-feather-lane verdict: report names no Range: add `Range: <from>..<to>`, the commit the review diffed from and the head it reviewed (scope: .agents/skills/code-review/SKILL.md (Verdict step)), then rerun
```

At the split (d52c6e79), lever output:

```
restored from a00d2e09: tests/gate/kit/lane_judge.py tests/gate/kit/test_lane_judge.py
  old ran (clean tree): scripts/lane_review.py (open scripts/lane_review.py)
defect: none  old: FAIL (exit 2)  new: pass (exit 0)
defect: first-question-dropped  old: FAIL (exit 2)  new: FAIL (exit 2)  (Seeded defect: judge drops the first judgment question by name (call-evidence) from those it answers.)
parity FAILS: want both pass with no defect, both fail on each; logs: /tmp/parity-lane-judge-real-call-evidence-_s4b_rxu
```

Clean old run fails with:

```
/home/exedev/src/octo-feather/.git/octo-feather/parity-kit-eqh8pium/.venv/bin/python /home/exedev/src/octo-feather/.git/octo-feather/parity-kit-eqh8pium/tests/gate/kit/lane_judge.py real_suite call-evidence exited 1 (its output: Captured stdout/stderr below)
    assert p.returncode == want, said
AssertionError: /home/exedev/src/octo-feather/.git/octo-feather/parity-kit-eqh8pium/scripts/octo-feather-lane verdict 7 34faae6 /tmp/gate.YtdFQZ/pytest-of-exedev/pytest-0/prepared-base/report: exit 1, want 0
octo-feather-lane verdict: report names no Range: add `Range: <from>..<to>`, the commit the review diffed from and the head it reviewed (scope: .agents/skills/code-review/SKILL.md (Verdict step)), then rerun
```

## lane-judge-real-ticket-slice

Changed on purpose: the old side posts a verdict from a report with no `Range:` line, which `octo-feather-lane verdict` now refuses ("report names no Range"): e00e89b3, PR #1223 (#1220), review rounds with Range. Retired in this branch (commit `test(parity): retire the six lane-judge cases`), no retargeted patch.

At 67ce2d7b, lever output:

```
restored from a00d2e09: tests/gate/kit/lane_judge.py tests/gate/kit/test_lane_judge.py
  old ran (clean tree): scripts/octo-feather-lane (exec scripts/octo-feather-lane)
defect: none  old: FAIL (exit 2)  new: pass (exit 0)
defect: last-question-dropped  old: FAIL (exit 2)  new: FAIL (exit 2)  (Seeded defect: judge drops the last judgment question by name (ticket-slice) from those it answers.)
parity FAILS: want both pass with no defect, both fail on each; logs: /tmp/parity-lane-judge-real-ticket-slice-yekzet_4
```

Clean old run fails with:

```
/tmp/cpchk/.git/octo-feather/parity-kit-ducz2bk2/.venv/bin/python /tmp/cpchk/.git/octo-feather/parity-kit-ducz2bk2/tests/gate/kit/lane_judge.py real_suite ticket-slice exited 1 (its output: Captured stdout/stderr below)
    assert p.returncode == want, said
AssertionError: /tmp/cpchk/.git/octo-feather/parity-kit-ducz2bk2/scripts/octo-feather-lane verdict 7 81f79be /tmp/gate.GT7zX9/pytest-of-exedev/pytest-0/prepared-base/report: exit 1, want 0
octo-feather-lane verdict: report names no Range: add `Range: <from>..<to>`, the commit the review diffed from and the head it reviewed (scope: .agents/skills/code-review/SKILL.md (Verdict step)), then rerun
```

At the split (d52c6e79), lever output:

```
restored from a00d2e09: tests/gate/kit/lane_judge.py tests/gate/kit/test_lane_judge.py
  old ran (clean tree): scripts/lane_review.py (open scripts/lane_review.py)
defect: none  old: FAIL (exit 2)  new: pass (exit 0)
defect: last-question-dropped  old: FAIL (exit 2)  new: FAIL (exit 2)  (Seeded defect: judge drops the last judgment question by name (ticket-slice) from those it answers.)
parity FAILS: want both pass with no defect, both fail on each; logs: /tmp/parity-lane-judge-real-ticket-slice-xyi2nci2
```

Clean old run fails with:

```
/home/exedev/src/octo-feather/.git/octo-feather/parity-kit-89192s3i/.venv/bin/python /home/exedev/src/octo-feather/.git/octo-feather/parity-kit-89192s3i/tests/gate/kit/lane_judge.py real_suite ticket-slice exited 1 (its output: Captured stdout/stderr below)
    assert p.returncode == want, said
AssertionError: /home/exedev/src/octo-feather/.git/octo-feather/parity-kit-89192s3i/scripts/octo-feather-lane verdict 7 f0593e8 /tmp/gate.xkqGMZ/pytest-of-exedev/pytest-0/prepared-base/report: exit 1, want 0
octo-feather-lane verdict: report names no Range: add `Range: <from>..<to>`, the commit the review diffed from and the head it reviewed (scope: .agents/skills/code-review/SKILL.md (Verdict step)), then rerun
```

## lane-judge-rerun

Changed on purpose: the old side posts a verdict from a report with no `Range:` line, which `octo-feather-lane verdict` now refuses ("report names no Range"): e00e89b3, PR #1223 (#1220), review rounds with Range. Retired in this branch (commit `test(parity): retire the six lane-judge cases`), no retargeted patch.

At 67ce2d7b, lever output:

```
restored from a00d2e09: tests/gate/kit/lane_judge.py tests/gate/kit/test_lane_judge.py
  old ran (clean tree): scripts/octo-feather-lane (exec scripts/octo-feather-lane)
defect: none  old: FAIL (exit 2)  new: FAIL (exit 2)
defect: rerun-posts-new  old: FAIL (exit 2)  new: FAIL (exit 2)  (Seeded defect: a judge rerun posts a second judgment comment instead of updating the one in place.)
parity FAILS: want both pass with no defect, both fail on each; logs: /tmp/parity-lane-judge-rerun-pca49ydj
```

Clean old run fails with:

```
/tmp/cpchk/.git/octo-feather/parity-kit-yeek4np1/.venv/bin/python /tmp/cpchk/.git/octo-feather/parity-kit-yeek4np1/tests/gate/kit/lane_judge.py rerun_in_place exited 1 (its output: Captured stdout/stderr below)
    assert p.returncode == want, said
AssertionError: /tmp/cpchk/.git/octo-feather/parity-kit-yeek4np1/scripts/octo-feather-lane verdict 7 1dd3d9d /tmp/gate.IRTcM2/pytest-of-exedev/pytest-0/prepared-base/report: exit 1, want 0
octo-feather-lane verdict: report names no Range: add `Range: <from>..<to>`, the commit the review diffed from and the head it reviewed (scope: .agents/skills/code-review/SKILL.md (Verdict step)), then rerun
```

At the split (d52c6e79), lever output:

```
restored from a00d2e09: tests/gate/kit/lane_judge.py tests/gate/kit/test_lane_judge.py
  old ran (clean tree): scripts/lane_review.py (open scripts/lane_review.py)
defect: none  old: FAIL (exit 2)  new: pass (exit 0)
defect: rerun-posts-new  old: FAIL (exit 2)  new: FAIL (exit 2)  (Seeded defect: a judge rerun posts a second judgment comment instead of updating the one in place.)
parity FAILS: want both pass with no defect, both fail on each; logs: /tmp/parity-lane-judge-rerun-6qx4hwl5
```

Clean old run fails with:

```
/home/exedev/src/octo-feather/.git/octo-feather/parity-kit-v9_yz7sy/.venv/bin/python /home/exedev/src/octo-feather/.git/octo-feather/parity-kit-v9_yz7sy/tests/gate/kit/lane_judge.py rerun_in_place exited 1 (its output: Captured stdout/stderr below)
    assert p.returncode == want, said
AssertionError: /home/exedev/src/octo-feather/.git/octo-feather/parity-kit-v9_yz7sy/scripts/octo-feather-lane verdict 7 0210937 /tmp/gate.qvSnhA/pytest-of-exedev/pytest-0/prepared-base/report: exit 1, want 0
octo-feather-lane verdict: report names no Range: add `Range: <from>..<to>`, the commit the review diffed from and the head it reviewed (scope: .agents/skills/code-review/SKILL.md (Verdict step)), then rerun
```

## lane-judge-threshold-below

Changed on purpose: the old side posts a verdict from a report with no `Range:` line, which `octo-feather-lane verdict` now refuses ("report names no Range"): e00e89b3, PR #1223 (#1220), review rounds with Range. Retired in this branch (commit `test(parity): retire the six lane-judge cases`), no retargeted patch.

At 67ce2d7b, lever output:

```
restored from a00d2e09: tests/gate/kit/lane_judge.py tests/gate/kit/test_lane_judge.py
  old ran (clean tree): scripts/octo-feather-lane (exec scripts/octo-feather-lane)
defect: none  old: FAIL (exit 2)  new: FAIL (exit 2)
defect: below-says-meets  old: FAIL (exit 2)  new: FAIL (exit 2)  (Seeded defect: judge calls a held-out score below an accepted threshold meeting it (spec judgment#rule-calibration).)
parity FAILS: want both pass with no defect, both fail on each; logs: /tmp/parity-lane-judge-threshold-below-z1j34u0k
```

Clean old run fails with:

```
/tmp/cpchk/.git/octo-feather/parity-kit-hfsp6oga/.venv/bin/python /tmp/cpchk/.git/octo-feather/parity-kit-hfsp6oga/tests/gate/kit/lane_judge.py threshold below exited 1 (its output: Captured stdout/stderr below)
    assert p.returncode == want, said
AssertionError: /tmp/cpchk/.git/octo-feather/parity-kit-hfsp6oga/scripts/octo-feather-lane verdict 7 f31b6c3 /tmp/gate.27ImRI/pytest-of-exedev/pytest-0/prepared-base/report: exit 1, want 0
octo-feather-lane verdict: report names no Range: add `Range: <from>..<to>`, the commit the review diffed from and the head it reviewed (scope: .agents/skills/code-review/SKILL.md (Verdict step)), then rerun
```

At the split (d52c6e79), lever output:

```
restored from a00d2e09: tests/gate/kit/lane_judge.py tests/gate/kit/test_lane_judge.py
  old ran (clean tree): scripts/lane_review.py (open scripts/lane_review.py)
defect: none  old: FAIL (exit 2)  new: pass (exit 0)
defect: below-says-meets  old: FAIL (exit 2)  new: FAIL (exit 2)  (Seeded defect: judge calls a held-out score below an accepted threshold meeting it (spec judgment#rule-calibration).)
parity FAILS: want both pass with no defect, both fail on each; logs: /tmp/parity-lane-judge-threshold-below-ie369fwc
```

Clean old run fails with:

```
/home/exedev/src/octo-feather/.git/octo-feather/parity-kit-iwgymki6/.venv/bin/python /home/exedev/src/octo-feather/.git/octo-feather/parity-kit-iwgymki6/tests/gate/kit/lane_judge.py threshold below exited 1 (its output: Captured stdout/stderr below)
    assert p.returncode == want, said
AssertionError: /home/exedev/src/octo-feather/.git/octo-feather/parity-kit-iwgymki6/scripts/octo-feather-lane verdict 7 aee171b /tmp/gate.ogkI0r/pytest-of-exedev/pytest-0/prepared-base/report: exit 1, want 0
octo-feather-lane verdict: report names no Range: add `Range: <from>..<to>`, the commit the review diffed from and the head it reviewed (scope: .agents/skills/code-review/SKILL.md (Verdict step)), then rerun
```

## lane-judge-threshold-meets

Changed on purpose: the old side posts a verdict from a report with no `Range:` line, which `octo-feather-lane verdict` now refuses ("report names no Range"): e00e89b3, PR #1223 (#1220), review rounds with Range. Retired in this branch (commit `test(parity): retire the six lane-judge cases`), no retargeted patch.

At 67ce2d7b, lever output:

```
restored from a00d2e09: tests/gate/kit/lane_judge.py tests/gate/kit/test_lane_judge.py
  old ran (clean tree): scripts/octo-feather-lane (exec scripts/octo-feather-lane)
defect: none  old: FAIL (exit 2)  new: FAIL (exit 2)
defect: brier-reversed  old: FAIL (exit 2)  new: FAIL (exit 2)  (Seeded defect: judge's calibration reads a higher Brier as better, so a score meeting an accepted threshold is called below it (spec judgment#rule-calibration).)
parity FAILS: want both pass with no defect, both fail on each; logs: /tmp/parity-lane-judge-threshold-meets-j8ffswra
```

Clean old run fails with:

```
/tmp/cpchk/.git/octo-feather/parity-kit-jdng3_ic/.venv/bin/python /tmp/cpchk/.git/octo-feather/parity-kit-jdng3_ic/tests/gate/kit/lane_judge.py threshold meets exited 1 (its output: Captured stdout/stderr below)
    assert p.returncode == want, said
AssertionError: /tmp/cpchk/.git/octo-feather/parity-kit-jdng3_ic/scripts/octo-feather-lane verdict 7 05ff611 /tmp/gate.GHDPaK/pytest-of-exedev/pytest-0/prepared-base/report: exit 1, want 0
octo-feather-lane verdict: report names no Range: add `Range: <from>..<to>`, the commit the review diffed from and the head it reviewed (scope: .agents/skills/code-review/SKILL.md (Verdict step)), then rerun
```

At the split (d52c6e79), lever output:

```
restored from a00d2e09: tests/gate/kit/lane_judge.py tests/gate/kit/test_lane_judge.py
  old ran (clean tree): scripts/lane_review.py (open scripts/lane_review.py)
defect: none  old: FAIL (exit 2)  new: pass (exit 0)
defect: brier-reversed  old: FAIL (exit 2)  new: FAIL (exit 2)  (Seeded defect: judge's calibration reads a higher Brier as better, so a score meeting an accepted threshold is called below it (spec judgment#rule-calibration).)
parity FAILS: want both pass with no defect, both fail on each; logs: /tmp/parity-lane-judge-threshold-meets-qknuncjx
```

Clean old run fails with:

```
/home/exedev/src/octo-feather/.git/octo-feather/parity-kit-w4fstsqy/.venv/bin/python /home/exedev/src/octo-feather/.git/octo-feather/parity-kit-w4fstsqy/tests/gate/kit/lane_judge.py threshold meets exited 1 (its output: Captured stdout/stderr below)
    assert p.returncode == want, said
AssertionError: /home/exedev/src/octo-feather/.git/octo-feather/parity-kit-w4fstsqy/scripts/octo-feather-lane verdict 7 0df4cfc /tmp/gate.MlIVbt/pytest-of-exedev/pytest-0/prepared-base/report: exit 1, want 0
octo-feather-lane verdict: report names no Range: add `Range: <from>..<to>`, the commit the review diffed from and the head it reviewed (scope: .agents/skills/code-review/SKILL.md (Verdict step)), then rerun
```

## lane-tickets

A gate fault, not a behaviour change: the old run exits 127 at its first git call, "git (kit stash guard ...): no git on PATH after this guard, and OCTO_FEATHER_GIT is unset", the #1324 stash guard bug (fixed on main 50418ed5). Kept, its patches retargeted to scripts/lane_ticketing.py; check-parity green.

At 67ce2d7b, lever output:

```
lever: refused: (a) on the clean tree the old test did not run scripts/octo-feather-lane (coverage) (exit 2, log /tmp/parity-lane-tickets-lslmwjv4/none.old.log)
restored from 3e8c414: tests/fixtures/lane-tickets/bodies/10.json tests/fixtures/lane-tickets/bodies/101.md tests/fixtures/lane-tickets/bodies/102.md tests/fixtures/lane-tickets/bodies/103.md tests/fixtures/lane-tickets/bodies/104-uv-app.md tests/fixtures/lane-tickets/bodies/105-http.md tests/fixtures/lane-tickets/bodies/106-env-script.md tests/fixtures/lane-tickets/bodies/107-ui.md tests/fixtures/lane-tickets/bodies/108-rule.md tests/fixtures/lane-tickets/bodies/110-runnable-script.md tests/fixtures/lane-tickets/bodies/21-no-criterion.md tests/fixtures/lane-tickets/bodies/22-unknown-anchor.md tests/fixtures/lane-tickets/bodies/23-unknown-spec.md tests/fixtures/lane-tickets/bodies/24-gate-only.md tests/fixtures/lane-tickets/bodies/25-no-section.md tests/fixtures/lane-tickets/bodies/26-demo-not-last.md tests/fixtures/lane-tickets/bodies/27-bad-expand.md tests/fixtures/lane-tickets/bodies/28-judge-printf.md tests/fixtures/lane-tickets/bodies/33-test-script.md tests/fixtures/lane-tickets/bodies/35-factory-recipe.md tests/fixtures/lane-tickets/bodies/36-judge-persistence.md tests/fixtures/lane-tickets/bodies/40-inline-python.md tests/fixtures/lane-tickets/bodies/41-judge-story-anchor.md tests/fixtures/spec-status/good/demo.spec.html tests/lane-tickets.sh
```

Clean old run fails with:

```
/tmp/cpchk/.git/octo-feather/parity-kit-oa3cei6b/tests/lane-tickets.sh exited 127 (its output: Captured stdout/stderr below)
git (kit stash guard /tmp/gate.8o8JdM/tmp.GD5RA0MrlO/sys/git): no git on PATH after this guard, and OCTO_FEATHER_GIT is unset
git (kit stash guard /tmp/gate.8o8JdM/tmp.GD5RA0MrlO/sys/git): no git on PATH after this guard, and OCTO_FEATHER_GIT is unset
```

At the split (d52c6e79), lever output:

```
lever: refused: (a) on the clean tree the old test did not run scripts/lane_ticketing.py (coverage) (exit 2, log /tmp/parity-lane-tickets-xhp7rmss/none.old.log)
restored from 3e8c414: tests/fixtures/lane-tickets/bodies/10.json tests/fixtures/lane-tickets/bodies/101.md tests/fixtures/lane-tickets/bodies/102.md tests/fixtures/lane-tickets/bodies/103.md tests/fixtures/lane-tickets/bodies/104-uv-app.md tests/fixtures/lane-tickets/bodies/105-http.md tests/fixtures/lane-tickets/bodies/106-env-script.md tests/fixtures/lane-tickets/bodies/107-ui.md tests/fixtures/lane-tickets/bodies/108-rule.md tests/fixtures/lane-tickets/bodies/110-runnable-script.md tests/fixtures/lane-tickets/bodies/21-no-criterion.md tests/fixtures/lane-tickets/bodies/22-unknown-anchor.md tests/fixtures/lane-tickets/bodies/23-unknown-spec.md tests/fixtures/lane-tickets/bodies/24-gate-only.md tests/fixtures/lane-tickets/bodies/25-no-section.md tests/fixtures/lane-tickets/bodies/26-demo-not-last.md tests/fixtures/lane-tickets/bodies/27-bad-expand.md tests/fixtures/lane-tickets/bodies/28-judge-printf.md tests/fixtures/lane-tickets/bodies/33-test-script.md tests/fixtures/lane-tickets/bodies/35-factory-recipe.md tests/fixtures/lane-tickets/bodies/36-judge-persistence.md tests/fixtures/lane-tickets/bodies/40-inline-python.md tests/fixtures/lane-tickets/bodies/41-judge-story-anchor.md tests/fixtures/spec-status/good/demo.spec.html tests/lane-tickets.sh
```

Clean old run fails with:

```
/home/exedev/src/octo-feather/.git/octo-feather/parity-kit-uqef08zc/tests/lane-tickets.sh exited 127 (its output: Captured stdout/stderr below)
git (kit stash guard /tmp/gate.7STYzA/tmp.0YB3eJlw3f/sys/git): no git on PATH after this guard, and OCTO_FEATHER_GIT is unset
git (kit stash guard /tmp/gate.7STYzA/tmp.0YB3eJlw3f/sys/git): no git on PATH after this guard, and OCTO_FEATHER_GIT is unset
```

## lane-spend

A lever fault, not a behaviour change: the old test passes as its gate item at 67ce2d7b (`just test "tests/gate/test_gate.py::test_script[tests/lane-spend.sh]"` in the same scratch copy, the old files restored from 644fad70: 1 passed; the fake curl, instrumented for that one run to log its stdin, received `Authorization: Bearer sk-test-123` each time) and run directly at 67ce2d7b and at the split (`bash tests/lane-spend.sh` in a copy of each tree, old files restored: lane-spend: ok), and fails only in the lever's run (its reconcile row: the fake curl answers 401). Kept, its patches retargeted to scripts/lane_reporting.py; check-parity green.

At 67ce2d7b, lever output:

```
lever: refused: (a) on the clean tree the old test did not run scripts/octo-feather-lane (coverage) (exit 2, log /tmp/parity-lane-spend-t7o526yi/none.old.log)
restored from 644fad70: tests/fixtures/lane-spend/curl tests/lane-spend.sh tests/spend-out
```

Clean old run fails with:

```
/tmp/cpchk/.git/octo-feather/parity-kit-c0jcq8vh/tests/lane-spend.sh exited 1 (its output: Captured stdout/stderr below)
lane-spend test: reconcile row for today, want '  today          $1.500000    $0.250000    $1.250000  (1 ledger calls of unknown cost)' in: Spend ledger: /tmp/gate.noyoOO/tmp.sBa88L8WoV/state/octo-feather/sessions/rc/spend.jsonl (4 calls)
```

At the split (d52c6e79), lever output:

```
lever: refused: (a) on the clean tree the old test did not run scripts/lane_reporting.py (coverage) (exit 2, log /tmp/parity-lane-spend-ot9bya_z/none.old.log)
restored from 644fad70: tests/fixtures/lane-spend/curl tests/lane-spend.sh tests/spend-out
```

Clean old run fails with:

```
/home/exedev/src/octo-feather/.git/octo-feather/parity-kit-n_x44eeu/tests/lane-spend.sh exited 1 (its output: Captured stdout/stderr below)
lane-spend test: reconcile row for today, want '  today          $1.500000    $0.250000    $1.250000  (1 ledger calls of unknown cost)' in: Spend ledger: /tmp/gate.6rLfwJ/tmp.l4y2KLdtz2/state/octo-feather/sessions/rc/spend.jsonl (4 calls)
```
