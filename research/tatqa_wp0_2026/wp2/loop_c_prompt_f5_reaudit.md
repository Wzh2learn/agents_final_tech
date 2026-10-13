# WP-2 F-5 / F-10 闭环复查（round 3）— Loop C 审计卡

- task: `tatqa-wp2-f5c-20261014`
- 范围: **只复查** F-5 资格决策与 F-10 修复的关闭质量；不重做全量审计、不跑 S4+、不改任何被审对象与历史文件。
- 输入（先读）: `docs/research/WP2_F5_ELIGIBILITY_DECISION_v1.md`；`research/tatqa_wp0_2026/wp2/{PILOT_ELIGIBILITY_RECEIPT.json, check_pilot_eligibility.py, F5_EXECUTION_REPORT.md}`；`research/tatqa_wp0_2026/wp1/{S0C_FIX_RECEIPT.json, checker_v2.py, fixtures/s0c_equivalent_form_fixtures_v2.json}`；`docs/INDEX.md` 新增两行。

## 复查点
1) **F-5 资格**: 独立复算 352/36/316；逐 role-origin 核验（预期恰 1 个 reserve shortfall = `tatqa_dace18a6-…`，且角色未改、仅给 rank 23+ 替换建议）；`null=identity` 显式记录；`currency` fail-closed 与 owner 授权口径一致；`gold_delta_source_unit` 数值校验。
2) **F-10**: `checker_v2.py` 新分支位置与守卫；严格性只允许 `wrong_period`→`wrong`；fixture 期望（pre-fix `wrong_period` → `wrong`）；尽量对 1 例做手推演复核；若可行核对 strictness matrix 声明。
3) **边界**: `normalize_unit`/`UNIT_ALIASES` 未改；item freeze 仍 S7；S0/S0B 收据哈希未动（钉住）；零模型调用声明属实。
4) **文档**: `docs/INDEX.md` 新增两行描述与实际产物一致。

## 产出与判定
- 尽量写 `docs/research/WP2_F5F10_LOOP_C_AUDIT_v1.md`；**若写盘仍被沙箱拒绝，把完整报告放进最终答复**（将被转录落盘，同前两轮）。
- 每项 PASS/CONDITIONAL/REJECTED + 总体判定；注明未验证面。

## 红线
只读；零模型、零网络、零凭证；不 commit、不 push；不改被审对象与历史文件。