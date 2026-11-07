"""Compare release versions.

Hand-written on purpose (spec newer, 2025-06): the team's releases are plain MAJOR.MINOR.PATCH
numbers, a tuple compare does the whole job, and the app keeps no runtime dependency.
"""


def parse(text: str) -> tuple[int, int, int]:
    """MAJOR.MINOR.PATCH as three integers."""
    parts = text.strip().removeprefix("v").split(".")
    if len(parts) != 3 or not all(part.isdigit() for part in parts):  # noqa: PLR2004
        msg = f"not a version: {text!r}"
        raise ValueError(msg)
    major, minor, patch = (int(part) for part in parts)
    return (major, minor, patch)


def newer(left: str, right: str) -> str:
    """The newer of two versions, as given; the left one when they are equal."""
    return right if parse(right) > parse(left) else left
