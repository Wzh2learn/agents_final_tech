# 未决项与真实缺口

| 项目 | 当前状态 | 影响/处理 |
|---|---|---|
| R1/R2 真人身份、能力与盲态声明 | UNASSIGNED | owner 指定后才可收集有效人工记录；不能由 agent 代替 |
| R3 仲裁/科学评审身份 | UNASSIGNED | 最终资格需真实独立评审；无第三人则保留未决 |
| 真人答案、证据定位、任务影响标签 | AWAITING_HUMAN_ANNOTATION | 所有表单留空；官方参考不冒充本轮 gold |
| 官方参考正确性 | HUMAN_TO_VERIFY | 必须核验单位、时期、对象、推导；允许指出数据集本身问题 |
| Stage1 实际接收/封存哈希/Stage2 释放时间 | NOT_OCCURRED | 空数组不是签名或封存证明 |
| 原始 TAT-QA 获取时 upstream commit | UNRESOLVED | 既有回执仅记录 master；已核对文件 SHA256，不能补造 commit |
| 原始报告/文档 ID | UNRESOLVED | 有 table UID 和上下文指纹；不宣称报告级独立，不能直接用作未来确认集 |
| 四类语义现象是否真实覆盖 | HUMAN_TO_ASSESS | 当前只保证输入结构分层，不能预判语义保持/改变 |
| 第二阶段研究预算、模型/调用许可 | UNRESOLVED / NOT_AUTHORIZED | 人工资格结束也不自动运行 Layer-2 |
| 大论文数据隔离与反馈权 | NOT_AUTHORIZED | 本包是已暴露诊断材料，未经新裁决不得作为独立测试/训练反馈 |
| 跨端材料交付 | LOCAL_ONLY | 忽略目录不随 Git 同步；本次没有远端写入或公开发布 |

费用与时长是规划上限：8 人时，不是已经花费。科学结论可以是 INCONCLUSIVE 或 TASK_GOLD_NOT_VALIDATED；不要求凑足某种标签。
