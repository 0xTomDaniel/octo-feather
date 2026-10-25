# gh119 judgment bench: question (d) call evidence, every available classifier (ticket #155)

Spec: docs/specs/judgment.spec.html, #acceptance-judge-labelled, #acceptance-judge-bench, #rules.
Suite: evals/judgment-call-evidence/ (kind judgment, director-owned): 33 cases, all real factory history (spec calls logged in docs/specs/*.calls.jsonl on main and branches; none constructed, no near-misses). Answers below are model judgments: advisory, no gate reads them; `just check` never calls a model.

## Set (copied as is)

From /tmp/gh119/labels/d-call-evidence (final, director-checked and owned 2026-10-23). question.json and cases.json byte-identical; every reference entry keeps its label, reason and source and adds `labelled_by: director`; gh80-prompt-eval-owed-evals-home also carries the set REPORT's one flip as `relabel` (does-not-show to shows, director ruling: an owner-ruled correction in force counts as shows). REPORT.md generated from cases.json and expectations.json, counts demo pasted. Totals: shows 9 (train 6, held-out 3), does-not-show 24 (train 15, held-out 9); train 21, held-out 12.

Scripted diff against the /tmp set (`/tmp/gh119/work-bcd/build.py diff d .`, compares question, cases and expectations with labelled_by and relabel dropped):

```
judgment-call-evidence: data equal to /tmp/gh119/labels/d-call-evidence (question, cases, expectations ignoring added labelled_by, relabel); 33 cases, labelled_by director 33, relabel ['gh80-prompt-eval-owed-evals-home']; files ['cases.json', 'question.json', 'reference/expectations.json', 'suite.json']
```

## Harness

Same as the pilot (evidence/2026-10-23-gh119-judgment-bench.md, Harness): `scripts/octo-feather-qa --suite judgment-call-evidence`, one Pi extension command in the qa sandbox, no agent, no chat model turn; choice and threshold from train only. Load rule: one live run at a time; smoke then full run, sequential. Both runs at kit 1f2017b (the suite only); the commit holding this file has the same evals/ tree.

## Smoke first: 3 cases x jev-1.13 (run 20261024T021613Z-1a537e)

```
$ scripts/octo-feather-qa --suite judgment-call-evidence --case gh54-public-surfaces-library --case gh80-prompt-eval-owed-evals-home --case gh56-signed-in-accept-record --classifier openrouter/typesafe/jev-1.13
evals: ok (5 suites, 203 cases)
qa: run 20261024T021613Z-1a537e: 3 case(s); kit 1f2017bbe7336fa9ff1a29d8dedde00f8d302d7b; artifacts /home/exedev/.local/state/octo-feather/qa/20261024T021613Z-1a537e
qc sandbox: ok   /tmp is private (nothing the judge writes there outlives the run)
qc sandbox: ok   judge holds no capabilities (CapEff 0000000000000000), no_new_privs 1, uid 1000
qc sandbox: ok   masks locked: umount of the Herdr mask exits 32, after its own unshare -rm 32
qc sandbox: ok   HOME, /var/tmp, the kit read-only
qc sandbox: ok   worktree /tmp/qa-1a537e-bench-y4or79xt is an overlay, upper dir on the run tmpfs and hidden from the judge
qc sandbox: ok   writable persistent paths: none
qc sandbox: ok   vendored-skill cache /home/exedev/.cache/octo-feather/skillfile bound read-only (not writable, not in the writable list)
qc sandbox: ok   live Herdr unreachable: raw herdr --session default workspace list exits 1
qc sandbox: ok   herdr shim pins sandbox session qa-1a537e-bench despite --session default --remote --machine
qc sandbox: ok   Herdr config shows only the sandbox session: [qa-1a537e-bench]
qc sandbox: ok   no gh or git creds: tokens 0, gh config entries 0, git-credentials 0 bytes, gh auth status exits 1
qc sandbox: ok   no tracker credential: LINEAR_API_KEY set 0 times
qc sandbox: ok   parent route unset: 0 of OCTO_FEATHER_PARENT/SESSION_ID/ROLE, HERDR_PANE/TAB/WORKSPACE_ID, HERDR_ENV set
qc sandbox: ok   state dir is per-run scratch: /tmp/.qc-qa-1a537e-bench/state/octo-feather/sessions/qa-1a537e-bench
qc sandbox: ok   history none (0 bound: no archived lanes, no director log; a factory eval sees no lane history); live records masked (6 paths, 0 bytes or entries visible)
qc sandbox: ok   github: none (factory eval: no GitHub evidence); the offline gh refuses every call (exit 1)
qc sandbox: ok   worktree clean at 3350dd698a3b
qc sandbox: cleanup: agents started 0 (headless pi 0, Herdr panes 0); leftover processes killed 1, left 0 (the kernel kills those as PID 1 exits); session qa-1a537e-bench stopped and deleted; offline gh refusals 0
bench judgment-call-evidence: question d-call-evidence, labels shows, does-not-show; 3 cases (train 2, held-out 1); every answer is a model judgment (classifier output, advisory: no gate reads it)
bench judgment-call-evidence: classifiers available (32): openai/gpt-6-luna, openrouter/~perplexity/pplx-decider-latest, openrouter/~typesafe/jev-latest, openrouter/cloudflare/clef, openrouter/cloudflare/clef-flash, openrouter/cloudflare/clef-omni, openrouter/inception/mercury-decide, openrouter/inception/mercury-decide:free, openrouter/jaredpalmer/kev-4b, openrouter/liquid/d1, openrouter/microsoft/microsoft-decision-1, openrouter/nace-ai/drex-v1.5, openrouter/nace-ai/drex-v2.0, openrouter/openai/gpt-6-luna-decisions, openrouter/perplexity/pplx-decider-v1.1-27b, openrouter/respan/span-01, openrouter/respan/span-01-lite, openrouter/respan/span-01-lite:free, openrouter/scaledown/classify-1, openrouter/togethercomputer/tev1-4b-experimental, openrouter/typesafe/jev-1.13, openrouter/typesafe/jev-1.14, openrouter/upstage/solar-decide, openrouter/upstage/solar-decide-flash, openrouter/~perplexity/pplx-decider-flash-latest, openrouter/baseten/elephant-1:free, openrouter/baseten/mammoth-1:free, openrouter/liquid/d1-ultra, openrouter/nace-ai/drex-max, openrouter/perplexity/pplx-decider-flash-v1.2, openrouter/perplexity/pplx-decider-v1.2, openrouter/respan/span-02
bench judgment-call-evidence: benched only --classifier openrouter/typesafe/jev-1.13
TRAIN (2 cases; the choice and threshold are made here):
  model                         answered  correct  accuracy  brier   ece     cost_usd   errors
  openrouter/typesafe/jev-1.13    2/2           1     0.500  0.836   0.530    0.000083  0
HELD-OUT (1 cases; the measure, never used to choose):
  model                         answered  correct  accuracy  brier   ece     cost_usd   errors
  openrouter/typesafe/jev-1.13    1/1           1     1.000  0.125   0.250    0.000083  0
  (cost_usd and errors: the model's every call, train and held-out; brier: mean multi-class Brier score, lower is better; ece: expected calibration error over top-probability buckets [0.0, 0.5), [0.5, 0.6), [0.6, 0.7), [0.7, 0.8), [0.8, 0.9), [0.9, 1.0])
chosen openrouter/typesafe/jev-1.13 (from train only: highest train accuracy over every train case answered; ties: lower train Brier, lower train cost, name): train accuracy 0.500, brier 0.836, ece 0.530
proposed threshold (for the director to accept; until met, the judge stays advisory): held-out accuracy >= 0.095 and held-out brier <= 2.373 (from train only: accuracy_min the Wilson 1.96 lower bound of train accuracy, brier_max train Brier mean + 1.96 standard errors)
held-out now: accuracy 1.000 (1/1 of 1), brier 0.125, ece 0.250: meets the proposed threshold
chosen calibration train (top probability bucket: n, mean top probability, accuracy): [0.8, 0.9) n 1 p 0.840 acc 1.000; [0.9, 1.0] n 1 p 0.900 acc 0.000
chosen calibration held-out (top probability bucket: n, mean top probability, accuracy): [0.7, 0.8) n 1 p 0.750 acc 1.000
DONE bench judgment-call-evidence: chosen openrouter/typesafe/jev-1.13 [2.2 s]
qa: 1/1 bench(es) done (run 20261024T021613Z-1a537e); artifacts /home/exedev/.local/state/octo-feather/qa/20261024T021613Z-1a537e
```

Pipeline real: 3 classify results with cost from usage; the hidden reference (labelled_by, relabel, reason) absent from input.json, extension.js and stdout.txt (grep count 0). jev-1.13 answers: gh54 shows (right, p 0.75), gh80 shows (right, p 0.84), gh56 shows (wrong, p 0.90).

## Demo: full bench (run 20261024T021628Z-d09cbc, 135.3 s, kit 1f2017b)

Artifacts: $(octo-feather-state)/qa/20261024T021628Z-d09cbc/judgment-call-evidence/ (input.json, extension.js, stdout.txt, stderr.txt, sandbox.json, answers.json, bench.json, report.txt) and summary.json. Full output:

```
$ scripts/octo-feather-qa --suite judgment-call-evidence
evals: ok (5 suites, 203 cases)
qa: run 20261024T021628Z-d09cbc: 33 case(s); kit 1f2017bbe7336fa9ff1a29d8dedde00f8d302d7b; artifacts /home/exedev/.local/state/octo-feather/qa/20261024T021628Z-d09cbc
qc sandbox: ok   /tmp is private (nothing the judge writes there outlives the run)
qc sandbox: ok   judge holds no capabilities (CapEff 0000000000000000), no_new_privs 1, uid 1000
qc sandbox: ok   masks locked: umount of the Herdr mask exits 32, after its own unshare -rm 32
qc sandbox: ok   HOME, /var/tmp, the kit read-only
qc sandbox: ok   worktree /tmp/qa-d09cbc-bench-9po8zpbh is an overlay, upper dir on the run tmpfs and hidden from the judge
qc sandbox: ok   writable persistent paths: none
qc sandbox: ok   vendored-skill cache /home/exedev/.cache/octo-feather/skillfile bound read-only (not writable, not in the writable list)
qc sandbox: ok   live Herdr unreachable: raw herdr --session default workspace list exits 1
qc sandbox: ok   herdr shim pins sandbox session qa-d09cbc-bench despite --session default --remote --machine
qc sandbox: ok   Herdr config shows only the sandbox session: [qa-d09cbc-bench]
qc sandbox: ok   no gh or git creds: tokens 0, gh config entries 0, git-credentials 0 bytes, gh auth status exits 1
qc sandbox: ok   no tracker credential: LINEAR_API_KEY set 0 times
qc sandbox: ok   parent route unset: 0 of OCTO_FEATHER_PARENT/SESSION_ID/ROLE, HERDR_PANE/TAB/WORKSPACE_ID, HERDR_ENV set
qc sandbox: ok   state dir is per-run scratch: /tmp/.qc-qa-d09cbc-bench/state/octo-feather/sessions/qa-d09cbc-bench
qc sandbox: ok   history none (0 bound: no archived lanes, no director log; a factory eval sees no lane history); live records masked (6 paths, 0 bytes or entries visible)
qc sandbox: ok   github: none (factory eval: no GitHub evidence); the offline gh refuses every call (exit 1)
qc sandbox: ok   worktree clean at b68567c4f069
qc sandbox: cleanup: agents started 0 (headless pi 0, Herdr panes 0); leftover processes killed 0, left 0 (the kernel kills those as PID 1 exits); session qa-d09cbc-bench stopped and deleted; offline gh refusals 0
bench judgment-call-evidence: question d-call-evidence, labels shows, does-not-show; 33 cases (train 21, held-out 12); every answer is a model judgment (classifier output, advisory: no gate reads it)
bench judgment-call-evidence: classifiers available (32): openai/gpt-6-luna, openrouter/~perplexity/pplx-decider-latest, openrouter/~typesafe/jev-latest, openrouter/cloudflare/clef, openrouter/cloudflare/clef-flash, openrouter/cloudflare/clef-omni, openrouter/inception/mercury-decide, openrouter/inception/mercury-decide:free, openrouter/jaredpalmer/kev-4b, openrouter/liquid/d1, openrouter/microsoft/microsoft-decision-1, openrouter/nace-ai/drex-v1.5, openrouter/nace-ai/drex-v2.0, openrouter/openai/gpt-6-luna-decisions, openrouter/perplexity/pplx-decider-v1.1-27b, openrouter/respan/span-01, openrouter/respan/span-01-lite, openrouter/respan/span-01-lite:free, openrouter/scaledown/classify-1, openrouter/togethercomputer/tev1-4b-experimental, openrouter/typesafe/jev-1.13, openrouter/typesafe/jev-1.14, openrouter/upstage/solar-decide, openrouter/upstage/solar-decide-flash, openrouter/~perplexity/pplx-decider-flash-latest, openrouter/baseten/elephant-1:free, openrouter/baseten/mammoth-1:free, openrouter/liquid/d1-ultra, openrouter/nace-ai/drex-max, openrouter/perplexity/pplx-decider-flash-v1.2, openrouter/perplexity/pplx-decider-v1.2, openrouter/respan/span-02
bench judgment-call-evidence: skipped: moving alias (3): openrouter/~perplexity/pplx-decider-latest, openrouter/~typesafe/jev-latest, openrouter/~perplexity/pplx-decider-flash-latest
TRAIN (21 cases; the choice and threshold are made here):
  model                                             answered  correct  accuracy  brier   ece     cost_usd   errors
  openrouter/nace-ai/drex-max                        21/21         16     0.762  0.379   0.232    0.000904  0
  openrouter/perplexity/pplx-decider-v1.2            21/21         15     0.714  0.298   0.190    0.000299  0
  openrouter/openai/gpt-6-luna-decisions             21/21         14     0.667  0.458   0.131    0.001551  0
  openrouter/perplexity/pplx-decider-flash-v1.2      21/21         14     0.667  0.614   0.301    0.000150  0
  openrouter/baseten/mammoth-1:free                  19/21         12     0.632  0.600   0.340    0.000000  2
  openrouter/upstage/solar-decide                    21/21         13     0.619  0.562   0.264    0.001165  0
  openrouter/typesafe/jev-1.13                       21/21         13     0.619  0.594   0.215    0.000945  0
  openrouter/microsoft/microsoft-decision-1          21/21         13     0.619  0.602   0.310    0.000558  0
  openrouter/typesafe/jev-1.14                       21/21         13     0.619  0.635   0.286    0.000945  0
  openrouter/nace-ai/drex-v2.0                       21/21         13     0.619  0.693   0.403    0.000773  0
  openrouter/cloudflare/clef-omni                    21/21         12     0.571  0.495   0.095    0.002425  0
  openrouter/togethercomputer/tev1-4b-experimental   21/21         12     0.571  0.500   0.131    0.000637  0
  openrouter/jaredpalmer/kev-4b                      21/21         12     0.571  0.514   0.120    0.000541  0
  openrouter/inception/mercury-decide:free           21/21         12     0.571  0.832   0.406    0.000000  0
  openrouter/inception/mercury-decide                21/21         12     0.571  0.832   0.411    0.000280  0
  openrouter/liquid/d1-ultra                         21/21         11     0.524  0.497   0.290    0.000560  0
  openrouter/liquid/d1                               21/21         11     0.524  0.737   0.302    0.000267  0
  openrouter/respan/span-02                          21/21         11     0.524  0.761   0.343    0.000158  0
  openrouter/cloudflare/clef                         21/21         10     0.476  0.656   0.329    0.003931  0
  openrouter/baseten/elephant-1:free                 21/21         10     0.476  0.829   0.479    0.000000  0
  openrouter/scaledown/classify-1                    21/21          9     0.429  0.643   0.270    0.000903  0
  openrouter/cloudflare/clef-flash                   21/21          8     0.381  0.638   0.308    0.000622  0
  openrouter/nace-ai/drex-v1.5                       21/21          8     0.381  1.050   0.517    0.000515  0
  openrouter/upstage/solar-decide-flash              21/21          7     0.333  0.756   0.386    0.001165  0
HELD-OUT (12 cases; the measure, never used to choose):
  model                                             answered  correct  accuracy  brier   ece     cost_usd   errors
  openrouter/nace-ai/drex-max                        12/12         11     0.917  0.235   0.158    0.000904  0
  openrouter/perplexity/pplx-decider-v1.2            12/12         10     0.833  0.249   0.093    0.000299  0
  openrouter/openai/gpt-6-luna-decisions             12/12         11     0.917  0.271   0.239    0.001551  0
  openrouter/perplexity/pplx-decider-flash-v1.2      12/12          8     0.667  0.592   0.308    0.000150  0
  openrouter/baseten/mammoth-1:free                  12/12          6     0.500  0.507   0.372    0.000000  2
  openrouter/upstage/solar-decide                    12/12          6     0.500  0.526   0.394    0.001165  0
  openrouter/typesafe/jev-1.13                       12/12          9     0.750  0.426   0.133    0.000945  0
  openrouter/microsoft/microsoft-decision-1          12/12         10     0.833  0.412   0.277    0.000558  0
  openrouter/typesafe/jev-1.14                       12/12          9     0.750  0.440   0.119    0.000945  0
  openrouter/nace-ai/drex-v2.0                       12/12          8     0.667  0.542   0.256    0.000773  0
  openrouter/cloudflare/clef-omni                    12/12          9     0.750  0.356   0.211    0.002425  0
  openrouter/togethercomputer/tev1-4b-experimental   12/12          7     0.583  0.601   0.185    0.000637  0
  openrouter/jaredpalmer/kev-4b                      12/12          6     0.500  0.510   0.098    0.000541  0
  openrouter/inception/mercury-decide:free           12/12          9     0.750  0.496   0.242    0.000000  0
  openrouter/inception/mercury-decide                12/12          9     0.750  0.496   0.242    0.000280  0
  openrouter/liquid/d1-ultra                         12/12          8     0.667  0.429   0.257    0.000560  0
  openrouter/liquid/d1                               12/12          7     0.583  0.436   0.251    0.000267  0
  openrouter/respan/span-02                          12/12          7     0.583  0.634   0.383    0.000158  0
  openrouter/cloudflare/clef                         12/12          7     0.583  0.599   0.262    0.003931  0
  openrouter/baseten/elephant-1:free                 12/12          7     0.583  0.621   0.368    0.000000  0
  openrouter/scaledown/classify-1                    12/12          7     0.583  0.499   0.211    0.000903  0
  openrouter/cloudflare/clef-flash                   12/12          8     0.667  0.409   0.258    0.000622  0
  openrouter/nace-ai/drex-v1.5                       12/12          3     0.250  0.961   0.557    0.000515  0
  openrouter/upstage/solar-decide-flash              12/12          4     0.333  0.788   0.432    0.001165  0
  (cost_usd and errors: the model's every call, train and held-out; brier: mean multi-class Brier score, lower is better; ece: expected calibration error over top-probability buckets [0.0, 0.5), [0.5, 0.6), [0.6, 0.7), [0.7, 0.8), [0.8, 0.9), [0.9, 1.0])
unavailable openai/gpt-6-luna: listed but answered no case: OpenAI Decisions error (404): OpenAI Decisions returned 404
unavailable openrouter/perplexity/pplx-decider-v1.1-27b: listed but answered no case: System One API error (404): {"error":{"message":"No endpoints found for perplexity/pplx-decider-v1.1-27b.","code":404},"user_id":"user_2j6vR9TdNFKYEGgN6TJb9xZd5EJ"}
unavailable openrouter/respan/span-01: listed but answered no case: System One API error (400): {"error":{"message":"Respan only accepts noul questions whose instructions and criteria are plain strings (question \"q\")","code":400}}
unavailable openrouter/respan/span-01-lite: listed but answered no case: System One API error (400): {"error":{"message":"Respan only accepts noul questions whose instructions and criteria are plain strings (question \"q\")","code":400}}
unavailable openrouter/respan/span-01-lite:free: listed but answered no case: System One API error (400): {"error":{"message":"Respan only accepts noul questions whose instructions and criteria are plain strings (question \"q\")","code":400}}
errors openrouter/baseten/mammoth-1:free: 2 case(s) unanswered, first: System One API error (429): {"error":{"message":"Rate limit exceeded: free-models-per-min. ","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"20","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1792808340000"},"limit_source":"openrouter_free_tier_per_minute","remedy_hint":"Slow down requests to free models, or retry after the per-minute window resets."}}}
chosen openrouter/nace-ai/drex-max (from train only: highest train accuracy over every train case answered; ties: lower train Brier, lower train cost, name): train accuracy 0.762, brier 0.379, ece 0.232
proposed threshold (for the director to accept; until met, the judge stays advisory): held-out accuracy >= 0.549 and held-out brier <= 0.655 (from train only: accuracy_min the Wilson 1.96 lower bound of train accuracy, brier_max train Brier mean + 1.96 standard errors)
held-out now: accuracy 0.917 (11/12 of 12), brier 0.235, ece 0.158: meets the proposed threshold
chosen calibration train (top probability bucket: n, mean top probability, accuracy): [0.5, 0.6) n 2 p 0.546 acc 1.000; [0.6, 0.7) n 2 p 0.664 acc 0.000; [0.8, 0.9) n 1 p 0.872 acc 1.000; [0.9, 1.0] n 16 p 0.970 acc 0.812
chosen calibration held-out (top probability bucket: n, mean top probability, accuracy): [0.5, 0.6) n 2 p 0.554 acc 1.000; [0.8, 0.9) n 1 p 0.872 acc 1.000; [0.9, 1.0] n 9 p 0.986 acc 0.889
DONE bench judgment-call-evidence: chosen openrouter/nace-ai/drex-max [135.3 s]
qa: 1/1 bench(es) done (run 20261024T021628Z-d09cbc); artifacts /home/exedev/.local/state/octo-feather/qa/20261024T021628Z-d09cbc
```

## Cost (per-model cost_usd and the run total; no spend ledger)

From this run's bench.json `models[].cost_usd` (every call, train and held-out) and `train_cost_usd` (the tie-break). Run total (bench.json `cost_usd`): $0.019294. Skipped moving aliases make no call and carry no cost: openrouter/~perplexity/pplx-decider-latest, openrouter/~typesafe/jev-latest, openrouter/~perplexity/pplx-decider-flash-latest.

| model | cost_usd | train_cost_usd |
|---|---|---|
| openai/gpt-6-luna | 0.000000 | 0.000000 |
| openrouter/cloudflare/clef | 0.003931 | 0.002493 |
| openrouter/cloudflare/clef-flash | 0.000622 | 0.000395 |
| openrouter/cloudflare/clef-omni | 0.002425 | 0.001538 |
| openrouter/inception/mercury-decide | 0.000280 | 0.000177 |
| openrouter/inception/mercury-decide:free | 0.000000 | 0.000000 |
| openrouter/jaredpalmer/kev-4b | 0.000541 | 0.000343 |
| openrouter/liquid/d1 | 0.000267 | 0.000169 |
| openrouter/microsoft/microsoft-decision-1 | 0.000558 | 0.000354 |
| openrouter/nace-ai/drex-v1.5 | 0.000515 | 0.000327 |
| openrouter/nace-ai/drex-v2.0 | 0.000773 | 0.000490 |
| openrouter/openai/gpt-6-luna-decisions | 0.001551 | 0.000985 |
| openrouter/perplexity/pplx-decider-v1.1-27b | 0.000000 | 0.000000 |
| openrouter/respan/span-01 | 0.000000 | 0.000000 |
| openrouter/respan/span-01-lite | 0.000000 | 0.000000 |
| openrouter/respan/span-01-lite:free | 0.000000 | 0.000000 |
| openrouter/scaledown/classify-1 | 0.000903 | 0.000573 |
| openrouter/togethercomputer/tev1-4b-experimental | 0.000637 | 0.000404 |
| openrouter/typesafe/jev-1.13 | 0.000945 | 0.000600 |
| openrouter/typesafe/jev-1.14 | 0.000945 | 0.000600 |
| openrouter/upstage/solar-decide | 0.001165 | 0.000739 |
| openrouter/upstage/solar-decide-flash | 0.001165 | 0.000739 |
| openrouter/baseten/elephant-1:free | 0.000000 | 0.000000 |
| openrouter/baseten/mammoth-1:free | 0.000000 | 0.000000 |
| openrouter/liquid/d1-ultra | 0.000560 | 0.000355 |
| openrouter/nace-ai/drex-max | 0.000904 | 0.000573 |
| openrouter/perplexity/pplx-decider-flash-v1.2 | 0.000150 | 0.000095 |
| openrouter/perplexity/pplx-decider-v1.2 | 0.000299 | 0.000190 |
| openrouter/respan/span-02 | 0.000158 | 0.000100 |

## Reading

- 32 listed; 3 moving aliases skipped (never called); 29 benched; 24 scored; 5 unavailable, same provider reasons as the pilot: gpt-6-luna direct 404, pplx-decider-v1.1-27b 404 no endpoint, Respan span-01, span-01-lite, span-01-lite:free 400 (bool-only questions; this is a 2-label choice question). mammoth-1:free answered 31 of 33 (2 provider 429 rate-limit errors on the free tier), scored on what it answered.
- Chosen from train only: openrouter/nace-ai/drex-max (train 16/21, 0.762, Brier 0.379), no tie. Proposed threshold: held-out accuracy >= 0.549 and Brier <= 0.655. Held-out now 11/12 (0.917), Brier 0.235: meets.
- Weak question for these models: the majority label (does-not-show) alone scores train 15/21 (0.714) and held-out 9/12 (0.750); the chosen model clears that by one train case. The calibration is overconfident at the top: 16 train answers at p >= 0.9 are right 0.812 of the time.
- Hardest cases (right answers out of 24 scored models): gh82-owner-pr-tracker 0, gh82-gate-green-linear-ban 0 (held-out), gh56-signed-in-accept-record 2, then gh67-qc-listed-parallel 4 and five more at 5: all does-not-show calls whose evidence is a real failure or contradiction bearing on a line other than the named criterion, or naming only criteria not in the accepted spec. Models answer shows on any evidence that sounds like a failure. drex-max misses 6: five does-not-show (gh82-owner-pr-tracker, gh82-gate-green-linear-ban, gh67-qc-listed-parallel, gh67-tab-headless-reviewer, gh82-issue-view-sub-issues) and one shows (gh67-patch-only-interrogate-folder, train).

## Rebench for the kit's one judgment model (run 20261025T144846Z-9643eb, 2026-10-25)

Owner ruling 2026-10-25 (spec judgment#rule-one-model): one judgment model for every question, openrouter/typesafe/jev-1.13,
recorded in evals/judgment-model.json (evidence/2026-10-25-gh119-judgment-model.md). This rerun refreshes this suite's
`calibration` (the kit model's held-out score and proposed threshold, accepted false); the bench shows the kit's model
beside the question's best-scoring classifier and no longer names a per-question choice. The Respan span-01 models are
now "skipped: yes/no only" by the probe (a tiny choice question refused, a tiny bool question answered), no longer unavailable.

`scripts/octo-feather-qa --suite judgment-call-evidence` (sandbox proof lines omitted; artifacts $(octo-feather-state)/qa/20261025T144846Z-9643eb/):

```
evals: ok (8 suites, 272 cases)
qa: run 20261025T144846Z-9643eb: 33 case(s); kit e19b3c8ada566378f6edd48b94942ed00c1d6105; artifacts /home/exedev/.local/state/octo-feather/qa/20261025T144846Z-9643eb
qc sandbox: cleanup: agents started 0 (headless pi 0, Herdr panes 0); leftover processes killed 0, left 0 (the kernel kills those as PID 1 exits); session qa-9643eb-bench stopped and deleted; offline gh refusals 0
bench judgment-call-evidence: question d-call-evidence, labels shows, does-not-show; 33 cases (train 21, held-out 12); every answer is a model judgment (classifier output, advisory: no gate reads it)
bench judgment-call-evidence: classifiers available (32): openai/gpt-6-luna, openrouter/~perplexity/pplx-decider-latest, openrouter/~typesafe/jev-latest, openrouter/cloudflare/clef, openrouter/cloudflare/clef-flash, openrouter/cloudflare/clef-omni, openrouter/inception/mercury-decide, openrouter/inception/mercury-decide:free, openrouter/jaredpalmer/kev-4b, openrouter/liquid/d1, openrouter/microsoft/microsoft-decision-1, openrouter/nace-ai/drex-v1.5, openrouter/nace-ai/drex-v2.0, openrouter/openai/gpt-6-luna-decisions, openrouter/perplexity/pplx-decider-v1.1-27b, openrouter/respan/span-01, openrouter/respan/span-01-lite, openrouter/respan/span-01-lite:free, openrouter/scaledown/classify-1, openrouter/togethercomputer/tev1-4b-experimental, openrouter/typesafe/jev-1.13, openrouter/typesafe/jev-1.14, openrouter/upstage/solar-decide, openrouter/upstage/solar-decide-flash, openrouter/~perplexity/pplx-decider-flash-latest, openrouter/baseten/elephant-1:free, openrouter/baseten/mammoth-1:free, openrouter/liquid/d1-ultra, openrouter/nace-ai/drex-max, openrouter/perplexity/pplx-decider-flash-v1.2, openrouter/perplexity/pplx-decider-v1.2, openrouter/respan/span-02
bench judgment-call-evidence: skipped: moving alias (3): openrouter/~perplexity/pplx-decider-latest, openrouter/~typesafe/jev-latest, openrouter/~perplexity/pplx-decider-flash-latest
bench judgment-call-evidence: skipped: yes/no only openrouter/respan/span-01: a tiny choice question refused, a tiny bool question answered (probability 0.9637); provider: System One API error (400): {"error":{"message":"Respan only accepts noul questions whose instructions and criteria are plain strings (question \"q\")","code":400}}
bench judgment-call-evidence: skipped: yes/no only openrouter/respan/span-01-lite: a tiny choice question refused, a tiny bool question answered (probability 0.9637); provider: System One API error (400): {"error":{"message":"Respan only accepts noul questions whose instructions and criteria are plain strings (question \"q\")","code":400}}
bench judgment-call-evidence: skipped: yes/no only openrouter/respan/span-01-lite:free: a tiny choice question refused, a tiny bool question answered (probability 0.9637); provider: System One API error (400): {"error":{"message":"Respan only accepts noul questions whose instructions and criteria are plain strings (question \"q\")","code":400}}
TRAIN (21 cases; the best and the kit model's threshold are made here):
  model                                             answered  correct  accuracy  brier   ece     cost_usd   errors
  openrouter/nace-ai/drex-max                        21/21         16     0.762  0.379   0.232    0.000904  0
  openrouter/perplexity/pplx-decider-v1.2            21/21         15     0.714  0.298   0.190    0.000299  0
  openrouter/upstage/solar-decide                    21/21         15     0.714  0.450   0.207    0.001165  0
  openrouter/liquid/d1-ultra                         21/21         14     0.667  0.426   0.100    0.000560  0
  openrouter/openai/gpt-6-luna-decisions             21/21         14     0.667  0.458   0.131    0.001551  0
  openrouter/microsoft/microsoft-decision-1          21/21         14     0.667  0.586   0.301    0.000558  0
  openrouter/perplexity/pplx-decider-flash-v1.2      21/21         14     0.667  0.614   0.301    0.000150  0
  openrouter/typesafe/jev-1.13                       21/21         13     0.619  0.615   0.280    0.000945  0
  openrouter/typesafe/jev-1.14                       21/21         13     0.619  0.630   0.213    0.000945  0
  openrouter/nace-ai/drex-v2.0                       21/21         13     0.619  0.693   0.403    0.000773  0
  openrouter/inception/mercury-decide                21/21         13     0.619  0.772   0.401    0.000281  0
  openrouter/cloudflare/clef-omni                    21/21         12     0.571  0.495   0.095    0.002425  0
  openrouter/togethercomputer/tev1-4b-experimental   21/21         12     0.571  0.498   0.131    0.000637  0
  openrouter/jaredpalmer/kev-4b                      21/21         12     0.571  0.515   0.158    0.000541  0
  openrouter/baseten/mammoth-1:free                  21/21         12     0.571  0.594   0.314    0.000000  0
  openrouter/inception/mercury-decide:free           21/21         12     0.571  0.777   0.391    0.000000  0
  openrouter/respan/span-02                          21/21         11     0.524  0.770   0.368    0.000158  0
  openrouter/cloudflare/clef                         21/21         10     0.476  0.653   0.329    0.003931  0
  openrouter/liquid/d1                               21/21         10     0.476  0.739   0.386    0.000267  0
  openrouter/baseten/elephant-1:free                 21/21         10     0.476  0.821   0.426    0.000000  0
  openrouter/scaledown/classify-1                    21/21          9     0.429  0.643   0.270    0.000903  0
  openrouter/cloudflare/clef-flash                   21/21          8     0.381  0.618   0.289    0.000311  0
  openrouter/nace-ai/drex-v1.5                       21/21          8     0.381  1.050   0.517    0.000515  0
  openrouter/upstage/solar-decide-flash              21/21          7     0.333  0.736   0.409    0.001165  0
HELD-OUT (12 cases; the measure, never used to pick):
  model                                             answered  correct  accuracy  brier   ece     cost_usd   errors
  openrouter/nace-ai/drex-max                        12/12         11     0.917  0.234   0.141    0.000904  0
  openrouter/perplexity/pplx-decider-v1.2            12/12         10     0.833  0.249   0.093    0.000299  0
  openrouter/upstage/solar-decide                    12/12          7     0.583  0.624   0.334    0.001165  0
  openrouter/liquid/d1-ultra                         12/12          8     0.667  0.429   0.236    0.000560  0
  openrouter/openai/gpt-6-luna-decisions             12/12         11     0.917  0.271   0.239    0.001551  0
  openrouter/microsoft/microsoft-decision-1          12/12         10     0.833  0.411   0.276    0.000558  0
  openrouter/perplexity/pplx-decider-flash-v1.2      12/12          8     0.667  0.592   0.308    0.000150  0
  openrouter/typesafe/jev-1.13                       12/12          9     0.750  0.436   0.173    0.000945  0
  openrouter/typesafe/jev-1.14                       12/12          9     0.750  0.477   0.221    0.000945  0
  openrouter/nace-ai/drex-v2.0                       12/12          8     0.667  0.542   0.256    0.000773  0
  openrouter/inception/mercury-decide                12/12          9     0.750  0.499   0.259    0.000281  0
  openrouter/cloudflare/clef-omni                    12/12          9     0.750  0.356   0.211    0.002425  0
  openrouter/togethercomputer/tev1-4b-experimental   12/12          7     0.583  0.614   0.187    0.000637  0
  openrouter/jaredpalmer/kev-4b                      12/12          6     0.500  0.511   0.098    0.000541  0
  openrouter/baseten/mammoth-1:free                  12/12          6     0.500  0.507   0.372    0.000000  0
  openrouter/inception/mercury-decide:free           12/12          9     0.750  0.502   0.260    0.000000  0
  openrouter/respan/span-02                          12/12          6     0.500  0.684   0.408    0.000158  0
  openrouter/cloudflare/clef                         12/12          7     0.583  0.599   0.262    0.003931  0
  openrouter/liquid/d1                               12/12          6     0.500  0.511   0.323    0.000267  0
  openrouter/baseten/elephant-1:free                 12/12          7     0.583  0.619   0.369    0.000000  0
  openrouter/scaledown/classify-1                    12/12          7     0.583  0.499   0.211    0.000903  0
  openrouter/cloudflare/clef-flash                   12/12          7     0.583  0.430   0.245    0.000311  0
  openrouter/nace-ai/drex-v1.5                       12/12          3     0.250  0.961   0.557    0.000515  0
  openrouter/upstage/solar-decide-flash              12/12          3     0.250  0.727   0.453    0.001165  0
  (cost_usd and errors: the model's every call, train and held-out; brier: mean multi-class Brier score, lower is better; ece: expected calibration error over top-probability buckets [0.0, 0.5), [0.5, 0.6), [0.6, 0.7), [0.7, 0.8), [0.8, 0.9), [0.9, 1.0])
unavailable openai/gpt-6-luna: listed but answered no case: OpenAI Decisions error (404): OpenAI Decisions returned 404
unavailable openrouter/perplexity/pplx-decider-v1.1-27b: listed but answered no case: System One API error (404): {"error":{"message":"No endpoints found for perplexity/pplx-decider-v1.1-27b.","code":404},"user_id":"user_2j6vR9TdNFKYEGgN6TJb9xZd5EJ"}
KIT MODEL BESIDE THE BEST (best: highest train accuracy over every train case answered; ties: lower train Brier, lower train cost, name; held-out apart, never used to pick):
        model                                             train acc  train brier  held-out acc  held-out brier  cost_usd
  kit   openrouter/typesafe/jev-1.13                          0.619        0.615         0.750           0.436  0.000945
  best  openrouter/nace-ai/drex-max                           0.762        0.379         0.917           0.234  0.000904
kit model openrouter/typesafe/jev-1.13 (judgment-model.json): proposed threshold (for the director to accept; until met, the judge stays advisory): held-out accuracy >= 0.409 and held-out brier <= 0.918 (from train only: accuracy_min the Wilson 1.96 lower bound of train accuracy, brier_max train Brier mean + 1.96 standard errors)
held-out now: accuracy 0.750 (9/12 of 12), brier 0.436, ece 0.173: meets the proposed threshold
kit model calibration train (top probability bucket: n, mean top probability, accuracy): [0.5, 0.6) n 2 p 0.580 acc 1.000; [0.6, 0.7) n 2 p 0.665 acc 0.500; [0.7, 0.8) n 4 p 0.750 acc 0.500; [0.8, 0.9) n 6 p 0.850 acc 0.667; [0.9, 1.0] n 7 p 0.946 acc 0.571
kit model calibration held-out (top probability bucket: n, mean top probability, accuracy): [0.6, 0.7) n 3 p 0.647 acc 0.667; [0.7, 0.8) n 2 p 0.720 acc 1.000; [0.8, 0.9) n 2 p 0.850 acc 0.500; [0.9, 1.0] n 5 p 0.952 acc 0.800
DONE bench judgment-call-evidence: kit model openrouter/typesafe/jev-1.13, best openrouter/nace-ai/drex-max [232.9 s]
qa: 1/1 bench(es) done (run 20261025T144846Z-9643eb); artifacts /home/exedev/.local/state/octo-feather/qa/20261025T144846Z-9643eb
```
