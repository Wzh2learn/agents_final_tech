# 项目大扫除批次证据（2026-10-03）

> 范围：文档/资产索引/代码安全/可审计性；不派模型、不跑 G-D、不下数据、不启动 Phase 1a/2/训练、不重启服务
> 起点 head：`7dfb426984c77e6a8a18127e0f273ba546f147a1`
> 目标文件原子收口：`paper/submission_references_arr_www_v1.md` 已在 `35e77d1c83844806b19195dabb8e03240f15b872` 提交

## 1. 文档与资产对齐

- `memory/STATE.md`：记录当前 head/提交链、Loop B 覆盖边界和 `DATA_NO_GO` / `NOT_IDENTIFIED` / V2-3 / 146 列未复核 / token 未就绪。
- `docs/research/README.md`：移除“无需裁定即可执行”口径；明确 FinQA 步级路线已由 V2-3 关闭，146 列只有输入包，R1/R2/ADJ 未运行。
- `docs/handoff/2026-09-22-paper-research-next-phase.md`：历史正文保留，新增当前状态覆盖注记；GB10 已验证，docs_lint 当前 `0 fail / 4 warn`。
- `paper/research_asset_map_v2.md`：修正 Office 视觉验收、D-C 暂存/不新增下载状态，登记 Q3 runner、输入包与“已装配未复核”边界。
- `docs/architecture/codebase_map.md`：登记 `research/valentine_q3_review_package.py` 的输入/输出、allowlist、零 ground_truth 读取与禁止事项。
- `docs/datasets/2026-09-24_label_review_protocol_templates.md`：补 R1/R2/ADJ 会话身份、模型身份互异且非生成者的治理硬约束；当前不派发。

## 2. Q3 runner 安全修复

修复前复现（GB10，旧实现）：输出目录已有 `sentinel.txt` 时调用 `build`，结果 `sentinel_exists=False`，旧文件被静默删除。

修复后合同：

1. `out_dir` 必须是绝对路径、位于系统临时目录内，不得是 temp 根、仓库或输入树的祖先/后代；不存在或空目录才接受，嵌套目录/非空目录/符号链接 fail closed，不再 `unlink`。
2. 输入树只允许 10 个批准 pair 目录；每 pair 只允许 `source_table.csv`、`target_table.csv`、`ground_truth.json` 三个普通文件。
3. `sha256_manifest.txt` 的 `valentine/experiments/data/` 范围必须恰为 30 个 allowlist 条目；额外 pair、文件、数据集或 manifest 项 fail closed。
4. `ground_truth.json` 只做存在性/文件类型校验，禁止打开读取。

新增/保留测试：`tests/test_valentine_q3_review_package.py` 共 **16 passed**，覆盖旧合同、gold 不读取、输出误删/嵌套/输入树内输出/临时根、额外 pair/文件/数据集、manifest 越界、重复表头和 direct-script 入口。

真实原始 staging 的负向探测：新 runner 以 `input_manifest_scope_mismatch` 拒绝（30 个 `_full/_result/_trajectory` 扩展项为 extra），且不创建输出目录。旧 Q3 包保持 hardening 前不可变历史产物；未来重建必须使用过滤输入根。

## 3. 链接与索引

- 扫描范围：`docs/`（排除 `docs/archive/`、`skills/`）+ `paper/`，319 个 Markdown。
- 现役断链修复 3 处：`skill_system_health.md` 的占位示例改为纯代码、Loop C 审稿件省略号路径改为路径说明、harness audit 的历史 `HANDOFF_PROMPT.md` 改为非链接并登记缺失。
- 模板占位 1 处单列保留：`docs/governance/reference/READING_NOTES_INDEX_TEMPLATE.md:56` 的 `file.md`，不计断链。
- `docs/INDEX.md` 保持四层结构和 `experiments/` 目录登记规则，本批未新增顶层实验类别。

## 4. 验证记录

- GB10 全量 pytest @ `1c4ffaf`：**819 passed / 13 skipped / 1 deselected**（相对 809 基线 +10，增量为 Q3 反例；无未解释变化）。
- `validate_paper_claims`：**PASS / 73 checks**。
- `docs_lint`：**rc=0 / 0 fail / 4 warn**；四条 warn 与 `logs/graph/docs_lint_warn_baseline.md` 机器比对 `SET_EQUAL=True`。
- 链接扫描：broken `0`，模板占位 `1`。
- secret scan：高置信凭证模式命中 `0`；未读取、未打印、未记录任何 token。
- 投稿准备清单 hash：**12/12 present**，包含 `fig_evaluate_distill_evolve_v1.svg` 补登记。

## 5. 未决技术债与范围外

- `docs/governance/audit/harness_audit_20260905/HANDOFF_PROMPT.md` 历史载体不在仓库；已清断链并登记 THREADS，不伪造文件。
- 原始 Valentine staging 的 `_full/_result/_trajectory` 扩展件不符合新 Q3 allowlist；旧包不重建，未来需过滤输入根。
- Loop B 最近自然 PASS 覆盖 `6ea6209`；`ae344ae..7dfb426` 及本批后续 head 尚未被自然周期覆盖，不冒充覆盖。
- 上一 goal 的 `research/build_submission_anonymous_preview.py` 与 `tests/test_submission_anonymous_preview.py` 是暂停线未提交工作区件，本大扫除未混入提交。
- 用户保护工作区资产和 Loop B 瞬态件均未 add/commit/删除。
