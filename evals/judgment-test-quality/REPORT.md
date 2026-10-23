# a-test-quality: labelled set (draft, lane gh119, for #119 scope 1-2)

Question: Judged against the code it exercises, is this test tautological (its expected value is computed the same way the code computes it, so it cannot disagree with the code), implementation-coupled (it reaches past the public surface into private functions, source text or internal collaborators, so a behaviour-preserving refactor breaks it), or ok (it drives a public surface and compares against an independent expected value)?

Labels: `tautological`, `implementation-coupled`, `ok`

Split rule (fixed before labelling patterns): per label in source order, the case at 0-based index i is held-out when i % 3 == 1.

| id | split | label | reason | source |
|---|---|---|---|---|
| a-tdd-add-restates-sum | train | tautological | expected value is a + b, the very operation add performs, so it passes by construction | .agents/skills/tdd/SKILL.md:31@5f8fca3 (tdd anti-pattern example) |
| a-tdd-total-reduce | held-out | tautological | expected is recomputed with the same reduce-sum calculateTotal performs; no independent value | .agents/skills/tdd/tests.md:67-71@5f8fca3 (tdd anti-pattern example) |
| a-shout-json-expected-upper | train | tautological | goes through the CLI but builds expected with the code's own .upper() + '!', so a wrong shout rule still passes | evals/fixtures/python-app-shout/tests/test_cli.py:32-36@649faad (#107 fixture; reviewer probes in evidence/2026-10-23-gh107-role-skill-loading-smoke.md@origin/gh107) |
| a-constructed-py-e2e-recompute-greeting | train | tautological | lines 22-28; the literal {'name': 'Grace', 'text': 'Hello, Grace'} was rewritten to strip the name and format f'Hello, {clean}', greet's own rule, so a wrong greeting rule still passes (constructed per director ruling 2026-10-23) | constructed from templates/python/tests/test_cli.py@5f8fca3 |
| a-constructed-ts-expected-from-greet | train | tautological | lines 4-5, 9-20; the literal { name: 'Ada', text: 'Hello, Ada' } was rewritten to greet('Ada'), the function the CLI prints, so expected is the code's own output (constructed per director ruling 2026-10-23) | constructed from templates/typescript/tests/cli.test.ts@5f8fca3 |
| a-constructed-pi-role-common-dir | train | tautological | lines 7-14; the literal $t/repo main-checkout path was rewritten to dirname of git rev-parse --git-common-dir, the lookup pi-role itself runs, so a wrong lookup rule still passes (constructed per director ruling 2026-10-23) | constructed from tests/pi-role.sh@5f8fca3 |
| a-constructed-shape-skill-roots | train | tautological | lines 5-12; its one assertion's literal want (six $kit/.agents/skills paths, T/repo/.agents/skills/spec-chat-shape, no-skills) was rewritten to octo-feather-shape --json run again for the same repo and HOME through the same filter as got, so want is the code's own output and equals got by construction: a home-not-repo lookup, a wrong skill list or a missing --no-skills still passes; nothing else in the test asserts (the rest is fixture setup, HOME faked at the boundary) (constructed per director ruling 2026-10-23) | constructed from tests/shape.sh@5f8fca3 |
| a-tdd-checkout-mock-payment | train | implementation-coupled | mocks the internal paymentService collaborator and asserts the call, not the checkout outcome | .agents/skills/tdd/tests.md:31-35@5f8fca3 (tdd anti-pattern example) |
| a-check-refs-sed-justfile | held-out | implementation-coupled | provokes a scanner error by sed-editing a private perl statement in the justfile; renaming it breaks the test | tests/check-refs.sh:68-79@0fc2232; finding internal-test-coupling, $(octo-feather-state)/lanes/archive/gh38.handoffs.jsonl at 2026-10-21T21:11:51Z |
| a-lane-tickets-parse-if | train | implementation-coupled | parses the private constant IF out of the ghsnap script's source with sed; a rename turns the gate red | tests/lane-tickets.sh:108-114@b1ab3dc; finding internal-test-coupling, $(octo-feather-state)/lanes/archive/gh40.handoffs.jsonl at 2026-10-21T21:26:41Z |
| a-review-host-rewrite-process-cmdline | train | implementation-coupled | simulates no-/proc by string-replacing Spec Chat's private process_cmdline in a copied script, not at an external boundary | tests/review-host.sh:95-108@1a77a78; finding test-private-helper-coupling, $(octo-feather-state)/lanes/archive/gh58.handoffs.jsonl at 2026-10-22T01:22:38Z |
| a-page-bounds-pagechars | held-out | implementation-coupled | asserts through internal pageChars/surfaceLines/parseLines instead of the update/read tool surface | exosurface repo plugins/bb-plugin-exo-a2ui-spike/test/page-bounds.test.ts:455-468@53e0ff2 (~/src/exosurface-gh21); finding test-reaches-internals, $(octo-feather-state)/lanes/exo-gh21.handoffs.jsonl at 2026-10-21T22:13:37Z |
| a-accepted-importlib-spec-page | train | implementation-coupled | loads review-serve.py as a module and calls its private _spec_page to get the served version | tests/accepted.sh:26-38@3e2c626; finding internal-test-surface, $(octo-feather-state)/lanes/archive/gh96.handoffs.jsonl at 2026-10-22T23:06:56Z |
| a-shout-suffix-source-read | train | implementation-coupled | reads core.py source text and asserts a constant's spelling; a rename breaks it while behaviour is unchanged | evals/fixtures/python-app-shout/tests/test_cli.py:39-41@649faad (#107 fixture) |
| a-tdd-checkout-confirmed | train | ok | drives checkout through its public API and checks the observable status against a literal | .agents/skills/tdd/tests.md:9-14@5f8fca3 (tdd good example) |
| a-tdd-total-literal | held-out | ok | public function, independent known literal 15 as expected value | .agents/skills/tdd/tests.md:74-76@5f8fca3 (tdd good example) |
| a-template-hello-json | train | ok | in-process CLI entry, literal expected JSON for the success and error paths | templates/python/tests/test_cli.py:12-19@5f8fca3 |
| a-recipe-args-exact-argv | train | ok | runs real just recipes against stub commands at the PATH boundary and compares recorded argv/cwd to the literal arguments it passed | tests/recipe-args.sh:15-46@5f8fca3 |
| a-check-refs-stub-on-path | held-out | ok | injects a failing perl/grep as a stub first on PATH (external boundary) and checks the gate's exit and message | tests/check-refs.sh:68-81@dcf8bcb (fix of the gh38 finding) |
| a-review-host-no-proc-namespace | train | ok | removes /proc with a mount namespace and a ps stub (OS boundary), drives the review-host CLI, asserts link and server facts | tests/review-host.sh:127-157@89cdfc9 (fix of the gh58 finding) |
| a-accepted-etag | train | ok | starts pinned review-serve as a server and reads the ETag over HTTP, compared to pinned literal hashes | tests/accepted.sh:28-37@dd07eaf (fix of the gh96 finding) |
| a-impl-shout-literal | held-out | ok | CLI entry with literal expected 'HELLO, ADA!' for text and JSON, independent of the implementation | /tmp/gh107/fx-impl tests/test_cli.py:17-25@7df51a7 (implementer probe from the #107 runs; scratch repo); copy: a-test-quality/sources/gh107-fx-impl-7df51a7/tests/test_cli.py:17-25 (code: sources/gh107-fx-impl-7df51a7/src/app/core.py, cli.py) |

## Counts (demo: python3 -c loading question.json, cases.json, reference/expectations.json)

```
$ cd /tmp/gh119/labels && python3 -c "
import json,collections,sys
q=sys.argv[1]; Q=json.load(open(q+'/question.json')); C=json.load(open(q+'/cases.json')); E=json.load(open(q+'/reference/expectations.json'))
print(Q['id'], len(C), 'cases; ids == expectation keys:', sorted(c['id'] for c in C)==sorted(E))
n=collections.Counter((E[c['id']]['label'],c['split']) for c in C)
for l in Q['labels']: print(' ', l, 'train', n[(l,'train')], 'held-out', n[(l,'held-out')])
" a-test-quality
a-test-quality 22 cases; ids == expectation keys: True
  tautological train 6 held-out 1
  implementation-coupled train 5 held-out 2
  ok train 5 held-out 3
```

## Director rulings (2026-10-23)

- DROP the spec-chat review-place case (tests/review-place.py:227-233@077c6b9; both tautological and coupled; a single-label question cannot calibrate on it): removed from cases.json, expectations.json and this report.
- ADD 4 CONSTRUCTED tautological cases, split train only, each a real kit or template test at 5f8fca3 with its expected value rewritten to recompute the code's own logic; source 'constructed from <path>@<sha>', reason says what was rewritten: a-constructed-py-e2e-recompute-greeting (templates/python/tests/test_cli.py), a-constructed-ts-expected-from-greet (templates/typescript/tests/cli.test.ts), a-constructed-pi-role-common-dir (tests/pi-role.sh), and a fourth from tests/lane-archive.sh, since swapped (next ruling). Held-out stays real only. Builder: /tmp/gh119/work-ac/apply_rulings.py.
- a-impl-shout-literal: /tmp/gh107/fx-impl files at 7df51a7 (tests/test_cli.py, src/app/core.py, src/app/cli.py) copied to a-test-quality/sources/gh107-fx-impl-7df51a7/; source keeps the original pointer and names the copy.
- No other case changed (diff -r against /tmp/gh119/labels-pre-ac-rulings/a-test-quality).
- Swap (one label per case, nothing mixed, as with review-place): the tests/lane-archive.sh constructed case kept the independent sha256 byte checks of archive_ok, so it was mixed; replaced by a-constructed-shape-skill-roots, constructed from tests/shape.sh@5f8fca3 (train). shape.sh has one assertion; its literal want was rewritten to octo-feather-shape --json run again for the same repo and HOME through the same filter as got, so the whole test is tautological and nothing in it is coupled or independently sound. Proof run on git archive 5f8fca3: the constructed test passes; with octo-feather-shape mutated (sharpen and --no-skills dropped) it still passes while the original shape.sh fails. Builder: /tmp/gh119/work-ac/a_swap.py; pre copy /tmp/gh119/labels-pre-a-swap/a-test-quality.
- state_shape made true and neutral: 'the test excerpt, trimmed from its source, then optionally Code it exercises'; 'never rewritten' dropped; constructed cases are not announced to the classifier (honest note below).

## Honest note on states

Every state is the test excerpt trimmed from its source (plus optional code it exercises). Cases whose source says "constructed from <path>@<sha>" are rewritten from a real test: only the expected value changed, as their reason says. question.json state_shape says neither, so the classifier is not told which cases are constructed.

## Doubts

- Tautological is scarce in real history (#107: 'no tautological-test finding has ever been logged'). Real ones: 2 from the tdd skill's own examples, 1 from the #107 fixture written on purpose to hold one tautological test (the one held-out case is a tdd example). The 4 constructed cases (train only) are real kit/template tests with only the expected value rewritten; they are the only states in the set not taken as committed (see the honest note).
- Constructed cases: a-constructed-shape-skill-roots is the purest (want is the code's own output, so the test cannot fail). a-constructed-py-e2e-recompute-greeting and a-constructed-ts-expected-from-greet sit beside a-template-hello-json (same template, ok): a deliberate contrast pair, both in train.
- a-page-bounds-pagechars: it also asserts through the public read tool (x.read.execute) in the same excerpt; the coupled part is the pageChars/parseLines asserts. Its code note names the public surface, which helps the classifier more than other states do.
- a-tdd-* states have no code under test (the skill shows none); a-tdd-add-restates-sum is a one-line fragment.
- a-impl-shout-literal points at /tmp/gh107/fx-impl (scratch repo from the #107 runs); its files at 7df51a7 are now copied into a-test-quality/sources/gh107-fx-impl-7df51a7/ and the source names both.
- Pairs share a source (check-refs sed vs PATH stub; accepted importlib vs ETag; review-host string replace vs namespace): good contrast, but both halves of a pair can land in one split (check-refs pair: both held-out).
- a-lane-tickets-parse-if: coupled, but the comparison is between two scripts' field lists, so it also partly restates the code (not labelled tautological: the value checked is gh's argv, not ghsnap's output).
