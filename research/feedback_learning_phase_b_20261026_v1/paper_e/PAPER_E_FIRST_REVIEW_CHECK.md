# Paper E First-Reviewer Scientific Check

日期：2026-10-26
结论：`NARROW_BOUNDARY_DEFENSIBLE / STRONGER_NOVELTY_NOT_SUPPORTED`

## 1. Contribution boundary

最强可辩护贡献是一个**可复现的、有限范围的测量审计**：在两个评价构造中，把观察面、
检测谓词、契约相对有害性、分数/平分敏感性、决策稳定性和复现边界分别绑定到同一
因果更新后的测量对象。稿件提出六步复核清单作为 application-ready proposal，
不是已经验证的普适方法。

必须保留的“不主张”：

- 不主张通用 Agent 评测理论或一般 Agent 系统覆盖；
- 不主张通用 detector ranking、自然缺陷率或普适 OCR 盲点；
- 不主张 flat 与 hierarchical 评分普遍等价；
- 不主张 FinRank 作者错误或主要 hard-negative 结论被推翻；
- 不主张 C2/C3 是第三个案例、已建立创新或跨来源泛化；
- 不主张“恰好复现”覆盖所有平台、依赖和未存 score matrices。

## 2. Nearest neighbors

| 近邻 | 已覆盖内容 | Paper E 的窄增量 | 不可越界 |
|---|---|---|---|
| Caban, *Measurement Without Validity*（arXiv:2608.00794） | Agent AI 评价的复合测量可靠性、三层 validity 框架 | 在具体构造中逐项绑定 observation surface 和 dataflow | 不再声称一般 validity/checklist 是新方法 |
| Bean et al., *Measuring What Matters*（arXiv:2511.04703） | 445 个 LLM benchmark 的 construct-validity 审计和 21 项编码表 | 用确定性重构解释具体分数、阈值、身份和复现边界 | 不声称通用 construct-validity 清单为新 |
| Jouseau et al.（DOI `10.1007/978-3-031-87327-0_11`） | 数据内在质量指标 | 审计既有测量契约，而非提出通用质量指标 | 不声称 universal quality metric |
| Bastos Germano et al.（DOI `10.1007/978-3-032-25032-2_14`） | 合成 Java 漏洞数据中的隐性偏差及偏差清洗后的 detector 准确率变化 | 分离 visibility、detection、harmfulness、score sensitivity、decision stability、reproduction gap | 不把两案例外推为数据偏差通用理论 |
| FinRank（arXiv:2608.07400） | 1,185 条记录、硬负例、tie-positive 规则和作者披露的 source limitations | 审计 tie contract、source identity、报告对象和残余复现差异 | 不宣称构建新 financial-QA benchmark，也不宣称作者主要结论失败 |
| Karamousalidis & Kefalas（DOI `10.1007/s42979-026-05242-8`，可见页面摘要级核对） | 多智能体 logic-programming benchmark、LLM-as-judge 和可靠性分析 | 审计评价测量对象、tie/identity contract 和决策稳定性，而非新建 benchmark framework | 不把摘要级可见页面核对写成全文复现 |

## 3. Units, clustering and post-hoc labels

### Case 1

- 主要注入对象是 95 张表、118 次合成 header injection、6 个 family；
  主冻结面为 96/118 visible、22/118 silently absorbed。
- OCR-like 为 0/13 visible，分布在 11 个 source-table clusters，并在五个阈值下均不可见；
  这只是观察面结果，不是 harmfulness 或 false-negative rate。
- 三 seed 的 table-run 点估计为 219/282=0.7766，但只对应 119 个唯一
  source-table UIDs；重复 UID 必须按 cluster 处理。
  post-hoc UID-cluster bootstrap 为 [0.7117, 0.8364]；等权 UID 估计为 0.7535，
  区间 [0.6835, 0.8207]。不得把 282 当作独立样本量，也不得把三个 seed 外推为总体分布。
- 2,382 条 clean records 的分数支持为 `{0}`，因此 clean-only 面板不能识别唯一
  matched-FPR operating point。
- 阶段对齐研究有 216 次 injection、72 个 clusters；perfect separation 只在
  contract-derived、直接叶明确 instrumented 的构造内成立。移除非直接叶后
  top-1 和 macro-F1 均为 0.3333，说明结果不是层级结构自动产生的通用定位能力。
- 嵌套 FinQA 为 89 行、30 clusters；V=89/89、D=0/89、O=0/89。由于扰动未重算
  下游结果字段，它只证明 measurement-object mismatch，不估计检测能力。

### Case 2

- FinRank 使用 1,185 条记录和 TF-IDF/BM25；未审计 neural/generative systems。
- ties-positive 到 strict-win 使 TF-IDF random accuracy 变化 1.084 点、BM25 变化
  1.029 点，跨过 1.0 点 materiality threshold；
  但 hard-random gap 只变化约 0.359/0.343 点且方向不变。
- `text_sha1` 的 442 个 hard-negative occurrences、305 个 records、33 个 gold loss 和
  2 个 all-gold loss 均是 **post-hoc v2 identity correction**。
  v1 的 raw-exact 293/220 是被取代的错误身份规则，不是 FinRank 的矛盾。
- in-record MRR/nDCG 和 pair metrics 可精确复现；global 最多漂移 0.19 点，
  metadata-filtered 最多 0.16 点，第二环境最多 0.47 点。漂移原因未解决，
  因此只能写 reproduction boundary。

## 4. Result-to-claim match

| 结果 | 可支持主张 | 必须降级或保留的条件 |
|---|---|---|
| 96/118 visible；OCR-like 0/13 | visibility 随 family 改变，单一 aggregate 隐藏 family boundary | 合成注入、单 corpus；不等于 harmfulness |
| flat/hierarchical 在单一 responsive leaf 下正仿射/同秩 | 当前构造下 raw protocol gap 不能解释成 ranking quality | 不是一般层级评分定理 |
| clean support `{0}` | 当前 clean-only procedure 不能选唯一 operating point | 不等于 matched-FPR 普遍不可用 |
| 216 injection 的 1.000/1.000 | 显式 stage-aligned instrumentation 能分离开明确定义的三阶段 | 直接叶由 contract 构造，非自然失效分布 |
| FinQA V89/D0/O0 | 扰动和 detection predicate 绑定到不同对象 | 不证明协议盲、不可迁移或语义正确 |
| FinRank gap 稳定、绝对值敏感 | 窄 hard-negative 结论稳定，absolute calibration 受 tie contract 影响 | 只覆盖 TF-IDF/BM25 和作者 curated pool |
| post-hoc 442/305、33/2 | author-disclosed canonical identity 可确定性重现 | 不是独立、前瞻、冻结应用 |
| 复现漂移 | “exactly reproducible”需平台、完整环境、score matrices 或 tolerance | 原因未解决 |

## 5. Limitations that must remain visible

1. Case 1 是一个公开表格 corpus 上的合成扰动；119 个 source-table UIDs 不能估计自然失败分布。
2. harmfulness 使用契约相对判断；单一 judge 把 13 个 OCR-like cases 判为 referentially equivalent，
   但该 judge 不是独立 human semantic gold。
3. 28-case 语义边界分析只有一个 judge；perfect localization 来自显式 instrumented 构造。
4. FinRank v2 在看到 v1 身份错误后进行修正，不是第二项完全冻结、盲法应用。
5. FinRank 未覆盖 neural/generative baselines；残余 global/metadata 漂移没有唯一解释。
6. ICAART 近邻比较主要为摘要、元数据和可见页面；Bastos PDF 请求只返回 HTML access page，
   不得声称全文复现。
7. Paper E 的六步清单仍缺第二个、因果对齐且真正冻结的独立数据流验证。

## 6. First-review recommendation

### 可提交的主张

> A reproducible measurement audit can separate score-contract sensitivity from decision
> stability in a real evidence-ranking benchmark and expose a residual reproducibility
> gap consistent with tie-order or environment drift, while a controlled staged evaluator
> shows that visibility, predicate response and contract-relative harmfulness are not
> interchangeable. The proposed checklist is an application-ready review procedure, not
> a universal theory.

### 首审前仍需检查

- 对 Barr、Papadakis 等 broad oracle/mutation novelty 威胁补全文核对；
- 对 ICAART/SNCS 近邻补正式 bibliography 与可见页面访问日期；
- 在摘要、贡献、图表标题和结论中逐字扫描“universal、blind spot、agent evaluation、
  exact reproducibility、confirmed generalization”等越界词；
- 保持 12 页包的 24/24 引用、匿名化和 claim/evidence hash 检查；
- 不以“ICAART 更易接收”或“Owner 已批准”为论证。

## 7. Evidence paths

- `paper/saner_rene_manuscript_v1.md`
- `research/paper_e_contribution_reassessment_v1/PAPER_E_CLAIM_EVIDENCE.md`
- `research/paper_e_contribution_reassessment_v1/NEAREST_WORK_COMPARISON.md`
- `research/research_direction_sprint_20261020_v1/execution_v1/PAPER_E_EXTERNAL_AUDIT.md`
- `research/publication_thesis_goals_v1/G1_SUBMISSION_PACKAGE/G1_ICAART_PACKAGE_AUDIT_20261025.json`
- `research/publication_thesis_goals_v1/G1_SUBMISSION_PACKAGE/PACKAGE_MANIFEST.json`
- `research/feedback_delivery_continuation_20261025_v1/PAPER_E_ROUTE_ADAPTATION_20261025.md`
