"""gh_records.py: the GitHub PR records the covers levers read, validated once at the edge (quality spec
#acceptance-edge-validated) with the kit's pinned jsonschema (pyproject.toml), unknown fields rejected, into typed
records. Every read of `gh pr list` / `gh pr view` output, and of the files that keep it (prs.json,
prs-overlap.json.gz), goes through here; code past it takes these records, never the parsed JSON.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from collections.abc import Callable
from typing import Any, cast

import jsonschema

Schema = dict[str, Any]
SHA: Schema = {"type": "string", "pattern": "^[0-9a-f]{40}$"}
TIME: Schema = {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"}
NUMBER: Schema = {"type": "integer", "minimum": 1}
COMMIT: Schema = {"type": "object", "properties": {"oid": SHA}, "required": ["oid"], "additionalProperties": False}
MERGED: Schema = {"type": "object", "additionalProperties": False, "required": ["number", "mergedAt", "mergeCommit"],
                  "properties": {"number": NUMBER, "mergedAt": TIME, "mergeCommit": COMMIT}}
MERGED_LIST: Schema = {"type": "array", "items": MERGED}
VIEW: Schema = {"type": "object", "additionalProperties": False, "required": ["number", "mergeCommit"],
                "properties": {"number": NUMBER, "mergeCommit": COMMIT}}
ANY_REQUIRED = ["number", "state", "createdAt", "mergedAt", "closedAt", "mergeCommit", "headRefOid"]
ANY_PROPS: Schema = {"number": NUMBER, "state": {"enum": ["OPEN", "CLOSED", "MERGED"]}, "createdAt": TIME,
                     "mergedAt": {"anyOf": [TIME, {"type": "null"}]}, "closedAt": {"anyOf": [TIME, {"type": "null"}]},
                     "mergeCommit": {"anyOf": [COMMIT, {"type": "null"}]}, "headRefOid": SHA}
ANY_LIST: Schema = {"type": "array", "items": {"type": "object", "additionalProperties": False,
                                               "required": ANY_REQUIRED, "properties": ANY_PROPS}}
OVERLAP_PR: Schema = {"type": "object", "additionalProperties": False, "required": [*ANY_REQUIRED, "files"],
                      "properties": {**ANY_PROPS, "base": {"type": "string"}, "head": SHA,
                                     "files": {"anyOf": [{"type": "array", "items": {"type": "string"}},
                                                         {"type": "null"}]}}}
OVERLAP: Schema = {"type": "object", "additionalProperties": False, "required": ["fetched", "first_merged", "prs"],
                   "properties": {"fetched": TIME, "first_merged": TIME, "prs": {"type": "array", "items": OVERLAP_PR}}}


def valid(text: str | bytes, schema: Schema, what: str) -> Any:
    """TEXT parsed as JSON and checked against SCHEMA; a mismatch raises SystemExit naming WHAT and the error."""
    data = json.loads(text)
    try:
        check = cast("Callable[[object], None]", jsonschema.Draft202012Validator(schema).validate)
        check(data)
    except jsonschema.ValidationError as e:
        raise SystemExit(f"gh_records: {what}: {e.message} at {list(e.absolute_path)}") from e
    return data


@dataclass(frozen=True)
class MergedPR:
    """A merged PR: number, merge time, merge commit."""

    number: int
    merged_at: str
    merge: str

    def raw(self) -> dict[str, object]:
        return {"number": self.number, "mergedAt": self.merged_at, "mergeCommit": {"oid": self.merge}}


@dataclass(frozen=True)
class AnyPR:
    """A PR in any state, with the files it changed and the range they come from (None: its head not fetchable)."""

    number: int
    state: str
    created_at: str
    merged_at: str | None
    closed_at: str | None
    merge: str | None
    head_ref: str
    base: str | None = None
    head: str | None = None
    files: tuple[str, ...] | None = None

    def end(self, now: str) -> str:
        return self.merged_at or self.closed_at or now

    def raw(self) -> dict[str, object]:
        out: dict[str, object] = {"number": self.number, "state": self.state, "createdAt": self.created_at,
                                  "mergedAt": self.merged_at, "closedAt": self.closed_at,
                                  "mergeCommit": {"oid": self.merge} if self.merge else None,
                                  "headRefOid": self.head_ref, "files": list(self.files) if self.files is not None
                                  else None}
        if self.base is not None:
            out["base"] = self.base
        if self.head is not None:
            out["head"] = self.head
        return out


def merged_list(text: str | bytes, what: str) -> list[MergedPR]:
    rows = cast("list[dict[str, Any]]", valid(text, MERGED_LIST, what))
    return [MergedPR(int(r["number"]), str(r["mergedAt"]), str(r["mergeCommit"]["oid"])) for r in rows]


def view(text: str | bytes, what: str) -> MergedPR:
    r = cast("dict[str, Any]", valid(text, VIEW, what))
    return MergedPR(int(r["number"]), "", str(r["mergeCommit"]["oid"]))


def _any(r: dict[str, Any]) -> AnyPR:
    mc = cast("dict[str, Any] | None", r.get("mergeCommit"))
    files = cast("list[str] | None", r.get("files"))
    return AnyPR(int(r["number"]), str(r["state"]), str(r["createdAt"]), r.get("mergedAt"), r.get("closedAt"),
                 str(mc["oid"]) if mc else None, str(r["headRefOid"]), r.get("base"), r.get("head"),
                 tuple(files) if files is not None else None)


def any_list(text: str | bytes, what: str) -> list[AnyPR]:
    return [_any(r) for r in cast("list[dict[str, Any]]", valid(text, ANY_LIST, what))]


@dataclass(frozen=True)
class Overlap:
    """prs-overlap.json.gz: when it was fetched, the earliest merge of the 60, every overlapping PR."""

    fetched: str
    first_merged: str
    prs: tuple[AnyPR, ...]

    def dumps(self) -> str:
        return json.dumps({"fetched": self.fetched, "first_merged": self.first_merged,
                           "prs": [p.raw() for p in self.prs]}, indent=1) + "\n"


def overlap(text: str | bytes, what: str) -> Overlap:
    d = cast("dict[str, Any]", valid(text, OVERLAP, what))
    return Overlap(str(d["fetched"]), str(d["first_merged"]),
                   tuple(_any(r) for r in cast("list[dict[str, Any]]", d["prs"])))


__all__ = ["AnyPR", "MergedPR", "Overlap", "any_list", "asdict", "merged_list", "overlap", "view"]
