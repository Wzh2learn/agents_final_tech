#!/usr/bin/env bash
# Positive and negative tests for scripts/graph/hooks/git-commit-guard.sh.
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CHK="$HERE/scripts/graph/hooks/git-commit-guard.sh"
pass=0
fail=0

run() {
  printf '%s' "$1" | bash "$CHK" >/tmp/git-commit-guard.out 2>/tmp/git-commit-guard.err
  echo $?
}

check() {
  local name=$1 input=$2 expected=$3
  local actual
  actual=$(run "$input")
  if [ "$actual" = "$expected" ]; then
    echo "PASS $name"
    pass=$((pass + 1))
  else
    echo "FAIL $name: got $actual want $expected"
    fail=$((fail + 1))
  fi
}

check "normal push passes" '{"tool_input":{"command":"git push origin main"}}' 0
check "force short flag blocks" '{"tool_input":{"command":"git push -f origin main"}}' 2
check "force long flag blocks" '{"tool_input":{"command":"git push --force origin main"}}' 2
check "force-with-lease blocks" '{"tool_input":{"command":"git push --force-with-lease origin main"}}' 2
check "git -C force push blocks" '{"tool_input":{"command":"git -C /tmp/repo push --force origin main"}}' 2
check "normal commit passes" '{"tool_input":{"command":"git commit -m test"}}' 0
check "amend blocks" '{"tool_input":{"command":"git commit --amend -m test"}}' 2
check "unrelated command passes" '{"tool_input":{"command":"git status --short"}}' 0
check "malformed JSON degrades visibly" '{"tool_input":' 0

if grep -q 'guard degraded' /tmp/git-commit-guard.err; then
  echo "PASS malformed JSON emits degradation warning"
  pass=$((pass + 1))
else
  echo "FAIL malformed JSON emits degradation warning"
  fail=$((fail + 1))
fi

echo "== $pass passed, $fail failed =="
[ "$fail" -eq 0 ]
