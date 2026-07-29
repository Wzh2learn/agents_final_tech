# Qoder CLI 迁移侦察报告

**日期**: 2026-07-29
**性质**: 只读侦察 + 隔离试装，**未执行任何切换/卸载/修改**
**状态**: Phase 0-1 完成，Phase 2 BLOCKED（需账号），Phase 3 方案已写

---

## Phase 0: 查证结果

### 包名与安装

| 项目 | 国际版 | 国内版 (CN) |
|------|--------|-------------|
| npm 包名 | `@qoder-ai/qodercli` | `@qodercn-ai/qoderclicn` |
| 二进制名 | `qodercli` | `qoderclicn` |
| 当前版本 | 1.1.7 (2026-07-28) | 1.1.7 (2026-07-28) |
| 解压大小 | 67.2 MB | 67.2 MB |
| Node 要求 | >= 20.0.0 | >= 20.0.0 |
| 唯一依赖 | sharp ^0.34.5 | sharp ^0.34.5 |
| 维护者 | yn_cr@alibaba-inc.com, dev@qoder.com | 同左 |
| 仓库 | github.com/nicepkg/qodercli (private) | 同左 |

安装命令（全局）:
```bash
npm install -g @qoder-ai/qodercli        # 国际版
npm install -g @qodercn-ai/qoderclicn    # 国内版
```

隔离安装（本次使用）:
```bash
npm install --prefix ~/.local/qoder @qoder-ai/qodercli
# 二进制: ~/.local/qoder/node_modules/.bin/qodercli
```

### 认证体系（硬门槛）

Qoder CLI 使用**自有认证体系**，即使配置了外部 provider 也**必须登录**：

1. **浏览器登录**: `qodercli login` → 打开浏览器 OAuth
2. **PAT 令牌**: `export QODER_PERSONAL_ACCESS_TOKEN="<pat>"` → 服务端验证
3. PAT 创建地址: `https://qoder.com/account/integrations`
4. CN 版认证端点: `openapi.qoder.com.cn`（阿里云帮助中心托管文档）
5. 国际版认证端点: `openapi.qoder.sh`

**实测**: 未登录时任何操作（含 `-p` 非交互模式）均返回
`Not logged in. Run 'qodercli login' to authenticate.`
PAT 格式错误时抛 `QoderAuthError: auth.exchangeJobToken failed: invalid personal token format`

### 非交互/脚本化执行

```bash
qodercli -p "prompt here"                           # 非交互，输出后退出
qodercli -p -m "provider/model" "prompt"            # 指定模型
qodercli --dangerously-skip-permissions -p "prompt" # 跳过权限检查
qodercli --permission-mode bypass_permissions -p "prompt"
```

权限模式: `default`, `accept_edits`, `bypass_permissions`, `dont_ask`, `auto`

环境变量对标:
| 环境变量 | 对标参数 |
|----------|----------|
| `QODER_MODEL` | `-m, --model` |
| `QODER_MCP_CONFIG` | `--mcp-config` |
| `QODER_WORKING_DIR` | `-w, --cwd` |
| `QODER_PERMISSION_MODE` | `--permission-mode` |
| `QODER_SESSION_ID` | `--session-id` |

### 自定义 Provider 配置（关键）

配置位置: `~/.qoder/settings.json`（全局）或 `<project>/.qoder/settings.json`（项目级）

settings.json 中 `"providers"` 字段语法（从 bundle 逆向确认）:

```json
{
  "providers": {
    "<provider-id>": {
      "displayName": "显示名称",
      "baseUrl": "http://127.0.0.1:8004/v1",
      "apiKey": "sk-xxx",
      "model": "默认模型ID",
      "contextWindow": 16384,
      "maxOutputTokens": 4096,
      "models": [
        {
          "modelId": "模型ID",
          "displayName": "显示名",
          "contextWindow": 16384,
          "maxOutputTokens": 4096,
          "capabilities": {
            "tools": true,
            "vision": false,
            "thinking": false
          }
        }
      ],
      "firstPayloadTimeoutMs": 60000,
      "streamIdleTimeoutMs": 30000
    }
  }
}
```

**适配器选择规则**:
- provider-id 为 `"aliyun-bailian"` → 使用阿里云百炼 API 适配器
- provider-id 为**其他任意值** → 使用标准 **OpenAI-compatible** 适配器
  （即 `/v1/chat/completions` + SSE streaming + function calling）

模型引用格式: `<provider-id>/<modelId>`，如 `local-llama/qwen3-14b`

### 协议分析

外部 provider 请求格式（从 bundle 确认）:
```
POST {baseUrl}/chat/completions
Content-Type: application/json
Authorization: Bearer {apiKey}

{
  "model": "<modelId>",
  "messages": [...],
  "stream": true,
  "stream_options": {"include_usage": true},
  "tools": [...]  // 如果 capabilities.tools=true
}
```

**结论**: 与 llama-server :8004 的 OpenAI chat 协议**完全兼容**。
与 responses2chat 代理 :8100 转出的 chat 协议也兼容。
**不需要** Qoder 支持 Responses API — 它走的就是标准 chat completions。

### 配置目录

| 站点 | 默认路径 | 完整路径变量 | 目录名称变量 |
|------|----------|-------------|-------------|
| Qoder | `~/.qoder` | `QODER_CONFIG_DIR` | `QODER_CONFIG_DIR_NAME` |
| QoderCN | `~/.qoder-cn` | `QODERCN_CONFIG_DIR` | `QODERCN_CONFIG_DIR_NAME` |

项目级: `<cwd>/.qoder/`（settings.json, settings.local.json, commands/, skills/）

### MCP 支持

- `--mcp-config <path-or-json>` 或 `QODER_MCP_CONFIG` 环境变量
- 支持 JSON 文件路径或 inline JSON
- 与 opencode.json 中的 MCP 配置格式兼容（标准 MCP 协议）

### 其他能力

- Skills 系统（类似 codex 的 SKILL.md）
- Hooks（PostToolUse 等事件钩子）
- Subagent / 子代理
- 会话管理（continue, resume, list, delete）
- Remote sessions（云端远程会话）
- Plugins 系统
- 动态 Workflows
- 多模态输入（图片、PDF）
- 内置 Web 搜索

---

## Phase 1: 隔离试装结果

| 项目 | 结果 |
|------|------|
| 安装路径 | `~/.local/qoder/node_modules/.bin/qodercli` |
| 版本 | 1.1.7 |
| 磁盘占用 | 156 MB（含 node_modules） |
| `--version` | ✅ 正常输出 `1.1.7` |
| `--help` | ✅ 正常输出完整帮助 |
| `--list-models` | ❌ 需要登录 |
| `-p "prompt"` | ❌ 需要登录 |
| 自动创建 `~/.qoder/` | 是（含默认 settings.json, installation_id, logs） |
| 对 `~/.codex` 的影响 | **无**（config.toml 未修改） |
| 对在跑服务的影响 | **无**（tmux sessions, :8004, :8100, :5000 均正常） |

---

## Phase 2: 连通性试跑

**状态: BLOCKED-auth**

原因: Qoder CLI 强制要求有效 Qoder 账号认证（服务端验证），即使只使用外部
provider 也不例外。无法在不替用户注册/登录的情况下完成连通性测试。

**理论适配度评估**（基于协议分析，非实测）:

| 目标 | 协议 | 理论适配 | 备注 |
|------|------|----------|------|
| llama-server :8004 | OpenAI chat completions | ✅ 完全兼容 | Qoder external provider 直接发 chat/completions |
| responses2chat :8100 | OpenAI chat completions (转出) | ✅ 兼容 | 代理转出的就是 chat 协议 |
| Token Plan (Responses API) | OpenAI Responses API | ⚠️ 需经 :8100 代理 | Qoder 不直接说 Responses API，但代理转 chat 后可用 |

**缺什么**: 仅需一个有效 Qoder 账号（免费注册）+ PAT 令牌即可解锁全部功能。

---

## Phase 3: 共存评估 + 迁移方案

### 共存评估

**结论: 完全可以共存，零冲突。**

| 维度 | Codex CLI | Qoder CLI | 冲突? |
|------|-----------|-----------|-------|
| 二进制 | `codex`（全局 npm） | `qodercli`（可隔离 prefix） | ❌ |
| 配置目录 | `~/.codex/` | `~/.qoder/` | ❌ |
| 项目配置 | `AGENTS.md` | `.qoder/settings.json` + `AGENTS.md`（也读） | ❌ |
| 认证 | OpenAI API key / Token Plan | Qoder 账号 PAT | ❌ 独立 |
| MCP | opencode.json | `--mcp-config` / settings | ❌ 可共用 |
| 端口 | 无独占端口 | 无独占端口 | ❌ |

### 资产复用评估

| 现有资产 | Qoder 下可复用? | 说明 |
|----------|----------------|------|
| SKILL.md (neat-freak 等) | ✅ 大概率可复用 | Qoder 有 Skills 系统，格式类似；需确认兼容性 |
| AGENTS.md | ✅ 可复用 | Qoder 也读 AGENTS.md |
| responses2chat 代理 :8100 | ✅ 工具无关 | Qoder 走 chat 协议，代理照用 |
| llama-server :8004 | ✅ 直接兼容 | Qoder external provider 直连 |
| opencode.json MCP 配置 | ✅ 可复用 | 标准 MCP 协议，`--mcp-config` 传入 |
| tmux loop 脚本 | ⚠️ 需改调用命令 | `codex exec` → `qodercli -p`，逻辑不变 |
| 监督器/loop 指令 | ✅ 工具无关 | prompt 内容不变，只换调用壳 |
| `~/.codex/` 会话历史 | ❌ 不迁移 | 留而不删，Qoder 有自己的会话管理 |

### Qoder 相对 Codex 的潜在优势

1. **Qwen 原生适配**: 内置 Qwen 3.7 Max/Plus/Flash 模型定义，含 thinking 能力声明
2. **阿里云百炼直连**: provider-id 为 `aliyun-bailian` 时有专用适配器
3. **国内链路**: CN 版认证/文档走 `qoder.com.cn` / 阿里云帮助中心
4. **无需代理即可用 Qwen**: 如果 Token Plan 的 Qwen 模型走百炼 API，可能不需要 responses2chat 代理
5. **权限模式更丰富**: `bypass_permissions` 不需要 `--dangerously-bypass-approvals-and-sandbox` 这种长 flag
6. **MCP + Skills + Hooks + Workflows**: 功能集与 Codex 对标或更丰富

### Qoder 相对 Codex 的潜在劣势/风险

1. **强制账号**: 即使只用本地模型也必须注册 Qoder 账号（网络依赖）
2. **认证服务端验证**: PAT 需要联网验证，离线环境无法使用
3. **私有仓库**: 代码不开源（github.com/nicepkg/qodercli 为 private），无法审计
4. **Proprietary 许可**: npm 包标注 `Proprietary`，非 OSS
5. **67MB 包体**: 比 codex 大（含 sharp 原生模块）
6. **生态成熟度**: 相比 Codex CLI（OpenAI 官方开源），Qoder CLI 社区/文档较新
7. **skill 格式兼容性未验证**: SKILL.md 可能需要适配

### 分步迁移方案（仅供用户审批后执行，本 loop 不执行）

#### 前置条件
- [ ] 用户注册 Qoder 账号（https://qoder.com 或 CN 版）
- [ ] 创建 PAT 令牌
- [ ] 在 GB10 上验证 PAT 可用: `QODER_PERSONAL_ACCESS_TOKEN="<pat>" qodercli --list-models`

#### Step 1: 正式安装（可选全局或隔离）
```bash
# 方案 A: 全局安装（与 codex 共存）
npm install -g @qodercn-ai/qoderclicn   # CN 版，国内链路更顺

# 方案 B: 隔离安装（更保守）
npm install --prefix ~/.local/qoder @qodercn-ai/qoderclicn
alias qodercli='~/.local/qoder/node_modules/.bin/qoderclicn'
```

#### Step 2: 配置外部 provider
```bash
cat > ~/.qoder/settings.json << 'EOF'
{
  "providers": {
    "local-llama": {
      "displayName": "Local Qwen3-14B (llama-server)",
      "baseUrl": "http://127.0.0.1:8004/v1",
      "apiKey": "sk-no-key-needed",
      "model": "qwen3-14b",
      "contextWindow": 16384,
      "maxOutputTokens": 4096,
      "models": [
        {
          "modelId": "qwen3-14b",
          "displayName": "Qwen3 14B Local",
          "contextWindow": 16384,
          "maxOutputTokens": 4096,
          "capabilities": { "tools": true, "vision": false, "thinking": false }
        }
      ]
    }
  }
}
EOF
```

#### Step 3: 连通性验证
```bash
export QODER_PERSONAL_ACCESS_TOKEN="<pat>"
qodercli -m "local-llama/qwen3-14b" -p "读取 AGENTS.md 首行并复述" --dangerously-skip-permissions
```

#### Step 4: 并行运行期（建议 1-2 周）
- codex 和 qodercli 同时可用
- 新 loop 用 qodercli 试跑，旧 loop 继续用 codex
- 比较两者在 M1 任务上的表现

#### Step 5: 切换默认（仅当 Step 4 满意后）
- 修改 tmux loop 脚本中的调用命令
- 更新 AGENTS.md 中的工具说明
- codex 保留不卸载（回滚用）

#### 回滚步骤
- 所有 loop 脚本改回 `codex exec`
- 删除 `~/.qoder/`（可选）
- `npm uninstall -g @qodercn-ai/qoderclicn`（可选）
- codex 配置从未被动过，零回滚成本

---

## 红线遵守清单

| 红线 | 状态 |
|------|------|
| 不卸载 codex | ✅ 未执行 |
| 不改 ~/.codex | ✅ config.toml 未修改 |
| 不动 responses2chat 代理 :8100 | ✅ 未触碰 |
| 不动 opencode.json | ✅ 未触碰 |
| 不动 llama-server :8004 | ✅ 健康检查 200 |
| 不动 FastAPI :5000 | ✅ 健康检查 200 |
| 不中断 tmux loop | ✅ 全部 6 个 session 正常运行 |
| 不 sudo | ✅ 未使用 |
| 不下载大模型 | ✅ 未下载 |
| 不 push | ✅ 仅本地 commit |
| 不碰 TAT-DQA / test split | ✅ 未触碰 |
| 报告脱敏 | ✅ 不含 key 值/服务器地址 |
| 隔离安装 | ✅ ~/.local/qoder prefix |

---

## 给用户的"是否切换"建议

**建议: 值得尝试，但不急切。**

**理由**:
1. Qoder 对 Qwen/百炼的原生适配确实比 Codex + responses2chat 代理更顺畅
2. 协议层面完全兼容我们的 :8004 和 :8100，不需要改任何现有服务
3. 共存零成本，可以先并行跑再决定
4. **但**: 强制账号 + 私有代码 + Proprietary 许可 是实质性顾虑
5. **但**: 我们已为 Codex 建的 skill/loop/监督器资产运作良好，切换收益需实测验证

**下一步行动（需用户确认）**:
1. 注册 Qoder 账号，获取 PAT
2. 用 PAT 完成 Phase 2 连通性实测
3. 跑一个 M1 小任务对比 Codex vs Qoder 体验
4. 根据实测结果决定是否进入并行期

---

## 附录: 本次试装产生的文件

- `~/.local/qoder/` — 隔离安装目录（156MB），可随时 `rm -rf` 清除
- `~/.qoder/` — CLI 自动创建的默认配置目录（仅含默认 settings.json），可保留或清除
- `/tmp/qoder_inspect/` — 临时检查目录，可清除
- `/tmp/qoder_test_config/` — 测试配置，可清除
