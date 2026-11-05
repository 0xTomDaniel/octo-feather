import argparse
import sys

from slugger.rules import slugify


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="slug", description="print a URL slug for TEXT")
    parser.add_argument("text")
    args = parser.parse_args(argv)
    slug = slugify(str(args.text))
    if not slug:
        sys.stderr.write("error: TEXT has no letters or digits\n")
        return 2
    sys.stdout.write(slug + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
