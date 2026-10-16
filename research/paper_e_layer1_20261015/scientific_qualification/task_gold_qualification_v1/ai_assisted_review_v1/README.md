# 单模型辅助标注诊断 v1

日期：2026-10-16（Asia/Shanghai）。状态：AI_DIAGNOSTIC_REVIEW；不是人工标注、独立 gold 或正式资格 PASS。

用户要求由当前助手实际标注并提供后续 Loop D prompt。本轮据此启动独立保存的 AI 辅助诊断支线，不伪造三个人，不改原人工方案的身份、封存、空表单或资格记录。

执行者 A1：当前 Codex/ChatGPT AI 助手。已见官方参考、源表、历史标签汇总、部分历史逐例标签与本轮全部 stage2 材料；属于 OPEN_BOOK_EXPOSED_REVIEW。没有重新经历盲态 Stage1，不补造 Stage1 提交或人工时间。

R1/R2/R3 的新工作分工见 REVIEW_ROSTER.json：R1 由 A1 做 AI 辅助初标；R2 指定 Loop D 做待执行的 AI 证据复核；R3 由同一个总规划师助手在 Loop D 返回后给综合建议，不是独立第三人仲裁。独立最终科学资格裁决尚未发生，不把三个角色称作三位独立评审。

## 本轮交付

- AI_ANNOTATIONS_v1.json：12 题实际 AI 判断，逐例参考复核、证据坐标、单位/时期、任务影响暂定标签、竞争解释与需要复核的问题。
- AI_ANNOTATIONS_v1.csv：同一批标注的便读表。
- CASE_REVIEW.md：逐题中文解释。
- MECHANICAL_CHECKS.json：来源、证据坐标与引用值、明确算式的本地复算，不能认证语义结论。
- REVIEW_ROSTER.json：真实角色与暴露说明；不修改原 human roster。
- LOOP_D_NEXT_PROMPT.md：接下来的 AI 证据复核指令，无需等待真人姓名即可完成本轮 AI 诊断。
- REVIEW_MANIFEST.json：本支线实际文件的哈希与输入 pin，不是验收签名。

## 科学边界

PRESERVED / ALTERED / UNDETERMINED 均为 A1 的 AI 暂定判断。官方参考核验状态同样仅代表 A1 的判断。机械复算成功不使其变成人工 gold，不报告人际一致率，不计算 checker FNR/FPR，也不将标签用于训练、经验库或论文已证实主张。

两种状态并存：原人工包继续 AWAITING_HUMAN_ANNOTATION；本支线已经完成 AI 逐例初标并等待 Loop D 复核。后续 AI 复核可发现、纠正或反驳初标，不升级为双人独立人工验证。

这是对前一轮组织方式的修订：不把三位真人到位设为本轮 AI 分析的前置条件；同时保留人工独立验证尚未发生的事实。Layer-2 实验与论文改稿仍未授权。
