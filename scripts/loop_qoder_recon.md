# 任务：Qoder CLI 迁移侦察（只读查证 + 隔离试装 + 写方案，不切换）

## 背景与授权边界（最重要，先读）
用户 2026-07-29 提出：远程开发机助手可能从 Codex CLI 换成 Qoder CLI，因 Qoder 对
Qwen 系列与国内链路（Token Plan）适配或更顺（Codex 现需 responses2chat 代理 +
--dangerously-bypass-approvals-and-sandbox，较拧巴）。**本 loop 只做侦察与隔离试装，
绝不执行切换。** 任何"卸载 codex / 切换默认助手 / 删除 ~/.codex / 修改正在用的
config / 中断在跑的 loop/代理/模型服务"的动作，只写进方案文档，等用户醒来看报告后确认。

已知事实（无需再证）：~/.codex 内无业务资产（仅 Codex 会话/记忆/skill 痕迹），换工具
不丢业务内容；业务资产在 git 与 ~/wzh/。Codex 会话历史留而不删、不迁。

## 待核实的未知（以官方/npm 实时查证为准，禁止凭假设写死配置）
- Qoder CLI 的确切包名与安装方式（npm 全局？独立二进制？pip？brew？）。
- Qoder 是否支持自定义 OpenAI-compatible provider / base_url，配置语法为何。
- Qoder 的非交互/脚本化执行方式（类比 codex exec）。
- Qoder 能否接本地 :8004（OpenAI chat 协议）与 Token Plan（responses 协议，或经本地
  responses2chat 代理 :8100 转 chat）。
种子线索（**待核实，可能过时或错误**）：Qoder 为阿里通义系 AI 编程产品，或有 IDE+CLI/agent
形态；官网/文档域名不确定，先搜官方与 npm registry 再定。

## 约束
- 不卸载 codex；不改 ~/.codex；不动 ~/.codex/config.toml 与正在用的 provider；不动
  responses2chat 代理(:8100)、OpenCode/opencode.json、llama-server(:8004)、FastAPI(:5000)。
- 不中断任何在跑的 tmux loop（codex-m1-* 等）。
- 隔离试装：装到独立 prefix（如 ~/.local/qoder 或 npm --prefix ~/.local/qoder），不污染
  全局 codex。试装失败→BLOCKED 记录，不重试破坏环境，不 sudo。
- 不下载大模型；模型试跑限单次、60s 超时、限流。
- 不 push；不碰 TAT-DQA / test split；报告脱敏（不含 key 值）。

## Phase 0 查证
搜官方文档与 npm registry（npm view / npm search qoder；curl 官方文档页），确认包名、
安装命令、自定义 provider 配置语法、非交互执行命令。把查证到的**确切**命令记入报告；
查不到就标 BLOCKED-unknown 并停，不猜。

## Phase 1 隔离试装
按 Phase 0 查证结果装到独立 prefix；记录版本、二进制路径、是否依赖网络登录/账号。
若需账号登录才能用→记录该门槛（不替用户登录）。

## Phase 2 连通性试跑（仅当 Phase 1 成功）
用 Qoder 接我们的 provider 跑一个最小只读任务（如"读取并复述 AGENTS.md 首行"），优先试
本地 :8004（chat 协议，最省事），再试 Token Plan / :8100 代理。单次、60s 超时。
若 Qoder 不支持我们的协议→记录 BLOCKED-mismatch + 缺什么；**不**为迎合而改我们的代理/
模型服务。记录 Qoder 实际发出的请求协议（若可观测），便于判断适配度。

## Phase 3 共存评估 + 迁移方案（不执行）
- Qoder 与 codex 能否共存（不同二进制/配置目录，大概率能）。
- 得失：Qoder 对 Qwen/国内链路适配 vs 我们已为 codex 建的 skill/监督器/loop 资产在 Qoder
  下能否复用（neat-freak 等 SKILL.md 是平台无关 markdown，或可复用；监督器/loop 指令与
  工具无关，可复用；responses2chat 代理与工具无关，可复用）。
- 给出**分步迁移方案**（含回滚步骤），但本 loop 不执行任何切换/卸载。

## 报告
docs/experiments/$(date +%F)_qoder_recon.md：查证结果（确切命令）/ 试装结果 / 连通性结果 /
共存评估 / 迁移方案 / 红线遵守清单 / 给用户的"是否切换"建议。脱敏。

## 提交（不 push）
git add 报告；commit 注明"recon only, no switch performed"。

## 停止条件
Phase 0 查不到安装方式→BLOCKED-unknown 停；Phase 1 装失败→BLOCKED 停；Phase 2 协议不匹配→
记录后仍写 Phase 3 方案；全完成→正常。全程不卸载/不切换/不删 ~/.codex/不中断在跑服务。
