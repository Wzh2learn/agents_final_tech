# memory/CORE.md — 架构与历史运行基线（按需加载）

更新: 2026-11-08。下列服务、CLI配置和质量数字是标注日期的历史基线，本次neat没有探测服务；当前任务、授权与研究actor以STATE、短计划和实际批次为准。

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

## 历史 CLI 路由（2026-10-09，不代表当前宿主子Agent）

- Loop A (Codex CLI): `mimo-v2.6-flash` via `Xiaomi_Token_Plan`，执行 profile `~/.codex/loopa-exec.config.toml`；诊断 profile 使用 `mimo-v2.6-pro`。
- Loop C (Claude Code): `mimo-v2.6-pro` via Anthropic-compatible endpoint `https://token-plan-cn.xiaomimimo.com/anthropic`（`~/.claude/settings.json`；2026-10-09 默认入口 smoke PASS）。
- 科研联网默认当前 Codex 宿主原生搜索；GB10 禁网实验由 D 提供带来源材料，不自动回退到 DeepSeek/Qwen 搜索。
- qwen_harness_tools.py: qwen3.8-max-preview（历史兼容工具，显式选用才执行；code_interpreter/web_extractor 功能保留）。
- 凭证只存外部受保护环境文件；不写入 Git、文档、日志或 prompt。
- 当前宿主子Agent优先续用相关上下文；新执行位按用户偏好使用GPT-6.1 Terra/max。它与上述GB10 CLI配置、实验中的8B/27B actor是不同对象；不据此改安装配置或承诺缓存命中。
- 禁止加载72B（已删除）；PaddleOCR曾有ARM64 SIGSEGV；VLM :8007/Triton为历史关闭记录，本次未复验。

## Graph 四层 Loop

- D日常主责；A按需隔离实现，B或离线脚本确定性验证，C在冻结协议/重大结论时独立审阅。不是每轮必经四阶段，也不是 `src/agents/` 业务图。
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
- 不碰API key、不加载72B；其他研究模型按当前授权和批次预算；归档用git mv；不enable systemd；审查意见须核实。
- OpenCode/MCP 交付物三件（09/10/2026-07-19_m2_mcp_verification）2026-08-05 归档至 docs/archive/：可归档、永不删除，INDEX 归档组保留条目
- HANDOFF.md 冻结为历史文档；现状写 memory/STATE.md
- 2026-08-31的:8006旧窗口要求曾为：预注册、白天错峰/夜间零调用、硬预算、canary异常停止、窗外零触碰。它不替代用户后续明确授权的科研批次，也不自动开启生产/J7探针；当前研究依STATE、固定profile与实际预算执行，共享服务不随意重启。

## 质量基线（2026-08-22 更新）

- M1 解析: 100%（scenario1 15 源 30 表）；现役台账唯一存放于 memory/THREADS.md，已结案轨迹在 memory/archive/THREADS_history.md（只引用不复述）
- M2 eval 基线: 确定性 16/16 + NF 0/9 + judge 四维 5.0（08-22, 经 :5050）；embeddings 137
- pytest: 379 passed / 13 skipped（08-22）；Loop B 30min 一轮（08-22 overall PASS）
