# 小论文投稿准备清单：ARR / WWW 窗口（v1）

> 状态：内部投稿准备件，不是投稿件 | 更新：2026-10-03
> 当前路线：成熟评估保底稿；Evaluate-Distill-Evolve 三阶段作为后续回填框架
> 硬门：`release_gate = patent_status_confirmation_required`。专利状态未确认前不正式投稿、不上传 arXiv、不公开代码、不外发。

## 1 窗口口径

- 主窗口：ARR **10/12**。
- 后备窗口：WWW **10/18 / 10/25**。
- 本件只准备内部投稿材料与检查单，不提交、不上传、不注册任何外部系统。
- venue、CFP、模板、页数/匿名规则必须以官方来源在投稿批次另行核验；当前引用池未核 venue 的条目保持 `arXiv preprint`，不把候选 venue 写成事实。

## 2 当前可纳入投稿包的材料

| 材料 | 角色 | 当前状态 | sha256 |
|---|---|---|---|
| `paper/teacher_review_draft_v1.md` | 可追踪英文评估主稿 | 9 个必需章节；claim 5 条；独立审稿第 5 轮双 ACCEPT | `7006d98e3d9e91cbba9ea4c8cd60a9fa9104f5f84af67fb6b71e579790a9e18a` |
| `paper/teacher_review_draft_v1.docx` | 导师向送审形态 | Office 视觉 PASS；尚未套 ARR/WWW venue 模板 | `7880429716bc0bb4727b3d09e70125de8f5145df948d78987c92782bee76f2ef` |
| `paper/teacher_review_note_v2.md` | 中文说明 | 阅读顺序与边界说明 | `02abf013e1a50a42189a4278ba240922fb70109e8e9f4a1d1cf5444f5e6d60e8` |
| `paper/research_story_v2.md` / `.docx` | 三阶段叙事/方向材料 | 只作研究框架与后续回填，不作未完成实验结果 | `1e83d05bd4426966b855cd2d21f5657ebcc826b078cb01e362f528ee658e06ac` / `311e0f625e785432f8dd3277faa466e60a4919b0a02034725bb48a0c5bea6a00` |
| `paper/claim_manifest_v1.json` | claim-evidence 映射 | 5 claims；含 SP-C5 预注册停止结论 | `5e1fa1c700f3584b0b010c9838fc243d56c3256af13dc75166caf46241aba7fa` |
| `paper/acceptance_report_v1.json` | 机械验收 | PASS / 5 claims / 73 checks | `33e800b2d48d633b0f77f31abd82dcc34b54e43b6bba263a144f014e62ccaea9` |
| `paper/references_v0.md` | 已核引用池 | arXiv/DOI 可追溯；venue 未核项不升级 | `0044e50be1635106939e105bfffaa96fb497e74c852bb4d6da2b62c1d2a3839b` |
| `paper/submission_references_arr_www_v1.md` | 投稿引用映射/BibTeX | 主稿 15 条逐条映射；Li 2025a/b 已固定消歧 | `1b49c7ffb1f9856e092d1a47199050c4d813e1421c5f1ca4ac77d179d22a7b82` |
| `docs/experiments/figures_paper/fig_checkpoint_trees_v2.svg` | Figure 1 | 已入稿 | `cb38b0c7adb96e93a22086f2561d3178762cb69b0da1929a274a4bed7e69e1db` |
| `docs/experiments/figures_paper/fig_visibility_spectrum.png` | Figure 2 | 已入稿；视觉验收记录在案 | `d9da2f7b2e290d557f14ef14bc163850f5c6a55117432137848e8b49a0e27226` |

## 3 投稿前必须完成的材料工作

1. **venue 官方核验**：在对应窗口的官方 CFP/模板页核对匿名规则、页数、参考文献格式、补充材料政策和双投限制；只把官方核验结果写入投稿包。
2. **作者与单位**：补齐作者、单位、通讯信息、利益冲突和基金信息；此前按专利门留空，不能把空项当成已完成。
3. **匿名化版本**：按 venue 规则生成作者/单位/致谢/仓库身份的匿名副本；正文中的 artifact 路径改为匿名可复现说明或补充材料引用，不能泄露内部运行身份。
4. **引用与参考文献**：以 `paper/references_v0.md` 为候选池，投稿版逐条复核 DOI/arXiv 与 venue；未核 venue 保持 `arXiv preprint`，不得补写推测会议名。GTA-2 只引已核的 `arXiv:2604.15715` 版本。
5. **图表与版式**：按 venue 模板重排 Figure 1/2、表 caption、字体和引用；重新做 PDF 视觉验收，不能直接把导师向 DOCX 当 camera-ready。
6. **可复现性附件**：只准备公开可披露的脚本/协议/聚合收据清单；私有数据、完整 manifest、模型输出、token 配置和生产路径不得随稿外发。
7. **统计与限制段**：保留 matched-FPR 仿射等价、PSO null、门控无显著收益、FinQA 步级停止条件和 `DATA_NO_GO` / `NOT_IDENTIFIED` 边界；不把 146 列输入包写成 Q3 结果。

## 4 硬阻塞与可并行工作

**硬阻塞**

- 专利状态由用户确认；未确认前不正式投稿、不上传 arXiv、不公开代码。
- venue/CFP 官方规则尚未核验，不能生成最终投稿 PDF。
- 作者、单位、匿名模板和 camera-ready 版式尚未完成。

**可并行的零模型工作**

- 准备 ARR/WWW 两套 checklist 与内部匿名化 diff 预览。
- 统一 citation key、图表 caption、Limitations 和 reproducibility statement 的文字。
- 为大论文第 3-8 章补充与投稿版一致的证据指针，不把空槽写成结果。

## 5 明确不主张

- 不主张当前 DOCX 是 ARR/WWW camera-ready。
- 不主张 146 列 Q3 已复核；其状态仍是“已装配、未复核”。
- 不主张 Stage D 闭合、RQ2 确认、`DATA_GO` 或训练完成。
- 不把 venue 候选、未核 CFP、私有数据或内部 token 配置写入投稿包。
