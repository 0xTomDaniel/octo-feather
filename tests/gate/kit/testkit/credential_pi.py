#!/usr/bin/env python3
"""Pi at the external model seam for qc-creds. As the legacy script's Pi, refuses without
both credential copies and delegates extension calls to the shared classifier stand-in. The
fallback reply is supplied by the scenario at its independently known target head, never derived
from product output. Only one non-probe request per fresh sandbox is recorded; extra requests
refuse. No owned QC, credential-copy or sandbox logic is replaced here.
"""

import json
import os
import sys
from pathlib import Path

argv = sys.argv[1:]
if argv == ["--version"]:
    sys.exit(0)
for name in ("auth.json", "models.json"):
    path = Path.home() / ".pi" / "agent" / name
    if not path.is_file() or "SECRET-pi" not in path.read_text():
        sys.stderr.write(f"fake pi: no {name}: no model access\n")
        sys.exit(9)
used = Path(os.environ["TMPDIR"]) / "credential-pi-used"
try:
    with used.open("x") as f:
        f.write("request\n")
except FileExistsError:
    sys.exit("credential pi: recording exhausted")
if "-e" in argv:
    classifier = Path(__file__).resolve().parents[3] / "fixtures" / "classify-stub" / "pi"
    os.execv(str(classifier), [str(classifier), *argv])
reply = json.loads(os.environ["CREDENTIAL_PI_REPLY"])
brief = argv[-1] if argv else ""
if f"head {reply['head']}" not in brief or "- acceptance-b:" not in brief:
    sys.exit("credential pi: no recording for fallback request")
if "- acceptance-a:" in brief:
    sys.exit("credential pi: unexpected demo criterion sent to fallback")
sys.stdout.write("```json\n" + json.dumps(reply) + "\n```\n")
