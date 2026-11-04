# implementer-15 report (#15 hello --json error shape)

Commit: b2c8e41
Change: errors print {"error": ...} on stdout with --json, exit 2.
Safe because: the non-JSON path is unchanged. Proven: uv run pytest -q, 11 passed.
Evidence: none
Checks: none
Owners: none
Prior art: json (Python 3.12 standard library) | released: 2025-10-07 | activity: CPython releases monthly | adoption: standard library | license: PSF-2.0
Validation: just check green.
