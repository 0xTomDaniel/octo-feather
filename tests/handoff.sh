#!/usr/bin/env bash
# Public writer CLI: arbitrary fields, quotes and literal newlines roundtrip.
set -euo pipefail
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
"$kit/scripts/octo-feather-handoff" encode --field kind finding \
  --field summary $'a "quote"\nand a second line' \
  --field extra 'unknown field retained' --json-field blocking false \
  --json-field details '{"nested":[1,null,"x"]}' |
  python3 -c 'import json,sys; d=json.load(sys.stdin); assert d == {"kind":"finding", "summary":"a \"quote\"\nand a second line", "extra":"unknown field retained", "blocking":False, "details":{"nested":[1,None,"x"]}}; print("handoff: ok (quotes, newlines, unknown and structured fields retained)")'
