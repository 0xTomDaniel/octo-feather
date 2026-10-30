#!/usr/bin/env bash
# Integration test for the check-skills gate (skills #acceptance-skill-frontmatter):
# in a throwaway git copy of the kit's tracked files, a planted skill whose SKILL.md lacks
# a --- frontmatter block with non-empty name and description makes `just check-skills` fail
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
# expect RECIPE CONTENT: a skill with SKILL.md CONTENT makes `just RECIPE` fail naming its path.
expect() {
  plant "$2"
  set +e; out="$(cd "$t" && just "$1" 2>&1)"; rc=$?; set -e
  unplant
  [[ "$rc" != 0 ]] || { echo "check-skills test: SKILL.md '$2' passed just $1" >&2; exit 1; }
  grep -qF "check-skills: $sk" <<<"$out" || { echo "check-skills test: '$2' not reported naming $sk" >&2; echo "$out" >&2; exit 1; }
  ! grep -qF 'skills: ok' <<<"$out" || { echo "check-skills test: '$2' printed skills: ok" >&2; exit 1; }
}
# allow CONTENT: a skill with SKILL.md CONTENT keeps `just check-skills` green.
allow() {
  plant "$1"
  set +e; out="$(cd "$t" && just check-skills 2>&1)"; rc=$?; set -e
  unplant
  [[ "$rc" == 0 ]] || { echo "check-skills test: good SKILL.md '$1' failed check-skills" >&2; echo "$out" >&2; exit 1; }
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
# Adversarial forms: body-only after an empty block, keys after the closing ---, no closing ---,
# leading text or spaces before ---, case and spelling variants, indented (nested) keys,
# empty quoted, null, comment-only and empty folded values, duplicates, a non-string.
expect check-skills "---\n---\nname: qc-bad\ndescription: Does a thing.\n"
expect check-skills "---\nname: qc-bad\n---\ndescription: Does a thing.\n"
expect check-skills "---\nname: qc-bad\ndescription: Does a thing.\n$body"
expect check-skills "\n---\nname: qc-bad\ndescription: Does a thing.\n---\n$body"
expect check-skills " ---\nname: qc-bad\ndescription: Does a thing.\n---\n$body"
expect check-skills "\xef\xbb\xbf---\nname: qc-bad\ndescription: Does a thing.\n---\n$body"
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
# One bad skill among good ones fails, naming only the bad one.
plant "---\nname: qc-bad\ndescription:\n---\n$body"
mkdir -p "$t/.agents/skills/qc-good"; printf -- '---\nname: qc-good\ndescription: Fine.\n---\n' > "$t/.agents/skills/qc-good/SKILL.md"
set +e; out="$(cd "$t" && just check-skills 2>&1)"; rc=$?; set -e
unplant; rm -rf "$t/.agents/skills/qc-good"
[[ "$rc" != 0 ]] && grep -qF "check-skills: $sk: empty description" <<<"$out" && ! grep -qF 'qc-good' <<<"$out" || { echo "check-skills test: mixed good and bad skills not reported as the bad one" >&2; echo "$out" >&2; exit 1; }
# Fails closed: an unreadable SKILL.md (a dangling link) fails naming it, never skills: ok.
mkdir -p "$t/${sk%/*}"; ln -s missing "$t/$sk"
set +e; out="$(cd "$t" && just check-skills 2>&1)"; rc=$?; set -e
unplant
[[ "$rc" != 0 ]] && grep -qF "check-skills: $sk: cannot read" <<<"$out" && ! grep -qF 'skills: ok' <<<"$out" || { echo "check-skills test: unreadable SKILL.md not reported" >&2; echo "$out" >&2; exit 1; }
# Fails closed: a broken python3 (a stub first on the caller's PATH, which the justfile keeps ahead of its tools)
# fails the gate, never skills: ok.
h="$t.bin"; mkdir -p "$h"
printf '#!/bin/sh\necho "python3: broken (check-skills test stub)" >&2\nexit 2\n' > "$h/python3"; chmod +x "$h/python3"
set +e; out="$(cd "$t" && PATH="$h:$PATH" just check-skills 2>&1)"; rc=$?; set -e
rm -rf "$h"
[[ "$rc" != 0 ]] && ! grep -qF 'skills: ok' <<<"$out" || { echo "check-skills test: broken python3 passed check-skills" >&2; echo "$out" >&2; exit 1; }
[[ -z "$(g status --porcelain)" ]] || { echo "check-skills test: cleanup left changes in the copy" >&2; g status --short >&2; exit 1; }
# The gate includes check-skills: `just check` in the copy fails on a skill with no name, naming its SKILL.md.
# The copy keeps only this test of tests/*.sh, so the gate there starts no other test, and the guard above
# stops this one if the planted skill ever got past check-skills.
find "$t/tests" -maxdepth 1 -name '*.sh' ! -name check-skills.sh -delete; g add -A
plant "---\ndescription: Does a thing.\n---\n$body"
set +e; out="$(cd "$t" && env -u CI CHECK_SKILLS_TEST_COPY=1 XDG_STATE_HOME="$t.home" just check 2>&1)"; rc=$?; set -e
[[ "$rc" != 0 ]] || { echo "check-skills test: a skill with no name passed just check" >&2; exit 1; }
grep -qF "check-skills: $sk" <<<"$out" || { echo "check-skills test: just check did not report $sk" >&2; echo "$out" >&2; exit 1; }
echo "check-skills: ok (missing, body-only and empty name or description fail naming the SKILL.md; quoted and folded values pass; adversarial forms and a broken checker fail closed)"
