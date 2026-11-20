"""The decision-log rule (quality spec #acceptance-decision-log-schema), in-process at its
interface, `check_decision_logs` of scripts/decision_log.py (its module docstring; ticket #1116,
seams agreed on it before any test): a bad line in a tracked decisions.jsonl fails naming
FILE:LINE and the field; valid, untracked and other-named logs pass; the schema drives fields,
extras and the pattern dialect (node's RegExp); an unusable schema or an unreadable log fails
closed. Each case writes its logs, and the schema, into a scratch root and checks the tracked
paths given. The cases are tests/check-decision-log.sh's planted ones (parity:
tests/parity/check-decision-log/); its command test keeps the wiring: git's listing, the
printing, the bootstrap, broken tools, the recipe in the gate.
"""

import json
from pathlib import Path
from typing import Any

from decision_log import check_decision_logs
from testkit import ROOT

SCHEMA = "schemas/decision-log.schema.json"
KIT_SCHEMA: dict[str, Any] = json.loads((ROOT / SCHEMA).read_text(encoding="utf-8"))
L, N = "decisions.jsonl", "docs/lane/run/decisions.jsonl"
HEAD = '"ts":"2026-10-19T00:00:00Z","agent":"implementer","phase":"handoff","decision":"ready"'
TAIL = '"evidence":"just check","result":"pending"'
OK = f'{{{HEAD},"why":"gate green",{TAIL}}}'
NO_WHY = f"{{{HEAD},{TAIL}}}"
UNUSABLE = f"check-decision-log: {SCHEMA}: unusable schema"


def why(value: str) -> str:
    """A log line whose why is VALUE, as JSON text (escapes kept)."""
    return f'{{{HEAD},"why":"{value}",{TAIL}}}'


def check(
    root: Path,
    logs: dict[str, bytes],
    *,
    schema: object = KIT_SCHEMA,
    untracked: tuple[str, ...] = (),
) -> tuple[int, list[str]]:
    """LOGS written under ROOT and tracked (but UNTRACKED), SCHEMA as the schema file (None: none);
    the Report's code and its lines, each `stream: text`."""
    (root / "schemas").mkdir(exist_ok=True)
    (root / SCHEMA).unlink(missing_ok=True)
    if schema is not None:
        text = schema if isinstance(schema, str) else json.dumps(schema)
        (root / SCHEMA).write_text(text, encoding="utf-8")
    for path, content in logs.items():
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).write_bytes(content)
    try:
        report = check_decision_logs(root, ["README.md", *(p for p in logs if p not in untracked)])
    finally:
        for path in logs:
            (root / path).unlink()
    return report.code, [f"{s}: {line.decode('utf-8', 'replace')}" for s, line in report.lines]


def expect(root: Path, logs: dict[str, bytes], *reports: str, schema: object = KIT_SCHEMA) -> None:
    """The logs fail (code 1), each REPORT line (`FILE:LINE: problem`) printed, never ok."""
    code, lines = check(root, logs, schema=schema)
    assert code == 1, (logs, lines)
    for r in reports:
        assert any(line.startswith(f"err: check-decision-log: {r}") for line in lines), (r, lines)
    assert not any(line.startswith("out: decision-log: ok") for line in lines), lines


def allow(
    root: Path,
    logs: dict[str, bytes],
    files: int = 1,
    *,
    schema: object = KIT_SCHEMA,
    untracked: tuple[str, ...] = (),
) -> None:
    """The logs pass: only the ok line, FILES the tracked logs, code 0."""
    ok = (0, [f"out: decision-log: ok ({files} files)"])
    assert check(root, logs, schema=schema, untracked=untracked) == ok, logs


def with_pattern(pattern: str) -> dict[str, Any]:
    """The kit schema with why's pattern set to PATTERN."""
    s = json.loads(json.dumps(KIT_SCHEMA))
    s["properties"]["why"]["pattern"] = pattern
    return s


def test_criterion_lines_fail(tmp_path: Path) -> None:
    """Missing why, invalid JSON, non-object, a nested path: each named FILE:LINE."""
    expect(tmp_path, {L: f"{NO_WHY}\n".encode()}, f"{L}:1: missing why")
    expect(tmp_path, {L: f'{OK}\n{{{HEAD},"why":"x",{TAIL}\n'.encode()}, f"{L}:2: invalid JSON")
    expect(tmp_path, {L: b'["why"]\n'}, f"{L}:1: not a JSON object")
    expect(tmp_path, {N: f"{OK}\n{OK}\n{NO_WHY}\n".encode()}, f"{N}:3: missing why")


def test_valid_logs_pass(tmp_path: Path) -> None:
    """One line, several, nested, no final newline, CRLF, any key order, unicode text."""
    allow(tmp_path, {L: f"{OK}\n".encode()})
    allow(tmp_path, {N: f"{OK}\n{OK}\n{OK}\n".encode()})
    allow(tmp_path, {L: OK.encode()})
    allow(tmp_path, {L: f"{OK}\r\n{OK}\r\n".encode()})
    reordered = (
        '{"result":"r","why":"w","evidence":"e","decision":"d","phase":"p","agent":"a","ts":"t"}'
    )
    allow(tmp_path, {L: f"{reordered}\n".encode()})
    allow(tmp_path, {L: why("tab\\tand newline\\n, caf\u00e9").encode() + b"\n"})


def test_out_of_scope_logs_pass(tmp_path: Path) -> None:
    """Exact name decisions.jsonl, tracked only; no log at all passes."""
    allow(tmp_path, {}, files=0)
    allow(tmp_path, {L: f"{NO_WHY}\n".encode()}, files=0, untracked=(L,))
    allow(tmp_path, {"decisions.jsonl.bak": f"{NO_WHY}\n".encode()}, files=0)
    allow(tmp_path, {"Decisions.jsonl": f"{NO_WHY}\n".encode()}, files=0)
    allow(tmp_path, {"docs/my-decisions.jsonl": b"not json\n"}, files=0)


def test_only_bad_lines_and_logs_named(tmp_path: Path) -> None:
    """Mixed lines in one log: lines 2 and 4 only; a good and a bad log: the bad one only."""
    mixed = f"{OK}\n{NO_WHY}\n{OK}\n{why('')}\n{OK}\n".encode()
    code, lines = check(tmp_path, {L: mixed})
    assert code == 1, lines
    assert [line.split(" (")[0] for line in lines] == [
        f"err: check-decision-log: {L}:2: missing why",
        f"err: check-decision-log: {L}:4: empty why",
    ], lines
    code, lines = check(tmp_path, {L: f"{OK}\n".encode(), N: f"{OK}\n{OK}\n[]\n".encode()})
    assert code == 1, lines
    assert [line.split(" (a")[0] for line in lines] == [
        f"err: check-decision-log: {N}:3: not a JSON object"
    ]


def test_adversarial_forms_fail(tmp_path: Path) -> None:
    """Variants of why, empty, blank, null and non-string values, a duplicate key, an extra field,
    every non-object JSON value, a blank or whitespace line, a BOM, a NaN, non-UTF-8 bytes, two
    objects on one line, an empty object."""
    cases: list[tuple[bytes, tuple[str, ...]]] = [
        (
            f'{{{HEAD},"Why":"x",{TAIL}}}\n'.encode(),
            (f"{L}:1: missing why", f"{L}:1: unknown field Why"),
        ),
        (f'{{{HEAD},"why ":"x",{TAIL}}}\n'.encode(), (f"{L}:1: missing why",)),
        (f'{{{HEAD},"whys":"x",{TAIL}}}\n'.encode(), (f"{L}:1: missing why",)),
        (why("").encode() + b"\n", (f"{L}:1: empty why",)),
        (why("  \\t ").encode() + b"\n", (f"{L}:1: why does not match",)),
        (f'{{{HEAD},"why":null,{TAIL}}}\n'.encode(), (f"{L}:1: why must be a string",)),
        (f'{{{HEAD},"why":1,{TAIL}}}\n'.encode(), (f"{L}:1: why must be a string",)),
        (f'{{{HEAD},"why":["x"],{TAIL}}}\n'.encode(), (f"{L}:1: why must be a string",)),
        (f'{{{HEAD},"why":{{"why":"x"}},{TAIL}}}\n'.encode(), (f"{L}:1: why must be a string",)),
        (
            f'{{{HEAD},"why":"x","why":"",{TAIL}}}\n'.encode(),
            (f"{L}:1: invalid JSON: duplicate key why",),
        ),
        (f'{{{HEAD},"why":"x",{TAIL},"note":"y"}}\n'.encode(), (f"{L}:1: unknown field note",)),
        (b'"why"\n', (f"{L}:1: not a JSON object",)),
        (b"null\n", (f"{L}:1: not a JSON object",)),
        (b"42\n", (f"{L}:1: not a JSON object",)),
        (f"{OK}\n\n{OK}\n".encode(), (f"{L}:2: invalid JSON",)),
        (f"{OK}\n  \n".encode(), (f"{L}:2: invalid JSON",)),
        (b"\xef\xbb\xbf" + f"{OK}\n".encode(), (f"{L}:1: invalid JSON",)),
        (f'{{{HEAD},"why":"x",{TAIL},"n":NaN}}\n'.encode(), (f"{L}:1: invalid JSON",)),
        (f'{{{HEAD},"why":"'.encode() + b"\xff" + f'",{TAIL}}}\n'.encode(), (f"{L}:1: not UTF-8",)),
        (f"{OK} {OK}\n".encode(), (f"{L}:1: invalid JSON",)),
        (b"{}\n", (f"{L}:1: missing ts", f"{L}:1: missing why", f"{L}:1: missing result")),
    ]
    for content, reports in cases:
        expect(tmp_path, {L: content}, *reports)


def test_pattern_dialect_is_node(tmp_path: Path) -> None:
    """The schema's patterns in node's Unicode RegExp (#142, #121 D9): \\S, \\d, \\w, \\b, ., $,
    [\\S], [^\\s] and an unmatched backreference, as node reads them, not Python's re."""
    result = f'{{{HEAD},"why":"x","evidence":"e","result":"\\ufeff"}}\n'.encode()
    expect(tmp_path, {L: result}, f"{L}:1: result does not match")
    expect(
        tmp_path,
        {L: why("\\u3000\\u00a0\\u2028\\u000b").encode() + b"\n"},
        f"{L}:1: why does not match",
    )
    for c in ("001c", "001d", "001e", "001f", "0085", "200b", "180e"):
        allow(tmp_path, {L: why(f"\\u{c}").encode() + b"\n"})
    for pattern, fail, passes in [
        ("^\\d+$", ["\\u0663", "1\\n"], ["12"]),
        ("^\\w\\b", ["\\u00e9"], ["a\\u00e9", "a b"]),
        ("^a.b$", ["a\\u2028b"], ["a\\u0085b"]),
        ("^[\\S]+$", ["a\\ufeff"], ["a\\u001c"]),
        ("^[^\\s]+$", ["a\\ufeff"], ["a\\u0085"]),
        ("^(a|(b))\\2c$", ["bc"], ["ac"]),
    ]:
        schema = with_pattern(pattern)
        for value in fail:
            expect(
                tmp_path,
                {L: why(value).encode() + b"\n"},
                f"{L}:1: why does not match",
                schema=schema,
            )
        for value in passes:
            allow(tmp_path, {L: why(value).encode() + b"\n"}, schema=schema)


def test_unusable_pattern_refused(tmp_path: Path) -> None:
    """A pattern node refuses fails closed (code 2) naming the property and node's error; a property
    named __proto__ is schema data like any other: refused with no log, its valid pattern tested."""
    for pattern, value, error in [
        ("^a++$", "a", "Invalid regular expression: /^a++$/u: Nothing to repeat"),
        (
            "^a{\u0661}$",
            "a{\\u0661}",
            "Invalid regular expression: /^a{\u0661}$/u: Incomplete quantifier",
        ),
    ]:
        code, lines = check(
            tmp_path, {L: why(value).encode() + b"\n"}, schema=with_pattern(pattern)
        )
        refused = f"err: {UNUSABLE}: property why: pattern {pattern!r}: {error}"
        assert code == 2, lines
        assert any(line.startswith(refused) for line in lines), lines
    proto = json.loads(json.dumps(KIT_SCHEMA))
    proto["properties"]["__proto__"] = {"type": "string", "pattern": "^a++$"}
    code, lines = check(tmp_path, {}, schema=proto)
    node_error = "Invalid regular expression: /^a++$/u: Nothing to repeat"
    refused = f"err: {UNUSABLE}: property __proto__: pattern '^a++$': {node_error}"
    assert code == 2, lines
    assert any(line.startswith(refused) for line in lines), lines
    proto["properties"]["__proto__"]["pattern"] = "^a$"
    line = f'{{{HEAD},"why":"x",{TAIL},"__proto__":"%s"}}\n'
    expect(
        tmp_path, {L: (line % "b").encode()}, f"{L}:1: __proto__ does not match ^a$", schema=proto
    )
    allow(tmp_path, {L: (line % "a").encode()}, schema=proto)


def test_schema_drives_fields_and_extras(tmp_path: Path) -> None:
    """The schema file is the one source for the field list and the extra-field policy."""
    ticket = json.loads(json.dumps(KIT_SCHEMA))
    ticket["required"].append("ticket")
    ticket["properties"]["ticket"] = {"type": "string"}
    expect(tmp_path, {L: f"{OK}\n".encode()}, f"{L}:1: missing ticket", schema=ticket)
    allow(tmp_path, {L: f'{{{HEAD},"why":"x",{TAIL},"ticket":"#44"}}\n'.encode()}, schema=ticket)
    ticket["additionalProperties"] = True
    allow(
        tmp_path,
        {L: f'{{{HEAD},"why":"x",{TAIL},"ticket":"#44","note":"y"}}\n'.encode()},
        schema=ticket,
    )


def test_unusable_schema_fails_closed(tmp_path: Path) -> None:
    """Invalid JSON, missing, or a keyword the validator does not enforce: fails with no log, never
    ok."""
    req = '{"type": "object", "required": ["why"], '
    for schema in [
        None,
        '{"type": "object", "required": ["why"',
        "[]",
        '{"type": "object", "required": ["why", "why"]}',
        '{"type": "object", "properties": {"why": {"minLength": 1.0}}}',
        '{"type": "object", "properties": {"why": {"minLength": true}}}',
        req + '"properties": {"why": {"type": "string", "maxLength": 9}}}',
        req + '"patternProperties": {}}',
        req + '"properties": {"why": {"type": ["string", "null"]}}}',
        req + '"properties": {"why": {"type": "string", "pattern": "("}}}',
        req + '"additionalProperties": {"type": "string"}}',
        req + '"properties": {"why": {"type": "string", "pattern": "(?P<a>x)"}}}',
        req + '"properties": {"why": {"type": "string", "pattern": "x\\\\Z"}}}',
    ]:
        code, lines = check(tmp_path, {}, schema=schema)
        assert code != 0, (schema, lines)
        assert any(line.startswith(f"err: {UNUSABLE}") for line in lines), (schema, lines)
        assert not any(line.startswith("out: decision-log: ok") for line in lines), (schema, lines)


def test_unreadable_log_fails_closed(tmp_path: Path) -> None:
    """A tracked log that cannot be read (a dangling link) fails naming it, never ok."""
    (tmp_path / SCHEMA).parent.mkdir()
    (tmp_path / SCHEMA).write_text(json.dumps(KIT_SCHEMA), encoding="utf-8")
    (tmp_path / L).symlink_to("missing")
    report = check_decision_logs(tmp_path, [L])
    assert report.code == 1, report
    assert report.lines[0][1].startswith(f"check-decision-log: {L}: cannot read".encode()), report
    assert not any(line.startswith(b"decision-log: ok") for _, line in report.lines), report
