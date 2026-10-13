# WP-0 Entry Package v1

> date: 2026-10-13 | author: Loop D | status: `ENTRY_READY_FOR_LOOP_A / QUALIFICATION_PENDING / NO_EXPERIMENT_AUTHORISED`
> 供下一位 Loop A 执行者直接开工。三块内容：source landscape、candidate ranking、literature gap map。
> 详版：[WP0_QUALIFICATION_REPORT_v1.md](WP0_QUALIFICATION_REPORT_v1.md)（资格）、[WP0_CANDIDATE_ANALYSIS_v1.md](WP0_CANDIDATE_ANALYSIS_v1.md)（排序/许可/最小设计）。
> 权威范围：[task card](thesis_experience_v1_task_card.md)、[blueprint](THESIS_EXECUTION_BLUEPRINT_v1.md)、[entry](MASTER_RESEARCH_EXECUTION_ENTRY_v1.md)。

## 1. Source landscape

**已登记候选（元数据层，全部 `download_approved=false`）**：TAT-QA、FinQA、ConvFinQA、MultiHiertt、HiTab、GitTables、Sherlock/VizNet、HybridQA、OTT-QA、Valentine/NYC。记录位置 `docs/datasets/paper-public-source-registry-v1.json`（10 行，含 official repo、checked head、repo SPDX、independence namespace、role fit）。

**许可分布**：MIT×6（TAT-QA、FinQA、ConvFinQA、MultiHiertt、HybridQA、OTT-QA、Sherlock 中的多数）、Apache-2.0×1（Valentine）、CC0-1.0×1（GitTables）、NOASSERTION×1（HiTab）。其中**数据体许可**只有 TAT-QA 有（README-reported CC BY 4.0，需 fetch 时复核），FinQA 在记录 head 上**零陈述**。

**未登记的候选（需 owner 授权）**：US SEC EDGAR 10-K/10-Q —— 美国政府公有领域、天然多期表 + 明确单位、可按公司分 origin；属于**新数据采集**，未获授权。

**必须排除**：ConvFinQA（FinQA 血缘，非独立测试源）、GitTables/Sherlock（无 pairwise gold）、HybridQA/OTT-QA（领域不符）、Valentine/NYC（任务不符）。**旧 95 表/118 注入、FinQA、PR-03 材料不得重新切分充当新面板。**

## 2. Candidate task ranking（针对"两期增减额 + 单位统一"）

判据：两期对齐 / 单位列 / 可独立复核 gold / ≥8 origin / 许可清晰 / 与本项目既有使用的独立性。

| 排名 | 来源 | 结论 |
|---|---|---|
| 1 | **TAT-QA** | 最佳契合（财报多期表）；**前置**：一次 exposure audit（它做过 Stage E 载体）+ CC BY 4.0 复核 |
| 2 | **MultiHiertt** | 强备选（层级表 + 财报）；前置：external package 许可范围审查；本项目未使用过 |
| 3 | FinQA | 仅第三选择：数据许可未决 + 已用于第二数据流（exposure） |
| 4 | HiTab | 许可风险（NOASSERTION / C-UDA-1.0），仅作压力材料 |
| 5+ | 其余 | 任务族或独立性不符（见详版 §1） |
| （新） | SEC EDGAR | 唯一需**新采集授权**的候选；若选它，WP-0 的全部前置需重走 |

## 3. Literature gap map（仅用已记录材料，不另搜热点）

| 邻居 | 已覆盖 | 留给 TH3-RQ2 的空位 |
|---|---|---|
| ACE | 生成+反思+整理构建经验手册，用自然执行反馈 | **事实支持**（非自评分）的反馈通道是否改变未来任务效用 |
| MemRL | 环境反馈驱动的记忆效用与检索 | 同上，换任务族 + 配对对照 |
| TRUSTMEM | 记忆转换的覆盖/保留/忠实性 | 不测下游任务效用 |
| PMD | 跨任务程序经验蒸馏进参数 | 参数内化，不是最小上下文复用问题 |

**唯一保留假设**（task card）：是否存在"事实支持的过去反馈 ↔ 未来任务效用"之间、最近邻尚未解释的分离（超出静态规则、朴素 few-shot、适配已有方法）。当前 `METHOD_NOVELTY = NOT_IDENTIFIED`。

## 4. Loop A 开工清单（不需要新授权即可做）

1. 依 task card §6 与 blueprint §2 撰写 **TAT-QA licence_record 草案**（仅官方页面元数据，不取数）。
2. 撰写 **origin-grouping 规则草案**（如何从"报告/公司"形成 origin，近重复如何隔离），对源 schema 文档。
3. 撰写 **task-adapter contract 草案**（字段/时期/单位抽取、gold 重算、工具消费校验），规格级，不实现。
4. 更新 `docs/datasets/` 的许可记录模板（若是 owner 选定族）。

## 5. 仍需 owner（不得由 Loop A 代决）

来源族选择（含 SEC EDGAR 是否授权新采集）／反馈权限定义／actor revision 冻结／任何下载、运行、预算窗口。

**本包不授权下载、不授权运行、不授权实现。它让下一次进入实验阶段不必从零开始。**