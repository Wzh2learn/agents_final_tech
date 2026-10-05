# 小论文可复现性与工件披露声明（ARR / WWW v1）

> 状态：内部投稿准备件，不是外发附件 | 更新：2026-10-04
> 硬门：`release_gate = patent_status_confirmation_required`。专利状态未确认前不外发、不上传 arXiv、不公开代码。

## 1 可复现性边界

当前主稿是成熟评估保底稿，结论只覆盖冻结公开表格语料上的评估协议与缺陷可见性。所有正文数字均来自可追溯 artifact；FinQA 步级路线的负结果、`DATA_NO_GO`、RQ2 `NOT_IDENTIFIED` 均原样保留。146 列 Q3 raw package 已封存并形成 corrected ledger `51/58/37`，但带 visibility exceptions，只能作为 exploratory learnability evidence，不进入本保底稿的结果主张。

## 2 可公开候选材料

| 类别 | 工件 | 披露口径 |
|---|---|---|
| 研究文本 | `paper/teacher_review_draft_v1.md`、`paper/teacher_review_draft_v1.docx` | 当前内部评估稿；投稿版需按 venue 匿名/版式转换 |
| 方法与理论 | `paper/method_theory_materials_v1.md`、`paper/dataset_protocol_v1.md` | 方法、变量、门与边界；不含私有数据正文 |
| 引用 | `paper/references_v0.md`、`paper/submission_references_arr_www_v1.md` | 已核 arXiv/DOI；未核 venue 不升级 |
| 图表 | `docs/experiments/figures_paper/fig_checkpoint_trees_v2.svg`、`fig_visibility_spectrum.png` | 论文图件；不得改写实验数字 |
| 机器验收 | `paper/claim_manifest_v1.json`、`paper/acceptance_report_v1.json` | claim-evidence 与静态验收报告 |
| 代码/协议 | `research/validate_paper_claims.py`、`research/build_teacher_review_docx.py`、相关协议与测试 | 专利确认后才考虑公开；当前只准备清单 |

## 3 不随稿外发

- 私有数据包、源表正文、完整 `phase1a_manifest`、逐样本标签/模型输出；
- `ground_truth.json`、Q3 review 输入包中的受限字段、任何 token/配置；
- GB10 生产路径、PID、服务端点、未公开仓库细节；
- 未完成的 Phase 1a/Phase 2/训练产物与未复核 exploratory 结果。

## 4 Provenance 与许可

- D-B 正式记录：`docs/datasets/phase1a_licence_record_v1.json`，`accepted_by=Wzh`，`accepted_at=2026-10-03T17:01:42Z`，`permitted_uses` 仅 `training / tuning / evaluation / rule_acceptance`。
- `covered_artifact_sha256` 仅覆盖 FinQA LICENSE、FinQA README、Valentine LICENSE 三件；不扩展到再分发、公开发布、商业用途、其他数据源或其他许可口径。
- D-C 最小下载已完成但数据体留在 GB10 仓外；不新增下载。Q3 runner 的三文件 allowlist 只约束下游复核输入，不改变 D-C 批准范围。

## 5 投稿前复现检查

1. 按 venue 匿名规则生成副本，移除作者、单位、内部路径与生产身份。
2. 把 artifact 路径改写为匿名补充材料编号，并保留 claim manifest 的证据关系。
3. 重新核对表图 caption、References 15 条与所有数字的 artifact 指针。
4. 重新跑 `validate_paper_claims.py`、论文验收测试、图表/DOCX 视觉验收。
5. 任何 venue 官方要求与本声明冲突时，以官方规则为准；不靠推测补许可、作者或模板字段。
