"""notes: a small note-keeping CLI.

Every error names the command that fixes it; usage errors exit 2, others 1.
"""

import argparse
import json
import pathlib
import sys

NOTES = pathlib.Path("notes.json")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="app")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init")
    add = sub.add_parser("add")
    add.add_argument("text")
    sub.add_parser("list")
    # argparse exits 2 on a usage error, as every usage error must.
    args = parser.parse_args(argv)
    if args.command == "init":
        NOTES.write_text("[]")
        return 0
    if not NOTES.exists():
        # Errors must name the fix: point the user at `app init`.
        print("error: no notes file here; run `app init` to create it", file=sys.stderr)
        return 1
    notes = json.loads(NOTES.read_text())
    if args.command == "add":
        notes.append(args.text)
        NOTES.write_text(json.dumps(notes))
    else:
        for note in notes:
            print(note)
    return 0


if __name__ == "__main__":
    sys.exit(main())
