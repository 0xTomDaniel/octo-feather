# #169: a classifier that cannot accept the question's form is listed by the real question's provider error

Rule: spec judgment#rule-available; owner ruling relayed on #169 ("we won't use models that only answer yes/no; they
must also be able to classify"). The colour/bool stand-in probe and `skipped_yes_no` are deleted; a classifier that
answered no case of the real question is listed unavailable with that question's provider error.

Smoke (one case) first, then the demo, at kit 39f817b plus this change (sandbox proof lines omitted).

## Smoke: `scripts/octo-feather-qa --suite judgment-ticket-slice --case c-3-pi-role-approve --classifier openrouter/respan/span-01 --classifier openrouter/typesafe/jev-1.13`

```
evals: ok (8 suites, 273 cases)
qa: run 20261026T170608Z-ee9ae7: 1 case(s); kit 39f817becbee6e8387a7ba2a26270af7d5089522; artifacts /home/exedev/.local/state/octo-feather/qa/20261026T170608Z-ee9ae7
bench judgment-ticket-slice: question c-ticket-slice, labels slice, layer-only; 1 cases (train 1, held-out 0); every answer is a model judgment (classifier output, advisory: no gate reads it)
bench judgment-ticket-slice: classifiers available (32): openai/gpt-6-luna, openrouter/~perplexity/pplx-decider-latest, openrouter/~typesafe/jev-latest, openrouter/cloudflare/clef, openrouter/cloudflare/clef-flash, openrouter/cloudflare/clef-omni, openrouter/inception/mercury-decide, openrouter/inception/mercury-decide:free, openrouter/jaredpalmer/kev-4b, openrouter/liquid/d1, openrouter/microsoft/microsoft-decision-1, openrouter/nace-ai/drex-v1.5, openrouter/nace-ai/drex-v2.0, openrouter/openai/gpt-6-luna-decisions, openrouter/perplexity/pplx-decider-v1.1-27b, openrouter/respan/span-01, openrouter/respan/span-01-lite, openrouter/respan/span-01-lite:free, openrouter/scaledown/classify-1, openrouter/togethercomputer/tev1-4b-experimental, openrouter/typesafe/jev-1.13, openrouter/typesafe/jev-1.14, openrouter/upstage/solar-decide, openrouter/upstage/solar-decide-flash, openrouter/~perplexity/pplx-decider-flash-latest, openrouter/baseten/elephant-1:free, openrouter/baseten/mammoth-1:free, openrouter/liquid/d1-ultra, openrouter/nace-ai/drex-max, openrouter/perplexity/pplx-decider-flash-v1.2, openrouter/perplexity/pplx-decider-v1.2, openrouter/respan/span-02
bench judgment-ticket-slice: benched only --classifier openrouter/respan/span-01, openrouter/typesafe/jev-1.13
bench judgment-ticket-slice: unclassified id (1): openrouter/respan/span-01; benched and scored, in neither list of classifiers.json, never the kit's model until the owner rules it there
TRAIN (1 cases; the best and the kit model's threshold are made here):
  model                         answered  correct  accuracy  brier   ece     cost_usd   errors
  openrouter/typesafe/jev-1.13    1/1           1     1.000  0.000   0.010    0.000037  0
HELD-OUT (0 cases; the measure, never used to pick):
  model                         answered  correct  accuracy  brier   ece     cost_usd   errors
  openrouter/typesafe/jev-1.13    0/0           0         -  -       -        0.000037  0
  (cost_usd and errors: the model's every call, train and held-out; brier: mean multi-class Brier score, lower is better; ece: expected calibration error over top-probability buckets [0.0, 0.5), [0.5, 0.6), [0.6, 0.7), [0.7, 0.8), [0.8, 0.9), [0.9, 1.0])
unavailable openrouter/respan/span-01: listed but answered no case: System One API error (400): {"error":{"message":"Respan only accepts noul questions whose instructions and criteria are plain strings (question \"q\")","code":400}}
KIT MODEL BESIDE THE BEST (best: highest train accuracy over every train case answered; ties: lower train Brier, lower train cost, name; held-out apart, never used to pick):
        model                         train acc  train brier  held-out acc  held-out brier  cost_usd
  kit   openrouter/typesafe/jev-1.13      1.000        0.000             -               -  0.000037
  best  openrouter/typesafe/jev-1.13      1.000        0.000             -               -  0.000037
kit model openrouter/typesafe/jev-1.13 (judgment-model.json): proposed threshold (for the director to accept; until met, the judge stays advisory): held-out accuracy >= 0.207 and held-out brier <= 0.0 (from train only: accuracy_min the Wilson 1.96 lower bound of train accuracy, brier_max train Brier mean + 1.96 standard errors)
held-out now: accuracy - (0/0 of 0), brier -, ece -: does not meet the proposed threshold
kit model calibration train (top probability bucket: n, mean top probability, accuracy): [0.9, 1.0] n 1 p 0.990 acc 1.000
kit model calibration held-out (top probability bucket: n, mean top probability, accuracy): no answers
DONE bench judgment-ticket-slice: kit model openrouter/typesafe/jev-1.13, best openrouter/typesafe/jev-1.13 [11.5 s]
qa: 1/1 bench(es) done (run 20261026T170608Z-ee9ae7); artifacts /home/exedev/.local/state/octo-feather/qa/20261026T170608Z-ee9ae7
```

## Demo: `scripts/octo-feather-qa --suite judgment-ticket-slice --classifier openrouter/respan/span-01 --classifier openrouter/typesafe/jev-1.13` (exit 0)

```
evals: ok (8 suites, 273 cases)
qa: run 20261026T170625Z-83d123: 22 case(s); kit 39f817becbee6e8387a7ba2a26270af7d5089522; artifacts /home/exedev/.local/state/octo-feather/qa/20261026T170625Z-83d123
bench judgment-ticket-slice: question c-ticket-slice, labels slice, layer-only; 22 cases (train 14, held-out 8); every answer is a model judgment (classifier output, advisory: no gate reads it)
bench judgment-ticket-slice: classifiers available (32): openai/gpt-6-luna, openrouter/~perplexity/pplx-decider-latest, openrouter/~typesafe/jev-latest, openrouter/cloudflare/clef, openrouter/cloudflare/clef-flash, openrouter/cloudflare/clef-omni, openrouter/inception/mercury-decide, openrouter/inception/mercury-decide:free, openrouter/jaredpalmer/kev-4b, openrouter/liquid/d1, openrouter/microsoft/microsoft-decision-1, openrouter/nace-ai/drex-v1.5, openrouter/nace-ai/drex-v2.0, openrouter/openai/gpt-6-luna-decisions, openrouter/perplexity/pplx-decider-v1.1-27b, openrouter/respan/span-01, openrouter/respan/span-01-lite, openrouter/respan/span-01-lite:free, openrouter/scaledown/classify-1, openrouter/togethercomputer/tev1-4b-experimental, openrouter/typesafe/jev-1.13, openrouter/typesafe/jev-1.14, openrouter/upstage/solar-decide, openrouter/upstage/solar-decide-flash, openrouter/~perplexity/pplx-decider-flash-latest, openrouter/baseten/elephant-1:free, openrouter/baseten/mammoth-1:free, openrouter/liquid/d1-ultra, openrouter/nace-ai/drex-max, openrouter/perplexity/pplx-decider-flash-v1.2, openrouter/perplexity/pplx-decider-v1.2, openrouter/respan/span-02
bench judgment-ticket-slice: benched only --classifier openrouter/respan/span-01, openrouter/typesafe/jev-1.13
bench judgment-ticket-slice: unclassified id (1): openrouter/respan/span-01; benched and scored, in neither list of classifiers.json, never the kit's model until the owner rules it there
TRAIN (14 cases; the best and the kit model's threshold are made here):
  model                         answered  correct  accuracy  brier   ece     cost_usd   errors
  openrouter/typesafe/jev-1.13   14/14         12     0.857  0.102   0.107    0.000742  0
HELD-OUT (8 cases; the measure, never used to pick):
  model                         answered  correct  accuracy  brier   ece     cost_usd   errors
  openrouter/typesafe/jev-1.13    8/8           8     1.000  0.004   0.027    0.000742  0
  (cost_usd and errors: the model's every call, train and held-out; brier: mean multi-class Brier score, lower is better; ece: expected calibration error over top-probability buckets [0.0, 0.5), [0.5, 0.6), [0.6, 0.7), [0.7, 0.8), [0.8, 0.9), [0.9, 1.0])
unavailable openrouter/respan/span-01: listed but answered no case: System One API error (400): {"error":{"message":"Respan only accepts noul questions whose instructions and criteria are plain strings (question \"q\")","code":400}}
KIT MODEL BESIDE THE BEST (best: highest train accuracy over every train case answered; ties: lower train Brier, lower train cost, name; held-out apart, never used to pick):
        model                         train acc  train brier  held-out acc  held-out brier  cost_usd
  kit   openrouter/typesafe/jev-1.13      0.857        0.102         1.000           0.004  0.000742
  best  openrouter/typesafe/jev-1.13      0.857        0.102         1.000           0.004  0.000742
kit model openrouter/typesafe/jev-1.13 (judgment-model.json): proposed threshold (for the director to accept; until met, the judge stays advisory): held-out accuracy >= 0.601 and held-out brier <= 0.229 (from train only: accuracy_min the Wilson 1.96 lower bound of train accuracy, brier_max train Brier mean + 1.96 standard errors)
held-out now: accuracy 1.000 (8/8 of 8), brier 0.004, ece 0.027: meets the proposed threshold
kit model calibration train (top probability bucket: n, mean top probability, accuracy): [0.5, 0.6) n 2 p 0.580 acc 0.000; [0.8, 0.9) n 1 p 0.820 acc 1.000; [0.9, 1.0] n 11 p 0.985 acc 1.000
kit model calibration held-out (top probability bucket: n, mean top probability, accuracy): [0.8, 0.9) n 1 p 0.880 acc 1.000; [0.9, 1.0] n 7 p 0.986 acc 1.000
DONE bench judgment-ticket-slice: kit model openrouter/typesafe/jev-1.13, best openrouter/typesafe/jev-1.13 [23.6 s]
qa: 1/1 bench(es) done (run 20261026T170625Z-83d123); artifacts /home/exedev/.local/state/octo-feather/qa/20261026T170625Z-83d123
```

Facts read from the artifacts (run 20261026T170625Z-83d123/judgment-ticket-slice): extension.js contains no "colour"
and no "bool" (no stand-in question sent); the command's stdout bench line has keys available, benched, skipped,
errors, rows (no yesno); bench.json has no skipped_yes_no, span-01 `available: false` with `first_error` equal to the
command's errors[0], the provider's errorMessage on the real choice question.

## Follow-up: whole provider errors, unclassified wording, lane reason

- BENCH_SOURCE `err()` no longer cuts an error at 400 characters: the listed error is the provider's whole text
  (dedup by full string as before). Every recorded bench run in `$(octo-feather-state)/qa/*/*/stdout.txt` was read: no
  error in any `errors` list reached 400 characters, so no classifier's listed error text changes in those runs.
  No new bench run: the command's output changes only by the dropped cut.
- The "unclassified id" report line says "benched (scored where it answered)": span-01 above was benched and answered
  nothing, so "benched and scored" was false for it.
- `octo-feather-lane judge`: the dead `yesno` read and its "yes/no only" reason are gone; a kit model not benched is
  "a moving alias, never called" (bench `skipped`) or "not an available classifier".
