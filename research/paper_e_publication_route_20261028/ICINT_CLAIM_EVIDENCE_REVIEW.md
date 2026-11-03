# ICINT 短稿：主张、证据及尚待核对事项

> 2026-11-03：Gemini 的修订稿与核查表已作为[历史审阅输入](archive/20261103_gemini_review.zip)保留，压缩包内 manifest 绑定原文哈希；现役为 [ICINT 正文](paper_e_icint_draft.md)和 [4 页 PDF](icint_latex/main.pdf)，更新三项文献出处后的 PDF SHA-256 `0425b9e74c7a6c18fe1f27e49149680fb48823047754cc50bf87cf39a48515a6`；此前 Gemini 修订版 PDF SHA-256 `8143d3759a4d3839798b30c069cd37ddd4f9b9c6e56cf11540953a274843c5b7` 保留于 Git 历史。Gemini 建议经项目侧数据与代码复核后选择性吸收，不把 AI 审阅当作外部同行评审或作者团队终审。

本次对既有证据的核对：保存的逐表/逐注入圆整分数上，flat `>=2.0` 与 hierarchical `>=0.75` 分别选中完全相同的 `75/95` 表与 `85/118` 注入。另一 strict `>1.0` / `>0.375` 网格的 24 个 H/HI 标签注入在 GB10 使用冻结输入离线重建，两者选中同一批 21 个；前一次仅凭汇总数无法确认集合，本次已消除该不确定性。重建使用 [D3 的 load_corpus / g1_reproduce](../paper_d3_matched_fpr_stage_a.py) 和 [matched-grid 的 clean 筛选与分折实现](../stage_e_method_revision_20261009/stage_e_matched_fpr_reanalysis.py)：对排序后的 clean 与 H/HI 表 UID 取索引模 5 选 fold 0，再以 `(uid, col, type)` 比较两规则选中的集合。重建得到 2,382 clean 表、111 个 H/HI 注入、fold 0 的 24 个注入及相同的 21 个命中。两项不是新样本或生产阈值定标。

叙事上明确了两个 BM25 配置、早期本地指标实现修正、加一 Monte Carlo 公式及同一 sign-flip 检验校正前后的 p 值。Gemini 将 FinRank 未解复现差异直接归因于环境或预处理的说法未被采纳；现稿直接报告差异及原因未解。此次 GB10 离线重建无模型、judge、训练或端点调用。

### 2026-11-03 补充：逐查询统计的另一套实现复核

使用保存的六系统逐查询分数及不同随机种子，在 GB10 的 Python 3.12.3 环境由 [SciPy + statsmodels 复核脚本](review_saved_query_statistics.py)重新执行两个数据集共 30 组配对符号翻转检验；每对 200,000 次抽样，分别在五个词法系统的 10 对和六系统的 15 对内做 Holm 校正。三个配对的穷举例、完全相同输出和已知 Holm 例均通过控制。结果与此前 200,000 次分析的**全部配对显著性判断一致**：词法系统在 SciFact 为 2/10、NFCorpus 为 1/10；六系统分别为 4/15 和 6/15。新的模拟中 BGE 与 BM25(1.2, 0.75) 的 Holm 值分别约为 0.06798 和 0.01476；原稿仍报告旧种子对应的 0.066000 和 0.015540，二者无需混写。

复核使用的是同一批已保存数据，不是新样本或人工统计评审，也未验证查询独立性等推断假设。逐对结果见[统计汇总](scipy_signflip_review_20261103.json)。输入与执行脚本的原始字节 SHA-256 分别为 `b4596b01db7557570f644fcecf0325af6a18261637e47b6c9e112480fb87acdc`、`3be21920756a8a0bd4617bad98f08d4e1c8a3747ce697ac6483404b666d9c15e`；执行回执原始字节 SHA-256 为 `1abd5468211d6c96d5ef1f5e4a5f506993eb0e5a551eb0fa509725e4f32405ad`，原始副本保存在 GB10 `/home/testuser/wzh/research_evidence/paper_e_20261028/stats_review_20261103/scipy_statsmodels_200k_v2.json` 和本机 `D:/Documents/Loop_D_assets/paper_e_statistics_review_20261103/scipy_statsmodels_200k_gb10_v2.json`；Git 工作树可能进行换行转换。此复核无模型调用、训练或新检索实验。

### 2026-11-03 补充：相关工作原始出处

针对现役稿核验了相关工作的作者、标题与载体：[FinRank](https://arxiv.org/abs/2608.07400) 与 [Caban 的有效性分析](https://arxiv.org/abs/2608.00794)对应当前 arXiv 编号；[AgentSuite 的 PMLR 页面](https://proceedings.mlr.press/v306/suh26a.html)确认 ICML 2026、卷 306 与页码。原稿以预印本引用的三篇工作有正式会议出处：Ross 等为 [COLM 2024](https://openreview.net/pdf?id=LFfktMPAci)，Bean 等为 [NeurIPS 2025 数据集与基准轨道](https://proceedings.neurips.cc/paper_files/paper/2025/hash/1967e0fc3aa6cbbace562f5cb8e3954e-Abstract-Datasets_and_Benchmarks_Track.html)，Soric 等为 [KDD 2026](https://soricm.github.io/table-extraction-benchmark/)；现役稿已改用对应会议出处。此项核验改善引用信息，不改变实验结果，也不意味着全部文献、底层数据许可或模型权重版本均已核完。

2026-10-30 科研负责人逐项对照，列出主张的可追溯证据。2026-11-02 当时的 ICINT 稿及 IEEE 双栏审阅 PDF 沿用这些案例，新增材料说明与 AI 披露候选；当时 PDF SHA-256 是 `68c594b6b1a43dc0ede95485000ecf4e4d2e4cf8c963f662af9f966111c8aaa0`。下方历史审查并未独立复审新增声明，也不是外部审稿、专家人工标注或全量原始实验的新复跑。

| 稿件主张 | 当前可追溯证据 | 此次检查及范围 |
|---|---|---|
| Case 1：95 表 / 118 注入；flat 75/95、85/118；hierarchical 20/95、13/118，原操作点是各自尺度上 `>=2` | [冻结操作点复核](../asset_revalidation_20261029_v1/operating_points_summary.json) | 记录决策标志与对应计数一致，含 12 张 flat 值恰为 2 的边界表；只复核保存结果，不是重跑全管线。 |
| 0.375 缩放和对应阈值；strict `>1` / `>0.375` 的指定折各检出同一批 `21/24` 标签注入 | [v6 阈值说明](../paper_e_agent_evidence_20261029/V6_THRESHOLD_EXPLANATION_RETURN.md)、[冻结 matched 结果](../stage_e_method_revision_20261009/matched_fpr_reanalysis.json) | 两个谓词和两个面板不得混写；仅适用于冻结 QA 和单响应叶设置。 |
| UID 聚类的 219/282 和 119 UID | [v6 正文](../paper_e_agent_evidence_20261029/paper_e_review_revision_v6.md)、[上一版提交包](../publication_thesis_goals_v1/G1_SUBMISSION_PACKAGE/README.md) | 三种子表运行不是独立表；区间是事后 UID 聚类估计。须保留 raw 及其重算路径，确认公开许可后才可能公开。 |
| Case 2：tie policy 下 TF-IDF / BM25 的 hard、random、gap | [FinRank 外部审计](../research_direction_sprint_20261020_v1/execution_v1/PAPER_E_EXTERNAL_AUDIT.md)、[独立复核](../research_direction_sprint_20261020_v1/execution_v1/INDEPENDENT_REVIEW.md) | 对照数值和统计单位为百分点；差与 gap 均在舍入前计算。身份/过滤数为源码知情的事后复现，未解决的全局差距未被解释。 |
| Case 3：自行运行的 5 系统 10 对比较，以及独立的 bootstrap 和 sign-flip/Holm | [修正回执](../paper_e_public_eval_20261028/D_BEIR_CORRECTION_RETURN_20261028.md)、[计算实现](../paper_e_public_eval_20261028/code/beir_audit.py) | 实现中每种比较默认 2,000 次，Bootstrap 与 sign-flip 为不同程序，不能把差值全部归因 Holm；未显著不证明相等。 |
| Case 3：后加 BGE 的 15 对与 200,000 次 Monte Carlo 复查 | [结果](../paper_e_evidence_followup_20261028/RESULTS.md)、[Holm 算术复核](../paper_e_evidence_followup_20261028/INDEPENDENT_HOLM_REVIEW.md)、[大文件证据位置](../paper_e_evidence_followup_20261028/EVIDENCE_LOCATION.md) | 后加 BGE 属事后探索。Holm 数值复核不等于统计假设被验证；保留私有 qrels / 分析文件和许可边界。 |
| 重复和退化对照中，尊重精确平局的点估计与配对审计都通过 | [修正回执](../paper_e_public_eval_20261028/D_BEIR_CORRECTION_RETURN_20261028.md)、[对照代码](../paper_e_public_eval_20261028/code/beir_audit_ab.py) | 不能写成审计证明优于该简单基线。 |

## 参考文献核验

已核对公开原文的标题、首作者、年份或出版渠道：[Ross](https://arxiv.org/abs/2412.13989)、[Caban](https://arxiv.org/abs/2608.00794)、[Bean](https://arxiv.org/abs/2511.04703)、[FinRank](https://arxiv.org/abs/2608.07400)、[BEIR](https://datasets-benchmarks-proceedings.neurips.cc/paper_files/paper/2021/hash/65b9eea6e1cc6bb9f0cd2a47751a186f-Abstract-round2.html)、[TAT-QA](https://aclanthology.org/2021.acl-long.254/)、[FinQA](https://aclanthology.org/2021.emnlp-main.300/)、[BGE model card](https://huggingface.co/BAAI/bge-small-en-v1.5)、[AgentSuite](https://proceedings.mlr.press/v306/suh26a.html)。BGE 网页存在 `5c38ec7` 修订，但此核查本身不证明本地模型实际使用的文件 hash；实验版本仍按既有运行收据核对。上述文献核验不代替稿件全部引用上下文和作者列表的最终检查。

后续补充两篇直接相关文档评价近邻：[SCORE](https://arxiv.org/abs/2509.19345)研究生成式文档解析的语义与结构评价；[Soric et al.](https://arxiv.org/abs/2511.16134)研究异构 PDF 的表格抽取及评测，arXiv v2 页面注明为 KDD 2026 论文的扩展版本。根据公开摘要和元数据核对了本稿引用范围；两篇均已覆盖部分评价设计问题，不支持将本稿表述为首次提出文档评测或阶段评价。

### 2026-11-02 补充：当前参考文献和 BGE 权重的来源核对

- 当前四页稿的 FinRank、Caban、Bean、Ross、SCORE 和 Soric arXiv 标识、标题及首作者可分别在上列原始记录核对；[AgentSuite 的 PMLR 原始页面](https://proceedings.mlr.press/v306/suh26a.html)确认为 ICML 2026、卷 306、116300–116319 页。[BEIR 正式论文集页面](https://datasets-benchmarks-proceedings.neurips.cc/paper/2021/hash/65b9eea6e1cc6bb9f0cd2a47751a186f-Abstract-round2.html)使用稿件中的 `Heterogeneous` 拼写；arXiv 元数据拼作 `Heterogenous`，这是来源差异，不应盲目按 arXiv 改写已引用的正式论文集标题。
- [Bean 等人的 NeurIPS 2025 论文集记录](https://proceedings.neurips.cc/paper_files/paper/2025/hash/1967e0fc3aa6cbbace562f5cb8e3954e-Abstract-Datasets_and_Benchmarks_Track.html)可作为比当前 arXiv 引文更具体的发表版本；Soric 等人的 [KDD 2026 作者版](https://pierre.senellart.com/publications/soric2026benchmarking.pdf)与正文引用的 arXiv v2 扩展版不是完全相同的版本，如更换引文须重新核对相应主张。这些是后续作者修订建议，不在 Gemini 当前审阅期间静默替换 PDF。
- [Hugging Face 固定版本的元数据](https://huggingface.co/api/models/BAAI/bge-small-en-v1.5/revision/5c38ec7c?blobs=true)给出的完整 revision 为 `5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`，其中 `model.safetensors` 的 LFS SHA-256 为 `3c9f31665447c8911517620762200d2245a2518d6e7208acc78cd9db317e21ad`。它与原始 dense run 收据 `dense_probe.json` 中记录的 revision、weight hash，以及 2026-11-02 GB10 对该缓存权重文件实际重算的 SHA-256 一致；该收据本身 SHA-256 为 `c7833c9bb78ca0246e25c13e0518fbe39bfa11b5bc5a68491154355cd1a4e738`。这把本稿引文版本与**已记录的权重文件**对应起来；不证明所有 tokenizer、依赖、其他文件及软件环境均已复现，也不是新跑的稠密检索实验。

## 2026-10-30 首次读者视角的叙事修订与构建复核

2026-10-30 快照中的短稿新增三案例总览表：分别说明“较低检测率是否意味着较弱排序”“绝对分数变化是否改变比较方向”和“均值排序是否支持每个配对”。该表不引入新实验或新的普遍理论；对应证据和范围仍分别由上面的操作点、FinRank 和 BEIR 条目支持。正文明确区分考察过的结论保持稳定、结论需要收窄和未能排除相等；不把无显著结果表述为两系统相等。

该快照用 ICINT 官网模板中的 IEEEtran class 和 Springer 官方 LNCS class 生成：ICINT PDF **4 页**，SHA-256 `e7db8986a315bd7ba147c6b1dd674d3205b106a9a18458ae6b59cffec511f47b`；ICDAR 模板预演 **8 页**，SHA-256 `6ffd22d05f94120ff52c5e18107b6cc9f11940cc57f674405faa6fb8bd5a22ee`。该快照的 ICINT 四页和 ICDAR 新表页已渲染检查，表格可读；两份 PDF 元数据均无 Author 字段，引用首次出现顺序与文献序号为 1–11，编译日志无 overfull 和 undefined references。仍有 underfull、Windows Fontconfig 提示，Poppler 的字符映射文件路径也产生提示。以上是工程和叙事自查，**不是**对匿名性、每项结果、统计假设或外部原创性的完整证明；独立首次读者/统计评审仍待完成。ICDAR 文档分析定位还需实质改写。

2026-10-31 稿件的机器审读、数值归属修正、复现信息及 200,000 次词法配对数值敏感性重算见 [审稿与复核回执](ICINT_AI_REVIEW_RETURN_20261031.md)；这是历史审查记录，不能替代对 2026-11-02 现役 PDF 的首次读者复核。

## 投稿级未完成事项

- [机器首次读者审稿计划](ICINT_AI_REVIEW_PLAN_20261030.md)只针对冻结短稿，以本地模型的两个独立上下文提供辅助意见；结果须逐项核验，不等同人工或同行审稿。
- 首次读者复核仍需针对当前 **4 页 PDF**，尤其是单位、图表、统计假设、可重复性和独立性；先前独立 AI 评审对应其他版本，不能当作本稿通过。
- 会议官方 2027 论文集出版方、学校认可和参会/远程展示凭证仍待核实；[ICINT 作者说明](https://www.icint.org/submission.html)规定 4–8 页及双盲，官网信息应在投稿前再次核对。
- 作者身份、第一单位、AI 披露措辞、材料公开许可及专利等需作者最终确认；不能凭缺省内容推断。当前稿为匿名审阅稿，不是已正式授权提交。
