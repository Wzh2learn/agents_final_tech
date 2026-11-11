# 第二篇：近邻、重合与实验判别

> 2026-11-11。D定向读原文，未复现原法。活表只留近期参照；上版完整表固定在`faa3a12b`的本文件Git blob，更早大表在`747eac14`，按需恢复。

## 当前裁决

**主线已改为反馈条件化的可复用纠正技能学习（FCCL工作名）。**学习具体纠正片段在不同公开反馈/接口条件下的效用；预算选证、EVSI及依赖撤回降为工具或历史参考。尚无成立新方法。下列为11-11重读一手方法页的机制判断，不是原法成绩复现。完整旧表见`89ca0dbd`本文件Git blob。

## 最直接的方法近邻

| 工作 | 已核机制 | 当前必须解决的区别 |
|---|---|---|
| [Agent-R](https://arxiv.org/html/2501.11425v1) | §3：MCTS构造共享前缀的纠正轨迹，过渡点及迭代SFT。 | 从失败续做/成功纠正学习已有；需检验跨执行条件的片段选择收益。 |
| [STeP](https://arxiv.org/html/2505.20023v1) | §3.3–3.4：教师合成反思轨迹，错误动作部分mask。 | 不能把教师反馈或仅训练正确片段当创新。 |
| [SkillRevise](https://arxiv.org/html/2606.01139v4) | §3及算法1：诊断、原则绑定、具体可执行锚点、保留约束、重执行、效用门。 | 已超出改写文本；须与匹配适配版同信息/候选/总成本比较。 |
| [AdaMEM](https://arxiv.org/html/2606.05684v1) | §3.1–3.2：动态策略记忆，成功/动作改变筛选；反事实动作不实际执行。 | 条件策略须由实际片段及续行后果支持，动作变化本身不是收益。 |
| [SkillApt](https://arxiv.org/html/2609.26863v3) | 条件化配对效用、Load/Abstain。 | 条件效用本身不新。作者公开包为guoshaung/SkillApt，`73db0b54`；旧404不能外推无代码。 |
| [CIPO](https://arxiv.org/html/2610.04991v1) | 可执行原子/技能、同前缀分支、结果差偏好信号。 | 可执行粒度、配对偏好损失不是差异；须识别反馈×环境条件的迁移增量。 |
| [StateGraph](https://arxiv.org/html/2611.02912) / [Skill-V](https://arxiv.org/html/2610.11781v1) | 依赖失效/局部撤回，以及可验证技能合同、反馈更新和回放非回归。 | 保留约束和验证门已有；不能只组合这两种机制。 |
| [Getafix](https://arxiv.org/abs/1902.06111) / [CEGIS agents](https://arxiv.org/abs/2606.11521) / [CESS](https://arxiv.org/abs/2607.15854) | 历史修复模式与上下文选择；验证器反例驱动纠正；锚点、回归约束与反例增补。 | 当前代码守卫归纳属复用部件；须证明来源反馈改变新任务的Agent工具动作选择及任务后果，不能用程序分支条件替代Agent策略学习。 |

## 反馈与测试 oracle 的近邻

| 工作 | 已核范围 / 实验约束 |
|---|---|
| [Teaching Agents to Code Reliably](https://arxiv.org/html/2610.03984) | §2.1–2.3：补丁/回退差分执行、覆盖与变体区分。复现优先须是强基线；提示基线不称完整TACR。 |
| [Bayesian Control for Coding Agents](https://aclanthology.org/2026.emnlp-main.1548/) | §3–5/A.6及官方`2a3de1dc`的kernel/controller/校准模块：修好/修坏转移及在线Beta均值已有实现。普通条件化转移也是强基线，不将修复概率改名为创新。 |
| [Rethinking Self-Repair](https://arxiv.org/html/2611.06863v1) | §3–5/A/B：机器人reset-and-retry，固定指导和不同标签反馈与动态模板点估计相近，未检出其优势。补固定开发指导＋同预算重试；未测保留失败现场的恢复。 |
| [VeriHarness](https://arxiv.org/abs/2607.14167) | 仅核摘要：原始反馈与位置/观测值/替代项，含prose/JSON对照。须排除额外信息与呈现收益。 |

## 其他近邻索引

上述旧blob保留VBL、BiPACE、Grounding/SkillGLoW、Budgeted Verification、CodeT、ErrorProbe、CBC及更早近邻；其余见[历史索引](../../docs/archive/2026-11-06_agent_research_context/README.md)。不在活表不代表失效。

## 对本项目实验的直接约束

1. 反馈可靠性、送达、采纳与能力分开；通用流程不是新机制。
2. 统一任务、信息、工具与总预算，保留普通历史、状态规则、全重验及最近邻。
3. 条件片段学习须面对普通反馈纠正、静态技能、简单接口/约束规则及匹配近邻；形成数据与模型预算一致，不用更多样本解释为独立机制。
4. 独立原生评分，形成/整理/取证/执行全成本；自写测试、AI检查、模式合法均不作任务成功。
5. 当前状态和授权见[短计划](STAGE2_AGENT_RESEARCH_PLAN_20261102.md)及[入口](../../docs/research/LOOP_D_RESEARCH_PROMPT.md)。

<a id="可执行候选反馈与经验的适用性而非又一个技能库"></a>
[历史候选诊断](../../docs/archive/2026-11-06_agent_research_context/rethinkskill_interface_diagnostics_20261105.md)
