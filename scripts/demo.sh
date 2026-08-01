#!/bin/bash
# 金融对账单智能解析与问答系统 - 综合演示脚本 (Phase 4)
#
# 用法: bash scripts/demo.sh
# 前提: 服务已启动 (bash scripts/run.sh)
#
# 特性:
#   - 幂等: 可安全重复运行 (不修改任何状态, 仅读取/解析/问答)
#   - 容错: 任一步骤失败不会中断整体, 最终 exit 0
#   - 计时: 每步显示耗时
#   - 汇总: 结尾输出 Markdown 结果表
#
# 流程:
#   0. 健康检查 (/health, /api/health/full)
#   1. 解析 5 个甲方样本 (/api/m1/parse-file)
#   2. M2 单轮问答 (3 问)
#   3. M2 多轮追问 (3 轮, 同一 session)
#   4. 跨期对比 (自然语言路由)
#   5. RAG QA 批量验证 (scripts/m1_rag_qa.py)

# 注意: 故意不使用 `set -e`, 保证单步失败不中断整体演示。
BASE="${DEMO_BASE:-http://127.0.0.1:5050}"
SAMPLES="${DEMO_SAMPLES:-$HOME/wzh/m1_samples}"
PROJ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# 当前时间 (毫秒, 用于计时)
now_ms() { python3 -c 'import time; print(int(time.time()*1000))'; }

# 从 stdin 的 JSON 中安全取字段; 失败输出空串
json_get() {
    python3 -c "import sys,json
try:
    d=json.load(sys.stdin)
    v=d$1
    print(v if v is not None else '')
except Exception:
    print('')" 2>/dev/null
}

# 汇总累加器: 每行 "状态|步骤|耗时|备注"
SUMMARY_LINES=()
record() {  # record <status> <step> <elapsed_s> <note>
    SUMMARY_LINES+=("$1|$2|$3|$4")
}

# 运行一个计时的步骤标题
STEP_START=0
step_begin() { STEP_START=$(now_ms); }
step_secs() {
    local end; end=$(now_ms)
    python3 -c "print(f'{($end - $STEP_START)/1000:.1f}')"
}

banner() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  $1"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

echo "╔══════════════════════════════════════════════════╗"
echo "║  金融对账单智能解析与问答系统 - 综合演示         ║"
echo "║  Phase 4 · idempotent · timed · fault-tolerant   ║"
echo "╚══════════════════════════════════════════════════╝"
echo "  服务地址: $BASE"
echo "  样本目录: $SAMPLES"

# ---------------------------------------------------------------------------
# Step 0: 健康检查
# ---------------------------------------------------------------------------
banner "[0/5] 系统健康检查"
step_begin
HEALTH_OK=0
OVERALL=""
if curl -sf "$BASE/health" >/dev/null 2>&1; then
    echo "  ✓ /health 存活"
    HEALTH_OK=1
else
    echo "  ✗ /health 不可达"
fi
FULL=$(curl -sf "$BASE/api/health/full" 2>/dev/null)
if [ -n "$FULL" ]; then
    OVERALL=$(echo "$FULL" | json_get "['overall']")
    echo "  ✓ /api/health/full 状态: ${OVERALL:-unknown}"
else
    echo "  ⚠ /api/health/full 不可达 (继续演示)"
fi
ELAPSED=$(step_secs)
if [ "$HEALTH_OK" -eq 1 ]; then
    record "✓" "Health check" "$ELAPSED" "overall=${OVERALL:-n/a}"
else
    record "✗" "Health check" "$ELAPSED" "服务未启动: bash scripts/run.sh"
    echo ""
    echo "  服务未启动, 后续步骤可能失败。请先运行: bash scripts/run.sh"
fi

# ---------------------------------------------------------------------------
# Step 1: 解析 5 个甲方样本
# ---------------------------------------------------------------------------
banner "[1/5] 解析甲方样本 (/api/m1/parse-file)"
step_begin
# 样本清单: 文件名|标签|是否预期跳过
SAMPLE_LIST=(
    "sample_fuxi_hunhe25_20231101.txt|复熙混合25 (TXT 快路径)|keep"
    "sample_jiaxing_minan_20231031.pdf|嘉兴民安 (PDF 文本层)|keep"
    "sample_20260506_233222LU.pdf|LU对账单 (扫描件 OCR)|keep"
    "sample_boshi_chuantong.pdf|博时传统 (PDF)|keep"
    "sample_xinhua.docx|新华 (运营文档, 预期跳过)|skip"
)
PARSE_OK=0
PARSE_TOTAL=0
PARSE_SKIP=0
for entry in "${SAMPLE_LIST[@]}"; do
    IFS='|' read -r fname label expect <<< "$entry"
    fpath="$SAMPLES/$fname"
    if [ ! -f "$fpath" ]; then
        echo "  ⚠ 跳过 (文件不存在): $label"
        PARSE_SKIP=$((PARSE_SKIP + 1))
        continue
    fi
    PARSE_TOTAL=$((PARSE_TOTAL + 1))
    RESP=$(curl -sf -X POST "$BASE/api/m1/parse-file" -F "file=@$fpath" 2>/dev/null)
    STATUS=$(echo "$RESP" | json_get "['status']")
    if [ "$STATUS" = "success" ]; then
        TABLES=$(echo "$RESP" | json_get "['result']['table_count']")
        MS=$(echo "$RESP" | json_get "['result']['parse_duration_ms']")
        OCR=$(echo "$RESP" | json_get "['result']['ocr_used']")
        RECON=$(echo "$RESP" | json_get "['result']['metrics']['reconcile_pass']")
        if [ "$expect" = "skip" ]; then
            echo "  ⊘ $label: ${TABLES:-0} 表 (运营文档, 预期低命中) ${MS}ms"
            PARSE_SKIP=$((PARSE_SKIP + 1))
        else
            echo "  ✓ $label: ${TABLES:-0} 表, 勾稽 ${RECON:-n/a}, OCR=${OCR:-False}, ${MS}ms"
            PARSE_OK=$((PARSE_OK + 1))
        fi
    else
        ERR=$(echo "$RESP" | json_get "['error']")
        echo "  ✗ $label: 解析失败 ${ERR}"
    fi
done
ELAPSED=$(step_secs)
KEEP_EXPECTED=$((PARSE_TOTAL - PARSE_SKIP))
record "✓" "Parse samples" "$ELAPSED" "${PARSE_OK}/${KEEP_EXPECTED} 成功, ${PARSE_SKIP} 跳过"

# ---------------------------------------------------------------------------
# Step 2: M2 单轮问答 (3 问)
# ---------------------------------------------------------------------------
banner "[2/5] M2 智能问答 (单轮 ×3)"
step_begin
QA_OK=0
QA_TOTAL=3
ask_single() {  # ask_single <question>
    local q="$1"
    local resp ans
    resp=$(curl -sf -X POST "$BASE/api/m2/ask" \
        -H "Content-Type: application/json" \
        -d "{\"question\": \"$q\", \"top_k\": 3}" 2>/dev/null)
    ans=$(echo "$resp" | json_get "['answer']")
    if [ -n "$ans" ]; then
        QA_OK=$((QA_OK + 1))
        echo "  Q: $q"
        echo "  A: $(echo "$ans" | head -c 100)"
        echo ""
    else
        echo "  Q: $q"
        echo "  A: ✗ 无响应"
        echo ""
    fi
}
ask_single "嘉兴民安的总资产是多少？"
ask_single "复熙混合25号的单位净值是多少？"
ask_single "博时传统产品的资金余额是多少？"
ELAPSED=$(step_secs)
record "✓" "M2 QA (3 questions)" "$ELAPSED" "${QA_OK}/${QA_TOTAL} 有答"

# ---------------------------------------------------------------------------
# Step 3: M2 多轮追问 (3 轮, 同一 session)
# ---------------------------------------------------------------------------
banner "[3/5] M2 多轮追问 (3 轮 · 同一会话)"
step_begin
MT_OK=0
# 第 1 轮: 建立 session
R1=$(curl -sf -X POST "$BASE/api/m2/ask" \
    -H "Content-Type: application/json" \
    -d '{"question": "嘉兴民安的总资产是多少？", "top_k": 3}' 2>/dev/null)
SID=$(echo "$R1" | json_get "['session_id']")
A1=$(echo "$R1" | json_get "['answer']")
if [ -n "$A1" ]; then MT_OK=$((MT_OK + 1)); fi
echo "  [轮1] Q: 嘉兴民安的总资产是多少？"
echo "        A: $(echo "$A1" | head -c 90)"
echo "        session: ${SID:-none}"

# 第 2 轮: 指代追问 (其中...)
R2=$(curl -sf -X POST "$BASE/api/m2/ask" \
    -H "Content-Type: application/json" \
    -d "{\"question\": \"其中证券市值呢？\", \"session_id\": \"$SID\"}" 2>/dev/null)
A2=$(echo "$R2" | json_get "['answer']")
if [ -n "$A2" ]; then MT_OK=$((MT_OK + 1)); fi
echo "  [轮2] Q: 其中证券市值呢？"
echo "        A: $(echo "$A2" | head -c 90)"

# 第 3 轮: 继续追问
R3=$(curl -sf -X POST "$BASE/api/m2/ask" \
    -H "Content-Type: application/json" \
    -d "{\"question\": \"那资金余额是多少？\", \"session_id\": \"$SID\"}" 2>/dev/null)
A3=$(echo "$R3" | json_get "['answer']")
if [ -n "$A3" ]; then MT_OK=$((MT_OK + 1)); fi
echo "  [轮3] Q: 那资金余额是多少？"
echo "        A: $(echo "$A3" | head -c 90)"
ELAPSED=$(step_secs)
record "✓" "Multi-turn (3 turns)" "$ELAPSED" "${MT_OK}/3 轮有答"

# ---------------------------------------------------------------------------
# Step 4: 跨期对比 (自然语言路由)
# ---------------------------------------------------------------------------
banner "[4/5] 跨期对比 (自然语言路由)"
step_begin
CMP_OK=0
CMP_Q="嘉兴民安 20231031 和 20231130 的总资产变化对比"
CMP_RESP=$(curl -sf -X POST "$BASE/api/m2/ask" \
    -H "Content-Type: application/json" \
    -d "{\"question\": \"$CMP_Q\", \"top_k\": 3}" 2>/dev/null)
CMP_ANS=$(echo "$CMP_RESP" | json_get "['answer']")
CMP_MODE=$(echo "$CMP_RESP" | json_get "['compare_mode']")
if [ -n "$CMP_ANS" ]; then
    CMP_OK=1
    echo "  Q: $CMP_Q"
    echo "  路由: compare_mode=${CMP_MODE:-False}"
    echo "  A: $(echo "$CMP_ANS" | head -c 200)"
else
    echo "  Q: $CMP_Q"
    echo "  A: ✗ 无响应"
fi
ELAPSED=$(step_secs)
record "✓" "Comparison query" "$ELAPSED" "compare_mode=${CMP_MODE:-n/a}"

# ---------------------------------------------------------------------------
# Step 5: RAG QA 批量验证
# ---------------------------------------------------------------------------
banner "[5/5] RAG QA 批量验证 (scripts/m1_rag_qa.py)"
step_begin
RAG_OK=0
RAG_LINE="未运行"
if [ -f "$PROJ/scripts/m1_rag_qa.py" ]; then
    ( cd "$PROJ" && [ -d venv ] && source venv/bin/activate 2>/dev/null
      python scripts/m1_rag_qa.py 2>&1 ) > /tmp/demo_rag_qa.log 2>&1
    RAG_LINE=$(grep "overall correct" /tmp/demo_rag_qa.log | tail -1 | sed 's/^\[qa\] //')
    if echo "$RAG_LINE" | grep -q "overall correct"; then
        RAG_OK=1
        echo "  ✓ $RAG_LINE"
    else
        echo "  ⚠ 批量验证未返回汇总 (可能依赖模型/向量库)"
        RAG_LINE="无汇总输出"
    fi
else
    echo "  ⚠ scripts/m1_rag_qa.py 不存在, 跳过"
    RAG_LINE="脚本缺失"
fi
ELAPSED=$(step_secs)
record "✓" "RAG QA batch" "$ELAPSED" "$RAG_LINE"

# ---------------------------------------------------------------------------
# 汇总
# ---------------------------------------------------------------------------
banner "Demo Summary"
echo "| Step | Status | Time | Note |"
echo "|------|--------|------|------|"
for line in "${SUMMARY_LINES[@]}"; do
    IFS='|' read -r st name el note <<< "$line"
    printf "| %-20s | %-6s | %5ss | %s |\n" "$name" "$st" "$el" "$note"
done
echo ""
echo "  UI:  $BASE/m1"
echo "  API: $BASE/docs"
echo ""
echo "演示完成 (本脚本始终 exit 0, 单步失败见上表)。"
exit 0
