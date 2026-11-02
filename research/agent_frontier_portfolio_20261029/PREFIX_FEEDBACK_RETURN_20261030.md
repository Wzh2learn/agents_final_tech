# Prefix-cache Agent repair: second development case

2026-10-30；独立于 dialogue-parser 的**任务**，仍属于同一 SkillsBench v1.1 checkout，不是独立 benchmark。使用真实隔离 OpenCode/Qwen Agent、固定原始代码/输出、无外网、事后独立挂载原 verifier。见[事前实验卡](archive/plans/PREFIX_FEEDBACK_PILOT_PLAN_20261030.md)、[逐次账本](prefix_feedback_summary_20261030.json)和[运行器](run_prefix_feedback_probe.py)。

源 checkout `b63b7b2850226b6aa4fb5929a8c1ac7bc4d9a6af`；`task.md` SHA-256 `76bc3280055cd05df0c9855391d795595acc454cfd7da43a448fbbdba6026c72`；上游 `oracle_helpers.py` SHA-256 `bc3579ef49fed337c6f707532f3572cb9dd5a82e42dea8184d2e2c278b6b896c`；原 `prefix-cache-replay` skill SHA-256 `28ced940ec272cc01cf06519912077492d948b10e08a933acba12dd9907220cf`。固定版本不排除模型预训练曝光。

| 条件 | 原 10 项测试 | 2,000 行 hit 数与原参考实现不一致 | 物理 POST | 解释 |
|---|---:|---:|---:|---|
| 原始失败输出 | 1/10 | 156 | 历史运行，另计 | prompt token 单位、resident count 和缓存策略均有问题。 |
| 无模型定点修复可见单位与 count | 2/10 | 156 | 0 | 输出字段部分变对，缓存策略未修；不能把简单补丁包装成完整修复。 |
| neutral：仅知道失败 | 2/10 | 152 | 8 | 重新生成报告，prompt token 单位正确，缓存结果仍有错误。 |
| diagnostic：可见合同提示，8,192 输出上限 | 1/10 | 156 | 3 | 最后一步输出达到上限，保存的原代码与报告没有改变；不是已完成的修复。 |
| diagnostic：同提示，事后加大到 16,384 | 5/10 | 92 | 5 | 报告有部分改善，但缓存行为、resident count 等仍不符合原参考。 |
| task skill：公开原始任务技能 + neutral | 10/10 | 0 | 8 | 对 2,000 条相应字段与同一原参考一致；技能含完整 policy 描述，信息量多于其他条件。 |

对应 2,000 行检查由 [check_prefix_full_trace.py](check_prefix_full_trace.py) 在每次生成完成后调用上游同一个 `oracle_helpers.py`，是对原测试只抽查 5 行的**覆盖扩展**，不是一个独立参考实现。输出还检查 `0 <= hit_tokens <= prompt_tokens`：neutral 和 task-skill 为 0 个越界，可见合同定点补丁为 7 个，原诊断输出为 1,999 个；其数量反映各自具体输出，不可外推到任务分布。

四次新 Agent 共 **24 POST / 277,195 reported step tokens（含缓存输入）**，wall time 分别为 171.602、147.157、120.613、69.443 秒；0 训练、0 付费 API。账本顺序按目录，含 raw 和 receipt hash；原始轨迹与输出留在 GB10 `/home/testuser/wzh/research_evidence/agent_learning_20261030/prefix_feedback/`。确定性补丁和 oracle 重算无需模型调用。诊断的 16k 运行是看见 8k 截断后追加的探索，不能与先前运行组成固定预注册推断；额外上限也不能单独证明 8k 是原失败的唯一原因。

**进一步尸检**：16k diagnostic 用可观察 shell heredoc 生成新 `report.json`，但未改原 `solve.py`；这符合本任务只要求报告的表面输出合同，但仅凭持久化程序文件无法重放它的报告，raw 中保留实际命令。task-skill 的 `solve.py`、config 和 trace 已复制到全新的无网络容器重跑，输出 JSON 与保存报告内容完全一致；但两份公开 skill 提供了前缀扫描、部分块计数及 S3FIFO 队列规则，故不应称作“只靠反馈修好”或与短提示当信息等量比较。模型可能在训练中见过该公开任务。

**研究含义**：两个开发任务共同说明反馈类型、可用知识、工具/输出合同和回归检查会共同影响后续行为；但 prefix 的 strongest baseline 是现成的公开任务 skill，simple feedback 没追平它。下一步不是继续给同一反馈措辞调参：应在新任务族或同族自然版本变化上，冻结可用 skill、外部反馈质量与输出成本，比较 no-skill、完整 skill、长度匹配的普通上下文、失败诊断、skill+诊断和候选选择/更新策略，报告历史正确行为的保留及计算成本。先对近邻 SkillLearnBench 做 source/机制逐项比对，避免把通用“从反馈生成 skill”当新发现。
