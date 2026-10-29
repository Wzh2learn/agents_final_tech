# Paper E v6：阈值机制与长期研究范围

日期 2026-10-29。[v6 正文](paper_e_review_revision_v6.md)由 [v5 正文](paper_e_review_revision_v5.md)通过 [build_paper_e_v6.py](build_paper_e_v6.py)可重复生成。没有新实验、模型调用或训练。

本次只改 Case 1 的读者解释：在既有 matched-threshold 网格中，flat 阈值 1.0 对应 hierarchical root-drop 阈值 0.375，指定折中二者均检出 21 个案例。该网格不是表中 75/95 和 20/95 的操作点配置，不将两者合并；依 [matched-FPR 原始结果](../stage_e_method_revision_20261009/matched_fpr_reanalysis.json) 与 [离线复核](../asset_revalidation_20261029_v1/REVALIDATION_AND_AUTOPSY.md)记录。

新增干净样本为何全为零的说明：在当前冻结定义中，同一个未修改记录经确定性计算后与自身比较；2,382 条 clean score 因此均为零。每个正阈值的观测 clean FPR 都为零，当前 clean-only 面板不能识别唯一部署阈值；这不是所有评测器都无法校准的主张。

用户同时明确第二篇不应收窄到 Agent 产物/进程区分。开放方向与已有实验边界记在 [长期研究组合](../agent_frontier_portfolio_20261029/AGENT_FRONTIER_RESEARCH_PORTFOLIO.md)顶部；它是候选和对标计划，不是已完成方法。

[PDF](paper_e_review_revision_v6.pdf)为 Pandoc 生成临时 DOCX、GB10 LibreOffice 24.2 渲染的 15 页单栏内部预览；表题和表格分页做过基础处理，并检查接触表。它不是会议模板或投稿终稿。具体目标渠道、完整参考文献/统计复核、匿名与作者声明仍待办理。
