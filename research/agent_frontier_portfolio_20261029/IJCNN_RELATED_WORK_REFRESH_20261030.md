# 第二篇原文、强基线与方法差异

> 2026-11-27｜[v5 阶段正文](IJCNN_MANUSCRIPT.md) · [研究议题与证据](STAGE2_AGENT_RESEARCH_PLAN_20261102.md#competitive-research-agenda)

## 全文复核与强基线

GB10 原文库 `~/wzh/research_evidence/agent_learning_20261030/ijcnn_related_work/reading_notes/INDEX.md` 收录 66 份原始 PDF、可搜索全文和 Zotero RIS 书目。包括现稿全部 12 项论文引用及重要历史和近期近邻。本机有完整副本。Git 保留原始出处和审阅依据。

| 参照 | 原文协议与观察 | 同场景竞争的用途 |
| --- | --- | --- |
| [CAR，2026-11](https://arxiv.org/html/2611.05166) | §3–4、表 2、附录 F。先评估收益减损害，再定位证据和限制编辑。FinQA 1,147 题，Qwen3-8B 63.21→66.43 NAA，采用答值归一化与 $10^{-4}$ 容差，无需提交程序。14.6% 恢复／2.1% 错改是跨设置的需求级结果。 | 同模型、同初答和证据的直接修订对手。净收益公式已有同型先例。区分若按原协议复现与在统一执行合同下适配。 |
| [BudgetVerify，2026-09](https://arxiv.org/html/2609.33052) | §3–4、图 4。FinQA 1,147 题。同一模型判别保留、局部复查或独立重解，图 4 展示准确率与生成＋验证 tokens。 | 有限预算对手。共享多状态监督应比较相同形成成本，在线与匹配的低/高费用策略对照。 |
| [DCRC / DSA-7B，KDD 2026](https://doi.org/10.1145/3770855.3818407) | [原文](https://arxiv.org/html/2605.31064v1)表 1–2。FinQA 完整公开测试 84.66%，同文 7B CoT SFT+RL 为 77.50%。证据验收＋难负例＋确定性执行，采用 1% 容差。 | 证据绑定和候选生成的强参照。待取得作者正式权重或预测才能直接复评分，机制可适配。 |
| [MoCA-Fin 作者代码](https://github.com/UBC-NLP/MoCA-Agent/tree/f8004486749f7061e4f426320f71283e66a649a2) | 作者仓库报告 Qwen3.6-27B 在 FinQA 官方 1,147 题上为 78.29%。市场式证据选择后生成受执行限制的 Python 程序，默认[评分实现](https://github.com/UBC-NLP/MoCA-Agent/blob/f8004486749f7061e4f426320f71283e66a649a2/mocafin/executor.py#L108-L147)接受 1% 相对容差以及 100 倍和 1/100 倍换算。 | 证据筛选与代码生成的可运行近邻。若进入统一对照，复用同题和同模型，分别计量模型调用及原生评分下的准确率。78.29% 保留为作者协议下的参考。 |
| [MATATA-8B](https://arxiv.org/pdf/2411.18915v5) | 表 3–4，FinQA 57.11→75.68→77.59，依次为提示、执行筛选 SFT、KTO。TAT-QA 公开 gold 77.81 EM，隐藏榜 77.6 EM。 | 先提高基础解题，再检查执行反馈的增量。公开与隐藏分开。 |
| [ODA-Fin-RL-8B](https://huggingface.co/OpenDataArena/ODA-Fin-RL-8B) | [原文](https://arxiv.org/html/2603.07223)表 1 报告 FinQA 73.3 与 TAT-QA 89.3，采用作者 Acc。Qwen3-8B 领域 SFT＋RL，开放权重。 | 首选可落地的同量级强基座。用同程序协议和官方分数测效果，同时保留开放答值协议下的分数作参照。 |
| [训练执行筛选](https://arxiv.org/html/2607.14709v1) | TAT-QA 带推导的 831 道测试题，7B 学生为 87.00 EM。训练中用金推导引导并执行筛选，学生重采教师失败样本。 | 借鉴训练池做法。绝对排名按实际过滤子集和官方全量分别列。 |

## 模型、代码与可复现状态

`OpenDataArena/ODA-Fin-RL-8B` BF16 固定在 `948c22ea48f9bf93e5747f4211657fcad9cb0295`。GB10 已完成[零训练探针](../finance_frontier_pilot/README.md#零训练诊断)和本地短程序的[强基线续做验收](../finance_frontier_pilot/README.md#续做强基线比较)。MATATA、DCRC 等原论文成绩按上表口径保留，待取得可执行产物后才能在本协议下比较。[固定发布版](https://huggingface.co/OpenDataArena/ODA-Fin-RL-8B/tree/948c22ea48f9bf93e5747f4211657fcad9cb0295)

[FINDER](https://aclanthology.org/2025.emnlp-main.1577/)在 FinQA 公开测试报告 75.32%，独立消融证据检索和示例选择。公开执行参照有 [FinMAN](https://github.com/coenliu/MultiAgentFin) 与 [LEVER](https://proceedings.mlr.press/v202/ni23b.html)。前者报告 BizBench 的 CodeFinQA/CodeTAT-QA，后者提供同候选执行重排。成绩对比用 [FinQA 官方评估器](https://github.com/czyssrs/FinQA/blob/main/code/evaluate/evaluate.py)、[TAT-QA 官方评估器](https://github.com/NExTplusplus/TAT-QA/blob/master/tatqa_eval.py) 和本项目原生回执。

## 已有方法与正文差异

- **本地纠正。** [CCT §6/F.2](https://aclanthology.org/2025.acl-long.203.pdf)已有按错答修复和正确保持的混配。[CARE](https://arxiv.org/html/2512.19554)已有外部验证的困难负例。我们的匹配控制固定监督总权重，比较同一条已执行修复前和修复后怎么用反例。33/29/34/37 的四臂已完成。新单步组和强基座上的增量仍是关键。
- **共享教师。** [CIR §3–5](https://arxiv.org/html/2610.00372)已有同状态分叉、恢复和损害。我们复用原始快照的一条教师轨迹去监督多个实际本地程序。缓存里 45 个随视图变化的来源中，41 个每个视图都采纳相同教师，所以额外标签主要同时反映本地正确性。需以相同教师成本和单状态监督匹配检验。[GenGate](https://aclanthology.org/2026.emnlp-main.2071/)与[RASER](https://aclanthology.org/2026.findings-aacl.219/)补上可选生成和后验动作的近邻。
- **契约与证据。** [TAGOP §3.3](https://aclanthology.org/2021.acl-long.254.pdf)独立预测 scale，[确定性规则研究](https://aclanthology.org/2026.finnlp-1.16/)报告跨数据集效果反向，[FINCARDS](https://aclanthology.org/2026.findings-acl.1244/)已经组织结构化财务证据。新生成方式要检验证据直接参与执行和保持监督所带来的结果变化。

<a id="可执行候选反馈与经验的适用性而非又一个技能库"></a>
[旧近邻完整记录](https://github.com/Wzh2learn/agents_final_tech/blob/7c7b30450ee8a694dc582032a4c66270a51634c2/research/agent_frontier_portfolio_20261029/IJCNN_RELATED_WORK_REFRESH_20261030.md)保留 SCoRe、STeP、HASP、PEAM、SkillApt、SkillRevise 及其他跨场景历史。其全文在 GB10 索引的对应分组。
