# ALFWorld执行纠正：现役采集记录

> 2026-11-07更新，批次始于11月6日 | 当前只加载本页；背景与已关闭的对照见[18任务研究](ALFWORLD_CONTEXT_STUDY.md)。目标是形成真实可执行的反馈监督，尚未训练或建立新方法贡献。

## 已完成：四现场的能力诊断

固定取三个自然未完成source（cool_01/cool_04/heat_03），加clean_02校准；后者不是新任务。补两条缺失8B drop_recent后，与27B在相同原source、公共目标/观察、最近3条accepted history及总cap比较，已有学生结果不重跑。教师不用专家动作、隐藏事实或参考计划。backend能力/实际计算不同，这不是等计算方法比较。

| 现场 | 8B won / POST | 27B won / POST | 27B新动作 / tokens |
| --- | --- | --- | --- |
| clean_02 | false / 10 | true / 16 | 15 / 128,280 |
| cool_01 | false / 12 | true / 12 | 10 / 80,968 |
| cool_04 | false / 63 | false / 47 | 46 / 681,234 |
| heat_03 | false / 71 | true / 6 | 5 / 33,449 |

27B成功恢复3/4，提供3个不同任务/布局的实际纠正候选；不是3个独立环境，也不是人工gold。成功轨迹仍须按真实tool结果、执行合法性、角色与来源检查后才能导出监督。cool_04的27B也触输入＋8192预留输出＋512余量的上下文门，不能称其任务不可解；它保留为失败和后续长轨迹分析，不混进成功监督。暂不围绕单例追加提示变体。

批次`context_study_v1/teacher_state_batch_v1/RESULT.json`为`ALL6_TEACHER_STATE_DIAGNOSTICS_RETURNED`，原PID4073951已退出。新6条共215真POST、2,863,108tokens＝2,853,227输入＋9,881输出；2条学生134 POST/1,939,177tokens，4条教师81 POST/923,931tokens。已知cached1,891,711仅来自学生输入；教师81次cache细分未知，不能填0。usage unknown为0；另3次本地预约未forward。

复用冻结独立审阅脚本的纯解析函数，逐条重读SSE/body SHA、输入绑定、原生终态和重放，四对prompt原文/caps/cohort/source相同；差异0。`TEACHER_STATES_RECOMPUTE_V1.json` SHA `1bf001d43834b4d9a691b151c7a76eca4bb74b6958c011b647d165708a4fee90`。它是确定性复算，不是新独立人工/统计审阅。

本批结束时本专题累计1,534真POST/17,447,106tokens，source形成只物理计一次；这不是项目全局账，研发Agent与更早形成/训练成本另账引用。没有新增训练、judge、付费科研API或生产写回。

两个增量私有薄包已在GB10和本机逐成员核验：`alfworld_simple_controls_v1_20261106.tar.gz`为3,080成员，SHA `7edfbc4635a5f175343dddb4721f6182e4efcb473c661cf15933d2c2479669a4`；`alfworld_teacher_states_v1_20261106.tar.gz`为1,241成员，SHA `52358c539c563e3e86a16a2be29ab8135bdd9c06267d87639d543ae7dd5d3bc4`。原source依赖[背景记录](ALFWORLD_CONTEXT_STUDY.md)所列18题包；这些不是完整runtime或公开artifact，不包含在途8题。原始命名保留批次开始日期，不因跨午夜改名。

## 已完成：原十二个失败现场的固定教师对照

八题扩展批已全部返回：look_01、cool_02、heat_02、heat_04、heat_05成功，look_02、cool_03、look_04失败；270真POST、2,893,399tokens。与前四题合计，27B recent恢复8/12，共351 POST、3,817,330tokens；本专题总计1,804 POST、20,340,505tokens，不是项目全局账。所有失败与形成成本保留；cool_04等上下文门不证明任务无解，look_04还包括大量被环境拒绝的动作。

`teacher_pool_expansion_v1/RESULT.json` SHA `7925d7ea2114fd392dfe843a821488c97fc8bede79d53d6e5b7716aa72d85cde`；PID4095165已退出。教师的每个现场都从原source分支，不能当作先免费尝试别臂再回滚的部署收益。

离线导出位于`context_study_v1/recovery_supervision_v2/teacher_drop_recent_complete_v1`：8个任务/布局组、83个接受动作回合；`data_manifest.json` SHA `aea83b3319a3f90f5472a28bb0ba5990a64f6e0e92c519a21a717473d76fa44b`。这是同一环境的四类任务，不是8个独立来源。全部351次教师请求（含4条失败）计入形成账；1576项输入证据未改变。`qualification_v1.json` SHA `91e1417146965d98ed52316b6398e276135b4366e472973b9ca1a10357695ef4`还检验了真实双轮失败：固定Continue、同会话、27次tool结果对齐22个实际动作，正监督为0。

导出保留真实请求/SSE、公共content与tool_calls；被拒绝动作、工具反馈与最终文字不作为正监督，失败上下文不删除。每个当前动作completion仍须按实际请求编译token标签。已验证多轮chat候选不等于可直接投入旧单completion训练器。

## 当前动作：普通成功经验与纠正经验的匹配对照

复用现有study新增`ordinary_reset`阶段：27B在相同18题从真实初始状态执行，使用与recent恢复一致的空历史/空经验提示合同；100实际动作、128 POST、1800秒总cap，普通stop未成功最多统一续做一次。无虚构失败source、不重放旧进度；与32 POST的学生collector不混称同预算。数据集按任务/布局配对，普通成功与纠正成功分开导出；交集用于匹配监督比较，全部失败仍计成本。

先发表代码、冻结队列及请求设置，再启动该批。它提供直接强模型成本基线和普通成功SFT监督，不把“有教师纠正”本身当新方法。8B HF权重已存在；CUDA空上下文探测两次OOM，暂不加载新GPU模型或改共享服务。4B继续作为支持项，不阻塞多任务数据与机制分析。

## 方法重叠与下一验证

[ACE §3](https://arxiv.org/html/2510.04618v1)已有带效用记录的条目、局部delta更新和保留历史知识；[AgentFold §3](https://arxiv.org/html/2510.24699v1)已有任务执行中的细粒度/深层上下文折叠和轨迹SFT。[STeP](https://arxiv.org/html/2505.20023v1)已有学生失败现场的教师纠正与partial masking。均已读方法正文，未复现成绩；局部改经验、继续外部进度或换LoRA都不足以构成独立贡献。

待验证的窄问题是：可见新反馈否定某条经验前提后，是否需要撤回其依赖步骤并保留仍成立的进度。先对比精确目标绑定、循环保护、等预算摘要及上述局部更新适配；当前失败轨迹并未证明这种残差。普通/纠正监督学习是能力和训练对照，不预先宣称新方法。第二环境按[短计划](../STAGE2_AGENT_RESEARCH_PLAN_20261102.md)接续；不再训练已无成功选择空间的旧四臂选择器。
