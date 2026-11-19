# 强基座零训练诊断

第一批对同一题分别运行自由推理和可执行 DSL。使用 `ODA-Fin-RL-8B` BF16 固定版本 `948c22ea48f9bf93e5747f4211657fcad9cb0295`，两臂均经 OpenCode 1.18.3。固定题干、报告输入与生成设置。27B FP8 在同一 DSL 合同下对首答错题独立作答。旧 Risk/Value 权重只读出分，首答同时作为两个状态，供分布迁移下比较。

- FinQA 官方 test 抽 200 题，114 道单步、86 道多步。与官方 TRAIN 表内容重复的 15 题排除。TAT-QA 官方 dev 抽 200 道算术题，来自 147 个表上下文，排除旧 C3 确认的 64 个表上下文。抽样以固定哈希排序，确认表只核对事先记录的成员标识。
- `M_strict` 两臂同用官方答案计分，DSL 可执行率另报。`M_norm` 是限定倍数下用参考答案复算的诊断。`M_rule` 在 TAT-QA DSL 臂使用已有公开尺度规则，其余沿用原答案。统计逐题救回与错改。自由臂剩余错误包含未能提取最终答案的情况。
- 来源复核从可执行程序回映公开坐标。同值歧义未唯一消除时不传入白名单。报告错误检测 AUC、27B 能恢复的错题 AUC，以及两者的覆盖数和共同样本对照。
- GB10 私有目录为 `~/wzh/research_evidence/finance_frontier_pilot_20261119_v1`。`panel/manifest.json` 固定题号，`calls/` 保留原始 OpenCode 回执，`generation_scores.json` 保存配对生成分数，`summary.json` 保存全批分数、AUC 和推理成本。模型按既有显存租约串行切换。费用按本地与校内分别核算。

路线 A 的开发门槛为规则后差距 ≥6 pp 或格式差 ≥8 pp。若差距较小且排序 AUC ≥0.72，进入路线 B 的交接对照。路线 C 还要求严格成绩高、教师恢复有限且排序 AUC <0.62。开放测试的 200 题用于选方向，后续全量比较记录经过探索的题号。

`diagnose.py --root <运行目录> --receipts-only` 可直接核对回执。全批结束后省略该参数，按报告或表上下文计算同题分差区间。它也用同一批操作数回映复算纯规则 AUC，量化 8B 反查的增量，无需新增调用。

ODA 论文的 FinQA 和 TAT-QA 报分使用 CompassVerifier，当前实验对照以自己的统一官方评分为准。[ODA 原文](https://arxiv.org/html/2603.07223v1#S4) · [固定版本](https://huggingface.co/OpenDataArena/ODA-Fin-RL-8B/tree/948c22ea48f9bf93e5747f4211657fcad9cb0295)
