# 代码来源：教师纠正与形成成本

> 状态: 活跃 | 更新: 2026-11-09 | 取代/被取代: 从ALFWORLD_CORRECTION_DATA按主题拆出代码来源；历史锚点保留。

<a id="current"></a>
## 当前结果

SymPy21055取得一条**教师辅助、经执行验证的代码纠正**。教师仅接收原公开问题、D定位的源码和实际公开复现反馈；未接收未来目标或gold。它是一条来源素材，不是学习方法或迁移收益的确认。

| 条件 | 实际结果 |
| --- | --- |
| nonthinking，1 POST | 正常stop，输出完整diff；原严格应用因hunk行数错误失败。 |
| 同一diff，Git --recount | 只重算hunk行数，不改生成程序文本；独立原题1/1、回归13/13通过。新增模型0。 |
| thinking，1 POST | 600秒超时，原SSE含16,355字符推理、无答案通道或finish；不是完成的能力对比。 |

重计数控制是在看到第一臂应用失败后选定的后验工程适配；原始失败、超时与raw均保留。原题/回归通过只支持该释放测试合同，未扩充为任意输入正确性。当前不追加同题思考模式重试。

实际两臂消息逐字节相同，只有enable_thinking不同；模型27B、seed17、temperature0.2、32k上下文与8192总输出相同。原始请求/通道/补丁/执行日志可定位；没有把候选代码写回模型服务或业务系统。

## 成本与执行边界

本阶段共3个物理POST：早先空tools被HTTP400拒绝1次，以及两臂各1次。仅nonthinking有完整provider用量：输入3,583、输出456、合计4,039；HTTP400与超时两请求usage未知，**阶段总量未知**，cache未知。旧source的48POST/465,678已知tokens另记一次，不按子臂重复收取。研发Agent用量未完整计量。

nonthinking生成64.885秒，thinking600.001秒；后验重计数及两组CPU评分合计5.616秒、2个评分容器。训练/judge/付费科研API为0。owner已退出、两个owned评分容器已实查不存在、资源锁已释放；共享模型服务未改动，断连后服务内部生成状态未探测。

首次直接CLI预检受旧校验器的全局模块清单影响；固定为stdin/importlib调用后，旧17组件与两个二进制严格一致，未改校验函数或历史manifest。无工具请求只省略空工具字段；传输层兼容检查85项GB10测试通过，原ALF工具合同hash不变。

## 证据定位

GB10私有根为`ROOT/code_source_expansion_v1/SOURCE_ACTOR_PREPARED_V2_BASH_FIX/sympy__sympy-21055/teacher_patch_v2`：

- 协议SHA `77d9a417e23cef5d7a6e3d23c9766ac172057d1d11cf447e073fc5bd190e928c`；准备manifest SHA `44af743dab01224bcb7085de6848dc65c9bd60596a6b9391d724908e877e062d`。
- 主结果false receipt SHA `519023796011a76195055f7b32dbe655ca01f7dee71233d80bb096d202773bed`；true receipt SHA `3234ee92c3c191c7b1987a03fb1ce334c4fdba68b8bb18fd394eeae39f1ac0fa`。
- 后验`recount_evaluation_v1/D_RESULT_V1.json` SHA `abcfd72d6cdce158bcdcd0c6ac2819721cc9ca20263d37fd36943c21d2fe802c`；D闭合SHA `e2ea0e06cf6d77dc40ee87756be218a3d5dc600cda1eb273cacdd88dba6de9b4`。
- 私有封存包`teacher_correction_closed_v1_20261108.tar.gz`，1,922成员/7,233,655bytes，SHA `f43b840d9591257792ae7ac705bccc98c4bd69928964022d2bc68615ba5507f2`；原HTTP400包SHA `da0ae15fdc46963e262bd0b2a9fe2148674de8d309ede19d24b56600fe88ecfd`。模型权重及依赖不在包内。

[单轮入口](../contextbench_teacher_patch.py)；[主线短计划](../STAGE2_AGENT_RESEARCH_PLAN_20261102.md)。纠正使用与后续目标必须继续隔离，不能把该已曝光source改称新确认。

## 后续代码版本边界

注册候选为21055→9384：源修复merge `4b03990bb9df237c110b8120ffe5ed94c610348c`是目标base `70cd4ffd093ac224fc0226c1be58f9163e2c800a`的祖先（ahead290/behind0）。既有compare索引SHA `c22b36b869f5b3d72827e1a352b15fa62585e6dccfd56297c97e812b669c97e6`，`ANCESTRY_CHECK_V1.json` SHA `c8412bc8d709509fa9336520dd4d19572c65f67dea571f8fa5a4ce6700143603`；本次仅核元数据与汇总，没有重查原始compare。这支持代码版本向前，不证明原issue提出时间或无曝光。目标维持DEVELOPMENT_EVAL_ONLY，本轮未运行它。9384与21309两条题面hash不同，但索引绑定同一上游PR21309与同一base，不能作为两项独立PR修复计数。集合候选16988→16953仍仅有公开行为/时序复现，未获actor资格。

**可复用的目标资格。** 21055的`refine/arg`与9384的`refine/Piecewise`同属假设化简问题。9384历史CPU资格已完成：原题base 0/2、gold 2/2，双方回归各320/320。本轮只读复验GB10现存`QUALIFICATION_RUN_V2/sympy__sympy-9384/clean_base`的1,883文件及公开题面，全部与原冻结SHA一致，没有重跑模型或资格测试。该目录是源码快照，不是Git checkout；Python3.8 ARM环境仍沿历史记录，未整体复验。私有`sympy_refine_transfer_v1/ASSET_STATUS_V1.json` SHA `906a6a1f28603b544097fc1dba6c8013490c754d3be200602bc33b55748be0d2`。已复用现有runner准备双臂隔离输入，gold/testpatch/资格父目录不进入actor；来源只能称教师辅助修复记录，尚无目标迁移结果，不再先重复已通过的资格。

**准备器已复用。** [现有目标驱动](../run_contextbench_target.py)新增SymPy显式分支：none与source_repair_record，固定绑定原教师失败、后验重计数及执行验证。实际执行复用既有SymPy评分器，不把修复记录称为普通成功轨迹。本机45项合成控制通过（导入替身及Windows UID适配）；GB10与ALF准备器合计97项/246个子控制通过，无替身。两臂实际CPU准备及D独立verify已完成，各1,883文件，0模型/HTTP/容器；gold/资格父目录/评分补丁不进actor挂载。私有`ROOT/sympy_refine_transfer_v1/TARGET_PROTOCOL_V1.json` SHA `698785a471942627e60b6dbeb30deb56fa66f5d7d955b21ba3dedd8984765884`及6份元数据已双端镜像；源/目标路径与manifest查同目录。普通none/修复记录两臂暂缓运行，作为新反馈机制第二环境的复用资产；尚无目标模型成绩。

## 先前准备与故障记录（迁入原文）

以下为原页面代码来源段的完整历史文本；其中“下一步”指当时状态，当前裁决只看上文。

<a id="source-tool-contract"></a>

**两源尸检已核。** `SOURCE_EPISODES_AUTOPSY_V1.json` SHA `52b958f5b39914c37017824e356ba9d56555a9b37907d7f30ad26311ebdb5727`：A共7次工具，D再核324绑定与96原SSE，合计input1,105,961/output5,586/total1,111,547tokens一致；96条cache未报告。每题48动作均只读/搜索、无编辑或测试，47轮后继工具反馈逐字带回，首user题面完整。确认实际只开放bash，而其说明禁止读写/编辑并指向未开放工具；这是能力/说明合同冲突，未证明它导致循环，亦不把两次失败当纯模型能力或反馈学习结论。先做source专用的最小合同修正和隔离写入验证，不改ALF/生产工具面，不直接重跑整批；source参考辅助纠正为低成本后续选项。

**工具说明修正与真实写入控制通过。** source专用v2只在转发前深拷贝替换唯一bash的说明，保留schema/messages及其他字段，非法工具拒绝；不改ALF或生产面。GB10 Python3.12聚焦57项通过，C限定静态PASS（SHA `1b1859f5b29ec70f16f7b52a247d817cb7c0a83371e4e1c831f07f642b1d9580`）。独立4POST/120秒/2MiB控制实际2POST、25.77秒、56,724wire bytes，1次原生bash真实写入并读回28bytes；D复核19绑定、原SSE和容器清理。receipt SHA `b8e914788bcaccf6aab7cc4dd639787993095b1648e1c28b9d41dd733d73ecaa`，D复核SHA `f0f8d6924735941ba8a2626a9196b55ce075a4ab55eb05af58cd27d8ac5afe96`。新增input5,341/output153/total5,494tokens，cache未知，训练0；旧96帽未重置、SWE题未重跑。只确认此次通路，不归因旧循环或认证修复能力。

该控制薄包21成员已双端核验，SHA `37516f9214d85400d8e082f0de583d44708e808c76396790a64acb7e3e834048`。新临时树仅5个受控修改与28缓存；五文件/patch及Git基线655afb2e已私有镜像，代码包SHA `aedaff8004b7e01bb9210294ac18b179023163aa18ebccf86ad9dad55dd7b1d8`，D核17组件的快照或Git重建后只移除这棵新测试树，7个历史树保留；收尾SHA `c11a983e20cc4edc8f1434b78bf5e294bdaac22aff1873b573ec6bf01f5fe6d2`。C9在本机/GB10各两harness定向分发，LF SHA `a496be2764834b097c9defd174d6eccd803573d146faa760dd19b8263c776ef3`，未声称全技能库重验。

**Bash-v2的已曝光来源开发重试已闭合，未形成成功来源。** 仅SymPy21055，新根`code_source_expansion_v1/SOURCE_ACTOR_PREPARED_V2_BASH_FIX/sympy__sympy-21055/attempt_v1`，manifest SHA `c1cbc8bcca58d6a5d32ac9322b777773bb4d8bc476676a508ebbf304bbaf71ba`；runner SHA `b2377f352cc824100c70bfb3340c0c9b78e3722d777b2fe113ed75b695c6b86d`。原题/wrapper与旧源一致，工具说明为既定v2；source-only输入未读未来9384题面/gold。D另给48POST/1200秒/64MiB，不重置旧96POST账；release SHA `85f43117f351875eef8106c9525e742a36a968c0c74767c23a91e38aea132076`。owner `1925392`/birth `1085721038`及3个owned actor/评分容器均已退出，锁已释放；未并发ALF模型、未重启共享服务。

实际48模型POST/49尝试，末次为封顶拒绝而未转发；输入461,600、输出4,078、总465,678tokens，usage未知0、cache未知。actor墙时714.981秒，两个独立评分容器合计4.527秒；训练/judge/付费科研API为0。源问题F2P0/1、PTP13/13完整覆盖，代码差异为空；模型运行真实公开复现后，重复同一命令33次。原receipt保留GENERATION_FAULT，403仅表示正常预算封顶；未修复判断由独立评分支持，不当作已查明的工具/模型单因果。

D核全部48原SSE/实际工具合同/请求hash/封顶账及容器清理；closure SHA `f92f4bb287b216cfb8401e6862656df6139e13416496b2b65c673bc2481ffb1a`，原receipt SHA `5d9cc82cd7a069e2b39b47920fcafa844b27c49ab0ff9f8733f99786824144fe`。私有薄包183成员/742,006bytes，SHA `9dd91038692e93b97319dd3fbb33bfa15d3e0d905e4aa19fc6b3b97cc7cb8825`，本机逐项核182文件。源码/依赖沿用原资格资产，不用参考patch冒充Agent成功。

**历史设计（已执行，结果见[当前结果](#current)）：同输入单轮教师代码修复能力对照。** 同27B/seed17/32k上下文/8k总输出，非thinking与thinking各最多1POST，只有请求级思考开关不同。输入限本来源的公开题面、源码和真实执行反馈；D定位辅助不冒充完整自主Agent。输出补丁在隔离工作区检查并原生评分，严格保留reasoning/content、格式或长度失败、调用和形成成本。固定模板具有True分支，但旧source入口强制False且False计数器不能套用True；当时只准备薄衔接与CPU验证，尚无True实际请求或新训练。不继续同配置48轮重试；必要时比较明确标记的source-reference辅助基线。新增[SymPy集合候选](ALFWORLD_LEARNING_RUNTIME.md#sympy-intersection)仍仅作公开行为素材。

当时[单轮入口](../contextbench_teacher_patch.py)与49项CPU检查已完成，尚未prepare或生成；后续实际执行由页首结果取代此状态。真实分词初检将BatchEncoding的2个字段误作长度，旧证明保留为无效；修复后按一维整数token计数，False为3,583、True为3,619，加8,192输出与512余量均小于32,768。协议SHA `983a80057a21db5863bf08a7a3f9de2f438ff778ed815a6b8d0d6ac878adaf67`；实际CPU复核SHA `76e67530e5eb66e72080325bed3a9230aab8351d03f09555092270ca7202088b`，模型/环境/容器0。它是代码来源的能力诊断，不把它设为其他已合格ALF来源继续研究的统一前置。

报告保留两项byte差：每题wire计数比原SSE body多6,720bytes。冻结relay明确wire另计HTTP响应头，body文件不含头；单位不同，不据此判断token丢失或超帽。动态头原文未归档，未声称独立重建每字节。两源闭合私有包349成员/2,068,583bytes已双端核验，SHA `3d3ac3fa60fcc0ac078204f96113e43397863a0aa67eb6e2e7d44e6399c2de63`，本机check SHA `973a88f07660ea1d4efdf6b7cf2091d22090b9942b6bd861007b9c05514c8d8a`；尸检报告随后单独镜像，不重打原包。

[Current result](#current)
