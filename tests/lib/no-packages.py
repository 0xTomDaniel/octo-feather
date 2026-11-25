#!/usr/bin/env python3
"""no-packages.py: a kit copy's JavaScript packages left out, for a nested gate that needs none.

A test helper run as a command (tests/check-refs.sh, tests/check-decision-log.sh,
tests/gate/kit/gate_untouched.py and gate_recipes_first.py); in tests/lib/ so the gate's tests/*.sh
glob does not collect it.

  no-packages.py DIR
      DIR's package.json without its devDependencies and its pnpm-lock.yaml one with no packages
      (NO_DEPS): the nested gate's check-tests prelude (`pnpm install --offline
      --frozen-lockfile`, the justfile) then installs nothing, ~2 s CPU less than installing the
      kit's packages from its store into a fresh copy.
"""

import json
import pathlib
import sys

NO_DEPS = """lockfileVersion: '9.0'

settings:
  autoInstallPeers: true
  excludeLinksFromLockfile: false

importers:

  .: {}
"""


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("usage: no-packages.py DIR")
    d = pathlib.Path(sys.argv[1])
    pkg = json.loads((d / "package.json").read_text())
    del pkg["devDependencies"]
    (d / "package.json").write_text(json.dumps(pkg, indent=2) + "\n")
    (d / "pnpm-lock.yaml").write_text(NO_DEPS)


if __name__ == "__main__":
    main()
