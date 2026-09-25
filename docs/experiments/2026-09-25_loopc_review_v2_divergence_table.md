# 双模型独立审稿 v2 差异对照表（不合并结论、不代用户仲裁，2026-09-25）

> 状态: 对照表件（Loop D）| 两份原始审稿逐字保留，本件只做对照与处置记录
> 原件: `docs/experiments/2026-09-25_loopc_review_teacher_review_v2_qwen3.8-max.md` ·
> `docs/experiments/2026-09-25_loopc_review_teacher_review_v2_deepseek-v4-pro.md`
> 派发: 同一 evidence packet（sha256 `ef6ddc7ac80b865d5441993b6187a2cd2db1789428c925fb36d2be39cf56fb78`，61 097 B），
> 两个独立会话并发、互不可见、不 resume、不带工具；GB10 上 PID 3812664 / 3812665；各 1 turn；均正常退出无 stderr
> 审计范围: 稿件 §6 新增两段与 claim SP-C5（上次 ACCEPT 之后的增量），并做全局一致性检查

## 1 判定

| 模型 | 总体判定 | Blocking | Major | Minor | 数字核对结论 |
|---|---|---|---|---|---|
| qwen3.8-max | REVISE | 1（B-1） | 3（M-1/M-2/M-3） | 5（m-1..m-5） | 9 项全部与 artifact 一致；第 8 项为量词失准非计数错误 |
| deepseek-v4-pro | REVISE | 1（B1） | 3（M1/M2/M3） | 3（m1/m2/m3） | 9 项裸数字全部一致；唯一不一致在限定语 |

两份审稿**独立收敛到同一条 Blocking**，且都明确指出稿件数字与 artifact 无计数级偏差。

## 2 收敛项（两模型一致，已修）

| 编号 | 问题 | 两侧证据 | 处置 |
|---|---|---|---|
| B-1 / B1 | "under any proportional assignment" 是全称量化，被自引 artifact 反驳 | 附录 D §8 G-B 明文：秩分位规则「可保证簇数 ≥4 时四层非空」，而 10 ≥ 4 ⇒ 存在反例构造 | 改为 "under the frozen hash-threshold bucketing rule"；该短语已从稿件消失（grep 命中 0） |
| M-2 / M2 | criterion (i) 的 "partially met" 过于模糊，低报缺口 | SPLIT_GO 未通过（该 corpus 自身 gate/sealed 被注册表 role_fit 扣住）；label 缺口属 LABEL_GO 而非 criterion (i) | 改为逐条款映射：SOURCE_GO 通过 / UID-disjoint 簇级分配就绪 / SPLIT_GO 未通过（含被扣层事实）/ label 缺口明确归属 label gate 且为结构性 / 原递延理由（transfer corpus 缺 table layer）显式记为仍开放 |
| — | criterion (ii) 的因果焊接（qwen M-1）与「Detection figures」狗哨（deepseek M1） | 附录 C §7 明令不得称复现/替代冻结 Stage E 口径；提及 detection 存在即暗示被禁数字 | 拆为两句：候选路线被自身预注册停止条件终止；因测量对象不同（推理步检查点 vs 冻结表头注入 leaf-state），leaf-state 复现条款为 **untested 而非 failed**。含 "Detection figures" 的整句删除，分母改以中性表述给出 |

## 3 分歧项（不合并，逐条记录处置与理由）

| 议题 | qwen3.8-max | deepseek-v4-pro | 处置与理由 |
|---|---|---|---|
| SP-C5 的 status 值 | 语义准确，「不建议降级，不需要新造 status」 | 与 SP-C1..C4 分类体系不统一，建议改 `boundary_observed_not_result_claimed` | **保留原值**，另在 scope_limit 首句加入 deepseek 要求的 "This entry reports a boundary finding, not a substantive result"。理由：qwen 明确反对新造 status，deepseek 的实质关切（横向可比性、不被读作被驳回的主张）由 scope_limit 满足；改名会削弱「attempted + stopped」这一事实陈述 |
| SP-C5 的 claim 文本 | 丢掉了 "geometrically" 限定，属治理文件层面的过度主张（M-3） | 「准确概括了三条结论…未发现过度主张或不足」 | **采纳 qwen 的加限定**（更保守的一侧）：claim 现写明 geometrically fillable、SPLIT_GO remains blocked（含被扣层与 dev 层为空的成因）、以及 criterion (ii) 为 untested 而非 failed。该改动不与 deepseek 的判断冲突（加限定不会使原本「准确」的文本变不准确） |
| manuscript_tokens 覆盖面 | 应补齐 "768 report clusters"、"ten origin clusters"、"0.5"、"16% to 24%" | 缺 token 「不削弱证据链」，因两者未作为数字主张出现在 claim 文本中 | **采纳 qwen 的补齐**：token 集扩到 8 项，覆盖段落全部数字，与 SP-C1/C2 的密度对齐；并按 deepseek m1/m3 把措辞改为 "16.3% to 23.7%"（保留一位小数）与 "ten table-pair clusters"（避免与 independence_cluster 术语混淆），token 随最终措辞逐字取值 |

## 4 其余已修 Minor

- qwen m-1：§6 第二段 "are not reported" 与末段的边界报告存在口径碰撞 ⇒ 改为 "are not reported as results"，并点破末段报告的是边界量与已触发的停止条件。
- qwen m-3：「admissibility rules」在 artifact 中无逐字对应 ⇒ 改为 "whose corpus, fault families and stop condition were fixed before any detector existed"。
- qwen m-4：`paper_result = false` 的引用前置条件（须独立审计落档）⇒ 两份审稿件入仓并登记进 SP-C5 的 evidence，本件即审计结论落档。
- qwen m-5：SP-C3 与 SP-C5 的 scope_limit 逐字重复造成表面自相矛盾 ⇒ SP-C3 加归属限定（仅就其 ranking-stability 结论），SP-C5 改为边界发现表述。
- deepseek m2：单段信息密度过高、两条线交错 ⇒ 拆为两段（第二数据流 / 第二 scorer），不改内容只改结构。
- qwen m-2：SOURCE_GO 的 per-file digests 未随本次审阅包提供 ⇒ 不改稿件；该件已在 SP-C5 evidence 中登记，下轮审阅包应附上。

## 5 未采纳或延后的建议

- deepseek M3 的 status 改名：未采纳，理由见 §3 第一行（两位审稿人意见相反，取保守且不损失事实陈述的一侧）。
- 两位审稿人均建议修订后仅需对 §6 末段与 SP-C5 的 diff 做确认性复核，不需重审全文；该确认复核作为下一动作派发，其结论另件落档。

## 6 预算与纪律

本轮消耗：canary 2 turns（qwen3.8-max / deepseek-v4-pro 各 1，返回 QWEN_OK / DS_OK）+ 审稿 2 turns = 4 turns。
两份审稿并发、互不可见、不 resume、不带工具；输出逐字落档，Loop D 未编辑正文。
本件不代替任何一位审稿人的结论，也不对分歧做科学仲裁；分歧的处置理由全部显式记录于 §3。
红线：零端点、零下载、未改冻结判据、未覆盖 production 脏件、不外发。
