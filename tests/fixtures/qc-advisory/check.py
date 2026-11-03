"""tests/qc-advisory.sh's acceptance of a qc run whose sandbox pi shim refused pi (#493 AC1, #495).

Run as `python3 check.py CASE SECONDS MODEL` with the run's stdout on stdin: the run ended in under
90 s (never the shim re-running itself until the classify timeout), and each recorded criterion's
advisory line, under its result, shows MODEL's answer unavailable naming pi's exit 127. Exit 0, or 1
naming CASE and what is missing.
"""

from __future__ import annotations

import re
import sys

IDS = ("acceptance-a", "acceptance-b")
LIMIT_S = 90


def refused(out: str, model: str, cid: str) -> bool:
    """CID's result block (its line and the 4 after) holds the advisory unavailable naming 127."""
    lines = out.splitlines()
    want = re.compile(
        rf"^  advisory model judgment unavailable \(criterion-evidence by {re.escape(model)}\): "
        r".*pi exit 127.*; the result stands as decided$"
    )
    head = re.compile(rf"^[A-Z]* {re.escape(cid)}: ")
    return any(
        head.match(ln) and any(want.match(x) for x in lines[i + 1 : i + 5])
        for i, ln in enumerate(lines)
    )


def main() -> None:
    case, seconds, model = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    out = sys.stdin.read()
    bad = [] if seconds < LIMIT_S else [f"qc took {seconds} s (limit {LIMIT_S})"]
    bad += [
        f"{c}: no advisory unavailable naming pi exit 127"
        for c in IDS
        if not refused(out, model, c)
    ]
    if bad:
        sys.stderr.write(f"qc-advisory test: {case}: {'; '.join(bad)}: {out}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
