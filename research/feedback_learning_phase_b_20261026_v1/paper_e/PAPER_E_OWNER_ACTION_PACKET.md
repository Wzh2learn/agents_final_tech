# Paper E Owner Action Packet

日期：2026-10-26（Asia/Shanghai）
状态：`OWNER_DECISION_REQUIRED / NO_EXTERNAL_ACTION_PERFORMED`

本包只汇总现有两案例稿件与投稿包，不构成投稿、付款、签字、公开发布或外部联系授权。

## 1. 条件式路线建议

### 建议

**条件主选：ICAART 2027 Regular Paper。顺序备选：SN Computer Science 的订阅制（APC=0）路径。**

这不是接收率比较，也没有可靠的 ICAART 分轨接收率证据。稿件身份必须保持为
`BOUNDED_TWO_CASE_MEASUREMENT_AUDIT`：恰好两个计数案例，FinQA 嵌套在 Case 1 内；
不得把 C2/C3 加成 Paper E 第三案例，也不得外推为通用 Agent 方法。

### Switch rule

仅当以下四项同时为“是”，Owner 才可授权按 ICAART 路径上传：

1. Owner 能在 **2026-10-29 AoE** 前明确授权现有 12 页包；
2. 接受作者必须报告/现场参与、会议登记费和未知旅行成本；
3. 学校明确接受 SCITEPRESS/ICAART 会议论文集的认定要求；
4. Owner 能完成作者、单位、联系方式、ORCID、专利和 AI 披露等身份敏感字段。

任一项为“否”，则 **不提交 ICAART**。同一两案例稿件可转成 SN Computer Science
单盲投稿包，但仍须 Owner 对转换后的完整作者页、Declarations、许可和投稿动作逐项授权。
如果 ICAART 已提交，只有在收到拒绝或完成撤回这一终端决定后，才可启动备选路线；
禁止同时投稿。

### 当前稿件身份

- 当前审查 PDF：`research/publication_thesis_goals_v1/G1_SUBMISSION_PACKAGE/PAPER_E_ICAART_REVIEW.pdf`
- 12 页；SHA-256：`30aa05af73e05c5e64f324014f982547b46f7166448f256425b5de0ca990b013`
- Canonical Markdown：`paper/saner_rene_manuscript_v1.md`，41,515 个非空白字符，
  SHA-256 `d93577338f2991c867c0f522d3e27fc6cd4286141277bb92d48cafa4c76aff74`
- ICAART TeX：`paper/icaart_2027_submission_v1/manuscript.tex`，41,013 个非空白字符，
  SHA-256 `ec30dd1f091f9b2196be870f91cf0472775367e5c57fb9886d92631e118adee1`
- 当前包审计：`research/publication_thesis_goals_v1/G1_SUBMISSION_PACKAGE/G1_ICAART_PACKAGE_AUDIT_20261025.json`，
  `PASS`；引用 24/24；匿名化、格式、哈希、交叉版本一致性和私有候选工件检查均通过。
- `research/feedback_delivery_continuation_20261025_v1/PAPER_E_ROUTE_ADAPTATION_RESULT_20261025.json`
  已标记为 `PRE_MANUSCRIPT_ADAPTATION_ROUTE_SNAPSHOT`；其中 11 页/40,284 字符是适配前状态，
  当前提交状态以包审计和 manifest 为准。

## 2. 12 页方案的已知成本与约束

### ICAART

| 项目 | 当前已知边界 |
|---|---|
| 篇幅 | Full 12 页，Short 8 页；最多 4 个付费附加页，EUR 50/页 |
| 截止与日期 | Regular 第二阶段 2026-10-29 AoE；通知 2026-12-04；camera-ready/登记 2026-12-18；会议 2027-02-23 至 2027-02-26，Valletta |
| 当前 12 页已知费用 | 被接受为 Full：早期非会员演讲者 EUR 680；早期 member/sponsor EUR 620 |
| Short 条件场景 | 若被接受为 Short 但保留 12 页，需 4 个附加页 EUR 200；早期非会员合计 EUR 880。该场景取决于 venue 最终认定和版式，不是已知可选项 |
| 可选活动 | 早期 social event EUR 80；已知费用区间因此为 EUR 680–960（Full/Short 条件和可选活动），不含旅行 |
| 迟交场景 | 非会员演讲者 late EUR 795；member/sponsor late EUR 725；若 Short 保留 12 页再加 EUR 200 |
| 取消规则 | 2026-12-22 前取消，退款扣除 EUR 100；之后不退款 |
| 评审与发表 | 双盲，至少两位、通常三位以上评审；在线论文集发表要求作者报告 |
| 报告形式 | Full 为 25 分钟口头；Short 为 20 分钟口头或 poster；口头作者可改 poster；online 模式仍须直播参与。确切 oral/poster、现场/线上安排在录用前未知 |
| 登记时点 | 早鸟登记截止 2026-12-18 AoE；演讲者 onsite price 在已核对页面未列出 |

### SN Computer Science

- 订阅路径：submission、page、color 和 APC 均为 0；无强制会议报告。
- 可选 OA：GBP 2,390 / USD 3,290 / EUR 2,690，另加适用税费；价格按接受日期确定。
- 评审为单盲，至少两份；已核页面给出的 median submission-to-first-decision 为 96 天，
  但不是录用或发表保证。
- 转换要求：150–250 词结构化摘要；单盲作者页；正式 Declarations；
  Methods/适当地点保留 LLM 使用披露；提交 LaTeX/BibTeX 和图源等可编辑源文件。

## 3. Owner 必须授权的精确外部动作

以下是动作清单，不是已执行清单。A-PAPER 未执行其中任何一项。

| Owner 决策/动作 | 需要 Owner 提供或确认 | 当前状态 |
|---|---|---|
| 路线裁决 | ICAART 条件主选 + 顺序备选；或明确立即切换 SNCS | `OWNER_REQUIRED` |
| 投稿唯一性 | 确认不同时提交，并记录 ICAART 终端决定 | `OWNER_REQUIRED` |
| 作者身份 | 作者顺序、申请人一作身份、BUPT 第一单位、通讯作者、邮箱、ORCID | `UNRESOLVED` |
| 专利/受限技术 | 确认无专利限制或提供内部审批状态 | `UNRESOLVED` |
| AI 使用披露 | 批准精确披露文本，并决定是否另列 OpenAI Codex software citation | `OWNER_REQUIRED` |
| 工件与许可 | 决定匿名补充、录用后仓库/DOI、发布时间和代码许可；先处理 FinRank CC BY-NC 4.0 与 TAT-QA 来源条款 | `OWNER_REQUIRED` |
| PRIMORIS 表单 | 登录后核对可填字段、上传结果和 supplementary handling；未登录前不得猜测 | `NOT_OBSERVED` |
| 提交动作 | 授权上传稿件并确认 no simultaneous submission | `NOT_AUTHORIZED` |
| 版权/许可签字 | 授权版权、许可或 venue 表单签署 | `NOT_AUTHORIZED` |
| 费用与旅行 | 批准登记费、附加页、可选活动、机票、酒店、签证、当地交通、保险和资金来源 | `TRAVEL_COST_UNKNOWN` |
| 学校认定 | 提供精确认定规则，确认 ICAART/SCITEPRESS 和 SNCS 分别是否满足 | `OWNER_REQUIRED` |
| 论文答辩时间线 | 提供 2027 年 10 月评审的确切日期；不得假定 10 月 31 日 | `UNRESOLVED` |

### 当前外部动作回执

- submission：`false`
- payment：`false`
- copyright/license signature：`false`
- public release：`false`
- author email/external contact：`false`

## 4. Owner 最小决策格式

Owner 可按以下格式一次性回复：

```text
ROUTE=ICAART | SNCS | HOLD
SCHOOL_RECOGNITION=CONFIRMED | REJECTED | UNKNOWN
AUTHORS=[name order, corresponding author, ORCID, email]
BUPT_FIRST_AFFILIATION=YES | NO
PATENT_STATUS=CLEAR | RESTRICTED | UNKNOWN
AI_DISCLOSURE=APPROVED | REVISE
SEPARATE_CODex_CITATION=YES | NO
ARTIFACT_RELEASE=PRIVATE_REVIEW | ANONYMOUS_SUPPLEMENT | POST_ACCEPTANCE_REPOSITORY | HOLD
LICENSE=APPROVED | HOLD
REGISTRATION_TRAVEL=APPROVED | HOLD
THESIS_REVIEW_DATE=YYYY-MM-DD or UNKNOWN
SUBMISSION_AUTHORIZATION=AUTHORIZED | NOT_AUTHORIZED
```

在 `SUBMISSION_AUTHORIZATION=AUTHORIZED` 且表单、路线、学校认定和身份字段均完成前，
不得上传、付款或签署。

## 5. 路线证据

- 路线适配：`research/feedback_delivery_continuation_20261025_v1/PAPER_E_ROUTE_ADAPTATION_20261025.md`
- 路线快照：`research/feedback_delivery_continuation_20261025_v1/PAPER_E_ROUTE_ADAPTATION_RESULT_20261025.json`
- 12 页包审计：`research/publication_thesis_goals_v1/G1_SUBMISSION_PACKAGE/G1_ICAART_PACKAGE_AUDIT_20261025.json`
- 包 manifest：`research/publication_thesis_goals_v1/G1_SUBMISSION_PACKAGE/PACKAGE_MANIFEST.json`
- Owner 待办：`research/publication_thesis_goals_v1/G1_SUBMISSION_PACKAGE/OWNER_DECISIONS_REQUIRED.md`
- Phase A 治理返回：`docs/governance/audit/loop_d_control_review/PHASE_A_RETURN.md`
