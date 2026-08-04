# 18 - 多 Agent 编排工具演进计划

> 状态: 活跃 | 更新: 2026-08-05 | 取代/被取代: 无

> **定位**: 本文档是 Graph Engineering (docs/17) 的工具层补充。
> docs/17 定义了四层 Loop 的架构和约束; 本文档解决"用什么工具来跑这些 Loop"。
>
> **面向**: 主线程 (指挥层) review 后执行部署。
> **状态**: 已部署 (2026-07-30), 待集成测试。

---

## 1. 目标

让主线程 (本机 Codex) 能够通过统一的编排层控制远端 GB10 上的多个 agent 会话,
每个会话可以使用不同的 harness (codex cli / qoder cli / zhikuncode / claude code),
并且各会话在 tmux 中隔离运行, 互不干扰。

最终效果:
```
主线程 (本机)
  │
  ├── AoE / OMC (编排控制层)
  │     ├── tmux: codex-cli    (Loop A 执行层, :8004 主力模型)
  │     ├── tmux: qoder-cli    (备选执行层)
  │     ├── tmux: zhikuncode   (Multi-Agent 协作, 国产模型直连)
  │     ├── tmux: claude-code  (高质量审计, Loop C)
  │     └── tmux: verify       (Loop B 纯脚本验证)
  │
  └── Web 仪表盘 (AoE / ZhikunCode 提供)
```

---

## 2. 工具选型与定位

### 2.1 Agent of Empires (AoE) - 编排控制层

- **仓库**: https://github.com/agent-of-empires/agent-of-empires
- **语言**: Rust (需要 aarch64 预编译包或源码编译)
- **定位**: tmux 会话管理器 + 多 harness 支持 + TUI/Web 仪表盘
- **支持的 harness**: Claude Code, Codex CLI, Gemini CLI, OpenCode, Mistral Vibe 等
- **核心能力**:
  - 每个 agent 独立 tmux session, 关终端/断 SSH 后继续跑
  - TUI 仪表盘实时查看所有 session 状态
  - Web 界面远程监控 (手机可看)
  - 会话持久化, 重启后恢复
- **与 Graph 的映射**:
  - Loop A → AoE session "codex-exec"
  - Loop B → AoE session "verify-guardian" (纯脚本)
  - Loop C → AoE session "audit-agent"
  - Loop D → 主线程通过 AoE Web/API 监控

### 2.2 oh-my-claudecode (OMC) - 并行 worker 管理

- **仓库**: https://github.com/yeachan-heo/oh-my-claudecode
- **语言**: TypeScript (Claude Code 插件)
- **定位**: Claude Code 的 team 模式增强, tmux 并行 worker
- **核心能力**:
  - team 模式: 用 tmux 启动并行 CLI worker (Claude/Codex/Gemini 混合)
  - staged pipeline: plan → prd → exec → review
  - 智能模型路由, 省 token
  - Ralph 循环: 自验证迭代直到完成
- **与 Graph 的映射**:
  - 适合 Loop C 审计层: 用 OMC 的 review pipeline 做代码审查
  - 适合并行任务: 多个 worker 同时处理不同样本的解析验证

### 2.3 ZhikunCode - 自托管 Multi-Agent 平台

- **仓库**: https://github.com/zhikunqingtao/zhikuncode
- **语言**: Java (需要 JDK 17+)
- **定位**: Claude Code / Cursor 开源自替代, 自托管
- **核心能力**:
  - CLI + Web UI 双入口
  - Multi-Agent 协作 (内置多 agent 编排)
  - 原生直连千问/DeepSeek 等国产大模型 (不需要 responses2chat 代理)
  - 插件系统 (Java SPI): 命令注册、工具注册、钩子拦截、MCP 集成
  - 8 层安全沙箱
  - 跨会话记忆 + 技能系统
  - SWE-bench Lite 56%
- **与 Graph 的映射**:
  - 可作为 Loop A 的替代执行引擎 (国产模型直连, 无协议转换)
  - Web UI 可作为 Loop D 的监控面板
  - Multi-Agent 能力可承载 Loop A + Loop C 的协同

### 2.4 其他 harness (按需安装)

| Harness | 安装方式 | 用途 |
|---------|----------|------|
| Codex CLI | 已安装 | 当前主力, Loop A |
| Qoder CLI | 已安装 (~/.local/qoder/) | 备选执行层 |
| Claude Code | npm install -g @anthropic-ai/claude-code | 高质量审计, Loop C |
| OpenCode | 已安装 (v1.18.3) | 多 agent 协同 |

---

## 3. GB10 环境现状与前置条件

| 项目 | 现状 | 需要 |
|------|------|------|
| 架构 | aarch64 (ARM64) | 所有工具需 ARM64 支持 |
| Java | OpenJDK 1.8.0_482 | ZhikunCode 需要 JDK 17+, 需升级 |
| Node.js | v25.9.0 | 够用 (OMC, Claude Code) |
| Rust/Cargo | 未安装 | AoE 需要 (或找预编译包) |
| Python | 3.12 | 够用 |
| 磁盘 | 2.8TB 可用 | 充足 |
| 内存 | 121GB (当前用 44GB) | 充足 |

---

## 4. 部署计划 (分阶段)

### Phase 1: 基础 harness 补全 (P0, 30min)

主线程执行:

```bash
# 1. 升级 JDK (ZhikunCode 前置)
sudo apt install -y openjdk-17-jdk
sudo update-alternatives --set java /usr/lib/jvm/java-17-openjdk-arm64/bin/java

# 2. 安装 Claude Code
npm install -g @anthropic-ai/claude-code
# 需要 ANTHROPIC_API_KEY 或 claude login

# 3. 验证已有 harness
codex --version
qodercli --version
opencode --version
```

### Phase 2: ZhikunCode 部署 (P0, 1-2h)

```bash
# 1. Clone
cd ~/wzh/tools
git clone https://github.com/zhikunqingtao/zhikuncode.git
cd zhikuncode

# 2. 构建 (Maven/Gradle, 看项目结构)
# 具体构建命令需要看 README, 可能是:
./mvnw package -DskipTests
# 或
./gradlew build

# 3. 配置模型 (千问 Token Plan 直连)
# 在配置文件中设置:
#   - API Key: 千问平台 Token Plan key
#   - 模型: qwen3.8-max / glm-5.2 / deepseek-v4-pro
#   - 不需要 responses2chat 代理

# 4. 启动
java -jar target/zhikuncode.jar --server.port=8080

# 5. 验证
curl http://127.0.0.1:8080/health
# 浏览器打开 http://<GB10_IP>:8080
```

### Phase 3: AoE 部署 (P1, 1h)

```bash
# 方案 A: 预编译包 (如果有 aarch64 release)
# 检查 https://github.com/agent-of-empires/agent-of-empires/releases

# 方案 B: 源码编译
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source ~/.cargo/env
cd ~/wzh/tools
git clone https://github.com/agent-of-empires/agent-of-empires.git
cd agent-of-empires
cargo build --release
# 二进制在 target/release/aoe

# 启动
./target/release/aoe
# 或作为服务: aoe serve --port 3000
```

### Phase 4: OMC 集成 (P2, 30min)

```bash
# OMC 是 Claude Code 插件, 需要先有 Claude Code
# 在 Claude Code 中安装:
claude
> /install-plugin https://github.com/yeachan-heo/oh-my-claudecode

# 或手动:
cd ~/.claude/plugins
git clone https://github.com/yeachan-heo/oh-my-claudecode.git
```

### Phase 5: 统一编排 (P2, 持续迭代)

用 AoE 作为统一入口, 注册所有 harness:

```
AoE sessions:
  ├── codex-exec     → codex cli --full-auto (Loop A)
  ├── verify         → bash loop_b_verify.sh --daemon (Loop B)
  ├── audit-claude   → claude code (Loop C, 高质量审计)
  ├── audit-qoder    → qodercli (Loop C, 备选)
  ├── zhikun-web     → zhikuncode server (Multi-Agent + Web UI)
  └── opencode       → opencode (多 agent 协同)
```

---

## 5. 与 Graph Engineering 的整合

### 5.1 Loop 到工具的映射

| Loop | 当前载体 | 演进后载体 | 变化 |
|------|----------|------------|------|
| Loop A (执行) | tmux + codex cli | AoE session + codex cli / zhikuncode | 编排层统一管理 |
| Loop B (验证) | tmux + bash 脚本 | AoE session + bash 脚本 (不变) | 纯脚本最可靠 |
| Loop C (审计) | tmux + codex cli (:8005) | AoE session + claude code / OMC review | 审计质量提升 |
| Loop D (战略) | 本机 Codex + ssh | AoE Web 仪表盘 + ZhikunCode Web UI | 可视化监控 |

### 5.2 模型分配

| 模型 | 端口 | 用途 |
|------|------|------|
| Qwen3.6-35B-A3B + mmproj | :8004 | Loop A 主力 (本地推理) |
| Qwen3-14B | :8005 | Loop C 辅助审计 (本地推理) |
| Qwen3-72B (待评估) | :8006 | 可能替换主力 |
| qwen3.8-max (云端) | 千问 API | Codex CLI / ZhikunCode 默认 |
| glm-5.2 (云端) | 千问 API via 代理 v2 | Codex CLI 可选 |
| deepseek-v4-pro (云端) | 千问 API via 代理 v2 | Codex CLI 可选 |
| Claude (云端) | Anthropic API | Claude Code / OMC |

### 5.3 关键原则

1. **Loop B 永远不用 AI**: 纯脚本验证是整个 Graph 的信任锚点, 不能被 AI 工具替代。
2. **本地模型优先**: 能用 :8004/:8005 的场景不走云端, 省 token 费 + 数据不出机器。
3. **harness 可替换**: 任何 Loop 的 harness 都可以换, 但 Loop 的职责和约束不变。
4. **ZhikunCode 是增量**: 它不替代现有体系, 而是提供一个国产模型直连的备选通道。

---

## 6. 风险与注意事项

| 风险 | 影响 | 缓解 |
|------|------|------|
| AoE 没有 aarch64 预编译包 | 需要装 Rust 编译 | 先检查 releases, 不行就 cargo build |
| ZhikunCode 需要 JDK 17+ | 当前只有 JDK 8 | apt install openjdk-17-jdk |
| Claude Code 需要 API Key | 需要 Anthropic 账户 | 用户决定是否配置 |
| 多 harness 同时跑占内存 | 121GB 可能紧张 | 按需启动, 不全部常驻 |
| ZhikunCode 成熟度 | 项目较新, 可能有坑 | 先试用, 不替代已验证的 codex cli |

---

## 7. 主线程执行清单

按优先级排序, 主线程 review 后逐步执行:

- [x] P0: JDK 17 已安装 (apt), Docker 部署不需要切默认 (2026-07-30)
- [x] P0: ZhikunCode Docker build + up, :8090 health UP, 配置 Token Plan 多 provider (2026-07-30)
- [x] P0: M1 API 404 已修 (commit 1472c6a, m1_serve.sh 加 /m1 路由) (2026-07-30)
- [x] P0: Graph 三层 Loop 已跑 (graph-loop-a/b/d, Loop A 产出 d209514) (2026-07-30)
- [x] P1: AoE v1.13.2 aarch64 预编译包已下载安装 (2026-07-30)
- [x] P1: Claude Code 2.1.220 已安装, Token Plan Anthropic 端点配置, 端到端验证通过 (2026-07-30)
- [x] P1: 72B vs 35B 对比已完成 (commit a8f640f, 72B 退化不可用) (2026-07-30)
- [x] P2: AoE 注册 3 sessions (codex-exec/verify-guardian/audit-claude) (2026-07-30)
- [ ] P2: OMC 插件 (需 Claude Code 交互安装, 暂缓)
- [ ] P2: ZhikunCode Web UI 浏览器实测 (Docker 已起, 待人眼看)
- [ ] P2: AoE 启动 session 替代手动 tmux (待集成测试)

---

## 8. 参考链接

- AoE: https://github.com/agent-of-empires/agent-of-empires
- OMC: https://github.com/yeachan-heo/oh-my-claudecode
- ZhikunCode: https://github.com/zhikunqingtao/zhikuncode
- amux: https://github.com/mixpeek/amux
- CAO: https://github.com/awslabs/cli-agent-orchestrator
- awesome-agent-orchestrators: https://github.com/andyrewlee/awesome-agent-orchestrators
- Tmux-Orchestrator: https://github.com/absmartly/Tmux-Orchestrator

## 9. 部署结果 (2026-07-30)

### 工具栈

| 工具 | 版本 | 模型通道 | 状态 |
|------|------|---------|------|
| Codex CLI | 0.145.0 | qwen 直连 + glm/deepseek 经 :8100 代理 | 已验证 |
| Claude Code | 2.1.220 | Token Plan Anthropic 端点 (千问) | 已验证 |
| Qoder CLI | 1.1.7 | 已装, 待配置 | 已装 |
| OpenCode | 1.18.3 | 本地 :8004 | 已验证 |
| AoE | 1.13.2 | 编排层, 3 sessions 注册 | 已装 |
| ZhikunCode | Docker latest | :8090, 多 provider 直连 | 已起 |

### AoE 注册的 sessions

| Session | Tool | 用途 |
|---------|------|------|
| codex-exec | codex | Loop A 执行层 |
| verify-guardian | codex | Loop B 验证 (实际跑 bash 脚本) |
| audit-claude | claude | Loop C 审计层 |

### Claude Code Token Plan 配置

通过千问 Anthropic 兼容端点, 不需要 Anthropic 账户:
- ANTHROPIC_BASE_URL: https://token-plan.cn-beijing.maas.aliyuncs.com/apps/anthropic
- ANTHROPIC_AUTH_TOKEN: Token Plan API Key
- 模型: qwen3.8-max-preview (主) / qwen3.6-flash (haiku) / qwen3.7-max (subagent)
- 端到端验证: claude -p "..." 返回正确响应

### ZhikunCode Docker 配置

- 端口: :8090
- 多 provider: DashScope + DeepSeek + Zhipu 均指向 Token Plan 端点
- Workspace: /home/testuser/wzh/projects/agents_final_tech
- Health: UP (SQLite + diskSpace + liveness + readiness)

### 待集成测试

- AoE session launch (aoe add -l 或 TUI 启动)
- ZhikunCode Web UI 浏览器实测
- Claude Code 作为 Loop C 审计的实际效果
- OMC 插件安装 (需 Claude Code 交互)

## 10. 记忆系统 (2026-08-04 Loop D 调研结论)

**应用位置优先级**: 主战场 = Graph × Skills 多 agent loop 的记忆层（解决跨会话、跨 Loop 信息同步；L1 文件协议 2026-08-04 落地，见根 AGENTS.md「记忆系统协议」）。次要 = OpenCode 侧——OpenCode 自带成熟的流程记忆机制（类 skill），交付链路中对接其现有机制即可，不重复造；未来如需语义记忆，通过 L2 的 mem0 MCP 接入。

**L1 文件协议层（已落地）**: `memory/` 目录四文件 + archive/（CORE / DECISIONS / STATE / THREADS），读取顺序 CORE → STATE → THREADS，替代 19KB HANDOFF.md 全文。

**L2 语义记忆层（排期项，OpenCode 交付链路打通后执行）**:

| 框架 | 结论 | 理由 |
|---|---|---|
| mem0（自托管 server） | **选用** | LLM/embedding 支持 OpenAI 兼容端点（可接 :8004 或 Token Plan）；向量库支持 pgvector（复用现成 :15432）；官方 MCP server（recall/save/forget）可直接暴露给 OpenCode/Claude/Codex；新增基建最少 |
| Letta (MemGPT) | 不选 | 完整 agent 运行时，引入等于换 harness，与 Graph 架构冲突 |
| Graphiti (Zep) | 升级候选 | 时序知识图谱，当"何时因何改了什么"类查询成为强需求再评估；需 Neo4j/FalkorDB 新增基建 |
| LangMem | 不选 | LangGraph 生态原语，适合嵌入 M2 代码，不适合做系统级记忆框架 |

**交付项**: mem0 部署 + MCP 接入，列入交付排期，OpenCode 交付链路验证后执行。
