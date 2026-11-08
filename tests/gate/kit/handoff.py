"""The scenarios of tests/gate/kit/test_handoff.py (its items), this file their command
(testkit.main): the public hand-off writer, `octo-feather-handoff encode`: arbitrary fields,
quotes and literal newlines, unknown and structured fields round-trip exactly."""

from __future__ import annotations

import json

from testkit import Scratch, kit, main


def encode_roundtrip(s: Scratch) -> None:
    """encode of a quoted two-line summary, an unknown field, a JSON false and a nested JSON
    value: its line decodes to exactly those fields."""
    ran = s.run(
        [
            kit("octo-feather-handoff"),
            "encode",
            "--field",
            "kind",
            "finding",
            "--field",
            "summary",
            'a "quote"\nand a second line',
            "--field",
            "extra",
            "unknown field retained",
            "--json-field",
            "blocking",
            "false",
            "--json-field",
            "details",
            '{"nested":[1,null,"x"]}',
        ]
    )
    want = {
        "kind": "finding",
        "summary": 'a "quote"\nand a second line',
        "extra": "unknown field retained",
        "blocking": False,
        "details": {"nested": [1, None, "x"]},
    }
    assert json.loads(ran.out) == want, ran.out


if __name__ == "__main__":
    main(encode_roundtrip)
