# gh122 (ticket #129): ladder suite, corrector rung choice

Smoke: evals/ladder/ (suite ladder, cases corrector-fuzzy-lesson, corrector-fact-lesson; role agents/corrector.md unchanged)
Removed: nothing from the owed list: the rung-choice entry in docs/owed-evals/118.md stays, reworded to point at evals/ladder/ and still owe a separating case, since both cases pass at head and at 61b9f22 (below). Fixture python-app instead of py-mini: the corrector's brief needs the `just check` gate, and python-app holds an executable `.githooks/pre-commit` for the fact lesson; same fixture as the evidence/2026-10-23-gh118-ladder-smoke.md run.

Suite: `role-transcript`, max_tool_calls 200, timeout_s 2700. Each case graded only on `{"fact": "declared", "field": "rung"}`: fuzzy `in` structure, structured-judgment, prose; fact `in` structure, exact-check. Both cases written and committed (a41fc21) before any run; neither reworded after.

## corrector-fuzzy-lesson (train)

Smoke (first run, real graded result), head a41fc21:

PASS ladder/corrector-fuzzy-lesson: declared rung: "structure", one of ["structure", "structured-judgment", "prose"] [stop: exit, 18 tool calls, 100.9 s] [kit a41fc21278898756b7177306a4ea8a6a381209d6]
qa: 1/1 passed (run 20261023T220430Z-784528)

Fails-before, `--kit-ref 61b9f22`:

PASS ladder/corrector-fuzzy-lesson: declared rung: "structure", one of ["structure", "structured-judgment", "prose"] [stop: exit, 16 tool calls, 96.0 s] [kit 61b9f22b869e630325e5b5013e767db9f3816eb7]
qa: 1/1 passed (run 20261023T221452Z-afcce8)

Finding: NON-SEPARATING. The kit at 61b9f22 (no ladder in docs/adr/0008) already refuses the inviting word-list check and picks `structure` (a `UserError(problem, *, fix)` with a required next step, typed by basedpyright), the same choice as head. Case not tuned. One trial each; a separating case needs a lesson where the pre-ladder corrector takes the proxy check, which this one does not invite strongly enough at 61b9f22.

## corrector-fact-lesson (held-out, scored apart)

Head a41fc21:

PASS ladder/corrector-fact-lesson: declared rung: "exact-check", one of ["structure", "exact-check"] [stop: exit, 15 tool calls, 98.0 s] [kit a41fc21278898756b7177306a4ea8a6a381209d6]
qa: 1/1 passed (run 20261023T222233Z-0ae3bd)

`--kit-ref 61b9f22`:

PASS ladder/corrector-fact-lesson: declared rung: "exact-check", one of ["structure", "exact-check"] [stop: exit, 13 tool calls, 82.9 s] [kit 61b9f22b869e630325e5b5013e767db9f3816eb7]
qa: 1/1 passed (run 20261023T222525Z-24c17d)

Held-out score: head 1/1, 61b9f22 1/1 (does not separate either; it guards against always answering a rung above exact-check).

## corrector-coupling-lesson (written, not run here)

Added after the two cases above did not separate: the check-test-surface incident (docs/adr/0008 Rejected), two `internal-test-surface` findings plus a reviewer's suggested import/private-name ban; expects `rung` in structure, structured-judgment, prose. Written and committed before any run; the lane supervisor runs it (lane Pi quota). No result yet.
