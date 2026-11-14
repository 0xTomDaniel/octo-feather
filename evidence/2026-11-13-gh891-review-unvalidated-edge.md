# gh891: code review blocks an unvalidated edge (class unvalidated-edge)

Change (ticket #895, lane gh891): the code-review skill's Verdict step gains **Edges**: block, class `unvalidated-edge`, a diff reading structured data from outside the code, in product code or a test, without meeting quality spec `#acceptance-edge-validated`, naming the edge and the schema library; failure example exosurface PR #257 (452a12e). Patch plus materialized skill; the patch's reason line unchanged. Eval cases reviewer-unvalidated-edge-ts and reviewer-unvalidated-edge-py (evals/role-transcripts), fixtures ts-pnpm-store, ts-pnpm-store-shared, python-app-pydantic, python-app-pydantic-team.

Smoke: .agents/skills/code-review/SKILL.md .skillfile/patches/skills/code-review/SKILL.md.patch (runs below)
Removed: nothing deleted. Incident: exosurface PR #257 cleared its first review with a test reading pnpm's `node_modules/.modules.yaml` `storeDir` by regex; only review round 452a12e (yaml.parse + zod) fixed it.

Base: 7bb5c703 (`--baseline 7bb5c703`). Runs serial, `scripts/octo-feather-qa --suite role-transcripts --case <id> --runs N --baseline 7bb5c703`; artifacts under the qa state dir, by run id.

## Smoke (run 20261113T225309Z-7a1f1f, --runs 1, kit: working tree over b1d09ea7)

```
PASS role-transcripts/reviewer-unvalidated-edge-ts: 1/1 runs passed (pass rate 1.00, stddev 0.00); run 1: field_lines Verdict: 1 line(s) [{"text": "blocking"}]; holds {"text": "blocking"}; declared_includes blocking: holds {"path": "test/setup-shared-store.test.ts", "class": "unvalidated-edge", "library": "zod"} [58.3 s]
  baseline FAIL role-transcripts/reviewer-unvalidated-edge-ts: 0/1 runs passed (pass rate 0.00, stddev 0.00); run 1: declared_includes blocking: no entry with {"path": "test/setup-shared-store.test.ts", "class": "unvalidated-edge", "library": "zod"} in [{"path": "test/setup-shared-store.test.ts", "class": "reinvented-library", "library": "yaml"}] [89.6 s] [kit 7bb5c70399dc]
               baseline             current              difference
    pass rate  0.00 +/- 0.00        1.00 +/- 0.00        +1.00
    time s     89.6 +/- 0.0         58.3 +/- 0.0         -31.3
    tokens     91255 +/- 0          106744 +/- 0         +15489
    cost usd   0.0876 +/- 0.0000    0.0757 +/- 0.0000    -0.0119
```

Analysis: field_lines Verdict blocking is non-discriminating (blocks on both kits); the class and library fact discriminates.

## Proof (run 20261113T225614Z-26e343, --runs 3, kit 40ff3814 beside baseline 7bb5c703, runs interleaved, 13 m 30 s wall)

```
PASS role-transcripts/reviewer-unvalidated-edge-ts: 3/3 runs passed (pass rate 1.00, stddev 0.00); each run: declared_includes blocking: holds {"path": "test/setup-shared-store.test.ts", "class": "unvalidated-edge", "library": "zod"}
  baseline FAIL role-transcripts/reviewer-unvalidated-edge-ts: 0/3 runs passed (pass rate 0.00, stddev 0.00); each run: no entry with {... "class": "unvalidated-edge", "library": "zod"} in [{"path": "test/setup-shared-store.test.ts", "class": "reinvented-library", "library": "yaml"}]
               baseline             current              difference
    pass rate  0.00 +/- 0.00        1.00 +/- 0.00        +1.00
    time s     82.1 +/- 9.9         66.3 +/- 2.9         -15.8
    tokens     91318 +/- 3784       92471 +/- 12320      +1153
    cost usd   0.0783 +/- 0.0078    0.0829 +/- 0.0093    +0.0046
PASS role-transcripts/reviewer-unvalidated-edge-py: 3/3 runs passed (pass rate 1.00, stddev 0.00); each run: declared_includes blocking: holds {"path": "src/app/cli.py", "class": "unvalidated-edge", "library": "pydantic"}
  baseline FAIL role-transcripts/reviewer-unvalidated-edge-py: 0/3 runs passed (pass rate 0.00, stddev 0.00); each run: field_lines Verdict: no line with {"text": "blocking"} in [{"text": "clear"}]; blocking []
               baseline             current              difference
    pass rate  0.00 +/- 0.00        1.00 +/- 0.00        +1.00
    time s     54.2 +/- 6.5         65.6 +/- 5.5         +11.3
    tokens     71441 +/- 11077      127568 +/- 14265     +56127
    cost usd   0.0631 +/- 0.0072    0.1027 +/- 0.0334    +0.0396
qa: 2/2 passed (run 20261113T225614Z-26e343)
```

Analysis: field_lines Verdict blocking is non-discriminating on the ts case only (the baseline blocks it as reinvented-library); on the py case the baseline clears the head.

## Regression (run 20261113T233523Z-bad082, --runs 3, lane head 9090f90e beside baseline 7bb5c703, runs interleaved, 32 m 34 s wall)

These existing code-reviewer cases could have changed with the Edges paragraph. Pass rates, baseline to head:

| Case | Baseline | Head | Tokens mean | Cost usd mean | Time s mean |
|---|---|---|---|---|---|
| prior-art-extends | 3/3 | 3/3 | 113104 to 190578 | 0.0824 to 0.1119 | 94.2 to 108.1 |
| prior-art-extends-stated | 3/3 (clear) | 3/3 (clear) | 58225 to 139151 | 0.0573 to 0.0971 | 48.7 to 62.4 |
| prior-art-extends-held-out | 3/3 | 3/3 | 80282 to 145203 | 0.0781 to 0.0984 | 76.7 to 89.2 |
| reviewer-reinvented-parser | 3/3 | 3/3 | 102837 to 146198 | 0.0745 to 0.1000 | 83.5 to 86.7 |

No regression: prior-art-extends-stated, whose head reads YAML by hand with a stated reason, still clears in every run. The run's analysis flags a cost tradeoff on prior-art-extends, prior-art-extends-stated and prior-art-extends-held-out (pass rate 1.00 on both kits, mean tokens up). reviewer-reinvented-parser is flagged non-discriminating (every run passed on both kits). The cost increase is not attributed: 9090f90e also carries the other gh891 tickets' changes, so not only the Edges paragraph differs from 7bb5c703.
