# Paper E 字符串全面扫描 v2 — 候选清单（待 owner 勾选；只列未改）

> 2026-10-13 | 来源：字符串专项 worker 全稿扫描（246 行）+ §8 既有裁定对照 | 状态：AWAITING_OWNER_TICK — 本文件不是执行记录，未改任何论文文本（行号按 2026-10-13 版）。
> 已执行（对照）：内嵌 sha256 ×2 → "content hash in the artifact manifest"（1d176c6）；`127.0.0.1:8004` → `served locally`、`:8004 judge` ×2 → `local judge`（078398e）。

## A. 高优先（内部代号，外部读者无法解读；建议描述化）
1. `DR4` ×3（L126）— 内部标准代号；建议首现给描述（如 "the deterministic rule-based standard"）。
2. `D3` ×2（L106/L246）— 内部数据流代号；建议描述化（如 "the frozen clean-input set" / "the earlier fixed-threshold analysis"）。
3. `Stage E`（L172/L230）、`Stage R`（L172）— 内部阶段代号；建议描述化或移除。
4. `SOURCE_GO` / `SPLIT_GO`（L234/L238）— 内部门禁码；建议首现定义或描述化。
5. `M2 judge pipeline` + `m2_judge`（L92）— 内部模块/标签名；建议 "the semantic judge pipeline"，标签名删或入附录。
6. `hungarian` 小写 ×2（L92）与 L102 "Hungarian" 不一致 — 建议统一（先核实是否为配置名）。

## B. 中优先（工程坐标；§8 曾判"可接受"，若要更干净口径可一并处理）
- L92：`scripts/m1_statement_parser.py, map_headers`；`config/eval_checkpoint_trees.json`；`data/research/drift_v0/*.json` ×2；"production"（匿名链中属被脱敏词）。
- L39：`config/eval_checkpoint_trees.json v0.1.0`；`(12 calls at the same endpoint)`。
- L142：`t2_visibility_sensitivity.json` + "path in the evidence ledger"。
- L106：`(table_uid, column)`；"fold assignment = sorted(table UID) index modulo 5"。
- L238："taken under the approved minimal scope" 等。
- 建议口径：正文只留必要坐标（matcher、模型），文件名/路径统一收进 "listed in the artifact manifest" 式描述句。

## C. 一致性 nit（低）
- 千分位混用：`2,382` vs `2409/1970/1478/10001`。
- NIST 引用两种写法（L15 `[NIST AI 100-1, 2023]` vs L21 `[NIST, 2023; NIST, 2024]`）。

## D. 建议保留（不动）
`Q4_K_M GGUF`（judge 身份）；公式符号；`TAT-QA`/`FinQA`/`NIST`；`drift-v0`；DOI；`M/R/N`（已定义）。

## E. 边界（另一条冻结链，另行拍板）
`paper/teacher_review_draft_v1.md`、`paper/submission_draft_arr_www_anonymous_v0.md`（Stage E ARR/WWW 旧稿）仍含 `:8004`/内嵌 sha256；被 `audit_submission_package.py` SHA256 钉死，需该链"修订 + 重钉"流程。
## 执行状态（2026-10-13 夜，owner 授权执行）

- 已执行：A 组 6 项全部落地（DR4→"the standard"；D3→"frozen clean-input set" / "earlier fixed-threshold analysis"；Stage E/R→"evaluation-track" / "reasoning-step"；SOURCE_GO/SPLIT_GO→"source-identity gate" / "split gate"；M2 judge/m2_judge→"judge pipeline (listed in the artifact manifest)"；hungarian→Hungarian）。B 组按"必要坐标保留、文件/路径收编"口径落地 6 处（checkpoint 配置、两个数据文件、matcher 脚本、QA 措辞、t2 文件名）。共 18 处替换 + 1 处句法微调；逐条"单次命中"守卫通过。
- 保留（不动）：`Q4_K_M GGUF`、`drift-v0`、`M/R/N`、数值与公式；`(table_uid, column)` 与 fold-assignment 定义句；统计语境 `endpoints`（k/95、k/282 网格）与 `reproduction` 等词。
- 验证：md→tex→bundle→PDF 重建（tectonic exit 0，9 页）；`PRE_SUBMISSION_AUDIT = PASS`；`WIDE_EVIDENCE_CHECK = PASS`（15/15、23/23、21/21）；PDF 文本断言：20 个禁用 token 全 0、替换词就位（`served locally`×1、`local judge`×2、`Hungarian`×3 等）、`??`=0。
- 记录：`PDF_LAYOUT_AUDIT_v1.md` 增补 Presentation fix (2026-10-13f)；本清单状态自此为 EXECUTED（保留为审计痕迹）。
- 边界：ARR/WWW 旧冻结链（`teacher_review_draft_v1.md`、`submission_draft_arr_www_anonymous_v0.md`）未动——SHA 钉死，需该链自修订重钉；数字/claim/证据哈希零变化。