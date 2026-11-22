# memory/CORE.md — 架构与历史运行基线（按需加载）

更新: 2026-11-15。Docker/PG、27B及OpenCode为本次恢复实测；其他服务、CLI配置和质量数字仍是注明日期的历史基线。当前任务与授权以Goal、用户指令及STATE为准。

## 系统拓扑（GB10 开发机，ARM64）

GB10 的默认 SSH 入口 `ssh jinrong-dev` 走 Tailscale，2026-11-22 已在 Windows 本机通过严格主机校验及免交互登录。现役脚本继续使用此别名。本机也可用 `ssh gb10`，连接端须加入有权访问 GB10 的 Tailscale 网络。校园网备用入口为 `ssh jinrong-dev-campus`，校园网地址变动时只更新备用别名。

| 端口 | 服务 | 说明 |
|---|---|---|
| :5050 | FastAPI 主 harness (main:app, uvicorn workers=2) | M1 解析 / M2 RAG 问答 / UI (/m1) |
| :8004 | llama-server Qwen3.6-35B-A3B + mmproj | 按需停用；需视觉/35B时先卸载驻留27B |
| :8005 | RETIRED (Qwen3-14B, 08-17 退位) | Loop B 断言 down; 权重保留 |
| :8006 | vLLM Qwen3.8-27B-FP8（研究别名） | 11-15用户要求恢复驻留：loopback，32K/单并发/4GiB KV；下轮训练先卸载，当前实况查私有*_current.json |
| :4096 | OpenCode 1.18.3（scripts/sidecar_launch.sh） | 默认/小模型均gb10v/qwen38-27b-fp8→:8006；禁工具实际回复OK已核验 |
| :8100 | responses2chat proxy v2 | Responses API → Chat API（Chat-only 模型用） |
| :15432 | PostgreSQL + PGVector (docker) | 已运行，pg_isready通过；未变更库或数据 |
| :8090 | ZhikunCode (docker) | Multi-Agent 平台，可选扩展面 |

本次只恢复必要研究环境，未探测/启动:5050、:8005、72B或历史可选容器；未新增开机自启。校园网络登录由既有bupt-login.service管理。校内DeepSeek历史24tokens检查保留；本轮TLS通达、未认证查询返回401，当前进程未驻留凭证，未新增校内模型调用。

内存保护：research_gpu_guard.py持有~/wzh/.gpu_lock，3秒检查MemAvailable，低于32GiB只停止其持有的不可变研究容器ID；Docker状态超时或停止失败继续持锁重试。FinQA权重加载器也取同锁，加载前至少48GiB可用。RPC使用另一个任务锁；训练/换模必须先卸载驻留模型。当前运行身份与日志在私有research_services/*_current.json；不是全机或任意手工进程的绝对OOM保证。

11-15追加恢复：监督从启动前持有权重锁，修复Docker小写“no such object”导致的误判；GB10守护定点检查7项通过。Docker/PG、OpenCode及CUDA环境均实测可用；OpenCode→27B禁工具回复OK，本次运维18,981tokens另账。运行证据保存在私有research_services/restore_1794684466/。

11-15再次核验：必要服务已在线，保留运行实例而未重启。OpenCode→27B新会话禁工具回复OK，新增本地运维18,981tokens（累计55,809，独立于科研账）；PG接受连接、校园登录服务active。可用内存73.4GiB，守护心跳与权重锁均已实测，仍为32K/单并发/32GiB余量。回执research_services/verify_1794694439/SERVICE_VERIFICATION.json；校内地址返回401，当前未恢复带凭证调用。无新科研训练或评估。

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
