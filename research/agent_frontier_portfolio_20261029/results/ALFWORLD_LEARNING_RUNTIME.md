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

| 旧16题开发结果 | heat/cool/look主比较 | clean诊断 | 全部原生won |
| --- | ---: | ---: | ---: |
| Frozen F | 6/12 | 1/4 | 7/16 |
| Ordinary O | 6/12 | 1/4 | 7/16 |
| Recovery R | 7/12 | 3/4 | 10/16 |
| 普通历史all7 | 5/12 | 2/4 | 7/16 |
| 普通历史top1 | 4/12 | 2/4 | 6/16 |

R-F/O主比较差的描述区间包含0；普通历史all7与F/O成功数相同、实际token更低。旧R存在原生成功后继续请求的长尾，未来三臂统一原生终态停止；工程停止控制不能算学习贡献，旧费用不扣除。[五臂完整账和C复核](../../../docs/archive/2026-11-06_agent_research_context/alfworld_learning_through_20261108.md#five-arm-results)给出全部费用、区间与旧27B参照。

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

| 冻结输入 | SHA256 |
| --- | --- |
| `BATCH_PLAN_V2.json` | `ea4731e0b3e0c1162393350f23601f35ee57bef20f730142716f987afaec3b0c` |
| `PROTOCOL_V1.json` | `684f68b7f56091734c474069994734a300e2b8fb9933628161a401ec6a636e92` |
| `SOURCE_ISOLATION_V1.json` | `fa764abde4d35bb2d1f86a1eb91281ce2318ac40f730e255a283ed6762f0de61` |

**复核及封存。** C独立核36个原生结果、11,694条raw绑定和1,913条原SSE；所有72个owned world容器退出，原18104 Q4已恢复、锁已释放。完整raw及16份代码快照双端封存：`trained_baseline_transfer36_closed_v1_20261108.tar.gz`，90,741,393bytes/12,545文件，SHA `86b782a2f154e336ebf72fffcd33791f9e7a3a5b1e89a1a1e6f7b02879af6390`；不含模型权重或完整actor缓存。C为AI独立复核，接受上述开发性结果及边界；未重哈希完整16GB父模型。27B的登录用户/proc不可见不代表容器死亡：D另以Docker状态及1次研究health GET确认存活，无新增生成。

H结果没有改写R的基线地位：all7对F新增2题、退化2题，对R新增1题、退化5题；目标匹配与F逐题成功向量相同。普通历史解释不了R的全部开发优势，但R仍是已有纠正配方，不能据此宣布新机制。停止追加普通SFT变体，下一步做组合效用识别。

**普通历史资产。** 旧16题共用同一份7条普通教师成功轨迹，heat4/cool2/look1，不是7条纠正。`hf_evaluation_v1/contexts/all7.txt` SHA `d19c16440cc7d7cc6d77c07248a37b7fde2a3142e28db7a68255ae0cc31a662b`，可直接复用内容。新12题仍须单独绑定pool、公开reset与共同配置；现役`experience_mode=none`拒绝该参考，旧驱动硬锁16题，不能直接替换输入或修改在途代码。

私有`ordinary_history_train12_inputs_v1/RUN_V1/RESULT.json`为`ALL18_HISTORY_RETURNED`，SHA `45d7351f3b070bc30e65eb352fbcaba651d24fdc72fdda9f83e20b6b4094663a`。C独立核18槽、766条原SSE及4,702项绑定，无结果阻断；原Q4恢复身份与锁释放已核。PID2349435已退出，不重启。先前V2在模型调用前因D漏绑计划文件被拒绝，0模型/HTTP/world，旧release/日志保留。

双端封存`history18_closed_v1_20261109.tar.gz`：38,570,450bytes/5,083文件/16份代码快照，SHA `e44cec93720f73ede013fa7eb535a8e92e19f965a3b63df372511dcae7e08ae0`；复用F证据依赖上面的36槽包，不重抄或重计。源权重、actor缓存及生产数据不在包内。

**下一机制识别。** look6已有00=F、10=单look轨迹A、11=all7；经验块外的题面、公开状态和真实首请求全部一致。A在all7字节`[9881,10689)`恰出现一次，补01=B（其余六轨迹）即可形成四格。`COMPONENT_INPUTS_V1/reference_B.txt` SHA `69d22b795c361c52683a293b4eb0c772a0ca1526e4aca845724205dc72af91bd`，协议SHA `77c04adf4224f3c9c098c387385f482f369ab4ef95f713b85ecc914af9d8aa23`；6新槽/768POST仅候选，尚未释放。只测试reset下再暴露组合效用，不称动态撤回或独立确认；学习设计见[研究组合](../AGENT_FRONTIER_RESEARCH_PORTFOLIO.md#可检验的机制方向)。

## 来源形成成本：已复算组件

由训练行追到原receipt，375份SSE及2份技能响应重算相符；all7的BANK、源组和receipt与O的7条来源逐一一致。

| 已用来源组件 | 历史POST | provider input+output tokens |
| --- | ---: | ---: |
| H/all7与O共用的7次普通教师成功执行 | 75 | 500,683 |
| R的7次学生失败前缀 | 202 | 2,295,467 |
| R的7次教师纠正接续 | 80 | 543,819 |
| R上游heat_1/clean_1成功执行及技能形成 | 20 | 113,981 |

R已用来源链合计302 POST/2,953,267 tokens，筛选/转换/训练等费用分列，非方法总成本。H与O各按策略计形成费，项目事件账只记一次共享事件；未知cache保留null，不把跨模型token当等价计算。此次历史回算无新模型调用。私有`D_SELECTED_SOURCE_COSTS_V4.json` SHA `374b4b5ae1dd5e7494c8f007ce7d9614d86bb2cc4e6b4e0db29c02ac344275a8`；未选中尝试及研发账另列。

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
