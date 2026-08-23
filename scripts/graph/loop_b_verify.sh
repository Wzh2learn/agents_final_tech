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
MODEL_AUX_PORT=8005          # RETIRED 2026-08-17: 仅用于 down 断言
MODEL_VERIFY_PORT=8006       # vLLM Qwen3.8-27B-FP8 (agent 验证链/judge/深度问答)
MODEL_PROXY_PORT=8008        # thinking_inject_proxy -> :8006
MODEL_ID_27B="qwen38-27b-fp8"

POLL_INTERVAL=1800

# ---- R1 增强开关 (2026-08-13) ----
# 增量开关: 默认全部 1 (启用), 可单独设 0 关闭; STEP 1-4 既有行为不变。
# QA canary 复用 m2_eval_deterministic.py 的确定性判分。
LOOP_B_CANARY="${LOOP_B_CANARY:-1}"
LOOP_B_GIT_ALIGN="${LOOP_B_GIT_ALIGN:-1}"
LOOP_B_DOCS_LINT="${LOOP_B_DOCS_LINT:-1}"

# ---- T5 升级开关 (2026-08-17, 授权例外) ----
LOOP_B_MODEL_TOPO="${LOOP_B_MODEL_TOPO:-1}"
LOOP_B_AGENT_WATCHDOG="${LOOP_B_AGENT_WATCHDOG:-1}"
LOOP_B_PYTEST="${LOOP_B_PYTEST:-1}"
AGENT_WATCHDOG_WINDOW="${AGENT_WATCHDOG_WINDOW:-30}"
AGENT_WATCHDOG_MIN_FALLBACKS="${AGENT_WATCHDOG_MIN_FALLBACKS:-25}"
# ---- T2 升级 (2026-08-24 夜, 批准): STEP 10 pg_pool_guard 哨兵 ----
# 纯 bash+psql, 无 AI。阈值: >PG_POOL_WARN WARN (信息性) / >PG_POOL_FAIL FAIL (计 overall)。
# 起源: 08-23 PG 池打满事故 (max_connections=100, 泄漏 7 天打满); GUC 10min + 实例缓存已根治, 本项为哨兵。
LOOP_B_PG_POOL="${LOOP_B_PG_POOL:-1}"
PG_POOL_WARN="${PG_POOL_WARN:-80}"
PG_POOL_FAIL="${PG_POOL_FAIL:-95}"

B4_LOG="$REPORT_DIR/b4_ask_log.jsonl"
CANARY_IDS="${LOOP_B_CANARY_IDS:-adv_ocr_meta,adv_refusal,q06_minan_cash_balance,adv_cross_doc}"
CANARY_TIMEOUT="${LOOP_B_CANARY_TIMEOUT:-75}"  # T5: 45s ask 超时 + 回落直连最坏 ~60s, 45 不够
CANARY_BUDGET=360  # T5: 4 题 x 最坏 ~75s 余量
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
    > "$REPORT_DIR/pytest_loopb.txt" 2>&1 || pytest_exit=$?  # [2026-08-23 批准] 子集写 pytest_loopb.txt; pytest_latest.txt 只接受收口全量

  local summary
  summary=$(tail -3 "$REPORT_DIR/pytest_loopb.txt")
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

  # 3d. Model services (T5: aux 已退位; 双模型拓扑断言见 STEP 8)
  for port in $MODEL_MAIN_PORT; do
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
  # [2026-08-19 用户批准: STEP4 白名单] 运行时状态文件豁免清单 —
  # config/schema_suggestions.json 是自学习闭环的合法写入目标
  # (kiosk 播放期间持续写观察计数), 不计入报警 dirty;
  # [2026-08-23 用户批准: 白名单扩充] +4 件:
  # logs/graph/dispatch_log.md (事件流, 主线程收口与 Loop B 翻转写入) /
  # logs/graph/docs_lint_report.json (docs_lint.py 自动写报告工件) /
  # logs/graph/pytest_latest.txt (只接受收口全量, Loop B STEP2 已分流) /
  # logs/graph/pytest_loopb.txt (Loop B STEP2 子集工件, 每周期覆写, 分流天然推论) /
  # [2026-08-23 用户批准: 白名单再扩 2 件]
  # logs/graph/verify-report.json (Loop B 周期报告, 含 timestamp 字段每周期必脏) /
  # logs/graph/loop_b_last_status (Loop B 翻转状态位, 已被 git 跟踪——核查坐实, 翻转日必脏)。
  # 其余脏文件照常计数报警。清单变更需 Loop D 批准。
  local dirty whitelisted_dirty
  dirty=$(git status --porcelain 2>/dev/null | grep -vE ' config/schema_suggestions\.json$| logs/graph/(dispatch_log\.md|docs_lint_report\.json|pytest_latest\.txt|pytest_loopb\.txt|verify-report\.json|loop_b_last_status)$' | wc -l)
  whitelisted_dirty=$(git status --porcelain 2>/dev/null | grep -cE ' config/schema_suggestions\.json$| logs/graph/(dispatch_log\.md|docs_lint_report\.json|pytest_latest\.txt|pytest_loopb\.txt|verify-report\.json|loop_b_last_status)$' || true)

  log "  HEAD=$head_commit branch=$branch dirty_files=$dirty whitelisted=$whitelisted_dirty (白名单 7 件: schema_suggestions + logs/graph 运行时 6 件)"

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

# ---- Step 8: 双模型拓扑断言 (T5, 2026-08-17) ----
# Returns: violation count
check_model_topology() {
  log "STEP 8: dual-model topology assertions..."
  local violations=0 code models

  code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 "http://127.0.0.1:${MODEL_MAIN_PORT}/health" 2>/dev/null)
  code=${code:-000}
  if [[ "$code" == "200" ]]; then
    log "  OK: :${MODEL_MAIN_PORT} A3B healthy"
  else
    violations=$((violations + 1)); log "  FAIL: :${MODEL_MAIN_PORT} A3B down (code=$code)"
  fi

  models=$(curl -s --max-time 5 "http://127.0.0.1:${MODEL_VERIFY_PORT}/v1/models" 2>/dev/null || echo "")
  if echo "$models" | grep -q "$MODEL_ID_27B"; then
    log "  OK: :${MODEL_VERIFY_PORT} serves $MODEL_ID_27B"
  else
    violations=$((violations + 1)); log "  FAIL: :${MODEL_VERIFY_PORT} missing $MODEL_ID_27B"
  fi

  models=$(curl -s --max-time 5 "http://127.0.0.1:${MODEL_PROXY_PORT}/v1/models" 2>/dev/null || echo "")
  if echo "$models" | grep -q "$MODEL_ID_27B"; then
    log "  OK: :${MODEL_PROXY_PORT} proxy passes $MODEL_ID_27B"
  else
    violations=$((violations + 1)); log "  FAIL: :${MODEL_PROXY_PORT} proxy missing $MODEL_ID_27B"
  fi

  code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 3 "http://127.0.0.1:${MODEL_AUX_PORT}/health" 2>/dev/null)
  code=${code:-000}
  if [[ "$code" == "000" ]]; then
    log "  OK: :${MODEL_AUX_PORT} retired (down as expected)"
  else
    violations=$((violations + 1)); log "  FAIL: :${MODEL_AUX_PORT} should be retired but responds (code=$code)"
  fi

  echo "$violations"
}

# ---- Step 9: B4 agent 完成率看门狗 (T5, 2026-08-17) ----
# 滚动窗口: route=on 但 agent 路持续零完成 (全回落) => 灰度路静默死亡。
# 计数窗口 (非时间窗), 低流量不误报; route 主动 off 时 fell_back=false, 亦不误报。
# Returns: 0=PASS, 1=alarm
check_b4_agent_watchdog() {
  log "STEP 9: B4 agent completion watchdog (window=$AGENT_WATCHDOG_WINDOW)..."
  if [[ ! -f "$B4_LOG" ]]; then
    log "  SKIP: no b4 log yet"
    echo 0
    return
  fi
  local verdict
  verdict=$("$VENV_PYTHON" - "$B4_LOG" "$AGENT_WATCHDOG_WINDOW" "$AGENT_WATCHDOG_MIN_FALLBACKS" <<'PYCHK'
import json, sys
path, window, min_fb = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
rows = []
for line in open(path, encoding="utf-8"):
    line = line.strip()
    if line:
        try:
            rows.append(json.loads(line))
        except Exception:
            pass
rows = rows[-window:]
if len(rows) < window:
    print("SKIP"); sys.exit(0)
agent_clean = sum(1 for r in rows if r.get("route") == "agent" and not r.get("fell_back"))
fell_back = sum(1 for r in rows if r.get("fell_back"))
if agent_clean == 0 and fell_back >= min_fb:
    print("ALARM"); sys.exit(0)
print("OK")
PYCHK
  )
  if [[ "$verdict" == "ALARM" ]]; then
    log "  FAIL: last $AGENT_WATCHDOG_WINDOW asks: 0 agent completions, >=$AGENT_WATCHDOG_MIN_FALLBACKS fallbacks — agent route not carrying traffic"
    echo 1
  else
    log "  $verdict: agent-route watchdog"
    echo 0
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
  local topo_violations=${8:-0}    # -1 = SKIP (T5)
  local watchdog_violations=${9:-0} # -1 = SKIP (T5)

  local overall="PASS"
  if [[ "$frozen_violations" -gt 0 ]] || [[ "$pytest_exit" -ne 0 ]] || [[ "$api_failures" -gt 0 ]] \
     || [[ "$canary_failures" -gt 0 ]] || [[ "$git_violations" -gt 0 ]] || [[ "$lint_failures" -gt 0 ]] \
     || [[ "$topo_violations" -gt 0 ]] || [[ "$watchdog_violations" -gt 0 ]]; then
    overall="FAIL"
  fi

  python3 "$GRAPH_DIR/write_report.py" \
    "$frozen_violations" "$pytest_exit" "$api_failures" "$head_commit" "$REPORT_FILE" \
    "$canary_failures" "$git_violations" "$lint_failures" \
    "$topo_violations" "$watchdog_violations" "$pgpool_violations" \
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

# ---- Step 10: PG Pool Guard (T2 2026-08-24, 纯 bash+psql 哨兵) ----
# Returns: 0 = PASS/WARN (WARN 仅信息性), 1 = FAIL (连接数 > PG_POOL_FAIL; 探测失败 WARN 不计败, 可用性由 STEP 3 兜底)
check_pg_pool() {
  log "STEP 10: pg_pool_guard (warn>${PG_POOL_WARN}/fail>${PG_POOL_FAIL})..."
  local cnt
  cnt=$(docker exec pgvector_15432 psql -U postgres -t -A -c "select count(*) from pg_stat_activity where datname is not null" 2>/dev/null | tr -d '[:space:]')
  if [[ -z "$cnt" || ! "$cnt" =~ ^[0-9]+$ ]]; then
    log "  WARNING: pg_pool_guard 探测失败 (docker/psql 不可达); 可用性由 STEP 3 api_anchors 兜底"
    echo 0
    return
  fi
  if (( cnt > PG_POOL_FAIL )); then
    log "  FAIL: pg pool connections=$cnt > ${PG_POOL_FAIL} (饱和风险; 对照 08-23 事故台账, 查 pg_stat_activity 泄漏端)"
    echo 1
  elif (( cnt > PG_POOL_WARN )); then
    log "  WARN: pg pool connections=$cnt > ${PG_POOL_WARN} (疑似泄漏增长, 建议查 pg_stat_activity 按进程归因)"
    echo 0
  else
    log "  OK: pg pool connections=$cnt (<= ${PG_POOL_WARN})"
    echo 0
  fi
}

# ---- Main Verification Run ----
run_verification() {
  log "=========================================="
  log "Loop B verification starting..."
  log "=========================================="

  # Each function logs to stderr, returns a single value on stdout
  local frozen_violations pytest_exit api_failures head_commit overall
  local canary_failures=-1 git_violations=-1 lint_failures=-1
  local topo_violations=-1 watchdog_violations=-1
  local pgpool_violations=-1

  frozen_violations=$(check_frozen_nodes)
  if [[ "$LOOP_B_PYTEST" == "1" ]]; then
    pytest_exit=$(run_pytest)
  else
    pytest_exit=0
    log "STEP 2: pytest SKIPPED (LOOP_B_PYTEST=0)"
  fi
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
  if [[ "$LOOP_B_MODEL_TOPO" == "1" ]]; then
    topo_violations=$(check_model_topology)
  else
    log "STEP 8: model topology SKIPPED (LOOP_B_MODEL_TOPO=0)"
  fi
  if [[ "$LOOP_B_AGENT_WATCHDOG" == "1" ]]; then
    watchdog_violations=$(check_b4_agent_watchdog)
  else
    log "STEP 9: agent watchdog SKIPPED (LOOP_B_AGENT_WATCHDOG=0)"
  fi
  if [[ "$LOOP_B_PG_POOL" == "1" ]]; then
    pgpool_violations=$(check_pg_pool)
  else
    log "STEP 10: pg_pool_guard SKIPPED (LOOP_B_PG_POOL=0)"
  fi
  head_commit=$(check_git_state)

  overall=$(write_report "$frozen_violations" "$pytest_exit" "$api_failures" "$head_commit" \
    "$canary_failures" "$git_violations" "$lint_failures" "$topo_violations" "$watchdog_violations")

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
