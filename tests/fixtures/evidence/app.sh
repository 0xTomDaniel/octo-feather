#!/bin/sh
# A stand-in for a template's app behind tests/evidence.sh's contract fixture (qc.toml beside this file): one sh
# process per call, no other program, answering each case of the verify-app hello drive as the template's app does,
# so the test pays for the evidence store's mechanics and not the app's (the record is the store's; each template's
# own tests prove its hello). $1: the problem, JSON-escaped, the template's request validator names for an unknown key.
problem=$1; shift
[ "$1" = hello ] && [ $# -gt 1 ] || { echo "usage: app hello <name> [--json]" >&2; exit 64; }
shift
json='' name='' req=''
while [ $# -gt 0 ]; do
  case $1 in --json) json=1 ;; --request) req=$2; shift ;; *) name=$1 ;; esac
  shift
done
case $req in
  *mood*) printf '{"error": "invalid request", "issues": [{"field": "mood", "problem": "%s"}]}\n' "$problem"; exit 2 ;;
  # {"name": "Ada"} (python's json.dumps) or {"name":"Ada"} (JSON.stringify): the name.
  ?*) name=${req#*\"name\":}; name=${name# }; name=${name#\"}; name=${name%%\"*} ;;
esac
# Trimmed of spaces at both ends.
name=${name#"${name%%[! ]*}"}; name=${name%"${name##*[! ]}"}
if [ -z "$name" ]; then
  if [ -n "$json" ]; then echo '{"error": "name is empty"}'; else echo "error: name is empty" >&2; fi
  exit 2
fi
if [ -n "$json" ]; then printf '{"name": "%s", "text": "Hello, %s"}\n' "$name" "$name"; else echo "Hello, $name"; fi
