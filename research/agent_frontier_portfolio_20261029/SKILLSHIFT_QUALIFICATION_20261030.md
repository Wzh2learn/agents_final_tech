# SkillShift-Bench：GB10 来源资格与适配调查

2026-10-30；状态 **SOURCE_INSPECTED / OFFICIAL_ENVIRONMENT_NOT_RUN**。本记录用于第二篇选题和环境规划，不是 benchmark 成绩，也不是对已有方法的复现。

## 为什么有价值

[SkillShift-Bench](https://aclanthology.org/2026.emnlp-main.1952/) 直接研究网页环境变化下的技能执行：官网列出 GitLab、Magento、WordPress 三类系统的 355 个任务族，以及源/目标环境与感知、执行变化的六种条件。作者的 MPCR 已经在固定 skill 库上研究测试时选择与局部可执行性，不能把这些概念当作我们首创。其[自定义接口](https://skillshift-bench.github.io/docs/custom-agent/)允许接入 Agent，并同时观察动作、报错及技能调用；原论文对照和官方固定技能库等信息见[基线说明](https://skillshift-bench.github.io/docs/baselines/)。

潜在研究问题仍然是：**当过去经验的适用条件或反馈可靠性变化时，Agent 如何利用可见证据决定复用、修订或放弃，并保持跨任务迁移？** 要先精读 MPCR、Skill-V 等具体实现，确定该问题与它们的实际差异；不能将数据集本身或这句话当成已建立的新方法。

## 本机资格检查

- GB10 `uname -m` 和 Docker 架构均为 `aarch64`。官方[环境说明](https://skillshift-bench.github.io/docs/environments/)要求 `linux/amd64`，GitLab 和两个 Magento 上游镜像没有 arm64 版本；官方未验证仿真路径。因此直接在 GB10 上运行官方完整环境并获得可比成绩**不可直接假定可行**。这不证明一切组件都不能在 ARM 上运行；替代架构或其他环境需另行实测。
- 在 GB10 `/home/testuser/wzh/research_evidence/agent_learning_20261030/skillshift_bench_source` 克隆官方 harness，HEAD 为 `d5589a04563caddd041e9d6dbe4d72d27f005555`，未更改源码。仓库代码 MIT 许可，第三方环境及数据须分别遵守上游许可，详见该仓库 `LICENSE`。
- 执行官方 `python3 scripts/smoke_test.py`：**15 项 PASS、1 项 FAIL**；未启动浏览器、网站、模型或训练。两版本各 355 条、任务 ID 映射、六种条件、schema、30 族校准样本检查均通过。
- 失败项为参考锚点检查：脚本把任意指标值为 null 都视为未测，但该 no-skill anchor 的 SFR 因技能调用数为 0 而按文档应为 null。对原始 JSON 独立计数：18 个环境单元的两个 gated 指标 SR/AS 全部有值，18 个 SFR 均为 null，样本数合计 180。**这是与其文档不一致的 smoke 检查条件；不据此宣称官方校准或运行环境已验证。** 同一时间官网 quickstart 称 anchor 尚未发布，而该提交的 `docs/calibration.md` 和 JSON 标为 published，也应以实际版本和后续修复为准。
- 发布方不提供论文四个学习型基线在其环境中的完整集成和逐题轨迹；MPCR 与其固定技能库发布。其官方汇总结果是不同模型与环境下的作者报告，不能作为本地 Qwen 结果直接等条件比较。

## 下一步

1. 确认可用的 x86 主机和官网镜像、数据与授权，再做单个任务的环境/版本健康检查；不要因为本地 smoke 的这一失败修改上游参考结果。基于实际版本修正或绕开检查时，应记录补丁和与原版差异。
2. GB10 同时继续基于可运行的公开任务和既有容器执行学习/适配实验；预先分别记录任务族、变化版本、模型可见反馈、经验来源、独立 evaluator 和调用成本，再考察未见族迁移。
3. 对照至少普通历史/无历史、直接重试、固定 skill、现成的 MPCR 或其公平复现，以及可见信息相同的简单规则；最终比较质量与总成本，而不是只比较某条反馈后的单任务成功。
