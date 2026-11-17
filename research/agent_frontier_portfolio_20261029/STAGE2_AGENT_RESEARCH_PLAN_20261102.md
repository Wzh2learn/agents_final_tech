# 第二阶段：执行反馈驱动的纠正学习

> 2026-11-17｜Goal active。独立提案/采纳33/64已闭合；旧成对37/64和路由36/64保留，下一转接管价值，新64未执行。

## 现役问题与执行规则

从真实执行反馈学习可复用纠正能力，在金融文档/工具计算中提高成功率或降低部署成本。FinQA主集、TAT-QA相关增强，跨场景适配留后续；Paper E和开题由独立对话维护。

保留原Actor与121组回放，只用rebind_operand、scale_output、prepend_step、KEEP；沿用解析/执行器，不建语义图编译器。首分叉margin/mask/系数扫参停止。每轮一个候选实现/训练后尽快真实出分，对缓存普通33/旧成对37；DEV净增至少3题再补消融和确认。探索不打包、不逐文件核SHA、不写长方法日志；失败、费用和未知用量保留。

## 已闭合结果：避免重复

- **旧成对学习**：88组开发普通33/成对37，53题一次确认均30（各恢复1/错改1）；源覆盖版DEV31，同121组扩样普通33/成对34。保留局部修复，不再扫首分叉。[结果](results/FINQA_CORRECTION_LEARNING.md#teacher-formation-expansion-v3)
- **四算子学生**：501更新后DEV33全KEEP。弱提案TRAIN32恢复0/错改5；强制冻结8B非KEEP解码仍恢复0/错改9，停止这版。[结果](results/FINQA_CORRECTION_LEARNING.md#campus-value-pilot)
- **27B路由**：TRAIN96恢复7/错改4；DEV36/64，保持33、恢复3、错改0，18调用。完整27B37；同18调用的错误风险/固定随机也36，仅问题35。可用作预算层，独立机制优势尚未拉开。[结果](results/FINQA_CORRECTION_LEARNING.md#correction-value-router-v1)
- **角色与校内候选**：角色头三版各4,416次CPU更新，DEV均33；完整语义向量使TRAIN恢复2→9、未外推，固定零阈值也无恢复。DeepSeek同96个TRAIN恢复7/错改4；效用头1,000次CPU更新后DEV33、21调用、0恢复/0错改。停止门槛扩展。[结果](results/FINQA_CORRECTION_LEARNING.md#role-repair-pilot)

## 下一步：复用最强轻量专家，学习接管净收益

按Goal备选转纠正价值。先补旧37模型在同96个TRAIN原始现场的真实OpenCode结果，与现有27B/DeepSeek结果对齐，学习哪个专家相对轻量参照有增益；旧37的DEV输出不得进入监督。完成一个预算内选择候选并原生出分，对缓存33/37及同预算错误风险/随机选择；不将通用路由或问题难度预测另称新方法。[形式化](results/FINQA_CORRECTION_METHOD.md#correction-value-algorithm)

独立提案/采纳456更新完成，TRAIN96提案恢复4/错改45，校准选择全KEEP，最终全部64原程序实际执行为33/64。本版不扩训、不调采纳门槛；35次DEV探索中34完整、0恢复/15错改，另1中断费用未知，未完成全64提案。[本批](results/FINQA_CORRECTION_LEARNING.md#proposal-acceptance-v1)

输入前缀已消除425token工具说明错配，新现场仅日期两token变化；不能继续用旧混杂解释当前无增量。保留31来源66目标、权重和5个部分正确动作，后者不是已验证多轮恢复。

可用材料：

- 30个成功教师补丁有296个实际执行子集（258错/38对/0无效）；29个原可执行错例中19个需至少两处联合改动，15个不含前置步骤。保留完整与部分修复的联合信用，不把子集当独立来源。
- 27B与DeepSeek在同96个TRAIN各恢复7题，只重合3题，合并11个不同现场，按来源去重。153可用形成来源已运行前96个，新材料继续按固定隔离规则取用。
- 旧经验/训练/融合的正向与死因保留在[机制知识](results/CONTINUATION_PROGRAM.md#mechanism-knowledge)；方法近邻按需查[索引](IJCNN_RELATED_WORK_REFRESH_20261030.md)。

**确认隔离**：按原固定117组顺序，64开发/53一次确认均已使用。另预约64个未用TRAIN公司年份来源（b1e888b0），仍RESERVED_NOT_EXECUTED；不得入形成/训练，DEV答案与教师输出也不得转TRAIN。[预约](results/FINQA_CORRECTION_LEARNING.md#project-filing-reservation-v2)

12月中旬依据具体机制、强简单基线、新来源确认与成本曲线判断IJCNN投稿条件；允许局部有效，不要求全领域领先。

## 成本与运行

本地FinQA累计5,560POST/23,405,326已知＋12未知393,216；校内5,510POST/53,214,738＋11未知2,883,584，含预留合56,098,322/10亿。本批131本地POST/493,696＋1中断未知；训练另456 GPU更新/783前向，采纳1,000 CPU更新，临时接线回放另1,000更新。TAT不变。[账本](results/FINQA_CORRECTION_LEARNING.md#finqa-costs)

本批进程已退出。27B恢复guard3937795/21003143、health200，可用75.1GiB，保留32GiB保护；无科研任务在跑。权重与短回执同步本机，raw留GB10，不制包、不逐文件核SHA。中断后循环曾继续，现让原生KeyboardInterrupt向上终止；恒KEEP以后直接执行原程序，不生成无用提案。

纠正阶段成本：普通/旧成对64POST，251,682/252,002tokens、366.89/388.52秒；27B路由18POST/71,053tokens、405.51秒，编码另8.56秒；完整27B64POST/249,755tokens、1,638.18秒。新DeepSeek路由21POST/104,397tokens、375.07秒，复用编码。共同首轮不重复计费；跨模型token减少不等于本地耗时减少。随机2000个分配的均值34.13、5%/95%分位32/36，单次随机36不是均值。

<a id="当前优先级2026-11-04"></a>
<a id="地震与板块工作流下一组开发对照2026-11-03"></a>
<a id="工具修复反馈接入与-astropy-批次2026-11-05"></a>
<a id="与-paper-e-并行"></a>
[旧探索归档](../../docs/archive/2026-11-06_agent_research_context/README.md)。
