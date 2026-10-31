# 真实技能学习基准中的反馈合同候选

2026-10-31。我们在公开 SkillLearnBench commit `726e1f79b96b0cb3d729d0e55a1c847e0b5353ae` 的 `financial-analysis` 开发任务中，发现一个可以复算的**参考实现与股票类别合同问题**。它适合研究 Agent 如何面对可能有缺陷或不充分说明的反馈，但目前不是 Agent 方法结果，也不能据此认定整个基准无效。

后续已在新增明确规则的受控改造任务上实际运行 [6 条 Agent 轨迹](FEEDBACK_CONFLICT_AGENT_PILOT_RETURN_20261031.md)：T1 实际答案触发两个检查器冲突；T2 五组均按当前合同答对，无历史和确定性程序亦答对，未观察到错误反馈的行动损害或提示的增益。该探索只使用上下文历史，未形成持久 skill。

## 发现一：参考实现中的相邻字符串被 Python 合并

[任务 1 的公开 solution](https://github.com/cxcscmu/SkillLearnBench/blob/726e1f79b96b0cb3d729d0e55a1c847e0b5353ae/tasks/financial-analysis/financial-analysis-1/solution/solve.sh)将股票类别列表中的部分字符串写在连续行上但没有逗号。Python 会拼接相邻字符串字面量：[AST 与 token 复算](audit_13f_class_literals.py)发现源码包含 25 个字符串 token，运行时列表只有 10 项；本地检查的 1–6 六个 solution 都出现这一结构。我们不运行 solution，只静态解析其 Python heredoc。

使用相同 Q3 输入与目标管理人的申报，分别按**实际运行时列表**和**逐个分开源码中的字符串**计数：

| 暴露开发任务 | 发布的 q2 参考 | 实际运行时列表 | 分开字符串的反事实 | 差异 |
| --- | ---: | ---: | ---: | ---: |
| financial-analysis-1 | 2,451 | 2,451 | 2,710 | +259 |
| financial-analysis-2 | 896 | 896 | 938 | +42 |

原实现计数与两个发布参考一致；这与其来源相容，但**不能证明**参考答案由该文件生成。差异来自原代码中单独写出的类别文本，例如 `sponsored adr`、`cl b`、`ord shs` 等；逐个分开只是一项有依据的**语法反事实**，不是经金融专家认证的完整股票类别标准。数值、类别分解和输入/solution/参考的 SHA-256 见[只读复算](skilllearnbench_13f_class_literal_audit_20261031.json)。

## 发现二：该反事实会被原测试的精确比较拒绝

我们构造两对**特权控制样本**：其他答案直接取发布 expected，只有 q2 分别填原参考或上述反事实计数。隔离无网容器中挂载原 `tests/test_outputs.py` 与 expected，运行其 pytest 断言：两个参考控制各 **2/2 通过**；两个反事实控制各 **1 通过、1 失败**，失败处分别为 `2710 == 2451` 与 `938 == 896`。日志和文件 hash 见[控制汇总](skilllearnbench_13f_feedback_controls_summary_20261031.json)，构造器为 [prepare_13f_feedback_controls.py](prepare_13f_feedback_controls.py)。

这些是使用了参考的合成控制，不是 Agent、用户或官方完整 harness 的运行；没有执行原 `test.sh` 的在线安装部分。它证明所检查的断言会对这个合同反事实给出失败反馈，不证明反事实是唯一正确答案或生产系统中的错误率。

## 参考仍存在其他可观察边界

[独立数据重算](skilllearnbench_13f_fund_recheck_20261031.json)在两个目标管理人的 Q3 申报上逐行求和 `INFOTABLE.VALUE`，与对应 `SUMMARYPAGE.TABLEVALUETOTAL` 和题目 q1 发布参考一致。但 SEC 13F 报告的是规定范围内的申报证券；将该值直接称为基金**全部 AUM**缺乏依据。q2 的自然语言“stocks”也没有定义 ADR、股份类别等具体纳入规则，因此需要把构念与可执行合同区分开，不能仅凭数值差断言金融语义真值。

另一个风险是把季度压缩包当作报告期过滤器：[时期/主体检查](skilllearnbench_13f_periods_20261031.json)发现 Q2/Q3 包分别有 788/469 条其他报告期的提交；Q2 对 `berkshire hathaway` 的子串查找还同时命中不同实体和前期修订记录。SEC [数据目录](https://catalog.data.gov/dataset/form-13f-data-sets)按申报窗口组织数据，[13F FAQ](https://www.sec.gov/rules-regulations/staff-guidance/frequently-asked-questions-about-form-13f)说明报告证券范围。本地 ZIP 尚未与 SEC 官方字节匹配。

## 对第二篇的研究机会

可以将真实来源中的**反馈合同冲突**作为开发材料：当任务明确给定某个可执行类别规则，而评分器反馈由不同实现产生时，Agent 能否利用可见输入、工具执行和反馈来源判断“采纳修正、保留原解、补充取证或报告不确定”，并在后续任务中更新经验？这需要与直接遵循明确规则、同预算普通重试、原始轨迹、总是采纳/总是忽略反馈、简单一致性检查以及 SkillLearnBench/反馈噪声近邻比较。

若为实验显式补入类别定义或制作受控评分冲突，必须标为**人工构造的合同变化**，不能称原自然题已有唯一正确类别；Agent 看不到隐藏 expected 和 tests。至少再找不同来源的自然工作流，包含可靠反馈、冲突反馈和本来无法判定的控制；检验是否改善独立任务完成及旧行为保留，并计入生成、取证、验证和更新的总成本。当前没有模型学习或迁移结果，候选新颖性也尚未成立。

本次来源扫描、数据重算和四个 pytest 控制均为 CPU 只读/离线工作，新增模型调用、judge、训练、付费 API 和生产 Memory 写回均为 0。原材料、控制答案和日志保存在 GB10 `/home/testuser/wzh/research_evidence/agent_learning_20261030/skilllearnbench_13f_feedback_controls_20261031/` 及同目录 JSON 中；本仓库保存脚本、聚合结果和 hash，不提交 13F 数据或参考答案文件。
