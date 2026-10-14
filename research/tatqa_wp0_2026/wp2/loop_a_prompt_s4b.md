# TAT-QA WP-2 S4b 重启卡（bridge 修复 + S4→S7）— Loop A 执行卡

- task: `tatqa-wp2-s4b-20261014`
- 背景: 上一卡 `tatqa-wp2-s4s7-20261014` 在 S4 第 1 个 plan 响应上 `BLOCKED_BRIDGE_FAILURE`（JSONDecodeError；响应未先持久化）。Loop D 定性: **工程桥接问题**（非泄漏、非科学结果）；按"同族工程失败最多一次修复"允许本轮；若本卡再次以同类 bridge 失败 → **STOP_THIS_PANEL** 并报告，不再开第三轮。
- 预算: 全流程 ≤300；上卡已用 1（永久计入）；本卡 history+development 窗口剩余 **39** 次（探针 ≤3、S4 ≤16、S5 ≤8；transport retries ≤4 计入）；judge=0。
- 必读: `research/tatqa_wp0_2026/wp2/S4S7_EXECUTION_REPORT.md`、`S4_HISTORY_FAILED_ATTEMPT_RECEIPT.json`、`run_wp2_episode_collection.py`（v1）、`serve_transformers_actor.py`、`research/tatqa_wp0_2026/wp1/implementation_contract.md`、`docs/research/WP0_TATQA_FEEDBACK_RIGHT_CONTRACT_v1.md`、runbook §4–5。

## 修复要求（本轮核心）
1. **persist-first（硬性）**: 每次请求在解析前先落 attempt 记录 —— request id、原始响应全文、响应 sha256、prompt sha256、tokens、耗时、exit、parse 结果；任何异常路径都不得丢 raw。
2. **plan/consume bridge 规范 v1（产出 `S4B_BRIDGE_PROTOCOL_RECEIPT.json`）**:
   - prompt 保持与实现合同的 tool 接口一致；可在 prompt 中加入 **≤1 个格式示例**（few-shot）；**不改设置**（temp 0 / 512 / 4096 / 600 / 无第三轮自动修复）；
   - 解析顺序: 严格 JSON → 代码围栏 JSON → 首个平衡 `{...}` 对象；三步皆失败 → fail-closed（持久化 raw + 按协议停该 episode 并记账）；
   - **探针（≤3 次，记账）**: 用 history 任务刻画实际响应格式；以探针定稿解析规则并把探针响应全文、prompt 版本 hash 写入 bridge 收据。
3. **停止语义澄清**: 停线规则中的 "bridge failure" 指**泄漏/反馈桥**违规；runner 格式失败属工程问题，按上述在预算内修复并重跑一次；再次同类失败 → STOP_THIS_PANEL、如实报告，不硬撑。

## 执行（S4b→S7；不得开始 S9）
- 重启 actor 服务（同 Transformers 本地路径；遵守 safety gates；不得扰动 :8004/:8006 与生产服务；收尾释放端口）。
- S4: history 8 episodes；S5: dev 4 items；全部走 **v2 runner（persist-first）** 与 bridge v1。
- S6: E/C 上下文（feedback 合同 v1）；E/C token 差 ≤5%；盲 id；origin-disjointness + near-duplicate isolation 收据。
- S7: `PREREG_v1.md` + `PREREG_v1_RECEIPT.json`（全字段哈希 pin：protocol / item+split（含 F-5 资格 + reserve 替换 `dace18a6`→`cb626a5c`）/ actor freeze / feedback v1 / bridge v1 / budget / analyze_wp2.py + bootstrap 方法与 seed / pilot 任务列表与顺序 / 重复数=2 / checker_v2·adapter·provenance 哈希；并披露上卡 1 次失败尝试与本次探针计数）。
- 产出: `S4B_EXECUTION_REPORT.md`；各阶段收据落 `research/tatqa_wp0_2026/wp2/`。
- 纪律: 零 judge/训练/写回；不 git 操作；不改历史收据；逐调用记账；S7 完成即停回报（S9 等 C 预审）。