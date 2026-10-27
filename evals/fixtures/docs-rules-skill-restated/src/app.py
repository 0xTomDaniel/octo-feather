"""notes: a small note-keeping CLI."""

import argparse
import json
import pathlib
import sys

NOTES = pathlib.Path("notes.json")


class Parser(argparse.ArgumentParser):
    def __init__(self, *args, fix, **kwargs):
        super().__init__(*args, **kwargs)
        self.fix = fix

    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(2, f"{self.prog}: error: {message}; run {self.fix}\n")


def main(argv=None):
    parser = Parser(prog="app", fix="`app init`, `app add \"<text>\"` or `app list`")
    sub = parser.add_subparsers(dest="command", required=True, parser_class=Parser)
    sub.add_parser("init", fix="`app init`")
    add = sub.add_parser("add", fix="`app add \"<text>\"`")
    add.add_argument("text")
    sub.add_parser("list", fix="`app list`")
    args = parser.parse_args(argv)
    if args.command == "init":
        NOTES.write_text("[]")
        return 0
    if not NOTES.exists():
        # Every error names the command that fixes it; a usage error exits 2 (Parser.error).
        print("error: no notes file here; run `app init` to create it", file=sys.stderr)
        return 1
    try:
        notes = json.loads(NOTES.read_text())
    except ValueError:
        notes = None
    if not isinstance(notes, list):
        print("error: notes.json is not a list of notes; run `app init` to start a new notes file", file=sys.stderr)
        return 1
    if args.command == "add":
        notes.append(args.text)
        NOTES.write_text(json.dumps(notes))
    else:
        for note in notes:
            print(note)
    return 0


if __name__ == "__main__":
    sys.exit(main())
