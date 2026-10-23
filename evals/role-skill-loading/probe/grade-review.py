#!/usr/bin/env python3
"""grade-review.py FINAL.txt TEST...: the reviewer's final report blocks each named test (facts only).

Blocked verdict: a paragraph naming 'verdict' and 'block'. A test is blocked when its name
appears in a section whose heading says block (not non-blocking), or in a paragraph or list
item that says block (not non-blocking/note). Prints per test; PASS when all hold.
"""
import re, sys

text = open(sys.argv[1], encoding="utf-8").read()
BLOCK = re.compile(r"(?<!non-)block", re.I)
verdict = any(re.search(r"verdict", p, re.I) and BLOCK.search(p) for p in re.split(r"\n\s*\n", text))
sections = re.split(r"\n(?=#+ )", "\n" + text)
blocked = ""
for s in sections:
    head, _, body = s.strip().partition("\n")
    if head.startswith("#") and BLOCK.search(head) and not re.search(r"non-block|note", head, re.I):
        blocked += body + "\n"
for c in re.split(r"\n\s*\n|\n(?=\s*(?:[-*]|\d+\.)\s)", text):
    if BLOCK.search(c) and not re.search(r"non-block", c, re.I):
        blocked += c + "\n"
ok = verdict
print(f"verdict blocked: {verdict}")
for t in sys.argv[2:]:
    hit = t in blocked
    print(f"{t}: {'blocked' if hit else 'NOT blocked'}")
    ok = ok and hit
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
