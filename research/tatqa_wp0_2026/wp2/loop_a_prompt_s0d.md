# F-10 严格性证据补档（S0d）— Loop A 执行卡

- task: `tatqa-wp2-f5d-20261014`
- 背景: Loop C round-3 判定 CONDITIONAL —— 唯一缺口 = `research/tatqa_wp0_2026/wp2/F5_EXECUTION_REPORT.md` L23 的 "24-case strictness matrix / five changed classifications" 断言无任何产物支撑（不可复现、不可核验）。C3 §2.2 已用分支差分独立证明严格性界（仅 `wrong_period`→`wrong`）。本轮目标 = 把该断言换成**可核验产物 + 明确撤回**。
- 授权记录: owner 2026-10-13 夜在会话中授权按 Loop D 判读闭环全部 conditional 项；派发卡 `research/tatqa_wp0_2026/wp2/loop_a_prompt_f5.md` 为在仓授权痕迹。
- 纪律: 零模型/网络/裁判；**不覆写任何既有收据与报告（只新增文件）**；不 git add/commit/push；失败即停、如实报告。

## 任务
1. 产出**新构建、如实标注**的严格性矩阵产物 `research/tatqa_wp0_2026/wp1/S0C_STRICTNESS_MATRIX_RECEIPT.json`:
   - 用例集: 完整枚举等价形分支空间（periods 顺序 × `delta_source` 对/错 × `delta_target` 对/错 × `unit` 对/错），并含直接形对照；用例构造规则与总数如实记录（记为 N，**不要预设 24**）。
   - pre/post 评分: pre = 临时重建的 pre-F-10 逻辑（在**临时文件**中删去分支 C；不得改动现行 `checker_v2.py`）；post = 现行 checker_v2。逐例记录 pre/post 归因。
   - 统计: 变更数；全部变更类型（**必须逐条为 `wrong_period`→`wrong`**，出现任何其他类型 → 停并报告；`correct*` 翻转计数必须 0，非 0 → 停并报告）。
   - 收据含: 输入/输出 sha256、重跑 byte-identical 说明、"post-hoc reconstruction；原未落盘 scratch 检查已撤回"标注。
2. `docs/research/F10_STRICTNESS_MATRIX_ADDENDUM_v1.md`:
   - **撤回** `F5_EXECUTION_REPORT.md` 的 "24-case / five" 原句（未落盘、不可核验）；
   - 改为引用新矩阵产物 + Loop C round-3 的分支差分证明（`docs/research/WP2_F5F10_LOOP_C_AUDIT_v1.md` §2.2）；
   - 如实记录矩阵实际计数；
   - 附 S7 建议两条（C3 备档）: (a) `prepare_item`/`recompute_gold` 增加 `late != early` 的 fail-closed 断言；(b) runner 携带 pre-fix 实跑路径，让 `observed_pre_fix_outcome` 证据链自足；
   - 记录 owner 授权出处（上一节）。
3. 结束写 `research/tatqa_wp0_2026/wp2/S0D_EXECUTION_REPORT.md`（状态/文件+sha256/命令/遗留点）。