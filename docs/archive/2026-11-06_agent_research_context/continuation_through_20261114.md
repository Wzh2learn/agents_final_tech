> 历史快照：2026-11-14，来源 research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md @36b68e0d。原数值、旧状态与当时待办保留；仅相对链接重定位。现役判断见[机制知识索引](../../../research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#mechanism-knowledge)，执行状态见[短计划](../../../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)。

# 纠正技能研究：跨批次归因与可复用信号

> 2026-11-14｜[反馈交互训练与迁移](../../../research/agent_frontier_portfolio_20261029/results/FEEDBACK_INTERACTION_LEARNING.md#feedback-policy-v1)按主题加载；[R训练拆分](#feedback-residual-v2)正向信号保留；旧面板停扩。

<a id="feedback-interaction-v1"></a>
<a id="feedback-policy-v1"></a>
## 反馈交互学习已按主题分离

四格来源、四组真实训练和原生迁移见[专题记录](../../../research/agent_frontier_portfolio_20261029/results/FEEDBACK_INTERACTION_LEARNING.md#feedback-policy-v1)；原锚点保留，避免接续时整篇加载旧批次。

<a id="feedback-residual-v2"></a>
## 复用O/R训练：两条新任务检验平均与差分

旧R/O为8/12、6/12且R少36.93%执行tokens，但监督内容、上下文及数量混合，尚非纯反馈因果收益。复用同BF16父模型的O/R适配器，精确构造0.5(O+R)及R−O；通过低秩因子拼接实现有效矩阵组合，非分别相减A/B。平均与差分均rank16/scale1，0新优化、教师或父模型加载；历史形成费仍归属。CaPE/任务向量已有算术机制，本探针不主张新公式。

按未用TRAIN UID/布局和固定hash选look/clean各1；原生expert/reset两项通过，参考不入Actor。旧v1因剩余look仅1布局在运行前停止，v2报告排序故障亦发生于模型运行前，原件均保留。随后冻结新两任务和四组，不按成败换样。

OpenCode＋同8B BF16父模型，O/R/平均/差分单并发共8组；seed17、temperature0.2、context32768/output8192、thinking关闭。每组48POST/900秒/100动作/64MB通信，最多384本地POST、0校园调用；普通终答未成功统一续一次。各组同初始状态/完整任务/无经验文本，任务次序交叉，组序冻结。差分独有成功，或成功不低于最佳对照且执行tokens少≥10%则保留线索，否则停本固定系数配方，不在这些题上调参。单种子开发，后续仍缺独立条件更新、两项目、强近邻及留出验证。

| 配置 | 原生成功 | 本地请求 | 执行tokens | 非缓存输入 | 非法动作反馈 |
|---|---:|---:|---:|---:|---:|
| O普通训练 | 1/2 | 53 | 363,032 | 11,157 | 41 |
| R纠正训练 | 2/2 | 18 | 90,850 | 8,700 | 0 |
| 平均 | 2/2 | 15 | 72,938 | 7,967 | 0 |
| 差分 | 1/2 | 11 | 50,033 | 6,517 | 0 |

**尸检与裁决。** O在clean误取soapbottle，看到soapbar后41次重复非法`drop`，48POST触帽；R同样误取，却用合法`move`放回，再取/清洗/放置soapbar，12动作成功。平均少两次初始sink访问，10动作成功。差分clean仅1个真实动作，后续动作出现在普通文字中，统一续一次仍未执行；look四组都成功，O/平均相同5动作、R6、差分8。差分无独有成功且成功少一题，未过冻结门，停止本固定配方，不把提前失败的低token当收益。R训练有新任务正向信号；平均较R少19.72%执行tokens，保留开发线索。反馈、工具格式与一般模仿仍混合，合法动作规则亦须比较；不称新学习机制成立。

97本地POST/576,853tokens，input572,513/output4,340，cache538,172为input子集，非缓存input34,341；未知0，0新优化/教师/校园调用。执行墙时合363.86秒，不含历史形成/训练与启动。21检查/26子测试通过，629份raw绑定、97原始SSE用量、任务/初态及原生won全匹配。会话19322/PID297673已结束，自有18104/资源锁释放；不恢复重启前的旧服务。

私有`alfworld_text_qualification_20261106/context_study_v1/learning_comparison_v1/feedback_residual_v2`，PLAN SHA `946b22b82372e53ac048e4a126e5a0c65426aca024f209848233b7f4add68e18`，CLOSEOUT SHA `63d2987ffa272c2d899c17510406c1f3855331bf8e134401b454a199d552deca`；EXECUTION_FREEZE定位实跑代码。形成/组合/复算脚本在`fccl_learning_rederivation_v1`。972载荷包119,678,686bytes，SHA `1129eae17cbe1083b67320b8b3184b23722e34ba23c0b17624384cdb46a94b84`，双端逐项验hash。

**先排除的低成本候选。** 对已有12条部署时点结果作固定缺失模式重放：简单实际反馈选1.0成功，预测纠偏0.875，未胜过简单更新，停止该配方。8个选择场景仅来自两旧任务，不是8独立样本；0新模型/原生任务/训练。`CALIBRATED_CREDIT_REPLAY.json` SHA `bf49fe510650d317d37b9c059d6b20a688f597f4237fc525b223fa52f2fd625c`保存完整记录，不转做奖励审计论文。

<a id="fragment-continuation-v1"></a>
## 同现场续做：普通继续已足够，固定提醒未见增益

从上一批两条simple_protocol轨迹首次成功充值后、首次真实客户回复处冻结前缀，不按未来结果换现场。复用现有原生checkpoint及OpenCode入口；同一账户/设备状态、完整公开前缀、新会话和小份读取面，仅额外公共流程提醒不同。私人用户工具只用于host重建，不入Actor输入。16 Actor/48总POST、1M tokens、600秒/120原生步；两现场顺序交叉，0形成/训练。

| 策略 | 原生成功 | Actor请求 / tokens | 全角色请求 / tokens |
|---|---:|---:|---:|
| 普通继续 | 2/2 | 22 / 327,322 | 46 / 441,469 |
| 固定提醒 | 2/2 | 22 / 327,790 | 46 / 441,117 |

四臂均继续检查手机设置并达到客户要求的速度，无重复充值、人工转接或程序自动动作。提醒全角色少352tokens（0.080%）、Actor反多468，不识别提醒收益。按冻结判据停止在这两个现场开发复杂继续选择器，不再同题试提示。此前有效的报价/确认/充值片段及条件节费保留；本结果不否定纠正技能学习，也不能把相对旧整会话的恢复单独归因于删材料、新会话或压缩。每臂仅一次随机采样，属于开发诊断。

92 POST/882,586已知、未知0；四项官方ENV重放、原始usage/角色、冻结代码和检查点匹配。序列化会重置时间戳，其余全部前缀字段逐项相同；账户/设备及Actor公开历史hash均一致。2项边界测试通过。会话24546/PID235242已终止。

私有根`fccl_continuation_program_v1/fragment_continuation_v1`含PLAN、原始请求/轨迹、`CONTINUATION_AUTOPSY.json`及CLOSEOUT。399文件包1,134,344bytes双端逐项验hash，包SHA `5948298c2e972379203fe140e00db880759377239e03ef84d0c329384ff3d247`；CLOSEOUT SHA `c75d81191bddf07db8c75309ae0aa4148488d9a4ef8e616adeeccfe3455c933d`。历史前缀获取已在总账，不再计作新物理请求；额外writer及训练均0。

<a id="fragment-transfer-v1"></a>
## 完整纠正片段：两新任务八组闭合，局部修复未带来总体增益

1共享形成/42,472tokens修订取价—报价—确认—执行，原候选覆盖8/10阶段，共享手写关联后9/10，简单流程10/10；关联不冒充学得。剩余cost关键词误认免费漫游为报价而yield，作为覆盖缺口保留。8项隔离检查通过，旧有害重放0。普通完整反馈同材料/候选可同选该策略，仅作别名，没有独立更新规则收益。

full池排除21已用故障族及40官方TEST族，从66候选按ID hash选2条新故障组合；4策略/同模型、信息及caps。完整冻结协议、部分覆盖登记见[cf205ad0](https://github.com/Wzh2learn/agents_final_tech/blob/cf205ad05a8df17ff9a2b1af8531882f74f50db0/research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#fragment-transfer-v1)。两新组合仍只一个环境，不是两项目或独立确认。

| 策略 | 原生成功 | Actor请求 | Actor tokens | 全角色tokens |
|---|---:|---:|---:|---:|
| Actor | 2/2 | 42 | 590,417 | 751,952 |
| 普通历史 | 2/2 | 45 | 693,217 | 885,667 |
| 简单流程 | 1/2 | 38 | 550,115 | 675,336 |
| 学得片段 | 2/2 | 40 | 760,354 | 955,010 |

Actor/User按wire请求SHA回连账本并对齐counts。学得片段较Actor多27.00%执行tokens、较历史多7.83%；新增形成后边际997,482仍未含共同历史获取费用，完整研究成本另见总账。题1较历史少14.09%，但较Actor只少334tokens（0.083%），不是稳健收益。Actor调用少2次却输入更多；User模拟费用已含全角色列，不能只按调用数或失败组低费用称优。缓存为input子集，不作额外token或等价新算力。

**失败与开销。** 两种流程各实际自动报价/充值4次。简单题0的充值分项满足，连接/速度仍不满足；测速No Connection后转人工。学得流程2/2成功但周边Actor轨迹不同，不能把这一对结果当成学习触发的因果改善。题0学得Actor输入456,016对历史335,665，输出反少448；实际读取experience全文返回32,611字符，对照只读2,000字符及部分代码。读取面与交还后继续策略均须控制，不据此宣判纠正技能无效，也不再追加同题writer。

318 POST/3,267,965已知，未知0，8项官方ENV重放/原始usage/最终mode及冻结代码匹配。会话8416/PID186354已结束，不重启。双端包1,152文件/4,019,545bytes，SHA f652bcd90e3e69a2c7798b3805a3d0a45c52d18f7d7f1a2b775b6013bee0ee68。形成40文件包SHA 2c78c73507ffa56370fbc317425957e73e61f89b675fef733ee96c8374d2073e。下一复用既有checkpoint做同现场/同读取面的继续策略对照；HASP已有corrective context、CIPO已有部分轨迹返回/同前缀续行，摘要或分叉本身不作创新。

<a id="binding-update-v1"></a>
## 绑定修订：两类互补，独立一致性配方停止

64源见证/4条曝光轨迹：原程序漏2个正效果，自动触发修订与简单关联各补中一处；诊断组合漏0但有4项中性处未验证改动，未入自动候选池。三种选择规则同选，无独立正则增益。报价前提与回执关联是不同缺口；细节保留于冻结记录。

2 POST/85,784已知（首交付拒绝39,555仍计），0未知/训练/新原生任务；6项检查通过，普通候选不受视图资格门牵连。两响应cache异常不扣减。完整表格、实现及前提归因见[1750ee9a冻结记录](https://github.com/Wzh2learn/agents_final_tech/blob/1750ee9ad1d3605017ce35fa68633723eae9c924/research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#binding-update-v1)。双端37文件包SHA 7a2cdff535766975ed6e46b3402ff1b3c9904341d26c6b9a1f390ca6304dc5d9。

<a id="deployment-timing-v1"></a>
## 部署时点12组：保留条件收益，停止扩跑

同一程序仅变等长常量，2曝光题×pre/post/both×2重复。pre/post/both成功3/4、4/4、4/4；tokens 1,232,342/1,781,850/1,569,751；POST 124/152/156。题1 pre两次成功且少24.16%tokens；both较post少11.90%tokens，却多4POST及7.84%轨迹时间，非全局最优。4次介入均为提议前充值，新增保护未触发。

首both漏接明确请求；pre失败已充值却漏查飞行模式，回执绑定亦缺失；两个0介入post因读取面/调用差别相差344,997tokens，不是时点的孤立因果作用。432请求/4,583,943全部核验、0形成/训练。完整表、归因及包hash见[db9f9be9](https://github.com/Wzh2learn/agents_final_tech/blob/db9f9be9aa1e37f8b2fa9245640511065d5c82cc/research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#deployment-timing-v1)，该冻结记录保留全部旧细节。

<a id="feedback-transfer-v1"></a>
## 新任务五组：成功保留与执行成本信号

从full任务池按既有hash顺序选两条未曝光的三故障组合：飞行模式＋额度＋境外漫游；VPN＋省流＋额度。排除所有已计划/执行的故障族及官方TEST族，未消费TEST。先冻结代码和ID，再开任务正文；host原生base/reference均0/1，只是评分完整性检查，不计Agent成功。

实际五组为基础Agent、普通历史、收据额度规则、原兼容更新、自动反馈更新。非冷启动组获得相同完整来源、代码执行反馈及共同候选池。post-only简单参考与自动反馈更新选中相同程序/输入，作为同策略参照，不另算独立样本或HASP复现。

复用原carrier、OpenCode `915ca1cd`与校内DeepSeek；每组24 Actor/72总POST、2M tokens、900秒、160原生步，普通终答未成功统一续一次；顺序冻结、seed不可控。10组完成，398 POST/4,034,182已知tokens、未知0；10项原生重放匹配，代码/策略无变更。下表为执行tokens，未混入形成成本。

| 策略 | 题0 / 题1 tokens | 原生成功 | 合计tokens / POST |
|---|---:|---:|---:|
| 基础Agent | 436,549 / 401,083 | 2/2 | 837,632 / 87 |
| 普通历史 | 420,712 / 456,481 | 2/2 | 877,193 / 84 |
| 收据额度规则 | 491,472 / 442,195 | 1/2 | 933,667 / 84 |
| 原兼容更新 | 292,925 / 428,459 | 2/2 | 721,384 / 73 |
| 自动反馈更新 | 366,266 / 298,040 | 2/2 | 664,306 / 70 |

**可保留的收益：**本次自动更新执行量较Actor少20.69%、历史少24.27%、原程序少7.91%；题0反而较原程序贵25.04%。三个自动动作均获环境接受：题0开启漫游、充值，题1充值。它们全部发生在无pending Actor提议时；新修订的重复充值保护未触发，故上述7.91%不能归因于该保护。两题各一次、完整轨迹不同，仍需重复和部署时点消融。

**失败中有效的部分：**题0规则组Actor24触帽、原生0；独立ENV重放显示网络、速度、充值三项目标全满足。保留原生0及费用，将“目标已达而会话超额未结束”单列。规则两题均无自动动作，不能把该组表现解释成规则自动纠正的效果。

本批0新形成/训练；复用的普通＋自动提案41,880已知tokens另列，两题修订形成＋执行边际706,186，不含共同历史来源/早期搜索失败，非全流程费用。计划SHA `88b2e7f4e60cc0081a1714c1c283812f9ab9df434ac09336f07ba964af4fb0f4`；双端私有`fccl_feedback_transfer_v1_closed_review.tar.gz`含1,436载荷，SHA `92b4010e154d67512cf7ad44c137a841a4881d9cb8deb9570e8b65c2dbddeafa`；`CLOSEOUT.json` SHA `58bafa23b4ba786bc4dba7ee0440e784acaa6a8c0efffd3e73600c83d4b6ff54`。执行协议保留于5115e951快照，不重跑本批。

<a id="local-edits-v1"></a>
## 源内自动反馈修订：已闭合

[开发程序](../../../research/agent_frontier_portfolio_20261029/feedback_corrective_policy.py)：1POST/12,230tokens，62源见证坏pending1→0、正例兼容不退；post-only参考同选，未计新原生收益。详见2f3f0082本文件blob。

<a id="phase-v1"></a>
## 早期阶段化原型

按原见证单位平均前/后提议视图兼容损失，加0.1复制正则；该项不是实测费用，可置0消融，替代动作未知不补收益。62单位/124派生视图仍仅两来源。旧两候选各漏一正例、放行一坏提议；首writer900秒无交付/usage、预留262,144，未发第二臂。详见[3a2d7648冻结记录](https://github.com/Wzh2learn/agents_final_tech/blob/3a2d764875b8fb25efdeefbfcb2d613a38b3fb44/research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#phase-v1)，原失败费保留。

<a id="normalized-v1"></a>
## 旧标准化十组：保留条件差别及完整费用

两题五组已完成，447 POST/4,255,067tokens，0新形成/训练。Actor与约束程序原生均2/2；约束自动开漫游2次，普通自动充值1次。约束较Actor多35.06%tokens、原生轨迹时间少7.66%；不能据此称整体优越。普通更新的一次timeout已满足目标，原生分数仍保留。
普通流程原要求先充值才开漫游，约束程序去除了这一偶然先后；派生提议视图又暴露VPN漏接和坏pending放行。相关规则、两角色/缓存口径、逐臂数值及包hash见[完整冻结记录](https://github.com/Wzh2learn/agents_final_tech/blob/0f98f7f503097c6348217d2e763b10c825b49ad2/research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#normalized-v1)。停扩源动作兼容性配方，保留有效程序和负例，不重复本批。

<a id="witness-v1"></a>
## 原先导：输入错误保留，形成产物复用

原2任务×5组仅启动4组便因null异常停调度；普通/Actor原生1，其余0，6组未启动。约束程序首次动作前异常，不能评价未执行纠正；共享规范修复后75项检查通过。194 POST/2,198,384tokens含4writer，全部保留；四次形成252,292，普通一轮耗尽输出帽无交付。两组同材料/模型/两提案及择优，字面compatibility仅proxy，yield不抢Actor信用，未知不作负例。两有效程序约3.8KB。

完整过程、空值等义反例与目标选择见[693f1a04冻结快照](https://github.com/Wzh2learn/agents_final_tech/blob/693f1a040f1180b4f5c57f196809acc44c051951/research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#witness-v1)。双端旧包SHA `442c4c8cef9a08aa56ea3297d25ea86f34e90c13be40fd0fddbfd92fbf08476f`；本批复用其提案，费用没有再次记作物理调用。

<a id="expansion-v1"></a>
## 旧四配置20组：停止整流程接管，保留局部价值

四个TRAIN故障组合×五冻结策略，单次开发。Actor/历史均4/4，固定旧流程/普通重写/学习路由均3/4；学习比Actor多51.24%tokens。但配置2同成功下学习少18.14%，新回跳机会0，收益不归新路由。失败包含漏开移动数据、同义反馈漏触发、未完成就转人工，以及44,551字符旧程序的读取负担；不是基础Actor不会操作。

845 POST/8,329,323已计，20份官方重放匹配；全部旧任务只作曝光开发。完整逐臂表、归因及双端包见[e8147ba6冻结记录](https://github.com/Wzh2learn/agents_final_tech/blob/e8147ba60c95572d54ef49d627255c8f124eab80/research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#expansion-v1)，原始结果不改。

<a id="prefix-v1"></a>
## 旧同一现场续做：保留复用与路由收益

程序复用较原续做少43.14%执行tokens，新增回跳再少7.31%；两项分开计。保留条件收益，不当作新任务泛化或更新规则已成立。完整逐臂结果、原生续做与形成成本见[固定快照](https://github.com/Wzh2learn/agents_final_tech/blob/0f98f7f503097c6348217d2e763b10c825b49ad2/research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#prefix-v1)，本批已完成，不重跑。

<a id="effect-witness-v1"></a>
## 旧失败进一步变成条件纠正监督：局部效果与执行归属

在新批代码保持冻结时，离线重算两条旧v2全题失败来源。按每次实际助手动作到下一助手决策划分62个完整交互片段，包含其间环境与客户动作；55段能把保存的程序决策与原生动作逐项绑定。每段的训练见证为公开历史/动作、前后原生分项向量差及执行来源。它是已发生的宏片段效果变化，不是单个助手动作的独立因果信用，分项标签仅在训练侧使用。

| 旧来源 / 位置 | 观察到的效果变化 | 可以学习什么 |
|---|---|---|
| 普通编辑，第14段，`await_refuel_confirm` | 充值使额度约束从不满足变为满足 | 保留有支持的动作与参数绑定，不能整题0分即丢弃。 |
| 同一来源，第22段，同一节点 | 再充值使相同约束从满足变为不满足 | 相同节点/操作的作用依赖已有额度、历史收据及当前需求；学习调用条件，不能把整个充值动作都当正例或负例。 |
| 效果条件来源，第14段 | 额度约束变为满足，之后未丢失 | 保留正确的额度处理；其全题失败不否定该效果。 |
| 普通编辑，第34段，基础Actor | 实际询问断开VPN，随后网速约束变为满足 | 提取基础Actor的真实纠正续行；不可把该收益归给未执行相应动作的程序主体。 |

第34段已回到OpenCode原始工具记录第58行核实：完成的Bash命令向world发送对应turn34的断开VPN询问；这段未匹配程序决策。因而旧描述应读作“该Agent运行恢复了网络”，而非“旧程序的网络节点已被证明正确”。**全运行的部分正确分数不足以支持冻结整份程序。**

由此得到下一更新候选：用实际效果见证区分应保留的动作、需要修订的调用条件，以及应从基础Actor吸收的新续行；更新的是纠正技能行为，不以审计结果代替方法。可用 `w=(h,a,Δr,ω)` 组织监督，ω标明程序/Actor的实际执行来源。下一必须与拿到同样见证的普通反馈更新比较，才能区分更新机制与额外标签信息；当时仅完成监督提取，未改运行中的四配置五组；后续形成及比较见[顶部](#normalized-v1)。

复用C的独立上下文复核支持这条数据解释，并把下一规则收窄为**有见证约束的条件程序修订**：对正效果上下文软约束保留对应动作，对负效果上下文软约束修改重入条件或交还Actor，结合程序改动量选择候选；不冻结整份donor。Actor来源的正效果片段单独提供，由可见前提决定是否吸收。新请求、授权或效果不明时不套用旧结论。普通更新必须得到相同62段、归属、代码与预算；另以“正确计算可用额度＋按请求范围核对成功回执＋普通Actor续行”为强简单对照。规则若同效更省则停止该具体修订机制。该提议与SkillRevise/HASP/SCOPE/SkillCAT仍有直接重合，待验差异是同节点跨公开上下文的正负效果约束及真实Actor纠正共同作用，而非新命名。

双端`partial_effect_witness_v1/PREFIX_EFFECTS.json` SHA **`e87a0626e6e599a841d445595d7ad77f7adc67eb48a862778656f5112d4d9322`**；`RECHECK.json`绑定脚本、原生数据与Actor日志hash。脚本`fccl_formation_tools/extract_partial_effect_witnesses.py`复算后与初始表完全一致；两条完整轨迹末端分项均匹配原评分。模型调用、Actor新episode与训练均0。62片段仍来自两条曝光来源，不当作62个独立任务。

<a id="preservation-v1"></a>
## 旧部分保留与控制流程修补：已完成、停止整节点冻结

旧两份v2程序各有部分正确效果，先冻结节点并学习路由，9个开发episode已闭合。首个新题全五组成功，新回跳未触发；另一事后定向配置中分支被激活，仍无对最强简单方法的可靠优势。385 POST/4,401,126已计，0训练；保存原生评分和公开缓存的两项历史残差不回填。后续同前缀与四配置结果见上方，证明应修调用条件、动作及退出，不宜冻结整个节点主体。

完整形成/反馈/集成、各臂及后验选择过程见[693f1a04快照](https://github.com/Wzh2learn/agents_final_tech/blob/693f1a040f1180b4f5c57f196809acc44c051951/research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#preservation-v1)。私有包SHA `24918a03bf4b19ba9b365b34143e04628191980cb4659bd2bc5f5776717693ef`；原件保留。

<a id="cross-batch-autopsy"></a>
## 修正判断方式

**“有没有效果”“为什么有效”“是否超过近邻”分开回答。** 后两项未成立，不能抹掉第一项；整题失败不自动否定有效片段。原生分数保留，局部信号另记，不补计整题成功。停止对象限定为具体配置、实现或饱和面板。

本次用first-principles复核归因，再按portfolio-triage排序：不把“完美来源、独立显著、每题全胜”设为开发资格。19份结果记录及固定历史覆盖14类，本次补入新先导为15类。按送达→触发→局部效果→完整任务→比较增量逐层判断；最后一列含研究推断。异构实验族不能合并算一个总失败率。

| 失败发生在哪一层 | 合理判断 | 回收方式 |
|---|---|---|
| 未实际送达或未交付：未读经验、reasoning耗尽、接入OOM | 本次端到端失败，但没有测到经验内容/学习机制的效用 | 保留失败费与接口反例；在已稳定链路验证，不要求先修好所有模型。 |
| 局部动作有效，整题失败：充值正确、网络未恢复，或补丁修原例但回归未全过 | 部分正确不是完整成功，也不是全部无效 | 提取公开前提、动作、后继效果及失效范围，学习保留与补缺。 |
| 有效果，尚未拆清来源：R训练8/12，O6/12 | 配方有正向开发信号，纯反馈因果与新颖性另待比较 | 保留适配器、成功/失败后缀，优先最小对照，不从零重训。 |
| 相对强基线无增量：规则14/14、程序扩样3/4而Actor4/4 | 停具体实现/已饱和面板 | 规则作强基线；回收条件性成本收益和失败条件，不关闭主问题。 |
| 来源身份不适合原主张：参考辅助、未来修复可读 | 不作为干净留出成绩；不等于素材无学习价值 | 标注教师/开发来源，同信息给基线；不包装自主发现或确认。 |

“严格”的对象保留为事实、评分与公平比较；“灵活”的对象是候选生成、部分成功利用和研究推进门槛。不要求一个方法对所有任务、模型、指标同时有效。

## 历次结果与可用素材

| 实验族 / 原件 | 实际信号 | 归因与素材用途 |
|---|---|---|
| [8B纠正训练→12新布局](../../../research/agent_frontier_portfolio_20261029/results/ALFWORLD_LEARNING_RUNTIME.md#trained-baselines) | 同BF16父模型F/O/R为4/12、6/12、8/12；R对O新增2题、未丢题，执行8,192,852→5,166,975tokens。 | **正向开发信号**：保留适配器与7组监督。训练配方有效信号与新算法贡献分开；内容/上下文因素仍未分离。 |
| [Astropy隔离四组](../../../research/agent_frontier_portfolio_20261029/results/ASTROPY_ISOLATED_CONTROLS_20261106.md) | 四组均3/3目标＋132/132回归；普通历史19→10 POST、491,274→268,655tokens，普通skill未超过历史。 | **历史有用，压成skill未必更好**。可定位有效执行细节，不能把“没有新方法”写成“经验没收益”。单次结果待重复。 |
| [Astropy A4/A5恢复](../../../research/agent_frontier_portfolio_20261029/results/CODE_SOURCE_CORRECTIONS.md#fcdr-recovery-result) | A5动态/普通同为3/3＋132/132，71,472 vs99,200tokens；A4均0/3，最后请求均length。 | 保留A5条件性正向；A4有交付瓶颈。两现场合计动态多60,915tokens，不能只留好例，也不能用合计抹掉A5。 |
| [ALF恢复](../../../research/agent_frontier_portfolio_20261029/results/ALFWORLD_CONTEXT_STUDY.md)及[full/recent](../../../research/agent_frontier_portfolio_20261029/results/ALFWORLD_ADDITIONAL_SOURCES.md) | 旧heat原会话失败、新会话成功；clean02近期更省、03完整更省。 | 上下文条件效用候选；会话格式/历史/提示共变，不能单归因清空。逐题oracle只是上界。 |
| [早期SymPy加载](../../../research/agent_frontier_portfolio_20261029/results/SYMPY_LATEX_TRANSFER_20261106.md)、[ALF通道](../../../research/agent_frontier_portfolio_20261029/results/ALFWORLD_TEXT_AGENT_20261106.md) | 三经验正文未进实际请求；inline后溢出；旧8B动作仅在reasoning未执行。 | **机制未暴露**，不能作经验语义负例。用于修正送达、上下文与工具通道，保留失败费用。 |
| [旧Astropy可读依赖](../../../research/agent_frontier_portfolio_20261029/results/ASTROPY_PROFILE_CONTROLS_20261106.md)、[参考辅助来源](../../../research/agent_frontier_portfolio_20261029/results/MATPLOTLIB_QUALIFICATION_20261106.md) | 旧wheel可读面含未来修复，故不能当参考隐藏证据；另有明确标注的source参考补丁＋真实执行。 | **来源身份决定用途，不等于全作废**。污染旧成绩不作干净迁移结论；参考辅助可作教师材料并给强基线同信息，不能冒充Agent自主成功。 |
| [27B能力](../../../research/agent_frontier_portfolio_20261029/results/CODE_SOURCE_CORRECTIONS.md#native27-capability)、Sphinx | 不推理档未编辑，低thinking档修好公开数组赋值但完整1/2；Sphinx多次读取不编辑，换工具仍未修好。 | 能力/动作落实瓶颈。不能一概归因4bit：旧分叉请求标识27B FP8，最新DeepSeek程序亦有逻辑错误；实际模型配置分批绑定。 |
| [绘图公开复现](../../../research/agent_frontier_portfolio_20261029/results/CODE_SOURCE_CORRECTIONS.md#probe-choice-screen)、[SymPy12481](../../../research/agent_frontier_portfolio_20261029/results/FCCL_FORMATION.md#new-source-v2) | 三候选均解除原公开崩溃，较强辅助验收未过；12481为1/1＋7/7，额外两失败在base也存在。 | **整段失败中有真实修复**。公开行为、既定评分、新增退化分报，共同既有失败不算方法新增错误。 |
| [源内程序学习](../../../research/agent_frontier_portfolio_20261029/results/FCCL_FORMATION.md#execution-fragment-v1)、[Django源](../../../research/agent_frontier_portfolio_20261029/results/FCCL_FORMATION.md#formset-source-v1) | 参数溯源＋非空前提使公开控制6/9→9/9；Django纠正达3/3＋49/49。 | **真实更新闭环已有**，保留反例、守卫、绑定和程序。可由经典候选消除/普通修复解释，不等于没有可用学习部件。 |
| [Django新任务四组](../../../research/agent_frontier_portfolio_20261029/results/FCCL_FORMATION.md#formset-target-v1) | 四份补丁全过2/2＋157/157；普通反馈6 POST/23,244tokens，候选12/107,282，且未试用原程序。 | 补丁正确、当前重绑定无收益、协议未完整落实分别记。触帽不改称代码失败；停止本版同题追提示。 |
| [ALF进度与文字修订](../../../research/agent_frontier_portfolio_20261029/results/ALFWORLD_ADDITIONAL_SOURCES.md) | soapbar/soapbottle冲突已送达仍做错；heat任务指导成功、普通/固定skill失败；文字修订未改善已测续做。 | **信息未连到行动**。可执行纠正是合理研究对象；手写指导有额外领域信息，保留作强对照。 |
| [ALF14规则恢复](../../../research/agent_frontier_portfolio_20261029/results/ALFWORLD_ADDITIONAL_SOURCES.md#simple-recovery)、异步状态控制 | 领域规则14/14；两个async实现的相反取消选择被API状态规则覆盖。 | **本面板残差已解释**。冻结复杂选择器，规则作参照/回归；不外推所有任务，人工规则研发也非零成本。 |
| [tau2 v2/v3/反应式](#activation-v2) | v2避免重复充值却不修网络，普通编辑修网络却充4GB；v3旧流程阻塞；最新把正常Say回执误当充值写入。 | **局部正确效果＋范围/续行失配**。可学效果保留、参数和退出，不能全题0分丢掉互补片段；也不能称盲合并已成功。 |
| [形成/训练中断](../../../research/agent_frontier_portfolio_20261029/results/CODE_SOURCE_CORRECTIONS.md)、[梯度试验](../../../research/agent_frontier_portfolio_20261029/results/ALFWORLD_ADDITIONAL_SOURCES.md) | 规划耗完读取预算无计划；reasoning耗尽输出；4B接入OOM、8B梯度试验无可评估终版。 | 是交付/资源失败，未测到机制收益。O/R另一批已各完成192更新，不能混写成“从未训成”。 |
| [见证更新先导及修复后10组](#normalized-v1) | 原空值0介入；修复后约束/Actor均2/2，约束多35.06%tokens、墙时少7.66%，3次程序纠正真实执行。 | 保留可用动作、条件差别和时间—用量权衡；不抹平原生结束/目标满足，不把动作正确直接当作额外收益。 |

## 最值得挖的三类资产与复用收益

**优先级1：已有纠正训练保留为正向资产。** [全36槽再归因](../../../research/agent_frontier_portfolio_20261029/results/ALFWORLD_LEARNING_RUNTIME.md#paired-autopsy)：R/O为8/12、6/12，R多2题无损失，覆盖本次F/O成功并集。`invalid_action`回执412→13，clean中263→11但成功均2/6，说明合法执行已改善，目标规划仍有残差。R在8题更省、4题更贵；总省36.93%执行tokens，其中72.12%来自两题新增成功，优先挖昂贵循环，不能要求每题全胜。look两臂均28更新、R/O唯一动作2/3、监督tokens1,246/1,225；内容/上下文仍混淆。现成LoRA与监督保留，不从零重训。已核来源＋执行R8,120,242、O8,693,535，少573,293；训练/筛选/研发/硬件未全计，不称全成本优势。配方收益可继续开发，独立算法贡献另证。

**优先级2：全题失败中的正确效果值得学习。** v2“只充2GB”、普通运行中Actor“恢复网络”、Sphinx“隐藏类型但新增重复签名”都保留。充值首次有效、重复反而破坏额度，源任务先充值再开漫游被误学为必要前提；宝藏是条件、参数、重入与退出监督。62段只有5个非零宏效果，未变化不标错误，用户动作混在片段中不冒充单步因果。先提取有效片段，补缺后再验全题；不要求源轨迹先整体完美，也不把盲合并当已成功。已有尝试见[新实验](#preservation-v1)。

**优先级3：双方成功仍能提供效用候选。** 新核两组分叉30份请求/SSE、参数及原生日志hash：heat先取杯/先去炉灶都成功，24,234 vs47,984tokens；cool先去冰箱/先加热苹果都成功，131,971 vs116,726。按现有15%成本带作**本轮后验筛查**，heat为49.50%成本候选，cool的11.55%保留TIE；旧“没有成败偏好”不变。只一臂一次、自定义environment_step而非OpenCode，不推期望效用，不把整段信用全给首动作，不能跨题训练A/B字母。

**复用成本是可累计收益。** Astropy普通历史同成功下少45.31%执行tokens；tau2同现场程序复用少43.14%，新增回跳再少7.31%；四配置扩样一题少18.14%，全批却更贵且少成功一题。证据指向何时复用、何时交还Actor，普通历史也应作为有效组件保留。

三条机制推断：整题0分遮蔽有效动作；冻结完整旧节点会冻结错误的反馈解释和退出；信息正确不保证行为改变。当前62段仅两条来源、5个非零宏效果，监督覆盖有限。应让局部程序接通实际行为，不用更多日志替代独立监督。

## 放宽开发门槛，保留事实标准

1. **分开发、扩样、论文结论。** 单题局部信号足以产生下一候选，重复与跨题放在扩样阶段；不先要求独立统计确认才准尝试。
2. **不要求每题每指标全胜。** 比较条件性成功率—成本和回归；无显著不等于无效，单次省token也不等于已证明省钱。单题信号进开发池、重复跨题后再升级；一次负结果仅停相应实现，不关主问题。
3. **来源不必整段完美。** 失败轨迹中的真实有效片段可训练，连同失效条件、未解目标保存；Actor退出与环境/代码成功分报。单步纠正也能有价值，不强行多步求复杂。
4. **成本按实际部署计。** 全项目物理总账保留；方法比较分共同来源、额外形成/搜索/训练、执行，在明示N个后续任务下摊销。不重复收整笔历史研发，也不删失败形成费；token不等价计算/货币。
5. **资格只约束相应主张。** 源PR已合入目标base只对特定历史迁移主张必需，不是所有经验复用的必要条件。base/reference共有既有回归失败可在新协议单列、比较新增退化；参考辅助材料标为教师来源而非自动废弃。旧分数不回改。
6. **从真实失败生成候选，再配对取得监督。** 不必先凑齐完美四格，g未触发不评价未执行π。手写规则也应在新题前冻结：看过答案后不断补规则不是免费的全知基线。只要求胜过预先定义的合理强基线，不要求胜过所有可能方法。

## 尸检导出的方向

**下一步优先利用已有收益形成学习机制。** 先从R新增成功和真实部分修复中定位“反馈后行为怎样改变”，保留训练资产、普通历史及有效动作。把已实现效果、可见前提、参数和退出共同用于纠正技能更新；[原首轮](#preservation-v1)与[最新十组](#normalized-v1)都保留，不重新包装旧四组或饱和面板。

**有用不只等于纠正基础Agent错误。** 在Actor推理前，正确的可复用片段可能节省后续推理；Actor已经给出正确动作后，应保留该动作，不能再收取“省掉推理”的收益。已有错误提议则是修订/阻止的对象。前后两个时点的内容、调用与交还要共同学习；双视图仅作接口诊断，替代动作收益须实际续行，不能凭空赋值。当前原型只能筛源内动作兼容，下一更新应针对部署收益，而非只增加正例重演。

**开发接受局部信号，论文检验增量。** 单步纠正、参考辅助教师及来源不完美均可开发，按来源标注并让基线拿同信息、同模型与同形成预算。没有触发就查适用性，没有交付就查执行链，动作正确但总量更贵就查覆盖、handoff和摊销，不统判机制无效。暂定优先级为R行为差异→失败中的有效片段→条件性成本；下一以原生成功、回归和形成＋执行成本比较普通反馈、冻结规则及[匹配近邻](../../../research/agent_frontier_portfolio_20261029/IJCNN_RELATED_WORK_REFRESH_20261030.md)。收益在声明的任务范围成立即可继续，不要求普遍最优；来源／工具修复及本轮尸检不单独算第二篇方法贡献。

## 证据范围与当前状态

新核19份结果文档的定位/hash，36条训练迁移receipt/manifest及所存终态，Astropy两份completed和所存评分，分叉30份请求/SSE的hash/usage/参数及world日志hash。未重跑环境、未重核所有历史SSE/模型权重，未重新全面外查文献；其余为项目记录支持，不升级成本轮独立复现。

归因阶段另核36槽及720旧先导载荷，见私有`REASSESSMENT.json` SHA `ada99c1656a8dc0867c111d3d8c6fdd9b8e0783938fe562357c8a89efdd37c07`。最新10组的1,596载荷/447usage及总账见[顶部](#normalized-v1)，派生程序探针不是新原生任务；不重新核所有旧SSE/模型权重。

早期19份记录及receipt复核见私有双端 `autopsy_reuse_20261113/RECHECK.json` SHA `959566614a474dce648fe3b0ee6fc865e874f2e47d7f6d08b8c3cbd257aaf71b`。GB10证据前缀 `/home/testuser/wzh/research_evidence/agent_learning_20261030/`，本机 `D:/Documents/Loop_D_assets/agent_learning_20261106/`。旧只读尸检阶段1,753请求/17,446,160已知为历史账，不当现况；本地历史模型不混入校园账。

<a id="reactive-v1"></a>
## 最近先导与固定历史

[0954279f反应式完整记录](https://github.com/Wzh2learn/agents_final_tech/blob/0954279fdfe88414f730ad350dd3dbb256016f6c/research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#reactive-v1)：三组原生均成功，唯一介入为回执误触发；执行464,898 vs同信息历史441,298tokens。当前关键词策略停扩，接口保留。149请求/1,450,383tokens已计；558载荷包SHA `6b308e7f8e3c8f7e08f992b4e3a7806815f18f1bb70c883f395df1818aa456ec`。

<a id="residual-option-v3"></a>
[v3完整记录](https://github.com/Wzh2learn/agents_final_tech/blob/0d09bc14dac2793c3bbafdecc7c5bafdea41aae2/research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#residual-option-v3)：旧流程阻塞后继纠正，173请求/1,984,377tokens已计。

<a id="activation-v2"></a>
[v2激活/消融](https://github.com/Wzh2learn/agents_final_tech/blob/6a2b838236ff36b430e180b762091dbe453c10d7/research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#activation-v2)：重复充值与网络恢复的互补失败，231请求/2,241,365tokens已计。

<a id="effect-conditioned-v2"></a>
[v2来源/数量反例](https://github.com/Wzh2learn/agents_final_tech/blob/f8cd77729665eb8cf8491ec78c716aa63c037b40/research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#effect-conditioned-v2)及[v1](https://github.com/Wzh2learn/agents_final_tech/blob/7836c893c3926ea97f2d337b6790b097f63c59f7/research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md)。原件未改；未投稿、付款、外部联系或生产操作。
