# Paper E 升级 — Loop D 决策与执行索引 v1

> 日期: 2026-10-15 | 作者: Loop D
> 性质: 决策索引（薄）。详细设计见下方 canonical 集合；本文件不重复内容、不改冻结稿、不改任何数字。

## 决策
- 采纳导师 2026-10-15 裁决：Paper E 从「我们的评价器有局限」升级为「共享观测的评测面会不会一起漏判 / 一起误判任务相关变化」，先做 Layer 1 可行性（独立任务级 gold），再定 Layer 2/3。
- 领域口径收紧为 *staged tabular document-intelligence evaluation*（受限；不外推 document AI）。
- 执行通道：GB10 `scripts/graph/loop_ac_launcher.sh`（Loop A 执行 + Loop C 独立审计）；app sub-agent 不用于关键路径。
- 冻结稿 T1「Visibility Is Not Detection」继续 `SUBMISSION_DRAFT_COMPLETE = YES`，作为 fallback；升级结论落地前不动主稿。

## 用户两问的直接回答
1. 导师引的三篇工作：oracle（Offutt）偏经典、ACES 为 2022、只有 *Auditing the Audit* 是 2026 —— 不够新。近年替代池见 canonical 的 recent-related-work 文件。
2. 「多阶段文档智能管线」领域：撑得住，但只能是「受控构造的 staged tabular document-intelligence **evaluation**」；数据（公开 TAT-QA 表 + FinQA）够支撑 case study / RENE negative result，不够支撑任何 document-AI 通用或 population 结论。详见 canonical 的 domain-fit 文件。

## Canonical 入口（升级集，唯一有效）
| 文件 | 作用 |
|---|---|
| paper/PAPER_E_RECENT_RELATED_WORK_2026_v1.md | 2025–2026 相关工作池（arXiv 已核） |
| paper/PAPER_E_DOMAIN_AND_DATA_FIT_v1.md | 领域 / 数据支撑裁定 |
| paper/PAPER_E_LAYER1_INDEPENDENT_GOLD_DESIGN_v1.md | Layer-1 独立 gold 设计（权威） |
| paper/PAPER_E_LAYER1_LOOP_A_PROMPT_v1.md | Loop A 执行 prompt |
| paper/PAPER_E_LAYER1_LOOP_C_AUDIT_PROMPT_v1.md | Loop C 审计 prompt |
| docs/research/PAPER_E_LAYER1_LOOP_C_AUDIT_v1.md | Layer-1 fresh-context 审计结论 |
| research/paper_e_layer1_20261015/ | Layer-1 运行输出（已生成） |

## 已核事实（2026-10-15）
- GB10 数据在 `data/research/drift_v0/`：`input/tatqa_tables.json` sha256 `3e7e0568…`、`output/injection_map.json` sha256 `d7612405…`，与 Loop A prompt 期望值逐字一致；`logs/graph/eval/t2_visibility_sensitivity.json` 存在。
- 本地 = GB10 = origin/main。

## 下一步
1. ~~Loop A 执行 Layer-1 独立 gold~~：已完成，`GOLD_NOT_ESTABLISHED`。
2. ~~Loop C 独立审计~~：GB10 launcher 长时间无进展后停止；由 Loop D fresh-context 按 Loop C 清单复核，结论为 `CONDITIONAL / GOLD_NOT_ESTABLISHED`。
3. **不进入 Layer 2**。当前 v1 independent gold 的 U 率为 59.3%，超过 30% 预设门槛；35 个 U 案例需人工裁决，或需要新的、绑定实际任务答案与下游执行的新契约。
