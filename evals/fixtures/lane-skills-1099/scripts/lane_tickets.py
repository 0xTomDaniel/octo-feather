"""The Skills: line of a ticket: `python3 scripts/lane_tickets.py BODY_FILE [COMMENT_FILE...]` prints the skills the
latest line names: a comment's line, later than the body, replaces the body's."""

import re
import sys

LINE = re.compile(r"^Skills: (.+)$", re.M)


def skills(*notes: str) -> list[str]:
    """The latest Skills: line's names over the notes in order (the body, then each comment), [] with none or
    `Skills: none`."""
    lines = [m.group(1).strip() for n in notes for m in LINE.finditer(n)]
    if not lines or lines[-1] == "none":
        return []
    return [s.strip().strip("`") for s in lines[-1].split(",")]


if __name__ == "__main__":
    print(", ".join(skills(*(open(p).read() for p in sys.argv[1:]))) or "none")
