# 导师决策表：证据优先级与 harmfulness 定义

> 状态: `RECOMMENDATION_ONLY / NOT_APPROVED / DO_NOT_EXECUTE`
> 日期: 2026-10-09
> 作用: 供导师比较选项，不构成路线决定、实验授权或结果声明。

## 1. Multi-leaf vs second dataflow

| 比较项 | Path M: multi-leaf / multi-stage injection | Path D: changed-pipeline second dataflow |
|---|---|---|
| 关闭的 reviewer attack | “只有一个 leaf 响应，因此 hierarchy/localization 结论不可识别” | “单一公开表格域、单一 pipeline，因此结果缺少 external validity” |
| 对 Stage E claim 的增益 | 可检验 visibility-to-localization 链条；若第二 leaf 独立响应，可把 localization 从 unestablished 变成可测问题 | 可检验 visibility profile 是否跨数据流复现；增强 measurement validity 的可迁移边界 |
| long-horizon | 中等：增加多阶段、多 checkpoint 的过程证据 | 高：改变 pipeline 结构，直接测试跨流程稳定性 |
| hierarchy | 高：直接检验多 leaf 下 evidence decomposition 是否仍有意义 | 中等：可比较 hierarchy 是否跨数据流保持，但不是首要目标 |
| localization | 高：是 Path M 的主要攻击面 | 低到中等：只有在第二流程也提供可观测 leaf-state 时才有帮助 |
| external validity | 低到中等：仍可能是同一语料和合成扰动 | 高：主要收益来源 |
| 是否需要新数据 | 不一定需要新 source；需要预先冻结的新 injection design | 需要新的 source/task-definition annex 和数据授权 |
| 是否需要新授权 | 需要实验设计、injection scope、GB10 执行窗口授权 | 需要 source、revision、file scope、licence、adapter、split、power 和独立 scorer 授权 |
| 预期工程成本 | 中低；主要工作是设计、预注册和多 leaf 证据合同 | 高；涉及数据获取、UID/role split、adapter、可观测性和独立复核 |
| 失败时仍得到的科学结论 | 可得到“多 leaf 可观测性/定位仍不可建立”的边界，或“新增 leaf 不改变 matched-FPR 结论” | 可得到 source/UID/observability gate 的 failure boundary；不能写成 E-D-R 被证伪 |
| 最大科研风险 | 仍是 synthetic / 单域；多 leaf 可能只是新测量表面，而非真实 localization | source 可能无法同时满足 independence、native bridge、harmfulness contract；成本可能先于证据产生 |
| 是否改变 frozen claim boundary | 不自动改变；任何升级都要新预注册、工件和独立审查 | 不自动改变；只有完整 gate 通过后才允许新 claim namespace |

**分析倾向。** 若目标是尽快补 Stage E 的 measurement gap，Path M 的依赖更少；若目标是回应 external validity，Path D 的科学价值更高但当前受真实外部输入阻塞。此倾向仅为分析，不构成选择。

## 2. Harmfulness 三种定义

| 比较项 | A. canonical equivalence 为主 | B. reader-referent equivalence 为主 | C. parallel constructs |
|---|---|---|---|
| 实际测量的 construct | 规范字段、canonical mapping 或功能结果是否保持 | 读者、下游任务或使用语境中的解释/决策是否被改变 | 同时保留规范等价与读者参照等价，不强行合并 |
| 与 visibility 是否独立 | 可以独立；先测 checkpoint 是否可见，再判 canonical consequence | 可以独立；但需要独立的 reader/task judgment protocol | 可以独立；两个 harmfulness judgement 都不得反向定义 visibility |
| reviewer 最可能质疑 | canonical preservation 不等于无害，可能掩盖真实使用后果 | 读者判断主观、样本少、依赖具体 reader/task，难以复现 | 指标数量增加，可能被质疑为多重比较或事后挑选 |
| 标注/复现成本 | 低到中等；可由冻结 schema/映射合同复核 | 高；需要明确 reader、task、rubric、独立标注者和可见性隔离 | 高；两套 rubric、两套报告和一致性审计 |
| 对现有 118 injections | 保留现有 criterion-dependent 记录；若改为主定义，需单独映射审计，不能静默重标 | 不能从现有 visibility/detection 结果推导，需新的 reader-referent judgement | 现有结果保留为一个 construct；另一个 construct 后续单独加入，不回写当前数字 |
| post-hoc definition risk | 中等；若看完结果后才选 canonical criterion，会有事后定义风险 | 高；若先看结果再选 reader/task/rubric，风险更高 | 最低；明确并列、分别解释，禁止事后合并成单一胜者 |
| 对论文最安全的写法 | “Under canonical equivalence, ...” | “Under reader-referent equivalence, ...” | “Harmfulness is reported as parallel, non-collapsed constructs under stated criteria.” |

**处理约束。** 本表不修改现有 harmfulness 定义，不重新标注 118 injections，不改变当前结果。无论选择哪一项，visibility、detection、harmfulness 仍保持正交，现有 frozen claim boundary 不变。
