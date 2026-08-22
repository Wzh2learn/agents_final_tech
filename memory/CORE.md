# memory/CORE.md — 永久事实（始终加载，<100 行）

更新: 2026-08-22（拓扑大修: 双模型+侧车, 侧线审计纠偏; 维护: 拓扑变化时才改；日常只改 STATE.md）

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

## 模型路由（2026-08-03 定版）

- Loop A (Codex CLI): qwen3.8-max，Token Plan 直连 Responses API（~/.codex/config.toml）
- Loop C (Claude Code): qwen3.8-max，Anthropic 兼容端点（~/.claude/settings.json）；不兼容的仅是 qwen3.8-max-preview
- qwen_harness_tools.py: qwen3.8-max-preview（独立于 Loop 路由）
- 禁止: 加载 72B（已删除; 硬禁 08-17 作废, 改模型准入预算门, 见 DECISIONS）；PaddleOCR（ARM64 SIGSEGV）；VLM :8007/Triton 线已关闭

## Graph 四层 Loop

- A 执行（Codex CLI 按需派活）/ B 验证（纯 bash，30min 常驻，信任锚点）/ C 审计（Claude Code，12h）/ D 战略（主线程）
- Loop A 派活: 任务写 /tmp/task.md → `tmux new-session -d -s loop-a-taskN "cd $PROJ && source ~/.bashrc && cat scripts/graph/loop_a_exec_constraints.md /tmp/task.md | codex exec --dangerously-bypass-approvals-and-sandbox 2>&1 | tee -a logs/graph/loop_a.log"`（PROJ=~/wzh/projects/agents_final_tech）
- Loop C 派活: `claude -p "<指令>"`
- 健康: `bash scripts/graph/graph_orchestrator.sh status|logs|start|stop`
- 每轮派活/验收写 `logs/graph/dispatch_log.md`: `[HH:MM] #N 任务 → 结果 → commit`

## 目录约定

- 项目: 远端 ~/wzh/projects/agents_final_tech ↔ 本地 D:\AIRcommend\JinRongAgents\agents_final_tech
- src/ ACL 三层: web / biz / storage；scripts/ 工具链；config/ schema
- 样本: ~/wzh/m1_samples/（含 scenario1/，永不 commit）；manifest 不 commit
- 文档四层: 见 docs/INDEX.md；skill 注册表: 见根 AGENTS.md「Skill 武库注册表」
- 开发机一键同步: `cd ~/wzh/projects/agents_final_tech && git pull && bash scripts/graph/sync_skills.sh`

## 冻结红线

- tests/test_m1_service.py（冻结节点）；scripts/graph/frozen_hashes.txt（冻结基准）；schema 冻结 hash
- 不碰 API key；模型准入走预算门（72B 已删除）；归档用 git mv 不用 rm；不 enable systemd；审查意见不照单全收
- OpenCode/MCP 交付物三件（09/10/2026-07-19_m2_mcp_verification）2026-08-05 归档至 docs/archive/：可归档、永不删除，INDEX 归档组保留条目
- HANDOFF.md 冻结为历史文档；现状写 memory/STATE.md

## 质量基线（2026-08-22 更新）

- M1 解析: 100%（scenario1 15 源 30 表）；gap/遗留项台账唯一存放于 memory/THREADS.md（只引用不复述）
- M2 eval 基线: 确定性 16/16 + NF 0/9 + judge 四维 5.0（08-22, 经 :5050）；embeddings 137
- pytest: 379 passed / 13 skipped（08-22）；Loop B 30min 一轮（08-22 overall PASS）