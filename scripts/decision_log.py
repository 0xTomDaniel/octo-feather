#!/usr/bin/env python3
"""The decision-log rule: a function of a repo dir and its tracked files, returning a Report.

Imported by name, never by path (pyproject.toml, [tool.pytest.ini_options] pythonpath). Imports
the kit's pinned jsonschema at its top, so it is its own module (check_rules runs on bare python3);
the command, scripts/check-decision-log, re-execs itself in the kit's environment without it.

Interface:

    check_decision_logs(root, tracked) -> Report
        Every tracked file named decisions.jsonl, anywhere in the repo, holds one JSON object per
        line that satisfies schemas/decision-log.schema.json (quality spec
        #acceptance-decision-log-schema, #decision-log, docs/adr/0010). ROOT the repo dir, the
        schema and the logs read under it; TRACKED its `git ls-files` paths. Each failure an err
        line naming FILE:LINE and the field, code 1. The schema file is the one source for the
        field list. jsonschema enforces structure, with a compatibility metaschema restricting the
        accepted schema vocabulary so previously unusable schemas still fail closed. Patterns run
        in node's RegExp (Unicode mode), one node call for every line. Fails closed: an unreadable
        log fails (code 1); an unusable schema, a missing or failing node (its stderr kept as err
        lines) fails with code 2, never reads as ok. Else the out line
        `decision-log: ok (N files)`, code 0.
"""

__all__ = ["check_decision_logs"]

import json
import shutil
import subprocess
from collections.abc import Callable, Iterator, Sequence
from pathlib import Path, PurePosixPath
from typing import Any, cast

import jsonschema
from check_rules import Report, Stream
from jsonschema import validators
from jsonschema.protocols import Validator

# jsonschema's extension factory has no typed signature; confine that boundary.
extension_api: Any = validators

SCHEMA = "schemas/decision-log.schema.json"
NAME = "decisions.jsonl"
TOP_KEYS = {
    "$schema",
    "$id",
    "title",
    "description",
    "type",
    "required",
    "properties",
    "additionalProperties",
}
FIELD_KEYS = {"description", "type", "minLength", "pattern"}
PROPERTY_PATH_DEPTH = 2

# This is the existing CLI's schema vocabulary, not another instance validator.
# jsonschema validates both this contract and each decision object.
SCHEMA_CONTRACT = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        **{k: {} for k in TOP_KEYS},
        "type": {"const": "object"},
        "required": {"type": "array", "items": {"type": "string"}, "uniqueItems": True},
        "additionalProperties": {"type": "boolean"},
        "properties": {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "description": {},
                    "type": {"const": "string"},
                    "minLength": {"type": "integer", "minimum": 0},
                    "pattern": {"type": "string"},
                },
            },
        },
    },
    "required": ["type"],
}
# Each pattern compiled with new RegExp(p, "u"), its error kept; each value tested, in order.
# Property names are schema data: pairs and Maps only, never a plain object keyed by them.
NODE_JS = r"""
const q = JSON.parse(require("fs").readFileSync(0, "utf8")), rx = new Map(), bad = new Map();
for (const [k, p] of q.patterns) {
  try { rx.set(k, new RegExp(p, "u")); } catch (e) { bad.set(k, e.message); }
}
const test = bad.size ? [] : q.values.map(([k, v]) => rx.get(k).test(v));
process.stdout.write(JSON.stringify({bad: [...bad], test}));
"""


class SchemaError(Exception):
    pass


def load_schema(root: Path) -> dict[str, Any]:
    with (root / SCHEMA).open(encoding="utf-8") as fh:
        s: dict[str, Any] = json.load(fh, object_pairs_hook=no_duplicates)

    # The old schema boundary rejects 1.0 as a minLength, unlike JSON Schema's
    # mathematical integer type. Keep that spelling constraint at this boundary.
    def integer(_checker: object, value: object) -> bool:
        return type(value) is int

    contract_validator: type[Validator] = extension_api.extend(
        jsonschema.Draft202012Validator,
        type_checker=jsonschema.Draft202012Validator.TYPE_CHECKER.redefine("integer", integer),
    )

    def order(error: jsonschema.ValidationError) -> tuple[int, int, int]:
        path = [str(part) for part in error.absolute_path]
        if not path:
            return (0 if error.validator in ("type", "additionalProperties") else 1, 0, 0)
        rank = {"type": 1, "required": 2, "properties": 3, "additionalProperties": 4}[path[0]]
        if len(path) < PROPERTY_PATH_DEPTH:
            return (rank, 0, 0)
        key = path[2] if len(path) > PROPERTY_PATH_DEPTH else ""
        return (
            5,
            list(s["properties"]).index(path[1]),
            {"type": 1, "minLength": 2, "pattern": 3}.get(key, 0),
        )

    for e in sorted(contract_validator(SCHEMA_CONTRACT).iter_errors(s), key=order):
        raise SchemaError(contract_problem(s, e))
    return s


def contract_problem(  # noqa: PLR0911  one return per contract part, in its order
    s: dict[str, Any], e: jsonschema.ValidationError
) -> str:
    path = [str(part) for part in e.absolute_path]
    if not path:
        if e.validator == "type":
            return "not a JSON object"
        if e.validator == "additionalProperties":
            return f"unsupported keyword {min(set(s) - TOP_KEYS)}"
        return 'type must be "object"'
    if path[0] == "type":
        return 'type must be "object"'
    if path[0] == "required":
        return "required must be a list of distinct names"
    if path[0] == "additionalProperties":
        return "additionalProperties must be true or false"
    if len(path) == 1:
        return "properties must be an object"
    name = path[1]
    prefix = f"property {name}: "
    if len(path) == PROPERTY_PATH_DEPTH:
        extra = min(set(s["properties"][name]) - FIELD_KEYS) if e.validator != "type" else ""
        detail = "form" if e.validator == "type" else "keyword " + extra
        return prefix + "unsupported " + detail
    key = path[2]
    detail = {
        "type": f"unsupported type {e.instance!r}",
        "minLength": "minLength must be a non-negative integer",
        "pattern": "pattern must be a string",
    }[key]
    return prefix + detail


def no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    seen: dict[str, Any] = {}
    for k, v in pairs:
        if k in seen:
            msg = f"duplicate key {k}"
            raise ValueError(msg)
        seen[k] = v
    return seen


def no_constant(name: str) -> None:
    msg = f"{name} is not JSON"
    raise ValueError(msg)


def line_problems(  # noqa: C901  the line's problems in the order the command prints them
    raw: bytes, schema: dict[str, Any], match: Callable[[str, str], bool]
) -> list[str]:
    """Problems of one log line; MATCH(name, value): does value match property name's pattern."""
    try:
        text = raw.decode("utf-8")
        obj: Any = json.loads(text, object_pairs_hook=no_duplicates, parse_constant=no_constant)
    except UnicodeDecodeError:
        return ["not UTF-8"]
    except ValueError as e:  # json.JSONDecodeError is a ValueError
        return [f"invalid JSON: {e}"]
    props: dict[str, dict[str, Any]] = schema.get("properties", {})

    # Python re differs on whitespace, classes, unmatched backreferences and ECMA
    # syntax. Keep Node's real Unicode RegExp, including compilation without logs.
    def pattern(
        _validator: Validator, regex: str, value: object, field_schema: dict[str, Any]
    ) -> Iterator[jsonschema.ValidationError]:
        length = {"minLength": field_schema.get("minLength", 0)}
        length_validator = cast("Validator", jsonschema.Draft202012Validator(length))
        if isinstance(value, str) and not list(length_validator.iter_errors(value)):
            name = next(k for k, p in props.items() if p is field_schema)
            if not match(name, value):
                yield jsonschema.ValidationError(f"{name} does not match {regex}")

    draft = jsonschema.Draft202012Validator
    validator: type[Validator] = extension_api.extend(draft, {"pattern": pattern})
    errors = list(validator(schema).iter_errors(obj))
    if any(e.validator == "type" and not e.path for e in errors):
        return [f"not a JSON object (a {type(obj).__name__})"]
    out = [
        f"missing {name}"
        for name in schema.get("required", [])
        if any(e.validator == "required" for e in errors) and name not in obj
    ]
    for name in props:
        for e in errors:
            if list(e.path) != [name]:
                continue
            if e.validator == "type":
                out.append(f"{name} must be a {e.validator_value}")
            elif e.validator == "minLength":
                out.append(f"empty {name}")
            elif e.validator == "pattern":
                out.append(e.message)
    if any(e.validator == "additionalProperties" for e in errors):
        out += [f"unknown field {k}" for k in sorted(set(obj) - set(props))]
    return out


class NodeError(Exception):
    """Node could not answer: the message, and node's stderr lines, if any."""

    def __init__(self, message: str, stderr: bytes = b"") -> None:
        super().__init__(message)
        text = stderr.decode("utf-8", "replace")
        self.stderr = text.removesuffix("\n").split("\n") if text else []


def node_tests(patterns: dict[str, str], values: list[tuple[str, str]]) -> list[bool]:
    """Node's verdict on PATTERNS {property: pattern} and VALUES [(property, value)]: the list of
    match results, SchemaError naming an invalid pattern, or NodeError when node cannot answer."""
    node = shutil.which("node")
    if not node:
        msg = "node not found on PATH: install node (Pi needs it too)"
        raise NodeError(msg)
    query = json.dumps({"patterns": list(patterns.items()), "values": values}).encode()
    try:
        run = subprocess.run([node, "-e", NODE_JS], input=query, capture_output=True, check=False)
    except OSError as e:
        raise NodeError(str(e)) from None
    if run.returncode != 0:
        msg = f"node exited {run.returncode}"
        raise NodeError(msg, run.stderr)
    try:
        res = json.loads(run.stdout)
        bad: dict[str, str] = dict(res["bad"])
        test: object = res["test"]
    except (ValueError, KeyError, TypeError) as e:
        msg = f"node gave no usable answer: {e}"
        raise NodeError(msg) from None
    if bad:
        name = min(bad)
        msg = f"property {name}: pattern {patterns[name]!r}: {bad[name]}"
        raise SchemaError(msg)
    verdicts = cast("list[object]", test) if isinstance(test, list) else None
    if (
        verdicts is None
        or len(verdicts) != len(values)
        or not all(isinstance(t, bool) for t in verdicts)
    ):
        msg = "node gave no usable answer: wrong result count"
        raise NodeError(msg)
    return cast("list[bool]", verdicts)


def read_logs(root: Path, logs: list[str]) -> list[tuple[str, list[bytes] | OSError]]:
    """Each log's lines (the final newline ends the last line, it is not a line), or its error."""
    read: list[tuple[str, list[bytes] | OSError]] = []
    for path in logs:
        try:
            rows = (root / path).read_bytes().split(b"\n")
        except OSError as e:
            read.append((path, e))
            continue
        if rows[-1] == b"":
            rows.pop()
        read.append((path, rows))
    return read


def log_problems(
    rows: list[bytes] | OSError, schema: dict[str, Any], match: Callable[[str, str], bool], why: str
) -> list[str]:
    """One log's problems, each as printed after its path; WHY ends each line's problem."""
    if isinstance(rows, OSError):
        return [f": cannot read: {rows}"]
    return [
        f":{n}: {p} ({why})"
        for n, raw in enumerate(rows, 1)
        for p in line_problems(raw, schema, match)
    ]


def pattern_results(
    read: list[tuple[str, list[bytes] | OSError]], schema: dict[str, Any]
) -> list[bool]:
    """Node's verdict on each value a pattern tests, in line order. Two passes over the same lines:
    this one collects the values, node tests them in one call; the caller's reads the verdicts."""
    values: list[tuple[str, str]] = []
    for raw in (raw for _, rows in read if isinstance(rows, list) for raw in rows):
        line_problems(raw, schema, lambda name, v: values.append((name, v)) or True)
    props: dict[str, dict[str, Any]] = schema.get("properties", {})
    patterns = {name: p["pattern"] for name, p in props.items() if "pattern" in p}
    return node_tests(patterns, values) if patterns else []


def check_decision_logs(root: Path, tracked: Sequence[str]) -> Report:
    lines: list[tuple[Stream, bytes]] = []

    def say(stream: Stream, text: str) -> None:
        lines.append((stream, text.encode("utf-8", "surrogateescape")))

    def unusable(e: Exception) -> Report:
        why = "fix the schema, the check cannot pass"
        say("err", f"check-decision-log: {SCHEMA}: unusable schema: {e}; {why}")
        return Report(tuple(lines), 2)

    try:
        schema = load_schema(root)
    except (OSError, ValueError, SchemaError) as e:
        return unusable(e)
    logs = sorted(p for p in tracked if PurePosixPath(p).name == NAME)
    fields = ", ".join(schema.get("required", []))
    read = read_logs(root, logs)
    try:
        results = iter(pattern_results(read, schema))
    except SchemaError as e:
        return unusable(e)
    except NodeError as e:
        for row in e.stderr:
            say("err", row)
        say("err", f"check-decision-log: {e}; the check cannot pass")
        return Report(tuple(lines), 2)
    why = f"each line is one JSON object with string fields {fields}; {SCHEMA}"
    for path, rows in read:
        for problem in log_problems(rows, schema, lambda _name, _v: next(results), why):
            say("err", f"check-decision-log: {path}{problem}")
    if lines:  # every line so far names a bad or unreadable log
        return Report(tuple(lines), 1)
    say("out", f"decision-log: ok ({len(logs)} files)")
    return Report(tuple(lines), 0)
