# gh119 judgment bench: question (a) test quality, every available classifier (tickets #135, #148)

Spec: docs/specs/judgment.spec.html, #acceptance-judge-bench, #rule-held-out, #boundary-bench.
Suite: evals/judgment-test-quality/ (kind judgment, director-owned, unchanged). Answers below are model judgments: advisory, no gate reads them; `just check` never calls a model.

## Harness (#148)

`scripts/octo-feather-qa --suite judgment-test-quality`. No agent: the bench is a Pi extension command (`extension.js` in the run dir) run as
`pi --no-session --no-skills --no-mcp --no-context-files --no-prompt-templates --no-extensions --no-tools -e <bench-extension.js> -p "/octo-feather-bench <input>"`
inside the qa sandbox (`octo-feather-qc-sandbox`, history none; proof lines in the full output: live Herdr unreachable, no creds; cleanup line: agents started 0). The command calls `ctx.modelRegistry.getAvailableOfType("classifier")` and `ctx.modelRegistry.classify(...)` directly, 4 at once; no chat model turn, so no launcher (docs/adr/0016 covers agents). Each case's state goes as its state string (general rule, no provider names). Choice and threshold from train only; ties on train Brier, then train cost (`train_cost_usd`), then name.

Load rule: one live run at a time; smoke and full run sequential, each one headless pi.

## Smoke first: 3 cases x the 3 Respan span-01 models + jev-1.13 (run 20261023T224948Z-1ae9a6)

```
evals: ok (4 suites, 165 cases)
qa: run 20261023T224948Z-1ae9a6: 3 case(s); kit 091d096e03e3a0f611bda246421e5cbb27dfe1c6; artifacts /home/exedev/.local/state/octo-feather/qa/20261023T224948Z-1ae9a6
qc sandbox: cleanup: agents started 0 (headless pi 0, Herdr panes 0); leftover processes killed 0, left 0 (the kernel kills those as PID 1 exits); session qa-1ae9a6-bench stopped and deleted; offline gh refusals 0
bench judgment-test-quality: question a-test-quality, labels tautological, implementation-coupled, ok; 3 cases (train 2, held-out 1); every answer is a model judgment (classifier output, advisory: no gate reads it)
bench judgment-test-quality: classifiers available (32): openai/gpt-6-luna, openrouter/~perplexity/pplx-decider-latest, openrouter/~typesafe/jev-latest, openrouter/cloudflare/clef, openrouter/cloudflare/clef-flash, openrouter/cloudflare/clef-omni, openrouter/inception/mercury-decide, openrouter/inception/mercury-decide:free, openrouter/jaredpalmer/kev-4b, openrouter/liquid/d1, openrouter/microsoft/microsoft-decision-1, openrouter/nace-ai/drex-v1.5, openrouter/nace-ai/drex-v2.0, openrouter/openai/gpt-6-luna-decisions, openrouter/perplexity/pplx-decider-v1.1-27b, openrouter/respan/span-01, openrouter/respan/span-01-lite, openrouter/respan/span-01-lite:free, openrouter/scaledown/classify-1, openrouter/togethercomputer/tev1-4b-experimental, openrouter/typesafe/jev-1.13, openrouter/typesafe/jev-1.14, openrouter/upstage/solar-decide, openrouter/upstage/solar-decide-flash, openrouter/~perplexity/pplx-decider-flash-latest, openrouter/baseten/elephant-1:free, openrouter/baseten/mammoth-1:free, openrouter/liquid/d1-ultra, openrouter/nace-ai/drex-max, openrouter/perplexity/pplx-decider-flash-v1.2, openrouter/perplexity/pplx-decider-v1.2, openrouter/respan/span-02
bench judgment-test-quality: benched only --classifier openrouter/respan/span-01, openrouter/respan/span-01-lite, openrouter/respan/span-01-lite:free, openrouter/typesafe/jev-1.13
TRAIN (2 cases; the choice and threshold are made here):
  model                                answered  correct  accuracy  brier   ece     cost_usd   errors
  openrouter/typesafe/jev-1.13           2/2           2     1.000  0.013   0.080    0.000069  0
HELD-OUT (1 cases; the measure, never used to choose):
  model                                answered  correct  accuracy  brier   ece     cost_usd   errors
  openrouter/typesafe/jev-1.13           1/1           1     1.000  0.003   0.040    0.000069  0
  (cost_usd and errors: the model's every call, train and held-out; brier: mean multi-class Brier score, lower is better; ece: expected calibration error over top-probability buckets [0.0, 0.5), [0.5, 0.6), [0.6, 0.7), [0.7, 0.8), [0.8, 0.9), [0.9, 1.0])
unavailable openrouter/respan/span-01: listed but answered no case: System One API error (400): {"error":{"message":"Respan only accepts noul questions whose instructions and criteria are plain strings (question \"q\")","code":400}}
unavailable openrouter/respan/span-01-lite: listed but answered no case: System One API error (400): {"error":{"message":"Respan only accepts noul questions whose instructions and criteria are plain strings (question \"q\")","code":400}}
unavailable openrouter/respan/span-01-lite:free: listed but answered no case: System One API error (400): {"error":{"message":"Respan only accepts noul questions whose instructions and criteria are plain strings (question \"q\")","code":400}}
chosen openrouter/typesafe/jev-1.13 (from train only: highest train accuracy over every train case answered; ties: lower train Brier, lower train cost, name): train accuracy 1.000, brier 0.013, ece 0.080
proposed threshold (for the director to accept; until met, the judge stays advisory): held-out accuracy >= 0.342 and held-out brier <= 0.027 (from train only: accuracy_min the Wilson 1.96 lower bound of train accuracy, brier_max train Brier mean + 1.96 standard errors)
held-out now: accuracy 1.000 (1/1 of 1), brier 0.003, ece 0.040: meets the proposed threshold
chosen calibration train (top probability bucket: n, mean top probability, accuracy): [0.9, 1.0] n 2 p 0.920 acc 1.000
chosen calibration held-out (top probability bucket: n, mean top probability, accuracy): [0.9, 1.0] n 1 p 0.960 acc 1.000
DONE bench judgment-test-quality: chosen openrouter/typesafe/jev-1.13 [2.5 s]
qa: 1/1 bench(es) done (run 20261023T224948Z-1ae9a6); artifacts /home/exedev/.local/state/octo-feather/qa/20261023T224948Z-1ae9a6
```

Pipeline real (jev-1.13 classify results, cost from usage). State shape fixed: the Respan 400 is no longer the state error of #135; Respan now rejects the question type: "Respan only accepts noul questions" (noul = Pi's wire name for bool). Probe (same extension mechanism, span-01-lite:free, case 1): a bool question answers (p 0.896), 3 bool questions in one call answer, a score question gets the same 400. So span-01 models take bool questions only; the bench asks one choice question. Open: see Blocker below.

## Demo: full bench (run 20261023T225249Z-8e1c64, 98.3 s)

Artifacts: $(octo-feather-state)/qa/20261023T225249Z-8e1c64/judgment-test-quality/ (input.json, extension.js, stdout.txt, stderr.txt, sandbox.json, answers.json, bench.json, report.txt) and summary.json. Full output:

```
$ scripts/octo-feather-qa --suite judgment-test-quality
evals: ok (4 suites, 165 cases)
qa: run 20261023T225249Z-8e1c64: 22 case(s); kit 091d096e03e3a0f611bda246421e5cbb27dfe1c6; artifacts /home/exedev/.local/state/octo-feather/qa/20261023T225249Z-8e1c64
qc sandbox: ok   /tmp is private (nothing the judge writes there outlives the run)
qc sandbox: ok   judge holds no capabilities (CapEff 0000000000000000), no_new_privs 1, uid 1000
qc sandbox: ok   masks locked: umount of the Herdr mask exits 32, after its own unshare -rm 32
qc sandbox: ok   HOME, /var/tmp, the kit read-only
qc sandbox: ok   worktree /tmp/qa-8e1c64-bench-5go6tvcf is an overlay, upper dir on the run tmpfs and hidden from the judge
qc sandbox: ok   writable persistent paths: none
qc sandbox: ok   vendored-skill cache /home/exedev/.cache/octo-feather/skillfile bound read-only (not writable, not in the writable list)
qc sandbox: ok   live Herdr unreachable: raw herdr --session default workspace list exits 1
qc sandbox: ok   herdr shim pins sandbox session qa-8e1c64-bench despite --session default --remote --machine
qc sandbox: ok   Herdr config shows only the sandbox session: [qa-8e1c64-bench]
qc sandbox: ok   no gh or git creds: tokens 0, gh config entries 0, git-credentials 0 bytes, gh auth status exits 1
qc sandbox: ok   no tracker credential: LINEAR_API_KEY set 0 times
qc sandbox: ok   parent route unset: 0 of OCTO_FEATHER_PARENT/SESSION_ID/ROLE, HERDR_PANE/TAB/WORKSPACE_ID, HERDR_ENV set
qc sandbox: ok   state dir is per-run scratch: /tmp/.qc-qa-8e1c64-bench/state/octo-feather/sessions/qa-8e1c64-bench
qc sandbox: ok   history none (0 bound: no archived lanes, no director log; a factory eval sees no lane history); live records masked (6 paths, 0 bytes or entries visible)
qc sandbox: ok   github: none (factory eval: no GitHub evidence); the offline gh refuses every call (exit 1)
qc sandbox: ok   worktree clean at af3c10d7c51c
qc sandbox: cleanup: agents started 0 (headless pi 0, Herdr panes 0); leftover processes killed 0, left 0 (the kernel kills those as PID 1 exits); session qa-8e1c64-bench stopped and deleted; offline gh refusals 0
bench judgment-test-quality: question a-test-quality, labels tautological, implementation-coupled, ok; 22 cases (train 16, held-out 6); every answer is a model judgment (classifier output, advisory: no gate reads it)
bench judgment-test-quality: classifiers available (32): openai/gpt-6-luna, openrouter/~perplexity/pplx-decider-latest, openrouter/~typesafe/jev-latest, openrouter/cloudflare/clef, openrouter/cloudflare/clef-flash, openrouter/cloudflare/clef-omni, openrouter/inception/mercury-decide, openrouter/inception/mercury-decide:free, openrouter/jaredpalmer/kev-4b, openrouter/liquid/d1, openrouter/microsoft/microsoft-decision-1, openrouter/nace-ai/drex-v1.5, openrouter/nace-ai/drex-v2.0, openrouter/openai/gpt-6-luna-decisions, openrouter/perplexity/pplx-decider-v1.1-27b, openrouter/respan/span-01, openrouter/respan/span-01-lite, openrouter/respan/span-01-lite:free, openrouter/scaledown/classify-1, openrouter/togethercomputer/tev1-4b-experimental, openrouter/typesafe/jev-1.13, openrouter/typesafe/jev-1.14, openrouter/upstage/solar-decide, openrouter/upstage/solar-decide-flash, openrouter/~perplexity/pplx-decider-flash-latest, openrouter/baseten/elephant-1:free, openrouter/baseten/mammoth-1:free, openrouter/liquid/d1-ultra, openrouter/nace-ai/drex-max, openrouter/perplexity/pplx-decider-flash-v1.2, openrouter/perplexity/pplx-decider-v1.2, openrouter/respan/span-02
TRAIN (16 cases; the choice and threshold are made here):
  model                                             answered  correct  accuracy  brier   ece     cost_usd   errors
  openrouter/typesafe/jev-1.13                       16/16         16     1.000  0.105   0.176    0.000806  0
  openrouter/respan/span-02                          16/16         15     0.938  0.089   0.081    0.000158  0
  openrouter/~typesafe/jev-latest                    16/16         15     0.938  0.130   0.137    0.000806  0
  openrouter/typesafe/jev-1.14                       16/16         15     0.938  0.151   0.142    0.000806  0
  openrouter/inception/mercury-decide:free           16/16         15     0.938  0.154   0.076    0.000000  0
  openrouter/baseten/mammoth-1:free                  15/16         14     0.933  0.072   0.051    0.000000  1
  openrouter/liquid/d1-ultra                         16/16         14     0.875  0.163   0.076    0.000546  0
  openrouter/inception/mercury-decide                16/16         14     0.875  0.230   0.105    0.000280  0
  openrouter/cloudflare/clef-omni                    16/16         14     0.875  0.259   0.219    0.002211  0
  openrouter/microsoft/microsoft-decision-1          16/16         14     0.875  0.280   0.219    0.000561  0
  openrouter/baseten/elephant-1:free                 16/16         13     0.812  0.181   0.183    0.000000  0
  openrouter/nace-ai/drex-max                        16/16         13     0.812  0.194   0.129    0.000848  0
  openrouter/perplexity/pplx-decider-flash-v1.2      16/16         13     0.812  0.252   0.210    0.000141  0
  openrouter/~perplexity/pplx-decider-flash-latest   16/16         13     0.812  0.252   0.210    0.000141  0
  openrouter/perplexity/pplx-decider-v1.2            16/16         13     0.812  0.257   0.126    0.000281  0
  openrouter/~perplexity/pplx-decider-latest         16/16         13     0.812  0.257   0.126    0.000281  0
  openrouter/openai/gpt-6-luna-decisions             16/16         12     0.750  0.252   0.213    0.001425  0
  openrouter/cloudflare/clef                         16/16         12     0.750  0.324   0.229    0.003651  0
  openrouter/liquid/d1                               16/16         12     0.750  0.330   0.161    0.000260  0
  openrouter/togethercomputer/tev1-4b-experimental   16/16         12     0.750  0.353   0.175    0.000623  0
  openrouter/upstage/solar-decide                    16/16         12     0.750  0.411   0.246    0.001013  0
  openrouter/nace-ai/drex-v1.5                       16/16         11     0.688  0.357   0.237    0.000506  0
  openrouter/nace-ai/drex-v2.0                       16/16         11     0.688  0.362   0.190    0.000760  0
  openrouter/jaredpalmer/kev-4b                      16/16         11     0.688  0.475   0.166    0.000532  0
  openrouter/cloudflare/clef-flash                   16/16          9     0.562  0.530   0.198    0.000578  0
  openrouter/scaledown/classify-1                    16/16          8     0.500  0.569   0.193    0.000792  0
  openrouter/upstage/solar-decide-flash              16/16          8     0.500  0.579   0.194    0.001013  0
HELD-OUT (6 cases; the measure, never used to choose):
  model                                             answered  correct  accuracy  brier   ece     cost_usd   errors
  openrouter/typesafe/jev-1.13                        6/6           6     1.000  0.109   0.190    0.000806  0
  openrouter/respan/span-02                           6/6           4     0.667  0.265   0.269    0.000158  0
  openrouter/~typesafe/jev-latest                     6/6           6     1.000  0.137   0.207    0.000806  0
  openrouter/typesafe/jev-1.14                        6/6           6     1.000  0.138   0.212    0.000806  0
  openrouter/inception/mercury-decide:free            6/6           5     0.833  0.178   0.124    0.000000  0
  openrouter/baseten/mammoth-1:free                   6/6           6     1.000  0.053   0.124    0.000000  1
  openrouter/liquid/d1-ultra                          6/6           5     0.833  0.174   0.036    0.000546  0
  openrouter/inception/mercury-decide                 6/6           5     0.833  0.250   0.148    0.000280  0
  openrouter/cloudflare/clef-omni                     6/6           6     1.000  0.152   0.293    0.002211  0
  openrouter/microsoft/microsoft-decision-1           6/6           4     0.667  0.391   0.315    0.000561  0
  openrouter/baseten/elephant-1:free                  6/6           5     0.833  0.244   0.140    0.000000  0
  openrouter/nace-ai/drex-max                         6/6           6     1.000  0.003   0.028    0.000848  0
  openrouter/perplexity/pplx-decider-flash-v1.2       6/6           5     0.833  0.316   0.150    0.000141  0
  openrouter/~perplexity/pplx-decider-flash-latest    6/6           5     0.833  0.316   0.150    0.000141  0
  openrouter/perplexity/pplx-decider-v1.2             6/6           6     1.000  0.021   0.090    0.000281  0
  openrouter/~perplexity/pplx-decider-latest          6/6           6     1.000  0.021   0.088    0.000281  0
  openrouter/openai/gpt-6-luna-decisions              6/6           6     1.000  0.052   0.120    0.001425  0
  openrouter/cloudflare/clef                          6/6           6     1.000  0.057   0.147    0.003651  0
  openrouter/liquid/d1                                6/6           4     0.667  0.483   0.305    0.000260  0
  openrouter/togethercomputer/tev1-4b-experimental    6/6           4     0.667  0.387   0.169    0.000623  0
  openrouter/upstage/solar-decide                     6/6           6     1.000  0.011   0.033    0.001013  0
  openrouter/nace-ai/drex-v1.5                        6/6           4     0.667  0.590   0.350    0.000506  0
  openrouter/nace-ai/drex-v2.0                        6/6           3     0.500  0.420   0.328    0.000760  0
  openrouter/jaredpalmer/kev-4b                       6/6           4     0.667  0.484   0.228    0.000532  0
  openrouter/cloudflare/clef-flash                    6/6           6     1.000  0.134   0.264    0.000578  0
  openrouter/scaledown/classify-1                     6/6           6     1.000  0.324   0.446    0.000792  0
  openrouter/upstage/solar-decide-flash               6/6           1     0.167  0.669   0.374    0.001013  0
  (cost_usd and errors: the model's every call, train and held-out; brier: mean multi-class Brier score, lower is better; ece: expected calibration error over top-probability buckets [0.0, 0.5), [0.5, 0.6), [0.6, 0.7), [0.7, 0.8), [0.8, 0.9), [0.9, 1.0])
unavailable openai/gpt-6-luna: listed but answered no case: OpenAI Decisions error (404): OpenAI Decisions returned 404
unavailable openrouter/perplexity/pplx-decider-v1.1-27b: listed but answered no case: System One API error (404): {"error":{"message":"No endpoints found for perplexity/pplx-decider-v1.1-27b.","code":404},"user_id":"user_2j6vR9TdNFKYEGgN6TJb9xZd5EJ"}
unavailable openrouter/respan/span-01: listed but answered no case: System One API error (400): {"error":{"message":"Respan only accepts noul questions whose instructions and criteria are plain strings (question \"q\")","code":400}}
unavailable openrouter/respan/span-01-lite: listed but answered no case: System One API error (400): {"error":{"message":"Respan only accepts noul questions whose instructions and criteria are plain strings (question \"q\")","code":400}}
unavailable openrouter/respan/span-01-lite:free: listed but answered no case: System One API error (400): {"error":{"message":"Respan only accepts noul questions whose instructions and criteria are plain strings (question \"q\")","code":400}}
errors openrouter/baseten/mammoth-1:free: 1 case(s) unanswered, first: System One API error (429): {"error":{"message":"Rate limit exceeded: free-models-per-min. ","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"20","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1792796100000"},"limit_source":"openrouter_free_tier_per_minute","remedy_hint":"Slow down requests to free models, or retry after the per-minute window resets."}}}
chosen openrouter/typesafe/jev-1.13 (from train only: highest train accuracy over every train case answered; ties: lower train Brier, lower train cost, name): train accuracy 1.000, brier 0.105, ece 0.176
proposed threshold (for the director to accept; until met, the judge stays advisory): held-out accuracy >= 0.806 and held-out brier <= 0.177 (from train only: accuracy_min the Wilson 1.96 lower bound of train accuracy, brier_max train Brier mean + 1.96 standard errors)
held-out now: accuracy 1.000 (6/6 of 6), brier 0.109, ece 0.190: meets the proposed threshold
chosen calibration train (top probability bucket: n, mean top probability, accuracy): [0.0, 0.5) n 1 p 0.490 acc 1.000; [0.5, 0.6) n 2 p 0.560 acc 1.000; [0.7, 0.8) n 3 p 0.737 acc 1.000; [0.8, 0.9) n 2 p 0.855 acc 1.000; [0.9, 1.0] n 8 p 0.958 acc 1.000
chosen calibration held-out (top probability bucket: n, mean top probability, accuracy): [0.5, 0.6) n 1 p 0.590 acc 1.000; [0.6, 0.7) n 1 p 0.660 acc 1.000; [0.7, 0.8) n 1 p 0.780 acc 1.000; [0.9, 1.0] n 3 p 0.943 acc 1.000
DONE bench judgment-test-quality: chosen openrouter/typesafe/jev-1.13 [98.3 s]
qa: 1/1 bench(es) done (run 20261023T225249Z-8e1c64); artifacts /home/exedev/.local/state/octo-feather/qa/20261023T225249Z-8e1c64
```

## Cost (owner ruling: per-model cost_usd and the run total; no spend ledger)

From this run's bench.json `models[].cost_usd` (every call, train and held-out) and `train_cost_usd` (the tie-break). Run total: $0.019016 (sum of per-model cost_usd; bench.json `cost_usd` carries this total from the commit after this run on).

| model | cost_usd | train_cost_usd |
|---|---|---|
| openai/gpt-6-luna | 0.000000 | 0.000000 |
| openrouter/~perplexity/pplx-decider-latest | 0.000281 | 0.000208 |
| openrouter/~typesafe/jev-latest | 0.000806 | 0.000593 |
| openrouter/cloudflare/clef | 0.003651 | 0.002699 |
| openrouter/cloudflare/clef-flash | 0.000578 | 0.000427 |
| openrouter/cloudflare/clef-omni | 0.002211 | 0.001632 |
| openrouter/inception/mercury-decide | 0.000280 | 0.000208 |
| openrouter/inception/mercury-decide:free | 0.000000 | 0.000000 |
| openrouter/jaredpalmer/kev-4b | 0.000532 | 0.000394 |
| openrouter/liquid/d1 | 0.000260 | 0.000193 |
| openrouter/microsoft/microsoft-decision-1 | 0.000561 | 0.000418 |
| openrouter/nace-ai/drex-v1.5 | 0.000506 | 0.000376 |
| openrouter/nace-ai/drex-v2.0 | 0.000760 | 0.000563 |
| openrouter/openai/gpt-6-luna-decisions | 0.001425 | 0.001052 |
| openrouter/perplexity/pplx-decider-v1.1-27b | 0.000000 | 0.000000 |
| openrouter/respan/span-01 | 0.000000 | 0.000000 |
| openrouter/respan/span-01-lite | 0.000000 | 0.000000 |
| openrouter/respan/span-01-lite:free | 0.000000 | 0.000000 |
| openrouter/scaledown/classify-1 | 0.000792 | 0.000584 |
| openrouter/togethercomputer/tev1-4b-experimental | 0.000623 | 0.000463 |
| openrouter/typesafe/jev-1.13 | 0.000806 | 0.000593 |
| openrouter/typesafe/jev-1.14 | 0.000806 | 0.000593 |
| openrouter/upstage/solar-decide | 0.001013 | 0.000748 |
| openrouter/upstage/solar-decide-flash | 0.001013 | 0.000748 |
| openrouter/~perplexity/pplx-decider-flash-latest | 0.000141 | 0.000104 |
| openrouter/baseten/elephant-1:free | 0.000000 | 0.000000 |
| openrouter/baseten/mammoth-1:free | 0.000000 | 0.000000 |
| openrouter/liquid/d1-ultra | 0.000546 | 0.000406 |
| openrouter/nace-ai/drex-max | 0.000848 | 0.000628 |
| openrouter/perplexity/pplx-decider-flash-v1.2 | 0.000141 | 0.000104 |
| openrouter/perplexity/pplx-decider-v1.2 | 0.000281 | 0.000208 |
| openrouter/respan/span-02 | 0.000158 | 0.000118 |

## Reading

- 32 listed; 27 scored; 5 unavailable: gpt-6-luna direct 404, pplx-decider-v1.1-27b 404 no endpoint (provider reasons); 3 Respan span-01 models 400, bool-only question type (provider capability, not our state shape; see Blocker).
- mammoth-1:free: 1 case unanswered, OpenRouter free-tier 429 rate limit (provider reason), so 15/16 train and not eligible for the choice.
- Chosen from train only: openrouter/typesafe/jev-1.13 (train 16/16, Brier 0.105). Proposed threshold: held-out accuracy >= 0.806 and Brier <= 0.177. Held-out now 6/6, Brier 0.109: meets.

## Blocker (to supervisor)

Acceptance asks Respan span-01 scored. They accept only bool questions; the closed question is a 3-label choice. Scoring them needs a question-form decision (see report).
