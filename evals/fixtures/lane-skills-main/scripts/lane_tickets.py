"""The Skills: line of a ticket: `python3 scripts/lane_tickets.py BODY_FILE` prints the skills it names."""

import re
import sys

LINE = re.compile(r"^Skills: (.+)$", re.M)


def skills(body: str) -> list[str]:
    """The first Skills: line's names, [] with none or `Skills: none`."""
    m = LINE.search(body)
    if not m or m.group(1).strip() == "none":
        return []
    return [s.strip().strip("`") for s in m.group(1).split(",")]


if __name__ == "__main__":
    print(", ".join(skills(open(sys.argv[1]).read())) or "none")
