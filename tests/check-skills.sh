#!/usr/bin/env bash
# gate: e2e
# Integration test for the check-skills gate (skills #acceptance-skill-frontmatter, #acceptance-only-listed):
# in a throwaway git copy of the kit's tracked files, a planted skill that Pi does not load, or whose
# frontmatter has no name as Pi's parser reads it, makes `just check-skills` fail
# naming its path (#231: the recipe under test, not the whole gate per case); one case runs
# `just check` to prove the gate includes check-skills. Run by `just check`.
set -euo pipefail
# The one `just check` case in the copy runs this test there too (its tests/*.sh step): stop there, nested.
[[ -z "${CHECK_SKILLS_TEST_COPY:-}" ]] || { echo "check-skills test: nested run in a copy (a planted skill passed check-skills)" >&2; exit 1; }
kit="$(cd "$(dirname "$0")/.." && pwd -P)"
t="$(mktemp -d)"; trap 'rm -rf "$t" "$t.home"' EXIT
(cd "$kit" && git ls-files -z | xargs -0 tar -cf - 2>/dev/null) | tar -xf - -C "$t"
g() { git -C "$t" -c user.name=t -c user.email=t@t "$@"; }
g init -q; g add -A; g commit -qm base
(cd "$t" && just check-skills >/dev/null 2>&1) || { echo "check-skills test: clean copy is not green" >&2; (cd "$t" && just check-skills) >&2; exit 1; }
sk=.agents/skills/qc-bad/SKILL.md
plant() { mkdir -p "$t/${sk%/*}"; printf '%b' "$1" > "$t/$sk"; g add -f "$sk"; }
unplant() { g rm -qf --cached "$sk" >/dev/null 2>&1 || true; rm -rf "${t:?}/${sk%/*}"; }
# The content cases are judged together (#558: each check-skills run starts Pi, so one run, not one per case): case N
# plants its SKILL.md as .agents/skills/qc-bad-N or qc-good-N, its own name qc-bad or qc-good spelled with -N so no
# two cases share a name, then judge runs the copy's scripts/check-skills (the command `just check-skills` runs, #507)
# once; the clean copy, the broken python3 and the gate case run `just check-skills` itself.
n=0; expected=(); allowed=(); planted=()
# queue DIR CONTENT: plant case n's SKILL.md under DIR-n, its qc-bad and qc-good names numbered.
queue() {
  n=$((n + 1)); local d=".agents/skills/$1-$n" c="${2//qc-bad/qc-bad-$n}"; c="${c//qc-good/qc-good-$n}"
  mkdir -p "$t/$d"; printf '%b' "$c" > "$t/$d/SKILL.md"; g add -f "$d/SKILL.md"; planted+=("$d")
}
# expect RECIPE CONTENT: a skill with SKILL.md CONTENT makes `just RECIPE` fail naming its path.
expect() { queue qc-bad "$2"; expected+=("${planted[-1]}/SKILL.md"$'\t'"$2"); }
# allow CONTENT: a skill with SKILL.md CONTENT keeps `just check-skills` green: it is never named.
allow() { queue qc-good "$1"; allowed+=("${planted[-1]}/SKILL.md"$'\t'"$1"); }
# judge: one check-skills run over every queued case; each expected path named, no allowed one; then unplanted.
judge() {
  set +e; out="$(cd "$t" && "$t/scripts/check-skills" 2>&1)"; rc=$?; set -e
  for d in "${planted[@]}"; do g rm -qf --cached "$d/SKILL.md" >/dev/null 2>&1 || true; rm -rf "${t:?}/$d"; done
  [[ "$rc" != 0 ]] && ! grep -qF 'skills: ok' <<<"$out" || { echo "check-skills test: the bad skills passed check-skills" >&2; echo "$out" >&2; exit 1; }
  for e in "${expected[@]}"; do
    grep -qF "check-skills: ${e%%$'\t'*}:" <<<"$out" || { echo "check-skills test: '${e#*$'\t'}' not reported naming ${e%%$'\t'*}" >&2; echo "$out" >&2; exit 1; }
  done
  for a in "${allowed[@]}"; do
    ! grep -qF "${a%%/SKILL.md*}" <<<"$out" || { echo "check-skills test: good SKILL.md '${a#*$'\t'}' failed check-skills" >&2; echo "$out" >&2; exit 1; }
  done
}
body='# Bad\n'
# The five criterion cases.
expect check-skills "---\ndescription: Does a thing.\n---\n$body"
expect check-skills "---\nname: qc-bad\n---\n$body"
expect check-skills "# qc-bad\nname: qc-bad\ndescription: Does a thing.\n"
expect check-skills "---\nname:\ndescription: Does a thing.\n---\n$body"
expect check-skills "---\nname: qc-bad\ndescription:\n---\n$body"
# Good skills, quoted and folded forms included.
allow "---\nname: qc-good\ndescription: Does a thing.\n---\n$body"
allow "---\nname: \"qc-good\"\ndescription: 'Does a thing.'\n---\n$body"
allow "---\nname: qc-good\ndescription: >\n  Does a thing,\n  over two lines.\n---\n$body"
allow "---\nname: qc-good\ndescription: |-\n  Does a thing.\nlicense: MIT\n---\n$body"
allow "---\nname: qc-good\ndescription:\n  Plain, continued on the next line.\n---\n$body"
allow "---\r\nname: qc-good\r\ndescription: Does a thing.\r\n---\r\n$body"
# #141, #121 D8 (owner: skills spec #acceptance-skill-frontmatter): quoted keys, an escape, a space before the colon.
allow "---\n\"name\": qc-good\ndescription: d\n---\n"
allow "---\n'name': qc-good\n\"description\" : Does a thing.\n---\n$body"
allow "---\n\"na\\\\x6de\": qc-good\ndescription: Does a thing.\n---\n$body"
allow "---\nname : qc-good\ndescription: Does a thing.\n---\n$body"
# A byte order mark before ---: Pi strips it and loads the skill, so the gate passes it (Pi decides, #558).
allow "\xef\xbb\xbf---\nname: qc-good\ndescription: Does a thing.\n---\n$body"
# Adversarial forms: body-only after an empty block, keys after the closing ---, no closing ---,
# leading text or spaces before ---, case and spelling variants, indented (nested) keys,
# empty quoted, null, comment-only and empty folded values, duplicates, a non-string.
expect check-skills "---\n---\nname: qc-bad\ndescription: Does a thing.\n"
expect check-skills "---\nname: qc-bad\n---\ndescription: Does a thing.\n"
expect check-skills "---\nname: qc-bad\ndescription: Does a thing.\n$body"
expect check-skills "\n---\nname: qc-bad\ndescription: Does a thing.\n---\n$body"
expect check-skills " ---\nname: qc-bad\ndescription: Does a thing.\n---\n$body"
expect check-skills "---\nName: qc-bad\ndescription: Does a thing.\n---\n$body"
expect check-skills "---\nname: qc-bad\nDESCRIPTION: Does a thing.\n---\n$body"
expect check-skills "---\nname: qc-bad\ndescriptions: Does a thing.\n---\n$body"
expect check-skills "---\nname:qc-bad\ndescription: Does a thing.\n---\n$body"
expect check-skills "---\nmeta:\n  name: qc-bad\ndescription: Does a thing.\n---\n$body"
expect check-skills "---\nname: \"\"\ndescription: Does a thing.\n---\n$body"
expect check-skills "---\nname: qc-bad\ndescription: '  '\n---\n$body"
expect check-skills "---\nname: ~\ndescription: Does a thing.\n---\n$body"
expect check-skills "---\nname: qc-bad\ndescription: null\n---\n$body"
expect check-skills "---\nname: qc-bad\ndescription: # todo\n---\n$body"
expect check-skills "---\nname: qc-bad\ndescription: >\n---\n$body"
expect check-skills "---\nname: qc-bad\ndescription: |\n\nlicense: MIT\n---\n$body"
expect check-skills "---\nname: qc-bad\ndescription: \"unterminated\n---\n$body"
expect check-skills "---\nname: [qc-bad]\ndescription: Does a thing.\n---\n$body"
expect check-skills "---\nname: qc-bad\nname: \ndescription: Does a thing.\n---\n$body"
# Quoted-key neighbours (#141): an empty value, another spelling, a key quoted apart, a duplicate across styles.
expect check-skills "---\n\"name\": \"\"\ndescription: d\n---\n"
expect check-skills "---\n\"Name\": qc-bad\ndescription: d\n---\n"
expect check-skills "---\n\"name \": qc-bad\ndescription: d\n---\n"
expect check-skills "---\n\"name\":qc-bad\ndescription: d\n---\n"
expect check-skills "---\nname: qc-bad\n'name': qc-bad\ndescription: d\n---\n"
expect check-skills "---\n\"description\": d\n---\n"
expect check-skills ""
# skills spec #loading-refuse (#558): a description Pi cannot read fails naming the skill; quoted, it passes; a role
# listing it fails naming both.
expect check-skills "---\nname: qc-bad\ndescription: Tests worth keeping: seams first.\n---\n$body"
allow "---\nname: qc-good\ndescription: \"Tests worth keeping: seams first.\"\n---\n$body"
judge
role=agents/qc-role.md
plant "---\nname: qc-bad\ndescription: Tests worth keeping: seams first.\n---\n$body"
printf -- '---\nname: qc-role\ndescription: A role.\nskills: qc-bad\n---\nBody.\n' > "$t/$role"
set +e; out="$(cd "$t" && "$t/scripts/check-skills" 2>&1)"; rc=$?; set -e
unplant; rm -f "$t/$role"
[[ "$rc" != 0 ]] && grep -qF "check-skills: role qc-role ($role): Pi does not offer its skill qc-bad" <<<"$out" \
  || { echo "check-skills test: a role listing a skill Pi refuses was not reported naming both" >&2; echo "$out" >&2; exit 1; }
# One bad skill among good ones fails, naming only the bad one.
plant "---\nname: qc-bad\ndescription:\n---\n$body"
mkdir -p "$t/.agents/skills/qc-good"; printf -- '---\nname: qc-good\ndescription: Fine.\n---\n' > "$t/.agents/skills/qc-good/SKILL.md"
set +e; out="$(cd "$t" && "$t/scripts/check-skills" 2>&1)"; rc=$?; set -e
unplant; rm -rf "$t/.agents/skills/qc-good"
[[ "$rc" != 0 ]] && grep -qF "check-skills: $sk: Pi does not load it: description is required" <<<"$out" && ! grep -qF 'qc-good' <<<"$out" || { echo "check-skills test: mixed good and bad skills not reported as the bad one" >&2; echo "$out" >&2; exit 1; }
# Fails closed: an unreadable SKILL.md (a dangling link) fails naming it, never skills: ok.
mkdir -p "$t/${sk%/*}"; ln -s missing "$t/$sk"
set +e; out="$(cd "$t" && "$t/scripts/check-skills" 2>&1)"; rc=$?; set -e
unplant
[[ "$rc" != 0 ]] && grep -qF "check-skills: $sk: cannot read" <<<"$out" && ! grep -qF 'skills: ok' <<<"$out" || { echo "check-skills test: unreadable SKILL.md not reported" >&2; echo "$out" >&2; exit 1; }
# Fails closed: a broken python3 (a stub first on the caller's PATH, which the justfile keeps ahead of its tools)
# fails the gate, never skills: ok.
h="$t.bin"; mkdir -p "$h"
printf '#!/bin/sh\necho "python3: broken (check-skills test stub)" >&2\nexit 2\n' > "$h/python3"; chmod +x "$h/python3"
set +e; out="$(cd "$t" && PATH="$h:$PATH" just check-skills 2>&1)"; rc=$?; set -e
rm -rf "$h"
[[ "$rc" != 0 ]] && ! grep -qF 'skills: ok' <<<"$out" || { echo "check-skills test: broken python3 passed check-skills" >&2; echo "$out" >&2; exit 1; }
# Fails closed: a broken pi (a stub first on PATH, the pi pi-role would exec) fails, never skills: ok.
mkdir -p "$h"; printf '#!/bin/sh\necho "pi: broken (check-skills test stub)" >&2\nexit 1\n' > "$h/pi"; chmod +x "$h/pi"
set +e; out="$(cd "$t" && PATH="$h:$PATH" "$t/scripts/check-skills" 2>&1)"; rc=$?; set -e
rm -rf "$h"
[[ "$rc" != 0 ]] && grep -qF 'pi: broken' <<<"$out" && ! grep -qF 'skills: ok' <<<"$out" || { echo "check-skills test: broken pi passed check-skills" >&2; echo "$out" >&2; exit 1; }
[[ -z "$(g status --porcelain)" ]] || { echo "check-skills test: cleanup left changes in the copy" >&2; g status --short >&2; exit 1; }
# The gate includes check-skills: `just check` in the copy fails on a skill with no name, naming its SKILL.md.
# The copy keeps only this test of tests/*.sh, so the gate there starts no other test, and the guard above
# stops this one if the planted skill ever got past check-skills.
# It selects only its own recipe item (PYTEST_ADDOPTS -k, pytest's own selection, #507), so no recipe before it runs.
find "$t/tests" -maxdepth 1 -name '*.sh' ! -name check-skills.sh -delete; g add -A
plant "---\ndescription: Does a thing.\n---\n$body"
set +e; out="$(cd "$t" && env -u CI CHECK_SKILLS_TEST_COPY=1 XDG_STATE_HOME="$t.home" PYTEST_ADDOPTS="--color=no -k 'test_recipe and check-skills'" just check 2>&1)"; rc=$?; set -e
[[ "$rc" != 0 ]] || { echo "check-skills test: a skill with no name passed just check" >&2; exit 1; }
grep -qF "check-skills: $sk" <<<"$out" || { echo "check-skills test: just check did not report $sk" >&2; echo "$out" >&2; exit 1; }
# Only its own item ran (#507): pytest's own selection, through the real `just check`.
grep -qF "FAILED tests/gate/test_gate.py::test_recipe[check-skills]" <<<"$out" && grep -qE '^=+ 1 failed(, [0-9]+ deselected)? in ' <<<"$out" \
  || { echo "check-skills test: just check ran more than its own item" >&2; echo "$out" >&2; exit 1; }
echo "check-skills: ok (missing, body-only and empty name or description fail naming the SKILL.md; quoted and folded values pass; a description or role skill Pi refuses fails naming both; adversarial forms, a broken checker and a broken pi fail closed)"
