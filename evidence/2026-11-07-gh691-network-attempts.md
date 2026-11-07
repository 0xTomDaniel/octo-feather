# gh691: srt's refused hosts in the qc sandbox's attempt record

Change: the qc sandbox runs srt through its own library (the CLI's Linux path, its bwrap argv identical for the same settings) and records each violation srt's store reports: a host outside the network allowlist becomes one attempt-record entry of the new kind `network`, which `attempt_blocked network` grades (eval-cases schema, Attempt record).

Smoke: .agents/skills/eval-cases/references/schema.md (the network kind: the run below produces exactly the entry it describes; no model run)

## Commands at the lane head, implementer pane of lane gh576

`scripts/octo-feather-qc-sandbox -- curl -sS https://example.com`:

```
curl: (56) CONNECT tunnel failed, response 403
{"attempts": [{"kind": "network", "attempt": true, "refused": true, "what": "connect example.com:443", "result": "srt refused: host is not on the allow list"}], "recorded": 1, "gh_misses": 0, "gh_miss_log": []}
qc sandbox: attempt record: 1 entries; offline gh refusals 0
```

Nested in a qc sandbox (`scripts/octo-feather-qc-sandbox -- sh -c '... scripts/octo-feather-qc-sandbox -- curl -sS https://example.com'`): the inner run prints the same 403 and `attempt record: 1 entries` naming `connect example.com:443`.

`tests/gate/kit/test_qc_sandbox.py::test_refused_host`: a refused host asked twice is exactly one entry; red on the launcher before this change, green after.
