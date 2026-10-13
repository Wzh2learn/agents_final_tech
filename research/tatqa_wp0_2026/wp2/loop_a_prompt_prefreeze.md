# TAT-QA WP-2 预冻结准备（S0–S3 + S10）— Loop A 执行卡

> 状态: DRAFT — 尚未派发（Loop D 收口 2026-10-13；派发需 Loop D 明示）。

- task: tatqa-wp2-prefreeze-20261013
- 授权口径: owner 批准 "wp-2 可以去做后续要做的"（2026-10-13）；依 WP2_EXECUTION_RUNBOOK_v1 §4「拍板未齐 -> 只做 S0–S3（不需要模型）」执行。
- 范围红线: 不做 S4 及以后（不采集经验、不调模型/judge、不训练、不跑 pilot）；本卡之外一律不动。

## 必读（按顺序）
1. docs/research/WP2_EXECUTION_RUNBOOK_v1.md
2. docs/research/WP1_COMPLETION_RECORD_v1.md（§4 filed residuals 与解决政策）
3. docs/research/WP0_TATQA_ADAPTER_CHECKER_CONTRACT_v1.md（spec rev 1.2）
4. docs/research/WP0_TATQA_EVALUATION_PROTOCOL_v1.md
5. research/tatqa_wp0_2026/wp1/（checker.py / adapter.py / provenance.py / run_fixtures.py / fixtures/ / 三份收据 / run_logs/）
6. research/tatqa_wp0_2026/build_origins.py、wp2_split_dryrun.py、WP2_SPLIT_DRYRUN_RECEIPT.json
7. 数据（本机 gitignored）: data/research/tatqa_wp0_2026/（origin_manifest.json、candidate_items_v1.json）

## S0 预冻结软件修复（rev 1.3）
原则: WP-1 run3 收据与 run_logs 一律不动；修复以「新版本 + 变更说明 + before/after sha256」追溯。
1) correct unit-gate 向上对齐: evaluation protocol 定义正确性包含 unit 与 period -> 为所有 correct-class 结果补 unit 合取项（含 correct_other_form 路径），加专用 fixture；只许更严格，不得放松任何已有判据。
2) leak-guard needle 补齐备选数字渲染（1,300 / 1.3e3 / 001300 一类），加 fixture。
3) 跑全部 fixtures 测试（Python 3.12），留命令与输出。
4) 合同/spec 按既有修订惯例升级 rev 1.3（只追加变更行，不重写历史）。
产物: research/tatqa_wp0_2026/wp1/S0_FIX_RECEIPT.json + docs/research/WP1_PREFREEZE_FIX_NOTE_v1.md。
停止点: 无法在不改科学语义下完成 -> 停下报 BLOCKED，不放松判据、不造数。

## S1 题本扩建（>=2 题/原点）
目标: 22 个角色 origins（pilot 8 / reserve 8 / dev 2 / history 4）各 >=2 题；176 origins 有 >=2 可用行。
实现: 新增确定性 builder（建议 research/tatqa_wp0_2026/wp2/build_items_v2.py；v1 产物不动）。
产物: data/research/tatqa_wp0_2026/candidate_items_v2.json + 回执 research/tatqa_wp0_2026/wp2/ITEMS_V2_RECEIPT.json（覆盖 origin 数、总题数、每题数量分布、22 origins 核验、重跑 byte-identical 说明、输入/输出 sha256）。状态 DRAFT_NOT_FROZEN。

## S2 target_unit 规则草案（不冻结）
新增 docs/research/WP2_TARGET_UNIT_RULES_DRAFT_v1.md: 选项（thousand->unit 折算、百分比/币种、period 对齐）+ 推荐默认 + 3–5 示例 + 两个 residual 修法（gold_delta_source_unit 命名陷阱；target_unit 缺失=identity conversion）。标注「待 owner/导师拍板」。

## S3 分组复跑
重跑 wp2_split_dryrun.py（seed wp2-split-dryrun-20261013）并与 WP2_SPLIT_DRYRUN_RECEIPT.json 比对: 一致 -> research/tatqa_wp0_2026/wp2/SPLIT_RERUN_RECEIPT.json（byte-identical 判定）；不一致 -> 报差异、不覆盖旧收据。

## S10 分析脚本骨架
新增 research/tatqa_wp0_2026/wp2/analyze_wp2.py（origin 级配对 E-B/E-C/E-S/C-B + 成本，纯 stdlib）+ 合成 fixture 测试；不触真实数据。

## 纪律
- 同仓其他未提交改动不是你的（不 revert）；不 git add/commit/push；不动 logs/。
- 零模型调用、零 judge、零训练、零对外网络；不读写凭证。
- 只追加新文件；历史收据/冻结数字不动。
- 结束写 research/tatqa_wp0_2026/wp2/WP2_PREFREEZE_EXECUTION_REPORT.md（各项状态、文件清单+sha256、命令与结果、遗留点）。
