#!/bin/bash
# 金融对账单智能解析与问答系统 - 一键演示脚本
# 用法: bash scripts/demo.sh
# 前提: 服务已启动 (bash scripts/run.sh)

set -e
BASE="http://127.0.0.1:5050"
SAMPLES="$HOME/wzh/m1_samples"

echo "╔══════════════════════════════════════════════════╗"
echo "║  金融对账单智能解析与问答系统 - 演示             ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# 0. Health check
echo "▶ [0/6] 系统健康检查..."
HEALTH=$(curl -sf "$BASE/api/health/full" 2>/dev/null)
if [ $? -ne 0 ]; then
    echo "  ✗ 服务未启动! 请先运行: bash scripts/run.sh"
    exit 1
fi
OVERALL=$(echo "$HEALTH" | python3 -c "import sys,json; print(json.load(sys.stdin)['overall'])" 2>/dev/null)
echo "  ✓ 系统状态: $OVERALL"
echo ""

# 1. Parse TXT (fast path)
echo "▶ [1/6] 解析 TXT 对账单 (复熙混合25号)..."
if [ -f "$SAMPLES/sample_fuxi_hunhe25_20231101.txt" ]; then
    RESP=$(curl -sf -X POST "$BASE/api/m1/parse-file" \
        -F "file=@$SAMPLES/sample_fuxi_hunhe25_20231101.txt")
    TABLES=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['result']['table_count'])" 2>/dev/null)
    MS=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['result']['parse_duration_ms'])" 2>/dev/null)
    echo "  ✓ 解析完成: ${TABLES} 表, ${MS}ms"
else
    echo "  ⚠ 样本文件不存在, 跳过"
fi
echo ""

# 2. Parse PDF (text layer)
echo "▶ [2/6] 解析 PDF 对账单 (嘉兴民安)..."
if [ -f "$SAMPLES/sample_jiaxing_minan_20231031.pdf" ]; then
    RESP=$(curl -sf -X POST "$BASE/api/m1/parse-file" \
        -F "file=@$SAMPLES/sample_jiaxing_minan_20231031.pdf")
    TABLES=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['result']['table_count'])" 2>/dev/null)
    RECONCILE=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['result']['metrics']['reconcile_pass'])" 2>/dev/null)
    MS=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['result']['parse_duration_ms'])" 2>/dev/null)
    echo "  ✓ 解析完成: ${TABLES} 表, 勾稽 ${RECONCILE}, ${MS}ms"
else
    echo "  ⚠ 样本文件不存在, 跳过"
fi
echo ""

# 3. Parse PDF (OCR)
echo "▶ [3/6] 解析扫描件 PDF (LU对账单, 需OCR ~30s)..."
if [ -f "$SAMPLES/sample_20260506_233222LU.pdf" ]; then
    RESP=$(curl -sf -X POST "$BASE/api/m1/parse-file" \
        -F "file=@$SAMPLES/sample_20260506_233222LU.pdf")
    TABLES=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['result']['table_count'])" 2>/dev/null)
    OCR=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['result']['ocr_used'])" 2>/dev/null)
    MS=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['result']['parse_duration_ms'])" 2>/dev/null)
    echo "  ✓ 解析完成: ${TABLES} 表, OCR=${OCR}, ${MS}ms"
else
    echo "  ⚠ 样本文件不存在, 跳过"
fi
echo ""

# 4. M2 QA - single turn
echo "▶ [4/6] M2 智能问答 (单轮)..."
RESP=$(curl -sf -X POST "$BASE/api/m2/ask" \
    -H "Content-Type: application/json" \
    -d '{"question": "嘉兴民安的总资产是多少？"}')
ANS=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['answer'][:80])" 2>/dev/null)
SID=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['session_id'])" 2>/dev/null)
echo "  Q: 嘉兴民安的总资产是多少？"
echo "  A: $ANS"
echo ""

# 5. M2 QA - multi-turn
echo "▶ [5/6] M2 多轮追问..."
RESP2=$(curl -sf -X POST "$BASE/api/m2/ask" \
    -H "Content-Type: application/json" \
    -d "{\"question\": \"其中证券市值呢？\", \"session_id\": \"$SID\"}")
ANS2=$(echo "$RESP2" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['answer'][:80])" 2>/dev/null)
echo "  Q: 其中证券市值呢？"
echo "  A: $ANS2"
echo ""

RESP3=$(curl -sf -X POST "$BASE/api/m2/ask" \
    -H "Content-Type: application/json" \
    -d "{\"question\": \"资金余额是多少？\", \"session_id\": \"$SID\"}")
ANS3=$(echo "$RESP3" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['answer'][:80])" 2>/dev/null)
echo "  Q: 资金余额是多少？"
echo "  A: $ANS3"
echo ""

# 6. RAG QA batch
echo "▶ [6/6] RAG QA 批量验证 (15 queries)..."
cd ~/wzh/projects/agents_final_tech
source venv/bin/activate 2>/dev/null
QA_RESULT=$(python scripts/m1_rag_qa.py 2>&1 | grep "overall correct")
echo "  $QA_RESULT"
echo ""

echo "╔══════════════════════════════════════════════════╗"
echo "║  演示完成!                                       ║"
echo "║  UI: http://localhost:5050/m1                    ║"
echo "║  API: http://localhost:5050/docs                 ║"
echo "╚══════════════════════════════════════════════════╝"
