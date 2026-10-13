# TAT-QA WP-2 S0b 修复轮（关闭 Loop C round-1 CONDITIONAL 发现）— Loop A 执行卡

- task: `tatqa-wp2-s0b-20261013`
- 输入（先读）: `research/tatqa_wp0_2026/wp2/WP2_PREFREEZE_EXECUTION_REPORT.md`；`docs/research/WP2_PREFREEZE_LOOP_C_AUDIT_v1.md`（Loop C round-1 审计）；`research/tatqa_wp0_2026/wp1/S0_FIX_RECEIPT.json`
- 范围红线: 只关闭下述 4 项。**F-5（source_unit currency/null 语义）属 owner/导师决策，禁止在本轮改动 `normalize_unit` 语义或 UNIT_ALIASES**；不做 S4+；零模型调用、零 judge、零训练、零对外网络；不 git add/commit/push；不动 `logs/`；不动任何历史收据与 run_logs。

## F-2/F-3 — 直接形 unit 标签错 → wrong_unit（一致性修复）
- 现象: 等价形（delta_source == -gold.delta_source 路径）在 unit 标签错时归 `wrong_unit`；直接形（delta_source == gold.delta_source 且 target 亦对、但答案 unit != target_unit）落到 `wrong`。两类都不算 correct（门槛未松），但类别归因不一致。
- 修复: 在直接形路径补 `wrong_unit` 分支，使 unit 标签错在两个形态下同类归因；**严格性只增不减**——任何现有 PASS 用例不得翻转成 correct，任何 not-correct 不得翻转成 correct。
- 加专用 fixture: 直接形 wrong_unit 用例（数值与目标单位换算均正确、unit 标签错）。

## F-4 — S0 收据布尔量格式
- 现象: `preservation_check` 等布尔量硬编码 `True`，未使用同代码库 `_safety_claim` 的 `derived`/`attested` 词汇；内容为真但格式不可核验。
- 修复: 改为与代码库既有约定一致的词汇（如 `{"basis": "derived", "evidence": "...", "value": true}`），事实不变。

## F-8 — 协议结果类别枚举对齐
- 现象: 评测协议 §5 列 7 类，契约/实现是 8 类（缺 `wrong`）。
- 修复: 在 `docs/research/WP0_TATQA_EVALUATION_PROTOCOL_v1.md` 以最小编辑补齐 `wrong`（或等价注记），使文档与实现的 8 类一致；只追加/最小改动，不重写历史内容。

## 产出
1. 修复后的 `checker_v2.py`（就地修订）+ 新 fixture 文件（如 `fixtures/s0b_direct_form_fixtures_v2.json`，命名自定）。
2. 全量重跑: `s0_run_fixtures_v2.py`（v2 + 新 fixture）全绿；留命令与输出。
3. 新收据 `research/tatqa_wp0_2026/wp1/S0B_FIX_RECEIPT.json`：引用 `S0_FIX_RECEIPT.json`（v1 原样保留）；含 before/after sha256、重跑结果、F-2/F-3/F-4/F-8 逐项关闭说明、遗留点。
4. 修复说明: 追加 S0b addendum 到 `docs/research/WP1_PREFREEZE_FIX_NOTE_v1.md`，或单独 `S0b` 说明文件，二选一并说明理由；保证哈希可追溯。
5. 结束写 `research/tatqa_wp0_2026/wp2/S0B_EXECUTION_REPORT.md`（各项状态、文件清单 + sha256、命令与结果、遗留点）。

## 停止点
- 若某项无法在不放松判据的前提下完成 → 停下报 BLOCKED，不造数、不放松判据。
- 完成后回报；不 commit、不 push、零 git 操作。