# 第二篇：近邻、重合与实验判别

> 更新至2026-11-12。D定向读原文，未复现原法。上轮活表固定在`d3fd4a13`本文件Git blob，早期完整表见`faa3a12b`/`747eac14`；按需读，不全部预载。

## 当前裁决

**主线已改为反馈条件化的可复用纠正技能学习（FCCL工作名）。**学习具体纠正片段在不同公开反馈/接口条件下的效用；预算选证、EVSI及依赖撤回降为工具或历史参考。尚无成立新方法。下列为11-11重读一手方法页的机制判断，不是原法成绩复现。完整旧表见`89ca0dbd`本文件Git blob。

## 最直接的方法近邻

| 工作 | 已核机制 | 当前必须解决的区别 |
|---|---|---|
| [Agent-R](https://arxiv.org/html/2501.11425v1) | §3：MCTS构造共享前缀的纠正轨迹，过渡点及迭代SFT。 | 从失败续做/成功纠正学习已有；需检验跨执行条件的片段选择收益。 |
| [STeP](https://arxiv.org/html/2505.20023v1) | §3.3–3.4：教师合成反思轨迹，错误动作部分mask。 | 不能把教师反馈或仅训练正确片段当创新。 |
| [SkillRevise](https://arxiv.org/html/2606.01139v4) | §3.1–3.4：诊断/原则绑定、执行锚点、保留约束、重执行、效用门；搜索继续自最新候选，返回最佳候选。 | 已覆盖有锚点的纠正；不能用中间零收益推断它无法越过。需同信息/候选/总成本适配比较。 |
| [AdaMEM](https://arxiv.org/html/2606.05684v1) | §3.1–3.2：动态策略记忆，成功/动作改变筛选；反事实动作不实际执行。 | 条件策略须由实际片段及续行后果支持，动作变化本身不是收益。 |
| [SkillApt](https://arxiv.org/html/2609.26863v3) | 条件化配对效用、Load/Abstain。 | 条件效用本身不新。作者公开包为guoshaung/SkillApt，`73db0b54`；旧404不能外推无代码。 |
| [CIPO](https://arxiv.org/html/2610.04991v1) | §3.3–3.4：参数绑定、软中断；首个可行粒度决策同前缀分叉，同策略续行，结果差辅助GRPO。 | 当前候选关注纠正片段内部条件效用；这是待验范围差异。配对、参数化及执行粒度本身已有。 |
| [CodePhage](https://people.csail.mit.edu/stelios/papers/codephage_pldi15.pdf) | §1.1：供体检查符号化、受体插入点/变量映射及回归验证，跨程序消除错误。 | 供体代码迁移与动态重绑定已有；自动片段提取不能单独当新贡献。须检验可复用策略/条件更新及续行收益。 |
| [Getafix](https://arxiv.org/abs/1902.06111) / [CEGIS agents](https://arxiv.org/abs/2606.11521) / [CESS](https://arxiv.org/abs/2607.15854) | 历史修复模式与上下文选择；验证器反例驱动纠正；锚点、回归约束与反例增补。 | 守卫归纳属复用部件。条件程序可作为Agent策略组件，无需相反外层标签；须在相同harness实际执行后证明来源反馈改变新任务表现，单独分支通过不足。 |
| [ReGAL](https://arxiv.org/html/2401.16467v2) | 11-12读§3.2/A.2：从query–program重构函数库；执行核验、保留失败、反馈重试、用成败测试更新/修剪helper。 | 执行反馈驱动程序抽象和更新已有。我们的固定谓词分类亦未超过Find-S；须检验自动程序/关系学习的额外机制，不将程序化、负例或更新循环换名。 |
| [SkillMorph](https://arxiv.org/html/2610.11858v1) | §2/4：跨重复、任务和演化轮的动作覆盖定位，再关联技能中的指令/脚本编辑位置并协调修订；固定模型/harness、留出任务评估。 | 失败轨迹定位和执行证据驱动技能修订已有，不能说它只看文本或没有实际行为。 |
| [SkillComposer](https://arxiv.org/html/2606.06079v1) | §3：create/improve/merge，delta pass rate拒绝采样训练；技能正文为主要表示，包含在线、离线与混合部署。 | 归纳、泛化和反馈修订已有；须比较同预算的一次归纳与普通修订，而非只比无记忆。 |
| [ASPIRE](https://arxiv.org/html/2607.00272v1) | §2.1–2.3：执行轨迹诊断、程序修复与搜索；验证后的修复归纳为含失败特征/适用条件/策略/代码草图的共享技能。 | 反馈形成可复用纠正经验已有；不能只将其改成可执行文件就算创新，须超过匹配的归纳/修订参照。 |

## 反馈与测试 oracle 的近邻

| 工作 | 已核范围 / 实验约束 |
|---|---|
| [Teaching Agents to Code Reliably](https://arxiv.org/html/2610.03984) | §2.1–2.3：补丁/回退差分执行、覆盖与变体区分。复现优先须是强基线；提示基线不称完整TACR。 |
| [Bayesian Control for Coding Agents](https://aclanthology.org/2026.emnlp-main.1548/) | §3–5/A.6及官方`2a3de1dc`的kernel/controller/校准模块：修好/修坏转移及在线Beta均值已有实现。普通条件化转移也是强基线，不将修复概率改名为创新。 |
| [Rethinking Self-Repair](https://arxiv.org/html/2611.06863v1) | §3–5/A/B：机器人reset-and-retry，固定指导和不同标签反馈与动态模板点估计相近，未检出其优势。补固定开发指导＋同预算重试；未测保留失败现场的恢复。 |
| [PracRepair](https://arxiv.org/html/2606.17612v1) | §III-C：静态/动态背景和修复假设指导补丁，以验证结果及前后行为差异再次诊断，最多3轮。动态证据、定位及重试已有，不能把输入整理收益当新方法。 |

## 其他近邻索引

旧blob保留StateGraph/Skill-V、SymC、VeriHarness、VBL、BiPACE、Grounding/SkillGLoW、Budgeted Verification、CodeT、ErrorProbe、CBC等；其余见[历史索引](../../docs/archive/2026-11-06_agent_research_context/README.md)。不在活表不代表失效。

## 对本项目实验的直接约束

1. 反馈可靠性、送达、采纳与能力分开；通用流程不是新机制。
2. 统一任务、信息、工具与总预算，保留普通历史、状态规则、全重验及最近邻。
3. 条件片段学习须面对普通反馈纠正、静态技能、简单接口/约束规则及匹配近邻；形成数据与模型预算一致，不用更多样本解释为独立机制。
4. 独立原生评分，形成/整理/取证/执行全成本；自写测试、AI检查、模式合法均不作任务成功。
5. 当前状态和授权见[短计划](STAGE2_AGENT_RESEARCH_PLAN_20261102.md)及[入口](../../docs/research/LOOP_D_RESEARCH_PROMPT.md)。

<a id="可执行候选反馈与经验的适用性而非又一个技能库"></a>
[历史候选诊断](../../docs/archive/2026-11-06_agent_research_context/rethinkskill_interface_diagnostics_20261105.md)
