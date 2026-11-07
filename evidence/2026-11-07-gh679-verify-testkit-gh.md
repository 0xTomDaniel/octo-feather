# gh679: the verify skill's correction and report drives fake GitHub with the testkit's gh

Change: tests/fixtures/tracker-gh/gh and tests/fixtures/lane-report/{gh,herdr} folded into the testkit's one gh and herdr (tests/gate/kit/testkit/gh.py, herdr.py) and deleted; verify-octo-feather's module (`fake_gh`, `tracker_issues`) and its docs repointed to it; the feature files' "proven by" pointers name the rewritten pytest items.

Smoke: .agents/skills/verify-octo-feather/SKILL.md (the fake-gh sentences: drives below)
Smoke: .agents/skills/verify-octo-feather/features/correction-intake.md (drive correction-intake below)
Smoke: .agents/skills/verify-octo-feather/features/correction-lane.md (drive correction-lane below)
Smoke: .agents/skills/verify-octo-feather/features/factory-report.md (drive factory-report below)
Smoke: .agents/skills/verify-octo-feather/features/template-tiers.md (drive template-tiers below)
Smoke: .agents/skills/verify-octo-feather/features/director-reflection.md (pointer only: the proving test's path, tests/gate/kit/test_director_reflect.py, which passes)

## Drives, lane gh653-679 head after merging gh653 4817a59 (`verify-octo-feather run FEATURE`)

- correction-intake: drive PASS (file-rule, intake); evidence records 20261106T234803Z-38169c4b, 20261106T234803Z-15ecfae7, 20261106T234803Z-682e925b.
- correction-lane: drive PASS (file-live, the real reflector, the tracker the testkit's gh); evidence record 20261106T234918Z-2067e888.
- factory-report: drive PASS (reflection-never, reflection-two-days, gate-budget-over, owner-caught-headline, skill-reach); evidence records 20261106T234920Z-0d440948, 20261106T234920Z-95034846, 20261106T234920Z-157135e8, 20261106T234921Z-f1695686.
- template-tiers: drive PASS, 17 of 17 cases (python and typescript: new-repo, check, fast-one-file, hook-core, fast-residual, trend, ci-status-only, ci-code); evidence record 20261107T025540Z-87220cf0 (comms#acceptance-report-gate-budget) beside the templates criteria's.

## Round 3 (review r7: recordings, never computed), lane head after merging gh653 ef42b60

The testkit gh answers another repo's correction-lane search and new issues only from recordings (fake_gh arms them; tracker_issues reads the creates it was sent): correction-intake drive PASS (evidence records 20261107T040919Z-dc40c805, 20261107T040919Z-596819a8, 20261107T040919Z-896f8770); correction-lane drive PASS (20261107T041021Z-bd1af427); factory-report drive PASS (20261107T041023Z-6448841f, 20261107T041023Z-f79fe176, 20261107T041024Z-f5748931, 20261107T041024Z-bb0846cb).
