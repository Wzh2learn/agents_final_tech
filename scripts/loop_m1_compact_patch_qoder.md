# 任务：M1 parser 紧凑摘要 + C 待审补丁回写（Qoder CLI 执行）

## 前置检查（硬性，不满足则 BLOCKED 记录后停）

```bash
# 1. Qoder 认证
test -n "$QODER_PERSONAL_ACCESS_TOKEN" || { echo "BLOCKED: QODER_PERSONAL_ACCESS_TOKEN not set"; exit 1; }
# 2. Qoder 二进制
QODER="$HOME/.local/qoder/node_modules/.bin/qodercli"
test -x "$QODER" || { echo "BLOCKED: qodercli not found at $QODER"; exit 1; }
# 3. 本地模型
curl -s http://127.0.0.1:8004/v1/models | head -3 || { echo "BLOCKED: :8004 not reachable"; exit 1; }
```

## 背景

你在 GB10 开发机上，项目 `~/wzh/projects/agents_final_tech`。
D 报告发现双跳 BLOCKED 的根因是 evidence-verifier 读 215KB 全量 JSON > 16K context。
C 报告产出了 15 条通过勾稽安全门的待审 schema 补丁。

本轮两个目标：
1. 给 parser 加 `--compact-summary` 旁路输出（每样本：代号/表数/各勾稽项 PASS-FAIL+关键数字，
   体积 << 16K tokens），解锁双跳复核。
2. 把 C 的 15 条待审补丁回写到 `~/wzh/m1_samples/m1_table_schema.json`（项目外，不进 Git）。

## 约束

- 样本与 schema 在 `~/wzh/m1_samples/`，不进 Git；报告脱敏。
- 不下载模型；不改 src/biz/m1_service.py；不 push；不碰 TAT-DQA / test split。
- 用 Qoder CLI 执行：`$QODER -m "local-llama/qwen3-14b" -p "prompt" --dangerously-skip-permissions`
  或交互模式 `$QODER`。
- 如果 Qoder 认证失败或 :8004 不可用，BLOCKED 记录后停，不无限重试。

## Phase 1: parser 紧凑摘要

修改 `scripts/m1_statement_parser.py`，新增 `--compact-summary <path>` 参数：
- 对每样本输出紧凑 JSON：`{sample_id, n_tables, reconcile: {market_value: "PASS|FAIL|SKIP", currency: "...", date: "...", silent_mismatch: "..."}, n_unmapped, unmapped_cols: [...]}`
- 总体积目标 < 2KB（6 样本），远小于 16K tokens。
- 不改变现有 `--json` 全量输出行为。

验证：跑一次 `--compact-summary /tmp/m1_compact.json`，确认体积 < 2KB 且包含所有勾稽结论。

## Phase 2: C 待审补丁回写 schema

读 C 报告（`docs/experiments/2026-07-29_m1_header_mapping_llm.md`）第 4 节的待审补丁列表，
把 15 条有效建议回写到 `~/wzh/m1_samples/m1_table_schema.json`：
- 证券持仓明细新增字段：交易日期、代理费用、印花税、在途数量、基金净值、最新单价、
  成交数量、手续费、清算费用、累计净值、资产账号
- 资金资产汇总新增字段：币种、资产账户

回写后重跑 parser 验证：unmapped 应从 23 降到约 7-8（剩余为 C 报告标注的需进一步扩 schema 的列）。

## Phase 3: 双跳验证（用紧凑摘要）

如果 OpenCode 可用（`~/.opencode/bin/opencode`），尝试：
1. coordinator 委派 m1-extraction 跑 parser（产出全量 + 紧凑摘要）
2. coordinator 委派 evidence-verifier 读**紧凑摘要**（而非 215KB 全量）做独立复核
3. 检查双跳是否在 180s 内完成

如果 OpenCode 不可用或双跳仍超时，记录 BLOCKED 原因。

## Phase 4: 报告

`docs/experiments/$(date +%F)_m1_compact_and_patch.md`：
- 紧凑摘要体积 + 内容样例
- schema 回写前后 unmapped 对比
- 双跳验证结果（成功/BLOCKED + 原因）
- 对甲方 M1 主线的贡献

## Phase 5: 提交（不 push）

```bash
git add scripts/m1_statement_parser.py docs/experiments/*_m1_compact_and_patch.md
git commit -m "feat(m1): compact reconciliation summary + apply C schema patches

Unlocks two-hop evidence verification (< 2KB summary vs 215KB full JSON).
15 LLM-suggested schema patches applied to ~/wzh/m1_samples/m1_table_schema.json
(outside repo, not committed). Unmapped expected to drop from 23 to ~7-8."
```

## 停止条件

- Qoder 认证失败 → BLOCKED
- :8004 不可用 → BLOCKED
- 全完成 → 正常结束
- 不 push、不碰 TAT-DQA、不下载模型