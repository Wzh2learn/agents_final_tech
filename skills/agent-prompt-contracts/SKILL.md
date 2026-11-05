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

## Completion and verification

修改prompt后交付变更原因、实际核验命令/结果和仍未验证的边界；引用固定证据版本。静态控制通过不代表真实模型或harness运行通过，未授权工作保持未执行身份。
