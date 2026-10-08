#!/usr/bin/env bash
# Positive and negative tests for scripts/graph/hooks/gpu-lock-guard.sh.
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CHK="$HERE/scripts/graph/hooks/gpu-lock-guard.sh"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/gpu-lock-guard.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT
LOCK="$TMP/gpu.lock"
mkdir -p "$TMP/not-a-file"
: > "$LOCK"
pass=0
fail=0

run() {
  local command=$1
  local lock_file=${2:-$LOCK}
  printf '{"tool_input":{"command":%s}}' "$(printf '%s' "$command" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')" \
    | GPU_LOCK_FILE="$lock_file" bash "$CHK" >/tmp/gpu-lock-guard.out 2>/tmp/gpu-lock-guard.err
  echo $?
}

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

check "ordinary command passes" "$(run 'git status --short')" 0
check "GPU monitoring passes" "$(run 'nvidia-smi')" 0
check "training with free lock passes" "$(run 'python train.py')" 0
check "accelerate launch is training" "$(run 'accelerate launch train.py')" 0
check "invalid lock path blocks" "$(run 'python train.py' "$TMP/not-a-file")" 2
check "malformed JSON blocks" "$(printf '{"tool_input":' | GPU_LOCK_FILE="$LOCK" bash "$CHK" >/dev/null 2>&1; echo $?)" 2

cat > "$TMP/heredoc-command.txt" <<'TESTEOF'
cat > run.sh <<EOF
python train.py
EOF
TESTEOF
HEREDOC=$(python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))' < "$TMP/heredoc-command.txt")
printf '{"tool_input":{"command":%s}}' "$HEREDOC" | GPU_LOCK_FILE="$LOCK" bash "$CHK" >/dev/null 2>&1
check "heredoc body is not executed" "$?" 0

flock "$LOCK" bash -c 'touch "$1"; sleep 2' _ "$TMP/ready" &
HOLDER=$!
for _ in 1 2 3 4 5 6 7 8 9 10; do
  [ -e "$TMP/ready" ] && break
  sleep 0.1
done
check "held lock blocks training" "$(run 'python train.py')" 2
wait "$HOLDER"

echo "== $pass passed, $fail failed =="
[ "$fail" -eq 0 ]
