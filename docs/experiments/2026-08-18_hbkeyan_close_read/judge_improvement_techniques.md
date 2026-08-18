# 2604.13717 LLM-as-a-Judge 改进技术 → 本项目四维 judge 技巧清单

> K1 只读精读产出之二。来源：arXiv:2604.13717v1（An Empirical Investigation of Practical
> LLM-as-a-Judge Improvement Techniques on RewardBench 2, Composo AI, Ryan Lail, 2026-04-15）。
> 提取文本 1077 行已分块通读（摘要 / §1 / §2 / §3 / §4 全部方法 / §5 全部结果与分析 / §6 讨论 /
> §7 结论 / 附录 A/B/C）。
> 本项目 judge 实况（已核实，见 §1）：`scripts/m2_eval_judge.py` 四维 rubric（faithfulness /
> numeric_correctness / citation_quality / refusal_appropriateness，每维 0–5 整数，`:8004` temp=0 整答级），
> `scripts/m2_eval_judge_consistency.py`（同答 3 次 / 漂移 >1 分标记 DRIFT），`scripts/m2_eval_number_faithfulness.py`（NF 去 LLM 化）。

---

## 1 论文五技术一览（含关键数字，供引用）

| 技术 | 原文结论 | 关键数字 |
|---|---|---|
| ① Ensemble scoring（k=8 取均值） | 最强单品：+9.8pp | 71.7%→81.5%（5.0× 成本）；k=3 已捕获 ~70% 收益；**temp=0 下 k=8 仍有 +4.6pp**（GPU 浮点非确定性，无 seed 参数）——对我们冲击最大 |
| ② Task-specific criteria（单句类别判据） | +3.0pp @k=1，几乎零成本；k=8 时仍 +2.1pp | Math +12.0pp（k=1，方向性）；判据必须预注册（pre-registration），防事后挑判据 |
| ③ Calibration context（同类别示例锚定分数尺度） | k=1 时 +1~2pp；k=8 时被 ensemble 吃掉，无增益 | 所有变体（high/low/both/cross）在 k=8 都在 81.0–81.7%（≈纯 ensemble 81.5%） |
| ④ Adaptive escalation（mini/full 双模型 + 方差路由） | mini k=8 是性价比甜点：79.2% @1.2× 成本；方差路由不划算 | mini k=8 只比 full k=8 低 2.3pp；hard routing/soft blending 在 held-out 上不泛化 |
| ⑤ Soft blending / variance-informed ensembling | 有 in-sample 增益，held-out 不复现 | soft blend test 80.2% < full k=8 81.5%；var-informed 74.9% @1.6× |

顶层结论：**「写一条任务特定判据 + 设 k=3–8」是唯一稳定收益组合；更复杂技术（calibration/routing/blending）在等价成本下不增稳**（§7 Conclusion）。

---

## 2 可移植到本项目四维 judge 的改进技巧清单

> 适用性标注：**[直接采用]** / **[改造后采用]** / **[不适用]** + 一句话理由；改造项写明改造点。

### T1. 单句语义判据注入（Task-specific criteria）—— [直接采用]
- 改造点：无（我们 rubric 已内嵌在 `JUDGE_PROMPT` 每维定义里；要补的是"以一句 focus 句收尾"的形式与预注册）。
- 理由：论文 +3.0pp @k=1 零边际成本；我们四维各有一句 rubric 语义，已天然满足。
- 落地建议：参照表 3 风格把四维各加一句「Focus on ...」句，例如 numeric_correctness 加「Focus on whether the stated numbers exactly match the reference (mask-aware)」。改动须登记为 rubric 版本并跑预注册（防事后挑判据，K2 一起做）。

### T2. 同答多次取均值（Ensemble scoring，k=3–8）—— [直接采用]（成本可控版）
- 改造点：无，但可先做小 k 实验验证视野；且**不能依赖 temp=0 的确定性**（论文数据点：temp=0 下 k=8 仍 +4.6pp）。
- 理由：这是防"同答案重复打分漂移"最直接的手段；漂移度量已存在（`m2_eval_judge_consistency.py` 同答 3 次、漂移 >1 分即标记）。
- 落地建议：`judge_one()` 改为支持 `--runs k`，聚合时平均分 + 方差；一致性脚本从 3 次改成 k=5 并把 DRIFT 阈值降到 ≤1 分（保契约：不引入平局）。成本：k=5 即 5× 单次调用；对本项目 16 题 × 4 维的规模，k=3 是首推（论文 ~70% 收益 @3/8 成本）。

### T3. 预注册判据（pre-registration）—— [直接采用]
- 理由：论文强调判据改动会污染结果；我们已有「rubric 存档、改动需同步 docs/18 记录」（`m2_eval_judge.py` 头部注释）的雏形，把"预注册"做成版本化管理即可。
- 落地建议：把 `JUDGE_PROMPT` 加版本号（v_k1，K1 精读后首个版本），K2 形式化时把 rubric 与检查点树定义一起入 JSON schema。

### T4. 防漂移计算（temp=0 非确定性认知）—— [直接采用]
- 理由：论文明确 temp=0 下 k=8 仍比 k=1 高 +4.6pp（GPU 浮点非确定性、无 seed）。本项目一致性脚本的"SPREAD 全 0 = STABLE"结论要标口径：只说明"同一 prompt 同一 temp=0 下瞬时稳定"，不证明"跨进程/跨 GPU 可复现"。
- 落地建议：一致性报告加一条 warning；若后续换 GPU/服务进程，重跑一致性脚本再定基线。

### T5. 分类别锚定示例（Calibration context）—— [改造后采用]（只用于"同一题跨次打分"的锚定，不用于跨题）
- 改造点：论文用"同类别另一题"当锚；我们题库只有 16 题且类别少，改为"同题已评估样本"作锚（存历史打分作为 in-prompt 参考），控制同题重评漂移。
- 理由：k=1 时 +1~2pp；但注意论文也给出了警告——k=8 后无增益、加进 criteria 反而 -1.0pp（combined 82.6% < criteria 83.6%）。所以只作为 k=1/低预算场景的降漂移手段。

### T6. 双模型 + 方差路由（Adaptive escalation）—— [改造后采用]（只鉴定"需要人工复核的场景"）
- 改造点：不引入第二 judge 模型，而是用"mini 方差"当"该题是否需要人工复核"信号：同答 k 次方差大 → 标记需复核（当前一致性脚本已有 DRIFT 标记，扩展成"方差大的题"）。
- 理由：论文双模型给 2.3pp 但成本翻倍；我们本地 judge 只有 :8004 一个端点，第二模型（:8008 27B）的判据未验证，成本高不划算。

### T7. Soft blending / variance-informed ensembling—— [不适用]
- 理由：需要 judge 双模型 + 参数调优，且论文在 held-out 上明确不泛化（test 80.2% < 81.5%）；我们规模小，直接 k=3 更有性价比。

### T8. 保守平局判定（unique winner + tie counts as incorrect）—— [改造后采用]
- 改造点：RB2 是"选出唯一最优"，我们是"每维独立打分"；平局场景发生在"多轮答案对比/组合评判"时。一致化出现"多个候选并列最优"时应显式降级（不静默取第一个）。
- 理由：原文用严格平局判定避免奖励判别力差的 judge；该原则可迁移到 K2 评测协议的多候选项比较。

### T9. 一维一个判定调用（粒度对齐）—— [改造后采用]
- 改造点：RB2 每响应一次打分；我们把"整答四维一次性打分"拆成"每维一次 judge 调用"（faithfulness / numeric_correctness / citation_quality / refusal_appropriateness 分开打）。
- 理由：判据注入对"单一语义"更聚焦；且跳维失败互不影响（现单 prompt 四维，一整 JSON 一个 parse 失败全丢）。代价：4× 调用；建议先在部分维（numeric/faithfulness）做 A/B 验证再全量切。

### T10. 输出解析鲁棒性（parse 失败重试 + 兜底）—— [直接采用]
- 理由：论文对 unusable 输出重试≤3 次（parse 提取最后一个整数）；我们 `_extract_json` 已有 f-string/markdown 剥离 + 失败兜底评分。补充：失败时明确计数（不可判题数）而不是静默给 0 分，进 K2 报告。

### T11. 聚合前的方差报告—— [改造后采用]
- 改造点：把每次 judge 的 score+reason 都留档（当前脚本只存 report），聚合时输出每题每维的 mean ± std；std 高即"待人工复核候选"。
- 理由：与 T6 一致；方差本身就是错误信号（图 1：错误判定方差更高，r=-0.13 弱相关但方向上一致）。

### T12. 一致性介入的门槛化—— [改造后采用]
- 改造点：把"同答 3 次漂移 >1 分"改为"同答 k 次，某维 std > 阈值 → 该维重评 + 人工复核"；并保留"整答级一致性 STABLE"作为低预算口径。
- 理由：论文的方差路由本质是"不确定性→升级处置"；我们已有的 DRIFT 机制就是它的低成本版。

### T13. 类别敏感性（Precise IF 类最难的教训）—— [改造后采用]
- 改造点：我们四维里最接近齐的难类是 numeric_correctness 与 citation_quality（约束/格式相关）；对这两维单独统计一致性（不在整答级合并），因为 RB2 的 Precise IF 类（~34–53%）对格式约束最挑。
- 理由：论文发现格式约束类是 judge 最难区分的（Precise IF 26–53%）；我们 citation 的豁免规则（拒答题来源为空不扣分）就是这类易混淆边界。

### T14. 长上下文告警—— [不适用（当前）]
- 理由：RB2 平均 ~576 token，论文自认未验证长上下文扩展；我们四维 judge 上下文 ~6k–9k token（context[:6000]+answer[:1500]+sources[:1500]），若要上长文档/多轮，需独立小实验验证（K2 可挂）。

---

## 3 一致性/防漂移专项（本项目已观察到"同答案重复打分漂移"）

现状事实（`m2_eval_judge_consistency.py` 与审计 08-11/08-16 记录）：
- 已实现：同答 3 次、per-dim spread、spread>1 即 DRIFT；07-11 抽查 3 题 spread 全 0（STABLE 结论入台账）。
- 已知风险：temp=0 非真正确定性（T4）；整答级四维单 prompt 的 parse 失败会整题丢分（T9 改造点）；跨进程/GPU 未验证（T4）。

防漂移建议按优先级排（来自本节 T2/T4/T9/T12）：
1. k=3–5 均值化打分（T2）——治标；
2. temp=0 口径标注与跨环境复验（T4）——防虚标；
3. 每维独立调用 + 失败计数（T9）——防静默丢分；
4. 方差→人工复核队列（T6/T11/T12）——把未知当已知管理。

---

## 4 精读范围声明（Judge 篇）

- 页数：22 页正文+附录（文本 1077 行）。已读：摘要、§1、§2（Related Work 全部）、§3（dataset/protocol/models/base prompt）、§4（五技术全部方法，含公式 1–6 与图 1/2）、§5（main results、分析、表 5–8、图 3–8）、§6（Discussion/limitations）、§7（Conclusion）、附录 A（prompt 模板）/B（分类 CI 表）/C（intersection 表）。
- 跳过：仅参考文献列表（§References）未逐条读；无其他章节跳过。
- 图表信息：图 1/2（方差分布与相关性）、图 3/5/6/7/8/9/10（准确率/成本曲线与 Pareto 前沿）为文本无法恢复的图形，关键数值与结论均已从正文提取标注。
