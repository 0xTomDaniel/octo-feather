"""The scenarios of tests/gate/kit/test_check_decision_log.py (its items), this file their command
(testkit.main): scripts/check-decision-log (quality #acceptance-decision-log-schema), the command
`just check-decision-log` runs, run as a command in a git copy of the kit's tracked files
(testkit.kit_repo, prepared once per gate run) by the interpreter running this file (the kit's
environment, as the gate's PATH gives the recipe's python3); the recipe itself where it is the
surface: a broken python3, and `just check`.

A tracked decisions.jsonl, at the root or nested, with a bad line fails naming FILE:LINE and the
field; valid, untracked and other-named logs pass. Logs judged under one schema are planted
together, each in its own dir, and judged by one run: each failing log named by its own lines
(an exact count where the old case counted), each passing one never named; the passing ones
alone keep the check green. The schema drives the fields, the extra-field policy and the
pattern dialect (node's RegExp, Unicode mode); an unusable schema, an unreadable log and a
broken python3, git or node fail closed, never decision-log: ok. That `just check` runs it on a
nested log line missing why: tests/gate/kit/check_refs.py in_gate (one gate run for three
recipes).
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys

from testkit import Scratch, kit_repo, main, tool_homes

SCHEMA = "schemas/decision-log.schema.json"
L = "decisions.jsonl"
N = "docs/lane/run/decisions.jsonl"
HEAD = '"ts":"2026-10-19T00:00:00Z","agent":"implementer","phase":"handoff","decision":"ready"'
TAIL = '"evidence":"just check","result":"pending"'
OK = f'{{{HEAD},"why":"gate green",{TAIL}}}'
NO_WHY = f"{{{HEAD},{TAIL}}}"


def why(value: str) -> bytes:
    """A line whose why is VALUE (JSON text, as written)."""
    return f'{{{HEAD},"why":{value},{TAIL}}}\n'.encode()


def u(s: str) -> bytes:
    return s.encode()


# Each log by its path: its bytes and, failing, the report lines it is named by (each printed
# after "check-decision-log: "; "" a line not counted), under the default schema.
FAIL: dict[str, tuple[bytes, list[str]]] = {
    # The criterion cases: missing why, invalid JSON, non-object, nested path.
    L: (u(f"{NO_WHY}\n"), ["1: missing why"]),
    "e2/" + L: (u(f'{OK}\n{{{HEAD},"why":"x",{TAIL}\n'), ["2: invalid JSON"]),
    "e3/" + L: (b'["why"]\n', ["1: not a JSON object"]),
    N: (u(f"{OK}\n{OK}\n{NO_WHY}\n"), ["3: missing why"]),
    # Adversarial forms: case and spelling variants of why, empty, blank, null and non-string
    # values, a duplicate key, an extra field (the schema forbids extras), every non-object JSON
    # value, a blank or whitespace line, a BOM, a NaN, non-UTF-8 bytes, an empty object.
    "a01/" + L: (u(f'{{{HEAD},"Why":"x",{TAIL}}}\n'), ["1: missing why", "1: unknown field Why"]),
    "a02/" + L: (u(f'{{{HEAD},"why ":"x",{TAIL}}}\n'), ["1: missing why"]),
    "a03/" + L: (u(f'{{{HEAD},"whys":"x",{TAIL}}}\n'), ["1: missing why"]),
    "a04/" + L: (why('""'), ["1: empty why"]),
    "a05/" + L: (why('"  \\t "'), ["1: why does not match"]),
    "a06/" + L: (why("null"), ["1: why must be a string"]),
    "a07/" + L: (why("1"), ["1: why must be a string"]),
    "a08/" + L: (why('["x"]'), ["1: why must be a string"]),
    "a09/" + L: (why('{"why":"x"}'), ["1: why must be a string"]),
    "a10/" + L: (why('"x","why":""'), ["1: invalid JSON: duplicate key why"]),
    "a11/" + L: (u(f'{{{HEAD},"why":"x",{TAIL},"note":"y"}}\n'), ["1: unknown field note"]),
    "a12/" + L: (b'"why"\n', ["1: not a JSON object"]),
    "a13/" + L: (b"null\n", ["1: not a JSON object"]),
    "a14/" + L: (b"42\n", ["1: not a JSON object"]),
    "a15/" + L: (u(f"{OK}\n\n{OK}\n"), ["2: invalid JSON"]),
    "a16/" + L: (u(f"{OK}\n  \n"), ["2: invalid JSON"]),
    "a17/" + L: (b"\xef\xbb\xbf" + u(f"{OK}\n"), ["1: invalid JSON"]),
    "a18/" + L: (u(f'{{{HEAD},"why":"x",{TAIL},"n":NaN}}\n'), ["1: invalid JSON"]),
    "a19/" + L: (b"{" + u(HEAD) + b',"why":"\xff",' + u(TAIL) + b"}\n", ["1: not UTF-8"]),
    "a20/" + L: (u(f"{OK} {OK}\n"), ["1: invalid JSON"]),
    "a21/" + L: (b"{}\n", ["1: missing ts", "1: missing why", "1: missing result"]),
    # Pattern dialect: the schema's $schema (#142, #121 D9). \S on U+FEFF, U+3000 U+00A0 U+2028
    # U+000B fails.
    "p1/" + L: (
        u(f'{{{HEAD},"why":"x","evidence":"e","result":"\\ufeff"}}\n'),
        ["1: result does not match"],
    ),
    "p2/" + L: (why('"\\u3000\\u00a0\\u2028\\u000b"'), ["1: why does not match"]),
    # Mixed good and bad lines in one file: only the bad lines are named, each with its field.
    "m/" + L: (
        u(f'{OK}\n{NO_WHY}\n{OK}\n{{{HEAD},"why":"",{TAIL}}}\n{OK}\n'),
        ["2: missing why", "4: empty why"],
    ),
    # A good and a bad log together: only the bad one is named (its good twin in PASS).
    "gb/x/" + L: (u(f"{OK}\n{OK}\n[]\n"), ["3: not a JSON object"]),
}
# The logs named by exactly their report lines, no other.
COUNTED = ("m/", "gb/")
# Logs that stay green, each never named (tracked unless under "untracked/").
PASS: dict[str, bytes] = {
    # Valid logs pass: one line, several, nested, no final newline, CRLF, any key order,
    # unicode text.
    "v1/" + L: u(f"{OK}\n"),
    "v2/a/b/" + L: u(f"{OK}\n{OK}\n{OK}\n"),
    "v3/" + L: u(OK),
    "v4/" + L: u(f"{OK}\r\n{OK}\r\n"),
    "v5/" + L: b'{"result":"r","why":"w","evidence":"e","decision":"d","phase":"p","agent":"a",'
    b'"ts":"t"}\n',
    "v6/" + L: why('"tab\\tand newline\\n, caf\u00e9"'),
    # Untracked logs and other names are out of scope (exact name decisions.jsonl, tracked only).
    "untracked/" + L: u(f"{NO_WHY}\n"),
    "decisions.jsonl.bak": u(f"{NO_WHY}\n"),
    "Decisions.jsonl": u(f"{NO_WHY}\n"),
    "docs/my-decisions.jsonl": b"not json\n",
    # \S passes U+001C..U+001F, U+0085, U+200B, U+180E.
    **{
        f"s{c}/{L}": why(f'"\\u{c}"')
        for c in ("001c", "001d", "001e", "001f", "0085", "200b", "180e")
    },
    "gb/" + L: u(f"{OK}\n"),
}


class Copy:
    """The kit copy, its commands run with the caller's tools' homes."""

    def __init__(self, s: Scratch) -> None:
        self.s = s
        self.dir = kit_repo(s)
        self.schema = (self.dir / SCHEMA).read_text()
        self.env = {**s.env, **tool_homes()}

    def plant(self, logs: dict[str, bytes]) -> None:
        """LOGS written; each tracked unless under untracked/."""
        for rel, data in logs.items():
            p = self.dir / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
        tracked = [r for r in logs if not r.startswith("untracked/")]
        if tracked:
            self.s.git(self.dir, "add", "-f", *tracked)

    def unplant(self, logs: dict[str, bytes]) -> None:
        tracked = [r for r in logs if not r.startswith("untracked/")]
        if tracked:
            self.s.git(self.dir, "rm", "-qf", "--cached", *tracked)
        for rel in logs:
            (self.dir / rel).unlink()

    def set_schema(self, edit: dict[str, object] | None = None, text: str | None = None) -> None:
        """The schema as the copy holds it, EDIT's properties merged in, or TEXT."""
        if text is None:
            s = json.loads(self.schema)
            for k, v in (edit or {}).items():
                if k == "properties":
                    s["properties"] |= v
                else:
                    s[k] = v
            text = json.dumps(s)
        (self.dir / SCHEMA).write_text(text)

    def run(self, env: dict[str, str] | None = None) -> tuple[int, str]:
        """The copy's scripts/check-decision-log: its exit, stdout and stderr as one stream."""
        cmd = [sys.executable, str(self.dir / "scripts" / "check-decision-log")]
        return self.call(cmd, env)

    def call(self, cmd: list[str], env: dict[str, str] | None = None) -> tuple[int, str]:
        p = subprocess.run(
            cmd,
            cwd=self.dir,
            env={**self.env, **(env or {})},
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            errors="replace",
            check=False,
        )
        return p.returncode, p.stdout


def judged(c: Copy, fail: dict[str, tuple[bytes, list[str]]], ok: dict[str, bytes]) -> str:
    """FAIL and OK planted: one run fails naming each FAIL log by exactly its report lines, no
    OK log named, never decision-log: ok; unplanted after."""
    logs = {**{k: v[0] for k, v in fail.items()}, **ok}
    c.plant(logs)
    rc, out = c.run()
    c.unplant(logs)
    assert rc != 0, f"the bad logs passed check-decision-log:\n{out}"
    assert "decision-log: ok" not in out, out
    lines = out.splitlines()
    for rel, (_, want) in fail.items():
        got = [ln for ln in lines if ln.startswith(f"check-decision-log: {rel}:")]
        exp = [f"check-decision-log: {rel}:{w}" for w in want]
        miss = [e for e in exp if not any(e in g for g in got)]
        assert not miss, f"{rel}: not reported: {miss}, got {got}:\n{out}"
        if rel.startswith(COUNTED):
            assert len(got) == len(want), f"{rel}: more than {exp} reported: {got}:\n{out}"
    named = [r for r in ok if f"check-decision-log: {r}:" in out]
    assert not named, f"good logs reported: {named}:\n{out}"
    return out


def green(c: Copy, ok: dict[str, bytes]) -> None:
    """OK planted keeps check-decision-log green; unplanted after."""
    c.plant(ok)
    rc, out = c.run()
    c.unplant(ok)
    assert rc == 0, f"good logs failed check-decision-log:\n{out}"
    assert "decision-log: ok" in out, out


def logs(s: Scratch) -> None:
    """No tracked log passes; the good logs alone pass; every bad log beside them fails, each
    named by its own lines, an unreadable one (a dangling link) too."""
    c = Copy(s)
    rc, out = c.run()
    assert rc == 0, f"clean copy with no log is not green:\n{out}"
    assert "decision-log: ok (0 files)" in out, out
    green(c, PASS)
    link = c.dir / "u" / L
    link.parent.mkdir()
    link.symlink_to("missing")
    s.git(c.dir, "add", "-f", f"u/{L}")
    out = judged(c, FAIL, PASS)
    assert f"check-decision-log: u/{L}: cannot read" in out, out


def patterns(s: Scratch) -> None:
    """The dialect (#142) on \\d \\w \\b . $ [\\S] [^\\s] and an unmatched backreference via
    schema edits, each pattern one run; refused patterns name the property and node's error,
    __proto__ a property like any other (PR #140 review rounds 2 to 4)."""
    c = Copy(s)

    why_t = json.loads(c.schema)["properties"]["why"]

    def pattern(p: str) -> None:
        c.set_schema({"properties": {"why": {**why_t, "pattern": p}}})

    cases: list[tuple[str, list[str], list[str]]] = [
        (r"^\d+$", ['"\\u0663"', '"1\\n"'], ['"12"']),
        (r"^\w\b", ['"\\u00e9"'], ['"a\\u00e9"', '"a b"']),
        (r"^a.b$", ['"a\\u2028b"'], ['"a\\u0085b"']),
        (r"^[\S]+$", ['"a\\ufeff"'], ['"a\\u001c"']),
        (r"^[^\s]+$", ['"a\\ufeff"'], ['"a\\u0085"']),
        (r"^(a|(b))\2c$", ['"bc"'], ['"ac"']),
    ]
    for p, bad, good in cases:
        pattern(p)
        fail = {f"f{i}/{L}": (why(v), ["1: why does not match"]) for i, v in enumerate(bad)}
        judged(c, fail, {f"g{i}/{L}": why(v) for i, v in enumerate(good)})
    unusable = "unusable schema: property"
    for p, value, err in (
        ("^a++$", '"a"', "Invalid regular expression: /^a++$/u: Nothing to repeat"),
        (
            "^a{\u0661}$",
            '"a{\\u0661}"',
            "Invalid regular expression: /^a{\u0661}$/u: Incomplete quantifier",
        ),
    ):
        pattern(p)
        c.plant({L: why(value)})
        rc, out = c.run()
        c.unplant({L: b""})
        want = f"check-decision-log: {SCHEMA}: {unusable} why: pattern '{p}': {err}"
        assert rc == 2, f"pattern {p} not refused (exit {rc}):\n{out}"
        assert want in out, out
    # __proto__: its invalid pattern refused with no tracked log, its valid one tested.
    proto = {"type": "string"}
    c.set_schema({"properties": {"__proto__": {**proto, "pattern": "^a++$"}}})
    rc, out = c.run()
    err = "Invalid regular expression: /^a++$/u: Nothing to repeat"
    want = f"check-decision-log: {SCHEMA}: {unusable} __proto__: pattern '^a++$': {err}"
    assert rc == 2, f"__proto__ pattern ^a++$ not refused (exit {rc}):\n{out}"
    assert want in out, out
    c.set_schema({"properties": {"__proto__": {**proto, "pattern": "^a$"}}})
    bad = u(f'{{{HEAD},"why":"x",{TAIL},"__proto__":"b"}}\n')
    good = u(f'{{{HEAD},"why":"x",{TAIL},"__proto__":"a"}}\n')
    judged(c, {L: (bad, ["1: __proto__ does not match ^a$"])}, {"g/" + L: good})


# Unusable schemas (invalid JSON, missing, or a keyword the validator does not enforce): each
# fails even with no log, never decision-log: ok. None: the schema file missing.
OBJ = '{"type": "object", "required": ["why"], '
STR = OBJ + '"properties": {"why": {"type": "string", '
BAD_SCHEMAS = [
    None,
    '{"type": "object", "required": ["why"',
    "[]",
    '{"type": "object", "required": ["why", "why"]}',
    '{"type": "object", "properties": {"why": {"minLength": 1.0}}}',
    '{"type": "object", "properties": {"why": {"minLength": true}}}',
    STR + '"maxLength": 9}}}',
    OBJ + '"patternProperties": {}}',
    OBJ + '"properties": {"why": {"type": ["string", "null"]}}}',
    STR + '"pattern": "("}}}',
    OBJ + '"additionalProperties": {"type": "string"}}',
    STR + '"pattern": "(?P<a>x)"}}}',
    STR + '"pattern": "x\\\\Z"}}}',
]


def schema(s: Scratch) -> None:
    """The schema file is the one source for the field list and the extra-field policy; an
    unusable one fails closed."""
    c = Copy(s)
    required = [*json.loads(c.schema)["required"], "ticket"]
    c.set_schema({"required": required, "properties": {"ticket": {"type": "string"}}})
    ticket = u(f'{{{HEAD},"why":"x",{TAIL},"ticket":"#44"}}\n')
    judged(c, {L: (u(f"{OK}\n"), ["1: missing ticket"])}, {"g/" + L: ticket})
    extras = {"additionalProperties": True}
    c.set_schema({"required": required, "properties": {"ticket": {"type": "string"}}, **extras})
    green(c, {L: u(f'{{{HEAD},"why":"x",{TAIL},"ticket":"#44","note":"y"}}\n')})
    for text in BAD_SCHEMAS:
        if text is None:
            (c.dir / SCHEMA).unlink()
        else:
            c.set_schema(text=text)
        rc, out = c.run()
        assert rc != 0, f"schema {text!r} did not fail closed:\n{out}"
        assert f"check-decision-log: {SCHEMA}: unusable schema" in out, f"{text!r}:\n{out}"
        assert "decision-log: ok" not in out, f"{text!r}:\n{out}"


def stub(s: Scratch, name: str) -> dict[str, str]:
    """A NAME that fails, first on PATH (which the justfile keeps ahead of its tools)."""
    b = s.root / f"broken-{name}"
    b.mkdir()
    (b / name).write_text(
        f'#!/bin/sh\necho "{name}: broken (check-decision-log test stub)" >&2\nexit 2\n'
    )
    (b / name).chmod(0o755)
    return {"PATH": f"{b}:{s.env['PATH']}"}


def fails_closed(s: Scratch) -> None:
    """A broken python3 (the recipe's: `just check-decision-log`), git or node, or no node on
    PATH, fails, never decision-log: ok."""
    c = Copy(s)
    rc, out = c.call(["just", "check-decision-log"], stub(s, "python3"))
    assert rc != 0, f"broken python3 passed check-decision-log:\n{out}"
    assert "python3: broken" in out, out
    assert "decision-log: ok" not in out, out
    for name, said in (
        ("git", "git ls-files exited 2"),
        ("node", "node exited 2; the check cannot pass"),
    ):
        rc, out = c.run(stub(s, name))
        assert rc != 0, f"broken {name} passed check-decision-log:\n{out}"
        assert f"{name}: broken" in out, out
        assert said in out, out
        assert "decision-log: ok" not in out, out
    # No node on PATH: git only.
    b = s.root / "git-only"
    b.mkdir()
    git = shutil.which("git")
    assert git, "git is not on PATH"
    (b / "git").symlink_to(git)
    rc, out = c.run({"PATH": str(b)})
    want = (
        "check-decision-log: node not found on PATH: install node (Pi needs it too); "
        "the check cannot pass"
    )
    assert rc == 2, f"missing node did not fail closed (exit {rc}):\n{out}"
    assert want in out, out


if __name__ == "__main__":
    main(logs, patterns, schema, fails_closed)
