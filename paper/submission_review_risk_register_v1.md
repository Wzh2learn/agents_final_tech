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
| RR-08 | 图表在打印尺寸下的可读性 | should-fix | Office 8/8 + 4/4 视觉 PASS；Figure 2 柱顶 absorbed 标签修复 | **closed**；camera-ready 仍需 venue 版式复验 |
| RR-09 | round5 N-1/N-2 簿记/证据锚点 | minor | N-1 `audit_status=round5` 已更新；N-2 已补 FinQA process structure evidence，claims 74/74 | **closed** |
| RR-10 | Loop B `adv_cross_doc` 间歇 source retrieval 缺失 | operational | `5f82efb` 自然周期 `sources empty`，上一周期同题 PASS | **tracked**；不阻塞论文文本，不隐藏、不重置 |

## 2 首要投稿前动作

1. 取得 venue 官方模板/CFP，确定页数、匿名、References 和 supplementary policy。
2. 在不改变 claim/evidence 的前提下生成 venue 版 PDF，补齐作者/单位并复验图表打印尺寸。
3. 专利确认后再决定任何外发、arXiv 或代码公开。
4. 146 列 Q3 仍只作为 exploratory 输入包；只有 token/授权满足后才派发 R1/R2/ADJ，并先做独立审计。

## 3 当前判定

没有发现新的 manuscript blocking issue；当前 blocking 全部是外部投稿条件，不能用内部 mechanical audit 绿灯替代。
