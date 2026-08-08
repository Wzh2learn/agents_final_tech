---
name: m1-gap-triage
description: M1 解析失败分诊（0 表 / unmapped 过高）：嘉合 playbook 固化的"读原文诊断 → 补 synonyms → 重跑 → 报 delta"流程。parse-file 返回 0 表、新样本字段命中率低、或需要判断"改 schema 还是改 parser"时使用。
---

# M1 Gap Triage（嘉合 playbook）

> 状态: 已注册（2026-08-05 用户批准，Loop D 补两处修订后入 AGENTS.md Skill 武库，sync_skills.sh 分发至 Loop A）

## 触发条件

- `/api/m1/parse-file` 返回 `table_count = 0`，且文档理应是对账单
- 字段映射命中率 < 80%（unmapped 列占比 > 20%）

## 红线

- 不碰冻结节点：`tests/test_m1_service.py`、`scripts/graph/frozen_hashes.txt`、schema 冻结 hash
- **schema 优先，代码靠后**：不为单一样本改 parser 逻辑；先穷尽 synonyms 扩展
- M1 解析热路径永远不走 agent（见 memory/DECISIONS.md 2026-08-05 条目）
- schema 写操作走 `/api/m1/schema/*` API 需 X-Admin-Token；或直接编辑 `config/m1_table_schema.json`（**非冻结**运行时 schema，可 commit）后热加载。**冻结澄清：`docs/m1_schema/` 是冻结基线目录，永远不碰**（与 tests/test_m1_service.py、frozen_hashes.txt 同级红线）

## 分诊决策树

读原文后先归类，再动手：

1. **列名未覆盖**（表结构正常，列名不在 schema）→ 补 synonyms，本 skill 主路径（嘉合先例 31.2%→93.8%）
2. **布局超出规则 parser 能力**（垂直布局/空格对齐/无线表格）→ 记录为 parser 能力缺口，派 Loop A 任务（先例：NCAMC 坐标重建、华泰 markdown OCR prompt），不在本 skill 内硬修
3. **非对账单文档**（操作流程/通知/传真噪声）→ 记 known_gap 入 memory/THREADS.md 台账，不投入

## 步骤

1. **读原文诊断**：PDF 用 pymupdf/pdfplumber 提取原始文本与表头（前 500 字足够定性）；txt/html 直接读（注意编码）。**image-only PDF 无文本层时，先读 OCR/vision 输出再诊断**（`_try_vision_ocr` 产物；vision 端点 :8004 mmproj，参考 scripts/m1_ocr_fallback.py 路径），不要拿空文本硬猜。确定是列名问题还是布局问题。
2. **人工映射**：把 unmapped 列名与 `m1_table_schema.json` 标准字段对照；有甲方映射表（xlsx）时优先用它做 (代码,名称) 交叉参照。
3. **补 synonyms**：通过 schema API 或直接编辑 schema 文件，给目标表的 standard 字段追加近义词；一次改完一类表。
4. **重跑验证**：先重跑触发样本确认命中率 ≥80%，再重跑同格式全量样本确认一致性。
5. **报 delta**：命中率 before/after、unmapped 剩余列表、是否引入新 known_gap。写 dispatch_log 一行 + 台账更新。

## 输出模板

```
[样本/批次] gap 分诊: <0表|命中率X%> → <诊断归类> → <动作> → 命中率 Y%（delta +Z%）
剩余 unmapped: [...]（可接受 | 需 parser 能力 | known_gap）
```

## Schema 演进 SOP（补词后必跑, 2026-08-09 沉淀）

补 synonyms 后**必须**走完以下链路再报 delta，否则 delta 无效：
1. 确定性重跑：`--no-llm`（纯规则，可复现口径）
2. 回归门禁：`python scripts/m1_scenario1_regression.py`（quick ~1s；`--full-m1` 语境下全量含 OCR）——PASS 才允许报 delta
3. 自学习闭环（可选）：LLM 兜底开启时 unmapped 列自动沉淀到 `config/schema_suggestions.json`；`python scripts/m1_apply_schema_suggestions.py` 验证后批量落库（先临时 schema 复跑，回归不写回；冻结运行时 schema 默认拒写，需 Loop D 授权 + manifest 刷新）

## M1 CLI 确定性合同（scripts/m1_statement_parser.py, 2026-08-09 沉淀）

- 文件发现：默认只认 `sample_*` / `mapping_*` 前缀；跳过的文件 **stderr 显式警告**（无静默丢弃）；`--files` 显式列表绕过过滤（相对 --samples-dir 或绝对路径）
- schema 口径：默认 `resolve_schema_path()` — config/m1_table_schema.json 优先（与 :5050 生产一致），冻结运行时 schema 仅 fallback；`--schema` 显式覆盖
- 可复现性：`--no-llm` = 纯规则确定性复现；LLM 兜底开启时 :8004 抽值 + 沉淀同义词建议（副作用仅 suggestions 文件）
- OCR 预算：`M1_OCR_BUDGET_SECONDS`（默认 240s/文件）；引擎顺序 paddle → :8007 VLM（如在）→ :8004 vision；每引擎结果（ok/empty/error/skipped-budget）记入结果 `ocr_engine_log`，回退留痕
- 输出：`--json` 脱敏汇总（tables[hit_rate,unmapped]/header_meta/reconcile）；`--dump-unmapped` 只读诊断；`--compact-summary` 供 evidence-verifier 复核

## 历史案例参照

| 案例 | 诊断归类 | 动作 | 结果 |
|---|---|---|---|
| 嘉合 8 份 | 列名未覆盖 | schema synonyms 扩展 | 31.2% → 93.8% |
| NCAMC | 垂直布局 | Loop A: pymupdf 坐标重建 | 0→1 表 75%（b927efe） |
| 华泰/TraFax | OCR 纯文本无线表 | Loop A: OCR prompt 要 markdown 表格 | 0→1 / 0→3（9ea3754） |
| email body | HTML 结构 | 预处理 HTML 提取 + parse_html | 3 封 0→9 表 |
| xinhua | 非对账单 | 不入库（ingest 过滤） | known_gap CLOSED |