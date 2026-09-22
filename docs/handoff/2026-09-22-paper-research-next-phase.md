# 小论文—大论文科研下一阶段执行计划与 Agent 交接 v1

> 状态：`0aee20d` 已 fast-forward 到 main；GB10 验收因 skill 安装漂移、隔离数据缺失和零端点违规而停；Phase 1a/2 未启动

> 更新：2026-09-22

> 接收方：后续负责科研实验、证据审计和论文写作的 Agent

> 当前分支：`test/compaction-guard-abort`

> 叙事权威：`paper/research_story_v2.md`

> 公开边界：专利状态确认前不得投稿、上传预印本或公开核心代码

## 0. 执行结论

本文件是唯一下一阶段执行计划；分层权威与冲突裁定见 `docs/research/README.md` §1。第一轮治理及 P1 本地审计已交付，导师包内容核对已修正；审计结论见资产账本 §3.1，阅读回执见 `paper/teacher_review_readiness_v2.md`。用户最新要求：保留测试代码和已有局部结果，不继续本机跑测试，剩余测试及 Office 视觉核对交服务器；所有后续实验仍待批准，不对外送稿、不另建计划。

既有阶段顺序如下（P1本地审计已完成，其余实验待批；不是自动派发队列）：

1. **Phase 1 先审计数据。** 还原 checkpoint、规则候选与门控标签的 provenance，按源表 uid 分组去重，报告独立样本、冲突和四层数据边界。
2. **Phase 1a 再做零端点可学性探针，Phase 2 补规则强基线。** always-skip、deterministic matcher、lexical/fuzzy、confidence-only、简单分类器回答“为什么需要小模型”；共享候选流上的七类规则门回答确定性安全门的增量价值。
3. **通过离线门后才申请训练窗口。** 4B 仅做训练链 smoke test，8B 是主学生；GGUF 不能当训练底座，先核验可训练权重、许可、显存和 LoRA/QLoRA 环境。数据不足只能申请明确标注的 smoke/pilot，不自动升级主实验。
4. **近期只做动作策略蒸馏/规则候选蒸馏。** 学生提出 `map_to / skip / hold`、目标字段并做验证预筛，不替代最终确定性门；拟建的 gain–collateral + 独立 gate-validation 门和版本化回滚仍须实证验收，不能写成已经闭合。
5. **随时执行止损门，而非等满三周。** 数据仅 `PILOT_ONLY`、简单规则已解决问题、非劣失败或安全回归时，立即转评估保底稿内部交导师，D/R 留给大论文；专利公开门未通过前不投稿。

A+C 双轨不互相阻塞：24–48 小时导师方向包 = 成熟评估稿 + 当前三阶段方向说明；实验完成后的统一论文初稿是另一交付，不能用方向包冒充三阶段结果。所有 null/adverse result 原样保留，不改 split、阈值、家族或容差救结论。

**技能路由**：每张卡按 `docs/SKILL_ROUTING.md` 选 ≤5 件，红线常备 `graph-loop-rules` 不占配额。历史治理批的装载记录留在 Git，不作为后续 Agent 自动装载或联网扫描许可。

### 0.1 第一轮治理的四个完成面

| 面 | 本轮修正与验收要求 | 权威落点 |
|---|---|---|
| 文档关系 | 入口、故事、资产、导师材料、唯一计划各司其职；旧路线/台账不再派工 | 科研入口、INDEX、导师说明与大论文骨架 |
| 代码资产 | 区分生产/科研、输入/输出、纯函数/在线入口；修复生产 MCP helper 分类和无效泄漏断言 | 代码地图、资产账本、catalog 与定点测试 |
| 科研进度 | E 成熟、D 未训练、R 机制级；494/60 的独立单位、冲突和单向偏好不被淡化；图/生成器/Word 同口径 | 现有故事/账本及原始 JSON；静态验收不冒充研究结论 |
| harness 协作 | D/A/B/C 责任、任务授权与执行面关联；watcher 预检校验绑定脚本的真实收据合同，不认任意非空文件 | docs/17、docs/29、A/C prompt、任务模板和预检测试 |

本轮完成以这些仓内修正和新鲜离线验收为准，验证结果只记 `memory/STATE.md`，剩余事项只记 `memory/THREADS.md`。另一台服务器的环境、原始语料、权重、调度及安装状态由用户明确排除：本轮未核验、不获取、不修复；缺少本机副本不是本轮失败。Office 视觉验收也不由 DOCX 结构测试代替。**治理闭环不等于 Phase 1 数据审计、训练完成、Loop B/C 生产验收或完整论文闭环。**

## 1. 为什么这条路线价值最高

### 1.1 当前真正的瓶颈不是文字，而是 Stage D 没有实验事实

Stage E 已有 95 张表、118 个受控注入、分层检查点、阈值/匹配器/seed/matched-FPR 审计和验收后的英文子稿。继续扩写同类评估文字，边际价值已经很低。

Stage R 已有候选生成、确定性规则固化、对抗/碰撞工件和回滚思想。它的问题是强基线和功效不足，而不是完全没有机制。

Stage D 只有训练前模型矩阵、蒸馏文献和偏好对，没有学生训练结果。完整三阶段论文能否成立，主要取决于 Stage D 是否获得可信、未泄漏、可复现的证据。

### 1.2 直接训练会浪费窗口

2026-09-22 从本地原始 JSON 机械复算（不运行实验生成器、不调用模型），结果如下：

| 口径 | 实测 |
|---|---|
| `logs/graph/eval/vgmc*_checkpoint.json` 文件数 | 16 |
| `arm_gated.sugg_log` 中 gain/collateral 均非空的事件 | 494 |
| 上述事件的唯一源表 uid / `(uid, col)` / `(uid, col, target)` | 48 / 94 / 139 |
| accepted / rejected | 292 / 202 |
| 同一 `(uid, col, target)` 同时有接受/拒绝标签 | 16 组 |
| 同一 `(uid, col)` 对应多个 target | 41 组 |
| `logs/graph/eval/dpo_pairs_v0.json` 实际 pairs | 60 对，36 个唯一 uid，60 个唯一 `(uid, col)` |
| 偏好方向 | 60/60 均为 chosen=`skip`、rejected=`map_to` |
| 正向偏好 map_to 的 Type-B / gate_fooled | 0 / 9 |

494 **不是所有动作**：16 文件的 gated 原始日志共 625 条，另有 126 条 `no_map`、5 条 `target_not_canonical` 无完整 gain/collateral，不进入上表 494 分母。它们仍须在数据审计中解释，不能把 `no_map`（可能含 parse_fail）自动标成正确 skip/hold。DPO 的 62.5% 仅为生成器原 96 列口径下 60 列覆盖率，不是独立表覆盖率；类型计数 A=50、C=51 有重叠，不可相加当样本数。

checkpoint 文件清单按相对路径排序，将每行 `path:sha256` 加换行后串联，再取 SHA-256，得到 `9b4bc0e63b4a5964d66648337e7d0f23d40d5fa2f4df597d8b60eae4f6cbd6c6`；DPO 文件 SHA-256 为 `20b09efd154862580cdaf1c9ef55311ec9fab4c8bb0373d0438965e0a116ae37`。Phase 1 必须把复算和稳定 hash 写入审计测试，工件变化不能静默沿用这份快照。

冲突可能来自 regime、规则版本或候选上下文变化，未完成 provenance 重建前不多数投票抹平。门接受不等于动作正确（`gate_fooled=9` 已是反例）；风险标签须以独立正确性证据核验，不能训练一个照抄门标签的模型。

DPO 的问题不只是小，而是偏好方向单一，直接训练可能学成“永远 skip”。A3 保持条件臂；现阶段更可能得到 `PILOT_ONLY`，不是已取得 `DATA_GO`。本次复算不等于完成 Phase 1 的 split、标签和功效审计。

小模型矩阵只有 16 道 QA（8B-xhigh 15/16，4B-off 14/16），只算训练前能力探针；bandit replay 各阈值臂奖励均为 1.0、前瞻与固定门相同，只保留无分辨力结果。因此必须先证明“数据足够且任务值得学习”，再占用训练资源。

### 1.3 最有价值的小模型角色不是替代确定性门

若把 gain 和 collateral 直接作为小模型输入，再让模型学习现有阈值门，任务会退化成复制一条确定性 `if` 语句，没有研究价值。若让小模型直接取代最终验证门，又会削弱现有安全边界。

推荐角色是：

1. **候选提出器**：根据表头、标准字段和局部 checkpoint 证据生成 `map_to / skip / hold`。
2. **验证预筛器**：在执行独立 gate-validation 验证前，预测候选的效用和风险，减少无价值的昂贵验证。
3. **最终门不交给学生**：持久化规则由确定性 gain–collateral 门及待补的独立 gate-validation 验收，写入版本化规则记忆；回滚须有冻结条件和重放证据，不声称现有脚本已完成全部机制。

这样 Stage E 负责产生监督信号，Stage D 负责低成本迁移，Stage R 负责安全积累，三条线才是因果相连，而不是三段素材拼接。

## 2. 路线比较与裁定

| 路线 | 近期导师交付 | 与用户原方向一致 | 复用现有资产 | 新实验风险 | 裁定 |
|---|---|---|---|---|---|
| A. 只继续评估稿 | 高 | 低 | 高 | 低 | 保底，不作为主路线 |
| B. 直接做通用 Agent/QA 蒸馏 | 中低 | 表面高 | 低 | 很高 | 不采用；任务过宽且 16 题基准不够 |
| C. checkpoint 引导的规则候选蒸馏 + 确定性固化门 | 高 | 高 | 最高 | 中，可分阶段止损 | **推荐主路线** |
| D. 先做 bandit/PSO/视觉补盲 | 低 | 低到中 | 中 | 中高 | 暂缓；已有 null 或前置阻塞 |

执行上采用 A+C 双轨：C 负责争取完整三阶段论文，A 始终保留为近期导师交稿和拆稿退路。

## 3. 推荐论文故事

### 3.1 一句话问题

长流程大模型产生的轨迹既昂贵又含有不可见错误；未经审计的蒸馏会把错误迁移给学生，未经验证的自学习又会把错误永久写入规则。本文研究如何用过程级评估同时充当蒸馏数据过滤器和规则更新安全门。

### 3.2 核心洞见

同一套 checkpoint 证据承担三个职责：

1. 发现教师轨迹在哪一步可靠或失效；
2. 选择哪些过程/动作可用于训练小模型；
3. 判断学生或教师提出的规则能否安全持久化。

内部仍可用 E–D–R 表示三阶段，但投稿前不要急于再造新缩写。VGRM 仅保留为规则固化模块名称。

### 3.3 小论文研究问题

沿用 `paper/research_story_v2.md` 的 RQ 编号；评估子稿的 SP-RQ* 是另一命名空间，不把其中 SP-RQ2 当作蒸馏主张。

| RQ | 问题 | 最小证据 |
|---|---|---|
| RQ1 | 哪些长流程错误能被 checkpoint 协议可靠观察？ | 现有 95 表/118 注入与协议审计 |
| RQ2 | checkpoint 过滤是否改善学生规则动作学习？ | A1 vs A2 两种公平口径、按 uid 聚类；A2 vs A3 是独立判门的条件消融 |
| RQ3 | 提出的规则能否安全积累与回滚？ | Phase 2 七类门基线，Phase 5 规则快照与回滚验证 |
| RQ4 | 学生预筛 + 确定性固化门能否改善质量—成本—风险权衡？ | 冻结系统闭环对照，sealed test 只读终评 |

### 3.4 小论文与大论文的边界

- **小论文**：一个教师、一个 8B 主学生、一个公开表格域、一次最小 E–D–R 闭环；4B 仅为训练链 smoke，不承担论文效果比较。
- **大论文**：多教师/多学生、跨数据流、学习门、长期规则演化、外部效度和更强理论保证。
- 小论文不承担通用 Agent 蒸馏、任意长流程普适性、规则长期单调增益或跨领域泛化。

## 4. 可直接复用的资产

### 4.1 评估底座

| 资产 | 用法 | 处理 |
|---|---|---|
| `paper/teacher_review_draft_v1.md` | Stage E 成熟方法与结果 | 压缩后并入完整稿；原稿保留为拆稿备选 |
| `logs/graph/eval/checkpoint_discrimination_tables_v2.json` | 95 表、118 注入、六家族可见性 | 作为 RQ1 主证据和数据分层依据 |
| `logs/graph/eval/t1_eval_baseline_comparison.json` | end-to-end/flat/hierarchical 对照 | 保留 null，不写 hierarchy 更敏感 |
| `logs/graph/eval/d2_cross_matcher_*.json`、`logs/graph/eval/d3_*.json` | scorer/matcher/FPR 边界 | 放稳健性或附录 |
| `docs/experiments/figures_paper/fig_checkpoint_trees_v2.svg` | checkpoint 方法图 | 可直接复用，投稿前统一字体 |
| `docs/experiments/figures_paper/fig_visibility_spectrum.png` | 可见性主结果 | 可复用；优先重生 SVG/PDF |

### 4.2 蒸馏准备资产

| 资产 | 用法 | 当前边界 |
|---|---|---|
| `docs/experiments/2026-09-20_kd_literature_candidates.md` | KD/Agent distillation 相关工作种子 | venue 仍须逐条复核 |
| `docs/experiments/2026-08-19_small_model_matrix_c1c2.md` | 8B/14B 训练前能力与成本 | 零样本探针，不是蒸馏结果 |
| `docs/experiments/2026-08-21_small_model_matrix_c3.md` | 4B 训练前能力与成本 | 适合 smoke 基线，不证明参数量规律 |
| `logs/graph/eval/dpo_pairs_v0.json` | 60 条动作偏好 pilot | 跨体制/跨类型重叠，必须按 uid 分组 |
| `research/dpo_pairs_v0.py` | 可复现偏好对生成 | 需扩成通用数据构建器，不能只产 DPO |
| `logs/graph/eval/vgmc*_checkpoint.json` | 候选动作、gain、collateral、接受结果 | 494 是重复事件总数，不得当独立样本量 |

### 4.3 规则进化资产

| 资产 | 用法 | 当前边界 |
|---|---|---|
| `research/vgmc_exp1.py` | 候选、规则库、门控和 replay 核心 | 动作日志非完整推理轨迹；离线逐臂重算，不重跑建议器 |
| `logs/graph/eval/vgmc_adv_curve.json` | 7/7 有害候选拒绝 | 机制证据；三项预注册预测并非全部通过 |
| `logs/graph/eval/vgmc_collision_curve.json` | 碰撞暴露下门控/无门差异 | 方向性证据，不能替代功效分析 |
| `logs/graph/eval/vgmc_baseline_curve.json` | few-shot/Mem0/AWM 式 null | 保留 negative result，不继续同类基线堆叠 |
| `logs/graph/eval/bandit_gate_v0_eval.json`、`logs/graph/eval/bandit_prospective_eval.json` | 学习门失败证据 | 奖励无分辨力，暂不作为下一阶段主任务 |
| `docs/experiments/2026-08-29_vgrm_method_chapter_draft_v0.md` | Stage R 方法和命题素材 | 需收窄“有界回归”适用域 |

### 4.4 写作与图表资产

- `paper/research_story_v2.md`：当前三阶段故事。
- `paper/figures/fig_evaluate_distill_evolve_v1.svg`：完整稿 Figure 1。
- `docs/experiments/2026-08-31_related_work_v4.md`：评估四簇相关工作。
- `paper/references_v0.md`：已核引用池。
- `docs/experiments/figures_k2/`：内部分析图，可选取吸收机制/置信区间图重制为英文投稿版。
- `docs/experiments/figures_paper/fig_pareto_current.png`：描述的是当前评估协议 Pareto，不得改名冒充蒸馏质量—成本图。

### 4.5 暂不激活的素材

- `OpenAI4S`、`tabfm`：与当前最短闭环关系弱，不为使用工具而使用工具。
- TAT-DQA D4：现有转换件没有表层结构，当前无法定义每家族样本量；继续冻结。
- PSO：与 greedy 同值且贵 114.2 倍，只保留 null。
- 视觉补盲：错位问题未闭合，不进入近期主线。
- `hbkeyan/` 五件材料在当前 clone 的相邻目录中不存在；只能使用仓内已核摘要，拿到原件前不得新增逐页或逐公式引用。

## 5. 数据合同

### 5.1 样本单位

主样本单位必须是源表 `uid`，不是一条事件。由同一源表派生的 clean、mutant、不同 regime、候选动作和偏好对必须进入同一个 split。

建议统一样本 schema：

```json
{
  "sample_id": "stable-hash",
  "group_id": "source-table-uid",
  "defect_family": "alias_variant",
  "context": {
    "headers": [],
    "candidate_fields": [],
    "cheap_checkpoint_summary": {}
  },
  "teacher_action": {"action": "map_to", "target": "..."},
  "verification": {
    "gain": 0.0,
    "collateral": 0.0,
    "accepted": false,
    "reason": "gated_fail"
  },
  "provenance": {"artifact": "...", "regime": "...", "round": 0}
}
```

学生输入不得包含会让任务退化成阈值复制的完整 gain/collateral 真值。它可以使用验证前可获得的便宜特征；gain/collateral 只作为标签和最终门证据。

### 5.2 四层数据边界与泄漏规则

先按 `group_id=uid` 分组，再构造动作/SFT/DPO 视图；同一源表的 clean、mutant、不同 regime、规则事件与偏好对不可跨层。不能把历史 fix/meas 名称直接解释成新的四层隔离。

| 层 | 允许用途 | 禁止用途 |
|---|---|---|
| proposal/train | 候选构造、SFT/DPO、便宜特征和标签开发；内部按 uid 再划 train/dev，用于可学性探针、超参、阈值选择和 early stopping | 读取后两层结果以调整样本/协议 |
| gate-validation | 与 proposal/train 独立的验证表；用已冻结的确定性门判断规则接受/拒绝、回归及回滚 | 用它训练学生或反复挑阈值；冒充最终泛化测试 |
| sealed test | 冻结模型、阈值、规则库后的一次只读终评，包含预先选定的未见家族压力测试 | **绝不参与规则是否接受、阈值选择、early stopping、split/家族/容差修改** |
| future replay | 冻结后新增独立 uid 的前瞻只读批次，评估长期漂移/风险；批次规则版本先冻结 | 回流当前轮训练/门控/选择；本批揭封后不可继续充当未见证据 |

1. 先盘点旧工件哪些已用于开发、筛选或审稿；已看过的结果只能作 development/pilot 证据，不能通过重新切分“洗成”未见 sealed test。新的 sealed/future 层若不存在，manifest 标 `missing` 并走扩充路线，不虚构样本。
2. 同一 `(uid,col,target)` 重复先聚合 provenance，16 组冲突逐组保留原因/状态；规则历史或 regime 不同不等于随机噪声，解释不了就隔离，禁止多数投票消除冲突。
3. 未见家族的选择只依据预注册设计与元数据，在训练/调参前冻结；其全部 uid 从 proposal/train 和 gate-validation 排除。少量家族只能作压力测试，不能拿约 5 表支撑显著性。
4. 主要区间按 uid 聚类 bootstrap；不得把 118 个注入或 494 条事件当 iid。功效/MDE 使用开发侧统计及事先设定效应，不看 sealed test 结果估参数。
5. 在任何终评揭封前冻结 split/hash、模型选择规则、阈值、非劣容差、early stopping、DPO pair 选择及比较/多重检验协议；训练期只在 proposal/train 内部 dev 执行该规则。
6. gate-validation 会被反复查询，必须记查询次数/适配历史，不把其成绩当无偏泛化证据。future replay 如在下一轮转为开发数据，须新建独立未来批次，不回改本轮结论。
7. 甲方数据为零；训练数据、权重、逐样本输出/完整 manifest 保持 gitignored，只提交许可证明、聚合统计、hash 与可复现脚本。

### 5.3 数据门与不足时扩充

每种数据视图独立判门，SFT 通过不代表 DPO 通过：

| 判定 | 条件与后续 |
|---|---|
| `DATA_GO` | provenance/标签可核验、冲突已解释或隔离，前三层独立 uid/类别覆盖成立，future replay 来源与独立批次协议预先登记（尚未到来的批次不虚构样本），两次构建 hash 一致，按 uid 聚类功效/MDE 足以检验预注册效应；可经离线门后申请相应训练臂 |
| `PILOT_ONLY` | 来源合法可复现但独立 uid、双向动作/偏好、功效或未见测试不足；只能有界 smoke/pilot，立即转近期评估稿保底，不宣称论文级蒸馏 |
| `DATA_NO_GO`（NO_GO） | 来源/许可不明、不可修复泄漏、冲突无法隔离或正确性标签无法重建；该视图停止构建/训练并登记阻塞 |

Phase 1 报告来源工件、uid、regime、round、规则状态、标签来源、各层独立 uid、类别/家族、排除数、有效数、hash 及功效假设。当前快照更可能为 `PILOT_ONLY`；最终判定待该任务完成，不能由 494/60 两个行数直接裁定。

不足时不复制事件扩量：增加独立公开源表（先用已获许可且本地可用的来源，不重开 TAT-DQA D4），增加独立 uid，补经核验的正确 `map_to`、`hold` 与双向偏好（含正向 map_to 的 Type-B），重新做 uid 聚类功效/MDE 和四层覆盖检查。新来源下载、模型标注或训练另行授权；合成扰动不得算新增独立表。扩充截止前仍不达门即维持拆稿，不无期限补样本救主张。

## 6. 分阶段执行卡

### Phase 0：接续已确认主张（本批治理，不重开规划）

小模型角色、双轨路线与边界已由用户确认；本计划、叙事和资产账本已对齐，Phase 1 本地审计现已交付，按 §10 移交服务器验证。claim–evidence–owner 复用 `paper/research_asset_map_v2.md`，不另建日期版矩阵/计划；目标贡献保留 `needs-evidence`。指标阈值、训练窗口仍待确认，不能把方向确认当执行许可。若要改成通用 QA 蒸馏或替代确定性门，先停下报用户。

### Phase 1：蒸馏数据审计与构建器（本地审计已交付，训练视图未放行）

**完成范围**：§10与资产账本§3.1。本地来源/标签参考/规则账本/冲突与历史缺层已审；完整源表和独立正确性、真正未见数据仍缺，不把本地交付等同DATA_GO。测试按用户要求移交服务器，以下保留验收合同。

**输入**：`logs/graph/eval/vgmc*_checkpoint.json`、`logs/graph/eval/dpo_pairs_v0.json`、`logs/graph/eval/checkpoint_discrimination_tables_v2.json` 及其本地来源。

**动作**：复核 §1.2 分母，去重/隔离冲突，重建 provenance/规则状态与真实标签；按 §5.2 建四层 uid 清单、家族分布与 hash，构建 action/SFT、风险预筛、DPO 三种视图并分别判门。

**代码落点**：优先扩展 `research/dpo_pairs_v0.py` 的离线构建/审计能力和复用 `research/vgmc_exp1.py` 纯函数，不执行在线 main；只有无法保持职责清晰时才新增最小模块，不预建重复构建器目录。

**提交内容**：离线代码/测试，现有资产账本内的数据卡摘要、provenance/hash/排除口径与功效假设；本地完整 manifest/数据视图不提交。

**通过门**：同 uid 零泄漏，已使用数据不伪装 sealed，冲突可解释或隔离，两次 hash 一致、公开来源合法且无甲方数据；每个视图给 `DATA_GO` / `PILOT_ONLY` / `DATA_NO_GO`。

**失败处理**：关键来源缺失或标签不可核验时只交缺口/扩充建议，不加载模型补洞；数据不足立即触发评估保底，允许开发侧继续有界探针。

### Phase 1a：零端点可学性探针（0.5–1 天，Phase 1 后）

只用 proposal/train 内部按 uid 分组的开发划分；不看 gate-validation、sealed test 或 future replay 结果来筛方案。不加载 LLM；简单分类器仅 CPU 拟合，例如 logistic regression，属于本卡离线探针，不是模型训练窗口。

| 基线 | 输入/行为 | 要排除的简单解释 |
|---|---|---|
| always-skip | 全部拒绝候选 | 低有害率是否只是零覆盖 |
| deterministic matcher | 既有标准字段/确定性匹配，不引入新 LLM 建议 | 一条确定性规则是否已足够 |
| lexical/fuzzy | 表头与候选字段字符串相似度，阈值只在内部 dev 选 | 是否只是字面匹配问题 |
| confidence-only | 只读建议时已记录的 confidence，冻结高/中/低处理和缺失策略 | 教师自报置信是否已解释收益 |
| 简单分类器 | 仅验证前便宜特征，按 uid 拟合/评估；不含 gain/collateral/accepted、事后规则或 split 标识 | 是否根本不需要 8B |

**输出**：action macro-F1、正确 map_to/hold 召回、有害动作率、有效动作覆盖、最坏家族及 uid 聚类区间；预筛与候选生成分开计分，缺 confidence/正确标签时标不可测，不填 0。比较同风险下覆盖和同覆盖下风险，不能只拿全拒绝的准确率获胜。

**门**：若强简单基线已满足事先在开发侧定义的质量/覆盖目标且无可辨残余，判 `SIMPLE_SUFFICIENT`，不申请主训练，走评估稿保底。若样本不足则 `PILOT_ONLY`；若存在稳定残余且标签可学，仅说明值得申请窗口，**不是小模型已经优于简单基线**，其必要性最终还须 Phase 4/5 实测。阈值在探针前登记于本计划或原预注册，不因 sealed 结果修改。

### Phase 2：规则强基线离线 replay（零端点，1–2 天）

**输入**：Phase 1 冻结的开发侧共享候选流及可重建的表/规则状态。

**七类对照**：no gate、gain-only、collateral-only、confidence-only、fixed dual gate、独立 gate-validation 增强门、rollback-versioning（增强门 + 版本快照/回滚）。confidence 缺失策略事先冻结，不可使用 gain/collateral 冒充 confidence。

**指标**：有害接受率、有效规则保留率、覆盖/正确率、最坏家族、验证次数、回滚次数、累计成本代理；成本代理不冒充真实模型延迟。

**关键纪律**：所有臂消费同一候选顺序并各自维护规则版本；接受历史分叉后必须在各臂状态上重新确定性计算 gain/collateral，不能照搬原臂记录分数。旧 `grid_replay` 只能复核历史摘要，不算完整反事实门比较。

**通过门**：先复现原固定门数字，再验证各臂状态和计分器；接受/回滚仅使用 proposal/train 与 gate-validation，sealed test 不参与本卡。表级区间可算，null 原样保留；源表/状态缺失则标 `REPLAY_BLOCKED`，不能伪造闭环或用在线建议器补齐。

### Phase 3：训练环境和 4B smoke（需用户批准，1 天）

**目的**：只验证 HF/PEFT 数据、loss、保存、恢复和离线评测链，不产论文结论。

**模型**：4B 可训练权重 + LoRA/QLoRA；现有 GGUF 仅作推理基线。

**动作**：仅在 proposal/train 内部固定小 split 上做极少步数/单 seed 冒烟，检查 loss、action 分布与拒绝率；不接触 sealed test 或 future replay。

**失败即停**：权重许可不明、显存预算不通过、输出格式不稳定、训练/测试泄漏、模型只学会永远 `skip`。

### Phase 4：8B 主蒸馏实验（需用户批准，3–5 天）

**前置**：相应 SFT 视图 `DATA_GO`，Phase 1a 留有值得学习的残余，Phase 2 可复现，4B smoke 通过且用户批准独立训练窗口；缺一不运行论文主实验。

| 臂 | 定义 | 作用 |
|---|---|---|
| A0 | 8B zero-shot | 同任务训练前基线，不使用原 16 道 QA 替代 |
| A1 | unfiltered SFT | 保留所有合法、可核验的教师动作；不是把来源错误/泄漏也纳入 |
| A2 | checkpoint-filtered SFT | 在同一来源母池上增加 checkpoint 过滤 |
| A3 | A2 + gate-derived DPO | 独立偏好数据门通过才执行 |

4B **仅用于 Phase 3 训练链 smoke**，不作主实验 ablation；14B **既有异常尚未归因**，不推断权重或模板为原因，暂不作主学生。论文级训练主臂至少 3 seeds；仅单 seed 时降为 pilot，A0 报告是否确定性解码，不伪装重复独立样本。

**A1/A2 必须同时报告两种公平比较**：

- **自然数据量**：同一原始母池各用实际可用数据，冻结相同优化策略，报告独立 uid、事件数、训练 token、步数与成本；允许过滤带来量差，用于实际使用效果，不把量差当过滤质量的因果证据。
- **size/token/group-matched**：只在 proposal/train 中按预先规则匹配样本数、有效训练 token/更新预算、独立 uid 及家族分布，固定底座、超参、seed。匹配不读取测试表现，不复制事件、不复制成新 uid；无法同时匹配的维度报告偏差并降级过滤因果主张。

**主指标**：预筛前后的有害动作率、action macro-F1、目标字段 exact match、最坏家族表现；规则最终接受率单列，避免最终门遮住学生退化。

**次指标**：risk–coverage、ECE/Brier、最终 H/ACC、有效动作覆盖、p50/p95 延迟、token、峰值内存、完整验证次数。比较教师/简单基线/学生时分开生成与预筛开销，confidence-only 所依赖的教师开销不能隐去。

**非劣门**：建议以未见家族 macro-F1 差值 A2−A1 的 uid 聚类 95% CI 下界 ≥ `-δ`，`δ=0.02` 仅为待用户/导师确认值；最坏家族、有害固化的安全容差、成本/风险最小收益及多重比较协议一并在训练前冻结。若未知家族功效不足则只能报告压力测试，不能用点估计过门。

**成功条件**：两种口径均报告，质量非劣成立，且在预注册同风险/覆盖条件下有成本或风险收益；要称“过滤本身有效”还须 matched 口径排除数据量/组构成解释。只做到教师→学生降本不得声称 checkpoint 过滤优越。

**A3 条件**：独立 uid、正确 map_to/hold、双向偏好及聚类功效足够；当前单向 60 对不满足论文级 DPO 门，不能靠复制/翻转偏好硬造 Type-B。

### Phase 5：统一闭环评测（需用户批准，1–2 天）

严格分开更新与评分：在 proposal/train 候选流上让已获准的 A0–A3 提案，所有臂用同一定义的确定性门、各自独立的规则库，**只用 gate-validation 判断接受/回滚**。冻结学生、预筛阈值、规则版本及所有超参后，才对 sealed test 做一次只读终评；不得把测试流候选写入规则库。未来独立 uid 的 future replay 用冻结快照单列前瞻结果，尚无未来批次时只标长期证据缺失。

回答：预筛减少多少完整验证、漏掉多少有效规则、有害固化/回滚是否增加、更新后的 Stage E 和最坏家族是否恶化。报告无预筛、简单预筛、学生预筛与冻结规则前后对照；不同提案器臂回答系统效果，共享候选流实验回答门本身效果，不混淆二者。

只有该阶段有效完成，RQ4 才能写最小闭环结果；future replay 不足不必虚构长期提升。否则只能称 E→D 与 R 机制分别有证据，不能声称闭环有效。

### Phase 6：合稿/拆稿决策门（每道门触发即执行，最晚 10-04）

| 结果 | 动作 |
|---|---|
| 数据/公平对照/非劣门均过，学生相对强简单基线有预注册增量，闭环成本或风险收益成立，Stage R 安全容差满足 | 继续三阶段统一初稿；过滤独立贡献只按 matched 结果写 |
| A1/A2 无可辨差异，但已证明质量非劣，学生相对强简单基线/教师确有成本收益，闭环及安全门均通过 | 仅写效率型收窄主张；不得由“不显著”推导非劣，也不得写过滤优越 |
| `PILOT_ONLY`、`DATA_NO_GO`、`SIMPLE_SUFFICIENT`、非劣未成立或出现安全回归 | 立即拆稿止损：成熟评估稿内部交导师，D/R 进入大论文；有界补数/pilot 不阻塞交付 |
| 截至 10-04 仍缺训练许可、足量数据或有效闭环结果 | 不等、不赶工降门；本轮统一稿转后续，评估稿保底 |
| A3 未达门或无增益 | 不跑或删除 DPO 贡献，记录原因/NULL；不否决已达标的 A2，不追调测试集 |
| 规则门只证明拒绝、不证明净收益 | Stage R 只写安全机制和边界；其他继续条件必须仍满足，不能单凭拒绝率过闭环门 |

拆稿不是公开授权。专利申请状态与权利要求覆盖仍须用户确认，本轮只内部交付；要重新合稿，须补齐原冻结门要求，不能改门追认。

### Phase 7：论文写作与审稿闭环（3–4 天）

1. 仅 Phase 6 通过后组装完整稿（本批不创建），不覆盖 `paper/teacher_review_draft_v1.md`；拆稿时直接使用成熟评估稿，不另造空壳。
2. 先写 Introduction、Method、Setup；结果表只从冻结工件生成。
3. Stage E 压缩为支撑数据过滤的评估方法，不再占全文大半。
4. Stage D 为中心实验；Stage R 证明安全落地和闭环。
5. 更新 claim manifest；每个数字带 artifact 路径和统计单位。
6. 做三类审查：方法/统计、领域/创新、Reviewer 2/可复现性。
7. 只修改被问题命中的章节，不全稿重写。

建议新稿路径：`paper/evaluate_distill_evolve_draft_v0.md`；老师 Word 版只在 claim gate 通过后生成。

## 7. 双交付与三周条件排期

**交付 A：24–48 小时导师方向包（09-22～09-24）**。使用 `paper/teacher_review_draft_v1.md` / `paper/teacher_review_draft_v1.docx` 成熟评估稿，加当前 `paper/research_story_v2.md` 方向说明与现有资产账本；明确 E 已有证据、D 未训练、R 机制级。`paper/research_story_v2.docx` 已离线同步当前正文与三阶段表并通过结构/口径检查；正式阅读前仍需 Office 视觉核对。包交用户内部审阅，本批不代发导师。

**交付 B：实验完成后的统一论文初稿**。仅在 Phase 6 继续条件满足时组装统一稿，附冻结工件、两种公平对照与真实闭环结果；失败则直接使用成熟评估保底稿，不能为了排期把方向说明改名“完整论文”。

| 日期（2026） | 工作 | 里程碑 |
|---|---|---|
| 09-22～09-24 | 接续 Phase 1；方向包并行准备 | 审计、split/hash、分视图判门；方向包不等训练 |
| 09-24～09-27 | Phase 1a + Phase 2；开发侧扩充数据时间盒 | 可学性与规则基线；09-27 不够则维持 PILOT_ONLY/拆稿 |
| 09-28 | 仅离线前置通过且用户批准时做 Phase 3 | 4B smoke；未获批不执行、不占生产 |
| 09-29～10-03 | 条件执行 Phase 4：8B A0–A2，A3 独立判门 | 学生及超参/规则快照冻结 |
| 最晚 10-04 | Phase 5 + Phase 6 | 条件不齐即拆，不为赶期减少 seeds 或改门 |
| 10-05～10-08 | Phase 7 | 统一稿 v0 或评估保底稿；不等待长期 future replay 伪造结论 |
| 10-09～10-11 | 对抗审查与定点修订 | 实验后内部初稿包，不是首次导师方向交付 |

上述是内部时间盒，不是训练或投稿许可。旧材料中的 ARR/WWW 日期仅作历史排期线索，本批未联网复核；正式投稿前须另核会议日期并通过专利公开门，不能按旧日期自动外发。

## 8. 图表与写作产物

| 编号 | 内容 | 来源/生成条件 |
|---|---|---|
| Figure 1 | Evaluate–Distill–Evolve 总架构 | 复用 `paper/figures/fig_evaluate_distill_evolve_v1.svg` |
| Figure 2 | checkpoint tree + visibility/absorption | 复用现有图，统一英文、字体和矢量格式 |
| Figure 3 | A0–A3 质量—成本或 risk–coverage Pareto | Phase 4 真实结果后生成 |
| Figure 4 | 规则累计收益、有害固化率和回滚曲线 | Phase 5 真实结果后生成 |
| Table 1 | A0–A3 主结果、最坏家族和成本 | Phase 4 |
| Table 2 | 七类 gate baseline（含 confidence-only） | Phase 2 + 学生预筛对照 |
| Appendix | 四层数据 schema、split/hash、逐家族结果、null | Phase 1–5 |

现有 `docs/experiments/figures_k2/` 更适合内部分析；投稿版只复用数据和生成脚本，不直接混用中文标题、旧阈值或过期口径。

## 9. Agent 执行协议

每个接手 Agent 开工前必须依次读取：

1. `AGENTS.md`
2. `memory/CORE.md`、`memory/STATE.md`、`memory/THREADS.md` 当前科研线
3. `docs/research/README.md`
4. `paper/research_story_v2.md`
5. `paper/research_asset_map_v2.md`
6. 本计划（直接接 §10）；首次接手只读 docs/33、docs/34 政策，不执行旧排期

协作设计依据为 `docs/17_Graph_Engineering_多层Loop设计.md`，工程路线为 `docs/29_graph_engineering_roadmap.md`；后者的历史 backlog 不覆盖本计划，当前未决只回链 THREADS。卡片复用 `templates/task_card_template.md`，不新造科研专属 harness。

| 阶段 | 本地控制/分析/审计 | GB10 正式执行与验收 |
|---|---|---|
| Phase 0/1 | 文档治理、已有 JSON 复算、provenance 审计、构建器与合成测试 | 需远端源表才能完成的核验/正式数据构建在授权执行面进行；未核验项保留缺口 |
| Phase 1a/2 | 起草可学性/规则基线代码、fixture 验证、审计已有输出 | 即使 endpoint=0，新 baseline 数字、校准和 replay 仍是正式实验事实，不在本地创造 |
| Phase 3–5 | 拟卡、预算/协议审查、已有结果复算 | 获批的环境核验、4B smoke、8B 训练及闭环终评 |
| Phase 6/7 | 基于有效工件判断合稿/拆稿、写作、图表和独立审查 | 不因写作/审稿缺数字而自动重跑实验 |

执行面唯一权威是 `docs/governance/2026-09-07_execution_plane_boundary.md`：D 给任务与授权，A 交实际 diff/工件，B 跑范围匹配的独立验证，C 审证据和主张，D 验收。A 自测不是 B/C 已审；报告必须绑定提交或工作区范围、时间和环境。默认 Loop B 包含真实 canary/API/QA/PG 检查，不得为本地治理启动它。watcher 收据预检只验证合同，不运行 watcher、不生成真实运行证据。

每张任务卡必须写明：目标、输入、输出、成功条件、失败条件、skill 装载清单（≤5 + 红线常备）、执行面与 endpoint/model 调用预算、禁止修改文件和回滚方法。

共同红线：

- 不修改 `docs/33*`、`docs/34*`。
- 不重启/探测生产服务，不触碰数据库；模型加载与训练必须先获用户批准。
- 不重开 TAT-DQA，不把 D4 不存在的结果写进论文。
- 不提交模型权重、训练样本正文、逐题私有输出、日志或凭证。
- 不把零样本矩阵写成蒸馏，不把重复事件写成独立样本，不把机制拒绝率写成显著净收益。
- 不为了“有结果”修改 test split、holdout 家族、阈值或 `δ`。

每阶段提交要求：

1. 仅在用户授权提交时做原子 commit，push 另有明确授权；不把前一批交付许可延伸到新改动；
2. `git diff --check`；
3. 最小相关测试和可复现命令；
4. 报告 endpoint/model 调用次数，包括 0；
5. 更新 `memory/STATE.md` 和 `memory/THREADS.md`，但只有用户确认的路线才写 `DECISIONS.md`。

## 10. P1 交付与服务器接手

### 10.0 2026-09-22 主线合并与 GB10 验收停点

`origin/test/compaction-guard-abort` 的17个提交已通过 `--ff-only` 合入
`main` 并推送，`main/origin/main=0aee20d913e32fdc7bdf99e7980d0eef0f15bb28`。
冻结清单所列仓内路径、docs/33 和 docs/34 在该范围内零改动。本地四项既有
用户资产保持原样。

GB10 生产 checkout 的 `logs/graph/dispatch_log.md` 与导入范围相交，因此按
保护规则保持在 `3dabbc7`，未 pull/stash/reset/clean；验收在 detached worktree
`/home/testuser/wzh/projects/agents_final_tech_accept_0aee20d` 完成。当前证据：

- 定向离线合同测试 159 passed；diff/Python/Bash 静态检查通过；论文 claim
  validator 49/49。
- `sync_skills.sh --check` 为 1/97 drift（仓内 `skill-doctor` 与 GB10 Codex
  安装副本不同），docs_lint 因此为 1 fail/1 warn；未擅自 sync/prune。
- skill-doctor 为 0 errors/139 warnings，按当前策略 exit 1；没有消警。
- 全量 pytest 一次：590 passed/14 skipped/4 failed。四项失败都来自 detached
  worktree 缺少 gitignored `data/research/drift_v0/output/injected_tables.json`；
  生产 checkout 中该文件存在，SHA256 为
  `827092cf6af2212ae334a9ad5f7b9ea12122d90ff9117353baf79bb1936e4fa9`。
- `strace connect` 实测除允许的 `:5050` 1 次和 PG `:15432` 6 次外，还发生
  `:8004` 5 次、`:8007` 1 次禁用连接尝试，并有 DNS `:53` 4 次与 GitHub
  SSH `:22` 4 次。连接尝试已违反零端点合同；不能因为未确认完成模型推理
  就降格为通过。

因此本轮验收结论是 **BLOCKED**。Phase 1a 与 Phase 2 均未实现、未运行、
未生成结果或提交。新接手者不得重复全量 pytest，直到任务卡明确硬网络隔离/
精确排除策略；不得生成或重算旧工件来填补 detached worktree 输入。后续先由
用户裁定 GB10 skill 安装漂移的处理、隔离数据挂载方式与安全测试清单，再恢复
验收。4B/8B、模型调用、judge、端点实验和服务重启仍未授权。

**本地完成**：37件既有工件的审计、三视图索引、冲突隔离和历史/缺层manifest；两次产物hash一致，聚合结果及复算命令见资产账本§3.1。动作SFT/风险预筛未放行，DPO仅保留审计素材；不把缺少本机原始语料当作远端资产失败。导师包内容修正和两份Word已生成，阅读顺序为中文说明→总叙事→英文评估稿。

**旧服务器接手卡（已由 §10.0 的实况取代）**：以下命令只保留作历史验收范围，不是再次运行指令。新接手者不得重复全量 pytest，也不得自动运行实验；先按 §10.0 处理 skill 漂移、隔离数据与硬网络边界：

```bash
PYTHONPATH=src python3 -m pytest tests/test_distillation_data_audit.py tests/test_paper_claim_acceptance.py tests/test_research_story_assets.py tests/test_document_governance.py -q
python3 research/validate_paper_claims.py
python3 scripts/docs_lint.py --json /tmp/docs_lint_p1_server.json
```

使用服务器已有含 python-docx 的 Python 环境；完整数据/来源明细可按资产账本命令在新的忽略路径重算，不提交原文。另在 Office/LibreOffice 打开两份导师 DOCX，检查缺字、分页、表格溢出与阅读顺序。需要修复时只定点修，不启动 Phase 1a/2、训练或新的正式回放；实验许可由用户后续给出。

以下保留 P1 任务合同供复核，**不是新的开工指令**：

```text
任务：P1-DATA-AUDIT，执行 Phase 1 动作策略蒸馏数据审计。
目标：确认真实独立样本、标签可信度与可用数据边界，不训练、不调用任何模型/服务。
Claim：当前叙事 RQ2 / TH-I3；兼为 RQ3 门基线提供候选账本，不沿用旧 SP-RQ2 编号。

开工：git status；读取 AGENTS.md、CORE/STATE/THREADS 当前科研线、科研入口、故事、资产账本与本计划。
执行面：本地只复算已有JSON、审计provenance并验证构建器/fixture；依赖另一服务器源表的步骤暂挂，正式数据构建或新论文数字按 §9 回 GB10，不因 endpoint=0 越界。
skill 装载清单：按 docs/SKILL_ROUTING.md 选不超过 5 件并完整读取；本卡至少用论文证据审查与文档治理，红线常备 graph-loop-rules。

输入：
- docs/handoff/2026-09-22-paper-research-next-phase.md（§1.2 与 §5 数据合同）
- paper/research_asset_map_v2.md
- logs/graph/eval/vgmc*_checkpoint.json（16 件）
- logs/graph/eval/dpo_pairs_v0.json
- logs/graph/eval/checkpoint_discrimination_tables_v2.json
- research/vgmc_exp1.py、research/dpo_pairs_v0.py（仅复用本地纯函数）

必须输出：
1. 原始/有效/排除/去重计数：625 日志、494 有分数事件、48 uid、94 uid-col、139 uid-col-target、292/202；不把事件当独立表。
2. 16 组相反接受标签、41 个多 target 列的 provenance、规则状态、隔离/解释状态；完整逐项表只保存在本地 gitignored 区。
3. DPO 60 对/36 uid/60 uid-col、全部 skip>map_to、Type-B=0、gate_fooled=9；真实正确性和门接受标签分开。
4. proposal/train（内部 uid-dev）、gate-validation、sealed test、future replay 四层 manifest/hash 与已使用数据清单；缺层标 missing，不洗旧测试。
5. 每视图/每层家族与动作分布、独立 uid 及聚类功效/MDE 敏感性分析；未批准效应/容差写条件判定，不自行拍数。
6. 各视图 DATA_GO / PILOT_ONLY / DATA_NO_GO 与理由；不足时给独立公开源表/uid、正确 map_to、hold、双向偏好的有界扩充需求，禁止复制事件扩量。
7. 可复现的离线构建/审计代码和测试；连续两次相同 hash，泄漏/冲突/缺标签/单向偏好有测试覆盖。

落点：优先扩展既有 research/dpo_pairs_v0.py；数据卡/摘要回填 paper/research_asset_map_v2.md，状态更新 memory/STATE.md、memory/THREADS.md，不建第二份计划。
通过：统计可复算、同 uid 零跨层、来源/标签可核、冲突不被静默抹平，判门可追溯；报告 PILOT_ONLY/NO_GO 也是有效审计交付，不算实验成功。
失败/停点：源表/状态/许可不可核即隔离并登记；不能为了填空调用模型、服务、数据库或重开 D4。
回滚：仅撤销本卡自己的可审阅变更；保留接手时未提交工作，提交后用补偿提交，不用 reset/checkout 覆盖现场。
预算：endpoint_calls=0、model_calls=0、service/database/health_probes=0；不加载模型、不执行训练。
保护：docs/33*、docs/34*、冻结节点及专利终态件不动；不提交训练正文、完整 manifest、私有逐样本输出、权重、日志、凭证。
验收：git diff --check；本卡新增离线测试；python3 research/validate_paper_claims.py；两份论文测试；docs_lint；受保护路径 git status 必须为空。
后续：只有此卡完成才进入 Phase 1a；PILOT_ONLY/NO_GO 立即启动评估稿保底，不自动申请训练。
```

## 11. 尚需用户确认的执行参数

“4B 仅 smoke、8B 主学生”已经确定，不再重问。以下不阻塞 Phase 1 的事实审计，但不能由 Agent 自行批准：

1. 离线门通过后，批准独立训练窗口、可训练权重/许可、LoRA/QLoRA、资源与调用预算；
2. 训练前确认主指标、非劣 `δ`（0.02 仍是建议）、最坏家族/安全容差、最低成本/风险收益及功效要求；未确认时只报告敏感性范围，不声称 DATA_GO 已放行主实验；
3. 若需新增源表下载/标注，批准具体来源和操作；专利申请状态/权利要求覆盖另为公开硬门。

先完成零端点数据审计、可学性探针和规则 baseline，不空等训练窗口。

## 12. Strict closeout addendum (2026-09-23)

This addendum records the current evidence and supersedes the old acceptance-stop status for operational handoff; historical §10.0 text remains unchanged for traceability.

- **GB10 alignment:** production checkout and `origin/main` are `d351d7e09e738f16727f17d5aa3dc35646989731`, ahead/behind `0/0`; `0aee20d` is an ancestor. The next natural Loop B cycle recorded `git_alignment=PASS`.
- **A-3 closed:** the authorized one-item installation sync repaired the confirmed `skill-doctor` drift. `sync_skills.sh --check` is `PASS: 97`, with A=76/C=21 and missing/orphan both zero. Repository skills were not edited; full-root warnings remain visible.
- **A-2 boundary:** four exact VGMC tests passed (`4 passed`, rc=0): `test_adv_map_deterministic_nested_wrong_target`, `test_overlay_merge_adds_columns_and_entries`, `test_overlay_none_is_identity`, and `test_real_overlay_artifact_loads`. `strace -f -e trace=connect` observed zero attempts to `:8004`, `:8006`, `:8007`, `:8008`, and `:4096` in that test scope (total connect syscalls 0). The scope used synthetic corpus helpers because `injection_map.json` is absent in the isolated worktree; it does not cover `load_corpus()`, full pytest, production, or future experiment paths. The correct label is `SCOPED_PASS`.
- **Phase 1a:** `DATA_NO_GO`; no baseline numbers were produced. Phase 2 remains unstarted. See `docs/experiments/2026-09-23_phase1a_data_no_go.md` for the structured gate report.
- **Traceability:** no backend agent session remains running. Production dirty assets and the external alignment backup remain outside the source commit; no rolling report is promoted to source evidence.

### Next-round entry contract

1. Data supplementation: reopen Phase 1a only after the listed source/schema, licence, independent-correctness, confidence, and disjoint-manifest evidence is accepted.
2. A-2 expansion: create new hard network-isolation evidence for any broader range; the present scoped trace is not reusable as a global guarantee.
3. Loop C Lead: control-plane, governance, documentation, archive candidates, and experiment-design work may proceed while the research gate is `DATA_NO_GO`; Phase 2 and training remain closed.
