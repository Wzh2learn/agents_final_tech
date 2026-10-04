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
| `paper/teacher_review_draft_v1.md` | 可追踪英文评估主稿 | 9 个必需章节；claim 5 条；独立审稿第 5 轮双 ACCEPT | `9d3e492694dda052a854c3cffac0b127ecda3aa383aa566abb75293fd7716f5c` |
| `paper/teacher_review_draft_v1.docx` | 导师向送审形态 | Office 视觉 PASS；尚未套 ARR/WWW venue 模板 | `4f0b88cf60dcad532e9871f4f3b3ca963f49ce1746b305497d9f0c4156498a5f` |
| `paper/teacher_review_note_v2.md` | 中文说明 | 阅读顺序与边界说明 | `3677450844b136807dddc67576064788726e651a4e3a561d4a86e97dbaf37d5a` |
| `paper/research_story_v2.md` / `.docx` | 三阶段叙事/方向材料 | 只作研究框架与后续回填，不作未完成实验结果 | `372153462d0fd5d52da8be77097c6375aaa6e05e53cc98c366aea69daf678c0c` / `311e0f625e785432f8dd3277faa466e60a4919b0a02034725bb48a0c5bea6a00` |
| `paper/claim_manifest_v1.json` | claim-evidence 映射 | 5 claims；含 SP-C5 预注册停止结论 | `62a119e8b6aca573ecfdfaf1ff38002298a99d8914bca99a0622807a142fafc5` |
| `paper/acceptance_report_v1.json` | 机械验收 | PASS / 5 claims / 74 checks | `cf6123638a042b9027db0f1a8a500571a75cc512c1866d04142b4b4a4a7b9d05` |
| `paper/references_v0.md` | 已核引用池 | arXiv/DOI 可追溯；venue 未核项不升级 | `8e89bef1bb8ea1a2d3fcb571c31d118bce4306c1c67eb957e8c5ccc155043eeb` |
| `paper/submission_references_arr_www_v1.md` | 投稿引用映射/BibTeX | 主稿 15 条逐条映射；Li 2025a/b 已固定消歧 | `1b49c7ffb1f9856e092d1a47199050c4d813e1421c5f1ca4ac77d179d22a7b82` |
| `paper/reproducibility_statement_arr_www_v1.md` | 可复现性/工件披露 | 区分可公开候选与不外发材料；纳入 D-B licence_record 边界 | `da8119733417d3dba27f20588e2f05d2ee6b878098bfe1bc3bd0c244e3b15dc8` |
| `paper/submission_draft_arr_www_anonymous_v0.md` | 匿名投稿源预览 | 11 处机械脱敏；claim tokens 全保留；不是 camera-ready | `6af1dfc661f56cd29b63ecc727a4ee35e0df93adf42e887254ba017de1f1b30e` |
| `paper/submission_redaction_map_v1.json` | 内部脱敏审计图 | 只供内部核对，不随稿外发 | `30f1be4b82759ef151d148f71ddf146cbdda75d84bfca3b1c1d93ea5a2af03a6` |
| `paper/submission_package_audit_v1.json` | 投稿包机器审计 | mechanical PASS / submission PENDING_EXTERNAL_ITEMS | `094e581789c75bbab66a1b74d0d04ff18cdb26fa23fe5bb285ef37503d9b278a` |
| `paper/submission_review_risk_register_v1.md` | Reviewer 风险登记 | 阻断项/受控风险/外部 pending 分离 | `42e98c45badd3c55758732b342688bd4a4ade89d7b03b1b412412e0343503f65` |
| `paper/related_work_contribution_matrix_v1.md` | Related Work 贡献边界矩阵 | 四簇代表工作、差异边界与 KD future-work 隔离 | `97253b3eb8a0cfb0e0646a4250346b6183202bdebad650f687d36c44620dbb42` |
| `paper/submission_language_audit_v1.md` | 语言/术语审计 | AI 套话、强主张、术语一致性与版本同步 | `0c1ad69ec1c99f2a11c8e6108e66129085cca32c09cc6591eeca74bc559c2384` |
| `docs/experiments/figures_paper/fig_checkpoint_trees_v2.svg` | Figure 1 | 已入稿 | `983f4f4657e83ff8d8996e9add265bee9bab4f69dca20be810899f3330911e7e` |
| `docs/experiments/figures_paper/fig_visibility_spectrum.png` | Figure 2 | 已入稿；视觉验收记录在案 | `d9da2f7b2e290d557f14ef14bc163850f5c6a55117432137848e8b49a0e27226` |
| `paper/figures/fig_evaluate_distill_evolve_v1.svg` | 三阶段总架构 | 研究框架图；不是实验结果图 | `3e8500b773f92291042fb0503df0e9b646f7ed5a07599465c8fea8f66ae15240` |

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

## 6. Internal submission route decision (2026-10-05)

Stage D necessity gate is `PILOT_ONLY`, with `stage_d_necessity=NOT_ESTABLISHED` and `training_recommendation=DO_NOT_TRAIN_YET`. Therefore the internal submission route remains the mature Stage E evaluation fallback. The internal manuscript content is finalized for internal submission review; Q3 and B0-B4 exploratory evidence stays outside the main result tables and is referenced only as future-work/limitations evidence.

External submission remains blocked by venue/template verification, authorship, patent confirmation, anonymization, and camera-ready acceptance. This route decision does not make the package ready for external submission.