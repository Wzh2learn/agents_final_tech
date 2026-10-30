# SkillEvolBench：来源与 GB10 只读资格

2026-10-30，状态 `SOURCE_INSPECTED / TASKS_AND_OFFICIAL_RUN_NOT_EXECUTED`。[论文](https://arxiv.org/abs/2605.24117)是 2026-05 预印本；作者描述的 180 任务、三种 Agent harness 和原始轨迹比较是作者结果，不是本项目复现。

## 检查结果

- 官方 [GitHub 仓库](https://github.com/AIoT-MLSys-Lab/SkillEvolBench)在 GB10 以 `--depth 1 --filter=blob:none --no-checkout` 拉取到 `/home/testuser/wzh/research_evidence/agent_learning_20261030/skillevolbench_source`，HEAD `9e3daa339987c3cfa624121e1be442593a53d43c`，提交时间为 2026-06-06。未 checkout 全部文件、未安装依赖、未运行模型或测试。
- `git ls-tree` 看到 **180 个 task 目录**，与 README 所述数量一致；这个数量检查不证明内容完整、任务可信或运行成功。README 将每个 family 的 T1–T3 作为获取阶段、T4–T6 作为部署评估阶段；分别对应上下文变化、干扰和组合。数据、实际时间边界和基准结果须逐项核验，不默认所有任务是自然真实业务。
- 树中未找到名称为 `LICENSE`、`LICENCE`、`COPYING` 或 `NOTICE` 的文件，`pyproject.toml` 也未声明许可。本次只能标记**许可未知**；没有将源码、数据或任务复制到项目 Git、发布或用于训练。各依赖与第三方素材也可能有单独许可。
- README 指定 Harbor、专用 `agent-runtime:latest`、外部模型预设和容器构建；其运行镜像构建脚本涉及联网安装多种 harness，项目没有为 GB10 本地 OpenCode/Qwen 提供现成适配。尚未验证 ARM 支持、容器可用性、模型身份、隐藏测试隔离或作者给出的 180 次任务调度。不可把基准榜单成绩直接当本机 Qwen 对照。
- 已只读查看一个 `E3-LS1-T5` 的大小写列名陷阱及其运行合同，用作开发理解；该任务**已暴露，不得再标为盲选确认样本**。其描述可启发我们对大小写、字段和经验条件的对照，但这不是无代价证据：任务本身已提示忽略大小写，普通规则可能完全解决。

## 后续行动

先读取论文和参考实现中 T1–T6 的划分、原始轨迹 RAG 与 self-generated skill 的具体机制；对代码/数据许可、执行环境和外部访问权限做明确核查。可以将作者公开分层协议作为实验设计对照，并在许可、模型可接入和隔离验证之后选小样本运行。若基准不可直接复用，则使用独立许可明确的公开任务，并保留相同的学习来源—冻结迁移和强原始轨迹对照；不把它们称为 SkillEvolBench 官方成绩。
