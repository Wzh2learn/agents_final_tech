# SymPy：成功经验能否迁移到后续变化任务

> 2026-11-06 | 开发比较；现役计划见[短计划](../STAGE2_AGENT_RESEARCH_PLAN_20261102.md)。本页是本对实验记录，不是新prompt或新Goal。原始源运行及计量修正见[Django批次的当日接续](DJANGO_AGGREGATION_AGENT_20261106.md#current-27b-handoff)。

## 问题与事前比较

Qwen27B已经实际修复源任务14774。现在检验：这些真实执行与反馈形成的历史、结果卡或普通skill，能否帮助8B完成后续19235任务？比较无历史、普通历史、结果卡和模型生成skill，所有目标从相同base开始，seed7202、temperature0.2、32K上下文、8192输出上限、48POST/1200秒/6MB，使用同一8B服务/隔离依赖。先固定三种经验再开始任何目标臂。

这是表示与经验利用的开发对照，信息量并不等同，不能直接解释为纯格式因果效果。普通skill与历史本身都不是新方法；后续候选还须超过最强简单策略和公开近邻。source题面直接提示修法，target引用前序PR；D已知参考，不能称跨来源、预训练隔离或独立确认。

## 已核实资产

- 数据资格：`sympy_latex_qualification_20261106/FINAL_QUALIFICATION.json` SHA `941e2cc1f44ddb77059d6feb6a51669b7e5cab39cb8456a832231b998ba974e7`。source base `8fc63c2d71752389a44367b8ef4aba8a91af6a45`，target base `226b942f0748819d5d2d723b91591fed4975961c`，时序祖先已核。
- 真实源：私有`agent_learning_20261030/sympy_latex_agent_20261106/attempts/teacher27_source_v1`；completed SHA `9d3d0e74502346202ab76bf4bef859eeb2bc8a06940ddf80a8038555e5e72a7e`。17POST、148,213 provider tokens；17响应用量完整。原题probe、focus1/1和114回归均通过。只改原有`printing/latex.py`与其测试，测试基础设施未改。
- 源历史33,614bytes，SHA `2acccd038177a67d4a7d23153cbf92699c804895ab95d5e3c54b3fb3cfb654b2`；结果卡9,171bytes，SHA `d6c0617f4e66ed3e72ee4d8f77e3b4782dba35c3b7b0a240ff0a3231831bbb53`。两者绑定实际source task、完整实际diff与独立结果；历史另含带status/error的截取动作。v2模型skill已生成，SHA `d1cf21b0af4a6e1f5eb1ac5fa408f31526454b6f622e8761d488d420933c9957`。
- 独立目标控制：`transfer_controls_20261106_v1` receipt SHA `456fea9e02d3217ec6d0b0ec5a5da2fb938c70a586171f57781e4364248f33f4`；base原题/focus失败，gold通过，两者142回归通过。原144项中的`test_issue_13559`与`test_issue_8470`均为两臂共同的Python3.8 AST问题，按原资格排除，不改口为144全过。
- actor只读指定任务、baseline、无SymPy wheel的依赖投影及选定经验；隐藏测试、参考patch与evaluator不进入actor。目标评测在独立副本恢复原有嵌套tests和配置，再应用隐藏测试；原题语义probe另核。

执行器：[源](../run_sympy_latex_agent_20261106.py)、[经验与目标](../run_sympy_latex_transfer_20261106.py)。当前私有经验目录`.../sympy_latex_agent_20261106/source_experience_v2`，v1保留原始接口失败；目标目录`.../transfer_attempts/<attempt-id>`。以各自manifest、raw、请求/响应及回执为准，不覆盖旧输出。

## 源冻结与接口资格

首个v1写入请求实际HTTP200/finish=stop、14,992tokens，却由provider将606字符文本放进`message.reasoning`，final content为空。它是通道资格失败，不是截断或方法负结果；原6个文件原样保留，没有将reasoning挪成答案。

新`source_experience_v2`的历史/卡与v1字节一致，仅在模型请求明确增加`chat_template_kwargs={enable_thinking:false}`。新请求同为14,992tokens，final content正常，获得上述skill。研发实际形成成本为2POST/29,984tokens，正常配置单次为1POST/14,992tokens；两种口径分开。source采集与这两次形成的已知总计19POST/178,197tokens，不把响应usage与公开步骤再相加。

三种载体已在任何目标准备/执行前冻结，manifest SHA `bf870b8188ed274d1350b59d6a9cc40095756a75a44211c3adb846849be2892a`。CLI所有步骤显式使用`--experience-id source_experience_v2`，目标manifest和回执也绑定该ID，错用v1会被拒绝。所有目标原题保持字节级前缀，并给同一条已知Python3.8 baseline失败说明；这些失败在评分器和actor侧采用一致边界，不给隐藏答案。

## 判定与成本

主要结果要求原题语义、focus和142项适用回归同时通过；agent正常退出或自称完成不替代验收。未运行、语法/接口失败、未读取经验分别记录。观察实际经验读取，不把读取直接当作语义使用。

成本保留按模型区分的请求、provider tokens、缓存及实际用时；provider和公开步骤的同一用量不相加。目标边际成本与完整冷启动成本分列：冷启动经验臂计入17次源采集，skill额外计其形成请求；已有源经验情形只比较各载体新增形成与目标成本。来源共享物理账本只记一次。Django与源采集曾共享GPU，不用这部分wall time主张延迟优势；目标臂串行，若出现成本信号，再重复顺序/seed验证。

## 后续分支

- 某种经验有成功率增量：先复核具体行为与普通历史/卡的作用，再做内容消融、重复和另一项目，不能以单任务认证方法。
- 全部成功、只有成本差：核对缓存、读取与形成成本后复验；普通历史若已解释收益，保留其为强基线。
- 全部失败：区分小模型能力、任务参考、工具接口与经验适用性，必要时用较强模型作诊断，不外推经验学习无效。

## 四臂实际结果与尸检

四臂均已执行，本次单个目标没有一臂达到原题/focus/142回归联合要求。以下是四个条件的一次开发运行，不是四个独立任务样本。

| 条件 | POST / 已知provider tokens | 实际产物与失败链 |
| --- | --- | --- |
| none | 48 / 667,145 | 19次grep、26次read、唯一编辑失败；源码净diff为0，48POST门终止，原问题仍在。142回归通过。 |
| source_history | 29 / 437,652 | 改坏源码缩进，导入阶段失败，未收集到测试。actor覆写测试，但独立评分已恢复原测试/配置，仍由源码IndentationError失败。 |
| feedback_card | 6 / 46,762＋1请求usage未知 | 新增未注册打印配置键；实际回归137失败、5通过，142项全部执行，不能将“通过数5”写成“仅执行5项”。第6请求参数流未完成后超时，接口故障另列。 |
| generated_skill | 10 / 94,266 | 编辑产生`'acosh''`语法错误；实际调用`npm test`失败并询问是否运行pytest，正常退出不替代完成。 |

最重要的观察是三个经验臂均没有将经验正文读入。实际read返回为history 0/330行、card 0/202行、skill 0/4行，29/6/10份已捕获请求正文也没有各自载体正文。首轮用户指令明确要求读`/root/source_experience.md`，但模型未照做；不是经验文件不存在。独立只读尸检与completed内`experience_read`一致。控制器打印的`experience_read_observation=null`用了另一个字段名，不作为读取证据。

因此本轮是“文件可供读取＋加载提醒”的端到端负结果，不支持三种经验内容的效用比较，也不把源码损坏归因于已读经验的负迁移。独立评分恢复测试与配置的措施阻止了删测试造成假通过。下一步只做两个诊断：同一冻结skill显式进入8B首轮上下文，以及27B无历史能力控制；分别核对实际请求、有效编辑和完整语义结果，再决定是否开展新比较。

目标共93POST、1,245,825已知provider tokens＋1请求usage未知；加源采集与两次形成后的研发共112POST、1,424,022已知tokens＋该未知请求。缓存是其中子集，不再相加；同源账本只记一次。完整冷启动与既有经验的使用成本仍须按臂分列，失败臂较少POST不构成有效率优势。

证据：私有`cohort_v2/RESULTS.jsonl`及各`transfer_attempts/target_*_v2`的raw/请求/独立评分；双端选定包`.../evidence_packets_20261106/sympy_frozen_four_arm_target_evidence_thin_20261106.tar.gz`，SHA `f90b1814e04243cb0cda259f25ef793c2ca60f60e16c5da614880e6ff20a15f8`，511成员逐项核验。旧manifest和输出不重写，全局方法贡献仍未成立。

## 加载与能力的两项诊断

沿用同一source manifest，先冻结两份独立新attempt，再串行执行；不是重新定义旧四臂，也不是独立确认。27B-none使用原生`enable_thinking=false`；8B-inline将同一冻结skill的607bytes直接送入首轮user上下文，不再要求它先读经验文件。源内容、目标题面/回归与seed均不改，实际转发body还要核对。

| attempt | inputs manifest SHA-256 |
| --- | --- |
| `target_none_teacher27b_file_diag_v1` | `71d7d6a8c4ec192421a559536637143d7045f689d20b363852eeaf747cf99d16` |
| `target_generated_skill_student8b_inline_diag_v1` | `cc1eba6f22c01ab6a656bfd7d4fdb1591656fff93a1110a4c41d9d5b33889016` |

代码SHA `f525d28da37ed15881686fd6d638f0c623175f4dcadf02c55eab8e65d8f29c60`；20项远端tests/24subtests通过，包括默认8B/file派生字节兼容、backend/delivery错配拒绝及实际首轮内容。两项真实运行均已结束，原题未修、142回归通过，源码均未改动：

- 27B-none：48POST、848,959tokens，usage完整；11read/34bash/2grep，重复打印原行为直到POST门终止。completed SHA `185d76de4555b5791d00ab59b31cf3ba151100970ae0f8a0ccea651a3e0ef5b5`。这说明仅换更强模型的默认不推理配置仍未解决本题，不是所有27B模式的能力上界。
- 8B-inline：607bytes确在首个实际user请求中，body SHA `641c831a442d2e33bfb010d36b6c7c53bdc17f20603a0d1d5563c6bf6e263c63`；5POST、19,977已知tokens。两次2000行read后，模型端明确拒绝48,522tokens请求，超过32,768上下文；随后退出ContextOverflowError，不能作为skill语义负结果。`00003`为已知上下文拒绝，但无provider usage，仍单列而不补零。completed SHA `cd9324bd2a1ec31c8fd2588f42344d4530c1344fcc0bf92cca73c21a051fc2c3`。

终态在私有`loading_capacity_diagnostics_v1/RESULTS.jsonl`。新诊断实际53POST、868,936已知tokens＋1个拒绝请求无usage；不与同一provider的公开步骤重复相加。当前暂停扩展这个SymPy执行配置；如重启，先显式控制读取/上下文和推理模式。主攻转向已有真实成功及新开发池的ALFWorld，不让单个代码任务阻塞经验研究。
