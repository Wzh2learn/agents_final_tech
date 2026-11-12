# 第二篇：近邻、重合与实验判别

> 更新至2026-11-13。D定向读方法，未复现原法；前表及删减细节见`bdb85edb`本文件Git blob，早期见`89ca0dbd`。按问题加载。

## 当前裁决

**FCCL主线：从执行反馈学习可复用纠正策略。** 尚无成立新方法。当前跨角色续行程序仅为候选；角色标签、可执行程序、配对执行和反馈更新本身已有，不以新载体替代增量。

## 最直接的方法近邻

| 工作 | 已核机制 | 当前必须解决的区别 |
|---|---|---|
| [Agent-R](https://arxiv.org/html/2501.11425v1) / [STeP](https://arxiv.org/html/2505.20023v1) | 共享前缀纠正/MCTS及迭代SFT；教师反思轨迹、错误动作部分mask。 | 从失败续做/正确片段学习已有，须证明条件纠正的额外收益。 |
| [HASP](https://arxiv.org/html/2605.17734v2) / [官方代码](https://github.com/HolaYan/ExecutableSkills-HASP) | §2/A/B：should_activate/intervene可执行触发、动作改写/上下文/弃权，执行过滤及技能更新；所读官方`2a0e859e`亦含配对重生成。 | 可执行纠正、条件触发、反馈更新、配对本身均已有。当前实现没有超越它的证据；单个训练函数用本轨迹信号，不代表整篇无配对。 |
| [SkillRevise](https://arxiv.org/html/2606.01139v4) | §3.1–3.4：诊断/原则绑定、执行锚点、保留约束、重执行、效用门；搜索继续自最新候选，返回最佳候选。 | 已覆盖有锚点的纠正；不能用中间零收益推断它无法越过。需同信息/候选/总成本适配比较。 |
| [AdaMEM](https://arxiv.org/html/2606.05684v1) | §3.1–3.2：动态策略记忆，成功/动作改变筛选；反事实动作不实际执行。 | 条件策略须由实际片段及续行后果支持，动作变化本身不是收益。 |
| [SkillApt](https://arxiv.org/html/2609.26863v3) | 条件化配对效用、Load/Abstain。 | 条件效用本身不新。作者公开包为guoshaung/SkillApt，`73db0b54`；旧404不能外推无代码。 |
| [CIPO](https://arxiv.org/html/2610.04991v1) | §3.3–3.4：参数绑定、软中断；首个可行粒度决策同前缀分叉，同策略续行，结果差辅助GRPO。 | 当前候选关注纠正片段内部条件效用；这是待验范围差异。配对、参数化及执行粒度本身已有。 |
| [CodePhage](https://people.csail.mit.edu/stelios/papers/codephage_pldi15.pdf) / [Getafix](https://arxiv.org/abs/1902.06111) / [CEGIS](https://arxiv.org/abs/2606.11521) / [CESS](https://arxiv.org/abs/2607.15854) | 供体检查/变量映射、历史修复模式、反例增补与回归验证。 | 重绑定/守卫归纳为复用部件，须在同harness证明后续任务收益。 |
| [ReGAL](https://arxiv.org/html/2401.16467v2) | 11-12读§3.2/A.2：从query–program重构函数库；执行核验、保留失败、反馈重试、用成败测试更新/修剪helper。 | 执行反馈驱动程序抽象和更新已有。我们的固定谓词分类亦未超过Find-S；须检验自动程序/关系学习的额外机制，不将程序化、负例或更新循环换名。 |
| [SkillMorph](https://arxiv.org/html/2610.11858v1) | §2/4：跨重复、任务和演化轮的动作覆盖定位，再关联技能中的指令/脚本编辑位置并协调修订；固定模型/harness、留出任务评估。 | 失败轨迹定位和执行证据驱动技能修订已有，不能说它只看文本或没有实际行为。 |
| [SkillComposer](https://arxiv.org/html/2606.06079v1) | §3：create/improve/merge，delta pass rate拒绝采样训练；技能正文为主要表示，包含在线、离线与混合部署。 | 归纳、泛化和反馈修订已有；须比较同预算的一次归纳与普通修订，而非只比无记忆。 |
| [ASPIRE](https://arxiv.org/html/2607.00272v1) | §2.1–2.3：执行轨迹诊断、程序修复与搜索；验证后的修复归纳为含失败特征/适用条件/策略/代码草图的共享技能。 | 反馈形成可复用纠正经验已有；不能只将其改成可执行文件就算创新，须超过匹配的归纳/修订参照。 |
| [WER](https://arxiv.org/html/2608.17587v1) / [代码](https://github.com/littlepkk/WER4skill-optimizer-training) | §3.1–3.4：冻结执行器，执行技能文档；同任务/技能成败轨迹驱动下一阶段技能优化及组相对RL。 | 真实成败驱动技能更新已有且覆盖tau2；须检验具体续行程序编辑收益。 |
| [Skill-α](https://arxiv.org/html/2608.01678v1) / [代码](https://github.com/ejhshen/skill-alpha) | §4.1–4.3：Create/Update/Merge/Prune/Noop；锚定query旧/新技能执行回滚奖励＋GRPO。 | 编辑信用与反事实奖励已有。可参考固定worker、短轨迹经验批设置，不将其称新学习规则。 |

## 反馈与测试 oracle 的近邻

| 工作 | 已核范围 / 实验约束 |
|---|---|
| [TACR](https://arxiv.org/html/2610.03984) / [Bayesian Control](https://aclanthology.org/2026.emnlp-main.1548/) | 差分执行/覆盖；修好与修坏转移、在线Beta均值（已核官方`2a3de1dc`）。普通差分诊断与条件转移须作强基线，提示适配不称原法复现。 |
| [Rethinking Self-Repair](https://arxiv.org/html/2611.06863v1) / [PracRepair](https://arxiv.org/html/2606.17612v1) | 固定指导/同预算重试；执行差异诊断和最多3轮修复。动态反馈或整理输入本身不是新机制；前者未测保留失败现场恢复。 |
| [World Model Predictive Paths](https://arxiv.org/abs/2610.28945) | 本轮仅核摘要：多候选动作、世界模型预测、MPPI式选择及双支经验记忆。正文/代码未核，不作完整比较；“预测后果再决策”本身不能当创新。WorldRepair原始PDF访问受验证页阻挡，方法差异仍待核。 |

## 其他近邻索引

[tau2原文](https://arxiv.org/html/2506.07982v1)§3已有双侧工具协作及官方进度流程。v1.0.1 `fc0055dc`已接入；[程序学习尸检](results/CONTINUATION_PROGRAM.md)未显示方法优势，下一比较效果保持与简单防重复规则。分支恢复双侧历史/DB；不同领域仍属同一benchmark。

旧blob保留StateGraph/Skill-V、SymC、VeriHarness、VBL、BiPACE、Grounding/SkillGLoW、Budgeted Verification、CodeT、ErrorProbe、CBC等；其余见[历史索引](../../docs/archive/2026-11-06_agent_research_context/README.md)。不在活表不代表失效。

## 对本项目实验的直接约束

1. 反馈可靠性、送达、采纳与能力分开；通用流程不是新机制。
2. 统一任务、信息、工具与总预算，保留普通历史、状态规则、全重验及最近邻。
3. 条件片段学习须面对普通反馈纠正、静态技能、简单接口/约束规则及匹配近邻；形成数据与模型预算一致，不用更多样本解释为独立机制。
4. 独立原生评分，形成/整理/取证/执行全成本；自写测试、AI检查、模式合法均不作任务成功。
5. 当前状态和授权见[短计划](STAGE2_AGENT_RESEARCH_PLAN_20261102.md)及[入口](../../docs/research/LOOP_D_RESEARCH_PROMPT.md)。

<a id="可执行候选反馈与经验的适用性而非又一个技能库"></a>
[历史候选诊断](../../docs/archive/2026-11-06_agent_research_context/rethinkskill_interface_diagnostics_20261105.md)
