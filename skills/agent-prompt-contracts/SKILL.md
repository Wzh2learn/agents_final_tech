---
name: agent-prompt-contracts
description: JinRongAgents 已验证的 4 条 agent prompt 契约 (verbatim 首查 / FORMAT_HINT / bash 先行 / 只读 summary)。编写或修改任何 OpenCode agent、Loop A/C prompt 时必读; 修复失败的 prompt 改动必须同 commit 补录本 skill (AGENTS.md 治理规则)。
---

# Agent Prompt 契约库 (已验证)

每条契约都来自真实失败 → 修复 → 回归验证。格式: 失败模式 → 对策 → 验证方式。新契约无证据链接不得入库。

## 1. verbatim 首查 (Verbatim First Query)

**适用**: 任何自主发起检索查询的 LLM (m2-qa、RAG agent)。

**失败模式**: 模型把用户问题"善意"缩写成实体名 ("嘉兴民安的总资产是多少?" → 只检索 "嘉兴民安")。本系统 fallback 排序 = 查询词在 chunk 内包含计数, 查询越短命中越差 → 漏召回。

**对策**: prompt 明写 "首查必须逐字使用用户完整原问题 (保留 资产总值/币种/市值 等全部字段词), 不得缩写"; 仅允许在字段缺失时追加一次 "实体名+字段关键词" 补充查询。

**验证方式**: RAG QA 15 问回归全跑 (scripts/m1_rag_qa.py, 基线 15/15); 抽查检索侧日志首条 query 是否为完整问句。

**证据**: docs/experiments/2026-08-05_opencode_e2e.md §6 (08-05 S3 M2 链 PASS 带引用)。

## 2. FORMAT_HINT (机器解析输出契约)

**适用**: 输出被程序解析的任何 agent (JSON 契约场景)。

**失败模式**: a) 答案包 markdown 围栏/散文 → 解析失败走兜底; b) sources=[] 但出处内嵌在答案文本里 → 下游溯源丢失 (08-06 实测约半数请求)。

**对策**: 三层防御: ① agent prompt 内嵌输出契约 — "最终回复必须是且仅是单个 JSON, 无围栏无 bullet" + 完整示例 + 显式拒绝条款; ② 请求侧追加 FORMAT_HINT (src/biz/opencode_adapter.py); ③ 确定性保守兜底提取器 — 只提取答案中已出现的真实引用, 永不虚构。

**验证方式**: 连续 10 问零空 sources; 单测钉住契约透传 / sources:[] 显式拒绝 / echo 提示词示例负例 (tests/test_opencode_adapter.py)。

**证据**: 62d21e3 (契约加固) + c5a8ecf (F3/F4 测试守卫); docs/18 08-06 section。

## 3. bash 先行 (Bash First, 证据先于断言)

**适用**: 所有验证/判定类任务 (Loop B、evidence-verifier、任何验收)。

**失败模式**: 模型凭训练记忆或 commit message 声明"判定 PASS"; 声称跑过测试但实际没跑 → 验收失真 (08-04 夜间验收审计抓出过多处声明与实况漂移)。

**对策**: 判定必须由真实执行的 bash 命令产生 (pytest/curl/diff/md5sum), 模型只转述输出并判定; 验证层尽量纯 bash 无 AI (Loop B = 信任锚点, 1800s 周期常驻)。审计 prompt 明写"不轻信任务描述与 commit message, 逐项独立核验"。

**验证方式**: verify-report.json 与手动复跑一致; "已修复"声明抽查复验 (重跑相关 pytest/curl)。

**证据**: scripts/graph/loop_b_verify.sh (07-31 起持续 PASS); docs/experiments/2026-08-05_opencode_e2e.md S3。

## 4. 只读 summary (Read-Only Compact Summary)

**适用**: 多 agent pipeline 的判定方 (evidence-verifier 类)。

**失败模式**: 判定方自行打开原始文件 → 超出证据范围再解读、scope creep、与执行方数据得出矛盾结论; 多信息源互相打架。

**对策**: prompt 把判定方数据源写成白名单: "第一且唯一数据源是 /tmp/opencode/m1_compact_summary.json, 用 bash cat 读一次; 禁止 open/glob/grep 任何其他文件 (尤其原始样本)"; 同时给判定模板 (PASS/FAIL + 具体理由 + 必须出最终文本, 不得静默结束)。

**验证方式**: e2e 彩排观察工具调用轨迹 (应仅一次 cat); verdict 与执行方实测数据交叉一致。

**证据**: opencode.json evidence-verifier prompt; 08-05 S3 verdict PASS 与 m1-extraction 实测一致。

## 治理规则

1. 修复任何 prompt 相关失败的改动, 必须同 commit 在本 skill 补录/更新对应契约 (失败模式 → 对策 → 验证方式)。
2. 契约条目必须附证据链接 (commit hash / 实验报告路径); 无证据不入库。
3. 新增 agent 前先扫本库: 涉及检索→契约 1, 涉及机器解析→契约 2, 涉及验证→契约 3/4。


## C-1 /no_think 思考开关（agent 路延迟）— 2026-08-12
- **失败模式**: m2-qa 经 sidecar 走 :8004 时默认开 thinking, reasoning token 先吃 completion 预算, warm 延迟 22-55s, 超 OPENCODE_ASK_TIMEOUT=18s 全量回落直连, "快与准"菜单名存实亡 (08-11 延迟事故)。
- **对策**: opencode_adapter._FORMAT_HINT 尾部追加 `/no_think` (Qwen3 user-message 开关), 模型层关思考; 不动 sidecar/provider 配置。判 :8005 已有 enable_thinking=False 先例 (m2_eval_judge.py)。
- **验证方式**: ① 重启后 warm 单问实测 <18s 记台账; ② 16 题确定性 eval + judge 质量不降 (关思考≠降质, 需复验); ③ status.sh B4 段 fallback 占比趋 0。
- **证据**: docs/experiments/2026-08-11_agent_latency_diagnosis.md; dispatch 2026-08-12 #S2。

## C-2 现役科研授权与角色证据边界（2026-10-26）

- **失败模式（静态核实）**：A/C现役正文仍把9月handoff称作唯一计划；A写有不连接另一服务器、4B仅smoke/8B主学生的历史默认，与Phase A确认的GB10、ordinary Qwen3-4B资产冲突。另有风险是将契约4的业务verifier summary白名单无条件套给科研C，导致审计只读被审方汇总。
- **对策**：A/C都绑定 `docs/research/LOOP_D_RESEARCH_PROMPT.md` 和当前任务卡版本/hash；执行位、学生规模、父checkpoint、范围与预算来自现役授权。科研C按任务卡读取冻结raw、参考和评分器，先独立复算后读A解释；业务verifier的既有白名单仍只在其业务任务适用。
- **验证方式**：静态核验A/C均引用唯一现役指令，退出旧阶段/服务器/学生默认；定点文档治理测试、skill分发比对及源码diff。该检查证明指令一致性，不证明harness已经启动或模型实验成功。
- **证据**：`docs/governance/audit/loop_d_control_review/PHASE_A_RETURN.md`（GB10 ordinary资产）；`docs/research/LOOP_D_RESEARCH_PROMPT.md`（当前角色/任务/预算）；本次A/C指令diff及Graph Loop执行交接核验。未声称已观察到一轮受该旧指令阻断的模型实验。

## C-3 先核完整合同，再归因输出预算（2026-10-28）

- **失败模式（静态反例）**：固定D/T/M快照中，T/M的UNKNOWN指令包含`numeric_value=null`，typed解析器却要求不含该字段的精确keys。按该指令提供字段会被拒；旧输出又有19/24达到512上限，不能仅加大上限就宣称完成公平机制比较。
- **对策**：生成前把答案与UNKNOWN的完整schema、prompt示例、解析器allowed keys成对核验；strict whole-JSON、embedded提取和语法适配分报。有合同或参考修订时冻结新版本，保留历史raw与分数；输出长度、thinking和额外字段负担作为实验对照，而非事后免费修复。
- **验证方式**：只读固定Git blob；确定性合法/非法key集合控制及字节/hash负例通过。该反例证明合同不一致，不证明它导致旧24条中的具体模型失败，不声称已运行新模型。科研C可读取固定raw和参考，不受业务summary-only限制。
- **证据**：`docs/governance/audit/loop_d_control_review/NEW_LOOP_D_HANDOFF_REVIEW_20261028.json`的`contract_probe`；同目录`review_loop_d_handoff_20261028.py --self-test`；现役`docs/research/LOOP_D_RESEARCH_PROMPT.md`第6节。版本化技能源与本机两份既有安装受控同步，未安装新技能或改harness配置。

**2026-11-13形成补充**：局部编辑两组各16,384输出、均length且无工具交付；旧成功形成实际用过25,476/30,736输出。不能从代码/输入变短推断思考预算足够，更不能据未交付裁决方法。两组共同声明形成输出/时间帽，先说明gained=false→true、lost=true→false；单次修订可先处理一处有害重放，不要求补齐所有覆盖。局部编辑/显式额度/标签契约本机68通过、1个Linux锁测试跳过；64K实际交付仍在跑，未证明这组工程修订的独立因果效应或原生收益。证据：[形成记录](../../research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md#local-edits-v1)、`test_local_editor_admits_declared_thinking_budget_and_explicit_label_direction`；旧raw与费用不回改。

## C-3补充：字段存在、接口资格与方法效应分层（2026-10-28）

- **失败模式（固定参考复算）**：D/T/M决策卡把不存在的`unit_reference`全None解释为8条参考都缺单位，实际8/8含`unit`；另把格式合规率持平作为停止M的语义方法判据。C额度耗尽被错误延伸为D不能继续已授权的内部图像修订。
- **对策**：先验证schema字段存在再判断缺失，UNKNOWN与缺字段分列；接口资格和语义/风险/成本增量分开；审阅派发额度不代替已授权实作范围。科学总output与reasoning细分不重复记账。
- **验证方式**：冻结JSON字段控制为unit=8/8、unit_reference=0/8，单位分布3/1/4；核现役指令明确D可继续修图、29/29不追加派发、新科研生成仍为0。仅静态与离线复算，不代表新模型比较或论文图像已修完。
- **证据**：`docs/governance/audit/loop_d_control_review/LOOP_D_POST_RETURN_REVIEW_20261028.md`；固定起点`c33c14bf`的`research/word_scoring_new_family_20261027_v1/exposure/PANEL_FREEZE.json`与`DTM_DECISION_CARD_20261028.md`。本次只更新版本化技能源，未同步机器安装或修改harness。

## C-3补充：第三方公式、对照真值与复现接口（2026-10-28）

- **失败模式**：公开BEIR评测审计两份本地实现共享二值nDCG假设，与trec_eval分级gain不同；MAP分母不同；AB真阳性计数比较方向颠倒；复现命令与脚本参数不符。
- **对策**：逐指标对照官方源码和可运行实现，构造分级/多相关文档及次序双向正负例；固定原稿和数据版本，重新计算受影响的输出；区分研究者示例排行榜、构造控制与官方结论。
- **验证方式**：独立执行固定反例：nDCG当前1.0、官方公式约0.8597187；MAP当前1.0、官方0.5。真实数据影响尚未复算，不预断新结果。
- **证据**：固定提交d79ba1a7的 `research/paper_e_public_eval_20261028/code/beir_audit.py` 和 `beir_audit_ab.py`；`docs/research/LOOP_D_RESEARCH_PROMPT.md`第0节及官方trec_eval源码链接。

## C-4 外部方法的反馈输入与离线工具先对齐（2026-11-05）

- **失败模式（实测）**：RethinkSkill 接入把完整历史放入自定义反馈字段，明显大于其原生 evaluator 摘要；扩大输出上限未保证契约合规。另有 OpenCode glob/grep 因容器缺 rg 而尝试下载，在禁网环境失败，Agent 生成的经验又将其写成通用工具建议。
- **对策**：对照固定上游的反馈构造、字段、候选验证和 gate；改变证据信息量必须标明适配，缺失答案或 gold 不补造。先验证离线工具是否存在，再给模型诊断提示。外部方法结构校验和实际方法效果分别验收，格式等价的候选不能直接计作技能改进。
- **验证**：同一禁网镜像 debug rg 搜索由缺工具 exit1 变为固定 hash 的只读 rg 挂载 exit0，零模型。原生字段摘要诊断一次生成后通过官方三字段及外层提案验证，但 diff 只有末尾换行变化；不据此认定学习收益，也不声称完整原方法复现。
- **证据**：[近邻接入记录](../../research/agent_frontier_portfolio_20261029/IJCNN_RELATED_WORK_REFRESH_20261030.md)、[现役研究计划](../../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)、[离线工具探针](../../scripts/graph/research_tool_runtime.py)。原始请求、响应和 paired 工具日志保存在对应 GB10 私有证据目录。

## C-5 研究入口按需加载与宿主搜索（2026-11-06）

- **现场问题**：现役第二阶段计划累积超过100KB，STATE/THREADS又复制实验过程；规则仍强制旧搜索CLI，容易让接任Agent误读历史状态或多次加载同一证据。
- **对策**：STATE只留恢复定位、THREADS只留未决，短计划仅承载当前比较和下一步；逐轮过程按主题分段归档、链接按新基址重定位，保留可逆映射与原文hash。科研默认宿主原生搜索，禁网执行层由D提供带来源材料；不臆造HTTP地址、不自动回退DeepSeek/Qwen搜索。
- **验证**：上下文检查覆盖7份活文档的UTF-8字节、总额与本地链接；历史分段可逆重建。已启动Astropy输出只读收录，没有为整理重跑模型。文件绑定和索引通过不当成方法确认。
- **证据**：`scripts/graph/research_context_check.py`、`docs/archive/2026-11-06_agent_research_context/MANIFEST.json`及同目录README；现役搜索规则在`graph-loop-rules`和唯一Loop D入口。

## C-6 同候选续修的执行要求与反馈边界（2026-11-06）

- **现场**：Django8B源执行8次请求后正常退出，但未运行测试，最终询问是否继续；实际补丁引入格式化TypeError与42项回归错误。正常退出不能算修复成功，也不能据未收到反馈的运行判定“反馈利用失败”。
- **对策**：续修N/F共享完全相同的真实候选、题面、模型/工具/预算和“实际运行相关测试、无需重复请求内部执行许可”的要求。F仅增加本候选的真实错误及应用代码栈，不给隐藏测试断言、参考补丁或目标信息；源/目标与经验形成分开记账。
- **验证**：单测核对候选字节相同、两臂prompt仅差真实反馈、快照/日志篡改拒绝。执行要求可能改善闭环，但是否改善语义修复仍须真实N/F结果判断，不把prompt修订当方法收益。
- **后续边界**：第一轮N/F均试改只读题面而非源码。一次资格复验向两臂同样说明题面只读、源码可写及评测路径映射，不提供待改函数/修法；仍失败则改用可靠教师，不继续以提示变体凑方法证据。该环境说明不是学习方法。
- **复验结果与教师切换**：8B复验N误把零测试当成功，F重复27次不匹配编辑且破坏语法，停止本候选提示变体。35B源轨迹资格沿用冻结题面/base，仅补通用只读题面/可写源码/自主测试说明；教师身份、不同上下文与输出上限显式记录，未经独立原题及回归验证不当成功经验。切换不是8B对35B的等预算因果比较，也不是反馈普遍无效。
- **教师续修**：35B修对原题后扩大原有公开测试发现SELECT计数回归。教师续修从真实work冻结候选，绑定父源、实际diff与新增回执/hash；该公开测试原本在actor base中，可提供真实失败栈和自身前次删改，不能附gold修法。隐藏测试的反馈边界不因此放宽；原题/局部通过与更广非回归分报，续修不是新方法确认。
- **联合目标对照**：单项反馈续修恢复原bug后，联合基线仍从同一父候选出发，再明确须保持其已通过的原题/关键检查。原题probe捕获异常后可exit0，必须检查observed语义结果。该对照属于强简单基线，不能把“提醒两个目标”包装成新方法。
- **长输出与客户端等待**：教师联合首启13POST但只有12个usage步骤，第13次在300秒客户端期限退出、没有完成编辑。教师隔离harness等待设900秒，仍受1200秒episode与48POST总门约束；同题面/反馈/候选重跑，未知usage单列。该工程故障不裁决方法；不改共享模型服务，8B计时不变。
- **反馈可执行性**：源训练反馈引用的检查须在隔离副本中可定位/运行，目标隐藏评分不因此公开。[Django源纠正](../../research/agent_frontier_portfolio_20261029/results/FCCL_FORMATION.md#formset-source-v1)6请求耗于搜索未挂载测试；按源训练方案交付同一可执行检查后12请求完成3/3＋49/49。提示/预算共同改变，全成本保留，不作单因素收益。旧Django入口不支持`--parallel=1`时沿实际版本去掉该参数，保留原失败。
- **证据**：[Django本批记录](../../research/agent_frontier_portfolio_20261029/results/DJANGO_AGGREGATION_AGENT_20261106.md)、`2b01d3d8`源代码及私有`runtime_ready_8b_20261106`的原始raw/独立评测；后续结果在同一批次原地更新。

## C-7 复用现有教师与固定迁移输入（2026-11-06）

- **问题**：已有27B HF/vLLM服务不能用35B GGUF进程校验或64K参数替代；只检查源任务窄面板曾放过实际回归。源经验形成完成前若先看目标结果，会污染载体选择。
- **对策**：教师profile分开绑定真实权重清单、服务、模板、原生上下文/输出和运行余量；不重启共享服务。真实源产物接受原题和已核回归的联合检查。历史、补丁卡、skill在目标前冻结，所有目标臂（含无历史）绑定同一来源；无历史绑定仅留D侧。形成、失败及使用成本分账，记录实际经验读取。
- **验证边界**：零生成base/gold联合验收反例、模型/端口/manifest篡改及同来源绑定测试；真实教师和学生效果仍须执行后判断。D可按既有本地资源授权调整新批运行余量，不将工程上限、单个候选停止或文档完成当科研目标完成。
- **长连接与真实反馈**：vLLM首轮156个usage步骤却仅首POST被代理计数，源作废并保留未知请求用量；新relay每响应关闭连接、逐请求保存私有body并核对计数。工具失败的`state.error`须进入新普通历史，旧载体按版本保留原字节；否则“经验无效”可能只是反馈丢失。
- **内部调用与配置**：公开step少于HTTP可来自压缩/失败调用，不等于超帽；反向多于HTTP才否定完整计量。保存SSE/provider usage，未知单列，不能与step tokens相加。推理开关按请求kwargs核实；客户端和桥接等待一致，单个任务不产补丁先做配置资格，不能包装为方法负结果。
- **经验迁移载体**：source只按其已归档快照、实际diff/反馈生成；目标前固定历史/卡/skill，全臂绑定同一manifest，无历史只作D侧绑定。跨任务函数适配须核对实际派生harness的模型/seed/任务/评测节点，不修改原模块全局、不沿用源任务的测试数。目标资格不是目标actor结果。
- **27B写入通道**：vLLM非流式请求仅靠模板默认关闭thinking，曾将606字符的技能放入reasoning、content为空；不是截断。原始失败保留，新attempt显式`chat_template_kwargs.enable_thinking=false`后final content正常，不把reasoning搬成答案、不盲目扩输出。已知baseline环境失败应同时告知所有目标actor，不能只在评分器里排除。
- **经验交付而非路径提醒**：SymPy三经验臂有读取提醒但真实read/请求正文均无经验内容，不能解释为内容无效或负迁移。新诊断将同一冻结skill显式注入首轮用户上下文，绑定交付模式/内容hash并核实实际请求；原文件式结果和默认配置保留。显式注入的效果仍须真实语义验收，不能靠prompt字符串测试认证。
- **证据**：[Django当前合同](../../research/agent_frontier_portfolio_20261029/results/DJANGO_AGGREGATION_AGENT_20261106.md#current-27b-handoff)、`research_teacher_backend.py`、`run_django_aggregation_agent_20261106.py`与对应测试；私有评测控制receipt `11b8ef99fc16255733eb754934fcf57115320d165f82099dc77091d077f98f8a`。

## C-8 非代码环境的动作与观察边界（2026-11-06）

- **风险与对策**：家居任务不能将私有PDDL、专家动作或初始缓存误当actor当前证据。任务prompt说明单条client动作、逐次读实际返回、look也计步、reset快照仅为初始缓存；OpenCode实际只暴露bash，游戏/专家/轨迹留在D侧，环境won决定成功。
- **已验证范围**：两游戏专家通过真实UDS动作及Docker隔离控制；28项远端契约测试与30个subtests通过，owned fake端口的两backend模拟各2假POST/1原生look，标为MOCK_ORACLE，不冒充模型经验。27B请求显式关闭thinking，保存逐请求/响应和未知usage；终态后请求、非法参数和结束竞态有确定性控制。真实模型任务另记结果。
- **资源和来源合同**：8B真实episode在响应字节门终止，扩源专家有85步；新批显式绑定pool/archives/game与实际POST/秒/动作/byte caps，并传到relay/world。上下文大小是另一个约束，不能把byte余量当模型token余量。新pool的20tests/33subtests及原生reset预检通过；旧reserved根和原预算不追改。
- **源经验与首轮交付**：公开任务、raw text/tool的input/output/error及world终态形成载体，不用PDDL/专家代替实际经验。普通skill单次生成并计量，先冻齐再跑目标；none仅D侧同源绑定，其余完整内联，并核对首个实际forwarded请求。形成入口查target reservation，冻结后的只读验证不再受该门阻断。37tests/56subtests及五臂零模型预检通过；交付验证不等于理解或迁移成功。
- **SDK编码与思考通道**：实际OpenCode把task包双引号并转义内部双引号；整串可逆且task hash相符时是完整encoded delivery，raw substring失败不能叫未交付。旧标签由sidecar更正。8B末次动作曾只出现在reasoning、无native tool_calls，不自动搬运；新诊断只显式关闭student thinking，默认原请求保持。39tests/63subtests与owned fake验证编码、native kwargs，真机语义结果另记。
- **通道资格不等于任务成功**：真实nativeFalse诊断62个forwarded payload均为false，SSE无reasoning且有60次native工具调用，仍拿错对象并提前结束；不能继续归因于旧通道故障，也不要求无经验先成功才允许经验比较。同冻结源的三经验条件随后补齐；真实失败状态的教师纠正须单独重放验收，不用从reset成功替代。
- **失败前缀与新对话**：恢复器只重放有hash的实际world动作并逐state核对；fresh-session不冒充原对话恢复。公开投影保留goal/动作/完整观察，只省去历史commands，末态保留全commands；两臂同额剩余cap，重放动作不算actor新动作，旧形成成本不重复计。原生模板资格须计input_ids，不能把BatchEncoding的键数当token；vLLM工具arguments的离线投影不改变forwarded payload。真实纠正资格仍看world won，不看mock成功或最终文字。
- **原会话不是文本回放**：只复制私有actor的DB/WAL/SHM并在副本checkpoint；原文件hash不变。实际首个续接请求须保留旧user/源载体、全部原tool call参数/反馈及末次assistant，不能以DB存在替代交付验收。普通续做失败后才追加同公开state；环境won而非新final决定完成，原source成本只计一次。8B离线模板计数与provider可有小差，复核真实usage与余量；新4B双臂共用client alias、同精度/模板/环境，零adapter工具控制与接入资格不等于学习效果。
- **多任务续做对照**：新任务与经验分配先冻结，fake来源不得进入真实恢复；四臂共用同一collector/hash及剩余额度，world总动作帽不随收集POST帽缩小。所有条件统一原会话最多一次中性续做并分报首停/最终won。复用旧qualifier/replay须按实际字段适配，原绑定与代码保留；来源预算截尾不写成自然失败。新通用study/pool的真实隔离fake闭环为3假POST/1look/1续做，22tests/99subtests通过；实际模型结果另见ALF记录。
- **纠正监督资格**：保留实际请求/响应的原始schema顺序和锚，不从reasoning生成答案；仅当前assistant＋EOS算loss，prompt/tool输出及EOS后换行mask。模板逐token对齐；JSON递归sort_keys会改变schema呈现，新导出保序并验序列化往返，旧已核数组不因写出修复重训。小步LoRA还须验base未变、adapter保存重载、匹配精度/模板；训练与同prompt生成资格不作heldout任务收益。
- **证据**：[ALFWorld记录](../../research/agent_frontier_portfolio_20261029/results/ALFWORLD_TEXT_AGENT_20261106.md)、`scripts/graph/research_alfworld_bridge.py`、`tests/test_research_alfworld_bridge.py`、`tests/test_alfworld_actor.py`。

## C-9 Source actor 的唯一工具与实际发送说明（2026-11-08）

- **确认的冲突**：两道代码source实际只开放bash，其发送给模型的说明却禁止文件读写/编辑/搜索，并指向未开放的专用工具。两题各48动作只读/搜索、47轮后继反馈完整、首user完整；这些事实未证明合同冲突导致过去循环，也不裁决反馈学习效应。
- **最小对策**：仅source入口在实际序列化、字节帽、预留和转发前深拷贝payload，将唯一bash说明改为可在隔离`/workspace`读、编辑和运行测试。函数名、参数schema、messages、sampling及其他字段保序保值；缺失、重复或未知工具明确拒绝。私有ledger绑定incoming/forwarded工具hash及实际body hash；新manifest显式绑定`contextbench_source_bash_v2`，旧attempt/raw/失败状态/费用不改、不复用旧reserved根。不扩大ALF或生产工具面。
- **验证边界**：假socket核实际forward body、字节帽/hash顺序、深拷贝及非法工具零转发，GB10聚焦57项通过。另一次独立4POST/120秒/2MiB接口控制实际用2POST/25.77秒/56,724bytes，原生bash写入读回28bytes完全匹配；D再核19绑定、两份原SSE费用和容器清理。只证明本次写入通路，未证明合同冲突是旧循环原因，未重跑SWE题目。旧96POST及失败费不重置；新接口控制5,494tokens另账，cache未知。
- **证据**：[现役source工具合同记录](../../research/agent_frontier_portfolio_20261029/results/ALFWORLD_CORRECTION_DATA.md#source-tool-contract)；私有尸检SHA `52b958f5b39914c37017824e356ba9d56555a9b37907d7f30ad26311ebdb5727`、`TOOL_CONTRACT_V2_CANARY_V1/receipt.json` SHA `b8e914788bcaccf6aab7cc4dd639787993095b1648e1c28b9d41dd733d73ecaa`，以及`run_contextbench_source.py`与其测试。仓库版本为权威，安装分发另核，不由Git同步推断。

## C-10 新任务派生须保留工具与副本可写性（2026-11-11）

- **已实测失败**：异步任务恢复v1的4次glob因未挂载既有rg失败；v2已生成write动作，却因宿主复制的0644文件不可写而被拒。root在`--cap-drop ALL`容器中不自动拥有宿主文件写权限。两次失败与费用均保留，不算模型或经验方法失败。
- **对策**：新任务优先从现役已验证派生入口接续；保留`research_tool_runtime.ripgrep_binding()`及已有副本权限处理。需要编辑的宿主副本应在隔离目录中具备实际读写权限，保持可执行位；恢复prompt准确说明已有文件。历史98行base为冻结材料，不能省略后来补齐的依赖与权限。原始实验和raw不覆写，不因接入修正重置费用。
- **验证**：新镜像原生OpenCode搜索命中`run_tasks`，无DAC override容器写入控制通过；v3真实write成功，原题仍5/6。工具可用与科研收益分开，不增加每轮全库资格流程。
- **证据**：[异步原始反馈节点与回执](../../research/agent_frontier_portfolio_20261029/results/CODE_SOURCE_CORRECTIONS.md#async-feedback-decision-node)，`research_tool_runtime.py`及现役`run_swe_contextbench_sympy_20261104.py`的副本权限处理；私有v1/v2/v3脚本及完整SSE保留。
- **规划交付补充**：后续两个4请求规划耗于读取/空搜索，没有最终JSON；一次原生OpenCode控制内联同样公开文件并关闭工具，1请求形成合法计划，但全部假设归同一粗行动、未执行探针。格式交付与决策有效性分开，不能仅因schema合法推断无需取证；呈现/工具同时变化不作单因素归因。派生评分器须保留全部bind源，即使当前分支未用；本次缺文件只重评保存代码，原exit125保留。[对照证据](../../research/agent_frontier_portfolio_20261029/results/CODE_SOURCE_CORRECTIONS.md#async-decision-comparison-result)。
- **Python入口补充**：SymPy16988源预检误用镜像默认Python而缺distutils；同一镜像内已有的资格运行实际依赖Python3.8挂载、PATH和入口三者。派生时一并继承，不从镜像名推断解释器；修正前后CPU预检及旧脚本保留，预检零模型。后续普通接续通过既定2+72项，不代表更广符号语义正确或新方法有效。[来源/接续证据](../../research/agent_frontier_portfolio_20261029/results/CODE_SOURCE_CORRECTIONS.md#sympy-source-continuation)。

## C-11 可调用纠正技能的验收与退出（2026-11-12）

- **实测失败**：源内技能调用和公开检查均通过后，Actor继续读源码并尝试不可用的编译依赖，8次请求触帽；保存的候选原题/回归通过，不改计为正常完成。
- **对策**：技能返回绑定到既定公开验收的退出信号（如`next_operation=STOP`），任务说明验收后应结束；编译不在当前合同内时不额外要求编译。此退出规则也须给简单基线，不作为学习方法独有优势。
- **验证与边界**：条件修订和退出说明同时更新后，新会话3次实际请求正常结束，原题1/1、回归54/54；两轮全部11次费用保留，不把8→3归因于单一改动或独立迁移收益。
- **证据**：[生成、反馈更新与OpenCode实际调用](../../research/agent_frontier_portfolio_20261029/results/FCCL_FORMATION.md#execution-fragment-v1)。

**11-13协作环境补充**：OpenCode最终文字不会自动发送给世界中的用户；DEV无历史组虽exit0，原生会话仍未终止。后续各组统一允许一次同会话续行，包含在原预算内；不能只给新方法额外重试。续做三组均原生通过，但不是该退出修正的独立因果对照。另，“第一条工具操作运行程序”只是提示：三程序组实际先读文件，再执行程序；未逐动作核验前不能写成硬执行保证。证据：[实际轨迹、统一续行与未完成组](../../research/agent_frontier_portfolio_20261029/results/CONTINUATION_PROGRAM.md)。

## Completion and verification

修改prompt后交付变更原因、实际核验命令/结果和仍未验证的边界；引用固定证据版本。静态控制通过不代表真实模型或harness运行通过，未授权工作保持未执行身份。
