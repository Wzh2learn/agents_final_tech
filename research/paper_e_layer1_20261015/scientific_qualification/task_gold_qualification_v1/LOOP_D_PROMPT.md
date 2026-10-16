# 可直接发送给 Loop D 的执行指令

你是 Paper E 的 Loop D。本轮只组织已批准的 task-gold qualification 人工标注与证据收口；不得让模型冒充人类标注者，不运行 Layer-2，不修改冻结稿或旧实验。

总规划师已拍板：
1. 批准从材料准备推进到真实双人独立人工资格核验，先归属 Paper E 升级线。大论文只能在后续通过资格与数据隔离审查后提议复用，当前不开放训练/记忆/反馈权。
2. v4 保留为词法绑定代理分析；“独立 binding gold 已构造”“10/11 已证实合法”的残留表述以本包 DECISION_AND_PROTOCOL.md 为准收紧。不要改写 v1-v4 或原解释文件。
3. 当前是固定真实问题在完整扰动资料上的任务证据保持性判断；不是模型输出正确率。多表头变化按整表条件判断，不做单列因果归因。
4. 已构建首批 12 个真实任务、12 张不同表，四类输入结构各 3 个。不要扩大到 24、按想要的标签替换案例或重选问题。12 个诊断案例不是新的未见确认集。
5. 基础人工 6 人时、协调与仲裁合计 2 人时，规划上限 8 人时。每人每题两阶段合计 15 分钟；到限记录不确定。无新增模型/judge/API/训练预算，Layer-2 不获授权。

只需先读以下绝对路径：

- D:/AIRcommend/JinRongAgents/agents_final_tech/research/paper_e_layer1_20261015/scientific_qualification/task_gold_qualification_v1/README.md
- D:/AIRcommend/JinRongAgents/agents_final_tech/research/paper_e_layer1_20261015/scientific_qualification/task_gold_qualification_v1/DECISION_AND_PROTOCOL.md
- D:/AIRcommend/JinRongAgents/agents_final_tech/research/paper_e_layer1_20261015/scientific_qualification/task_gold_qualification_v1/COORDINATOR_RUNBOOK.md
- D:/AIRcommend/JinRongAgents/agents_final_tech/research/paper_e_layer1_20261015/scientific_qualification/task_gold_qualification_v1/PREPARATION_RECEIPT.json
- D:/AIRcommend/JinRongAgents/agents_final_tech/research/paper_e_layer1_20261015/scientific_qualification/task_gold_qualification_v1/VALIDATION_REPORT.json
- D:/AIRcommend/JinRongAgents/agents_final_tech/research/paper_e_layer1_20261015/scientific_qualification/task_gold_qualification_v1/PACKAGE_MANIFEST.json

下文 BASE 指：
D:/AIRcommend/JinRongAgents/agents_final_tech/research/paper_e_layer1_20261015/scientific_qualification/task_gold_qualification_v1/

材料已经构建，无需再开发 harness、重跑 v4 或运行 PREPARE_MATERIALS.py：
- BASE/raw/：5 份原始数据 + 2 份旧获取回执；来源与哈希在 SOURCE_MANIFEST.json。
- BASE/coordinator/case_provenance.json：逐题真实 UID、原问题路径、源表/注入关系、变化单元格。只供协调者，不能发给 Stage1 标注者。
- BASE/exports/R1_stage1/ 和 R2_stage1/：第一阶段独立材料、HTML 阅读页、空白 CSV/JSON 表单。
- BASE/exports/R1_stage2/ 和 R2_stage2/：第二阶段原表与官方参考；两人 Stage1 全部封存后才能发放。
- BASE/coordinator/annotator_roster.json、seal_log.json：空白人员与封存台账。
- BASE/annotations/：空白仲裁表与资格状态模板。

执行顺序：
1. 核对材料数量、哈希及权限边界。材料准备 PASS 不等于 task-gold PASS。
2. 登记 owner 指定的两名真人标注者及仲裁/科学评审；没有真实人员则返回 AWAITING_HUMAN_ANNOTATION 和缺少的角色，不能用 agent 自动填满。
3. 按 RUNBOOK 逐阶段发放，每人只接收自己的目录。收件人和渠道由 owner 指定；不要自行向任何人发送消息。CSV/JSON 二选一作为正式提交。
4. 收到实际 Stage1 文件后保留原字节、计算真实 SHA256、记录真实收件时间；两人的 12 题均完成后才发 Stage2。未经实际收件不得填封存条目。
5. 两轮人工记录齐全后，做格式、来源、坐标、单位及分歧检查。两人一致但证据冲突也进入复核；不能用 U 率或一致率单独判定 gold 成立。
6. R3/科学评审根据证据给出资格意见。分歧未解决保留 U；官方参考错误单列。允许 TASK_GOLD_NOT_VALIDATED、INCONCLUSIVE。即使资格通过也只允许提交下一阶段设计，不启动实验。

写入边界：
- 允许追加 BASE/submissions/ 的真实原始提交及修订版本。
- 允许填入 BASE/coordinator/annotator_roster.json 和 seal_log.json 的实际事件。
- 允许在 BASE/annotations/ 下另存处理结果、disagreements.csv、TASK_GOLD_QUALIFICATION_v2.json、QUALIFICATION_REVIEW.md，以及 BASE/LOOP_D_RETURN.md。
- 不覆盖已发 exports、源数据、协议、准备回执、原空模板及已封存提交。
- 不修改 manuscript、claim matrix、scope lock、旧 v1-v4、旧停止状态；不新增通用平台代码。

验收与回写：
- 12 题 × 2 人 × 2 阶段 = 48 行真实阶段记录；不当成 48 个独立样本。
- 身份、盲态、时间、证据引用及分歧处理均可核验。没有真人记录时不验收为标注完成。
- LOOP_D_RETURN.md 分清“材料状态、人员状态、标注状态、科学资格状态”，报告 actual human hours、未决问题与唯一下一步。
- 总规划师下一轮只需读 LOOP_D_RETURN.md、annotations/QUALIFICATION_REVIEW.md、TASK_GOLD_QUALIFICATION_v2.json、disagreements.csv；有争议时再回溯原始提交。

停止条件：资料哈希不符、阶段提前暴露、人员不足、任务定义无法适用或人工预算耗尽。不得通过凑标签、放宽 gold、假造签名或额外调用模型绕过。

注意：本包数据目录被 Git 忽略，当前仅在本地；普通 git 同步不会传送材料。没有明确同步并逐文件核验前不得声称 GB10/远端数据齐全。本指令不授权公开发布或三端推送。

owner 补充实际人员与交付渠道（尚未提供时保持待人工）：
R1：________；R2：________；R3/科学评审：________；指定交付渠道：________。
