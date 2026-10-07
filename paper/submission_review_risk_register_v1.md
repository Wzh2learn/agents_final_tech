# 小论文投稿前 reviewer 风险登记 v1

> 状态：内部审稿风险登记，不是投稿许可 | 更新：2026-10-04
> 来源：双模型审稿原件、步级链路审计、投稿包审计、Office 视觉验收
> 判定口径：blocking = 阻止投稿；should-fix = 投稿前应处理；controlled = 已有正文边界；pending-external = 等用户/venue/专利外部确认

## 1 风险表

| id | 风险 | 严重度 | 当前证据 | 状态/处置 |
|---|---|---|---|---|
| RR-01 | matched-FPR `[0,0]` 区间看起来退化，审稿人可能质疑 | should-fix | §5.2 已补 single-varying-leaf 仿射分数推导，明确 `[0,0]` 是退化支持集而非一般等价定理 | **closed**；主稿已补推导，数字/结论不变 |
| RR-02 | 112 > 96 的首读悖论 | should-fix | Abstract 与 §5.2 已明确 checkpoint visibility 与 protocol detection 是不同信号，不是 96 的分区 | **closed**；保留显式解释 |
| RR-03 | 单一公开表格语料、单 varying leaf 的外部效度 | major limitation | §5.2/§6 明确不主张普适性；第二数据流仍 pending | **controlled/open**；必须保留在 Limitations |
| RR-04 | step-level scorer 的低保真度被误读为检测能力 | should-fix | SP-C5 = `attempted_stopped_by_preregistration`；0.0298/0.2233 停止条件触发；detection/localization 禁止作为能力结论 | **closed**；V2-3 已关闭，不开 v3 |
| RR-05 | 匿名预览中的 artifact 路径/模型身份脱敏后，复现细节不够 | should-fix | `submission_draft_arr_www_anonymous_v0.md` 禁词 0；`reproducibility_statement` 列出可公开候选与不外发边界 | **pending-external**；venue 版需补匿名补充材料编号 |
| RR-06 | venue 模板、作者/单位、匿名、专利门未完成 | blocking-submission | `submission_package_audit` 明确 `PENDING_EXTERNAL_ITEMS` | **open**；不得投稿/上传/公开 |
| RR-07 | Related Work 部分 venue 标签未全部核验 | should-fix | `references_v0` 坚持未核 venue 写 `arXiv preprint`；15 条主稿引用集合已机械闭合 | **controlled/open**；venue 官方核验后才能改 |
| RR-08 | 图表在打印尺寸下的可读性 | should-fix | 叙事修订版 DOCX 已重建，GB10 PDF 8 页，抽样 1/4/5/8 页 PASS；Figure 2 与 Table 1 完整 | **closed for internal review**；camera-ready 仍需 venue 版式复验 |
| RR-09 | round5 N-1/N-2 簿记/证据锚点 | minor | N-1 `audit_status=round5` 已更新；N-2 已补 FinQA process structure evidence，claims 74/74 | **closed** |
| RR-10 | Loop B `adv_cross_doc` 间歇 source retrieval 缺失 | operational | `5f82efb` 自然周期 `sources empty`，上一周期同题 PASS | **tracked**；不阻塞论文文本，不隐藏、不重置 |
| RR-11 | 标题/摘要未把反直觉结论放在首屏 | should-fix | 已改为 `Visibility Is Not Detection`，摘要、Introduction、结果标题与 Conclusion 同步 | **closed**；写作层修复，不改数字或 claim |
| RR-12 | 第二数据流、独立 scorer 与多 leaf localization 证据不足 | major limitation | 当前仍为 deferred/unestablished；计划见 `teacher_review_readiness_v2.md` | **open**；只允许 future work，不升级当前主张 |
| RR-13 | 社会价值场景过于单一 | should-fix | 当前只保留金融文档动机；通用场景列入 readiness backlog | **pending**；后续可在不改变技术结论的前提下扩展场景 |

## 2 首要投稿前动作

1. 取得 venue 官方模板/CFP，确定页数、匿名、References 和 supplementary policy。
2. 在不改变 claim/evidence 的前提下生成 venue 版 PDF，补齐作者/单位并复验图表打印尺寸。
3. 专利确认后再决定任何外发、arXiv 或代码公开。
4. 146 列 Q3 已完成 R1/R2/ADJ 并封存 raw/ledger/hash，但带 visibility exceptions；它只作为 exploratory learnability evidence，不进入 Stage E 保底稿结果，也不得升级为 Stage D/RQ2。

## 3 当前判定

没有发现新的 manuscript blocking issue；当前 blocking 全部是外部投稿条件，不能用内部 mechanical audit 绿灯替代。
| RR-14 | 仍被误读为 hierarchical evaluator 方法论文 | should-fix | 标题、Abstract、贡献和 Method 均明确 measurement validity；hierarchy 明示为 instrument | **closed**；身份已收敛 |
| RR-15 | 被误读为 schema-matching robustness 论文 | should-fix | §4.1 明示 schema/header matching 是 perturbation carrier，研究对象是 observation boundary | **closed for positioning**；跨 pipeline 泛化仍是 evidence ceiling |
| RR-16 | visibility / detection / harmfulness 概念混淆 | should-fix | §3.2 增加 visibility × detection 矩阵，harmfulness 明确为 orthogonal annotation | **closed** |
| RR-17 | single responsive leaf 被掩盖 | major limitation | Abstract、§3.1、§5.2、§6.1 和 Conclusion 均明示 localization 未建立 | **controlled/open**；等待导师决策后续证据优先级 |
| RR-18 | null result 被解释为方法失败 | should-fix | §5.2 明示 threshold confounding diagnostic；PSO 明示 informative null；Stage R 明示 boundary case | **closed** |
