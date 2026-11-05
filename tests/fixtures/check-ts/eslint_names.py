"""tests/gate/kit/check_ts.py's assertion that eslint named a finding at a file and line (#245).

Run as `python3 eslint_names.py FILE LINE RULE` with `just check-ts` output on stdin. eslint's
default (stylish) output is a block per file: the file's absolute path on its own line, then one
row per finding, `  LINE:COL  error  MESSAGE  RULE`. Exit 0 when FILE's block has a row at LINE
for RULE; exit 1 naming what is missing.
"""

from __future__ import annotations

import sys


def named(out: str, path: str, line: int, rule: str) -> bool:
    current = ""
    for row in out.splitlines():
        if row.startswith("/"):
            current = row.strip()
            continue
        fields = row.split()
        if (
            current == path
            and fields
            and fields[0].split(":")[0] == str(line)
            and fields[-1] == rule
        ):
            return True
    return False


def main() -> int:
    path, line, rule = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    if named(sys.stdin.read(), path, line, rule):
        return 0
    sys.stderr.write(f"eslint did not name {path}:{line} {rule}\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
