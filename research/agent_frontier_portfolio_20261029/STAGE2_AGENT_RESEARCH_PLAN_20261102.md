# 第二阶段：反馈条件化的可复用纠正技能学习

> 2026-11-14。[完整片段](results/CONTINUATION_PROGRAM.md#fragment-transfer-v1)形成闭合，2条新故障任务×4策略原生比较运行中；本轮先裁决真实任务与总成本，不再追加源内writer。

## 目标与已有资产

从真实执行反馈学习可复用的纠正条件、内容、参数、续行与退出，以新任务原生成功、回归及形成＋执行成本裁决。FCCL为工作名；对照用于产生监督及验证，不以审计为论文贡献。运行只用当前公开信息，隐藏状态/评分不入Actor输入。Paper E/开题由独立对话维护。

- [已有8B训练](results/ALFWORLD_LEARNING_RUNTIME.md#trained-baselines)：R/O/F为8/12、6/12、4/12，R多2题未丢题，较O少36.93%执行tokens；改善集中look，clean同2/6。保留适配器和监督，不从零重训。
- [Astropy历史](results/ASTROPY_ISOLATED_CONTROLS_20261106.md)同成功下少45.31%执行tokens；[同现场复用](results/CONTINUATION_PROGRAM.md#prefix-v1)少43.14%，回跳再少7.31%。这些条件收益和普通历史基线均保留。
- 旧整流程接管、源内闭环及旧四组已完成/停止；空值先导失败费保留，不重复跑资格。完整历史按[归因入口](results/CONTINUATION_PROGRAM.md#cross-batch-autopsy)加载。

## 最新判断

[前五组](results/CONTINUATION_PROGRAM.md#feedback-transfer-v1)修订程序2/2、执行tokens较Actor少20.69%；[时点重复](results/CONTINUATION_PROGRAM.md#deployment-timing-v1)未识别新增保护收益，但题1前置复用两次成功、较post少24.16%。保留条件收益，不作全局最优。

[绑定形成](results/CONTINUATION_PROGRAM.md#binding-update-v1)保留互补修复，独立一致性配方已停止。[完整片段形成](results/CONTINUATION_PROGRAM.md#fragment-transfer-v1)再用1请求/42,472tokens，修订取价—报价—确认—执行过程：原自动候选覆盖8/10阶段，共享手写关联后9/10，强简单流程10/10。8项隔离检查通过；这不是原生任务结果，也未识别独立学习规则增益。

现用技能K=(B_fixed,G_learned,A)：B是双方同一手写实体关联，G由实际纠正段及公共前提修订，A保留实际工具操作。只把G的修订称学得，不把预处理冒充学习。ENV成功末端不等于可立即执行；剩余cost关键词把免费漫游误认作已报价而yield，保留这一覆盖缺口，不要求完美才做开发实验。

## 唯一下一交付

1. **接续原生八组，严禁重复启动。** GB10 fragment_transfer_v1，PID186354/start_ticks1715374/会话8416；RUN_HANDLE含boot_id。先核实际/proc及完成文件，不因观察超时重启。2条新故障族已按ID冻结，排除官方TEST及全部已计划/执行族，任务不按结果替换。
2. **四组为Actor、普通历史、强简单流程、片段。** 同模型/信息/24 Actor及72总POST、2M tokens、900秒/160步，初始冷却与未完成续一次相同；单并发，帽576POST/16M。普通完整反馈可从相同阶段材料/候选同选片段，作为策略别名而非另一独立样本，不能据此声称超过普通更新。9/10的yield、共享手写处理及基线修正均在新任务前登记。
3. **按行为和全成本归因。** 原生成功、目标分项、报价/确认/实际操作、自动介入数及Actor/User全部请求和费用分报；旧源费用不隐去，形成42,472单列。ENV目标达成而会话未终止仍留原生失败；中性处替代行为不补造正负结果。核每组最终mode/冻结文件，避免把条件漂移算方法收益。
4. **裁决后只推进有价值的分支。** 若强简单/普通历史同效更省，停当前配方，不追加同题writer；保留可用子修复和失败。出现条件收益先辨别绑定、阶段或材料读取差异，再扩至少两项目、4—6独立任务、来源隔离留出及匹配[近邻](IJCNN_RELATED_WORK_REFRESH_20261030.md)比较。当前仍未完成这些要求，不把阶段程序/guard换名为新理论。

开发接受局部有效和有限适用范围，不追逐事后全知规则；成功率与全成本分报。已有LoRA可复用，可靠监督和机制收益明确后再决定训练。12月中旬IJCNN评估点不变。

## 成本与同步

已闭合校园**4,559请求/46,512,890已知**，10未知预留2,621,440，合49,134,330/10亿；[总账](results/FCCL_FORMATION.md#成本与证据定位)。完整片段形成1请求/42,472已计入，0训练；原生在跑费用另记，不当0或预算支出。形成40文件已双端验hash，代码/状态随main同步。cache异常、历史340-token差额和研发费用保留；LoopB/其他对话WIP不动。

<a id="当前优先级2026-11-04"></a>
<a id="地震与板块工作流下一组开发对照2026-11-03"></a>
<a id="工具修复反馈接入与-astropy-批次2026-11-05"></a>
<a id="与-paper-e-并行"></a>
[旧探索归档](../../docs/archive/2026-11-06_agent_research_context/README.md)。
