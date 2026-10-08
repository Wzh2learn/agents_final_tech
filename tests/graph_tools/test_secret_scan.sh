#!/usr/bin/env bash
# Negative tests for scripts/graph/tools/secret_scan.sh.
# Fixtures are temporary and contain deliberate fake credentials.
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CHK="$HERE/scripts/graph/tools/secret_scan.sh"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/secretscan.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT
pass=0
fail=0

check() {
  local name=$1 actual=$2 expected=$3
  if [ "$actual" = "$expected" ]; then
    echo "PASS $name"
    pass=$((pass + 1))
  else
    echo "FAIL $name: got $actual want $expected"
    fail=$((fail + 1))
  fi
}

scan_rc() {
  bash "$CHK" "$@" >/tmp/secret-scan-test.out 2>/tmp/secret-scan-test.err
  echo $?
}

hits() {
  bash "$CHK" "$TMP/t" 2>/dev/null | grep -c "FINDING.*$1"
}

mkdir -p "$TMP/t"
printf 'nothing to see\n' > "$TMP/t/clean.md"
check "clean tree passes" "$(scan_rc "$TMP/t")" 0

printf 'ak = "LTAI5tZq9mV0nR7xK3pL6sQ2"\n' > "$TMP/t/k.md"
check "LTAI shape caught" "$(hits LTAI)" 1
printf 'ghp_0123456789abcdef0123456789abcdef0123\n' > "$TMP/t/k.md"
check "GitHub token shape caught" "$(hits ghp_)" 1
printf 'api_key = "0123456789abcdef0123456789abcdef"\n' > "$TMP/t/k.md"
check "opaque assignment caught" "$(hits api_key)" 1
printf 'contact someone@corp.example.internal\n' > "$TMP/t/k.md"
check "ordinary prose passes" "$(scan_rc "$TMP/t")" 0

printf -- '-----BEGIN OPENSSH PRIVATE KEY-----\n' > "$TMP/t/pem.md"
check "PEM header alone passes" "$(scan_rc "$TMP/t")" 0
printf -- '-----BEGIN OPENSSH PRIVATE KEY-----\nQUJDREVGR0hJSktMTU5PUFFSU1RVVldYWVphYmNkZWZnaGlqa2xtbm9w\n-----END OPENSSH PRIVATE KEY-----\n' > "$TMP/t/pem.md"
check "PEM body caught" "$(hits pem-body)" 1
rm "$TMP/t/pem.md"

printf 'real path /Users/jsmith42/work/notes.md\n' > "$TMP/t/k.md"
check "home path caught only with --paths" "$(bash "$CHK" --paths "$TMP/t" 2>/dev/null | grep -c "FINDING.*Users")" 1
check "home path hidden by default" "$(scan_rc "$TMP/t")" 0
printf 'example path /Users/jsmith42/work/notes.md  secret-scan:allow\n' > "$TMP/t/k.md"
check "inline exemption passes" "$(scan_rc "$TMP/t")" 0

printf 'codename XYZZY-internal appears here\n' > "$TMP/t/k.md"
printf 'XYZZY-internal\n' > "$TMP/words.txt"
check "word list caught" "$(bash "$CHK" --words "$TMP/words.txt" "$TMP/t" 2>/dev/null | grep -c 'FINDING.*word')" 1
check "missing word list exits 2" "$(scan_rc --words "$TMP/nope.txt" "$TMP/t")" 2

mkdir -p "$TMP/g"
git -C "$TMP/g" init -q
printf 'x\n' > "$TMP/g/f.md"
git -C "$TMP/g" -c user.name='Real Name' -c user.email='real@corp.internal' add f.md
git -C "$TMP/g" -c user.name='Real Name' -c user.email='real@corp.internal' commit -qm init
printf 'corp\\.internal\n' > "$TMP/pats.txt"
check "history pattern caught" "$(bash "$CHK" --history --patterns "$TMP/pats.txt" "$TMP/g" 2>/dev/null | grep -c 'FINDING.*history')" 1
check "history dimension lists identity" "$(bash "$CHK" --history "$TMP/g" 2>/dev/null | grep -c 'real@corp.internal')" 1

echo "== $pass passed, $fail failed =="
[ "$fail" -eq 0 ]
