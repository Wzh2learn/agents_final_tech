# ICINT 短稿：机器审稿与证据复核

> 2026-11-02：此回执的 PDF hash 和页数属于当时快照，现役稿加入材料与 AI 披露候选后的版本见 [最新核验](ICINT_PREFLIGHT_20261101.md)。下方机器审读不是对新增加段落的审阅。

2026-10-31。机器审读的是 2026-10-30 冻结的 Markdown Git blob `4469384d5be81a8dff76eeba81598c07be935cf8`，不是本次修订后的稿件。方法和限制见 [审稿计划](ICINT_AI_REVIEW_PLAN_20261030.md)。两条请求使用同一 GB10 Qwen、两个不互相传递输出的上下文，只看到正文；**不是两位专家、人工标注或同行评审**。

## 有价值的意见及核验

| 意见 | 我们的证据核验与处理 |
|---|---|
| 可见性定义不够具体 | 成立。[原 runner](../k2_table_discrimination_v2.py)将已注入表头仍匹配回其原 canonical 字段判为吸收，否则计为 visible；这不是逐字符不等。冻结结果复算为 95 表、118 注入、96 visible，原 canonical 缺失数为 0。短稿已补 matcher-relative 定义；没有照搬模型建议的字符差异定义。 |
| 匹配阈值与原阈值容易混淆 | 部分成立，已补数值：平坦尺度 2 对应层级约 0.75；原协议分别在各自尺度用 2。**模型的一处算术方向反了**：它把平坦 2 错说成层级约 5.33；5.33 是层级 2 大致对应的平坦值。原操作点与另一个严格大于的匹配网格仍分别报告。 |
| 三种子聚类 bootstrap 的抽样步骤不清楚 | 成立。核对 [重算代码](../publication_thesis_goals_v1/g1_recompute_seeds.py)后，补充“按 UID 有放回抽样、每个被抽 UID 带入所有出现的 run、计算汇总比率”；这是事后条件性区间。 |
| FinRank 未量化复现差距，Gap 定义不够直接 | 成立。按 [外部审计](../research_direction_sprint_20261020_v1/execution_v1/PAPER_E_EXTERNAL_AUDIT.md)补入指定环境下 global / metadata-filtered 与发布结果的最大差值 0.19 / 0.16 个百分点，并明确 Gap = random − hard；差距原因依然未解，未采纳模型建议的“归因于已知实现差异”。 |
| BEIR 系统构造细节不足、10 对比较缺少效果量 | 成立。核对 [检索实现](../paper_e_public_eval_20261028/code/beir_audit.py)后补入标题与文本、词元、TF-IDF 和 tie 顺序，并在正文列出三个支持配对的效果量及 2,000 次 sign-flip/Holm p 值。全部 20 个词法配对及未校正区间见 [私有审阅补充表](BEIR_PAIRWISE_REVIEW_SUPPLEMENT.md)。 |
| 2,000 次符号翻转可能使临界结论受模拟噪声影响 | 值得检查。使用此前六系统 200,000 次复算中的五个词法系统，重新在每个数据集各自的 10 对家族做 Holm；对照旧结果的 20 个配对差值绝对值均一致至 `1e-12`，支持的配对仍为 SciFact 2、NFCorpus 1。见 [重算脚本](recheck_lexical_holm.py)与 [结果](lexical_holm_200k_sensitivity.json)。这是已见数据上的事后数值敏感性分析，匹配配对均值不证明逐查询完全相同，也不验证统计假设。 |
| BGE 的事后分析可能分散重点 | 保留为有标签的探索结果，强调它不验证审计收益或稠密模型的平局性质；是否移至补充材料由目标会议和最终篇幅决定。 |

跨平台复算时，Windows 工作树的 CRLF 和 GB10 的 LF 导致两份文本输入的物理文件哈希不同，数值本身一致。重算脚本现记录 **CRLF 规范化为 LF 后**的 SHA-256；该值用于核对版本化文本内容，不冒充各机器原始文件字节的哈希。此前报告的工作树哈希保留在历史提交中。

## 我们另行发现并修正的数值归属

短稿原文在 TF-IDF 名次句后写“its MAP@10 从 0.2225 到 0.1193”，将两项数值误归属为 TF-IDF；这并非机器审稿明确指出的错误。直接读取 [原实现结果](../paper_e_public_eval_20261028/results/v1_uncorrected/BEIR_AUDIT_RESULT_20261028.json)与[修正结果](../paper_e_public_eval_20261028/results/BEIR_AUDIT_RESULT_V2_20261028.json)：

| NFCorpus 系统 | 原 MAP@10 | 修正 MAP@10 |
|---|---:|---:|
| TF-IDF | 0.220030… | 0.116230… |
| BM25(1.5, 0.6) | 0.222493… | 0.119330… |

现役稿已改为 TF-IDF `0.2200 → 0.1162`；历史稿与 raw 未覆盖。这个修正不改变“分级 nDCG 排名变化”和“MAP 分母变化是不同修正”的区分，但必须明确保留更正历史。

## 成本、产物与未完成事项

两次本地模型 POST 均返回 `stop`，总 usage **11,991 tokens**（请求分别 6,067、5,924；报告缓存读取为 0）；无重试、训练或付费 API。完整请求、响应和 ledger 在 GB10 `/home/testuser/wzh/research_evidence/agent_learning_20261030/icint_ai_review_20261030/`，response SHA-256 分别 `bb908e7893c37158fab15adc3e4a896c9525f421d3e891fba67a512d7a3d44fc` 与 `647a1e410d566e7a5994f204f8c8c4ab271570073f0a25c27abb90adc0e33b90`。

修订后的 [ICINT PDF](icint_latex/main.pdf) 为 4 页、SHA-256 `2b7a4e1349e71826a88f91c1be84f116fa5a8ed888f3382822f51fa8fca7f0b5`；[ICDAR 模板预演](icdar_latex/main.pdf) 为 8 页、SHA-256 `20cba14e5d26b3ae7152bbf6ff066c2cc9084146f124e53fd086fc6dd48894aa`。两种都已编译，ICINT 四页与 ICDAR 八页均重新渲染检查；ICDAR 仍需文档分析定位改写。机器审读没有检查引用原文、数据来源许可、人工语义标注或所有数值；AI/作者声明、署名、投稿系统及学校成果认定仍需实际办理。

如作者希望再让网页版 Gemini 用独立上下文审读，可附现役 PDF 与配对补充表，使用 [可直接转发的提示](GEMINI_REVIEW_PROMPT_20261031.md)。这仍是 AI 辅助审读，不是人工统计背书。
