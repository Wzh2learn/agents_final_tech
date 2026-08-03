# Loop C 审计报告 — 2026-08-02 22:40 (deepseek-v4-flash-0731)

## 审计范围
- 审计 commit 范围: `de7336b` (schema synonyms) .. `97b8b9e` (OCR prompt)
- Loop B 状态: **PASS** (`logs/graph/verify-report.json`, head `97b8b9e`,
  frozen_nodes PASS / pytest exit 0 / api_anchors PASS)

## 代码变更审查
- 变更摘要:
  - `de7336b` — 新增 `config/m1_table_schema.json` (+711, 新文件), 为嘉合基
    金格式补 38 个近义词; `m1_accuracy_eval.py`/`m1_rag_ingest.py` 改用
    `resolve_schema_path()` (各 +1/−1)。
  - `97b8b9e` — 仅改 `_OCR_VISION_PROMPT` 常量 (加 markdown 表格格式示例),
    未触碰解析器/分词逻辑。
  - 全程 **未触碰** `tests/`、`m1_samples/`(冻结节点)。
- 是否服务于甲方需求: **YES** (表头同义词映射 + 结构化提取, 正是甲方 M1
  对账单解析诉求)。
- 架构漂移风险: **LOW** (两次变更均小、聚焦, 无无关重构)。
- 不当修改: **无**。冻结路径哈希与 `frozen_hashes.txt` 一致。

## 甲方样本端到端验证 (真实 API :5050, `POST /api/m1/parse-file`)

| 样本 | 解析状态 | 表数 | 列数 | unmapped | hit_rate | 备注 |
|------|----------|------|------|----------|----------|------|
| 嘉合基金 att0 (PDF) | success | 2 | 16 | 0 | **93.8%** | 8 列表1 + 8 列表2, 均全映射 |
| 嘉合基金 att1 (PDF, 镜像账户) | success | 2 | 16 | 0 | **93.8%** | 复现一致 |
| 博时传统 (PDF) | success | 1 | 5 | 0 | 60.0% | |
| LU 20260506 (PDF) | success | 3 | 23 | 0 | 60.9% | |
| 嘉兴民安 (PDF) | success | 6 | 62 | 0 | 93.5% | |
| 新华 (DOCX, 纯图片需 OCR) | success | 5 | 11 | 0 | 0.0% | LLM-fallback 已映射 11 列; 0.0 为 hit 计数不统计 LLM 分配,t是已知基线 |
| 华泰紫金丰泰智盈 (PDF) | success | 1 | 14 | 0 | 35.7% | commit 声称 0→tables, 已确认检出表 |
| TraFax / WaveFax (msg) | 不适用 | — | — | — | — | `.msg` 非注册解析类型 (预存行为, 非回归) |

所有真实样本 unmapped=0; 无字段回归。

## 独立计算 — 嘉合 hit rate (qwen code_interpreter + 实盘校验)

任务要求: "8 columns mapped out of 8+1 total = 多少?" 浅层解释 `8/9=88.9%`
与 commit 的 93.8% 对不齐。**深入核实后确认 commit 的数字完全可复现**——
真实指标是跨两张表的 `total_hits/total_cols`, 且表1中 `基金份额`+`可用份额`
共同映射到同一标准字段 `持仓数量`, 故 8 个来源列命中 7 个标准字段:

- **Before** (冻结 sample schema, de7336b 前默认): `p0_table_1 2/8`,
  `p0_table_2 3/8` → **5/16 = 31.2%** ✅ 与 commit 的 "31.2%" 一致
- **After** (config schema, 实盘 API): `p0_table_1 7/8`, `p0_table_2 8/8`
  → **15/16 = 93.8%** ✅ 与 commit 的 "93.8%" 一致
- 分母 16 的两张表均来自嘉合 PDF 的本期余额表 + 交易明细表。

结论: `31.2% → 93.8%` 是真实、可复现的提升。任一嘉合账户实盘解析均返回
`{"metrics": {"hit_rate": 93.8, "unmapped": 0, "columns": 16}}`。

## pytest 全量
- 冻结文件 `tests/test_m1_service.py`: **18 passed** (哈希与 frozen manifest 一致)。
- M1 相关套件 (parser/schema_api/ocr_fallback/reconcile/edge/core): **74 passed, 2 skipped**。
- 全库: **223 passed, 15 skipped / 238 collected**, exit 0。

## 判定
- **ACCEPTED** (两 commit 均正确、聚焦、通过冻结门禁)。
- 无驳回原因。
- 建议改进方向:
  1. `hit_rate` 计数对"多列同标准字段"(如 基金份额+可用份额→持仓数量)
     会低估列级覆盖率 (8/8→7/8)。建议在指标里同时暴露 `cols`/`distinct_mapped`
     两个口径, 避免对外误读。
  2. LLM-fallback 分配的标准字段不计入 `hits`, 导致新华等纯图片 DOCX 显示
     hit_rate 0.0 而实际已全映射 → 建议 metrics 增加 `llm_mapped` 计数。
  3. `.msg` 需先解附件 (scenario1 已有解包流程), 建议 UI/API 层明确报错而非
     HTTP 空响应。

## 给 Loop D 的建议 (如有)
- 无冻结/解冻诉求。schema 演进方向 (presentation synonym 冷启动 + unmapped
  回写闭环) 与甲方需求一致, 可继续。