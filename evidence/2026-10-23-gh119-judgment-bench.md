# gh119 judgment bench: question (a) test quality, every available classifier (tickets #135, #148)

Spec: docs/specs/judgment.spec.html, #acceptance-judge-labelled, #acceptance-judge-bench, #rule-held-out, #boundary-bench.
Suite: evals/judgment-test-quality/ (kind judgment, director-owned) at kit 20c64c8: 27 cases, 18 factory history (excluding the 4 constructed and the 5 tdd-skill examples). Answers below are model judgments: advisory, no gate reads them; `just check` never calls a model.

## Set change (#135, kit 20c64c8)

5 director-accepted historical cases added (`/tmp/gh119/labels-a-history/DIRECTOR-LABELS.json`, director 2026-10-23); each reference entry has label, one-line reason, source and `labelled_by: director`; existing 22 cases unchanged. Split by the rule fixed before the rerun (per label, source order: existing cases in their order, then new ones by source commit time; 0-based i with i%3==1 held-out):

| id | label | i | split | source commit |
|---|---|---|---|---|
| a-tracker-prose-load-pi-role-trackers | implementation-coupled | 7 | held-out | 19b818e (2026-10-23T00:23Z) |
| a-tracker-linear-fake-keyed-on-issueview | implementation-coupled | 8 | train | fd899ad (2026-10-23T03:58Z) |
| a-qa-stub-regex-bench-script | implementation-coupled | 9 | train | 091d096 (2026-10-23T22:26Z) |
| a-new-repo-want-from-ls-files | ok | 8 | train | 62a6302 (2026-10-19T20:00Z) |
| a-lane-tickets-snapshot-via-fake-github | ok | 9 | train | 2215bbf (2026-10-21T21:28Z) |

a-new-repo-want-from-ls-files: proposed tautological, relabelled ok by the director (recorded as `relabel` in its reference entry). Totals: tautological 7 (train 6, held-out 1), implementation-coupled 10 (train 7, held-out 3), ok 10 (train 7, held-out 3); train 20, held-out 7.

## Harness (#148)

`scripts/octo-feather-qa --suite judgment-test-quality`. No agent: the bench is a Pi extension command (`extension.js` in the run dir) run as
`pi --no-session --no-skills --no-mcp --no-context-files --no-prompt-templates --no-extensions --no-tools -e <bench-extension.js> -p "/octo-feather-bench <input>"`
inside the qa sandbox (`octo-feather-qc-sandbox`, history none; proof lines in the full output: live Herdr unreachable, no creds; cleanup line: agents started 0). The command calls `ctx.modelRegistry.getAvailableOfType("classifier")` and `ctx.modelRegistry.classify(...)` directly, 4 at once; no chat model turn, so no launcher (docs/adr/0016 covers agents). Each case's state goes as its state string (general rule, no provider names). Choice and threshold from train only; ties on train Brier, then train cost (`train_cost_usd`), then name.

Load rule: one live run at a time; smoke and full run sequential, each one headless pi.

## Smoke first: 3 new cases x jev-1.13 (run 20261024T001405Z-fb6f71)

```
$ scripts/octo-feather-qa --suite judgment-test-quality --case a-tracker-prose-load-pi-role-trackers --case a-tracker-linear-fake-keyed-on-issueview --case a-new-repo-want-from-ls-files --classifier openrouter/typesafe/jev-1.13
evals: ok (4 suites, 170 cases)
qa: run 20261024T001405Z-fb6f71: 3 case(s); kit 20c64c8657013b7885366e6ec5c8fdcc876f261f; artifacts /home/exedev/.local/state/octo-feather/qa/20261024T001405Z-fb6f71
qc sandbox: ok   /tmp is private (nothing the judge writes there outlives the run)
qc sandbox: ok   judge holds no capabilities (CapEff 0000000000000000), no_new_privs 1, uid 1000
qc sandbox: ok   masks locked: umount of the Herdr mask exits 32, after its own unshare -rm 32
qc sandbox: ok   HOME, /var/tmp, the kit read-only
qc sandbox: ok   worktree /tmp/qa-fb6f71-bench-5ddd2w6i is an overlay, upper dir on the run tmpfs and hidden from the judge
qc sandbox: ok   writable persistent paths: none
qc sandbox: ok   vendored-skill cache /home/exedev/.cache/octo-feather/skillfile bound read-only (not writable, not in the writable list)
qc sandbox: ok   live Herdr unreachable: raw herdr --session default workspace list exits 1
qc sandbox: ok   herdr shim pins sandbox session qa-fb6f71-bench despite --session default --remote --machine
qc sandbox: ok   Herdr config shows only the sandbox session: [qa-fb6f71-bench]
qc sandbox: ok   no gh or git creds: tokens 0, gh config entries 0, git-credentials 0 bytes, gh auth status exits 1
qc sandbox: ok   no tracker credential: LINEAR_API_KEY set 0 times
qc sandbox: ok   parent route unset: 0 of OCTO_FEATHER_PARENT/SESSION_ID/ROLE, HERDR_PANE/TAB/WORKSPACE_ID, HERDR_ENV set
qc sandbox: ok   state dir is per-run scratch: /tmp/.qc-qa-fb6f71-bench/state/octo-feather/sessions/qa-fb6f71-bench
qc sandbox: ok   history none (0 bound: no archived lanes, no director log; a factory eval sees no lane history); live records masked (6 paths, 0 bytes or entries visible)
qc sandbox: ok   github: none (factory eval: no GitHub evidence); the offline gh refuses every call (exit 1)
qc sandbox: ok   worktree clean at 392520b311d3
qc sandbox: cleanup: agents started 0 (headless pi 0, Herdr panes 0); leftover processes killed 1, left 0 (the kernel kills those as PID 1 exits); session qa-fb6f71-bench stopped and deleted; offline gh refusals 0
bench judgment-test-quality: question a-test-quality, labels tautological, implementation-coupled, ok; 3 cases (train 2, held-out 1); every answer is a model judgment (classifier output, advisory: no gate reads it)
bench judgment-test-quality: classifiers available (32): openai/gpt-6-luna, openrouter/~perplexity/pplx-decider-latest, openrouter/~typesafe/jev-latest, openrouter/cloudflare/clef, openrouter/cloudflare/clef-flash, openrouter/cloudflare/clef-omni, openrouter/inception/mercury-decide, openrouter/inception/mercury-decide:free, openrouter/jaredpalmer/kev-4b, openrouter/liquid/d1, openrouter/microsoft/microsoft-decision-1, openrouter/nace-ai/drex-v1.5, openrouter/nace-ai/drex-v2.0, openrouter/openai/gpt-6-luna-decisions, openrouter/perplexity/pplx-decider-v1.1-27b, openrouter/respan/span-01, openrouter/respan/span-01-lite, openrouter/respan/span-01-lite:free, openrouter/scaledown/classify-1, openrouter/togethercomputer/tev1-4b-experimental, openrouter/typesafe/jev-1.13, openrouter/typesafe/jev-1.14, openrouter/upstage/solar-decide, openrouter/upstage/solar-decide-flash, openrouter/~perplexity/pplx-decider-flash-latest, openrouter/baseten/elephant-1:free, openrouter/baseten/mammoth-1:free, openrouter/liquid/d1-ultra, openrouter/nace-ai/drex-max, openrouter/perplexity/pplx-decider-flash-v1.2, openrouter/perplexity/pplx-decider-v1.2, openrouter/respan/span-02
bench judgment-test-quality: benched only --classifier openrouter/typesafe/jev-1.13
TRAIN (2 cases; the choice and threshold are made here):
  model                         answered  correct  accuracy  brier   ece     cost_usd   errors
  openrouter/typesafe/jev-1.13    2/2           0     0.000  1.187   0.715    0.000148  0
HELD-OUT (1 cases; the measure, never used to choose):
  model                         answered  correct  accuracy  brier   ece     cost_usd   errors
  openrouter/typesafe/jev-1.13    1/1           1     1.000  0.267   0.370    0.000148  0
  (cost_usd and errors: the model's every call, train and held-out; brier: mean multi-class Brier score, lower is better; ece: expected calibration error over top-probability buckets [0.0, 0.5), [0.5, 0.6), [0.6, 0.7), [0.7, 0.8), [0.8, 0.9), [0.9, 1.0])
chosen openrouter/typesafe/jev-1.13 (from train only: highest train accuracy over every train case answered; ties: lower train Brier, lower train cost, name): train accuracy 0.000, brier 1.187, ece 0.715
proposed threshold (for the director to accept; until met, the judge stays advisory): held-out accuracy >= 0.0 and held-out brier <= 2.403 (from train only: accuracy_min the Wilson 1.96 lower bound of train accuracy, brier_max train Brier mean + 1.96 standard errors)
held-out now: accuracy 1.000 (1/1 of 1), brier 0.267, ece 0.370: meets the proposed threshold
chosen calibration train (top probability bucket: n, mean top probability, accuracy): [0.5, 0.6) n 1 p 0.500 acc 0.000; [0.9, 1.0] n 1 p 0.930 acc 0.000
chosen calibration held-out (top probability bucket: n, mean top probability, accuracy): [0.6, 0.7) n 1 p 0.630 acc 1.000
DONE bench judgment-test-quality: chosen openrouter/typesafe/jev-1.13 [2.2 s]
qa: 1/1 bench(es) done (run 20261024T001405Z-fb6f71); artifacts /home/exedev/.local/state/octo-feather/qa/20261024T001405Z-fb6f71
```

Pipeline real: 3 classify results with cost from usage; the hidden reference (labelled_by, relabel, reason) absent from input.json, extension.js and stdout.txt (grep count 0). jev-1.13 answers: tracker-prose implementation-coupled (right), tracker-linear ok (wrong), new-repo tautological (wrong).

## Demo: full bench (run 20261024T001416Z-aa46f7, 110.1 s, kit 20c64c8)

Artifacts: $(octo-feather-state)/qa/20261024T001416Z-aa46f7/judgment-test-quality/ (input.json, extension.js, stdout.txt, stderr.txt, sandbox.json, answers.json, bench.json, report.txt) and summary.json. Full output:

```
$ scripts/octo-feather-qa --suite judgment-test-quality
evals: ok (4 suites, 170 cases)
qa: run 20261024T001416Z-aa46f7: 27 case(s); kit 20c64c8657013b7885366e6ec5c8fdcc876f261f; artifacts /home/exedev/.local/state/octo-feather/qa/20261024T001416Z-aa46f7
qc sandbox: ok   /tmp is private (nothing the judge writes there outlives the run)
qc sandbox: ok   judge holds no capabilities (CapEff 0000000000000000), no_new_privs 1, uid 1000
qc sandbox: ok   masks locked: umount of the Herdr mask exits 32, after its own unshare -rm 32
qc sandbox: ok   HOME, /var/tmp, the kit read-only
qc sandbox: ok   worktree /tmp/qa-aa46f7-bench-0wpxq6yy is an overlay, upper dir on the run tmpfs and hidden from the judge
qc sandbox: ok   writable persistent paths: none
qc sandbox: ok   vendored-skill cache /home/exedev/.cache/octo-feather/skillfile bound read-only (not writable, not in the writable list)
qc sandbox: ok   live Herdr unreachable: raw herdr --session default workspace list exits 1
qc sandbox: ok   herdr shim pins sandbox session qa-aa46f7-bench despite --session default --remote --machine
qc sandbox: ok   Herdr config shows only the sandbox session: [qa-aa46f7-bench]
qc sandbox: ok   no gh or git creds: tokens 0, gh config entries 0, git-credentials 0 bytes, gh auth status exits 1
qc sandbox: ok   no tracker credential: LINEAR_API_KEY set 0 times
qc sandbox: ok   parent route unset: 0 of OCTO_FEATHER_PARENT/SESSION_ID/ROLE, HERDR_PANE/TAB/WORKSPACE_ID, HERDR_ENV set
qc sandbox: ok   state dir is per-run scratch: /tmp/.qc-qa-aa46f7-bench/state/octo-feather/sessions/qa-aa46f7-bench
qc sandbox: ok   history none (0 bound: no archived lanes, no director log; a factory eval sees no lane history); live records masked (6 paths, 0 bytes or entries visible)
qc sandbox: ok   github: none (factory eval: no GitHub evidence); the offline gh refuses every call (exit 1)
qc sandbox: ok   worktree clean at 5737f8d21113
qc sandbox: cleanup: agents started 0 (headless pi 0, Herdr panes 0); leftover processes killed 0, left 0 (the kernel kills those as PID 1 exits); session qa-aa46f7-bench stopped and deleted; offline gh refusals 0
bench judgment-test-quality: question a-test-quality, labels tautological, implementation-coupled, ok; 27 cases (train 20, held-out 7); every answer is a model judgment (classifier output, advisory: no gate reads it)
bench judgment-test-quality: classifiers available (32): openai/gpt-6-luna, openrouter/~perplexity/pplx-decider-latest, openrouter/~typesafe/jev-latest, openrouter/cloudflare/clef, openrouter/cloudflare/clef-flash, openrouter/cloudflare/clef-omni, openrouter/inception/mercury-decide, openrouter/inception/mercury-decide:free, openrouter/jaredpalmer/kev-4b, openrouter/liquid/d1, openrouter/microsoft/microsoft-decision-1, openrouter/nace-ai/drex-v1.5, openrouter/nace-ai/drex-v2.0, openrouter/openai/gpt-6-luna-decisions, openrouter/perplexity/pplx-decider-v1.1-27b, openrouter/respan/span-01, openrouter/respan/span-01-lite, openrouter/respan/span-01-lite:free, openrouter/scaledown/classify-1, openrouter/togethercomputer/tev1-4b-experimental, openrouter/typesafe/jev-1.13, openrouter/typesafe/jev-1.14, openrouter/upstage/solar-decide, openrouter/upstage/solar-decide-flash, openrouter/~perplexity/pplx-decider-flash-latest, openrouter/baseten/elephant-1:free, openrouter/baseten/mammoth-1:free, openrouter/liquid/d1-ultra, openrouter/nace-ai/drex-max, openrouter/perplexity/pplx-decider-flash-v1.2, openrouter/perplexity/pplx-decider-v1.2, openrouter/respan/span-02
bench judgment-test-quality: skipped: moving alias (3): openrouter/~perplexity/pplx-decider-latest, openrouter/~typesafe/jev-latest, openrouter/~perplexity/pplx-decider-flash-latest
TRAIN (20 cases; the choice and threshold are made here):
  model                                             answered  correct  accuracy  brier   ece     cost_usd   errors
  openrouter/respan/span-02                          20/20         18     0.900  0.199   0.127    0.000216  0
  openrouter/typesafe/jev-1.13                       20/20         18     0.900  0.232   0.173    0.001074  0
  openrouter/baseten/mammoth-1:free                  20/20         16     0.800  0.250   0.100    0.000000  0
  openrouter/typesafe/jev-1.14                       20/20         16     0.800  0.271   0.176    0.001074  0
  openrouter/liquid/d1-ultra                         20/20         16     0.800  0.344   0.185    0.000756  0
  openrouter/baseten/elephant-1:free                 20/20         15     0.750  0.317   0.218    0.000000  0
  openrouter/cloudflare/clef-omni                    20/20         15     0.750  0.341   0.176    0.003012  0
  openrouter/nace-ai/drex-max                        20/20         15     0.750  0.356   0.214    0.001164  0
  openrouter/perplexity/pplx-decider-v1.2            20/20         15     0.750  0.389   0.145    0.000386  0
  openrouter/inception/mercury-decide:free           20/20         15     0.750  0.423   0.213    0.000000  0
  openrouter/liquid/d1                               20/20         15     0.750  0.432   0.223    0.000360  0
  openrouter/inception/mercury-decide                20/20         15     0.750  0.473   0.229    0.000388  0
  openrouter/openai/gpt-6-luna-decisions             20/20         14     0.700  0.350   0.179    0.001945  0
  openrouter/perplexity/pplx-decider-flash-v1.2      20/20         14     0.700  0.369   0.195    0.000193  0
  openrouter/microsoft/microsoft-decision-1          20/20         14     0.700  0.422   0.179    0.000779  0
  openrouter/upstage/solar-decide                    20/20         14     0.700  0.596   0.290    0.001356  0
  openrouter/cloudflare/clef                         20/20         13     0.650  0.426   0.286    0.004974  0
  openrouter/nace-ai/drex-v1.5                       20/20         13     0.650  0.448   0.229    0.000704  0
  openrouter/nace-ai/drex-v2.0                       20/20         13     0.650  0.469   0.201    0.001056  0
  openrouter/togethercomputer/tev1-4b-experimental   20/20         13     0.650  0.478   0.196    0.000855  0
  openrouter/cloudflare/clef-flash                   20/20         12     0.600  0.503   0.218    0.000788  0
  openrouter/jaredpalmer/kev-4b                      20/20         12     0.600  0.543   0.197    0.000739  0
  openrouter/scaledown/classify-1                    20/20          9     0.450  0.581   0.195    0.001055  0
  openrouter/upstage/solar-decide-flash              20/20          9     0.450  0.691   0.249    0.001356  0
HELD-OUT (7 cases; the measure, never used to choose):
  model                                             answered  correct  accuracy  brier   ece     cost_usd   errors
  openrouter/respan/span-02                           7/7           7     1.000  0.107   0.190    0.000216  0
  openrouter/typesafe/jev-1.13                        7/7           7     1.000  0.135   0.212    0.001074  0
  openrouter/baseten/mammoth-1:free                   7/7           7     1.000  0.047   0.117    0.000000  0
  openrouter/typesafe/jev-1.14                        7/7           7     1.000  0.129   0.207    0.001074  0
  openrouter/liquid/d1-ultra                          7/7           7     1.000  0.179   0.231    0.000756  0
  openrouter/baseten/elephant-1:free                  7/7           6     0.857  0.213   0.139    0.000000  0
  openrouter/cloudflare/clef-omni                     7/7           7     1.000  0.137   0.278    0.003012  0
  openrouter/nace-ai/drex-max                         7/7           7     1.000  0.006   0.042    0.001164  0
  openrouter/perplexity/pplx-decider-v1.2             7/7           7     1.000  0.023   0.096    0.000386  0
  openrouter/inception/mercury-decide:free            7/7           6     0.857  0.153   0.107    0.000000  0
  openrouter/liquid/d1                                7/7           5     0.714  0.414   0.170    0.000360  0
  openrouter/inception/mercury-decide                 7/7           6     0.857  0.153   0.107    0.000388  0
  openrouter/openai/gpt-6-luna-decisions              7/7           7     1.000  0.066   0.144    0.001945  0
  openrouter/perplexity/pplx-decider-flash-v1.2       7/7           6     0.857  0.322   0.197    0.000193  0
  openrouter/microsoft/microsoft-decision-1           7/7           5     0.714  0.552   0.410    0.000779  0
  openrouter/upstage/solar-decide                     7/7           7     1.000  0.031   0.059    0.001356  0
  openrouter/cloudflare/clef                          7/7           7     1.000  0.060   0.158    0.004974  0
  openrouter/nace-ai/drex-v1.5                        7/7           4     0.571  0.648   0.384    0.000704  0
  openrouter/nace-ai/drex-v2.0                        7/7           4     0.571  0.430   0.251    0.001056  0
  openrouter/togethercomputer/tev1-4b-experimental    7/7           5     0.714  0.421   0.238    0.000855  0
  openrouter/cloudflare/clef-flash                    7/7           7     1.000  0.157   0.296    0.000788  0
  openrouter/jaredpalmer/kev-4b                       7/7           4     0.571  0.551   0.302    0.000739  0
  openrouter/scaledown/classify-1                     7/7           7     1.000  0.360   0.470    0.001055  0
  openrouter/upstage/solar-decide-flash               7/7           2     0.286  0.544   0.308    0.001356  0
  (cost_usd and errors: the model's every call, train and held-out; brier: mean multi-class Brier score, lower is better; ece: expected calibration error over top-probability buckets [0.0, 0.5), [0.5, 0.6), [0.6, 0.7), [0.7, 0.8), [0.8, 0.9), [0.9, 1.0])
unavailable openai/gpt-6-luna: listed but answered no case: OpenAI Decisions error (404): OpenAI Decisions returned 404
unavailable openrouter/perplexity/pplx-decider-v1.1-27b: listed but answered no case: System One API error (404): {"error":{"message":"No endpoints found for perplexity/pplx-decider-v1.1-27b.","code":404},"user_id":"user_2j6vR9TdNFKYEGgN6TJb9xZd5EJ"}
unavailable openrouter/respan/span-01: listed but answered no case: System One API error (400): {"error":{"message":"Respan only accepts noul questions whose instructions and criteria are plain strings (question \"q\")","code":400}}
unavailable openrouter/respan/span-01-lite: listed but answered no case: System One API error (400): {"error":{"message":"Respan only accepts noul questions whose instructions and criteria are plain strings (question \"q\")","code":400}}
unavailable openrouter/respan/span-01-lite:free: listed but answered no case: System One API error (400): {"error":{"message":"Respan only accepts noul questions whose instructions and criteria are plain strings (question \"q\")","code":400}}
chosen openrouter/respan/span-02 (from train only: highest train accuracy over every train case answered; ties: lower train Brier, lower train cost, name): train accuracy 0.900, brier 0.199, ece 0.127
proposed threshold (for the director to accept; until met, the judge stays advisory): held-out accuracy >= 0.699 and held-out brier <= 0.39 (from train only: accuracy_min the Wilson 1.96 lower bound of train accuracy, brier_max train Brier mean + 1.96 standard errors)
held-out now: accuracy 1.000 (7/7 of 7), brier 0.107, ece 0.190: meets the proposed threshold
chosen calibration train (top probability bucket: n, mean top probability, accuracy): [0.6, 0.7) n 6 p 0.640 acc 0.833; [0.7, 0.8) n 1 p 0.746 acc 1.000; [0.8, 0.9) n 4 p 0.864 acc 1.000; [0.9, 1.0] n 9 p 0.953 acc 0.889
chosen calibration held-out (top probability bucket: n, mean top probability, accuracy): [0.5, 0.6) n 1 p 0.572 acc 1.000; [0.6, 0.7) n 1 p 0.643 acc 1.000; [0.7, 0.8) n 1 p 0.784 acc 1.000; [0.8, 0.9) n 1 p 0.850 acc 1.000; [0.9, 1.0] n 3 p 0.940 acc 1.000
DONE bench judgment-test-quality: chosen openrouter/respan/span-02 [110.1 s]
qa: 1/1 bench(es) done (run 20261024T001416Z-aa46f7); artifacts /home/exedev/.local/state/octo-feather/qa/20261024T001416Z-aa46f7
```

## Cost (owner ruling: per-model cost_usd and the run total; no spend ledger)

From this run's bench.json `models[].cost_usd` (every call, train and held-out) and `train_cost_usd` (the tie-break). Run total (bench.json `cost_usd`): $0.024231. Skipped moving aliases make no call and carry no cost: openrouter/~perplexity/pplx-decider-latest, openrouter/~typesafe/jev-latest, openrouter/~perplexity/pplx-decider-flash-latest.

| model | cost_usd | train_cost_usd |
|---|---|---|
| openai/gpt-6-luna | 0.000000 | 0.000000 |
| openrouter/cloudflare/clef | 0.004974 | 0.003874 |
| openrouter/cloudflare/clef-flash | 0.000788 | 0.000613 |
| openrouter/cloudflare/clef-omni | 0.003012 | 0.002343 |
| openrouter/inception/mercury-decide | 0.000388 | 0.000304 |
| openrouter/inception/mercury-decide:free | 0.000000 | 0.000000 |
| openrouter/jaredpalmer/kev-4b | 0.000739 | 0.000581 |
| openrouter/liquid/d1 | 0.000360 | 0.000283 |
| openrouter/microsoft/microsoft-decision-1 | 0.000779 | 0.000614 |
| openrouter/nace-ai/drex-v1.5 | 0.000704 | 0.000553 |
| openrouter/nace-ai/drex-v2.0 | 0.001056 | 0.000829 |
| openrouter/openai/gpt-6-luna-decisions | 0.001945 | 0.001515 |
| openrouter/perplexity/pplx-decider-v1.1-27b | 0.000000 | 0.000000 |
| openrouter/respan/span-01 | 0.000000 | 0.000000 |
| openrouter/respan/span-01-lite | 0.000000 | 0.000000 |
| openrouter/respan/span-01-lite:free | 0.000000 | 0.000000 |
| openrouter/scaledown/classify-1 | 0.001055 | 0.000813 |
| openrouter/togethercomputer/tev1-4b-experimental | 0.000855 | 0.000670 |
| openrouter/typesafe/jev-1.13 | 0.001074 | 0.000828 |
| openrouter/typesafe/jev-1.14 | 0.001074 | 0.000828 |
| openrouter/upstage/solar-decide | 0.001356 | 0.001049 |
| openrouter/upstage/solar-decide-flash | 0.001356 | 0.001049 |
| openrouter/baseten/elephant-1:free | 0.000000 | 0.000000 |
| openrouter/baseten/mammoth-1:free | 0.000000 | 0.000000 |
| openrouter/liquid/d1-ultra | 0.000756 | 0.000594 |
| openrouter/nace-ai/drex-max | 0.001164 | 0.000910 |
| openrouter/perplexity/pplx-decider-flash-v1.2 | 0.000193 | 0.000151 |
| openrouter/perplexity/pplx-decider-v1.2 | 0.000386 | 0.000302 |
| openrouter/respan/span-02 | 0.000216 | 0.000170 |

## Reading

- 32 listed; 3 moving aliases skipped (never called): openrouter/~perplexity/pplx-decider-latest, openrouter/~typesafe/jev-latest, openrouter/~perplexity/pplx-decider-flash-latest; 29 benched; 24 scored; 5 unavailable: gpt-6-luna direct 404, pplx-decider-v1.1-27b 404 no endpoint (provider reasons); Respan span-01, span-01-lite, span-01-lite:free 400: they accept only bool (noul) questions and the bench asks one 3-label choice question, a provider capability, not our state shape.
- Chosen from train only: openrouter/respan/span-02 (train 18/20, Brier 0.199), tied on train accuracy with jev-1.13 (18/20, Brier 0.232), broken on lower train Brier. Proposed threshold: held-out accuracy >= 0.699 and Brier <= 0.39. Held-out now 7/7, Brier 0.107: meets.
- New cases are harder than the old set (right answers out of 24 scored models): tracker-prose 20, lane-tickets-snapshot 22, new-repo 8, qa-stub-regex 4, tracker-linear 0. tracker-linear's coupling sits in the fake, not the assertion (literal JSON), so every model says ok; span-02 misses it and new-repo is right.

## Rebench for the kit's one judgment model (run 20261025T144513Z-79e9f1, 2026-10-25)

Owner ruling 2026-10-25 (spec judgment#rule-one-model): one judgment model for every question, openrouter/typesafe/jev-1.13,
recorded in evals/judgment-model.json (evidence/2026-10-25-gh119-judgment-model.md). This rerun refreshes this suite's
`calibration` (the kit model's held-out score and proposed threshold, accepted false); the bench shows the kit's model
beside the question's best-scoring classifier and no longer names a per-question choice. The Respan span-01 models are
now "skipped: yes/no only" by the probe (a tiny choice question refused, a tiny bool question answered), no longer unavailable.

`scripts/octo-feather-qa --suite judgment-test-quality` (sandbox proof lines omitted; artifacts $(octo-feather-state)/qa/20261025T144513Z-79e9f1/):

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
