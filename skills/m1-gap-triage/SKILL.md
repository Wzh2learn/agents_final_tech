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

## 历史案例参照

| 案例 | 诊断归类 | 动作 | 结果 |
|---|---|---|---|
| 嘉合 8 份 | 列名未覆盖 | schema synonyms 扩展 | 31.2% → 93.8% |
| NCAMC | 垂直布局 | Loop A: pymupdf 坐标重建 | 0→1 表 75%（b927efe） |
| 华泰/TraFax | OCR 纯文本无线表 | Loop A: OCR prompt 要 markdown 表格 | 0→1 / 0→3（9ea3754） |
| email body | HTML 结构 | 预处理 HTML 提取 + parse_html | 3 封 0→9 表 |
| xinhua | 非对账单 | 不入库（ingest 过滤） | known_gap CLOSED |