# 第二阶段：执行反馈驱动的纠正学习

> 2026-11-17｜Goal active。共享教师状态效用模型已开训；旧37/64保留，新64未使用。

## 当前候选与交付

目标是在金融文档/工具计算中学习可复用纠正能力，提高成功率或降低部署成本。四算子生成器与旧小值头按止损停止；本轮转既定接管价值备选。Paper E及开题由独立对话维护。

**共享教师结果，学习当前状态的接管价值。** 教师固定从原始快照生成替代程序，本地状态可以取已执行的原程序、旧37纠正、失败提案和补丁子集。一次实际教师轨迹可计算各本地状态经同一单位保护后的收益/损害/中性标签；不假装教师执行过不同输入，不将视图当独立来源。[方法](results/FINQA_CORRECTION_METHOD.md#shared-teacher-value)

- 完整教师TRAIN96已完成182POST/858,816tokens；本地61成功，原始教师63，单位保护及失败回退后74（恢复16/错改3）。
- 96来源形成252状态视图，B收益68/A损害13/N中性171；45来源随当前状态变化而改变标签。未来教师程序与正确性标签不进入预测输入。
- 从旧37 HF适配器继续训练，原样保留121来源/195目标回放；2轮计划434更新/894前向。源码[finqa_acquisition_learning.py](finqa_acquisition_learning.py)。
- 现有父4100174/21736071、训练子4100300/21736480。完成后自动做64次实际HF效用前向，按P(B)-P(A)冻结最多18个正收益接管任务，然后恢复27B。
- 预测完成后运行evaluate，用已授权校内Key的隐藏输入启动完整OpenCode教师执行；原始快照、单位保护与训练定义一致。Key仅进程内。HF前向/本地训练/教师POST分别计费，不称零模型计算。

## 已闭合证据：不重复

- 普通33/64、旧成对37/64；53一次确认均30。121组扩样普通33/成对34，首分叉margin/mask扫参停止。[历史](results/FINQA_CORRECTION_LEARNING.md#teacher-formation-expansion-v3)
- 四算子首版与独立提案/采纳均33全KEEP；三版角色头、新校内路由均无增量。保留30个成功补丁、296个已执行子集和局部正确动作，进入当前状态视图。[已闭合](results/FINQA_CORRECTION_LEARNING.md#proposal-acceptance-v1)
- 原27B路由36，18调用；同预算错误风险/固定随机也36。新相对旧37的BGE路由35，恢复1/错改3，停止；不继续改阈值。
- 匿名候选比较TRAIN16从9到10，恢复5/错改4，未到预设11，未启用其DEV臂。完整DeepSeek与旧37的DEV互补上限44；简单尺度保护缓存回放43，属于强规则参照，不能写成学习结果。[本批](results/FINQA_CORRECTION_LEARNING.md#shared-teacher-value-v1)

## 判断与边界

一个候选先真实出分，对缓存33/37及同预算简单策略。净增至少3题后补齐对照；复用旧37本身的增量不算新贡献，需要新增修复或有意义的成本改善。不要求所有任务领先；12月中旬按机制、确认效果和成本判断IJCNN条件。

原64开发/53一次确认均已用；另64个公司年份来源仍RESERVED_NOT_EXECUTED，严禁入形成/训练。DEV教师输出不转TRAIN。[预约](results/FINQA_CORRECTION_LEARNING.md#project-filing-reservation-v2)

单GPU、32GiB保护；不扩编译器/调度/治理，不制包、不逐文件核SHA，不并行全套消融。原始失败保留，状态只维护当前答案。正向与死因按[机制知识](results/CONTINUATION_PROGRAM.md#mechanism-knowledge)和[近邻](IJCNN_RELATED_WORK_REFRESH_20261030.md)按需加载。

## 成本与运行

已结算本地5,686POST/23,910,452＋12未知393,216；校内5,692POST/54,073,554＋11未知2,883,584，含预留56,957,138/10亿，TAT不变。本批新增本地126POST/505,126、校内182POST/858,816，新增未知0。新训练进度见TRAIN_LIVE，不把434计划写成完成。[账本](results/FINQA_CORRECTION_LEARNING.md#finqa-costs)

完整教师原始wire留GB10，短回执及代码同步本机/GitHub；其他对话WIP保留。现有训练不重启，观察超时先核原PID；父流程在训练/预测子进程退出后恢复27B。

<a id="当前优先级2026-11-04"></a>
<a id="地震与板块工作流下一组开发对照2026-11-03"></a>
<a id="工具修复反馈接入与-astropy-批次2026-11-05"></a>
<a id="与-paper-e-并行"></a>
[旧探索归档](../../docs/archive/2026-11-06_agent_research_context/README.md)。
