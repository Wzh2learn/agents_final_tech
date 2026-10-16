# 总规划师裁决与资格核验契约 v1

日期：2026-10-15。授权依据：用户要求“先拍板，然后把人工裁决的标注和数据都构建起来”。

## 裁决

批准 TASK_GOLD_QUALIFICATION 的材料准备和独立人工标注流程；未批准 Layer-2 实验、模型调用、训练、改稿或对外发布。首先归属 Paper E 升级线；只有经人工核验的证据才可提议供大论文复用，未自动获得训练/反馈使用权。

本包不修改 Loop D 既有解释文件，但明确收紧两处残留表述：v4 建立的是可复现词法绑定代理标签，不称“独立 binding gold”；10/11 是规则赋予 E 的数量，不称已证实合法。源列位置真值、算法绑定预测、任务语义正确性分别记录。

## 测量对象

本轮单位为一个真实 TAT-QA 问题 + 来源表/上下文 + 已冻结的全注入表/相同上下文。目标是验证：原任务的有依据答案（含单位、时期、对象与所需证据关系）在扰动材料中是否保留。

不测模型输出正确率，也不测人类首次答题正确率；没有实际系统输出时，不产生系统漏检/误报结论。未来若评价实际系统答案，必须新增 system-output 评价对象与独立参考答案契约。

使用全注入表，不合成“单扰动”新表。多处表头同时变化时，裁决属于整个表格条件，不能归因于某一个注入。问题中未涉及的表头改变可以不影响本题。上下文中真实冗余信息允许用于作答，不能为了制造有害案例而删除段落。

## 来源与选择

静态来源取回自 GB10 /home/testuser/wzh/projects/agents_final_tech/；SSH/SCP 为读取与传输，不是实验，不宣称零网络。原始三文件须与 v4 契约 SHA256 相同，原始 QA 两文件须与 2026-10-13 FETCH_RECEIPT.sha256 相同。

样本池为已公开 v4 的 59 个 injection-level 条目。设计者已经见过历史输出；本次不宣称设计者盲态或确认性预注册。选择函数只读 injection_id/uid/type/原始表头，不用 label/reason/binding/checker_verdict/距离/官方答案选择样本。

首批固定 12 个任务、12 张不同表，四个输入结构层各 3 个：S1 来源表首行仅一个非空字符串；S2 非 S1 且 ocr_similar；S4 非 S1 且 date_variant/unit_suffix；S3 非 S1 且 alias_variant/mixed_lang。其余为储备。非空按 strip 判断，不重新运行 v4 norm。这些层是输入类型，不预断语义是否改变，也不保证四种语义现象都存在。

按 S1/S2/S3/S4 顺序，各层按 SHA256(injection_id UTF-8) 排序，取此前未选表 UID 的前三项。若不足则记录覆盖缺口，不借标签改选。

每表选一个原始 table/table-text 问题：按原表头与问题的英文词集合交集数降序，再优先 arithmetic，再按原 question order/uid 排序。仅做问题关联启发式，不认证该题确实依赖变化列。词集规则见 coordinator/selection_policy.json；不使用答案/derivation/标签排序。若候选问题缺失则停止。所有题保留原文，不新编问题。精确表相等和唯一 UID 关联为必需条件。

## 两阶段人工流程

每人只接收属于自己的 exports/R1_stage1 或 exports/R2_stage1。阶段 1 仅含问题、完整扰动表、完整原始段落；不含原表、官方答案/derivation、变化位置、checker/v4 标签、选层理由。两位独立作答，记录单元格与段落依据、单位/时期、不可答或不确定原因及耗时。

两人全部 stage1 提交后，由协调者保存原始提交字节并记录真实 SHA256 与接收时间，再分别发 stage2；不能预填封存哈希。stage2 给原表、官方参考答案/derivation/scale 和完整扰动表。两人先验证官方参考是否可信，随后独立判断任务证据是否保持。标注者不得看对方答案；协调者不得提供 v4/checker 标签或期望结论。

目录隔离不是安全访问控制；发放时只复制对应 exports 目录，不把整个仓库或本包给标注者。提供 stage2 早于两人 stage1 封存、或看过旧标签，必须记录盲态破坏，不能伪称独立。用户/研究者已见旧汇报不自动具备盲态，需真实声明。

## 判定字段

reference_status：CONFIRMED / QUESTIONABLE / INSUFFICIENT。官方答案是待核验参考，不是自动 gold。reference_status 非 CONFIRMED 时 task_effect 为 UNDETERMINED；官方错误单列，不擅自改写原数据。

task_effect：
- PRESERVED：原任务有依据的答案及单位/时期/对象/必要证据关系在扰动条件下仍成立；须列具体证据，不能只说数值未变或猜回原表头。
- ALTERED：能用证据说明答案、单位、时期、对象或必要证据关系改变，或关键证据丢失使原答案不再可被唯一支持；须明确改变点、竞争解释/冲突或缺失。它是任务证据受损，不等同已观测模型失败。
- UNDETERMINED：资料不足、参考未验证、语言/领域不熟、歧义无法裁决、标注者不一致未解决。不能把“我没答出来”当作 ALTERED。

另记 perturbed_answerability = ANSWERABLE / UNANSWERABLE / UNCERTAIN，change_relevance = RELEVANT / IRRELEVANT / UNCERTAIN；不能用这两个字段自动派生 task_effect。阶段 1 答错也不能自动推出 ALTERED，阶段 2 必须区分人类计算错误与材料语义问题。

数值比较先核验单位与 scale，再看推导；不得统一四舍五入到整数。标注者记录原值、推导和被参考精度支持的容差；无依据不得自行放宽。字符串同义性须人工给依据。表格坐标统一 0-based，r0 为第一行；段落按原 order/uid 引用。

## 人工资格、预算与退出

两名真实人类独立标注，能阅读英文财报表格及包内中英混合表头，具备基础财务/算术判断能力。模型或 agent 不得填入人类身份、标注或签名；可协助机械检查。协调者登记经验、利益/盲态声明。第三人仅处理分歧，确实无人可仲裁时保留 U，不伪造第三人。

首批 12 case × 2 人；每人每 case 两阶段合计建议不超过 15 分钟，到限记录 U/原因，不强迫给答案。基础标注约 6 人时上限，协调/核对约 1 人时、仲裁约 1 人时，总规划上限 8 人时（预算，不是实际消耗）。不得为了凑 E/H 数量替换、扩大样本。人员不可用则停在 AWAITING_HUMAN_ANNOTATION。

## 资格判定——不由 U 单阈值签发 PASS

产物状态仅能从 MATERIALS_READY_AWAITING_HUMANS → ANNOTATED_PENDING_SCIENTIFIC_REVIEW → QUALIFIED_FOR_LAYER2_DESIGN / TASK_GOLD_NOT_VALIDATED / INCONCLUSIVE。

必要条件：24 份真实独立两阶段记录、真实封存、问题/来源关联可追溯、参考核验与证据坐标充分、所有冲突有独立仲裁或保留 U、无循环 gold、任务边界明确。逐层报告分歧/U/耗时及原因，不能把高一致率当语义正确性证明。

没有自动 PASS 阈值。第三位科学评审需逐例检查证据是否足以支持最终标签，并签署哪些任务范围可评价、哪些不具备资格。若标签都 PRESERVED，可能是当前问题不受扰动影响，不得制造 ALTERED；当前面板不支持比较有害漏检。若语义覆盖缺失、同一定义反复无法适用或仅靠猜测，结论 INCONCLUSIVE 或 TASK_GOLD_NOT_VALIDATED。

“资格通过”最多允许提交 Layer-2 设计供裁决，不自动启动实验。Layer-2 预算仍为 UNRESOLVED，未授权。

## 回滚与既有停止状态

新包独立保存；解释不获支持可退回诊断材料，保留全部记录。旧 v1-v4、冻结稿、WP-2/TAT-DQA/FinQA 停止状态不动。新样本不得直接进入大论文训练/记忆/反馈；未来独立评测需按表/报告来源隔离，报告级 ID 不明的地方标 UNRESOLVED。
