# 16 Qoder CLI 迁移评估与计划（2026-07-29 用户发起，侦察进行中）

**状态：侦察 loop 已排队/运行中，尚未切换；现役远程助手仍为 Codex CLI。**
本文是计划与决策留痕，不是现役配置说明。现役边界以 AGENTS.md 为准；收口时需把本文
结论回写 AGENTS.md / HANDOFF.md（见末节收口待办）。

## 1. 决策来源

用户 2026-07-29 睡前提出：远程开发机助手或由 Codex CLI 换为 Qoder CLI，理由是 Qoder 对
Qwen 系列与国内链路（Token Plan）适配或更顺。现状痛点属实：Codex CLI 接 Token Plan 需
responses2chat 代理(:8100)，接 GB10 需 `--dangerously-bypass-approvals-and-sandbox`
（bubblewrap user namespace 不可用），配置拧巴。

## 2. 时序（关键）

迁移**排在业务链 C/D 之后**，绝不与在跑的 loop 并行改环境：
A(扩schema+勾稽,已完成) → C(LLM建未知表头映射,运行中) / B(OCR兜底,收尾) →
D(多Agent委派验证) → **Qoder 侦察** →（用户确认后）才可能切换。
由独立 v2 监督器 `supervisor_qoder.sh` 接力：与旧 `supervisor_m1.sh` 在 D 上互斥兜底
（B 失败时旧监督器会跳过 D，v2 接手启 D），D 完成后启 Qoder 侦察。

## 3. 红线（侦察 loop 已硬编码，切换需用户另行确认）

侦察 loop `loop_qoder_recon.md` 只做：官方查证 + 隔离试装(独立 prefix) + 连通性试跑(单次/
限流) + 写迁移方案。**不**卸载 codex、**不**切换默认助手、**不**删 ~/.codex、**不**改正在用
的 config、**不**中断在跑 loop/代理/模型服务。任何切换/卸载动作只进方案文档。

## 4. 资产影响评估（已只读核实）

- `~/.codex`（157M）仅含 Codex 会话/记忆/skill(neat-freak)/config 备份等痕迹，**无业务资产**；
  grep 用户手放笔记/密钥类文件为空。换工具不丢业务内容。
- 业务资产在 git 与 `~/wzh/`（m1_samples 真实样本、models 权重、datasets），与 CLI 无关。
- 与工具无关、可复用的资产：responses2chat 代理、OpenCode/opencode.json 与 MCP、监督器/
  loop 指令（纯 markdown/bash）、neat-freak 的 SKILL.md（平台无关 markdown，Qoder 若支持读
  markdown 指令即可复用）。
- 结论：Codex 会话历史**留而不删、不迁**；切换零业务数据风险。

## 5. Qoder 侦察结论（待 loop 填写，以下为决策框架占位）

| 侦察结果 | 建议 |
|---|---|
| Qoder 可装 + 可接我们的 provider + 对 Qwen 明显更顺 | 建议迁，按方案分步执行并保留 codex 回滚 |
| Qoder 可装但无明显优势 / 需额外账号门槛 | 建议暂留 codex，记录差异备查 |
| Qoder 不可装 / 协议不匹配 / 需破坏性改动 | 建议留 codex，记录阻塞原因 |

注：Qoder CLI 的确切包名/安装/自定义 provider 语法在本计划撰写时**未经核实**，以侦察 loop
实时查证官方/npm 为准；本表不预设结论。

## 6. 收口待办（整条链跑完、工作树静止后一次性处理，不自动执行）

1. 回写规则层：据侦察结论给 AGENTS.md / HANDOFF.md 加 Qoder 指针或更新现役助手表述
   （本轮为避与 C/D 改既有文件冲突，未改 AGENTS/HANDOFF，仅以本文 + git log 留痕）。
2. 处理 git 三方分叉：远程本地含 A/B 的 commit（HEAD 曾为 41ea6ad）与 origin 分叉，且远程
   工作树有 untracked 的 C/D/监督脚本（与 origin tracked 同名）+ B 的 m1_ocr_*.py + modified
   parser。收口步骤：确认所有 codex 进程退出 → 同名 untracked 与 origin 版本 diff 一致后删除
   或 checkout 覆盖 → 真正新改动(B 脚本/parser)单独 commit → rebase origin 解冲突 → push。
   此步有冲突风险，人工/下次 check 做，不自动 reset。
3. 恢复 A 报告工作树副本：若 `docs/experiments/*_m1_schema_reconcile.md` 工作树缺失，用
   `git show <A-commit> -- <path>` 还原（git 历史中仍在）。
4. 可选清理：已完成的空挂 tmux（codex-integrate/m1-batch/m1-real/m1-schema）与残留 ssh 会话。

—— 本文为用户确认的迁移评估计划；在侦察 loop 出报告且用户拍板前，远程现役助手保持 Codex CLI。
