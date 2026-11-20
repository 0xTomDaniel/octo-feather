"""The testkit's one typed walk over JSON a kit command wrote (#998): a value at a path of object
keys and list indexes, a list, an object's keys, a key that may be absent. A missing step fails
naming its path. Kit test code is stdlib-only (AGENTS.md Rules), so no schema library: every
scenario reads a run's JSON through this walk (install_check.field, a string at a path, is built
on it), never by casts or shape checks of its own."""

from __future__ import annotations

from typing import cast


def at(v: object, *keys: str | int, where: str = "") -> object:
    """V's value at KEYS, a JSON path of object keys and list indexes; a missing step fails
    naming WHERE and the path to it."""
    for i, k in enumerate(keys):
        path = f"{where}: " * bool(where) + ".".join(map(str, keys[: i + 1]))
        if isinstance(k, int):
            assert isinstance(v, list), f"{path}: not in a JSON list: {v!r}"
            items = cast("list[object]", v)
            assert len(items) > k, f"{path}: no item"
            v = items[k]
        else:
            assert isinstance(v, dict), f"{path}: not in a JSON object: {v!r}"
            d = cast("dict[str, object]", v)
            assert k in d, f"no {path}"
            v = d[k]
    return v


def seq(v: object) -> list[object]:
    """V, a JSON list."""
    assert isinstance(v, list), f"no JSON list: {v!r}"
    return cast("list[object]", v)


def keys(v: object) -> set[str]:
    """V's keys, a JSON object."""
    assert isinstance(v, dict), f"no JSON object: {v!r}"
    return set(cast("dict[str, object]", v))


def get(v: object, k: str) -> object:
    """V's K, None when V is no JSON object or lacks it."""
    return cast("dict[str, object]", v).get(k) if isinstance(v, dict) else None
