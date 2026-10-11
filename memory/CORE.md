# memory/CORE.md — 永久事实（始终加载，<100 行）

更新: 2026-10-09（Loop A/C Xiaomi 模型路由收敛；运行拓扑仍按现场服务核验）

## 系统拓扑（GB10 开发机: ssh jinrong-dev, testuser@10.129.237.26, ARM64）

| 端口 | 服务 | 说明 |
|---|---|---|
| :5050 | FastAPI 主 harness (main:app, uvicorn workers=2) | M1 解析 / M2 RAG 问答 / UI (/m1) |
| :8004 | llama-server Qwen3.6-35B-A3B + mmproj | 主力模型 + 视觉 OCR (vision-8004) |
| :8005 | RETIRED (Qwen3-14B, 08-17 退位) | Loop B 断言 down; 权重保留 |
| :8006/:8008 | vLLM Qwen3.8-27B-FP8 (GB10 镜像) | M2 agent 验证链 / judge / 深度问答（thinking 档位控制） |
| :4096 | opencode 侧车 (启动器 scripts/sidecar_launch.sh) | M2 agent 路交付链 |
| :8100 | responses2chat proxy v2 | Responses API → Chat API（Chat-only 模型用） |
| :15432 | PostgreSQL + PGVector (docker) | vector_db, collection m1_parsed_statements |
| :8090 | ZhikunCode (docker) | Multi-Agent 平台，可选扩展面 |

## 模型路由（2026-10-09 现役）

- Loop A (Codex CLI): `mimo-v2.6-flash` via `Xiaomi_Token_Plan`，执行 profile `~/.codex/loopa-exec.config.toml`；诊断 profile 使用 `mimo-v2.6-pro`。
- Loop C (Claude Code): `mimo-v2.6-pro` via Anthropic-compatible endpoint `https://token-plan-cn.xiaomimimo.com/anthropic`（`~/.claude/settings.json`；2026-10-09 默认入口 smoke PASS）。
- qwen_harness_tools.py: qwen3.8-max-preview（独立于 Loop 路由，仍属历史/工具线）。
- 凭证只存外部受保护环境文件；不写入 Git、文档、日志或 prompt。
- 禁止: 加载 72B（已删除; 硬禁 08-17 作废, 改模型准入预算门, 见 DECISIONS）；PaddleOCR（ARM64 SIGSEGV）；VLM :8007/Triton 线已关闭。

## Graph 四层 Loop

- D 授权/验收 → A 执行 → B 独立验证 → C 独立审计；这是研发协作，不是 `src/agents/` 业务图。
- 当前任务决定范围与预算，入口为 `scripts/graph/loop_a_exec_constraints.md`、`scripts/graph/loop_c_audit_prompt.md`；不从历史模型/频率推断许可。
- `graph_orchestrator.sh` 仅有 B 的实际启动逻辑，A/C 主要打印说明；start/stop 会改变运行状态，不是健康查询。
- B 的判分确定性不等于零调用：默认 canary/API/QA/PG 检查会访问真实服务；本地定点测试不替代它。
- 本地分析与 GB10 正式执行边界见 `docs/governance/2026-09-07_execution_plane_boundary.md`；代码在库不代表 hooks、skills、调度或 daemon 已安装。
- 每轮派活/验收按既有规则写 `logs/graph/dispatch_log.md`；当前状态写 STATE，未决写 THREADS。

## 目录约定

- 项目: 远端 ~/wzh/projects/agents_final_tech ↔ 本地 D:\AIRcommend\JinRongAgents\agents_final_tech
- src/ ACL 三层: web / biz / storage；scripts/ 工具链；config/ schema
- 样本: ~/wzh/m1_samples/（含 scenario1/，永不 commit）；manifest 不 commit
- 文档四层: 见 docs/INDEX.md；skill 注册表: 见 docs/governance/SKILL_REGISTRY.md
- 技能分发入口为 `scripts/graph/sync_skills.sh`；同步会修改机器安装，须单独授权，不随文档治理自动执行。

## 冻结红线

- tests/test_m1_service.py（冻结节点）；scripts/graph/frozen_hashes.txt（冻结基准）；schema 冻结 hash
- 不碰 API key；模型准入走预算门（72B 已删除）；归档用 git mv 不用 rm；不 enable systemd；审查意见不照单全收
- OpenCode/MCP 交付物三件（09/10/2026-07-19_m2_mcp_verification）2026-08-05 归档至 docs/archive/：可归档、永不删除，INDEX 归档组保留条目
- HANDOFF.md 冻结为历史文档；现状写 memory/STATE.md
- :8006 有条件可用（2026-08-31 用户裁定, 五条件全列）: ① 仅限预注册窗口卡内 ② 仅限白天错峰、夜间零调用 ③ 卡内硬预算门（调用计数器）④ canary 异常即停+记账、窗内不归因 ⑤ 窗口外恢复零触碰; J7 端点鲁棒性窗不随本条自动开启（原判据另批）。此为 :8006 零触碰红线的唯一有效放宽。

## 质量基线（2026-08-22 更新）

- M1 解析: 100%（scenario1 15 源 30 表）；现役台账唯一存放于 memory/THREADS.md，已结案轨迹在 memory/archive/THREADS_history.md（只引用不复述）
- M2 eval 基线: 确定性 16/16 + NF 0/9 + judge 四维 5.0（08-22, 经 :5050）；embeddings 137
- pytest: 379 passed / 13 skipped（08-22）；Loop B 30min 一轮（08-22 overall PASS）
