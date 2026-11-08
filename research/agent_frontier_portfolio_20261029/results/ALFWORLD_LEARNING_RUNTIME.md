# 已训练8B基线：复用入口

> 2026-11-09 | 本页索引复用资产与当前批次，下一动作见[短计划](../STAGE2_AGENT_RESEARCH_PLAN_20261102.md)。训练、部署及旧五臂过程已[归档](../../../docs/archive/2026-11-06_agent_research_context/alfworld_learning_through_20261108.md)。

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

同HF8B、seed17、q/v LoRA r8/alpha16/dropout0、lr2e-4、batch1，两臂各192更新；O为1,135,199序列/8,239监督tokens，R为1,135,273/8,378。实际135个唯一行中O为67行、R为68行，来自相同7组；只监督当前助手动作与EOS。同父模型/初始化/更新数，非完全等训练量；训练wall为O 1,579.4秒、R 1,600.1秒，共享GPU，不能写成GPU秒。R是失败前缀接续，O从reset形成，只比较配方整体。

旧16题F/O/R/all7/top1为7/7/10/7/6个won；完整分型和费用见下方归档链接。训练行尸检：look的O/R唯一动作行3/2、实际更新均28、监督tokens 1,225/1,246，R并非用了更多look动作或更新；上下文和监督内容仍不同。私有`TRAINING_REPRESENTATION_CENSUS_V1.json`双端留存。

旧R-F/O主比较差的区间含0；新批已统一原生终态停止，旧长尾费用不扣除。[旧五臂完整账](../../../docs/archive/2026-11-06_agent_research_context/alfworld_learning_through_20261108.md#five-arm-results)保留区间、成本及27B参照。

## 新布局比较：36槽闭合，纠正训练保留为强基线

7条直接监督任务为heat4/cool2/look1，无clean目标；与新12题的UID、family、layout、layout_group、game hash交集均0。R形成链另用过heat_1/clean_1经验，两祖先与新12题的UID/family/layout/game hash也均无重叠（私有D_UPSTREAM_SOURCE_SCOPE_V1）。clean只称监督目标类型留出，不能称整个形成链没见过clean。同benchmark、D已曝光TRAIN；look6主比较、clean6诊断、all12次级，非独立确认。

私有根`next_train_source_v1/trained_baseline_transfer_v1/`的`RUN_V1/RESULT.json`状态为`ALL36_TRANSFER_RETURNED`，SHA `aa48994ebe77ce3b616038a1f482891d00ba72a6fab6a0b8974127b9de9c551c`。36槽均闭合，无未解释usage或未运行项。三臂显式绑定共同BF16父模型、O/R唯一LoRA且scale1；统一reset、无经验、seed17、temperature0.2、thinking=false、32K/8192、full历史、原生终态停止及最多一次普通续做。每槽128POST/1800秒/100动作/64,000,000收发bytes，旧默认Q4不作frozen替身。

| 臂 | look主比较 | clean诊断 | 全部原生won | 策略POST | input+output tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| Frozen F | 4/6 | 0/6 | 4/12 | 748 | 9,003,145 |
| Ordinary O | 4/6 | 2/6 | 6/12 | 732 | 8,192,852 |
| Recovery R | 6/6 | 2/6 | 8/12 | 433 | 5,166,975 |
| all7历史 | 3/6 | 1/6 | 4/12 | 479 | 7,343,138 |
| 目标类型匹配 | 4/6 | 0/6 | 4/12 | 287新＋478复用 | 8,963,091（含复用） |

原F/O/R36槽为1,913 POST、input 22,280,136、output 82,836，cache 21,849,417为input子集。R对O两题增益、零损失，对F四题增益、零损失；F/O在look成功身份互换，R覆盖二者成功并集。新增H18为766 POST、input 10,624,832、output 32,740、合计10,657,572，cache 10,380,370仍为子集。目标匹配策略账含旧F clean6的478 POST/5,648,657 tokens，不重复计入新增支出。均为单seed曝光开发，未识别反馈因果或独立方法。

冻结批次计划、协议和来源隔离表随下方36槽包保存；其原始hash以包内manifest为准。

**封存。** C核36个原生结果、11,694绑定及1,913 SSE；72个world容器退出，Q4恢复/解锁。双端`trained_baseline_transfer36_closed_v1_20261108.tar.gz`为90,741,393bytes/12,545文件/16份代码快照，SHA `86b782a2f154e336ebf72fffcd33791f9e7a3a5b1e89a1a1e6f7b02879af6390`。不含权重/actor缓存；C未重哈希16GB模型，D另以Docker及1次health GET核27B存活。

all7对F新增2题/退化2题，对R新增1题/退化5题；目标匹配与F逐题向量相同。R仍是已有配方，不追加普通SFT变体。

**历史资产。** `hf_evaluation_v1/contexts/all7.txt`为7条普通教师成功轨迹（heat4/cool2/look1），非纠正；SHA `d19c16440cc7d7cc6d77c07248a37b7fde2a3142e28db7a68255ae0cc31a662b`。复用需绑定新pool/reset/配置；`experience_mode=none`不接受参考，旧16题驱动不能换输入重跑。

私有`ordinary_history_train12_inputs_v1/RUN_V1/RESULT.json`为`ALL18_HISTORY_RETURNED`，SHA `45d7351f3b070bc30e65eb352fbcaba651d24fdc72fdda9f83e20b6b4094663a`。C核18槽、766 SSE及4,702绑定；Q4恢复/解锁。PID2349435已退出，不重启；先前零调用准入失败随包保留。

双端封存`history18_closed_v1_20261109.tar.gz`：38,570,450bytes/5,083文件/16份代码快照，SHA `e44cec93720f73ede013fa7eb535a8e92e19f965a3b63df372511dcae7e08ae0`；复用F证据依赖上面的36槽包，不重抄或重计。源权重、actor缓存及生产数据不在包内。

**四格已闭合。** A为单look轨迹，B为其余六条；all7中`[9881,10689)`恰为A。题面、公开状态及经验外首请求匹配；传输含已记录引号转义，不称原始线上字节完全相同。

| 固定mask / look6 | 逐题won向量 | 成功 |
| --- | --- | ---: |
| 00 无经验 | 0,0,1,1,1,1 | 4/6 |
| 10 A | 0,0,1,1,1,1 | 4/6 |
| 01 B（新增） | 0,0,0,1,0,1 | 2/6 |
| 11 A+B | 1,0,0,0,1,1 | 3/6 |

`I=V11−V10−V01+V00=[1,0,0,-1,1,0]`，3布局数值非零，达到开发H1；一格一次0/1并非期望交互。oracle5/6在补B前已有，不是B增益或部署成绩；R在同六题为6/6。B01/03/05各两次普通stop、0工具/动作；B02为63 POST/50动作后达context帽；不能把差异归为纯语义依赖。

新增139 POST、input 2,062,676/output 5,706、共2,068,382 tokens，cache 1,997,824为input子集，训练/judge为0。C独立核6终态、139 SSE、879绑定和首帧证明；D另核当前Q4身份、35/27及锁释放。预测卡把O误抄成A，按实际24份receipt更正，旧卡/旧裁决保留；不称前瞻确认。汇报print错误发生在内核写结果/恢复/解锁后，不重跑。初次CPU检查的源文件JSON误读为0模型失败；修后GB10为94测试/184子测通过。

私有当前裁决`COMPONENT_INPUTS_V1/D_C_CLOSEOUT_V1.json` SHA `dbe88de043a0d5cc2195dc0c3fc5dbd77859f3565d36367ced959795680afcd4`。双端包`component_probe6_closed_v1_20261109.tar.gz`为7,286,660bytes/955文件，SHA `2315574faa213c3f1f960e834d840323fb2c2c1c478b5cbf3052b290e58e04a6`；依赖上述旧36/H18包。下一步先做通道诊断，不在此六题训练联合选择器，见[短计划](../STAGE2_AGENT_RESEARCH_PLAN_20261102.md)。

## 来源形成成本：已复算组件

由训练行追到原receipt，375份SSE及2份技能响应重算相符；all7的BANK、源组和receipt与O的7条来源逐一一致。

| 已用来源组件 | 历史POST | provider input+output tokens |
| --- | ---: | ---: |
| H/all7与O共用的7次普通教师成功执行 | 75 | 500,683 |
| R的7次学生失败前缀 | 202 | 2,295,467 |
| R的7次教师纠正接续 | 80 | 543,819 |
| R上游heat_1/clean_1成功执行及技能形成 | 20 | 113,981 |

R来源链302 POST/2,953,267 tokens，非含筛选/训练的完整总成本。H/O策略计形成费，物理账共享事件只记一次；未知cache保留null，跨模型token不等价计算。私有`D_SELECTED_SOURCE_COSTS_V4.json` SHA `374b4b5ae1dd5e7494c8f007ce7d9614d86bb2cc4e6b4e0db29c02ac344275a8`。

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
