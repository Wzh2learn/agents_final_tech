# WP-2 S8 C 预检（pre-result audit）— Loop C 审计卡

- task: `tatqa-wp2-s8pre-20261014`
- 范围: **只审计 S7 冻结包**（pre-result）；不跑 S9、不改任何被审对象。
- 输入（先读）: `research/tatqa_wp0_2026/wp2/PREREG_v1.md` + `PREREG_v1_RECEIPT.json`；`research/tatqa_wp0_2026/wp2/S4S7_EXECUTION_REPORT.md`；`research/tatqa_wp0_2026/wp2/ACTOR_FREEZE_RECEIPT.json`；`docs/research/WP0_TATQA_FEEDBACK_RIGHT_CONTRACT_v1.md`（对照 draft 与 owner 默认值）；`research/tatqa_wp0_2026/wp2/{ITEMS_V2_RECEIPT.json, PILOT_ELIGIBILITY_RECEIPT.json, SPLIT_RERUN_RECEIPT.json}`；`docs/research/WP2_F5_ELIGIBILITY_DECISION_v1.md`；S4/S5/S6 收据；`research/tatqa_wp0_2026/wp2/analyze_wp2.py`；eval protocol 与 runbook §4–5。

## 预检点
1) **prereg 遵守**: PREREG_v1 是否覆盖 runbook/协议要求（臂/任务/重复/预算/停止规则/统计）；与协议任何冲突即为 REJECTED 级发现。
2) **哈希 pin**: 全字段可解析、指向盘上真实字节；checker_v2/adapter/provenance/分析脚本/任务列表/分组/actor/反馈合同/budget 均 pin。
3) **feedback v1**: 五个空是否按 owner 默认填（executed-only 修正、无 gold、无测试源信息）；与 draft 的允许/禁止清单一致；无越权展示项。
4) **actor freeze**: revision 与设置（temp 0 / 512 / 4096 / 600 / 无第三轮）重核（只读）；F2 哈希复核声明是否有一手证据。
5) **item/split**: F-5 资格规则与 reserve 替换（dace18a6→cb626a5c）是否文档化、收据化；pilot 8/dev 2/history 4 组成不变；盲 id 与 origin 不相交证据。
6) **S4/S5/S6**: 调用计数 ≤40 且逐调用记账；E/C token 差 ≤5% 证据；无泄漏（无 gold/测试源进入上下文）；重试计数。
7) **边界**: 无 S9 痕迹（pilot 未跑）；零 judge；历史收据未动。

## 产出与判定
- 尽量写 `docs/research/WP2_S8PRE_LOOP_C_AUDIT_v1.md`；被拒则全文入答复（转录）。
- 每项 PASS/CONDITIONAL/REJECTED + 总体；未验证面明示。总体 PASS 方可放行 S9。
- 红线: 只读；零模型/网络/凭证；不 commit/push；不改被审对象与历史文件。