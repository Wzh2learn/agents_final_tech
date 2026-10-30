# ICINT 短稿：主张、证据及尚待核对事项

2026-10-30 科研负责人逐项对照，适用 [ICINT 短稿](paper_e_icint_draft.md) 和同源 [IEEE 双栏审阅 PDF](icint_latex/main.pdf)。该表不是独立的外部审稿、专家人工标注或对全量原始实验的新复跑。

| 稿件主张 | 当前可追溯证据 | 此次检查及范围 |
|---|---|---|
| Case 1：95 表 / 118 注入；flat 75/95、85/118；hierarchical 20/95、13/118，原操作点是各自尺度上 `>=2` | [冻结操作点复核](../asset_revalidation_20261029_v1/operating_points_summary.json) | 记录决策标志与对应计数一致，含 12 张 flat 值恰为 2 的边界表；只复核保存结果，不是重跑全管线。 |
| 0.375 缩放和对应阈值；strict `>1` / `>0.375` 的指定折 21/21 | [v6 阈值说明](../paper_e_agent_evidence_20261029/V6_THRESHOLD_EXPLANATION_RETURN.md)、[冻结 matched 结果](../stage_e_method_revision_20261009/matched_fpr_reanalysis.json) | 两个谓词和两个面板不得混写；仅适用于冻结 QA 和单响应叶设置。 |
| UID 聚类的 219/282 和 119 UID | [v6 正文](../paper_e_agent_evidence_20261029/paper_e_review_revision_v6.md)、[上一版提交包](../publication_thesis_goals_v1/G1_SUBMISSION_PACKAGE/README.md) | 三种子表运行不是独立表；区间是事后 UID 聚类估计。须保留 raw 及其重算路径，确认公开许可后才可能公开。 |
| Case 2：tie policy 下 TF-IDF / BM25 的 hard、random、gap | [FinRank 外部审计](../research_direction_sprint_20261020_v1/execution_v1/PAPER_E_EXTERNAL_AUDIT.md)、[独立复核](../research_direction_sprint_20261020_v1/execution_v1/INDEPENDENT_REVIEW.md) | 对照数值和统计单位为百分点；差与 gap 均在舍入前计算。身份/过滤数为源码知情的事后复现，未解决的全局差距未被解释。 |
| Case 3：自行运行的 5 系统 10 对比较，以及独立的 bootstrap 和 sign-flip/Holm | [修正回执](../paper_e_public_eval_20261028/D_BEIR_CORRECTION_RETURN_20261028.md)、[计算实现](../paper_e_public_eval_20261028/code/beir_audit.py) | 实现中每种比较默认 2,000 次，Bootstrap 与 sign-flip 为不同程序，不能把差值全部归因 Holm；未显著不证明相等。 |
| Case 3：后加 BGE 的 15 对与 200,000 次 Monte Carlo 复查 | [结果](../paper_e_evidence_followup_20261028/RESULTS.md)、[Holm 算术复核](../paper_e_evidence_followup_20261028/INDEPENDENT_HOLM_REVIEW.md)、[大文件证据位置](../paper_e_evidence_followup_20261028/EVIDENCE_LOCATION.md) | 后加 BGE 属事后探索。Holm 数值复核不等于统计假设被验证；保留私有 qrels / 分析文件和许可边界。 |
| 重复和退化对照中，尊重精确平局的点估计与配对审计都通过 | [修正回执](../paper_e_public_eval_20261028/D_BEIR_CORRECTION_RETURN_20261028.md)、[对照代码](../paper_e_public_eval_20261028/code/beir_audit_ab.py) | 不能写成审计证明优于该简单基线。 |

## 参考文献核验

已核对公开原文的标题、首作者、年份或出版渠道：[Ross](https://arxiv.org/abs/2412.13989)、[Caban](https://arxiv.org/abs/2608.00794)、[Bean](https://arxiv.org/abs/2511.04703)、[FinRank](https://arxiv.org/abs/2608.07400)、[BEIR](https://datasets-benchmarks-proceedings.neurips.cc/paper_files/paper/2021/hash/65b9eea6e1cc6bb9f0cd2a47751a186f-Abstract-round2.html)、[TAT-QA](https://aclanthology.org/2021.acl-long.254/)、[FinQA](https://aclanthology.org/2021.emnlp-main.300/)、[BGE model card](https://huggingface.co/BAAI/bge-small-en-v1.5)、[AgentSuite](https://proceedings.mlr.press/v306/suh26a.html)。BGE 网页存在 `5c38ec7` 修订，但此核查本身不证明本地模型实际使用的文件 hash；实验版本仍按既有运行收据核对。上述文献核验不代替稿件全部引用上下文和作者列表的最终检查。

后续补充两篇直接相关文档评价近邻：[SCORE](https://arxiv.org/abs/2509.19345)研究生成式文档解析的语义与结构评价；[Soric et al.](https://arxiv.org/abs/2511.16134)研究异构 PDF 的表格抽取及评测，arXiv v2 页面注明为 KDD 2026 论文的扩展版本。根据公开摘要和元数据核对了本稿引用范围；两篇均已覆盖部分评价设计问题，不支持将本稿表述为首次提出文档评测或阶段评价。

## 2026-10-30 首次读者视角的叙事修订与构建复核

当前短稿新增三案例总览表：分别说明“较低检测率是否意味着较弱排序”“绝对分数变化是否改变比较方向”和“均值排序是否支持每个配对”。该表不引入新实验或新的普遍理论；对应证据和范围仍分别由上面的操作点、FinRank 和 BEIR 条目支持。正文明确区分考察过的结论保持稳定、结论需要收窄和未能排除相等；不把无显著结果表述为两系统相等。

用 ICINT 官网模板中的 IEEEtran class 和 Springer 官方 LNCS class 重新生成：ICINT PDF **4 页**，SHA-256 `e7db8986a315bd7ba147c6b1dd674d3205b106a9a18458ae6b59cffec511f47b`；ICDAR 模板预演 **8 页**，SHA-256 `6ffd22d05f94120ff52c5e18107b6cc9f11940cc57f674405faa6fb8bd5a22ee`。当前 ICINT 四页和 ICDAR 新表页已渲染检查，表格可读；两份 PDF 元数据均无 Author 字段，引用首次出现顺序与文献序号为 1–11，编译日志无 overfull 和 undefined references。仍有 underfull、Windows Fontconfig 提示，Poppler 的字符映射文件路径也产生提示。以上是工程和叙事自查，**不是**对匿名性、每项结果、统计假设或外部原创性的完整证明；独立首次读者/统计评审仍待完成。ICDAR 文档分析定位还需实质改写。

## 投稿级未完成事项

- 首次读者复核仍需针对当前 **4 页 PDF**，尤其是单位、图表、统计假设、可重复性和独立性；先前独立 AI 评审对应其他版本，不能当作本稿通过。
- 会议官方 2027 论文集出版方、学校认可和参会/远程展示凭证仍待核实；[ICINT 作者说明](https://www.icint.org/submission.html)规定 4–8 页及双盲，官网信息应在投稿前再次核对。
- 作者身份、第一单位、AI 披露措辞、材料公开许可及专利等需作者最终确认；不能凭缺省内容推断。当前稿为匿名审阅稿，不是已正式授权提交。
