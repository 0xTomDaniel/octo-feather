# gh119 judgment bench: question (a) test quality, every available classifier (ticket #135)

Spec: docs/specs/judgment.spec.html @ e67a151, #acceptance (labelled set; bench), #modular-boundaries, #rules.
Suite: evals/judgment-test-quality/ (kind judgment), copied as is from the director's final set /tmp/gh119/labels/a-test-quality/ (`diff -r` empty; suite.json added). Answers below are model judgments: advisory, no gate reads them; `just check` never calls a model.

Harness: `scripts/octo-feather-qa --suite judgment-test-quality` (what `just qa --suite judgment-test-quality` runs). One relay pi (`pi --no-session --no-skills --no-mcp --no-context-files --no-prompt-templates --tools read,codemode --mode json -p`) inside the qa sandbox (`octo-feather-qc-sandbox`, history none; proof lines below show live Herdr unreachable, no creds). It is told to run one fixed codemode script unchanged; the grader keeps only the codemode call whose input equals that script. All classify calls batched in that one script (at most 4 at once, per Pi). Box load rule (director): one live pi per run, `pgrep -fc "(^|/)pi( |$)"` was 7 when checked; both runs below were one headless pi each, never in parallel.

## Smoke first: 3 cases x 2 models (run 20261023T221402Z-25c076)

```
$ scripts/octo-feather-qa --suite judgment-test-quality --case a-tdd-add-restates-sum --case a-tdd-checkout-mock-payment --case a-tdd-total-literal --classifier openrouter/typesafe/jev-1.14 --classifier openrouter/cloudflare/clef
...
TRAIN (2 cases; the choice and threshold are made here):
  openrouter/typesafe/jev-1.14    2/2           2     1.000  0.011   0.080    0.000070  0
  openrouter/cloudflare/clef      2/2           2     1.000  0.027   0.118    0.000264  0
HELD-OUT (1 cases; the measure, never used to choose):
  openrouter/typesafe/jev-1.14    1/1           1     1.000  0.001   0.020    0.000070  0
  openrouter/cloudflare/clef      1/1           1     1.000  0.003   0.046    0.000264  0
DONE bench judgment-test-quality: chosen openrouter/typesafe/jev-1.14 [22.6 s]
```

Real classify results (probabilities, usage cost) from both models; then the full bench.

## Demo: full bench (run 20261023T221439Z-c19f69, 119.7 s, total classifier cost $0.0196)

Artifacts: $(octo-feather-state)/qa/20261023T221439Z-c19f69/judgment-test-quality/ (input.json, script.js, prompt.md, transcript.jsonl, stderr.txt, sandbox.json, answers.json, bench.json, report.txt) and summary.json. Full output:

```
$ scripts/octo-feather-qa --suite judgment-test-quality
evals: ok (4 suites, 165 cases)
qa: run 20261023T221439Z-c19f69: 22 case(s); kit 9760e73cd50abb0d87410732359e360d50d929a4; artifacts /home/exedev/.local/state/octo-feather/qa/20261023T221439Z-c19f69
qc sandbox: ok   /tmp is private (nothing the judge writes there outlives the run)
qc sandbox: ok   judge holds no capabilities (CapEff 0000000000000000), no_new_privs 1, uid 1000
qc sandbox: ok   masks locked: umount of the Herdr mask exits 32, after its own unshare -rm 32
qc sandbox: ok   HOME, /var/tmp, the kit read-only
qc sandbox: ok   worktree /tmp/qa-c19f69-bench-hkduluj5 is an overlay, upper dir on the run tmpfs and hidden from the judge
qc sandbox: ok   writable persistent paths: none
qc sandbox: ok   vendored-skill cache /home/exedev/.cache/octo-feather/skillfile bound read-only (not writable, not in the writable list)
qc sandbox: ok   live Herdr unreachable: raw herdr --session default workspace list exits 1
qc sandbox: ok   herdr shim pins sandbox session qa-c19f69-bench despite --session default --remote --machine
qc sandbox: ok   Herdr config shows only the sandbox session: [qa-c19f69-bench]
qc sandbox: ok   no gh or git creds: tokens 0, gh config entries 0, git-credentials 0 bytes, gh auth status exits 1
qc sandbox: ok   no tracker credential: LINEAR_API_KEY set 0 times
qc sandbox: ok   parent route unset: 0 of OCTO_FEATHER_PARENT/SESSION_ID/ROLE, HERDR_PANE/TAB/WORKSPACE_ID, HERDR_ENV set
qc sandbox: ok   state dir is per-run scratch: /tmp/.qc-qa-c19f69-bench/state/octo-feather/sessions/qa-c19f69-bench
qc sandbox: ok   history none (0 bound: no archived lanes, no director log; a factory eval sees no lane history); live records masked (6 paths, 0 bytes or entries visible)
qc sandbox: ok   github: none (factory eval: no GitHub evidence); the offline gh refuses every call (exit 1)
qc sandbox: ok   worktree clean at eaca90d94bca
qc sandbox: cleanup: agents started 0 (headless pi 0, Herdr panes 0); leftover processes killed 0, left 0 (the kernel kills those as PID 1 exits); session qa-c19f69-bench stopped and deleted; offline gh refusals 0
bench judgment-test-quality: question a-test-quality, labels tautological, implementation-coupled, ok; 22 cases (train 16, held-out 6); every answer is a model judgment (classifier output, advisory: no gate reads it)
bench judgment-test-quality: classifiers available (32): openai/gpt-6-luna, openrouter/~perplexity/pplx-decider-latest, openrouter/~typesafe/jev-latest, openrouter/cloudflare/clef, openrouter/cloudflare/clef-flash, openrouter/cloudflare/clef-omni, openrouter/inception/mercury-decide, openrouter/inception/mercury-decide:free, openrouter/jaredpalmer/kev-4b, openrouter/liquid/d1, openrouter/microsoft/microsoft-decision-1, openrouter/nace-ai/drex-v1.5, openrouter/nace-ai/drex-v2.0, openrouter/openai/gpt-6-luna-decisions, openrouter/perplexity/pplx-decider-v1.1-27b, openrouter/respan/span-01, openrouter/respan/span-01-lite, openrouter/respan/span-01-lite:free, openrouter/scaledown/classify-1, openrouter/togethercomputer/tev1-4b-experimental, openrouter/typesafe/jev-1.13, openrouter/typesafe/jev-1.14, openrouter/upstage/solar-decide, openrouter/upstage/solar-decide-flash, openrouter/~perplexity/pplx-decider-flash-latest, openrouter/baseten/elephant-1:free, openrouter/baseten/mammoth-1:free, openrouter/liquid/d1-ultra, openrouter/nace-ai/drex-max, openrouter/perplexity/pplx-decider-flash-v1.2, openrouter/perplexity/pplx-decider-v1.2, openrouter/respan/span-02
TRAIN (16 cases; the choice and threshold are made here):
  model                                             answered  correct  accuracy  brier   ece     cost_usd   errors
  openrouter/typesafe/jev-1.13                       16/16         16     1.000  0.088   0.168    0.000811  0
  openrouter/baseten/mammoth-1:free                  16/16         15     0.938  0.066   0.054    0.000000  0
  openrouter/typesafe/jev-1.14                       16/16         15     0.938  0.116   0.129    0.000811  0
  openrouter/~typesafe/jev-latest                    16/16         15     0.938  0.119   0.187    0.000811  0
  openrouter/liquid/d1-ultra                         16/16         15     0.938  0.123   0.171    0.000594  0
  openrouter/respan/span-02                          16/16         15     0.938  0.145   0.142    0.000158  0
  openrouter/inception/mercury-decide                16/16         14     0.875  0.162   0.095    0.000283  0
  openrouter/inception/mercury-decide:free           16/16         14     0.875  0.162   0.096    0.000000  0
  openrouter/baseten/elephant-1:free                 16/16         14     0.875  0.226   0.133    0.000000  0
  openrouter/nace-ai/drex-max                        16/16         13     0.812  0.213   0.134    0.000881  0
  openrouter/openai/gpt-6-luna-decisions             16/16         13     0.812  0.214   0.123    0.001520  0
  openrouter/~perplexity/pplx-decider-latest         16/16         13     0.812  0.279   0.078    0.000292  0
  openrouter/perplexity/pplx-decider-v1.2            16/16         13     0.812  0.280   0.076    0.000292  0
  openrouter/perplexity/pplx-decider-flash-v1.2      16/16         13     0.812  0.281   0.248    0.000146  0
  openrouter/~perplexity/pplx-decider-flash-latest   16/16         13     0.812  0.281   0.248    0.000146  0
  openrouter/cloudflare/clef                         16/16         13     0.812  0.284   0.172    0.003779  0
  openrouter/microsoft/microsoft-decision-1          16/16         13     0.812  0.287   0.045    0.000563  0
  openrouter/cloudflare/clef-omni                    16/16         13     0.812  0.312   0.184    0.002352  0
  openrouter/liquid/d1                               16/16         13     0.812  0.327   0.201    0.000283  0
  openrouter/togethercomputer/tev1-4b-experimental   16/16         13     0.812  0.336   0.202    0.000625  0
  openrouter/upstage/solar-decide                    16/16         13     0.812  0.338   0.156    0.001015  0
  openrouter/nace-ai/drex-v2.0                       16/16         12     0.750  0.346   0.202    0.000762  0
  openrouter/nace-ai/drex-v1.5                       16/16         12     0.750  0.357   0.114    0.000508  0
  openrouter/cloudflare/clef-flash                   16/16         12     0.750  0.401   0.174    0.000598  0
  openrouter/jaredpalmer/kev-4b                      16/16         11     0.688  0.465   0.184    0.000534  0
  openrouter/upstage/solar-decide-flash              16/16          9     0.562  0.555   0.145    0.001015  0
  openrouter/scaledown/classify-1                    16/16          8     0.500  0.569   0.193    0.000792  0
HELD-OUT (6 cases; the measure, never used to choose):
  model                                             answered  correct  accuracy  brier   ece     cost_usd   errors
  openrouter/typesafe/jev-1.13                        6/6           6     1.000  0.136   0.208    0.000811  0
  openrouter/baseten/mammoth-1:free                   6/6           6     1.000  0.046   0.117    0.000000  0
  openrouter/typesafe/jev-1.14                        6/6           6     1.000  0.127   0.198    0.000811  0
  openrouter/~typesafe/jev-latest                     6/6           6     1.000  0.105   0.183    0.000811  0
  openrouter/liquid/d1-ultra                          6/6           5     0.833  0.182   0.156    0.000594  0
  openrouter/respan/span-02                           6/6           4     0.667  0.333   0.284    0.000158  0
  openrouter/inception/mercury-decide                 6/6           5     0.833  0.285   0.151    0.000283  0
  openrouter/inception/mercury-decide:free            6/6           5     0.833  0.242   0.145    0.000000  0
  openrouter/baseten/elephant-1:free                  6/6           5     0.833  0.283   0.187    0.000000  0
  openrouter/nace-ai/drex-max                         6/6           6     1.000  0.001   0.018    0.000881  0
  openrouter/openai/gpt-6-luna-decisions              6/6           6     1.000  0.037   0.102    0.001520  0
  openrouter/~perplexity/pplx-decider-latest          6/6           6     1.000  0.018   0.085    0.000292  0
  openrouter/perplexity/pplx-decider-v1.2             6/6           6     1.000  0.019   0.086    0.000292  0
  openrouter/perplexity/pplx-decider-flash-v1.2       6/6           5     0.833  0.322   0.138    0.000146  0
  openrouter/~perplexity/pplx-decider-flash-latest    6/6           5     0.833  0.322   0.138    0.000146  0
  openrouter/cloudflare/clef                          6/6           6     1.000  0.073   0.154    0.003779  0
  openrouter/microsoft/microsoft-decision-1           6/6           5     0.833  0.284   0.231    0.000563  0
  openrouter/cloudflare/clef-omni                     6/6           5     0.833  0.181   0.282    0.002352  0
  openrouter/liquid/d1                                6/6           4     0.667  0.552   0.369    0.000283  0
  openrouter/togethercomputer/tev1-4b-experimental    6/6           4     0.667  0.354   0.374    0.000625  0
  openrouter/upstage/solar-decide                     6/6           5     0.833  0.169   0.139    0.001015  0
  openrouter/nace-ai/drex-v2.0                        6/6           4     0.667  0.329   0.168    0.000762  0
  openrouter/nace-ai/drex-v1.5                        6/6           4     0.667  0.623   0.374    0.000508  0
  openrouter/cloudflare/clef-flash                    6/6           6     1.000  0.149   0.270    0.000598  0
  openrouter/jaredpalmer/kev-4b                       6/6           4     0.667  0.486   0.220    0.000534  0
  openrouter/upstage/solar-decide-flash               6/6           1     0.167  0.619   0.452    0.001015  0
  openrouter/scaledown/classify-1                     6/6           6     1.000  0.324   0.446    0.000792  0
  (cost_usd and errors: the model's every call, train and held-out; brier: mean multi-class Brier score, lower is better; ece: expected calibration error over top-probability buckets [0.0, 0.5), [0.5, 0.6), [0.6, 0.7), [0.7, 0.8), [0.8, 0.9), [0.9, 1.0])
unavailable openai/gpt-6-luna: listed but answered no case: OpenAI Decisions error (404): OpenAI Decisions returned 404
unavailable openrouter/perplexity/pplx-decider-v1.1-27b: listed but answered no case: System One API error (404): {"error":{"message":"No endpoints found for perplexity/pplx-decider-v1.1-27b.","code":404},"user_id":"user_2j6vR9TdNFKYEGgN6TJb9xZd5EJ"}
unavailable openrouter/respan/span-01: listed but answered no case: System One API error (400): {"error":{"message":"Respan state must be a string or an object with only input (a message array) and output (a message), where each message has a string content and a role of system, user, assistant or tool, and the output role is assistant","code":400}}
unavailable openrouter/respan/span-01-lite: listed but answered no case: System One API error (400): {"error":{"message":"Respan state must be a string or an object with only input (a message array) and output (a message), where each message has a string content and a role of system, user, assistant or tool, and the output role is assistant","code":400}}
unavailable openrouter/respan/span-01-lite:free: listed but answered no case: System One API error (400): {"error":{"message":"Respan state must be a string or an object with only input (a message array) and output (a message), where each message has a string content and a role of system, user, assistant or tool, and the output role is assistant","code":400}}
chosen openrouter/typesafe/jev-1.13 (from train only: highest train accuracy over every train case answered; ties: lower train Brier, lower cost, name): train accuracy 1.000, brier 0.088, ece 0.168
proposed threshold (for the director to accept; until met, the judge stays advisory): held-out accuracy >= 0.806 and held-out brier <= 0.14 (from train only: accuracy_min the Wilson 1.96 lower bound of train accuracy, brier_max train Brier mean + 1.96 standard errors)
held-out now: accuracy 1.000 (6/6 of 6), brier 0.136, ece 0.208: meets the proposed threshold
chosen calibration train (top probability bucket: n, mean top probability, accuracy): [0.6, 0.7) n 4 p 0.620 acc 1.000; [0.7, 0.8) n 2 p 0.745 acc 1.000; [0.8, 0.9) n 4 p 0.867 acc 1.000; [0.9, 1.0] n 6 p 0.978 acc 1.000
chosen calibration held-out (top probability bucket: n, mean top probability, accuracy): [0.5, 0.6) n 1 p 0.530 acc 1.000; [0.6, 0.7) n 1 p 0.630 acc 1.000; [0.7, 0.8) n 1 p 0.720 acc 1.000; [0.9, 1.0] n 3 p 0.957 acc 1.000
DONE bench judgment-test-quality: chosen openrouter/typesafe/jev-1.13 [119.7 s]
qa: 1/1 bench(es) done (run 20261023T221439Z-c19f69); artifacts /home/exedev/.local/state/octo-feather/qa/20261023T221439Z-c19f69
```

## Reading

- 32 classifiers listed by getAvailableOfType; 27 answered all 22 cases; 5 listed but unavailable, each with its error (gpt-6-luna direct 404; pplx-decider-v1.1-27b no endpoint; three respan span-01 models reject the `{text}` state shape).
- Chosen from train only: openrouter/typesafe/jev-1.13 (train 16/16). Proposed threshold for the director: held-out accuracy >= 0.806 and held-out Brier <= 0.14. Held-out now 6/6, Brier 0.136: meets, by a thin margin on Brier; 6 held-out cases make every held-out number coarse.
- Choice rule and threshold rule are fixed in scripts/octo-feather-qa (`--help`), applied mechanically; held-out never enters either.
