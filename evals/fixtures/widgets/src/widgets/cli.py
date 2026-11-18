"""The widgets CLI."""

import sys

WIDGETS = {"w1": "sprocket", "w2": "gear"}


def main(argv: list[str]) -> int:
    if argv[:1] == ["show"] and len(argv) == 2 and argv[1] in WIDGETS:
        print(WIDGETS[argv[1]])
        return 0
    print("usage: widgets show ID", file=sys.stderr)
    return 2
