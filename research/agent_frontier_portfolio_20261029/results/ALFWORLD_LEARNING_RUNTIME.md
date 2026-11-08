# 已训练8B基线：复用入口

> 2026-11-08 | 本页索引复用资产与当前批次，下一动作见[短计划](../STAGE2_AGENT_RESEARCH_PLAN_20261102.md)。训练、部署及旧五臂过程已[归档](../../../docs/archive/2026-11-06_agent_research_context/alfworld_learning_through_20261108.md)。

<a id="trained-baselines"></a>
## 当前复用：同BF16父模型的 frozen / ordinary / recovery

O/R均已真实训练、保存重载、转为GGUF LoRA并实际推理，现成资产可直接比较新布局，不需要先增加训练。私有根`learning_comparison_v1/`在GB10证据目录，具体加载前重新核对实际文件与自有进程。

| 资产 | 相对私有根路径 | SHA256 |
| --- | --- | --- |
| 共同BF16父模型 | `gguf_conversion_v1/hf_parent_bf16_v1/Qwen3-8B-HF-BOUND-BF16.gguf` | `505618debb4e6ff112a8724f22853f09d4a6dd7ba0e32123d404fe9a4da8f5e3` |
| 普通训练 O | `gguf_conversion_v1/ordinary_v4/ordinary_v4.gguf` | `deaf4b1618cdc3664dab92d798c375f36ae2e9e6c87e787e9118277fa2bb805f` |
| 纠正训练 R | `gguf_conversion_v1/recovery_v4/recovery_v4.gguf` | `560a86bd66d11fd2186a9ddff0130b8c4bc37a1fb148623a6faea831cc4b34ba` |
| HF父权重绑定 | `HF8B_MODEL_BINDING_V1.json` | `b8d5af477c1f6be67981583a4a60df9561ea53872e0676535aa9745fce011dc1` |

两个约15MB的GGUF是适配器，不能单独充当完整模型。旧默认Q4未证实与HF LoRA坐标兼容，不能代替共同BF16 frozen。

<a id="实际训练表示复核2026-11-07"></a>
## 训练和旧成绩：可引用到哪里

同HF8B、seed17、q/v LoRA r8/alpha16/dropout0、lr2e-4、batch1，两臂各192更新；O为1,135,199序列/8,239监督tokens，R为1,135,273/8,378。实际135个唯一行中O为67行、R为68行，来自相同7组；只监督当前助手动作与EOS。可称同父模型/初始化/更新数，不能称完全等训练量。R来自失败前缀的教师接续，O从reset形成，比较的是配方整体，不是孤立反馈因果。

| 旧16题开发结果 | heat/cool/look主比较 | clean诊断 | 全部原生won |
| --- | ---: | ---: | ---: |
| Frozen F | 6/12 | 1/4 | 7/16 |
| Ordinary O | 6/12 | 1/4 | 7/16 |
| Recovery R | 7/12 | 3/4 | 10/16 |
| 普通历史all7 | 5/12 | 2/4 | 7/16 |
| 普通历史top1 | 4/12 | 2/4 | 6/16 |

R-F/O主比较差的描述区间包含0；普通历史all7与F/O成功数相同、实际token更低。旧R存在原生成功后继续请求的长尾，未来三臂统一原生终态停止；工程停止控制不能算学习贡献，旧费用不扣除。[五臂完整账和C复核](../../../docs/archive/2026-11-06_agent_research_context/alfworld_learning_through_20261108.md#five-arm-results)给出全部费用、区间与旧27B参照。

## 新布局比较：36槽输入已冻结，实际运行中

本轮从本机已核私有包重新提取原POOL与训练来源：7组为heat4/cool2/look1/clean0，对新train12的task UID、family、layout、layout_group、game hash交集均为0。仍共享look类型、同benchmark且属于D已曝光TRAIN，不是独立确认；6个look报告同类型布局迁移，6个clean报告未训练类型诊断，all12仅次级汇总。

使用现役`ordinary_reset/student8b --runtime-profile <path> --runtime-profile-sha <sha>`，三臂统一reset提示、无经验、world/模型seed、解码、终态停止、历史窗口和预算。frozen也必须显式绑定BF16 profile，否则会落回默认Q4。每臂新自有进程、admission、O/R唯一LoRA且scale1；旧PID只作历史，不作当前归属证明。

旧HF驱动锁定16题/五臂，不能直接替换池执行；复用其有限生命周期和恢复原语。`ordinary_reset`读取`total_caps`，旧HF为128POST/1800秒/100动作/64M收发bytes，来源采集96/900是另一合同。先冻结任务清单、共同设置与实际恢复身份，再进入新批次，不再围绕已闭合heat_2追加接口分支。

私有根`next_train_source_v1/trained_baseline_transfer_v1/`已冻结全部12题×F/O/R共36槽，最多4,608转发POST；每臂按池原顺序，首4题只查接口/计量，不按输赢缩样、换题或改帽。world/model seed17、temperature0.2、thinking=false、32K/8192、full历史、native停止及最多一次普通续做全臂相同。正常非won和已证预算封帽保留；超时/137/不明错误/未知总usage/清理不闭合停队，不自动重跑。

| 冻结输入 | SHA256 |
| --- | --- |
| `BATCH_PLAN_V2.json` | `ea4731e0b3e0c1162393350f23601f35ee57bef20f730142716f987afaec3b0c` |
| `PROTOCOL_V1.json` | `684f68b7f56091734c474069994734a300e2b8fb9933628161a401ec6a636e92` |
| `SOURCE_ISOLATION_V1.json` | `fa764abde4d35bb2d1f86a1eb91281ce2318ac40f730e255a283ed6762f0de61` |

V1草案有一项Windows CRLF代码摘要，V2改按Git blob并保留运输映射，当时尚无模型运行。C只读复核36槽、同条件、来源和判读范围，未发现科学输入矛盾。GB10完整`study.protocol`及代码hash/36个新root不存在检查通过；该纯读取阶段模型/world/HTTP为0。本机完整parser的旧依赖字节失败仍保留，不冒充Linux准入。

**裁决边界。** R训练于失败前缀接续，from-reset只测配方迁移，不单独识别反馈因果；负结果不否定其恢复用途。学习优越性裁决前补同12题Frozen＋普通history_all7：Frozen复用本批合格闭合结果；在途期间只准备all7输入，待本批闭合、释放模型锁后另冻有限执行，禁止重复启动Frozen或占用当前窗口。旧16题不能替代。

**普通历史资产。** 旧16题共用同一份7条普通教师成功轨迹，heat4/cool2/look1，不是7条纠正。`hf_evaluation_v1/contexts/all7.txt` SHA `d19c16440cc7d7cc6d77c07248a37b7fde2a3142e28db7a68255ae0cc31a662b`，可直接复用内容。新12题仍须单独绑定pool、公开reset与共同配置；现役`experience_mode=none`拒绝该参考，旧驱动硬锁16题，不能直接替换输入或修改在途代码。

私有`ordinary_history_train12_inputs_v1/`已准备原POOL与all7。`reference_only`候选补丁SHA `705a90bb94f3630a6c7a8681916ae114ae652b327a9e8c92fdd007694fae0e04`通过本机Python3.12的32项合成CPU控制与patch check，**未应用、未运行历史臂、未做Linux集成**。闭合后由D集成、核真实输入并释放有限批次；旧null-assignment模板仍是阻断草稿。

**真实执行中。** operator SHA `83fa07e1af89197307b11c7b529b410af23cc23fc47d2a9caa05a06fe78b5b2f`；release SHA `b3823c72efd7c4eb00334ff2cddc03367ff576bcc2e81a05d1cf74c72bd0138b`。16组件、原8B身份、共享进程及锁已核，当前进度查`RUN_V1/STATE.json`，最终须`RESULT.json`和raw闭合。SSE、world归属、取消与写盘失败控制的C/D证据留在本批私有目录；旧代码与测试退出码边界保留。

**第一臂闭合观察。** Frozen为look **4/6**、clean **0/6**，共748 POST；O/R未齐，尚不能裁决训练。clean6的476条完成工具调用中220次返回公共世界状态、256次为非法动作；248次非法集中在两题，另一类失败包含目标物体错绑。该后验诊断不构成因果解释。私有`D_CLEAN_FROZEN_AUTOPSY_V1.json` SHA `be9eeb756d2cf29c3d48d7094bc100f86e565de74d3c628c111a17641c132641`。

## 来源形成成本：已复算组件

由训练行追到原receipt及SSE，357份响应逐条重算相符；all7的BANK、源组和receipt也与O的7条来源逐一一致。

| 已用来源组件 | 历史POST | provider input+output tokens |
| --- | ---: | ---: |
| H/all7与O共用的7次普通教师成功执行 | 75 | 500,683 |
| R的7次学生失败前缀 | 202 | 2,295,467 |
| R的7次教师纠正接续 | 80 | 543,819 |

R上述来源组件合计282 POST/2,839,286 tokens，尚须并入祖先carrier、筛选、训练等费用；不是方法总成本。H与O按方法分别计形成费，项目事件总账只记一次共享事件。cache未知仍为null，不把不同模型的token当等价计算。此次仅历史回算，新增模型调用0。私有`D_SELECTED_SOURCE_COSTS_V3.json` SHA `b555af7517dc7d44f7bd09f5b11c5fa87346268941c8a7d9cf7224c39652ff02`；全项目与研发Agent未知账保持。

## 历史记录按需读

<a id="learning-runtime-history"></a>
- [训练全过程与表示核查](../../../docs/archive/2026-11-06_agent_research_context/alfworld_learning_through_20261108.md#已闭合同来源两臂真实训练)。
<a id="deployment-bindings"></a>
- [共同父模型、转换与部署](../../../docs/archive/2026-11-06_agent_research_context/alfworld_learning_through_20261108.md#deployment-bindings)。
<a id="private-packets"></a>
- [闭合私有镜像](../../../docs/archive/2026-11-06_agent_research_context/alfworld_learning_through_20261108.md#private-packets)。
<a id="terminal-retry-20261107"></a>
- [终态重试修复](../../../docs/archive/2026-11-06_agent_research_context/alfworld_learning_through_20261108.md#terminal-retry-20261107)。
<a id="five-arm-results"></a>
- [旧五臂结果与成本](../../../docs/archive/2026-11-06_agent_research_context/alfworld_learning_through_20261108.md#five-arm-results)。
<a id="code-source-controls"></a>
- [早期代码来源与接口](../../../docs/archive/2026-11-06_agent_research_context/alfworld_learning_through_20261108.md#code-source-controls)。当前代码纠正查[现役代码记录](CODE_SOURCE_CORRECTIONS.md#current)。
<a id="sympy-intersection"></a>
- [SymPy集合语义公开复现](../../../docs/archive/2026-11-06_agent_research_context/alfworld_learning_through_20261108.md#sympy-intersection)：16988→16953只是开发候选，目标语义及完整回归未形成Agent方法比较，不为其另建runner。
