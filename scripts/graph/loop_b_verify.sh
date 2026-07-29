#!/bin/bash
# ============================================================
# Graph Engineering - Loop B: Independent Verification Guardian
# ============================================================
# 纯脚本验证, 不用 AI, 不会"耍花招"。
# 职责: 校验冻结文件 -> 跑 pytest -> curl API -> 写报告
#
# 用法:
#   bash scripts/graph/loop_b_verify.sh          # 单次验证
#   bash scripts/graph/loop_b_verify.sh --daemon  # 持续轮询 (30min)
# ============================================================

set -uo pipefail

PROJECT_DIR="$HOME/wzh/projects/agents_final_tech"
GRAPH_DIR="$PROJECT_DIR/scripts/graph"
REPORT_DIR="$PROJECT_DIR/logs/graph"
FROZEN_FILE="$GRAPH_DIR/frozen_hashes.txt"
REPORT_FILE="$REPORT_DIR/verify-report.json"
LOG_FILE="$REPORT_DIR/loop_b.log"
VENV_PYTHON="$PROJECT_DIR/venv/bin/python"

API_BASE="${M1_API_BASE:-http://127.0.0.1:5000}"
MODEL_MAIN_PORT=8004
MODEL_AUX_PORT=8005

POLL_INTERVAL=1800

mkdir -p "$REPORT_DIR"

# log goes to stderr + logfile, NEVER to stdout (stdout is for return values)
log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >&2
}

# ---- Step 1: Frozen Node Integrity Check ----
# Returns: integer violation count on stdout
check_frozen_nodes() {
  log "STEP 1: Checking frozen node integrity..."
  local violations=0

  while IFS= read -r line; do
    # Skip comments (lines starting with #) and empty lines
    case "$line" in
      '#'*|'') continue ;;
    esac

    # Only process lines that look like: <32-char-hex>  <path>
    local expected_md5 filepath
    expected_md5=$(echo "$line" | awk '{print $1}')
    filepath=$(echo "$line" | awk '{print $2}')

    # Validate md5 format (32 hex chars)
    if ! echo "$expected_md5" | grep -qE '^[0-9a-f]{32}$'; then
      continue
    fi
    # Skip if no filepath
    if [[ -z "$filepath" ]]; then
      continue
    fi

    # Resolve relative paths against project dir
    if [[ "$filepath" != /* ]]; then
      filepath="$PROJECT_DIR/$filepath"
    fi

    if [[ ! -f "$filepath" ]]; then
      violations=$((violations + 1))
      log "  FROZEN VIOLATION: $filepath is MISSING"
      continue
    fi

    local actual_md5
    actual_md5=$(md5sum "$filepath" | awk '{print $1}')

    if [[ "$actual_md5" != "$expected_md5" ]]; then
      violations=$((violations + 1))
      log "  FROZEN VIOLATION: $filepath hash mismatch!"
    else
      log "  OK: $filepath"
    fi
  done < "$FROZEN_FILE"

  # Check test file count
  local test_count
  test_count=$(find "$PROJECT_DIR/tests" -name "test_*.py" 2>/dev/null | wc -l)
  if [[ "$test_count" -lt 10 ]]; then
    violations=$((violations + 1))
    log "  FROZEN VIOLATION: test file count dropped to $test_count"
  fi

  echo "$violations"
}

# ---- Step 2: Independent pytest Run ----
# Returns: pytest exit code on stdout
run_pytest() {
  log "STEP 2: Running pytest independently..."
  cd "$PROJECT_DIR"

  local py="$VENV_PYTHON"
  if [[ ! -x "$py" ]]; then
    py="python3"
  fi

  local pytest_exit=0
  "$py" -m pytest tests/test_m1_service.py -v --tb=short \
    > "$REPORT_DIR/pytest_latest.txt" 2>&1 || pytest_exit=$?

  local summary
  summary=$(tail -3 "$REPORT_DIR/pytest_latest.txt")
  log "  pytest exit=$pytest_exit | $summary"

  echo "$pytest_exit"
}

# ---- Step 3: API Endpoint Anchors ----
# Returns: integer failure count on stdout
check_api_anchors() {
  log "STEP 3: Checking API anchors..."
  local failures=0

  # 3a. App health
  local code
  code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 "$API_BASE/health" 2>/dev/null || echo "000")
  if [[ "$code" == "200" ]]; then
    log "  OK: /health -> 200"
  else
    failures=$((failures + 1))
    log "  FAIL: /health -> $code"
  fi

  # 3b. M1 sample endpoint
  code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 "$API_BASE/api/m1/sample" 2>/dev/null || echo "000")
  if [[ "$code" == "200" ]]; then
    log "  OK: /api/m1/sample -> 200"
  else
    failures=$((failures + 1))
    log "  FAIL: /api/m1/sample -> $code"
  fi

  # 3c. M1 extract endpoint
  code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 -X POST "$API_BASE/api/m1/extract" \
    -H "Content-Type: application/json" \
    -d '{"text":"规则一：测试规则。触发条件：当某业务事件发生且满足预设条件时触发执行。执行动作：系统执行相应操作并记录完整日志以便追溯。"}' 2>/dev/null || echo "000")
  if [[ "$code" == "200" ]]; then
    log "  OK: /api/m1/extract -> 200"
  else
    failures=$((failures + 1))
    log "  FAIL: /api/m1/extract -> $code"
  fi

  # 3d. Model services
  for port in $MODEL_MAIN_PORT $MODEL_AUX_PORT; do
    local mh
    mh=$(curl -s --max-time 5 "http://127.0.0.1:${port}/health" 2>/dev/null || echo "")
    if echo "$mh" | grep -q "ok"; then
      log "  OK: model :$port healthy"
    else
      failures=$((failures + 1))
      log "  FAIL: model :$port not responding"
    fi
  done

  echo "$failures"
}

# ---- Step 4: Git State Check ----
# Returns: short commit hash on stdout
check_git_state() {
  log "STEP 4: Checking git state..."
  cd "$PROJECT_DIR"

  local head_commit
  head_commit=$(git rev-parse --short HEAD 2>/dev/null || echo "UNKNOWN")
  local branch
  branch=$(git branch --show-current 2>/dev/null || echo "UNKNOWN")
  local dirty
  dirty=$(git status --porcelain 2>/dev/null | wc -l)

  log "  HEAD=$head_commit branch=$branch dirty_files=$dirty"

  # Check if tests/ was modified in last commit
  local test_modified
  test_modified=$(git diff --name-only HEAD~1 HEAD 2>/dev/null | grep -c '^tests/' || true)
  if [[ "${test_modified:-0}" -gt 0 ]]; then
    log "  WARNING: tests/ was modified in last commit!"
  fi

  echo "$head_commit"
}

# ---- Write Report ----
write_report() {
  local frozen_violations=$1
  local pytest_exit=$2
  local api_failures=$3
  local head_commit=$4

  local overall="PASS"
  if [[ "$frozen_violations" -gt 0 ]] || [[ "$pytest_exit" -ne 0 ]] || [[ "$api_failures" -gt 0 ]]; then
    overall="FAIL"
  fi

  local frozen_status="PASS"
  [[ "$frozen_violations" -gt 0 ]] && frozen_status="FAIL"
  local pytest_status="PASS"
  [[ "$pytest_exit" -ne 0 ]] && pytest_status="FAIL"
  local api_status="PASS"
  [[ "$api_failures" -gt 0 ]] && api_status="FAIL"
  local action="Loop A may continue"
  [[ "$overall" == "FAIL" ]] && action="HALT: Loop A must fix before proceeding"

  python3 "$GRAPH_DIR/write_report.py" \
    "$frozen_violations" "$pytest_exit" "$api_failures" "$head_commit" "$REPORT_FILE" \
    2>/dev/null || log "  WARNING: report write failed"

  log "REPORT: overall=$overall -> $REPORT_FILE"
}

# ---- Main Verification Run ----
run_verification() {
  log "=========================================="
  log "Loop B verification starting..."
  log "=========================================="

  # Each function logs to stderr, returns a single value on stdout
  local frozen_violations pytest_exit api_failures head_commit

  frozen_violations=$(check_frozen_nodes)
  pytest_exit=$(run_pytest)
  api_failures=$(check_api_anchors)
  head_commit=$(check_git_state)

  write_report "$frozen_violations" "$pytest_exit" "$api_failures" "$head_commit"

  log "Loop B verification complete."
}

# ---- Entry Point ----
if [[ "${1:-}" == "--daemon" ]]; then
  log "Loop B starting in daemon mode (poll every ${POLL_INTERVAL}s)"
  while true; do
    run_verification
    log "Sleeping ${POLL_INTERVAL}s until next check..."
    sleep "$POLL_INTERVAL"
  done
else
  run_verification
fi
