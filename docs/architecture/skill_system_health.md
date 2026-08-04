# Skill 体系体检报告 (2026-08-04, Phase 1)

> 补注 (2026-08-05): 本报告扫描时仓库 skills/ 为 10 个；2026-08-04 新增第 11 个 jinrong-docs-sync（Phase 4 自定义 skill，已注册进 AGENTS.md Skill 武库），未经本轮 doctor/map 扫描。

工具: skill-doctor + skill-map (均 uv run; Windows 需 PYTHONUTF8=1 规避 GBK 解码崩溃 — skill-map 的已知平台 bug)。
扫描根: 本机 `C:\Users\王中华\.codex\skills` (Loop D 工作区) + 仓库 `skills/` (source of truth)。

## 总量

- 本地安装区: 35 个 active skill (17 社区 + 系统/插件贡献)
- 仓库 skills/: 10 个 active skill (Phase 0 入库)
- skill-map 合计去重后 63 条目 (含两处安装的重复计数)

## skill-doctor 结果

| 时点 | error | warning |
|---|---|---|
| 初检 | 47 | 32 |
| --fix-safe 后 (20 处修复) | 27 | 32 |

**已修复 (20)**: 缺失的 `agents/openai.yaml` 由 fix-safe 创建 (含仓库 skills/ 内 7 个: executing-plans / receiving-code-review / requesting-code-review / review-codebase / subagent-driven-development / systematic-debugging / verification-before-completion)。

**手工补齐 (3, 仓库 skills/)**: differential-review / spec-to-code-compliance 补 `policy.allow_implicit_invocation: true`; security-best-practices 补 `false` (其描述要求仅显式触发)。仓库 source of truth 现无 doctor error。

**剩余 27 error (全部在本机安装区, 不阻塞)**:
- 19 × OPENAI_POLICY_MISSING: 既有 yaml 缺 policy 布尔值 (fix-safe 不代写值, 需逐个按 skill 语义判定, 列入后续 neat)
- 4 × RESOURCE_LINK_MISSING: 文档链接失效
- 4 × FRONTMATTER_MISSING: algorithm-description 等个人 skill 无 frontmatter (非社区包, 不处理)

**32 warning (advisory, 不自动修)**: FRONTMATTER_FIELD_ORDER (字段顺序) 与 COMPLETION_EVIDENCE_MISSING (缺完成判据) — 社区 skill 原文风格, 记录不改。

## skill-map 结果

**重复安装 (10, 均为设计使然)**: Phase 0 的 10 个 skill 同时存在于本机 `~/.codex/skills` 与仓库 `skills/`。仓库是 source of truth, 本机是 Loop D 工作副本, 远端经 sync_skills.sh 分发 — 不视为缺陷。

**依赖关系 (全部已解析)**: figma 家族内部互链 (figma-use / figma-generate-* / figma-implement-design / figma-code-connect-components), playwright-interactive → playwright。金融项目链路 (review/debug/verify 系) 无外部依赖。

**未解析引用**: 全部为文档占位符误报 (skill-name / cdn-cgi / 50-100 等), 无需处理。

## 结论

- Phase 0 注册的 10 个 skill: metadata 健康 (仓库侧 error=0), 双端 harness 可见性已验证
- 治理动作: 每次 neat 收尾跑一次 doctor + map (AGENTS.md 治理规则 #2); 本机安装区 19 个 POLICY 缺失项列入低优清单
- 已知工具问题: skill-map 在 Windows GBK locale 崩溃, 需 PYTHONUTF8=1 (可向作者反馈)