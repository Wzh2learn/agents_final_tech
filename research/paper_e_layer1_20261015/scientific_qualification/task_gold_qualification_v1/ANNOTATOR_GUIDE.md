# 独立人工标注说明

这是研究材料的资格诊断，不是考试。允许无法确定；不要为了完整率猜答案。请独立填写，不查网络、不调用模型、不读取另一人的答案或未发放文件。你应能阅读英文财报与少量中文表头；不熟悉的词义请明确记录。

## Stage 1：仅用所发材料作答

打开本目录 PACKET.html，阅读每题、扰动后完整表格和完整段落。对每题记录：答案、单位/scale、时期、对象、计算或引用依据、表格单元格和段落、可答性以及耗时。

同目录 responses.csv 与 responses.json 二选一作为正式记录。UTF-8 CSV 可用支持 UTF-8 的表格软件打开；不得把科学计数法/日期转换后的值默默当原答案。必要时用 JSON 或以文本保留原值。annotator_kind 填 HUMAN，annotator_id 填你真实使用的研究人员代号；不要由代理预填。时间使用带时区的 ISO 8601，elapsed_minutes 为实际分钟。

answerability 取 ANSWERABLE / UNANSWERABLE / UNCERTAIN；不会做或语义不明时写 UNCERTAIN 并说明。空白只代表尚未作答，不代表 U。答案可以使用原有段落提供的信息，不要人为删除冗余证据。

表格坐标从 0 开始：r0 是第一行，c0 是第一列。evidence_cells 示例格式为 r2c1;r3c1（只是格式示例，不对应任何题的正确证据）；evidence_paragraphs 写原段落 order 或 uid。不得只引用最后数值而不说明其对象与时期。

提交后不要覆盖原文件。协调者封存两人的 Stage 1 原始提交后才会发 Stage 2。你不应自行打开 Stage 2。

## Stage 2：核验参考与任务证据

该阶段增加原表与数据集官方答案/derivation/scale。先核验官方参考；官方答案也可能有问题。reference_status 填 CONFIRMED / QUESTIONABLE / INSUFFICIENT，并填写 verified_reference_answer、单位/时期/对象、依据与推导。不要只复制官方答案作为核验。

然后判断相同问题在完整扰动材料中是否仍有相同且有依据的答案。task_effect 取：

- PRESERVED：答案及单位、时期、对象、必要证据关系仍成立。须引用扰动资料的依据；不能仅说数字没变，也不能凭已知原表猜回缺失表头。
- ALTERED：能具体证明答案/单位/时期/对象/必要证据关系改变，或原答案因关键证据损坏不再被唯一支持。说明改变或冲突在哪，并讨论可用上下文能否消除它。
- UNDETERMINED：参考本身不可信、信息不足、领域/语言知识不足或无法在合理解释之间裁决。reference_status 非 CONFIRMED 时必须选此项。

另填 perturbed_answerability（ANSWERABLE/UNANSWERABLE/UNCERTAIN）与 change_relevance（RELEVANT/IRRELEVANT/UNCERTAIN）。变化与本题无关可能支持 PRESERVED，但仍须证据。你的 Stage 1 计算错误本身不构成 ALTERED，数值相同也不必然构成 PRESERVED。

检查答案精度、scale（例如 million 与 percent）、符号和引用对象。tolerance_and_basis 记录参考精度或明确计算依据，不统一放宽容差。只有在 Stage 2 对先前答案有所修正时才填 stage1_revision_reason，原 Stage 1 保留。

## 时间、独立性与提交

每题两阶段合计以 15 分钟为上限；到限保留不确定原因，不强迫猜测。独立完成，不讨论个案结论。prior_exposure 如实记录是否见过旧标签、检查器判断或其他人的回答；若已见过，在分析中标记暴露，不伪称盲态。

所有人类裁决栏由本人填写。AI/脚本只允许整理与格式校验，不能冒充第二位人类。完整包的正式资格结论由后续科学评审给出，你的个人标签不是自动生效的 gold。
