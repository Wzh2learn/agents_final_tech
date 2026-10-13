# TAT-QA WP-2 F-5 闭环轮（S1b，owner 授权执行）— Loop A 执行卡

- task: `tatqa-wp2-f5-20261013`
- 背景: Loop C round-1 审计 F-5（阻塞项）——352 题中 36 题 `source_unit:"currency"` 使 `normalize_unit` 抛 `ValueError` 不可评分；312 题 `null` 被静默当作 `"unit"`。owner 已授权（2026-10-13 夜）按 Loop D 默认闭环执行。
- 决策（默认，执行之；**不改 checker 语义**）:
  1) generic `currency`（无币种/面额）→ **fail-closed 排除**出 pilot 题本；
  2) `source_unit` null/absent → 显式视为 identity（dimensionless `unit`），write 进资格收据（不许静默）；
  3) `%` → percent / percentage-point identity（保留）；
  4) thousand/million/billion → 默认 identity（Option A），除非未来有显式审定的 Option B 赋值；
  5) `gold_delta_source_unit` 命名陷阱 → 决策文档记录语义别名与校验（数值字段，勿当单位解析）。
- 禁止: 不改 `normalize_unit` / `UNIT_ALIASES` / `checker_v2` 语义；不做 S4+；零模型调用、零对外网络；不 git add/commit/push；不动历史收据与 run_logs。

## F-10 — 等价形"错值"归因（Loop C round-2 备档项，转正修复）
- 现象: 等价形（`periods == [early, late]`）若 delta 值不正确（未满足精确取负条件）而期间表达合法、单位正确，会被后置的 `wrong_period` 分支截获；基线 v1 与 v2 同样存在（round-2 已备档）。
- 修复: 在等价形两个既有分支之后、`wrong_period` 之前，为"`periods == [early, late]` 且未满足精确条件"补 `wrong` 归因；**严格性只增不减**——唯一允许的类别变化是 `wrong_period` → `wrong`，任何用例不得翻成 correct。
- 加专用 fixture: 等价形、期间合法、delta 值错误、单位正确 → 期望 `wrong`（修复前为 `wrong_period`）。
## 产出
1. `research/tatqa_wp0_2026/wp2/check_pilot_eligibility.py`（纯 stdlib、确定性；读 `data/research/tatqa_wp0_2026/candidate_items_v2.json` + origin manifest + split 收据）→ `research/tatqa_wp0_2026/wp2/PILOT_ELIGIBILITY_RECEIPT.json`:
   - counts: total / excluded_currency / eligible；source_unit 分布；target_unit 解析逐项计数（identity_unit / percent_identity / scale_identity）；
   - 22 个角色 origins 的合格题数逐项核验（须 ≥2；若某 origin <2 → **不静默改角色**，报告并给出基于 reserve 池的替换建议）；
   - 输入/输出 sha256；重跑 byte-identical 说明。
2. `docs/research/WP2_F5_ELIGIBILITY_DECISION_v1.md`: 决策 + 理由 + owner 授权记录 + 边界（item freeze 仍在 S7；本决策只定 pilot 资格规则）+ 数字。
3. 在 `docs/research/WP2_TARGET_UNIT_RULES_DRAFT_v1.md` 末尾追加 3 行 status addendum（指向决策文档；不改其历史内容）。
4. 结束写 `research/tatqa_wp0_2026/wp2/F5_EXECUTION_REPORT.md`（状态 / 文件 + sha256 / 命令 / 遗留点）。
5. F-10 修复并入本轮（独立收据链）: `checker_v2.py` 就地修订 + 新 fixture（如 `fixtures/s0c_equivalent_form_fixtures_v2.json`）+ 更新 `s0_run_fixtures_v2.py` 写 `S0C_FIX_RECEIPT.json` 并钉校验 `S0B_FIX_RECEIPT.json`（**不得覆盖 S0B/S0 收据**）+ 全量重跑；S0C 收据含 F-10 逐项关闭说明。

## 停止点
- 若某角色 origin 合格题 <2 且无法在不改哈希规则的前提下给出 reserve 替换建议 → 停并报告。
- 完成后回报；不 commit、不 push、零 git 操作。