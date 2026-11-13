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
