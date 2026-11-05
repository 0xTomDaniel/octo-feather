# implementer-14 report (#14 hello --times)

Commit: 7d09e3b
Change: --times N repeats the greeting N times, 1 to 10; 0 is a usage error.
Safe because: default N is 1, output unchanged without the flag. Proven: uv run pytest -q, 9 passed.
Evidence: none
Checks: none
Owners: none
Prior art: argparse (Python 3.12 standard library) | released: 2025-10-07 | activity: CPython releases monthly | adoption: standard library | license: PSF-2.0
Validation: just check green.
