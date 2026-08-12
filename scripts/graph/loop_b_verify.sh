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

API_BASE="${M1_API_BASE:-http://127.0.0.1:5050}"
MODEL_MAIN_PORT=8004
MODEL_AUX_PORT=8005

POLL_INTERVAL=1800

# ---- R1 增强开关 (2026-08-13) ----
# 增量开关: 默认全部 1 (启用), 可单独设 0 关闭; STEP 1-4 既有行为不变。
# QA canary 复用 m2_eval_deterministic.py 的确定性判分。
LOOP_B_CANARY="${LOOP_B_CANARY:-1}"
LOOP_B_GIT_ALIGN="${LOOP_B_GIT_ALIGN:-1}"
LOOP_B_DOCS_LINT="${LOOP_B_DOCS_LINT:-1}"
CANARY_IDS="${LOOP_B_CANARY_IDS:-adv_ocr_meta,adv_refusal,q06_minan_cash_balance,adv_cross_doc}"
CANARY_TIMEOUT="${LOOP_B_CANARY_TIMEOUT:-45}"
CANARY_BUDGET=240
STATE_FILE="$REPORT_DIR/loop_b_last_status"
DISPATCH_LOG="$REPORT_DIR/dispatch_log.md"

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

# ---- Step 5: QA Canary Sentinel (R1, flag-gated) ----
# 复用 m2_eval_deterministic.py 确定性判分: OCR meta-query 回归哨兵 + 拒答题 + 数值题 + 跨文档题
# Returns: 0=全过; 1=有题失败或服务不可用
run_qa_canary() {
  log "STEP 5: QA canary sentinel (${CANARY_IDS})..."
  cd "$PROJECT_DIR"
  local py="$VENV_PYTHON"
  if [[ ! -x "$py" ]]; then
    py="python3"
  fi
  local rc=0
  timeout "$CANARY_BUDGET" "$py" scripts/m2_eval_deterministic.py \
    --only "$CANARY_IDS" --timeout "$CANARY_TIMEOUT" \
    --report "$REPORT_DIR/eval/m2_canary_report.json" \
    > "$REPORT_DIR/canary_latest.txt" 2>&1 || rc=$?
  local summary
  summary=$(tail -2 "$REPORT_DIR/canary_latest.txt" | tr '\n' ' ')
  if [[ "$rc" -eq 0 ]]; then
    log "  OK: canary all pass | $summary"
    echo 0
  else
    log "  FAIL: canary exit=$rc | $summary"
    echo 1
  fi
}

# ---- Step 6: Git Alignment (R1, flag-gated; GB10 视角) ----
# 本地 (Windows) 对齐由 Loop D 单独保证, 此处只查 GB10 HEAD vs origin/main
# Returns: 0=对齐或 origin 不可达(网络问题不计违规); 1=HEAD 分叉
check_git_alignment() {
  log "STEP 6: git alignment (GB10 HEAD vs origin/main)..."
  cd "$PROJECT_DIR"
  local head_full remote_main
  head_full=$(git rev-parse HEAD 2>/dev/null || echo "")
  remote_main=$(timeout 20 git ls-remote origin main 2>/dev/null | awk '{print $1}' | head -1)
  if [[ -z "$remote_main" ]]; then
    log "  SKIP: origin unreachable (network?), not counted"
    echo 0
    return
  fi
  if [[ "$head_full" == "$remote_main" ]]; then
    log "  OK: aligned at ${head_full:0:7}"
    echo 0
  else
    log "  FAIL: GB10=${head_full:0:7} origin/main=${remote_main:0:7}"
    echo 1
  fi
}

# ---- Step 7: docs_lint (R1, flag-gated) ----
# Returns: 0=PASS; 1=有 fail
run_docs_lint() {
  log "STEP 7: docs_lint..."
  cd "$PROJECT_DIR"
  local py="$VENV_PYTHON"
  if [[ ! -x "$py" ]]; then
    py="python3"
  fi
  local rc=0 out
  out=$(timeout 120 "$py" scripts/docs_lint.py 2>&1) || rc=$?
  if [[ "$rc" -eq 0 ]]; then
    log "  OK: docs_lint PASS"
    echo 0
  else
    log "  FAIL: docs_lint exit=$rc"
    local line
    while IFS= read -r line; do
      [[ -n "$line" ]] && log "    $line"
    done <<< "$(echo "$out" | grep '^FAIL' | head -5)"
    echo 1
  fi
}

# ---- Write Report ----
write_report() {
  local frozen_violations=$1
  local pytest_exit=$2
  local api_failures=$3
  local head_commit=$4
  local canary_failures=$5   # -1 = SKIP
  local git_violations=$6    # -1 = SKIP
  local lint_failures=$7     # -1 = SKIP

  local overall="PASS"
  if [[ "$frozen_violations" -gt 0 ]] || [[ "$pytest_exit" -ne 0 ]] || [[ "$api_failures" -gt 0 ]] \
     || [[ "$canary_failures" -gt 0 ]] || [[ "$git_violations" -gt 0 ]] || [[ "$lint_failures" -gt 0 ]]; then
    overall="FAIL"
  fi

  python3 "$GRAPH_DIR/write_report.py" \
    "$frozen_violations" "$pytest_exit" "$api_failures" "$head_commit" "$REPORT_FILE" \
    "$canary_failures" "$git_violations" "$lint_failures" \
    2>/dev/null || log "  WARNING: report write failed"

  log "REPORT: overall=$overall -> $REPORT_FILE"
  echo "$overall"
}

# ---- FAIL 翻转检测 (R1: 只在状态翻转时写 dispatch_log, 不每周期刷屏) ----
record_status_flip() {
  local overall=$1
  local prev="UNKNOWN"
  if [[ -f "$STATE_FILE" ]]; then
    prev=$(cat "$STATE_FILE" 2>/dev/null || echo "UNKNOWN")
  fi
  if [[ "$overall" == "$prev" ]]; then
    return
  fi
  echo "$overall" > "$STATE_FILE"
  if [[ "$prev" == "UNKNOWN" ]]; then
    log "STATUS init: $overall (first run, no dispatch entry)"
    return
  fi
  local head_short
  head_short=$(git -C "$PROJECT_DIR" rev-parse --short HEAD 2>/dev/null || echo "?")
  echo "[$(date '+%m-%d %H:%M')] #LOOP-B-FLIP overall $prev -> $overall (head=$head_short; 详见 logs/graph/verify-report.json + loop_b.log)" >> "$DISPATCH_LOG"
  log "STATUS FLIP: $prev -> $overall, dispatch_log entry written"
}

# ---- Main Verification Run ----
run_verification() {
  log "=========================================="
  log "Loop B verification starting..."
  log "=========================================="

  # Each function logs to stderr, returns a single value on stdout
  local frozen_violations pytest_exit api_failures head_commit overall
  local canary_failures=-1 git_violations=-1 lint_failures=-1

  frozen_violations=$(check_frozen_nodes)
  pytest_exit=$(run_pytest)
  api_failures=$(check_api_anchors)
  if [[ "$LOOP_B_CANARY" == "1" ]]; then
    canary_failures=$(run_qa_canary)
  else
    log "STEP 5: QA canary SKIPPED (LOOP_B_CANARY=0)"
  fi
  if [[ "$LOOP_B_GIT_ALIGN" == "1" ]]; then
    git_violations=$(check_git_alignment)
  else
    log "STEP 6: git alignment SKIPPED (LOOP_B_GIT_ALIGN=0)"
  fi
  if [[ "$LOOP_B_DOCS_LINT" == "1" ]]; then
    lint_failures=$(run_docs_lint)
  else
    log "STEP 7: docs_lint SKIPPED (LOOP_B_DOCS_LINT=0)"
  fi
  head_commit=$(check_git_state)

  overall=$(write_report "$frozen_violations" "$pytest_exit" "$api_failures" "$head_commit" \
    "$canary_failures" "$git_violations" "$lint_failures")

  record_status_flip "$overall"

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
