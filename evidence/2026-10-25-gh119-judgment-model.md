# The kit's one judgment model: openrouter/typesafe/jev-1.13 (#119, #148, #156)

Spec: docs/specs/judgment.spec.html #rule-one-model (one judgment model for every question, recorded in one place,
changed only when a rebench shows another clearly better). Owner ruling 2026-10-25: openrouter/typesafe/jev-1.13.

Recorded once: `evals/judgment-model.json` `model`. Read by `octo-feather-qa` (each bench shows it beside the
question's best-scoring classifier and proposes its threshold) and `octo-feather-lane judge` (asks it every
question). `scripts/check-evals` refuses a suite that names a model; each suite keeps only its `calibration` of
this model (held-out accuracy and Brier, proposed threshold, `accepted` false).

## Why jev-1.13: recomputed from the four benches' artifacts

Recomputed from each bench's `answers.json` (artifacts under `$(octo-feather-state)/qa/<run>/judgment-<q>/`), every
case, train and held-out together, correct = the classifier's choice equals the director's label:

| question | run | cases |
|---|---|---|
| test-quality | 20261024T001416Z-aa46f7 | 27 |
| call-evidence | 20261024T021628Z-d09cbc | 33 |
| exact-or-proxy | 20261025T013852Z-21c7ad | 31 |
| ticket-slice | 20261025T020619Z-f2d2ec | 22 |
| combined | | 113 |

| classifier | combined | test-quality | call-evidence | exact-or-proxy | ticket-slice |
|---|---|---|---|---|---|
| openrouter/nace-ai/drex-max | 93 | 22/27 | 27/33 | 23/31 | 21/22 |
| openrouter/perplexity/pplx-decider-v1.2 | 92 | 22/27 | 25/33 | 25/31 | 20/22 |
| openrouter/typesafe/jev-1.13 | 91 | 25/27 | 22/33 | 24/31 | 20/22 |
| openrouter/typesafe/jev-1.14 | 89 | 23/27 | 22/33 | 24/31 | 20/22 |
| openrouter/respan/span-02 | 84 | 25/27 | 18/33 | 21/31 | 20/22 |

Same as the ruling's figures: drex-max 93, pplx-decider-v1.2 92, jev-1.13 91 of 113 (a 2-case spread, within
noise at n 113). One difference: jev-1.13 is best on test-quality at 25/27 tied with span-02 (25/27), not alone;
span-02 wins that question's train tie-break (lower train Brier). Switch only when a rebench (#151) shows another
clearly better.

jev-1.13's calibration per question from the same artifacts (the bench's rule, train only), recorded in each
suite's `calibration` until the rebench below refreshed it (superseded):

| question | held-out accuracy | held-out Brier | proposed accuracy_min | proposed brier_max |
|---|---|---|---|---|
| test-quality | 1.000 | 0.135 | 0.699 | 0.412 |
| call-evidence | 0.750 | 0.426 | 0.409 | 0.891 |
| exact-or-proxy | 0.818 | 0.212 | 0.531 | 0.446 |
| ticket-slice | 1.000 | 0.004 | 0.601 | 0.239 |

## Rebench, 2026-10-25 (the four benches, one at a time, at kit e19b3c8 plus this lane's uncommitted change)

| question | run | kit model train acc | held-out acc | held-out Brier | proposed accuracy_min | proposed brier_max | held-out meets | best (train) |
|---|---|---|---|---|---|---|---|---|
| test-quality | 20261025T144513Z-79e9f1 | 0.900 | 1.000 (7/7) | 0.123 | 0.699 | 0.381 | yes | openrouter/typesafe/jev-1.13 |
| call-evidence | 20261025T144846Z-9643eb | 0.619 | 0.750 (9/12) | 0.436 | 0.409 | 0.918 | yes | openrouter/nace-ai/drex-max |
| exact-or-proxy | 20261025T145239Z-a5d4b6 | 0.800 | 0.818 (9/11) | 0.218 | 0.584 | 0.468 | yes | openrouter/typesafe/jev-1.14 |
| ticket-slice | 20261025T145621Z-0180da | 0.857 | 1.000 (8/8) | 0.004 | 0.601 | 0.192 | yes | openrouter/inception/mercury-decide |

These are each suite's `calibration` now (`accepted` false: the director accepts a threshold, issue #151). Combined over
the rerun's 113 cases: drex-max 93, jev-1.13 92, pplx-decider-v1.2 92, microsoft-decision-1 92, jev-1.14 90. Differences
from the first benches: jev-1.13 92 (was 91: exact-or-proxy 25/31, was 24/31); microsoft-decision-1 92 (was 88);
test-quality's best is now jev-1.13 itself (span-02 ties it on train accuracy 0.900, higher train Brier 0.240 vs
0.206); exact-or-proxy's best is now jev-1.14 (jev-1.14, clef and jev-1.13 tie on train accuracy 0.800; train Brier
0.293, 0.294, 0.315). Still within noise of each other: no rebench shows another clearly better, so jev-1.13 stays.

## Smoke first: 3 cases x jev-1.13 plus the three Respan span-01 (run 20261025T144418Z-980cc7)

```
evals: ok (8 suites, 272 cases)
qa: run 20261025T144418Z-980cc7: 3 case(s); kit e19b3c8ada566378f6edd48b94942ed00c1d6105; artifacts /home/exedev/.local/state/octo-feather/qa/20261025T144418Z-980cc7
qc sandbox: cleanup: agents started 0 (headless pi 0, Herdr panes 0); leftover processes killed 0, left 0 (the kernel kills those as PID 1 exits); session qa-980cc7-bench stopped and deleted; offline gh refusals 0
bench judgment-test-quality: question a-test-quality, labels tautological, implementation-coupled, ok; 3 cases (train 2, held-out 1); every answer is a model judgment (classifier output, advisory: no gate reads it)
bench judgment-test-quality: classifiers available (32): openai/gpt-6-luna, openrouter/~perplexity/pplx-decider-latest, openrouter/~typesafe/jev-latest, openrouter/cloudflare/clef, openrouter/cloudflare/clef-flash, openrouter/cloudflare/clef-omni, openrouter/inception/mercury-decide, openrouter/inception/mercury-decide:free, openrouter/jaredpalmer/kev-4b, openrouter/liquid/d1, openrouter/microsoft/microsoft-decision-1, openrouter/nace-ai/drex-v1.5, openrouter/nace-ai/drex-v2.0, openrouter/openai/gpt-6-luna-decisions, openrouter/perplexity/pplx-decider-v1.1-27b, openrouter/respan/span-01, openrouter/respan/span-01-lite, openrouter/respan/span-01-lite:free, openrouter/scaledown/classify-1, openrouter/togethercomputer/tev1-4b-experimental, openrouter/typesafe/jev-1.13, openrouter/typesafe/jev-1.14, openrouter/upstage/solar-decide, openrouter/upstage/solar-decide-flash, openrouter/~perplexity/pplx-decider-flash-latest, openrouter/baseten/elephant-1:free, openrouter/baseten/mammoth-1:free, openrouter/liquid/d1-ultra, openrouter/nace-ai/drex-max, openrouter/perplexity/pplx-decider-flash-v1.2, openrouter/perplexity/pplx-decider-v1.2, openrouter/respan/span-02
bench judgment-test-quality: benched only --classifier openrouter/typesafe/jev-1.13, openrouter/respan/span-01, openrouter/respan/span-01-lite, openrouter/respan/span-01-lite:free
bench judgment-test-quality: skipped: yes/no only openrouter/respan/span-01: a tiny choice question refused, a tiny bool question answered (probability 0.9637); provider: System One API error (400): {"error":{"message":"Respan only accepts noul questions whose instructions and criteria are plain strings (question \"q\")","code":400}}
bench judgment-test-quality: skipped: yes/no only openrouter/respan/span-01-lite: a tiny choice question refused, a tiny bool question answered (probability 0.9637); provider: System One API error (400): {"error":{"message":"Respan only accepts noul questions whose instructions and criteria are plain strings (question \"q\")","code":400}}
bench judgment-test-quality: skipped: yes/no only openrouter/respan/span-01-lite:free: a tiny choice question refused, a tiny bool question answered (probability 0.9637); provider: System One API error (400): {"error":{"message":"Respan only accepts noul questions whose instructions and criteria are plain strings (question \"q\")","code":400}}
TRAIN (2 cases; the best and the kit model's threshold are made here):
  model                         answered  correct  accuracy  brier   ece     cost_usd   errors
  openrouter/typesafe/jev-1.13    2/2           2     1.000  0.107   0.215    0.000086  0
HELD-OUT (1 cases; the measure, never used to pick):
  model                         answered  correct  accuracy  brier   ece     cost_usd   errors
  openrouter/typesafe/jev-1.13    1/1           1     1.000  0.245   0.350    0.000086  0
  (cost_usd and errors: the model's every call, train and held-out; brier: mean multi-class Brier score, lower is better; ece: expected calibration error over top-probability buckets [0.0, 0.5), [0.5, 0.6), [0.6, 0.7), [0.7, 0.8), [0.8, 0.9), [0.9, 1.0])
KIT MODEL BESIDE THE BEST (best: highest train accuracy over every train case answered; ties: lower train Brier, lower train cost, name; held-out apart, never used to pick):
        model                         train acc  train brier  held-out acc  held-out brier  cost_usd
  kit   openrouter/typesafe/jev-1.13      1.000        0.107         1.000           0.245  0.000086
  best  openrouter/typesafe/jev-1.13      1.000        0.107         1.000           0.245  0.000086
kit model openrouter/typesafe/jev-1.13 (judgment-model.json): proposed threshold (for the director to accept; until met, the judge stays advisory): held-out accuracy >= 0.342 and held-out brier <= 0.25 (from train only: accuracy_min the Wilson 1.96 lower bound of train accuracy, brier_max train Brier mean + 1.96 standard errors)
held-out now: accuracy 1.000 (1/1 of 1), brier 0.245, ece 0.350: meets the proposed threshold
kit model calibration train (top probability bucket: n, mean top probability, accuracy): [0.7, 0.8) n 1 p 0.700 acc 1.000; [0.8, 0.9) n 1 p 0.870 acc 1.000
kit model calibration held-out (top probability bucket: n, mean top probability, accuracy): [0.6, 0.7) n 1 p 0.650 acc 1.000
DONE bench judgment-test-quality: kit model openrouter/typesafe/jev-1.13, best openrouter/typesafe/jev-1.13 [50.1 s]
qa: 1/1 bench(es) done (run 20261025T144418Z-980cc7); artifacts /home/exedev/.local/state/octo-feather/qa/20261025T144418Z-980cc7
```

Respan span-01, span-01-lite, span-01-lite:free are "skipped: yes/no only": the tiny choice probe came back with the
provider error quoted verbatim, the tiny bool probe was answered (probability 0.9637). Not scored, not listed unavailable.
gpt-6-luna (404) and pplx-decider-v1.1-27b (404 no endpoint) answered neither probe, so stay listed unavailable.

## Demo: `scripts/octo-feather-qa --suite judgment-test-quality` (run 20261025T144513Z-79e9f1)

Prints every scored classifier's TRAIN and HELD-OUT table, the kit's model beside the question's best-scoring
classifier, held-out apart, and the yes/no-only skip lines. Full output, sandbox proof lines omitted:

```
evals: ok (8 suites, 272 cases)
qa: run 20261025T144513Z-79e9f1: 27 case(s); kit e19b3c8ada566378f6edd48b94942ed00c1d6105; artifacts /home/exedev/.local/state/octo-feather/qa/20261025T144513Z-79e9f1
qc sandbox: cleanup: agents started 0 (headless pi 0, Herdr panes 0); leftover processes killed 0, left 0 (the kernel kills those as PID 1 exits); session qa-79e9f1-bench stopped and deleted; offline gh refusals 0
bench judgment-test-quality: question a-test-quality, labels tautological, implementation-coupled, ok; 27 cases (train 20, held-out 7); every answer is a model judgment (classifier output, advisory: no gate reads it)
bench judgment-test-quality: classifiers available (32): openai/gpt-6-luna, openrouter/~perplexity/pplx-decider-latest, openrouter/~typesafe/jev-latest, openrouter/cloudflare/clef, openrouter/cloudflare/clef-flash, openrouter/cloudflare/clef-omni, openrouter/inception/mercury-decide, openrouter/inception/mercury-decide:free, openrouter/jaredpalmer/kev-4b, openrouter/liquid/d1, openrouter/microsoft/microsoft-decision-1, openrouter/nace-ai/drex-v1.5, openrouter/nace-ai/drex-v2.0, openrouter/openai/gpt-6-luna-decisions, openrouter/perplexity/pplx-decider-v1.1-27b, openrouter/respan/span-01, openrouter/respan/span-01-lite, openrouter/respan/span-01-lite:free, openrouter/scaledown/classify-1, openrouter/togethercomputer/tev1-4b-experimental, openrouter/typesafe/jev-1.13, openrouter/typesafe/jev-1.14, openrouter/upstage/solar-decide, openrouter/upstage/solar-decide-flash, openrouter/~perplexity/pplx-decider-flash-latest, openrouter/baseten/elephant-1:free, openrouter/baseten/mammoth-1:free, openrouter/liquid/d1-ultra, openrouter/nace-ai/drex-max, openrouter/perplexity/pplx-decider-flash-v1.2, openrouter/perplexity/pplx-decider-v1.2, openrouter/respan/span-02
bench judgment-test-quality: skipped: moving alias (3): openrouter/~perplexity/pplx-decider-latest, openrouter/~typesafe/jev-latest, openrouter/~perplexity/pplx-decider-flash-latest
bench judgment-test-quality: skipped: yes/no only openrouter/respan/span-01: a tiny choice question refused, a tiny bool question answered (probability 0.9637); provider: System One API error (400): {"error":{"message":"Respan only accepts noul questions whose instructions and criteria are plain strings (question \"q\")","code":400}}
bench judgment-test-quality: skipped: yes/no only openrouter/respan/span-01-lite: a tiny choice question refused, a tiny bool question answered (probability 0.9637); provider: System One API error (400): {"error":{"message":"Respan only accepts noul questions whose instructions and criteria are plain strings (question \"q\")","code":400}}
bench judgment-test-quality: skipped: yes/no only openrouter/respan/span-01-lite:free: a tiny choice question refused, a tiny bool question answered (probability 0.9637); provider: System One API error (400): {"error":{"message":"Respan only accepts noul questions whose instructions and criteria are plain strings (question \"q\")","code":400}}
TRAIN (20 cases; the best and the kit model's threshold are made here):
  model                                             answered  correct  accuracy  brier   ece     cost_usd   errors
  openrouter/typesafe/jev-1.13                       20/20         18     0.900  0.206   0.165    0.001074  0
  openrouter/respan/span-02                          20/20         18     0.900  0.240   0.150    0.000216  0
  openrouter/typesafe/jev-1.14                       20/20         17     0.850  0.256   0.148    0.001074  0
  openrouter/baseten/mammoth-1:free                  20/20         16     0.800  0.250   0.100    0.000000  0
  openrouter/liquid/d1-ultra                         20/20         16     0.800  0.322   0.199    0.000756  0
  openrouter/baseten/elephant-1:free                 20/20         15     0.750  0.317   0.149    0.000000  0
  openrouter/cloudflare/clef-omni                    20/20         15     0.750  0.341   0.176    0.003012  0
  openrouter/nace-ai/drex-max                        20/20         15     0.750  0.356   0.214    0.001164  0
  openrouter/perplexity/pplx-decider-v1.2            20/20         15     0.750  0.389   0.145    0.000386  0
  openrouter/microsoft/microsoft-decision-1          20/20         15     0.750  0.406   0.141    0.000779  0
  openrouter/liquid/d1                               20/20         15     0.750  0.407   0.149    0.000360  0
  openrouter/inception/mercury-decide                20/20         15     0.750  0.442   0.221    0.000386  0
  openrouter/inception/mercury-decide:free           20/20         15     0.750  0.457   0.225    0.000000  0
  openrouter/upstage/solar-decide                    20/20         15     0.750  0.463   0.215    0.001356  0
  openrouter/openai/gpt-6-luna-decisions             20/20         14     0.700  0.350   0.179    0.001945  0
  openrouter/perplexity/pplx-decider-flash-v1.2      20/20         14     0.700  0.369   0.195    0.000193  0
  openrouter/cloudflare/clef                         20/20         13     0.650  0.426   0.286    0.004974  0
  openrouter/nace-ai/drex-v1.5                       20/20         13     0.650  0.448   0.229    0.000704  0
  openrouter/nace-ai/drex-v2.0                       20/20         13     0.650  0.469   0.201    0.001056  0
  openrouter/togethercomputer/tev1-4b-experimental   20/20         13     0.650  0.480   0.191    0.000855  0
  openrouter/cloudflare/clef-flash                   20/20         12     0.600  0.528   0.266    0.000394  0
  openrouter/jaredpalmer/kev-4b                      20/20         12     0.600  0.543   0.147    0.000739  0
  openrouter/scaledown/classify-1                    20/20          9     0.450  0.576   0.194    0.001055  0
  openrouter/upstage/solar-decide-flash              20/20          8     0.400  0.700   0.313    0.001356  0
HELD-OUT (7 cases; the measure, never used to pick):
  model                                             answered  correct  accuracy  brier   ece     cost_usd   errors
  openrouter/typesafe/jev-1.13                        7/7           7     1.000  0.123   0.206    0.001074  0
  openrouter/respan/span-02                           7/7           5     0.714  0.330   0.304    0.000216  0
  openrouter/typesafe/jev-1.14                        7/7           7     1.000  0.134   0.216    0.001074  0
  openrouter/baseten/mammoth-1:free                   7/7           7     1.000  0.047   0.117    0.000000  0
  openrouter/liquid/d1-ultra                          7/7           6     0.857  0.196   0.101    0.000756  0
  openrouter/baseten/elephant-1:free                  7/7           6     0.857  0.216   0.145    0.000000  0
  openrouter/cloudflare/clef-omni                     7/7           7     1.000  0.137   0.278    0.003012  0
  openrouter/nace-ai/drex-max                         7/7           7     1.000  0.006   0.042    0.001164  0
  openrouter/perplexity/pplx-decider-v1.2             7/7           7     1.000  0.023   0.096    0.000386  0
  openrouter/microsoft/microsoft-decision-1           7/7           7     1.000  0.045   0.134    0.000779  0
  openrouter/liquid/d1                                7/7           6     0.857  0.347   0.251    0.000360  0
  openrouter/inception/mercury-decide                 7/7           6     0.857  0.153   0.107    0.000386  0
  openrouter/inception/mercury-decide:free            7/7           6     0.857  0.191   0.119    0.000000  0
  openrouter/upstage/solar-decide                     7/7           6     0.857  0.179   0.007    0.001356  0
  openrouter/openai/gpt-6-luna-decisions              7/7           7     1.000  0.066   0.144    0.001945  0
  openrouter/perplexity/pplx-decider-flash-v1.2       7/7           6     0.857  0.322   0.197    0.000193  0
  openrouter/cloudflare/clef                          7/7           7     1.000  0.060   0.158    0.004974  0
  openrouter/nace-ai/drex-v1.5                        7/7           4     0.571  0.648   0.384    0.000704  0
  openrouter/nace-ai/drex-v2.0                        7/7           4     0.571  0.430   0.251    0.001056  0
  openrouter/togethercomputer/tev1-4b-experimental    7/7           4     0.571  0.426   0.203    0.000855  0
  openrouter/cloudflare/clef-flash                    7/7           7     1.000  0.141   0.275    0.000394  0
  openrouter/jaredpalmer/kev-4b                       7/7           4     0.571  0.552   0.259    0.000739  0
  openrouter/scaledown/classify-1                     7/7           7     1.000  0.360   0.470    0.001055  0
  openrouter/upstage/solar-decide-flash               7/7           1     0.143  0.687   0.415    0.001356  0
  (cost_usd and errors: the model's every call, train and held-out; brier: mean multi-class Brier score, lower is better; ece: expected calibration error over top-probability buckets [0.0, 0.5), [0.5, 0.6), [0.6, 0.7), [0.7, 0.8), [0.8, 0.9), [0.9, 1.0])
unavailable openai/gpt-6-luna: listed but answered no case: OpenAI Decisions error (404): OpenAI Decisions returned 404
unavailable openrouter/perplexity/pplx-decider-v1.1-27b: listed but answered no case: System One API error (404): {"error":{"message":"No endpoints found for perplexity/pplx-decider-v1.1-27b.","code":404},"user_id":"user_2j6vR9TdNFKYEGgN6TJb9xZd5EJ"}
KIT MODEL BESIDE THE BEST (best: highest train accuracy over every train case answered; ties: lower train Brier, lower train cost, name; held-out apart, never used to pick):
        model                                             train acc  train brier  held-out acc  held-out brier  cost_usd
  kit   openrouter/typesafe/jev-1.13                          0.900        0.206         1.000           0.123  0.001074
  best  openrouter/typesafe/jev-1.13                          0.900        0.206         1.000           0.123  0.001074
kit model openrouter/typesafe/jev-1.13 (judgment-model.json): proposed threshold (for the director to accept; until met, the judge stays advisory): held-out accuracy >= 0.699 and held-out brier <= 0.381 (from train only: accuracy_min the Wilson 1.96 lower bound of train accuracy, brier_max train Brier mean + 1.96 standard errors)
held-out now: accuracy 1.000 (7/7 of 7), brier 0.123, ece 0.206: meets the proposed threshold
kit model calibration train (top probability bucket: n, mean top probability, accuracy): [0.0, 0.5) n 1 p 0.470 acc 1.000; [0.5, 0.6) n 2 p 0.550 acc 0.500; [0.6, 0.7) n 1 p 0.640 acc 1.000; [0.7, 0.8) n 4 p 0.725 acc 1.000; [0.8, 0.9) n 4 p 0.857 acc 1.000; [0.9, 1.0] n 8 p 0.955 acc 0.875
kit model calibration held-out (top probability bucket: n, mean top probability, accuracy): [0.5, 0.6) n 1 p 0.550 acc 1.000; [0.6, 0.7) n 1 p 0.670 acc 1.000; [0.7, 0.8) n 2 p 0.740 acc 1.000; [0.9, 1.0] n 3 p 0.953 acc 1.000
DONE bench judgment-test-quality: kit model openrouter/typesafe/jev-1.13, best openrouter/typesafe/jev-1.13 [208.2 s]
qa: 1/1 bench(es) done (run 20261025T144513Z-79e9f1); artifacts /home/exedev/.local/state/octo-feather/qa/20261025T144513Z-79e9f1
```
