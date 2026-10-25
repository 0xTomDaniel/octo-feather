# gh119 judgment bench: question (c) ticket slice, every available classifier (ticket #154)

Spec: docs/specs/judgment.spec.html, #acceptance-judge-labelled, #acceptance-judge-bench, #rules.
Suite: evals/judgment-ticket-slice/ (kind judgment, director-owned): 22 cases, real factory history: 16 filed GitHub tickets and 6 qc judge ticket drafts from the gh40 lane (c-draft-*), logged in $(octo-feather-state)/qc/*.json and the gh40 hand-off log but never filed, counted as real logged history; none constructed. Answers below are model judgments: advisory, no gate reads them; `just check` never calls a model.

## Set (copied as is)

From /tmp/gh119/labels/c-ticket-slice (final, director-checked and owned 2026-10-23). question.json and cases.json byte-identical; every reference entry keeps its label, reason and source and adds `labelled_by: director`; the set's REPORT names no relabel (its rulings add #86 and #87 and keep #72, #9, #110), so no `relabel`. REPORT.md generated from cases.json and expectations.json, counts demo pasted. Totals: slice 13 (train 8, held-out 5), layer-only 9 (train 6, held-out 3); train 14, held-out 8.

c-42-gate-retired-words quotes the retired words its ticket bans; check-refs skips judgment label data by the owner ruling of 2026-10-25 (commit 779dd94), so the set needed no edit.

Scripted diff against the /tmp set (`/tmp/gh119/work-bcd/build.py diff c .`, compares question, cases and expectations with labelled_by and relabel dropped):

```
judgment-ticket-slice: data equal to /tmp/gh119/labels/c-ticket-slice (question, cases, expectations ignoring added labelled_by, relabel); 22 cases, labelled_by director 22, relabel []; files ['REPORT.md', 'cases.json', 'question.json', 'reference/expectations.json', 'suite.json']
```

## Harness

Same as the pilot (evidence/2026-10-23-gh119-judgment-bench.md, Harness): `scripts/octo-feather-qa --suite judgment-ticket-slice`, one Pi extension command in the qa sandbox, no agent, no chat model turn; choice and threshold from train only. Load rule: one live run at a time; smoke then full run, sequential. Both runs at kit 9abb28d (the suite on ae5ca60); the commit holding this file has the same evals/ tree.

## Smoke first (run 20261025T020611Z-ce5858)

```
$ scripts/octo-feather-qa --suite judgment-ticket-slice --case c-3-pi-role-approve --case c-10-contracts-text --case c-86-reviewer-quality-only --classifier openrouter/typesafe/jev-1.13
evals: ok (8 suites, 272 cases)
qa: run 20261025T020611Z-ce5858: 3 case(s); kit 9abb28d25b4af88adcd93cdc4cd7855e4708804f; artifacts /home/exedev/.local/state/octo-feather/qa/20261025T020611Z-ce5858
qc sandbox: ok   /tmp is private (nothing the judge writes there outlives the run)
qc sandbox: ok   judge holds no capabilities (CapEff 0000000000000000), no_new_privs 1, uid 1000
qc sandbox: ok   masks locked: umount of the Herdr mask exits 32, after its own unshare -rm 32
qc sandbox: ok   HOME, /var/tmp, the kit read-only
qc sandbox: ok   worktree /tmp/qa-ce5858-bench-5fi4iey7 is an overlay, upper dir on the run tmpfs and hidden from the judge
qc sandbox: ok   writable persistent paths: none
qc sandbox: ok   vendored-skill cache /home/exedev/.cache/octo-feather/skillfile bound read-only (not writable, not in the writable list)
qc sandbox: ok   live Herdr unreachable: raw herdr --session default workspace list exits 1
qc sandbox: ok   herdr shim pins sandbox session qa-ce5858-bench despite --session default --remote --machine
qc sandbox: ok   Herdr config shows only the sandbox session: [qa-ce5858-bench]
qc sandbox: ok   no gh or git creds: tokens 0, gh config entries 0, git-credentials 0 bytes, gh auth status exits 1
qc sandbox: ok   no tracker credential: LINEAR_API_KEY set 0 times
qc sandbox: ok   parent route unset: 0 of OCTO_FEATHER_PARENT/SESSION_ID/ROLE, HERDR_PANE/TAB/WORKSPACE_ID, HERDR_ENV set
qc sandbox: ok   state dir is per-run scratch: /tmp/.qc-qa-ce5858-bench/state/octo-feather/sessions/qa-ce5858-bench
qc sandbox: ok   history none (0 bound: no archived lanes, no director log; a factory eval sees no lane history); live records masked (6 paths, 0 bytes or entries visible)
qc sandbox: ok   github: none (factory eval: no GitHub evidence); the offline gh refuses every call (exit 1)
qc sandbox: ok   worktree clean at 2a8919b50695
qc sandbox: cleanup: agents started 0 (headless pi 0, Herdr panes 0); leftover processes killed 1, left 0 (the kernel kills those as PID 1 exits); session qa-ce5858-bench stopped and deleted; offline gh refusals 0
bench judgment-ticket-slice: question c-ticket-slice, labels slice, layer-only; 3 cases (train 2, held-out 1); every answer is a model judgment (classifier output, advisory: no gate reads it)
bench judgment-ticket-slice: classifiers available (32): openai/gpt-6-luna, openrouter/~perplexity/pplx-decider-latest, openrouter/~typesafe/jev-latest, openrouter/cloudflare/clef, openrouter/cloudflare/clef-flash, openrouter/cloudflare/clef-omni, openrouter/inception/mercury-decide, openrouter/inception/mercury-decide:free, openrouter/jaredpalmer/kev-4b, openrouter/liquid/d1, openrouter/microsoft/microsoft-decision-1, openrouter/nace-ai/drex-v1.5, openrouter/nace-ai/drex-v2.0, openrouter/openai/gpt-6-luna-decisions, openrouter/perplexity/pplx-decider-v1.1-27b, openrouter/respan/span-01, openrouter/respan/span-01-lite, openrouter/respan/span-01-lite:free, openrouter/scaledown/classify-1, openrouter/togethercomputer/tev1-4b-experimental, openrouter/typesafe/jev-1.13, openrouter/typesafe/jev-1.14, openrouter/upstage/solar-decide, openrouter/upstage/solar-decide-flash, openrouter/~perplexity/pplx-decider-flash-latest, openrouter/baseten/elephant-1:free, openrouter/baseten/mammoth-1:free, openrouter/liquid/d1-ultra, openrouter/nace-ai/drex-max, openrouter/perplexity/pplx-decider-flash-v1.2, openrouter/perplexity/pplx-decider-v1.2, openrouter/respan/span-02
bench judgment-ticket-slice: benched only --classifier openrouter/typesafe/jev-1.13
TRAIN (2 cases; the choice and threshold are made here):
  model                         answered  correct  accuracy  brier   ece     cost_usd   errors
  openrouter/typesafe/jev-1.13    2/2           2     1.000  0.003   0.030    0.000108  0
HELD-OUT (1 cases; the measure, never used to choose):
  model                         answered  correct  accuracy  brier   ece     cost_usd   errors
  openrouter/typesafe/jev-1.13    1/1           1     1.000  0.001   0.020    0.000108  0
  (cost_usd and errors: the model's every call, train and held-out; brier: mean multi-class Brier score, lower is better; ece: expected calibration error over top-probability buckets [0.0, 0.5), [0.5, 0.6), [0.6, 0.7), [0.7, 0.8), [0.8, 0.9), [0.9, 1.0])
chosen openrouter/typesafe/jev-1.13 (from train only: highest train accuracy over every train case answered; ties: lower train Brier, lower train cost, name): train accuracy 1.000, brier 0.003, ece 0.030
proposed threshold (for the director to accept; until met, the judge stays advisory): held-out accuracy >= 0.342 and held-out brier <= 0.007 (from train only: accuracy_min the Wilson 1.96 lower bound of train accuracy, brier_max train Brier mean + 1.96 standard errors)
held-out now: accuracy 1.000 (1/1 of 1), brier 0.001, ece 0.020: meets the proposed threshold
chosen calibration train (top probability bucket: n, mean top probability, accuracy): [0.9, 1.0] n 2 p 0.970 acc 1.000
chosen calibration held-out (top probability bucket: n, mean top probability, accuracy): [0.9, 1.0] n 1 p 0.980 acc 1.000
DONE bench judgment-ticket-slice: chosen openrouter/typesafe/jev-1.13 [2.3 s]
qa: 1/1 bench(es) done (run 20261025T020611Z-ce5858); artifacts /home/exedev/.local/state/octo-feather/qa/20261025T020611Z-ce5858
```

Pipeline real: 3 classify results with cost from usage; the hidden reference (labelled_by, reason) absent from input.json, extension.js and stdout.txt (grep count 0). jev-1.13 answers: c-3-pi-role-approve slice (right, p 0.99), c-10-contracts-text layer-only (right, p 0.95), c-86-reviewer-quality-only slice (right, p 0.98).

## Demo: full bench (run 20261025T020619Z-f2d2ec, 83.5 s, kit 9abb28d)

Artifacts: $(octo-feather-state)/qa/20261025T020619Z-f2d2ec/judgment-ticket-slice/ (input.json, extension.js, stdout.txt, stderr.txt, sandbox.json, answers.json, bench.json, report.txt) and summary.json. Full output:

```
$ scripts/octo-feather-qa --suite judgment-ticket-slice
evals: ok (8 suites, 272 cases)
qa: run 20261025T020619Z-f2d2ec: 22 case(s); kit 9abb28d25b4af88adcd93cdc4cd7855e4708804f; artifacts /home/exedev/.local/state/octo-feather/qa/20261025T020619Z-f2d2ec
qc sandbox: ok   /tmp is private (nothing the judge writes there outlives the run)
qc sandbox: ok   judge holds no capabilities (CapEff 0000000000000000), no_new_privs 1, uid 1000
qc sandbox: ok   masks locked: umount of the Herdr mask exits 32, after its own unshare -rm 32
qc sandbox: ok   HOME, /var/tmp, the kit read-only
qc sandbox: ok   worktree /tmp/qa-f2d2ec-bench-5a5kro3m is an overlay, upper dir on the run tmpfs and hidden from the judge
qc sandbox: ok   writable persistent paths: none
qc sandbox: ok   vendored-skill cache /home/exedev/.cache/octo-feather/skillfile bound read-only (not writable, not in the writable list)
qc sandbox: ok   live Herdr unreachable: raw herdr --session default workspace list exits 1
qc sandbox: ok   herdr shim pins sandbox session qa-f2d2ec-bench despite --session default --remote --machine
qc sandbox: ok   Herdr config shows only the sandbox session: [qa-f2d2ec-bench]
qc sandbox: ok   no gh or git creds: tokens 0, gh config entries 0, git-credentials 0 bytes, gh auth status exits 1
qc sandbox: ok   no tracker credential: LINEAR_API_KEY set 0 times
qc sandbox: ok   parent route unset: 0 of OCTO_FEATHER_PARENT/SESSION_ID/ROLE, HERDR_PANE/TAB/WORKSPACE_ID, HERDR_ENV set
qc sandbox: ok   state dir is per-run scratch: /tmp/.qc-qa-f2d2ec-bench/state/octo-feather/sessions/qa-f2d2ec-bench
qc sandbox: ok   history none (0 bound: no archived lanes, no director log; a factory eval sees no lane history); live records masked (6 paths, 0 bytes or entries visible)
qc sandbox: ok   github: none (factory eval: no GitHub evidence); the offline gh refuses every call (exit 1)
qc sandbox: ok   worktree clean at 1285278be650
qc sandbox: cleanup: agents started 0 (headless pi 0, Herdr panes 0); leftover processes killed 0, left 0 (the kernel kills those as PID 1 exits); session qa-f2d2ec-bench stopped and deleted; offline gh refusals 0
bench judgment-ticket-slice: question c-ticket-slice, labels slice, layer-only; 22 cases (train 14, held-out 8); every answer is a model judgment (classifier output, advisory: no gate reads it)
bench judgment-ticket-slice: classifiers available (32): openai/gpt-6-luna, openrouter/~perplexity/pplx-decider-latest, openrouter/~typesafe/jev-latest, openrouter/cloudflare/clef, openrouter/cloudflare/clef-flash, openrouter/cloudflare/clef-omni, openrouter/inception/mercury-decide, openrouter/inception/mercury-decide:free, openrouter/jaredpalmer/kev-4b, openrouter/liquid/d1, openrouter/microsoft/microsoft-decision-1, openrouter/nace-ai/drex-v1.5, openrouter/nace-ai/drex-v2.0, openrouter/openai/gpt-6-luna-decisions, openrouter/perplexity/pplx-decider-v1.1-27b, openrouter/respan/span-01, openrouter/respan/span-01-lite, openrouter/respan/span-01-lite:free, openrouter/scaledown/classify-1, openrouter/togethercomputer/tev1-4b-experimental, openrouter/typesafe/jev-1.13, openrouter/typesafe/jev-1.14, openrouter/upstage/solar-decide, openrouter/upstage/solar-decide-flash, openrouter/~perplexity/pplx-decider-flash-latest, openrouter/baseten/elephant-1:free, openrouter/baseten/mammoth-1:free, openrouter/liquid/d1-ultra, openrouter/nace-ai/drex-max, openrouter/perplexity/pplx-decider-flash-v1.2, openrouter/perplexity/pplx-decider-v1.2, openrouter/respan/span-02
bench judgment-ticket-slice: skipped: moving alias (3): openrouter/~perplexity/pplx-decider-latest, openrouter/~typesafe/jev-latest, openrouter/~perplexity/pplx-decider-flash-latest
TRAIN (14 cases; the choice and threshold are made here):
  model                                             answered  correct  accuracy  brier   ece     cost_usd   errors
  openrouter/inception/mercury-decide                14/14         14     1.000  0.002   0.016    0.000238  0
  openrouter/inception/mercury-decide:free           14/14         14     1.000  0.003   0.020    0.000000  0
  openrouter/baseten/elephant-1:free                 13/14         13     1.000  0.068   0.123    0.000000  1
  openrouter/upstage/solar-decide                    14/14         13     0.929  0.068   0.112    0.000908  0
  openrouter/nace-ai/drex-max                        14/14         13     0.929  0.110   0.094    0.000752  0
  openrouter/openai/gpt-6-luna-decisions             14/14         13     0.929  0.152   0.136    0.001290  0
  openrouter/microsoft/microsoft-decision-1          14/14         13     0.929  0.157   0.088    0.000483  0
  openrouter/typesafe/jev-1.14                       14/14         12     0.857  0.090   0.099    0.000742  0
  openrouter/typesafe/jev-1.13                       14/14         12     0.857  0.107   0.111    0.000742  0
  openrouter/cloudflare/clef                         14/14         12     0.857  0.123   0.170    0.003215  0
  openrouter/perplexity/pplx-decider-v1.2            14/14         12     0.857  0.124   0.120    0.000249  0
  openrouter/perplexity/pplx-decider-flash-v1.2      14/14         12     0.857  0.185   0.131    0.000125  0
  openrouter/cloudflare/clef-omni                    14/14         12     0.857  0.194   0.196    0.001990  0
  openrouter/scaledown/classify-1                    14/14         12     0.857  0.200   0.135    0.000717  0
  openrouter/upstage/solar-decide-flash              14/14         12     0.857  0.218   0.169    0.000908  0
  openrouter/liquid/d1-ultra                         14/14         12     0.857  0.220   0.139    0.000491  0
  openrouter/respan/span-02                          14/14         12     0.857  0.228   0.129    0.000137  0
  openrouter/togethercomputer/tev1-4b-experimental   14/14         12     0.857  0.233   0.122    0.000537  0
  openrouter/cloudflare/clef-flash                   14/14         12     0.857  0.254   0.108    0.000254  0
  openrouter/jaredpalmer/kev-4b                      14/14         11     0.786  0.267   0.164    0.000466  0
  openrouter/liquid/d1                               14/14         11     0.786  0.279   0.165    0.000234  0
  openrouter/nace-ai/drex-v2.0                       14/14         11     0.786  0.299   0.165    0.000665  0
  openrouter/nace-ai/drex-v1.5                       14/14         11     0.786  0.381   0.192    0.000443  0
  openrouter/baseten/mammoth-1:free                   9/14          6     0.667  0.355   0.260    0.000000  8
HELD-OUT (8 cases; the measure, never used to choose):
  model                                             answered  correct  accuracy  brier   ece     cost_usd   errors
  openrouter/inception/mercury-decide                 8/8           8     1.000  0.000   0.001    0.000238  0
  openrouter/inception/mercury-decide:free            8/8           8     1.000  0.000   0.001    0.000000  0
  openrouter/baseten/elephant-1:free                  8/8           8     1.000  0.009   0.051    0.000000  1
  openrouter/upstage/solar-decide                     8/8           8     1.000  0.016   0.072    0.000908  0
  openrouter/nace-ai/drex-max                         8/8           8     1.000  0.000   0.003    0.000752  0
  openrouter/openai/gpt-6-luna-decisions              8/8           8     1.000  0.008   0.048    0.001290  0
  openrouter/microsoft/microsoft-decision-1           8/8           8     1.000  0.000   0.003    0.000483  0
  openrouter/typesafe/jev-1.14                        8/8           8     1.000  0.002   0.022    0.000742  0
  openrouter/typesafe/jev-1.13                        8/8           8     1.000  0.004   0.029    0.000742  0
  openrouter/cloudflare/clef                          8/8           8     1.000  0.026   0.085    0.003215  0
  openrouter/perplexity/pplx-decider-v1.2             8/8           8     1.000  0.000   0.012    0.000249  0
  openrouter/perplexity/pplx-decider-flash-v1.2       8/8           8     1.000  0.018   0.076    0.000125  0
  openrouter/cloudflare/clef-omni                     8/8           7     0.875  0.193   0.256    0.001990  0
  openrouter/scaledown/classify-1                     8/8           7     0.875  0.139   0.188    0.000717  0
  openrouter/upstage/solar-decide-flash               8/8           8     1.000  0.135   0.212    0.000908  0
  openrouter/liquid/d1-ultra                          8/8           8     1.000  0.001   0.025    0.000491  0
  openrouter/respan/span-02                           8/8           8     1.000  0.005   0.045    0.000137  0
  openrouter/togethercomputer/tev1-4b-experimental    8/8           8     1.000  0.052   0.141    0.000537  0
  openrouter/cloudflare/clef-flash                    8/8           8     1.000  0.088   0.179    0.000254  0
  openrouter/jaredpalmer/kev-4b                       8/8           8     1.000  0.146   0.252    0.000466  0
  openrouter/liquid/d1                                8/8           8     1.000  0.000   0.003    0.000234  0
  openrouter/nace-ai/drex-v2.0                        8/8           8     1.000  0.001   0.012    0.000665  0
  openrouter/nace-ai/drex-v1.5                        8/8           8     1.000  0.001   0.016    0.000443  0
  openrouter/baseten/mammoth-1:free                   5/8           5     1.000  0.006   0.050    0.000000  8
  (cost_usd and errors: the model's every call, train and held-out; brier: mean multi-class Brier score, lower is better; ece: expected calibration error over top-probability buckets [0.0, 0.5), [0.5, 0.6), [0.6, 0.7), [0.7, 0.8), [0.8, 0.9), [0.9, 1.0])
unavailable openai/gpt-6-luna: listed but answered no case: OpenAI Decisions error (404): OpenAI Decisions returned 404
unavailable openrouter/perplexity/pplx-decider-v1.1-27b: listed but answered no case: System One API error (404): {"error":{"message":"No endpoints found for perplexity/pplx-decider-v1.1-27b.","code":404},"user_id":"user_2j6vR9TdNFKYEGgN6TJb9xZd5EJ"}
unavailable openrouter/respan/span-01: listed but answered no case: System One API error (400): {"error":{"message":"Respan only accepts noul questions whose instructions and criteria are plain strings (question \"q\")","code":400}}
unavailable openrouter/respan/span-01-lite: listed but answered no case: System One API error (400): {"error":{"message":"Respan only accepts noul questions whose instructions and criteria are plain strings (question \"q\")","code":400}}
unavailable openrouter/respan/span-01-lite:free: listed but answered no case: System One API error (400): {"error":{"message":"Respan only accepts noul questions whose instructions and criteria are plain strings (question \"q\")","code":400}}
errors openrouter/baseten/elephant-1:free: 1 case(s) unanswered, first: System One API error (429): {"error":{"message":"Rate limit exceeded: free-models-per-min. ","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"20","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1792894080000"},"limit_source":"openrouter_free_tier_per_minute","remedy_hint":"Slow down requests to free models, or retry after the per-minute window resets."}}}
errors openrouter/baseten/mammoth-1:free: 8 case(s) unanswered, first: System One API error (429): {"error":{"message":"Rate limit exceeded: free-models-per-min. ","code":429,"metadata":{"headers":{"X-RateLimit-Limit":"20","X-RateLimit-Remaining":"0","X-RateLimit-Reset":"1792894080000"},"limit_source":"openrouter_free_tier_per_minute","remedy_hint":"Slow down requests to free models, or retry after the per-minute window resets."}}}
chosen openrouter/inception/mercury-decide (from train only: highest train accuracy over every train case answered; ties: lower train Brier, lower train cost, name): train accuracy 1.000, brier 0.002, ece 0.016
proposed threshold (for the director to accept; until met, the judge stays advisory): held-out accuracy >= 0.785 and held-out brier <= 0.004 (from train only: accuracy_min the Wilson 1.96 lower bound of train accuracy, brier_max train Brier mean + 1.96 standard errors)
held-out now: accuracy 1.000 (8/8 of 8), brier 0.000, ece 0.001: meets the proposed threshold
chosen calibration train (top probability bucket: n, mean top probability, accuracy): [0.9, 1.0] n 14 p 0.984 acc 1.000
chosen calibration held-out (top probability bucket: n, mean top probability, accuracy): [0.9, 1.0] n 8 p 0.999 acc 1.000
DONE bench judgment-ticket-slice: chosen openrouter/inception/mercury-decide [83.5 s]
qa: 1/1 bench(es) done (run 20261025T020619Z-f2d2ec); artifacts /home/exedev/.local/state/octo-feather/qa/20261025T020619Z-f2d2ec
```

## Cost (per-model cost_usd and the run total; no spend ledger)

From this run's bench.json `models[].cost_usd` (every call, train and held-out) and `train_cost_usd` (the tie-break). Run total (bench.json `cost_usd`): $0.015587. Skipped moving aliases make no call and carry no cost: openrouter/~perplexity/pplx-decider-latest, openrouter/~typesafe/jev-latest, openrouter/~perplexity/pplx-decider-flash-latest.

| model | cost_usd | train_cost_usd |
|---|---|---|
| openai/gpt-6-luna | 0.000000 | 0.000000 |
| openrouter/cloudflare/clef | 0.003215 | 0.002085 |
| openrouter/cloudflare/clef-flash | 0.000254 | 0.000165 |
| openrouter/cloudflare/clef-omni | 0.001990 | 0.001290 |
| openrouter/inception/mercury-decide | 0.000238 | 0.000155 |
| openrouter/inception/mercury-decide:free | 0.000000 | 0.000000 |
| openrouter/jaredpalmer/kev-4b | 0.000466 | 0.000303 |
| openrouter/liquid/d1 | 0.000234 | 0.000152 |
| openrouter/microsoft/microsoft-decision-1 | 0.000483 | 0.000315 |
| openrouter/nace-ai/drex-v1.5 | 0.000443 | 0.000289 |
| openrouter/nace-ai/drex-v2.0 | 0.000665 | 0.000433 |
| openrouter/openai/gpt-6-luna-decisions | 0.001290 | 0.000836 |
| openrouter/perplexity/pplx-decider-v1.1-27b | 0.000000 | 0.000000 |
| openrouter/respan/span-01 | 0.000000 | 0.000000 |
| openrouter/respan/span-01-lite | 0.000000 | 0.000000 |
| openrouter/respan/span-01-lite:free | 0.000000 | 0.000000 |
| openrouter/scaledown/classify-1 | 0.000717 | 0.000463 |
| openrouter/togethercomputer/tev1-4b-experimental | 0.000537 | 0.000349 |
| openrouter/typesafe/jev-1.13 | 0.000742 | 0.000479 |
| openrouter/typesafe/jev-1.14 | 0.000742 | 0.000479 |
| openrouter/upstage/solar-decide | 0.000908 | 0.000586 |
| openrouter/upstage/solar-decide-flash | 0.000908 | 0.000586 |
| openrouter/baseten/elephant-1:free | 0.000000 | 0.000000 |
| openrouter/baseten/mammoth-1:free | 0.000000 | 0.000000 |
| openrouter/liquid/d1-ultra | 0.000491 | 0.000319 |
| openrouter/nace-ai/drex-max | 0.000752 | 0.000489 |
| openrouter/perplexity/pplx-decider-flash-v1.2 | 0.000125 | 0.000081 |
| openrouter/perplexity/pplx-decider-v1.2 | 0.000249 | 0.000162 |
| openrouter/respan/span-02 | 0.000137 | 0.000089 |

## Reading

- 32 listed; 3 moving aliases skipped (never called); 29 benched; 24 scored; 5 unavailable, same provider reasons as the pilot: gpt-6-luna direct 404, pplx-decider-v1.1-27b 404 no endpoint, Respan span-01, span-01-lite, span-01-lite:free 400 (bool-only questions; this is a 2-label choice question). Free-tier 429 rate limits: mammoth-1:free left 8 cases unanswered, elephant-1:free 1 (a train case, so it answered 13 of 14 train cases and could not be chosen).
- Chosen from train only: openrouter/inception/mercury-decide (train 14/14, Brier 0.002), tied on accuracy with mercury-decide:free (Brier 0.003), broken on lower train Brier. Proposed threshold: held-out accuracy >= 0.785 and Brier <= 0.004, near zero because train Brier is. Held-out now 8/8, Brier 0.000: meets.
- Easy set, and held-out is easier still: 22 of 24 scored models miss no held-out case they answered (mammoth-1:free answered 5 of 8); only clef-omni and classify-1 miss one. All 3 held-out layer-only cases are gh40 qc drafts (storage layer, deferred CLI, unrelated demo), which every model gets right; the 3 filed layer-only tickets (#10, #72, #87) are all train. So held-out does not test the hard filed layer-only case. The set's REPORT doubts already name the drafts as near-duplicates of one pattern.
- Hard cases are exactly those filed layer-only tickets (right answers out of the models that answered): c-72-checks-facts-text 5/23, c-87-prune-patches 11/24, c-10-contracts-text 13/24. Every other case gets at least 22. mercury-decide misses none.
