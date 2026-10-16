# 发给 Loop D：推进 AI 辅助证据复核，不再等待真人身份

你是 Paper E 的 Loop D。本轮执行 R2：对已经完成的 12 题 AI 初标做证据复核。该轮明确属于 AI 辅助诊断，不是人工标注；不要把模型登记为真人，不需要等待 R1/R2/R3 的真人姓名才能完成本轮工作。

用户已要求总规划师助手直接标注。总规划师已完成 12 题初标，并将实际身份与分工记录在独立支线：
- R1：当前 Codex/ChatGPT 总规划师助手 A1，AI 初标已完成。
- R2：Loop D，AI 证据复核，本次待你执行。
- R3：总规划师助手收到你结果后给综合建议；与 A1 同一执行者，不是第三名独立评审。
- 交付渠道：本地文件 + owner 手动粘贴 prompt，无自动外发。

重要事实：A1 已见官方参考、原表、历史标签汇总及部分逐例标签，属于 OPEN_BOOK_EXPOSED_REVIEW；没有完成盲态 Stage1，也没有人类标注或独立 gold。原人工协议/人员表/封存表继续保留原状态。不能将这条 AI 支线改写为原人工方案已完成。

根目录 BASE：
D:/AIRcommend/JinRongAgents/agents_final_tech/research/paper_e_layer1_20261015/scientific_qualification/task_gold_qualification_v1/

先读以下绝对路径：
1. D:/AIRcommend/JinRongAgents/agents_final_tech/research/paper_e_layer1_20261015/scientific_qualification/task_gold_qualification_v1/ai_assisted_review_v1/README.md
2. D:/AIRcommend/JinRongAgents/agents_final_tech/research/paper_e_layer1_20261015/scientific_qualification/task_gold_qualification_v1/ai_assisted_review_v1/REVIEW_ROSTER.json
3. D:/AIRcommend/JinRongAgents/agents_final_tech/research/paper_e_layer1_20261015/scientific_qualification/task_gold_qualification_v1/ai_assisted_review_v1/AI_ANNOTATIONS_v1.json
4. D:/AIRcommend/JinRongAgents/agents_final_tech/research/paper_e_layer1_20261015/scientific_qualification/task_gold_qualification_v1/ai_assisted_review_v1/CASE_REVIEW.md
5. D:/AIRcommend/JinRongAgents/agents_final_tech/research/paper_e_layer1_20261015/scientific_qualification/task_gold_qualification_v1/packets/stage2_cases.json
6. D:/AIRcommend/JinRongAgents/agents_final_tech/research/paper_e_layer1_20261015/scientific_qualification/task_gold_qualification_v1/DECISION_AND_PROTOCOL.md
7. D:/AIRcommend/JinRongAgents/agents_final_tech/research/paper_e_layer1_20261015/scientific_qualification/task_gold_qualification_v1/ai_assisted_review_v1/MECHANICAL_CHECKS.json

必要时查 BASE/coordinator/case_provenance.json 和 BASE/raw/ 的真实源材料，不重建数据包、不重跑 v4、不改题、不补造新案例。

任务：
1. 逐题复核 A1 给出的参考答案、计算、单位/时期/对象、证据引用及暂定任务影响。不要只核对 JSON 字段齐全；对每题明确 ACCEPT_PROVISIONAL / REVISE / UNRESOLVED 及理由。ACCEPT_PROVISIONAL 只是接受AI诊断建议，不是科学PASS。
2. 对 Q01、Q07 优先核查原题期间与官方推导的歧义；不要把原参考缺陷归因于扰动。
3. 对 Q06 优先反驳 A1 的 ALTERED：只用扰动表与段落，能否唯一恢复 purchased intangible assets 的列与单位？若能，用精确证据推翻 A1。若不能，说明是证据损坏候选，不称已观测模型失败。不得为了保住唯一 ALTERED 强行接受。
4. 对 Q08、Q09 检查附加年份/范围词究竟能否从现有上下文明确排除；无法排除就保留不确定，不临时建立有利于某结果的冲突优先规则。
5. 对 Q11 查包内已有材料能否直接确认 million scale，以及官方 paragraph 11 是否确实支撑该经营收入问题；没有直接证据则记录缺失，不凭其他指标单位补齐。
6. 对六个暂定 PRESERVED 同样做证据复核，区分“被改列与本题无关”“冗余上下文恢复”“语义变化确实无影响”。尤其 Q12 只对其特定 receipts 问题成立，不推广到整个表。
7. 汇总本轮暴露的是参考题质量问题、问题与扰动不相关、上下文冗余、真实语义损伤候选，还是尚无法裁决。不要报告人际一致率或总体有害率。

本轮输出目录，仅追加新文件：
BASE/ai_assisted_review_v1/loop_d_review_v1/

交付：
- LOOP_D_CASE_REVIEW.json：12 题逐例复核及差异；明确 actor_kind=AI、blind=false、human=false、qualified=false。
- DISAGREEMENTS.md：真正有证据分歧的条目与反驳，不强求一致。
- NEXT_RESEARCH_DECISION.md：给总规划师的下一步建议，说明哪些定义能收敛、哪些需要更强来源；若建议新任务或新对照，只写设计与预算，不运行。
- LOOP_D_RETURN.md：实际执行、证据发现、剩余缺口与唯一下一步。不要以“未提供真人姓名”结束这轮 AI 复核。

边界与预算：
一个完整逐例复核回合；如有材料读取/格式问题允许一次修正。使用当前执行对话进行分析与本地确定性复算，不另启动模型/judge服务、子代理或生产API，不训练。
不修改 A1 初标、旧人工包、原身份表/封存表、官方题目、准备哈希、冻结稿、v1-v4 或既有停止状态。不扩样本、不凑标签、不重开旧分支。
输出可保留分歧和 NOT_VALIDATED；不需要把 6/1/5 变得更好看。机械复算通过不等于语义成立。Layer-2 实验、论文改稿及大论文训练/反馈仍未授权。

研究定位：本轮产物可以帮助修订测量契约与筛出需进一步核验的案例，不能写成独立人工 gold。若希望以后采用纯AI评价，须另提透明的方法契约、误差验证与论文主张边界，不能改个角色名称就视为原方案完成。
