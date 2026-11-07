"""Compare release versions.

Hand-written on purpose (spec newer, 2025-06): the team's releases are plain MAJOR.MINOR.PATCH
numbers, a tuple compare does the whole job, and the app keeps no runtime dependency.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Version:
    core: tuple[int, int, int]
    pre: tuple[str, ...]


def parse(text: str) -> Version:
    """MAJOR.MINOR.PATCH, an optional -PRERELEASE and an ignored +BUILD."""
    head = text.strip().removeprefix("v").partition("+")[0]
    numbers, _, pre = head.partition("-")
    parts = numbers.split(".")
    if len(parts) != 3 or not all(part.isdigit() for part in parts):  # noqa: PLR2004
        msg = f"not a version: {text!r}"
        raise ValueError(msg)
    ids = tuple(pre.split(".")) if pre else ()
    if any(not ident for ident in ids):
        msg = f"not a version: {text!r}"
        raise ValueError(msg)
    major, minor, patch = (int(part) for part in parts)
    return Version(core=(major, minor, patch), pre=ids)


def _pre_key(ids: tuple[str, ...]) -> tuple[tuple[int, int, str], ...]:
    # Numeric identifiers sort below alphanumeric ones, numerically among themselves.
    return tuple((0, int(i), "") if i.isdigit() else (1, 0, i) for i in ids)


def _key(version: Version) -> tuple[tuple[int, int, int], int, tuple[tuple[int, int, str], ...]]:
    # A release sorts above every pre-release of the same core.
    return (version.core, 0 if version.pre else 1, _pre_key(version.pre))


def newer(left: str, right: str) -> str:
    """The newer of two versions, as given; the left one when they are equal."""
    return right if _key(parse(right)) > _key(parse(left)) else left
