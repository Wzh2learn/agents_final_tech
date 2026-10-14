# WP-2 S4C 在线资格执行卡（bridge v2；owner 已批准）

- task: `tatqa-wp2-s4c-qual-20261014`
- owner 批准: 2026-10-14「我批准在线资格」；预算沿用：全局 9/300 已用，本卡 <=3 请求，judge=0
- 依据: `docs/research/WP2_BRIDGE_LONGTERM_ANALYSIS_v1.md` §L4/§6（<=3 探针；通过 → 恢复 S4（S4c）；不通过 → STOP_THIS_PANEL 永久、不再第五轮）；`BRIDGE_V2_RECEIPT.json`（离线资格 PASS；"在线 GPU 约束解码"明示为未验证面）
- 执行者: Loop D 直接执行（受控小台阶：单服务、<=3 请求；规避子代理 harness 在预算关键路径上的误发风险；此为如实披露的执行偏离）。独立复核: fresh-context Loop C 后置（复算优先）。
- 范围: 仅向 127.0.0.1:8112 的 bridge-v2 服务发送本卡冻结的 3 个探针请求；tokenizer-only preflight；不产生 judge / 数据库 / 训练 / 生产服务调用；不跑 S4/S5–S9；执行窗口内不 git 操作（冻结与结果提交由 Loop D 治理步骤完成）。

## 冻结件（本卡提交时点；sha256）

| 件 | 路径 | sha256 |
|---|---|---|
| 探针集 | `research/tatqa_wp0_2026/wp2/s4c_qual_run/PROBES_FROZEN.json` | `061f871f1849d84eb5c6c70275fd8ee40a7920f2a3611257f720dbd702cc3f6f` |
| 执行器 | `research/tatqa_wp0_2026/wp2/s4c_qual_run/run_s4c_qualification.py` | `a3f9b0584f25bbbd2bc0479d117262246917bbddaf5f01c76d1af1ed0d297924` |
| 探针生成器（溯源） | `research/tatqa_wp0_2026/wp2/s4c_qual_run/build_probes_frozen.py` | `9a8ac83c2bde9d91f1eaea75f6857780c479b45ecfccb336a2d3b966b443897f` |
| 校验器（bridge_v2 冻结组件） | `research/tatqa_wp0_2026/wp2/bridge_v2/validate_v2.py` | `c4fc4febbb8deffac10569633d35b8fe6f87e805656f18cace8330e5f691d63a` |

run 前置条件：`BRIDGE_V2_RECEIPT.json` component_hashes 5/5 复验一致（preflight 自动检查）。

## 探针协议（与 PROBES_FROZEN.json 一致）

1. 顺序固定 3 探针：`S4CQ-01-plan-history-01`（plan；复现最终失败 case 同一 episode 上下文）→ `S4CQ-02-plan-history-03`（plan）→ `S4CQ-03-consume-history-03`（consume，含冻结 tool trace）。
2. 请求设置: `model=tatqa-wp2-qwen3-8b-b968826d; max_tokens=512; temperature=0; n=1`；端口 8112；不扰 :8004/:8006。
3. persist-first：先写 request.json 再传输；raw 先于解析落盘；逐探针写台账。
4. 无传输重试；任何已发送请求计入预算；首探针不满足判定即早停（不耗尽剩余探针）。
5. preflight（零模型调用）: 组件哈希 + 模板渲染 token 数 <=4096 + 源链接（protocol receipt / 失败 prompt 哈希）一致性；PASS 才允许 run。
6. 服务启动命令（预声明，另写入 service/start_command.txt）: `TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1 ./venv/bin/python research/tatqa_wp0_2026/wp2/bridge_v2/serve_transformers_actor_v2.py --model-root /home/testuser/wzh/models/hf/Qwen3-8B --metadata docs/datasets/2026-10-05_qwen_model_metadata_v1.json --host 127.0.0.1 --port 8112 --startup-receipt research/tatqa_wp0_2026/wp2/s4c_qual_run/service/STARTUP_RECEIPT.json`

## 判定（预先声明，冻结）

- **PASS**: 3/3 探针均 HTTP 200 且 `validate_v2` route=`strict_json` 且 ok=true（即：schema 合法、无散文、字段齐全）→ S4c 恢复路径开放（S4c 执行卡另行按治理流程制定，不自动开跑）。
- **FAIL**: 任一已发送探针不满足判定（含 criterion_failure / http_error / transport_failure）→ STOP_THIS_PANEL 永久（不再第五轮）。
- **ENGINEERING_INCOMPLETE**: 零传输类工程故障（如服务启动失败、健康检查失败）；最多允许修复后重试一次（上限 2 次启动、共 2 轮执行）；冻结组件 / prompt / schema 一律不得改动；否则停报。
- 预算：本卡 <=3 请求（跨轮合计）；全局 9 → <=12/300；judge=0。

## 产物

- `s4c_qual_run/`：`PREFLIGHT_RENDER_RECEIPT.json`、`ACTOR_CALL_LEDGER_QUAL.json`、`QUAL_RUN_RESULT.json`、`attempts/<probe_id>/{request.json, raw_response.txt, completion.txt, validation_result.json}`、`service/{start_command.txt, STARTUP_RECEIPT.json, service.log, SERVICE_STOP_RECEIPT.json}`
- `S4C_ONLINE_QUALIFICATION_RECEIPT.json`（最终收据；Loop D 汇总、Loop C 独立复核后归档）
- `LOOP_C_S4C_QUAL_AUDIT_v1.md`（fresh-context 复核：复算校验 / 复核计数与哈希 / 设置核对 / 无生产扰动）