# gh891: the edge rule in the python and typescript skills (#896)

Change: the python and typescript skills point at quality `#acceptance-edge-validated` and templates `#tpl-edge` and keep only their language practice (Pydantic: parse then validate, one strict `extra="forbid"` base model, typed values past the edge; Zod: real parser to `unknown`, `z.strictObject`, never `.passthrough()`). The typescript skill's general boundary policy, with its "reason documented in the code or issue evidence" exception, is removed. Cases `implementer-python-edge` (fixture python-app-edge) and `implementer-typescript-edge` (fixture ts-app-edge) in evals/role-transcripts.

Smoke: .agents/skills/python/SKILL.md (Data At Edges; runs below, case implementer-python-edge)
Smoke: .agents/skills/typescript/SKILL.md (Data At Edges; runs below, case implementer-typescript-edge)

Graded, as the cases are committed (5b03af78): library adoption only, by what the branch changed (`branch_paths` touched `pyproject.toml` + `uv.lock`, `package.json` + `pnpm-lock.yaml`), and a `Prior art:` line. The earlier runs below also graded `ran uv add pydantic` / `ran pnpm add zod`, dropped because `ran` matches arguments by equality and refused `pnpm add zod@4` (80d4e62a, 5b03af78). Strict models and validation at the edge are observed, not graded: no fact in the closed list reads file content. The observations below come from the write/edit/bash calls in each run's transcript.jsonl (tests excluded).

## Fixtures offline

Both installed with no network inside `scripts/octo-feather-qc-sandbox` by hand (QC_PI=none): python-app-edge `uv add pydantic` (pyproject `[tool.uv] offline = true`, the box's uv cache overlay), pydantic 2.14.3 imported; ts-app-edge `pnpm install --frozen-lockfile`, `pnpm add zod` (zod 4.6.7), `pnpm test`, `pnpm typecheck` (`.npmrc` `offline=true`, `cache-dir=.pnpm-cache` holding zod's registry metadata; packages from the box's pnpm store, readable in the sandbox).

## Smoke run 20261113T230959Z-fe3360 (kit 1351b11b, --runs 1 --baseline 7bb5c703)

```
current PASS implementer-python-edge 1/1: ran uv add pydantic (exit 0); pyproject.toml, uv.lock changed; Prior art 1 line
baseline FAIL 0/1: no uv add pydantic; nothing changed under pyproject.toml, uv.lock
pass rate 0.00 -> 1.00; time 94.9 -> 134.4 s; tokens 219909 -> 482317; cost 0.4188 -> 0.6010
```

## Earlier proof run 20261113T231426Z-5c26fa (kit 76efd9ef, --runs 3 --baseline 7bb5c703; with the dropped `ran` facts)

```
scripts/octo-feather-qa --suite role-transcripts --case implementer-python-edge --case implementer-typescript-edge --runs 3 --baseline 7bb5c703
PASS role-transcripts/implementer-python-edge: 3/3 runs passed (pass rate 1.00, stddev 0.00)
  baseline FAIL role-transcripts/implementer-python-edge: 0/3 runs passed (pass rate 0.00, stddev 0.00)
  compare role-transcripts/implementer-python-edge: baseline kit 7bb5c70399dc beside current kit 76efd9ef8b92
               baseline             current              difference
    pass rate  0.00 +/- 0.00        1.00 +/- 0.00        +1.00
    time s     89.8 +/- 9.5         112.0 +/- 9.4        +22.2
    tokens     203322 +/- 27367     342934 +/- 25907     +139612
    cost usd   0.3620 +/- 0.0079    0.4812 +/- 0.0137    +0.1192
PASS role-transcripts/implementer-typescript-edge: 3/3 runs passed (pass rate 1.00, stddev 0.00)
  baseline FAIL role-transcripts/implementer-typescript-edge: 0/3 runs passed (pass rate 0.00, stddev 0.00)
  compare role-transcripts/implementer-typescript-edge: baseline kit 7bb5c70399dc beside current kit 76efd9ef8b92
               baseline             current              difference
    pass rate  0.00 +/- 0.00        1.00 +/- 0.00        +1.00
    time s     89.6 +/- 10.7        96.9 +/- 5.2         +7.3
    tokens     275539 +/- 49478     412094 +/- 133355    +136555
    cost usd   0.4044 +/- 0.0238    0.4788 +/- 0.0746    +0.0744
qa: analysis: non-discriminating fact field_lines Prior art in both cases (passes on both kits)
qa: 2/2 passed (run 20261113T231426Z-5c26fa)
```

## Per run: graded facts, and what was observed but not graded

| case | kit | run | ran | branch_paths | observed in the diff (not graded) |
|---|---|---|---|---|---|
| python | baseline | 1 | fail | fail | `json.loads` then 6 `isinstance` checks; no schema library |
| python | baseline | 2 | fail | fail | `json.loads` then 6 `isinstance` checks; no schema library |
| python | baseline | 3 | fail | fail | `json.loads` then 6 `isinstance` checks; no schema library |
| python | current | 1 | pass | pass | pydantic base model `ConfigDict(strict=True, extra="forbid")`, `model_validate_json` at the file edge; one `isinstance` only to word an `OSError` message |
| python | current | 2 | pass | pass | same: strict extra-forbid base model, `model_validate_json` at the edge |
| python | current | 3 | pass | pass | same: strict extra-forbid base model, `model_validate_json` at the edge |
| typescript | baseline | 1 | fail | fail | `JSON.parse` then hand-written `typeof` (5) and `Array.isArray` (3) checks; no zod |
| typescript | baseline | 2 | fail | pass | ran `pnpm add zod@4`; `z.strictObject` schemas, `JSON.parse` then parse |
| typescript | baseline | 3 | fail | pass | ran `pnpm add zod@4`; `z.object` (not strict: unknown fields stripped, not rejected) |
| typescript | current | 1 | pass | pass | ran `pnpm add zod --offline`; `z.strictObject` schemas, `JSON.parse` then parse |
| typescript | current | 2 | pass | pass | `z.strictObject` schemas, `JSON.parse` then parse |
| typescript | current | 3 | pass | pass | `z.strictObject` schemas, `JSON.parse` then parse |

Honest reading of the typescript case: the baseline typescript skill already named Zod 4 for a repo with none, and baseline runs 2 and 3 adopted zod. They fail the `ran` fact only because they spelled the add `pnpm add zod@4`, which the fact's positional match (`add`, `zod`) does not accept. So the case's 0/3 on the baseline is real for run 1 only; for runs 2 and 3 it measures the argument spelling, not adoption. What did change between the kits is strictness (baseline run 3 `z.object`, current 3 of 3 `z.strictObject`), which no fact grades. The python case discriminates on adoption itself: no baseline run added a schema library.

## Proof run 20261114T000816Z-d0ef96 (kit 5b03af78, the cases as committed, --runs 3 --baseline 7bb5c703)

```
scripts/octo-feather-qa --suite role-transcripts --case implementer-python-edge --case implementer-typescript-edge --runs 3 --baseline 7bb5c703
FAIL role-transcripts/implementer-python-edge: 2/3 runs passed (pass rate 0.67, stddev 0.58); run 3: field_lines Prior art: no column-0 `Prior art:` line with a value outside code blocks
  baseline FAIL role-transcripts/implementer-python-edge: 0/3 runs passed (pass rate 0.00, stddev 0.00); runs 1-3: branch_paths: nothing changed under pyproject.toml, uv.lock
  compare role-transcripts/implementer-python-edge: baseline kit 7bb5c70399dc beside current kit 5b03af788052
               baseline             current              difference
    pass rate  0.00 +/- 0.00        0.67 +/- 0.58        +0.67
    time s     82.1 +/- 14.1        95.4 +/- 12.9        +13.3
    tokens     200315 +/- 3106      280857 +/- 48833     +80541
    cost usd   0.3733 +/- 0.0112    0.4303 +/- 0.0613    +0.0570
PASS role-transcripts/implementer-typescript-edge: 3/3 runs passed (pass rate 1.00, stddev 0.00)
  baseline PASS role-transcripts/implementer-typescript-edge: 3/3 runs passed (pass rate 1.00, stddev 0.00)
  compare role-transcripts/implementer-typescript-edge: baseline kit 7bb5c70399dc beside current kit 5b03af788052
               baseline             current              difference
    pass rate  1.00 +/- 0.00        1.00 +/- 0.00        +0.00
    time s     161.9 +/- 62.0       155.4 +/- 5.0        -6.5
    tokens     288119 +/- 31051     444321 +/- 83008     +156202
    cost usd   0.4135 +/- 0.0329    0.5577 +/- 0.0645    +0.1442
qa: analysis: high variance implementer-python-edge (current 0.67 +/- 0.58); cost tradeoff implementer-typescript-edge (pass rate 1.00 on both kits; tokens 288119 to 444321)
qa: 1/2 passed (run 20261114T000816Z-d0ef96)
```

| case | kit | run | branch_paths | Prior art | add run | observed in the diff (not graded) |
|---|---|---|---|---|---|---|
| python | baseline | 1 | fail | pass | none | `json.loads` then 6 `isinstance` checks; no schema library |
| python | baseline | 2 | fail | pass | none | `json.loads` then 6 `isinstance` checks; no schema library |
| python | baseline | 3 | fail | pass | none | `json.loads` then 6 `isinstance` checks; no schema library |
| python | current | 1 | pass | pass | `uv add pydantic` | strict extra-forbid base model, `model_validate_json` at the edge |
| python | current | 2 | pass | pass | `uv add pydantic` | strict extra-forbid base model, `model_validate_json` at the edge |
| python | current | 3 | pass | fail | `uv add pydantic` | strict extra-forbid base model, `model_validate_json` at the edge; report wrote `- Prior art: ...` as a bullet, so the field reader refused it |
| typescript | baseline | 1 | pass | pass | `pnpm add zod@^4` | `z.strictObject`, `JSON.parse` then parse |
| typescript | baseline | 2 | pass | pass | `pnpm add zod@4` | `z.object` (not strict: unknown fields stripped, not rejected) |
| typescript | baseline | 3 | pass | pass | `pnpm add zod@4`, `--save-exact zod@4.6.7` | `z.strictObject`, `JSON.parse` then parse |
| typescript | current | 1 | pass | pass | `pnpm add zod` | `z.strictObject`, `JSON.parse` then parse |
| typescript | current | 2 | pass | pass | `pnpm add zod`, `-E zod` | `z.strictObject`, `JSON.parse` then parse |
| typescript | current | 3 | pass | pass | `pnpm add zod` | `z.strictObject`, `JSON.parse` then parse |

Reading, cases as committed:

- implementer-python-edge is fail-before proof on adoption: the baseline adds no library in 6 of 6 runs over both proof runs; the change adds pydantic in 6 of 6. Its one current FAIL (run 3) is the report form, a bulleted `Prior art:` line, not adoption: that run added pydantic and built strict extra-forbid models.
- implementer-typescript-edge is a regression guard, not fail-before proof: the old typescript skill already named Zod 4 for a repo with none, and the baseline adopts zod in 3 of 3 runs. What differed between the kits in these runs is strictness (baseline run 2 `z.object`; current 3 of 3 `z.strictObject`), observed and not graded.

Owed eval: docs/owed-evals/891.md.
