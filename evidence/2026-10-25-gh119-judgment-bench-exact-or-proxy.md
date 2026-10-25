# gh119 judgment bench: question (b) exact or proxy, every available classifier (ticket #153)

Spec: docs/specs/judgment.spec.html, #acceptance-judge-labelled, #acceptance-judge-bench, #rules.
Suite: evals/judgment-exact-or-proxy/ (kind judgment, director-owned): 31 cases, all real factory history (checks and graders the factory committed, each state led by the rule quoted where it is owned; none constructed). Answers below are model judgments: advisory, no gate reads them; `just check` never calls a model.

## Set (copied as is)

From /tmp/gh119/labels/b-exact-or-proxy (final, director-checked and owned 2026-10-23). question.json and cases.json byte-identical; every reference entry keeps its label, reason and source and adds `labelled_by: director`; the set REPORT's two final flips (ticket-what-to-build-names-demo, gh82-tracker-prose: exact to proxy, owner's "delete 1 2 and 3") carry a one-line `relabel`. Left out: the set's held/ (gh108-check-evals-leaks, pending #108) and DEFECTS.md. REPORT.md generated from cases.json and expectations.json, counts demo pasted. Totals: exact 16 (train 10, held-out 6), proxy 15 (train 10, held-out 5); train 20, held-out 11.

The label data quotes kit history verbatim, retired words and lane-branch strings included; check-refs skips judgment label data by the owner ruling of 2026-10-25 (commit 779dd94), so the set needed no edit.

Scripted diff against the /tmp set (`/tmp/gh119/work-bcd/build.py diff b .`, compares question, cases and expectations with labelled_by and relabel dropped):

```
judgment-exact-or-proxy: data equal to /tmp/gh119/labels/b-exact-or-proxy (question, cases, expectations ignoring added labelled_by, relabel); 31 cases, labelled_by director 31, relabel ['ticket-what-to-build-names-demo', 'gh82-tracker-prose']; files ['REPORT.md', 'cases.json', 'question.json', 'reference/expectations.json', 'suite.json']
```

## Harness

Same as the pilot (evidence/2026-10-23-gh119-judgment-bench.md, Harness): `scripts/octo-feather-qa --suite judgment-exact-or-proxy`, one Pi extension command in the qa sandbox, no agent, no chat model turn; choice and threshold from train only. Load rule: one live run at a time; smoke then full run, sequential. Both runs at kit b5ed8aa (the suite on 779dd94); the commit holding this file has the same evals/ tree.

## Smoke first (run 20261025T013839Z-e2b9b5)

```
$ scripts/octo-feather-qa --suite judgment-exact-or-proxy --case justfile-check-scripts --case check-refs-linear-word --case gh82-tracker-prose --classifier openrouter/typesafe/jev-1.13
evals: ok (7 suites, 250 cases)
qa: run 20261025T013839Z-e2b9b5: 3 case(s); kit b5ed8aa369d8f582e456e64dc00ffb0d3ab7e3d0; artifacts /home/exedev/.local/state/octo-feather/qa/20261025T013839Z-e2b9b5
qc sandbox: ok   /tmp is private (nothing the judge writes there outlives the run)
qc sandbox: ok   judge holds no capabilities (CapEff 0000000000000000), no_new_privs 1, uid 1000
qc sandbox: ok   masks locked: umount of the Herdr mask exits 32, after its own unshare -rm 32
qc sandbox: ok   HOME, /var/tmp, the kit read-only
qc sandbox: ok   worktree /tmp/qa-e2b9b5-bench-k14c4c79 is an overlay, upper dir on the run tmpfs and hidden from the judge
qc sandbox: ok   writable persistent paths: none
qc sandbox: ok   vendored-skill cache /home/exedev/.cache/octo-feather/skillfile bound read-only (not writable, not in the writable list)
qc sandbox: ok   live Herdr unreachable: raw herdr --session default workspace list exits 1
qc sandbox: ok   herdr shim pins sandbox session qa-e2b9b5-bench despite --session default --remote --machine
qc sandbox: ok   Herdr config shows only the sandbox session: [qa-e2b9b5-bench]
qc sandbox: ok   no gh or git creds: tokens 0, gh config entries 0, git-credentials 0 bytes, gh auth status exits 1
qc sandbox: ok   no tracker credential: LINEAR_API_KEY set 0 times
qc sandbox: ok   parent route unset: 0 of OCTO_FEATHER_PARENT/SESSION_ID/ROLE, HERDR_PANE/TAB/WORKSPACE_ID, HERDR_ENV set
qc sandbox: ok   state dir is per-run scratch: /tmp/.qc-qa-e2b9b5-bench/state/octo-feather/sessions/qa-e2b9b5-bench
qc sandbox: ok   history none (0 bound: no archived lanes, no director log; a factory eval sees no lane history); live records masked (6 paths, 0 bytes or entries visible)
qc sandbox: ok   github: none (factory eval: no GitHub evidence); the offline gh refuses every call (exit 1)
qc sandbox: ok   worktree clean at 6043f013cc0b
qc sandbox: cleanup: agents started 0 (headless pi 0, Herdr panes 0); leftover processes killed 0, left 0 (the kernel kills those as PID 1 exits); session qa-e2b9b5-bench stopped and deleted; offline gh refusals 0
bench judgment-exact-or-proxy: question b-exact-or-proxy, labels exact, proxy; 3 cases (train 2, held-out 1); every answer is a model judgment (classifier output, advisory: no gate reads it)
bench judgment-exact-or-proxy: classifiers available (32): openai/gpt-6-luna, openrouter/~perplexity/pplx-decider-latest, openrouter/~typesafe/jev-latest, openrouter/cloudflare/clef, openrouter/cloudflare/clef-flash, openrouter/cloudflare/clef-omni, openrouter/inception/mercury-decide, openrouter/inception/mercury-decide:free, openrouter/jaredpalmer/kev-4b, openrouter/liquid/d1, openrouter/microsoft/microsoft-decision-1, openrouter/nace-ai/drex-v1.5, openrouter/nace-ai/drex-v2.0, openrouter/openai/gpt-6-luna-decisions, openrouter/perplexity/pplx-decider-v1.1-27b, openrouter/respan/span-01, openrouter/respan/span-01-lite, openrouter/respan/span-01-lite:free, openrouter/scaledown/classify-1, openrouter/togethercomputer/tev1-4b-experimental, openrouter/typesafe/jev-1.13, openrouter/typesafe/jev-1.14, openrouter/upstage/solar-decide, openrouter/upstage/solar-decide-flash, openrouter/~perplexity/pplx-decider-flash-latest, openrouter/baseten/elephant-1:free, openrouter/baseten/mammoth-1:free, openrouter/liquid/d1-ultra, openrouter/nace-ai/drex-max, openrouter/perplexity/pplx-decider-flash-v1.2, openrouter/perplexity/pplx-decider-v1.2, openrouter/respan/span-02
bench judgment-exact-or-proxy: benched only --classifier openrouter/typesafe/jev-1.13
TRAIN (2 cases; the choice and threshold are made here):
  model                         answered  correct  accuracy  brier   ece     cost_usd   errors
  openrouter/typesafe/jev-1.13    2/2           2     1.000  0.200   0.300    0.000091  0
HELD-OUT (1 cases; the measure, never used to choose):
  model                         answered  correct  accuracy  brier   ece     cost_usd   errors
  openrouter/typesafe/jev-1.13    1/1           0     0.000  0.871   0.660    0.000091  0
  (cost_usd and errors: the model's every call, train and held-out; brier: mean multi-class Brier score, lower is better; ece: expected calibration error over top-probability buckets [0.0, 0.5), [0.5, 0.6), [0.6, 0.7), [0.7, 0.8), [0.8, 0.9), [0.9, 1.0])
chosen openrouter/typesafe/jev-1.13 (from train only: highest train accuracy over every train case answered; ties: lower train Brier, lower train cost, name): train accuracy 1.000, brier 0.200, ece 0.300
proposed threshold (for the director to accept; until met, the judge stays advisory): held-out accuracy >= 0.342 and held-out brier <= 0.435 (from train only: accuracy_min the Wilson 1.96 lower bound of train accuracy, brier_max train Brier mean + 1.96 standard errors)
held-out now: accuracy 0.000 (0/1 of 1), brier 0.871, ece 0.660: does not meet the proposed threshold
chosen calibration train (top probability bucket: n, mean top probability, accuracy): [0.6, 0.7) n 1 p 0.600 acc 1.000; [0.8, 0.9) n 1 p 0.800 acc 1.000
chosen calibration held-out (top probability bucket: n, mean top probability, accuracy): [0.6, 0.7) n 1 p 0.660 acc 0.000
DONE bench judgment-exact-or-proxy: chosen openrouter/typesafe/jev-1.13 [2.1 s]
qa: 1/1 bench(es) done (run 20261025T013839Z-e2b9b5); artifacts /home/exedev/.local/state/octo-feather/qa/20261025T013839Z-e2b9b5
```

Pipeline real: 3 classify results with cost from usage; the hidden reference (labelled_by, relabel, reason) absent from input.json, extension.js and stdout.txt (grep count 0). jev-1.13 answers: check-refs-linear-word proxy (right, p 0.80), gh82-tracker-prose proxy (right, p 0.60), justfile-check-scripts proxy (wrong, p 0.66).

## Demo: full bench (run 20261025T013852Z-21c7ad, 137.2 s, kit b5ed8aa)

Artifacts: $(octo-feather-state)/qa/20261025T013852Z-21c7ad/judgment-exact-or-proxy/ (input.json, extension.js, stdout.txt, stderr.txt, sandbox.json, answers.json, bench.json, report.txt) and summary.json. Full output:

```
$ scripts/octo-feather-qa --suite judgment-exact-or-proxy
evals: ok (7 suites, 250 cases)
qa: run 20261025T013852Z-21c7ad: 31 case(s); kit b5ed8aa369d8f582e456e64dc00ffb0d3ab7e3d0; artifacts /home/exedev/.local/state/octo-feather/qa/20261025T013852Z-21c7ad
qc sandbox: ok   /tmp is private (nothing the judge writes there outlives the run)
qc sandbox: ok   judge holds no capabilities (CapEff 0000000000000000), no_new_privs 1, uid 1000
qc sandbox: ok   masks locked: umount of the Herdr mask exits 32, after its own unshare -rm 32
qc sandbox: ok   HOME, /var/tmp, the kit read-only
qc sandbox: ok   worktree /tmp/qa-21c7ad-bench-lwb_l9q7 is an overlay, upper dir on the run tmpfs and hidden from the judge
qc sandbox: ok   writable persistent paths: none
qc sandbox: ok   vendored-skill cache /home/exedev/.cache/octo-feather/skillfile bound read-only (not writable, not in the writable list)
qc sandbox: ok   live Herdr unreachable: raw herdr --session default workspace list exits 1
qc sandbox: ok   herdr shim pins sandbox session qa-21c7ad-bench despite --session default --remote --machine
qc sandbox: ok   Herdr config shows only the sandbox session: [qa-21c7ad-bench]
qc sandbox: ok   no gh or git creds: tokens 0, gh config entries 0, git-credentials 0 bytes, gh auth status exits 1
qc sandbox: ok   no tracker credential: LINEAR_API_KEY set 0 times
qc sandbox: ok   parent route unset: 0 of OCTO_FEATHER_PARENT/SESSION_ID/ROLE, HERDR_PANE/TAB/WORKSPACE_ID, HERDR_ENV set
qc sandbox: ok   state dir is per-run scratch: /tmp/.qc-qa-21c7ad-bench/state/octo-feather/sessions/qa-21c7ad-bench
qc sandbox: ok   history none (0 bound: no archived lanes, no director log; a factory eval sees no lane history); live records masked (6 paths, 0 bytes or entries visible)
qc sandbox: ok   github: none (factory eval: no GitHub evidence); the offline gh refuses every call (exit 1)
qc sandbox: ok   worktree clean at ada6078a47e0
qc sandbox: cleanup: agents started 0 (headless pi 0, Herdr panes 0); leftover processes killed 0, left 0 (the kernel kills those as PID 1 exits); session qa-21c7ad-bench stopped and deleted; offline gh refusals 0
bench judgment-exact-or-proxy: question b-exact-or-proxy, labels exact, proxy; 31 cases (train 20, held-out 11); every answer is a model judgment (classifier output, advisory: no gate reads it)
bench judgment-exact-or-proxy: classifiers available (32): openai/gpt-6-luna, openrouter/~perplexity/pplx-decider-latest, openrouter/~typesafe/jev-latest, openrouter/cloudflare/clef, openrouter/cloudflare/clef-flash, openrouter/cloudflare/clef-omni, openrouter/inception/mercury-decide, openrouter/inception/mercury-decide:free, openrouter/jaredpalmer/kev-4b, openrouter/liquid/d1, openrouter/microsoft/microsoft-decision-1, openrouter/nace-ai/drex-v1.5, openrouter/nace-ai/drex-v2.0, openrouter/openai/gpt-6-luna-decisions, openrouter/perplexity/pplx-decider-v1.1-27b, openrouter/respan/span-01, openrouter/respan/span-01-lite, openrouter/respan/span-01-lite:free, openrouter/scaledown/classify-1, openrouter/togethercomputer/tev1-4b-experimental, openrouter/typesafe/jev-1.13, openrouter/typesafe/jev-1.14, openrouter/upstage/solar-decide, openrouter/upstage/solar-decide-flash, openrouter/~perplexity/pplx-decider-flash-latest, openrouter/baseten/elephant-1:free, openrouter/baseten/mammoth-1:free, openrouter/liquid/d1-ultra, openrouter/nace-ai/drex-max, openrouter/perplexity/pplx-decider-flash-v1.2, openrouter/perplexity/pplx-decider-v1.2, openrouter/respan/span-02
bench judgment-exact-or-proxy: skipped: moving alias (3): openrouter/~perplexity/pplx-decider-latest, openrouter/~typesafe/jev-latest, openrouter/~perplexity/pplx-decider-flash-latest
TRAIN (20 cases; the choice and threshold are made here):
  model                                             answered  correct  accuracy  brier   ece     cost_usd   errors
  openrouter/cloudflare/clef                         20/20         16     0.800  0.298   0.111    0.005713  0
  openrouter/typesafe/jev-1.14                       20/20         16     0.800  0.302   0.092    0.001239  0
  openrouter/baseten/mammoth-1:free                  20/20         16     0.800  0.314   0.154    0.000000  0
  openrouter/cloudflare/clef-omni                    20/20         16     0.800  0.337   0.125    0.003460  0
  openrouter/microsoft/microsoft-decision-1          20/20         16     0.800  0.343   0.130    0.000915  0
  openrouter/typesafe/jev-1.13                       20/20         15     0.750  0.300   0.139    0.001239  0
  openrouter/perplexity/pplx-decider-v1.2            20/20         15     0.750  0.400   0.127    0.000449  0
  openrouter/upstage/solar-decide-flash              20/20         14     0.700  0.385   0.078    0.001565  0
  openrouter/openai/gpt-6-luna-decisions             20/20         14     0.700  0.413   0.151    0.002264  0
  openrouter/liquid/d1-ultra                         20/20         14     0.700  0.441   0.178    0.000880  0
  openrouter/inception/mercury-decide:free           20/20         14     0.700  0.479   0.211    0.000000  0
  openrouter/scaledown/classify-1                    20/20         14     0.700  0.505   0.232    0.001145  0
  openrouter/nace-ai/drex-max                        20/20         13     0.650  0.377   0.213    0.001354  0
  openrouter/jaredpalmer/kev-4b                      20/20         13     0.650  0.463   0.082    0.000862  0
  openrouter/inception/mercury-decide                20/20         13     0.650  0.594   0.319    0.000444  0
  openrouter/upstage/solar-decide                    20/20         13     0.650  0.624   0.306    0.001565  0
  openrouter/respan/span-02                          20/20         12     0.600  0.522   0.254    0.000251  0
  openrouter/perplexity/pplx-decider-flash-v1.2      20/20         12     0.600  0.527   0.231    0.000225  0
  openrouter/liquid/d1                               20/20         12     0.600  0.636   0.315    0.000419  0
  openrouter/baseten/elephant-1:free                 20/20         11     0.550  0.400   0.240    0.000000  0
  openrouter/nace-ai/drex-v1.5                       20/20         11     0.550  0.720   0.363    0.000821  0
  openrouter/cloudflare/clef-flash                   20/20         10     0.500  0.415   0.280    0.000452  0
  openrouter/nace-ai/drex-v2.0                       20/20         10     0.500  0.803   0.430    0.001231  0
  openrouter/togethercomputer/tev1-4b-experimental   20/20          9     0.450  0.582   0.283    0.000989  0
HELD-OUT (11 cases; the measure, never used to choose):
  model                                             answered  correct  accuracy  brier   ece     cost_usd   errors
  openrouter/cloudflare/clef                         11/11          8     0.727  0.344   0.196    0.005713  0
  openrouter/typesafe/jev-1.14                       11/11          8     0.727  0.279   0.148    0.001239  0
  openrouter/baseten/mammoth-1:free                  11/11         10     0.909  0.160   0.141    0.000000  0
  openrouter/cloudflare/clef-omni                    11/11          9     0.818  0.272   0.273    0.003460  0
  openrouter/microsoft/microsoft-decision-1          11/11          9     0.818  0.152   0.184    0.000915  0
  openrouter/typesafe/jev-1.13                       11/11          9     0.818  0.212   0.185    0.001239  0
  openrouter/perplexity/pplx-decider-v1.2            11/11         10     0.909  0.242   0.239    0.000449  0
  openrouter/upstage/solar-decide-flash              11/11          7     0.636  0.429   0.203    0.001565  0
  openrouter/openai/gpt-6-luna-decisions             11/11          7     0.636  0.360   0.125    0.002264  0
  openrouter/liquid/d1-ultra                         11/11          8     0.727  0.381   0.225    0.000880  0
  openrouter/inception/mercury-decide:free           11/11          9     0.818  0.380   0.237    0.000000  0
  openrouter/scaledown/classify-1                    11/11          8     0.727  0.400   0.086    0.001145  0
  openrouter/nace-ai/drex-max                        11/11         10     0.909  0.245   0.174    0.001354  0
  openrouter/jaredpalmer/kev-4b                      11/11          8     0.727  0.421   0.203    0.000862  0
  openrouter/inception/mercury-decide                11/11          7     0.636  0.522   0.276    0.000444  0
  openrouter/upstage/solar-decide                    11/11          9     0.818  0.232   0.108    0.001565  0
  openrouter/respan/span-02                          11/11          9     0.818  0.299   0.260    0.000251  0
  openrouter/perplexity/pplx-decider-flash-v1.2      11/11          6     0.545  0.430   0.304    0.000225  0
  openrouter/liquid/d1                               11/11          8     0.727  0.359   0.230    0.000419  0
  openrouter/baseten/elephant-1:free                 11/11          9     0.818  0.347   0.253    0.000000  0
  openrouter/nace-ai/drex-v1.5                       11/11          5     0.455  0.647   0.426    0.000821  0
  openrouter/cloudflare/clef-flash                   11/11          9     0.818  0.332   0.162    0.000452  0
  openrouter/nace-ai/drex-v2.0                       11/11          6     0.545  0.637   0.395    0.001231  0
  openrouter/togethercomputer/tev1-4b-experimental   11/11          9     0.818  0.422   0.272    0.000989  0
  (cost_usd and errors: the model's every call, train and held-out; brier: mean multi-class Brier score, lower is better; ece: expected calibration error over top-probability buckets [0.0, 0.5), [0.5, 0.6), [0.6, 0.7), [0.7, 0.8), [0.8, 0.9), [0.9, 1.0])
unavailable openai/gpt-6-luna: listed but answered no case: OpenAI Decisions error (404): OpenAI Decisions returned 404
unavailable openrouter/perplexity/pplx-decider-v1.1-27b: listed but answered no case: System One API error (404): {"error":{"message":"No endpoints found for perplexity/pplx-decider-v1.1-27b.","code":404},"user_id":"user_2j6vR9TdNFKYEGgN6TJb9xZd5EJ"}
unavailable openrouter/respan/span-01: listed but answered no case: System One API error (400): {"error":{"message":"Respan only accepts noul questions whose instructions and criteria are plain strings (question \"q\")","code":400}}
unavailable openrouter/respan/span-01-lite: listed but answered no case: System One API error (400): {"error":{"message":"Respan only accepts noul questions whose instructions and criteria are plain strings (question \"q\")","code":400}}
unavailable openrouter/respan/span-01-lite:free: listed but answered no case: System One API error (400): {"error":{"message":"Respan only accepts noul questions whose instructions and criteria are plain strings (question \"q\")","code":400}}
chosen openrouter/cloudflare/clef (from train only: highest train accuracy over every train case answered; ties: lower train Brier, lower train cost, name): train accuracy 0.800, brier 0.298, ece 0.111
proposed threshold (for the director to accept; until met, the judge stays advisory): held-out accuracy >= 0.584 and held-out brier <= 0.41 (from train only: accuracy_min the Wilson 1.96 lower bound of train accuracy, brier_max train Brier mean + 1.96 standard errors)
held-out now: accuracy 0.727 (8/11 of 11), brier 0.344, ece 0.196: meets the proposed threshold
chosen calibration train (top probability bucket: n, mean top probability, accuracy): [0.5, 0.6) n 7 p 0.543 acc 0.571; [0.6, 0.7) n 5 p 0.660 acc 0.800; [0.7, 0.8) n 2 p 0.715 acc 1.000; [0.8, 0.9) n 5 p 0.870 acc 1.000; [0.9, 1.0] n 1 p 0.909 acc 1.000
chosen calibration held-out (top probability bucket: n, mean top probability, accuracy): [0.5, 0.6) n 3 p 0.541 acc 0.667; [0.6, 0.7) n 3 p 0.633 acc 0.333; [0.7, 0.8) n 2 p 0.757 acc 1.000; [0.8, 0.9) n 3 p 0.870 acc 1.000
DONE bench judgment-exact-or-proxy: chosen openrouter/cloudflare/clef [137.2 s]
qa: 1/1 bench(es) done (run 20261025T013852Z-21c7ad); artifacts /home/exedev/.local/state/octo-feather/qa/20261025T013852Z-21c7ad
```

## Cost (per-model cost_usd and the run total; no spend ledger)

From this run's bench.json `models[].cost_usd` (every call, train and held-out) and `train_cost_usd` (the tie-break). Run total (bench.json `cost_usd`): $0.027480. Skipped moving aliases make no call and carry no cost: openrouter/~perplexity/pplx-decider-latest, openrouter/~typesafe/jev-latest, openrouter/~perplexity/pplx-decider-flash-latest.

| model | cost_usd | train_cost_usd |
|---|---|---|
| openai/gpt-6-luna | 0.000000 | 0.000000 |
| openrouter/cloudflare/clef | 0.005713 | 0.003685 |
| openrouter/cloudflare/clef-flash | 0.000452 | 0.000292 |
| openrouter/cloudflare/clef-omni | 0.003460 | 0.002230 |
| openrouter/inception/mercury-decide | 0.000444 | 0.000286 |
| openrouter/inception/mercury-decide:free | 0.000000 | 0.000000 |
| openrouter/jaredpalmer/kev-4b | 0.000862 | 0.000556 |
| openrouter/liquid/d1 | 0.000419 | 0.000270 |
| openrouter/microsoft/microsoft-decision-1 | 0.000915 | 0.000589 |
| openrouter/nace-ai/drex-v1.5 | 0.000821 | 0.000529 |
| openrouter/nace-ai/drex-v2.0 | 0.001231 | 0.000794 |
| openrouter/openai/gpt-6-luna-decisions | 0.002264 | 0.001458 |
| openrouter/perplexity/pplx-decider-v1.1-27b | 0.000000 | 0.000000 |
| openrouter/respan/span-01 | 0.000000 | 0.000000 |
| openrouter/respan/span-01-lite | 0.000000 | 0.000000 |
| openrouter/respan/span-01-lite:free | 0.000000 | 0.000000 |
| openrouter/scaledown/classify-1 | 0.001145 | 0.000739 |
| openrouter/togethercomputer/tev1-4b-experimental | 0.000989 | 0.000637 |
| openrouter/typesafe/jev-1.13 | 0.001239 | 0.000798 |
| openrouter/typesafe/jev-1.14 | 0.001239 | 0.000798 |
| openrouter/upstage/solar-decide | 0.001565 | 0.001010 |
| openrouter/upstage/solar-decide-flash | 0.001565 | 0.001010 |
| openrouter/baseten/elephant-1:free | 0.000000 | 0.000000 |
| openrouter/baseten/mammoth-1:free | 0.000000 | 0.000000 |
| openrouter/liquid/d1-ultra | 0.000880 | 0.000567 |
| openrouter/nace-ai/drex-max | 0.001354 | 0.000873 |
| openrouter/perplexity/pplx-decider-flash-v1.2 | 0.000225 | 0.000145 |
| openrouter/perplexity/pplx-decider-v1.2 | 0.000449 | 0.000290 |
| openrouter/respan/span-02 | 0.000251 | 0.000162 |

## Reading

- 32 listed; 3 moving aliases skipped (never called); 29 benched; 24 scored, every one on all 31 cases; 5 unavailable, same provider reasons as the pilot: gpt-6-luna direct 404, pplx-decider-v1.1-27b 404 no endpoint, Respan span-01, span-01-lite, span-01-lite:free 400 (bool-only questions; this is a 2-label choice question).
- Chosen from train only: openrouter/cloudflare/clef (train 16/20, 0.800, Brier 0.298). Five models tie at 16/20 (clef, jev-1.14, mammoth-1:free, clef-omni, microsoft-decision-1); lower train Brier breaks it, clef 0.298 against jev-1.14 0.302. clef is the dearest model in the run ($0.005713, about 4.6 times jev-1.14). Proposed threshold: held-out accuracy >= 0.584 and Brier <= 0.41. Held-out now 8/11 (0.727), Brier 0.344: meets. Three of the tied models score higher on held-out (mammoth-1:free 10/11, clef-omni and microsoft-decision-1 9/11); held-out is never used to choose.
- Majority label (exact) alone scores train 10/20 and held-out 6/11, so the best models clear the base rate by 6 train cases.
- Hardest cases (right answers out of 24 scored models): gh82-tracker-prose 5 and ticket-what-to-build-names-demo 10 (the two director flips; the set's REPORT doubts already say a classifier may fairly answer exact on gh82, whose label rests on a ruling the state cannot show without leaking), gh107-grade-skill-before-target 6, check-gate-free 8, gh108-qa-transcript-grader 8 (held-out). Models lean exact on proxies whose code looks structural. clef misses 7: justfile-check-scripts, check-behavior-smoke-presence, check-test-surface (held-out); check-refs-lane-branch-strings, expand-contract-waiver, gh107-grade-skill-before-target, gh82-tracker-prose (train).

## Rebench for the kit's one judgment model (run 20261025T145239Z-a5d4b6, 2026-10-25)

Owner ruling 2026-10-25 (spec judgment#rule-one-model): one judgment model for every question, openrouter/typesafe/jev-1.13,
recorded in evals/judgment-model.json (evidence/2026-10-25-gh119-judgment-model.md). This rerun refreshes this suite's
`calibration` (the kit model's held-out score and proposed threshold, accepted false); the bench shows the kit's model
beside the question's best-scoring classifier and no longer names a per-question choice. The Respan span-01 models are
now "skipped: yes/no only" by the probe (a tiny choice question refused, a tiny bool question answered), no longer unavailable.

`scripts/octo-feather-qa --suite judgment-exact-or-proxy` (sandbox proof lines omitted; artifacts $(octo-feather-state)/qa/20261025T145239Z-a5d4b6/):

```
evals: ok (8 suites, 272 cases)
qa: run 20261025T145239Z-a5d4b6: 31 case(s); kit e19b3c8ada566378f6edd48b94942ed00c1d6105; artifacts /home/exedev/.local/state/octo-feather/qa/20261025T145239Z-a5d4b6
qc sandbox: cleanup: agents started 0 (headless pi 0, Herdr panes 0); leftover processes killed 0, left 0 (the kernel kills those as PID 1 exits); session qa-a5d4b6-bench stopped and deleted; offline gh refusals 0
bench judgment-exact-or-proxy: question b-exact-or-proxy, labels exact, proxy; 31 cases (train 20, held-out 11); every answer is a model judgment (classifier output, advisory: no gate reads it)
bench judgment-exact-or-proxy: classifiers available (32): openai/gpt-6-luna, openrouter/~perplexity/pplx-decider-latest, openrouter/~typesafe/jev-latest, openrouter/cloudflare/clef, openrouter/cloudflare/clef-flash, openrouter/cloudflare/clef-omni, openrouter/inception/mercury-decide, openrouter/inception/mercury-decide:free, openrouter/jaredpalmer/kev-4b, openrouter/liquid/d1, openrouter/microsoft/microsoft-decision-1, openrouter/nace-ai/drex-v1.5, openrouter/nace-ai/drex-v2.0, openrouter/openai/gpt-6-luna-decisions, openrouter/perplexity/pplx-decider-v1.1-27b, openrouter/respan/span-01, openrouter/respan/span-01-lite, openrouter/respan/span-01-lite:free, openrouter/scaledown/classify-1, openrouter/togethercomputer/tev1-4b-experimental, openrouter/typesafe/jev-1.13, openrouter/typesafe/jev-1.14, openrouter/upstage/solar-decide, openrouter/upstage/solar-decide-flash, openrouter/~perplexity/pplx-decider-flash-latest, openrouter/baseten/elephant-1:free, openrouter/baseten/mammoth-1:free, openrouter/liquid/d1-ultra, openrouter/nace-ai/drex-max, openrouter/perplexity/pplx-decider-flash-v1.2, openrouter/perplexity/pplx-decider-v1.2, openrouter/respan/span-02
bench judgment-exact-or-proxy: skipped: moving alias (3): openrouter/~perplexity/pplx-decider-latest, openrouter/~typesafe/jev-latest, openrouter/~perplexity/pplx-decider-flash-latest
bench judgment-exact-or-proxy: skipped: yes/no only openrouter/respan/span-01: a tiny choice question refused, a tiny bool question answered (probability 0.9637); provider: System One API error (400): {"error":{"message":"Respan only accepts noul questions whose instructions and criteria are plain strings (question \"q\")","code":400}}
bench judgment-exact-or-proxy: skipped: yes/no only openrouter/respan/span-01-lite: a tiny choice question refused, a tiny bool question answered (probability 0.9637); provider: System One API error (400): {"error":{"message":"Respan only accepts noul questions whose instructions and criteria are plain strings (question \"q\")","code":400}}
bench judgment-exact-or-proxy: skipped: yes/no only openrouter/respan/span-01-lite:free: a tiny choice question refused, a tiny bool question answered (probability 0.9637); provider: System One API error (400): {"error":{"message":"Respan only accepts noul questions whose instructions and criteria are plain strings (question \"q\")","code":400}}
TRAIN (20 cases; the best and the kit model's threshold are made here):
  model                                             answered  correct  accuracy  brier   ece     cost_usd   errors
  openrouter/typesafe/jev-1.14                       20/20         16     0.800  0.293   0.090    0.001239  0
  openrouter/cloudflare/clef                         20/20         16     0.800  0.294   0.107    0.005713  0
  openrouter/baseten/mammoth-1:free                  20/20         16     0.800  0.314   0.154    0.000000  0
  openrouter/typesafe/jev-1.13                       20/20         16     0.800  0.315   0.173    0.001239  0
  openrouter/cloudflare/clef-omni                    20/20         16     0.800  0.337   0.125    0.003460  0
  openrouter/microsoft/microsoft-decision-1          20/20         16     0.800  0.339   0.128    0.000915  0
  openrouter/upstage/solar-decide                    20/20         16     0.800  0.387   0.231    0.001565  0
  openrouter/perplexity/pplx-decider-v1.2            20/20         15     0.750  0.400   0.127    0.000449  0
  openrouter/liquid/d1-ultra                         20/20         15     0.750  0.409   0.198    0.000880  0
  openrouter/upstage/solar-decide-flash              20/20         14     0.700  0.395   0.263    0.001565  0
  openrouter/openai/gpt-6-luna-decisions             20/20         14     0.700  0.413   0.151    0.002264  0
  openrouter/respan/span-02                          20/20         14     0.700  0.448   0.165    0.000251  0
  openrouter/inception/mercury-decide                20/20         14     0.700  0.552   0.286    0.000446  0
  openrouter/nace-ai/drex-max                        20/20         13     0.650  0.377   0.213    0.001354  0
  openrouter/scaledown/classify-1                    20/20         13     0.650  0.511   0.182    0.001145  0
  openrouter/cloudflare/clef-flash                   20/20         12     0.600  0.380   0.215    0.000452  0
  openrouter/baseten/elephant-1:free                 20/20         12     0.600  0.386   0.191    0.000000  0
  openrouter/jaredpalmer/kev-4b                      20/20         12     0.600  0.463   0.049    0.000862  0
  openrouter/perplexity/pplx-decider-flash-v1.2      20/20         12     0.600  0.527   0.231    0.000225  0
  openrouter/inception/mercury-decide:free           20/20         12     0.600  0.579   0.289    0.000000  0
  openrouter/liquid/d1                               20/20         12     0.600  0.596   0.357    0.000419  0
  openrouter/nace-ai/drex-v1.5                       20/20         11     0.550  0.720   0.363    0.000821  0
  openrouter/nace-ai/drex-v2.0                       20/20         10     0.500  0.803   0.430    0.001231  0
  openrouter/togethercomputer/tev1-4b-experimental   20/20          9     0.450  0.585   0.281    0.000989  0
HELD-OUT (11 cases; the measure, never used to pick):
  model                                             answered  correct  accuracy  brier   ece     cost_usd   errors
  openrouter/typesafe/jev-1.14                       11/11          8     0.727  0.270   0.147    0.001239  0
  openrouter/cloudflare/clef                         11/11          7     0.636  0.341   0.213    0.005713  0
  openrouter/baseten/mammoth-1:free                  11/11         10     0.909  0.161   0.141    0.000000  0
  openrouter/typesafe/jev-1.13                       11/11          9     0.818  0.218   0.125    0.001239  0
  openrouter/cloudflare/clef-omni                    11/11          9     0.818  0.272   0.273    0.003460  0
  openrouter/microsoft/microsoft-decision-1          11/11          9     0.818  0.146   0.178    0.000915  0
  openrouter/upstage/solar-decide                    11/11         10     0.909  0.131   0.068    0.001565  0
  openrouter/perplexity/pplx-decider-v1.2            11/11         10     0.909  0.242   0.239    0.000449  0
  openrouter/liquid/d1-ultra                         11/11          8     0.727  0.350   0.209    0.000880  0
  openrouter/upstage/solar-decide-flash              11/11          7     0.636  0.463   0.244    0.001565  0
  openrouter/openai/gpt-6-luna-decisions             11/11          7     0.636  0.360   0.125    0.002264  0
  openrouter/respan/span-02                          11/11          9     0.818  0.308   0.193    0.000251  0
  openrouter/inception/mercury-decide                11/11          9     0.818  0.364   0.220    0.000446  0
  openrouter/nace-ai/drex-max                        11/11         10     0.909  0.245   0.174    0.001354  0
  openrouter/scaledown/classify-1                    11/11          6     0.545  0.473   0.165    0.001145  0
  openrouter/cloudflare/clef-flash                   11/11          9     0.818  0.340   0.174    0.000452  0
  openrouter/baseten/elephant-1:free                 11/11          9     0.818  0.337   0.166    0.000000  0
  openrouter/jaredpalmer/kev-4b                      11/11          8     0.727  0.419   0.257    0.000862  0
  openrouter/perplexity/pplx-decider-flash-v1.2      11/11          6     0.545  0.430   0.304    0.000225  0
  openrouter/inception/mercury-decide:free           11/11          9     0.818  0.380   0.244    0.000000  0
  openrouter/liquid/d1                               11/11          8     0.727  0.293   0.218    0.000419  0
  openrouter/nace-ai/drex-v1.5                       11/11          5     0.455  0.647   0.426    0.000821  0
  openrouter/nace-ai/drex-v2.0                       11/11          6     0.545  0.637   0.395    0.001231  0
  openrouter/togethercomputer/tev1-4b-experimental   11/11          9     0.818  0.436   0.274    0.000989  0
  (cost_usd and errors: the model's every call, train and held-out; brier: mean multi-class Brier score, lower is better; ece: expected calibration error over top-probability buckets [0.0, 0.5), [0.5, 0.6), [0.6, 0.7), [0.7, 0.8), [0.8, 0.9), [0.9, 1.0])
unavailable openai/gpt-6-luna: listed but answered no case: OpenAI Decisions error (404): OpenAI Decisions returned 404
unavailable openrouter/perplexity/pplx-decider-v1.1-27b: listed but answered no case: System One API error (404): {"error":{"message":"No endpoints found for perplexity/pplx-decider-v1.1-27b.","code":404},"user_id":"user_2j6vR9TdNFKYEGgN6TJb9xZd5EJ"}
KIT MODEL BESIDE THE BEST (best: highest train accuracy over every train case answered; ties: lower train Brier, lower train cost, name; held-out apart, never used to pick):
        model                                             train acc  train brier  held-out acc  held-out brier  cost_usd
  kit   openrouter/typesafe/jev-1.13                          0.800        0.315         0.818           0.218  0.001239
  best  openrouter/typesafe/jev-1.14                          0.800        0.293         0.727           0.270  0.001239
kit model openrouter/typesafe/jev-1.13 (judgment-model.json): proposed threshold (for the director to accept; until met, the judge stays advisory): held-out accuracy >= 0.584 and held-out brier <= 0.468 (from train only: accuracy_min the Wilson 1.96 lower bound of train accuracy, brier_max train Brier mean + 1.96 standard errors)
held-out now: accuracy 0.818 (9/11 of 11), brier 0.218, ece 0.125: meets the proposed threshold
kit model calibration train (top probability bucket: n, mean top probability, accuracy): [0.5, 0.6) n 6 p 0.550 acc 0.833; [0.6, 0.7) n 4 p 0.655 acc 0.500; [0.7, 0.8) n 2 p 0.725 acc 1.000; [0.8, 0.9) n 4 p 0.843 acc 0.750; [0.9, 1.0] n 4 p 0.948 acc 1.000
kit model calibration held-out (top probability bucket: n, mean top probability, accuracy): [0.5, 0.6) n 2 p 0.545 acc 0.500; [0.6, 0.7) n 2 p 0.660 acc 0.500; [0.7, 0.8) n 1 p 0.730 acc 1.000; [0.8, 0.9) n 3 p 0.833 acc 1.000; [0.9, 1.0] n 3 p 0.933 acc 1.000
DONE bench judgment-exact-or-proxy: kit model openrouter/typesafe/jev-1.13, best openrouter/typesafe/jev-1.14 [221.8 s]
qa: 1/1 bench(es) done (run 20261025T145239Z-a5d4b6); artifacts /home/exedev/.local/state/octo-feather/qa/20261025T145239Z-a5d4b6
```
