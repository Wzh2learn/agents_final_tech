# 2026-08-07 全系统工具盘点（T1）

> 状态: 活跃 | 更新: 2026-08-07 | 取代/被取代: 无（docs/21 为 08-02 基础设施盘点, 本文是其工具层续篇）
> 方法: skill-doctor 实跑 + 三端安装 diff + 进程/端口实测 + dispatch_log 使用证据 grep
> 口径更正 (2026-08-08): skill-map 未实跑 — GB10 无 ripgrep (其硬依赖), GitHub release 下载 rg 失败 (08-08 实测); 三端分发一致性由 skill-doctor + sync 清单人工核验覆盖。

## 1. Skills 体系

**规模**: 仓库 skills/ 14 个 (source of truth) → sync_skills.sh 分发 A 列 8 个到 ~/.codex/skills (+独立 neat-freak), C 列 8 个到 ~/.claude/skills; OpenCode 经 opencode.json \"skills.paths: [skills]\" 直接读仓库目录 (14 个全可见, S4 已验证)。

**三端 diff (实测)**: 三端与 sync_skills.sh 清单完全一致, 无漂移。

**skill-doctor 实跑结果**:
- 仓库 skills/: 5 error + 13 warning。error 全部是 agents/openai.yaml 缺失/策略不符 (agent-prompt-contracts、graph-loop-rules、jinrong-docs-sync、m1-gap-triage 缺 yaml; security-best-practices allow_implicit_invocation=false 与 doctor 期望 true 不符), 均可 --fix-safe 修, 不影响运行时分发。warning 为社区 skill 缺显式完成契约 (COMPLETION_EVIDENCE_MISSING), 记录不修。
- 本地 ~/.codex/skills (Loop D 全套): 同类 error 若干 (playwright/security-threat-model/vercel-deploy 等缺 policy 字段; skills-best-practices 缺 frontmatter), Loop D 自用不受影响, 记录不修。

**使用证据 (dispatch_log grep)**: jinrong-docs-sync 6 次 | graph-loop-rules 2 | m1-gap-triage 2 | neat-freak 2 | agent-prompt-contracts 1 (昨夜创建即用于 T1 闭环审计口径)。

**逐项状态**:
| skill | 状态 |
|---|---|
| 10 个 Phase 0 社区 skill (A4+C6) | 存活, 已分发, 有使用证据或按需触发型 |
| jinrong-docs-sync / m1-gap-triage / graph-loop-rules | 存活-活跃 (自定义, 高频) |
| agent-prompt-contracts | 存活 (08-06 新建, 治理规则 5 强制挂钩) |
| skill-doctor / skill-map | 存活 (Loop D 体检工具, 本轮实跑) |
| 本地其余 Loop D 工具 skill (codebase-map/pdf/playwright 等) | 存活, 按需 |

**建议**: ① 对仓库 4 个缺 openai.yaml 的自定义 skill 跑一次 skill-doctor --fix-safe (低风险, 下轮顺手); ② 其余保留现状。

## 2. MCP 三件套

| server | 进程 | 挂载方 | 状态 |
|---|---|---|---|
| jinrong-rag (mcp_server) | PID 811916 (opencode stdio 子进程) | OpenCode ✓ | 存活-活跃 (m2-qa 经它检索, A2 灰度链在用) |
| vision_mcp_server | PID 811919 | OpenCode ✓ | 存活 (后端 :8004 mmproj; :8007 VLM 停摆, GGUF 线已关闭) |
| tabular_mcp_server | PID 811922 | OpenCode ✓ | 存活 (tabular-runner demo 用过) |

**各 harness 可达性**: OpenCode ✓ (opencode.json 注册, e2e 验证过) | Loop C (Claude Code) 待接线 — 方案已评估入 THREADS 待办 (claude mcp add + start 脚本自载 env, 配置侧零密钥) | Loop A (codex CLI) 无 — config.toml 无 mcp_servers 段, 当前无需求。

**建议**: 保留; Loop C 接线按触发条件启动 (审计需频繁核验 RAG 答案时)。

## 3. CLI 表面

上轮 T3.3 清单 (THREADS 待批) 仍成立: 唯一动手项 = m1-extraction prompt 内联绝对路径长命令 → 建议封装 scripts/opencode_m1_extract.sh; verifier/m2-qa 不动。

**使用证据 (dispatch_log)**: m1_rag_ingest 4 | m1_rag_qa 3 | m1_statement_parser 2 (经 opencode m1-extraction) | demo.sh 2 (+本轮实跑全绿)。scripts/ 61 个活跃脚本清单见 phase3_review_scripts.md, 无新增死脚本。

## 4. 千问 Harness 工具 (scripts/qwen_harness_tools.py)

**使用证据**: dispatch_log 0 次直接调用记录; 唯一实证 = 07-31 Loop C R7 审计用 web_search 辅助 (SUMMARY_audit_loop_c.md)。phase3 审查确认脚本本身健康度好 (stdlib 单文件, 错误路径规范)。

**判定**: 保留 (成本低, 审计/验证场景的备用能力), 不强制使用; Loop C 审计 prompt 中的工具说明保留。

## 5. Top 3 建议

1. **skill-doctor --fix-safe 仓库 4 个自定义 skill 的 openai.yaml** (5 min 级, 消 doctor error)。
2. **Loop C 接 jinrong-rag MCP 的触发条件保持观望** — 当前审计靠 bash + git 足够, 接线收益未显现。
3. **opencode_m1_extract.sh 封装待用户批准后动手** — 唯一 CLI 表面债务, 收益 = prompt 缩短 + 路径漂移免疫。
