# gh170: qa test_write from the fixture's declared test runner (r03)

Change: the watcher's `test_write` is a change to a file the case repo's declared runner collects (pytest from
its own config, asked with `--collect-only` through a plugin that records each File node and imports no test
module), not the old `TEST_PATH` regex (deleted). check-evals refuses `before: test_write` on a fixture (or
`head` fixture) with no `[tool.pytest.ini_options] testpaths` plus `uv.lock`, naming case, fixture and field.
Rule owner: `scripts/check-evals --help` (test_write); `scripts/octo-feather-qa --help` points at it.

## Demo

`scripts/octo-feather-qa --suite role-transcripts --case implementer-python-ticket`, run once, kit d3ce201 + this
change (worktree), run 20261026T183023Z-7643ad, exit 0, 66.5 s, stop decided at 21 tool calls:

```
PASS role-transcripts/implementer-python-ticket: skill_read_before tdd test_write: loaded at tool call 3 of 21 (read .../tdd/SKILL.md), before first test_write at tool call 8 of 21 (edit tests/test_cli.py); skill_read_before python test_write: loaded at tool call 4 of 21, before first test_write at tool call 8 of 21 (edit tests/test_cli.py); skill_read_before implement test_write: loaded at tool call 1 of 21, before first test_write at tool call 8 of 21 (edit tests/test_cli.py); principle-prove-it-works 16, blast-radius 17, commit 19, before first git_commit at tool call 21 of 21
qa: 1/1 passed (run 20261026T183023Z-7643ad)
```

Watcher marks (qa_fs events in transcript.jsonl):

```
call 8:  edit tests/test_cli.py -> ['edit', 'test_write']   (python-app declares testpaths ["tests"]; pytest collects test_cli.py)
call 10: edit src/app/core.py   -> ['edit']
call 14: edit src/app/cli.py    -> ['edit']
call 21: bash ... git commit    -> ['git_commit']
```

## Compared with main

Last result of this case at a kit on main under `$(octo-feather-state)/qa`: run 20261023T165649Z-9d0768 (kit
4e7c6ae, on origin/main), PASS, first test_write at tool call 6 of 16 (edit tests/test_cli.py). Honest change:
none in verdict (PASS both); the test_write mark lands on the same file, now because pytest collects it from the
fixture's declaration rather than because its path looks like a test. (Model runs differ in call count: 16 vs 21.)

## Tests (tests/qa.sh, through octo-feather-qa and check-evals as commands)

- `declared` (fixture spec: testpaths ["specs"], python_files ["*_check.py"]): tests/README.md -> edit, tests/test_y.py
  (test-looking, outside the declaration) -> edit, specs/cli_check.py -> edit + test_write.
- `order`, `fsonly`, `contract` now run in a python-app copy (pytest declared); marks unchanged.
- check-evals: `case order fact #1: field before: test_write needs fixture fx to declare its tests`, and fx2 via head.
- Red before: `declared` FAILed under the regex (README counted as test_write at call 2); the check-evals cases exited 0.

## #170 defect fix: deterministic test_write (lane gh167, branch implementer-gh170)

Report (implementer-gh169): `rt "declared"` sometimes marked tests/test_y.py test_write ("qa test: rt artifacts wrong").

Root cause, two halves of one fault: test_write was decided from a different repo state than the snapshot it was
credited to.
- `declared_tests` ran pytest in the live case repo after the snapshot was taken, and paired the collected paths with
  that snapshot's hashes. The stub (as Pi) does not wait for the watcher: its next call (`specs/cli_check.py`) landed
  during collection, pytest collected it, the snapshot had no hash for it (None), so the tests map differed and the
  earlier call (tests/test_y.py) got test_write.
- The watcher took each snapshot only when its loop reached the end line, i.e. after the previous collection finished.
  A slow collection (>0.5 s, the stub's turn) put later calls' writes into an earlier call's snapshot. Shown by fixing
  only the first half under a forced delay: `first test_write at tool call 3 of 5 (read .../tdd/SKILL.md)`.

Fix (scripts/octo-feather-qa, watcher only, classify() untouched): a reader thread snapshots at each end event as it
arrives (bytes kept), and pytest collects in a tree written from that snapshot's own bytes (`uv run --project <repo>`,
cwd the tree). No retry, sleep or assertion change.

Forced interleaving (tests/qa.sh, kept): a uv shim makes `--collect-only` in the spec fixture take 1.5 s, longer than
the stub's 0.5 s turn, so the next write always lands during collection.
- Before (watcher at f746f31, shim on): red, every time it was run (2 of 2):
  `FAIL rt/declared: skill_read_before tdd test_write: first test_write at tool call 2 of 5 (bash echo r > tests/README.md)`
- After: `bash tests/qa.sh` x10 loop:

```
run 1: ok (qa: ok)
run 2: ok (qa: ok)
run 3: ok (qa: ok)
run 4: ok (qa: ok)
run 5: ok (qa: ok)
run 6: ok (qa: ok)
run 7: ok (qa: ok)
run 8: ok (qa: ok)
run 9: ok (qa: ok)
run 10: ok (qa: ok)
```

10 of 10 passed. `just check` ok.
