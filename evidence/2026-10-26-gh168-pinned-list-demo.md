# gh168 demo: pinned is one ruled list (evals/classifiers.json)

Kit at 8451938 + this ticket's change. Live classifier catalogue read 2026-10-26: 32 ids, the same 32 as evidence/2026-10-25-gh119-judgment-bench-ticket-slice.md; no catalogue field marks an alias, so moving_alias holds the 3 the owner ruling names (~typesafe/jev-latest, ~perplexity/pplx-decider-latest, ~perplexity/pplx-decider-flash-latest) and pinned the other 29. check-evals takes EVALS_DIR as a positional argument (it has no --evals flag).

One edit after the run: the unclassified line's last words, a retired word in the run, now read "[the owner]" as the committed code prints them (check-refs, GLOSSARY.md); the rest is verbatim.

## check-evals refuses judgment-model.json naming a listed alias

```
$ scripts/check-evals <tmp>/evals   # judgment-model.json names openrouter/~typesafe/jev-latest
check-evals: judgment-model.json: field model: openrouter/~typesafe/jev-latest is a moving alias in classifiers.json (owner: owner 2026-10-23 to the director: 'remove Jev latest from the bench'; director generalization the same night, gh119 gate bench-aliases 2026-10-23T23:11:59Z (lanes/archive/gh119.handoffs.jsonl): 'bench pinned versions only; ~ and -latest ids skipped as moving alias', owner did not object; spec judgment#rule-one-model); name a pinned one
check-evals: 1 problem(s) above; fix the case (check-evals --help lists the shape)
exit 1
```

## bench, run once (after a one-case smoke on jev-1.13, cost 0.000037 USD): tmp evals copy whose classifiers.json drops openrouter/typesafe/jev-1.14 from pinned

```
$ scripts/octo-feather-qa --evals <tmp evals copy, classifiers.json without openrouter/typesafe/jev-1.14 in pinned> --suite judgment-ticket-slice --classifier openrouter/~typesafe/jev-latest --classifier openrouter/typesafe/jev-1.13 --classifier openrouter/typesafe/jev-1.14
evals: ok (8 suites, 273 cases)
qa: run 20261026T152818Z-3a9ffd: 22 case(s); kit 8451938bc467fb18f012228c938869c3fb5c1ecf; artifacts ~/.local/state/octo-feather/qa/20261026T152818Z-3a9ffd
qc sandbox: cleanup: agents started 0 (headless pi 0, Herdr panes 0); leftover processes killed 0, left 0 (the kernel kills those as PID 1 exits); session qa-3a9ffd-bench stopped and deleted; offline gh refusals 0
bench judgment-ticket-slice: question c-ticket-slice, labels slice, layer-only; 22 cases (train 14, held-out 8); every answer is a model judgment (classifier output, advisory: no gate reads it)
bench judgment-ticket-slice: classifiers available (32): openai/gpt-6-luna, openrouter/~perplexity/pplx-decider-latest, openrouter/~typesafe/jev-latest, openrouter/cloudflare/clef, openrouter/cloudflare/clef-flash, openrouter/cloudflare/clef-omni, openrouter/inception/mercury-decide, openrouter/inception/mercury-decide:free, openrouter/jaredpalmer/kev-4b, openrouter/liquid/d1, openrouter/microsoft/microsoft-decision-1, openrouter/nace-ai/drex-v1.5, openrouter/nace-ai/drex-v2.0, openrouter/openai/gpt-6-luna-decisions, openrouter/perplexity/pplx-decider-v1.1-27b, openrouter/respan/span-01, openrouter/respan/span-01-lite, openrouter/respan/span-01-lite:free, openrouter/scaledown/classify-1, openrouter/togethercomputer/tev1-4b-experimental, openrouter/typesafe/jev-1.13, openrouter/typesafe/jev-1.14, openrouter/upstage/solar-decide, openrouter/upstage/solar-decide-flash, openrouter/~perplexity/pplx-decider-flash-latest, openrouter/baseten/elephant-1:free, openrouter/baseten/mammoth-1:free, openrouter/liquid/d1-ultra, openrouter/nace-ai/drex-max, openrouter/perplexity/pplx-decider-flash-v1.2, openrouter/perplexity/pplx-decider-v1.2, openrouter/respan/span-02
bench judgment-ticket-slice: benched only --classifier openrouter/~typesafe/jev-latest, openrouter/typesafe/jev-1.13, openrouter/typesafe/jev-1.14
bench judgment-ticket-slice: skipped: moving alias (1): openrouter/~typesafe/jev-latest; never called, ruling (classifiers.json owner): owner 2026-10-23 to the director: 'remove Jev latest from the bench'; director generalization the same night, gh119 gate bench-aliases 2026-10-23T23:11:59Z (lanes/archive/gh119.handoffs.jsonl): 'bench pinned versions only; ~ and -latest ids skipped as moving alias', owner did not object; spec judgment#rule-one-model
bench judgment-ticket-slice: unclassified id (1): openrouter/typesafe/jev-1.14; benched and scored, in neither list of classifiers.json, never the kit's model until [the owner] rules it there
TRAIN (14 cases; the best and the kit model's threshold are made here):
  model                         answered  correct  accuracy  brier   ece     cost_usd   errors
  openrouter/typesafe/jev-1.13   14/14         12     0.857  0.095   0.107    0.000742  0
  openrouter/typesafe/jev-1.14   14/14         12     0.857  0.100   0.104    0.000742  0
HELD-OUT (8 cases; the measure, never used to pick):
  model                         answered  correct  accuracy  brier   ece     cost_usd   errors
  openrouter/typesafe/jev-1.13    8/8           8     1.000  0.004   0.028    0.000742  0
  openrouter/typesafe/jev-1.14    8/8           8     1.000  0.002   0.022    0.000742  0
  (cost_usd and errors: the model's every call, train and held-out; brier: mean multi-class Brier score, lower is better; ece: expected calibration error over top-probability buckets [0.0, 0.5), [0.5, 0.6), [0.6, 0.7), [0.7, 0.8), [0.8, 0.9), [0.9, 1.0])
KIT MODEL BESIDE THE BEST (best: highest train accuracy over every train case answered; ties: lower train Brier, lower train cost, name; held-out apart, never used to pick):
        model                         train acc  train brier  held-out acc  held-out brier  cost_usd
  kit   openrouter/typesafe/jev-1.13      0.857        0.095         1.000           0.004  0.000742
  best  openrouter/typesafe/jev-1.13      0.857        0.095         1.000           0.004  0.000742
kit model openrouter/typesafe/jev-1.13 (judgment-model.json): proposed threshold (for the director to accept; until met, the judge stays advisory): held-out accuracy >= 0.601 and held-out brier <= 0.212 (from train only: accuracy_min the Wilson 1.96 lower bound of train accuracy, brier_max train Brier mean + 1.96 standard errors)
held-out now: accuracy 1.000 (8/8 of 8), brier 0.004, ece 0.028: meets the proposed threshold
kit model calibration train (top probability bucket: n, mean top probability, accuracy): [0.5, 0.6) n 2 p 0.555 acc 0.000; [0.7, 0.8) n 1 p 0.790 acc 1.000; [0.9, 1.0] n 11 p 0.984 acc 1.000
kit model calibration held-out (top probability bucket: n, mean top probability, accuracy): [0.8, 0.9) n 1 p 0.890 acc 1.000; [0.9, 1.0] n 7 p 0.984 acc 1.000
DONE bench judgment-ticket-slice: kit model openrouter/typesafe/jev-1.13, best openrouter/typesafe/jev-1.13 [5.1 s]
qa: 1/1 bench(es) done (run 20261026T152818Z-3a9ffd); artifacts ~/.local/state/octo-feather/qa/20261026T152818Z-3a9ffd
exit 0
```

bench.json (benched, skipped, skipped_ruling, unclassified), then the models in answers.json (jev-latest never called):

```
{'benched': ['openrouter/typesafe/jev-1.13', 'openrouter/typesafe/jev-1.14'], 'skipped': ['openrouter/~typesafe/jev-latest'], 'skipped_ruling': "owner 2026-10-23 to the director: 'remove Jev latest from the bench'; director generalization the same night, gh119 gate bench-aliases 2026-10-23T23:11:59Z (lanes/archive/gh119.handoffs.jsonl): 'bench pinned versions only; ~ and -latest ids skipped as moving alias', owner did not object; spec judgment#rule-one-model", 'unclassified': ['openrouter/typesafe/jev-1.14']}
['openrouter/typesafe/jev-1.13', 'openrouter/typesafe/jev-1.14']
```
