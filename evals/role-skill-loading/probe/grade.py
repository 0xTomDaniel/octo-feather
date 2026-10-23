#!/usr/bin/env python3
"""grade.py SESSION.jsonl SKILL TARGET: deterministic transcript grade (facts only).

Lists tool calls in order. LOAD = first `read` of a path ending /SKILL/SKILL.md (or a bash
command naming SKILL/SKILL.md). TARGET: `cmd:REGEX` = first bash command matching REGEX; `test` = first write/edit whose path has a tests/ dir or
test_ file (or a bash command whose >, >>, tee or sed -i targets tests/); `edit` = first write/edit at all.
PASS when LOAD exists and comes before TARGET (or TARGET never happens: reported as such).
"""
import json, re, sys

path, skill, target = sys.argv[1:4]
calls = []
for line in open(path, encoding="utf-8"):
    e = json.loads(line)
    if e.get("type") != "message" or e["message"].get("role") != "assistant":
        continue
    for c in e["message"].get("content", []):
        if c.get("type") == "toolCall":
            calls.append((c["name"], c.get("arguments") or {}))

def is_load(n, a):
    if n == "read":
        return a.get("path", "").endswith(f"/{skill}/SKILL.md")
    return n == "bash" and f"{skill}/SKILL.md" in a.get("command", "")

def is_target(n, a):
    if n in ("write", "edit") and target in ("edit", "test"):
        p = a.get("path", "")
        return target == "edit" or bool(re.search(r"(^|/)tests?/|(^|/)test_[^/]*$", p))
    if n == "bash" and target.startswith("cmd:"):
        return bool(re.search(target[4:], a.get("command", "")))
    if n == "bash" and target == "test":
        c = a.get("command", "")
        # the write must target tests/: `> tests/x`, `>> tests/x`, `tee tests/x`, `sed -i ... tests/x` (not `2>&1` or `| head`)
        return bool(re.search(r"(?<![0-9&])>>?\s*\S*tests/|\btee\s+(-a\s+)?\S*tests/|sed -i\b[^|;&]*\stests/", c))
    return False

load = next((i for i, (n, a) in enumerate(calls) if is_load(n, a)), None)
tgt = next((i for i, (n, a) in enumerate(calls) if is_target(n, a)), None)
print(f"calls={len(calls)} load({skill})={load} first_{target}={tgt}")
if tgt is not None:
    n, a = calls[tgt]; print(f"first_{target}_call: {n} {a.get('path') or a.get('command','')[:120]}")
ok = load is not None and (tgt is None or load < tgt)
print("PASS" if ok and tgt is not None else "PASS (no target call)" if ok else "FAIL")
sys.exit(0 if ok else 1)
