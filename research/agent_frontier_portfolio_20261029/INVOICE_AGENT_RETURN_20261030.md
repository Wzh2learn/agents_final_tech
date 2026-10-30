# Invoice benchmark: skills, feedback and simple-rule control

2026-10-30。状态：**第三个真实工具 Agent 开发任务，非独立 benchmark 或模型未见来源确认。** SkillsBench v1.1 checkout `b63b7b2850226b6aa4fb5929a8c1ac7bc4d9a6af`，任务是根据发票 PDF、供应商表及采购订单按固定优先顺序标注异常。所有材料为公开任务数据，不是线上财务审核。公开输入及 SHA-256、环境和预算见[实验卡](INVOICE_AGENT_PILOT_PLAN_20261030.md)、[逐次账本](invoice_agent_summary_20261030.json)。Python 容器使用 pypdf 6.4.1、openpyxl 3.1.5 和 rapidfuzz 3.14.3，与原 Dockerfile 的完整环境并不完全相同；隐藏 verifier 和参考数据仅在 Agent 结束后挂载。每条一轮，模型预训练曝光未知。

| 条件 | 实际输出和原 verifier | 按页检出 P/R | 异常原因与参考一致 | 物理 POST |
|---|---|---|---:|
| 无 skill 起始 | 有报告，1/2 测试通过 | 1.000 / 1.000 | 18/50 | 16 |
| 原任务全部 skill | 未生成报告，0/2；达到请求上限 | 无可评分输出 | — | 16 |
| 相同起点 + neutral 失败反馈 | 报告与起始输出逐字节相同，1/2 | 1.000 / 1.000 | 18/50 | 7 |
| 相同起点 + 精确匹配诊断 | 生成报告，2/2；Agent 随后达到请求上限 | 1.000 / 1.000 | 50/50 | 16 |
| 不调用模型的精确匹配优先修复 | 生成报告，2/2 | 1.000 / 1.000 | 50/50 | 0 |

上表 P/R 和原因一致由[诊断脚本](score_invoice_output.py)在 Agent 后使用参考汇总；该脚本不检查每个字段，完整字段以原两项测试为准。该面板只有 3 张 clean、50 张异常，纯粹标记所有 53 页的下限基线已经有 P=50/53≈0.943、R=1，但不给出正确原因。页级检出几乎相同不能代替理由和字段正确性；0/2 分别对应原 verifier 的文件存在及内容检查，不是 0 个正确案例。

**机制及强基线**：原始代码在已有完全相同供应商名称时仍使用 `rapidfuzz.partial_ratio`：`Vendor 11` 与 `Vendor 1`、`Vendor 31` 与 `Vendor 3` 的分数均为 100，导致错误映射。具体反馈要求先精确匹配、后模糊匹配并重建报告；Agent 输出与参考 50/50 原因一致。之后[确定性规则补丁](prepare_invoice_exact_match_control.py)对同一初始程序直接加入 exact-first 判断，也得到 2/2、50/50，生成 JSON 与诊断 Agent 的 JSON 内容完全一致。**这个开发面板不能证明模型修复优于给定同一诊断的简单规则**；但它显示一条自然工具轨迹中，反馈可以改变从文件读取到最终报告的实际行动。

**持久产物复算**：原无 skill Agent 保存的程序在新隔离容器里重跑，原因一致由已保存报告的 18/50 变为 20/50，说明代码和原报告不同步；如 page 2，PDF 金额 8347.33、订单金额 1587.74，最新代码可识别金额不一致，但旧报告仍为 vendor mismatch。具体反馈组保存的程序在新容器里重跑得到的 JSON 与其 Agent 报告相同。容器和轨迹不同步的历史记录保留不重写。

**成本与边界**：4 个 Agent episodes 共 **55 POST / 763,357 returned step tokens（含缓存输入）**；没有训练、付费 API、生产 Memory 写回。两条修复从同一初始程序与报告 hash 开始，模式修正允许写入。反馈与 exact-first 规则在看过初始失败之后构造，是事后开发对照，不是跨来源确认；参考标签未做人工独立审计，不能外推真实金融场景。完整原始轨迹、失败与 verifier 存在 GB10 `/home/testuser/wzh/research_evidence/agent_learning_20261030/invoice_agent/`；附加 deterministic 和 replay 材料分别位于同级 `invoice_exact_match_control_20261030/`、`invoice_diag_reexecution/` 和 `invoice_no_skill_reexecution/`。

**下一步**：在不同来源/不同自然任务上保留诊断可用性相同的规则 baseline，研究何时从经验中选择适用的检查、何时反馈会造成新错误，以及如何在质量与 token/工具成本之间取舍。这个案例本身不构成新算法或 IJCNN 投稿充分证据。
