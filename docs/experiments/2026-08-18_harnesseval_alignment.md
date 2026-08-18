# HarnessEval 对标 — 四阶段协议/evidence tree/Skill Library 对照 + K2 混合三层升级依据

> 状态: 活跃 | 更新: 2026-08-18 | 类型: K1.5 科研线补充对标（只读调研 + 文档修改；不改代码/配置，不调用推理端点）
> 范围: 快查对照 → docs/33 §2.1 评估线升级 → docs/30 §3 related work 锚点。（本文件为产出 1，后续改动见对应 doc 的 git diff）
> 素材: 机器之心文章 `/tmp/wx_article.txt`（08-13 报道） | Blog https://mirros.ai/blog/harnesseval（web_extractor 已 fetch, 2026-08-18） | Repo https://github.com/mirros-lab/harnesseval-w（git clone --depth 1 至 /tmp/harnesseval-w, 只读 README + 目录树 + 一份 skill_plan 样例, 未安装未运行）
> 降级声明: arXiv 链接 README 标 2608.16859, 未打开正文（任务范围以外）; blog/repo 均可达, 无降级。

## 1 四阶段协议细节（含原文依据）

机器之心正文的四阶段为 **Plan / Route / Decompose / Verify**（文章原文 "整个过程可以概括为四个阶段"）：
- **Plan｜先理解案例，再决定测什么**：评测智能体读取初始状态、动作、任务类型和评测目标，生成与当前案例对应的评测计划。
- **Route｜选择适用技能，而不是跑完所有指标**：系统从 Skill Library 中调用适合当前案例的 skill，并记录为什么启用某项检查、为什么跳过另一项检查。
- **Decompose｜把抽象判断拆成可验证证据**：高层问题被拆成目标定位、状态追踪、时序变化、因果顺序、结构保持等子问题，再由专门的 sub-agent 或工具分别处理。
- **Verify｜先审计证据，再交付分数**：主智能体验证各分支的证据质量与逻辑关系。最终输出的不只是一个标量分数，而是一棵完整的 evidence tree。

README（"How It Works"）三段对应：
1. **Case-specific skill routing** — "the planner routes it to the skills that can legitimately evaluate it — and records an evidence-grounded reason for every skill it skips"（Route 的跳过理由记录）
2. **Sub-agent reasoning** — "Each skill decomposes its evaluation into measurable sub-questions, each answered by a dedicated sub-agent against rollout evidence"（Decompose）
3. **Validated aggregation** — "The parent agent validates the collected evidence and aggregates it into the case score. The full trace — every question, answer, score, and supporting frame — is saved as an auditable case card."（Verify + case card）
- 路由只依赖案例上下文、不依赖被测模型：README "Routing depends only on the case context, never on the model being evaluated"（公平性设计）

## 2 Evidence tree schema

- 记录内容: 测了什么 / 为什么要测 / 调用了什么工具 / 找到了什么证据 / 这些证据如何支持最终结论（文章 "这棵证据树记录了…"）。
- 两层交付: 一层是用于模型比较与排名的量化分数；另一层是可检查、可复现、可追责的证据与推理结构（文章 "HarnessEval 交付的是两层结果"）。
- 落盘形态（README + benchmark/plans 样例）: 每案例一个 `*.skill_plan.json`（case_id / taxonomy(primary_axis, probe_family) / selected_skills[]，每 skill 带 `reason` 与参数），运行后产出 auditable case card；目录 `benchmark/plans/{drift_resistance,exploratory_transition,intentional_transition,offscreen_evolution,physical_transition,return_revisit_consistency}/`。
- 定位用途: 准确定位错误来源，据此改进下一阶段模型设计/训练（文章 03 节）。

## 3 Skill Library 设计

- **动态路由**: 案例不同 → harness 组织出的评测路径不同（文章 "案例不同，Harness 组织出的评测路径也不同"）；"记录为什么启用某项检查、为什么跳过另一项检查"（Route）。
- **skill → sub-agents 拆解**: "每一个 skill 都会衍生出来一系列 subagents 来拆解复杂问题，从不同角度衡量模型能力"；"Skill Decomposition — questions are broken into sub-questions delegated to sub-agents/tools"（blog；例子: 物体状态变化 → 存在性/对象正确性/预期状态/场景锚点/无关变化五检查；物理碰撞 → 目标追踪/时间交叠/速度估计/因果顺序）。
- **技能与证据缺口主动暴露**: "当系统遇到能力边界之外的问题时，还应主动暴露自身的技能与证据缺口"（文章 04 节）。
- **living system**: "benchmark 不再是一套固定规则，而成为能够持续扩展和自我完善的 living system"；README "Extending HarnessEval"（提交新 case / 提交新 skill）；"the evaluator evaluates the evaluator … updates its own skill library"（blog Future 3: RSI）。
- Blog 数据点: 9 skills（Render Quality Inspector、Physical Plausibility Inspector、Viewpoint Trajectory Verifier、Offscreen Evolution Verifier 等, extensible）；三评价轴 = Observation Quality / Transition Correctness / World Persistence。

## 4 与 run_eval.sh 现状逐项对照表

对照素材（脚本/文件级）:
- run_eval.sh 四步: ① `scripts/m1_scenario1_regression.py`（M1 门禁, quick/full）② `scripts/m2_eval_deterministic.py`（确定性 16 问）③ `scripts/m2_eval_number_faithfulness.py`（NF, top_k=5）④ `scripts/m2_eval_judge.py`（:8004 temp=0 四维 judge）
- K2 检查点树: `config/eval_checkpoint_trees.json`（meta + parse/qa 两棵, 20 叶）+ `scripts/eval_checkpoint_aggregate.py`（Algorithm 1 聚合, 确定性, 缺工件 missing_score 降级）→ 报告 `logs/graph/eval/checkpoint_aggregate_report.{json,md}`
- judge 一致性: `scripts/m2_eval_judge_consistency.py`（同答案 judge 3 次, drift>1 标 DRIFT; 输出 `logs/graph/eval/judge_consistency_report.json`）+ `scripts/m2_eval_judge_crosscheck.py`
- 检索透明面板: `src/web/static/m1.js`（m2AddAssistantBubble sources toggle, `▸ N 条来源` 详情）; `src/biz/m2_service.py` 的 answer/sources 契约
- B4 结构化日志: `logs/graph/b4_ask_log.jsonl`（route/latency_ms/sources_count/fell_back/status 每请求一行）；`scripts/graph/status.sh` 的 "B4 观察窗口" 汇总段

| HarnessEval 要素 | 他们的做法（blog/README/文章） | 我们现状（脚本/文件级） | gap | 可借鉴度 |
|---|---|---|---|---|
| Plan: 案例理解→评测计划 | 每 case 读取 (初始世界, 动作, probe intent) 生成 plan; 交付物 = 固定 plan 文件（benchmark/plans/*.skill_plan.json, routing_mode: shipped_case_plan） | `config/eval_checkpoint_trees.json` 的 meta（caliber/source/口径）+ 固定题库（m2_eval_deterministic.py + m1_scenario1_regression.py 的样本集）; K2 报告 `logs/graph/eval/checkpoint_aggregate_report.json`; 无每案例 plan 工件 | 我们是"一套树/题库对全部案例"的静态 plan；无"这个 case 为什么这样测"的 per-case 记录 | 中：per-case plan 文件可作为 K2 报告的审计附件，但金融 QA 案例同构性强, plan 差异小于世界模型 |
| Route: 按案例选 skill, 不跑全量指标 | skill_plan.json 的 selected_skills 每项带 reason；跳过也要记录理由; "case-specific skill routing", 路由只看 case 不看被测模型 | 无动态路由；run_eval.sh 四步全跑（含 `--quick`/`--full-m1` 的手工模式选择）；qa 树叶子由确定性契约 + judge 静态组成 | 无"跳过检查及理由"的审计记录；无按案例裁剪指标集 | 高→中：金融场景可先把"跳过理由"落到 eval_summary.jsonl, 动态路由需判别力数据支撑（K2 成本-判别力曲线的前提） |
| Decompose: 高层问题→可验证子问题(sub-agent/诊断工具) | "Each skill decomposes its evaluation into measurable sub-questions, each answered by a dedicated sub-agent against rollout evidence"; skill→sub-agents 拆解 | K2 检查点树已把高层任务拆成解析 5 叶 + QA 7 叶（带 weight/requirement）; 确定性优先, agent 深挖按需（尚无 third layer） | 子问题由人工配置而非按案例程序化生成；sub-agent 仅出现在 M2 agent 灰度链路（B4 route=agent 记录）, 未接入评测协议 | 高：K2 树的叶子层 = 静态 Decompose, 第三层（agent 深挖）正是论文 B 的混合三层增量 |
| Verify: 主智能体检证据→聚合评分 + case card | 父 agent 校验各分支证据与逻辑关系后聚合为 case score; 全 trace（每问/每答/每分/支持帧）存 auditable case card; evidence tree 两层交付（量化分 + 可追溯证据） | 聚合是确定性 Algorithm 1（eval_checkpoint_aggregate.py, 缺工件 missing_score 降级, 不静默给 0）; judge 一致性由 m2_eval_judge_consistency.py 独立审计; B4 每行日志记录 route/fallback; 无"每问每答每分"证据卡 | 我们有聚合与一致性, 缺 per-case 证据树工件（叶子为什么得这个分的证据链只散在 judge report 与 B4 日志） | 高：把 checkpoint_aggregate_report + judge_consistency + B4 合并成 per-case card 是低成本高价值增量 |
| Evidence tree schema | 记录测了什么/为什么/工具/证据/逻辑链; skill_plan.json 带 reason | eval_checkpoint_trees.json meta（口径/基线引用） + eval_summary.md（run_eval.sh 末段汇总: 门禁/确定性/NF/judge 全写入一行行条目） | 有"结论"层无"证据链"层：叶子分←哪个工件哪个 check 不落盘为结构化卡片 | 高：形成我们自己的 case card 即可对标 |
| Skill Library 动态路由 / 缺口暴露 / living system | 案例不同评测路径不同; 主动暴露技能与证据缺口; benchmark 持续扩展（提交 case / skill） | skills/ 注册表（AGENTS.md Skill 武库）是执行侧武器库, 与评测侧分离; schema_suggestions.json 的 apply/reject/hold 是"建议-验证-固化"闭环, 与 skill 缺口管理无关 | 评测技能库未成型; 缺口暴露靠人（m1-gap-triage、m2-rag-playbook 是 skill 不是自动缺口报告） | 低→中：论文 B 的 "evaluation harness" 可以借 living system 叙事, 但金融领域更实用的是"评测产出→规则固化→回归门禁"闭环（差异化口径 ②） |
| 公平性: 路由不看被测模型 | "Routing depends only on the case context, never on the model being evaluated" | 我们评测对象 vs 评测脚本同仓且固定题库, 天然一致; judge 防泄漏（judge 不看期望答案, docs/30 §2.2 C 模块） | 无 per-model 路由概念（当前只有一条评测链） | 低：单模型单链场景无此需求, 论文 B 可提一句方法论对齐 |
| 交付物形态 | summary.json / leaderboard_latest + per-case artifacts + metric cache; verify run 子命令重新校验已有 run | run_eval.sh 汇出 eval_summary.{json,md}; K2 报告 checkpoint_aggregate_report; 工件目录 logs/graph/eval/（gitignored） | 无 leaderboard 持久化页; 无 verify-run 式可复现重校验（有口径对照文档 2026-08-18_checkpoint_protocol_v0.md §3） | 中：论文 B 需要 leaderboard, 可沉淀 eval/ 目录为公开数据卡 |

## 5 对 docs/33 §2.1 与 docs/30 §3 的改动依据（本文件为三项产出的溯源）

- **差异化口径三条**（写入 docs/33 §2.1）: ① 确定性检查层在前的混合三层 harness ② 评测直接驱动验证门控自学习（闭环执行器 vs 诊断系统）③ 金融文档领域首个 evaluation harness 落地。
- **K2 设计决策升级**（写入 docs/33 §2.1）: 方法骨架从"静态检查点树 (GTA-2)"升级为"混合三层" — 确定性检查 → 静态检查点树聚合 → 按需 agent 深挖（对标 HarnessEval Route+Verify）; 核心实验 = 评测成本 vs 判别力曲线（含与纯 agentic 评测的对照）; K2 已交付 v0 = 第二层, 第一层已有, 第三层是 v1 新增。
- **术语决议**: 论文 B 采用 "evaluation harness" 表述借势。
- **docs/30 §3 锚点**: 加 HarnessEval 一条（评估线相关工作, 与记忆线锚点分列）+ 差异化策略一条（vs HarnessEval: 诊断式评测 harness vs 评测驱动的闭环执行器, verification-gated 固化是它没有的下游）。

## 6 独立判断与质疑（供 Loop D / 用户复核）

1. **"金融文档领域首个 evaluation harness 落地"主张的强度**: 这是文献调研主张, 无检索证据支撑 "首个" — 建议在论文 B 中表述为 "将 evaluation harness 范式引入金融文档智能体领域" , 并在一轮 targeted 检索后决定是否保留 "首个"。任务纪律要求只做快查对照, 已如实标注。**[08-19 定稿]** 用户批复 ④: "首个"措辞正式降级为"引入范式"; FORCE-Bench（arXiv 2607.19409, 企业金融 agent 评测 harness）补入 related work 作工业先行证据。
2. **HarnessEval 与我们的本质差异**: 它是"诊断系统" — 评测终结于分数与证据树, 供研究者改进模型; 我们是"闭环执行器" — 评测产出直接驱动 schema 规则固化进回归门禁（GTA-2/Judge 精读已证路线）。这个差异是论文 B 真正的立足点, 不是 "我们也有 agent 评测" 这种附属叙事。
3. **四阶段命名差异**: 机器之心用 Plan/Route/Decompose/Verify 四阶段; README 用三步骤（routing → sub-agent reasoning → validated aggregation）+ 明确 "case card" 交付。论文 B 引用时以 README 为准（四阶段源自文章转述）, 避免引用错位。
4. **可借鉴度最高项 = per-case evidence card**: 我们已有全部原料（checkpoint report + judge report + B4 日志）, 缺的是把它们合成为结构化卡片与 leaderboard 页。这是 K2 第三层之外最便宜的增量, 建议单独立项。
5. **世界模型 vs 金融文档的迁移边界**: HarnessEval 动态路由的正当性来自世界模型案例的异构性（碰撞/漂移/离屏演化需要不同 skill）; 金融 QA 案例同构性更强, 动态路由收益需用成本-判别力曲线实证, 不能直接照搬 — 这是我们 K2 核心实验的理由。
