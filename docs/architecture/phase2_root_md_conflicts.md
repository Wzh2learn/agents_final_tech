# Phase 2 根目录 MD 文档一致性审查报告

- 审查日期: 2026-08-03
- 审查范围: 仓库根目录散落 md 文件（README.md、README_Codex_使用说明.md、PROJECT_REVIEW_REPORT.md、code_review_prompt.md、implementation_guide.md）+ AGENTS.md + HANDOFF.md。根目录无 CLAUDE.md；docs/CLAUDE.md（22 行，仅通用目录/边界指引）经抽查无数值型矛盾，未列入清单。
- 方式: 只读审查，未修改任何现有文件，未执行 git 操作，未读取 ~/wzh/m1_samples/。

## 实况基准（本次审查依据）

1. Loop A / Loop C 均为 qwen3.8-max（2026-08-03 切换并验证）
2. ZhikunCode v1.2.1+7（2026-08-03 升级，docker，:8090）
3. M1 解析率 100%（scenario1：15 源 30 表）
4. M2 RAG QA 14/15 = 93%
5. VLM 线已关闭（Triton ARM64 + GGUF CDN 不可达）
6. 72B 模型已删除
7. 测试 227 passed / 13 skipped
8. skills/ Phase 0 武库已注册
9. /health embeddings = 137（计数已修复）

---

## S1 高严重度（直接误导交付或下一 session 的模型/指标判断）

### 1. HANDOFF.md:12-13 — Loop C 模型错误 + 错误的"不兼容"结论
- 原文摘录: `Claude Code model: deepseek-v4-flash-0731 (qwen3.8-max-preview incompatible with / Claude Code multi-step prompts)`
- 矛盾点: 与基准 1 冲突。2026-08-03 已验证 Loop C 使用 qwen3.8-max（Anthropic-compatible endpoint，tool_use 通过）；不兼容的仅是 qwen3.8-max-preview（AGENTS.md:276-277 已更正）。HANDOFF.md 是 AGENTS.md 指定新 session 必读文件，此条位于顶部 2026-08-01 快照，会被当作现行配置，导致 Loop C 继续挂错模型。
- 建议改法: 改为 "Claude Code (Loop C) model: qwen3.8-max via Anthropic-compatible endpoint（tool_use 验证于 2026-08-03；此前不兼容仅限 qwen3.8-max-preview）"。

### 2. README.md:5,7,18,84,98 — 客户可见指标全面过期（测试数 + RAG QA）
- 原文摘录:
  - L5: `[![Tests](https://img.shields.io/badge/tests-164%20passed-brightgreen)]()`
  - L7: `[![RAG QA](https://img.shields.io/badge/RAG%20QA-15%2F15-blue)]()`
  - L18: `| RAG 问答 | 自然语言查询 + 答案溯源 | 15/15 = 100%, 295ms |`
  - L84: `tests/                       # 164 tests (0 failures)`
  - L98: `- **测试**: pytest (164 passed, 13 skipped)`
- 矛盾点: 与基准 4、7 冲突。现行测试 227 passed / 13 skipped（非 164）；RAG QA 为 14/15 = 93%（非 15/15 = 100%）。README 是对甲方/老师的第一交付面，虚高的 15/15 与落后的 164 同时出现，交付时要么夸大数据要么显得未维护。
- 建议改法: 徽章与表格统一更新为 `227 passed / 13 skipped` 与 `RAG QA 14/15 = 93%`；L18 延迟 295ms 若仍属实可保留，否则一并复核。

### 3. AGENTS.md:172, 209 — Loop C 仍写作 "Claude Code + glm-5.2"
- 原文摘录:
  - L172: `| Loop C | Quality audit | Claude Code + glm-5.2 | 12h freq (after 3x ACCEPTED) |`
  - L209: `- Loop C: 12h frequency (4x consecutive ACCEPTED), Claude Code + glm-5.2`
- 矛盾点: 与基准 1 冲突，且与同文件 L275-277（2026-08-03 Model Routing，Loop C = qwen3.8-max）自相矛盾。AGENTS.md 是代理行为约束文件，两处旧 Loop 状态表会把审计层指回 glm-5.2。
- 建议改法: 两处模型列改为 qwen3.8-max，并加注 "(2026-08-03 自 glm-5.2 切换)"；或在表头标注快照日期并指向 L273-281 的 Model Routing 为准。

### 4. README_Codex_使用说明.md:20 — 主线状态停留在 7 月中旬
- 原文摘录: `当前已实现三个 MCP 工具：knowledge_search、knowledge_list_collections、knowledge_get_source。M1 OCR/规则抽取、正式评测和完整多 Agent 工作流仍是后续任务。`
- 矛盾点: 与基准 3 及现行架构冲突。MCP 面为 5 个工具（另有 vision_ocr_extract、tabular_classify，见 AGENTS.md:16-20）；M1 已达成 100% 解析率（scenario1 15 源 30 表）并交付工作台；显式两跳委派已于 2026-07-29 验证（AGENTS.md:96-101）。该文件是新 session 的阅读入口之一（其自身第 5-12 行规定阅读顺序），会让代理误判 M1 仍未开始。
- 建议改法: 更新为 5 工具清单，并将"M1 仍是后续任务"改为"M1 解析 100%（scenario1 15 源 30 表），现行主线见 AGENTS.md Current Work Mainline"；或直接标注"本文件为 2026-07-19 快照，以 AGENTS.md/HANDOFF.md 为准"。

### 5. HANDOFF.md:28, 33-34 — M2 RAG QA "15/15、100% correct"
- 原文摘录:
  - L28: `M1 100% parse rate, M2 15/15 RAG QA + multi-turn sessions.`
  - L33-34: `QA suite / expanded to 15 queries, 100% correct (13 answerable + 2 documented gaps).`
- 矛盾点: 与基准 4 冲突（现行 14/15 = 93%，OCR 查询因库扩容被稀释，仍高于 80% 门槛）。L28 位于无日期限定的交付结论句，最易被当作现状引用。
- 建议改法: L28 补注快照日期（2026-08-01），并追加一行 2026-08-02 后的现行值 "14/15 = 93%（库扩至 137 embeddings 后）"；L33-34 保留日期即可，但建议在节首加"历史快照"标注。

---

## S2 中严重度（陈旧运行状态，可能误导运维/排障判断）

### 6. HANDOFF.md:50-53 — 标注 "Current state" 的段落实为 2026-07-31 状态
- 原文摘录: `**Current state**: Loop B daemon running (30min cycle, all PASS). Loop A standby. Loop C 12h frequency. :5050 M1 harness healthy (workers=2). :8004 and :8005 model services healthy. Git aligned at fe5d662 ...`
- 矛盾点: 与基准 1、2、7、9 均不同步（缺 2026-08-03 模型切换、ZhikunCode v1.2.1+7 docker :8090、227 测试、137 embeddings）。"Current state" 字样使其成为全文最具误导性的标签。
- 建议改法: 将标题改为 "State at 2026-07-31"，并在 Snapshot 顶部新增 2026-08-03 现行状态段。

### 7. AGENTS.md:272, 280 + HANDOFF.md:11 — VLM 表述为 "BLOCKED / ready"，实况为已关闭
- 原文摘录:
  - AGENTS.md:272: `VLM: scripts/vlm_server_8007.py ready but BLOCKED (Triton ARM64 JIT compilation)`
  - AGENTS.md:280: `:8007: Qwen3-VL-8B (VLM, NOT RUNNING - Triton blocked)`
  - HANDOFF.md:11: `VLM deployment blocked by Triton ARM64 (code ready in scripts/vlm_server_8007.py).`
- 矛盾点: 与基准 5 冲突。"blocked / ready" 暗示可恢复，实况是 VLM 线已整体关闭（Triton ARM64 + GGUF CDN 不可达双因），OCR 由 vision-8004 承担。代理可能据此浪费循环去复活 :8007。
- 建议改法: 三处统一改为 "VLM 线已关闭（CLOSED，2026-08-03：Triton ARM64 JIT + GGUF CDN 不可达）；OCR 走 vision-8004"。

### 8. AGENTS.md:192 — embeddings 仍写 17（4/5 样本）
- 原文摘录: `Uses PGVector collection m1_parsed_statements (17 embeddings, 4/5 samples)`
- 矛盾点: 与基准 9 冲突（现行 137 embeddings，含 scenario1 HTML + NCAMC 坐标表；计数已修复）。同文件 L283 已是 137，前后矛盾。
- 建议改法: 该节（2026-07-31 M2 RAG QA Endpoint）加"历史快照"标注，数值更新为 137 或注明"以 L283 Scenario 1 节为准"。

### 9. AGENTS.md:244 + HANDOFF.md:17 — 测试数停留在 225
- 原文摘录:
  - AGENTS.md:244: `Tests: 225 passed (was 164), 13 skipped, 0 failed`
  - HANDOFF.md:17: `5 phases complete. 225 tests (was 164).`
- 矛盾点: 与基准 7 冲突（227 passed / 13 skipped）。两处均带日期语境（2026-08-01 sprint），但都是各自文件中"最新"测试数，引用时易当成现状。
- 建议改法: 在最新快照处补一行 "2026-08-03: 227 passed / 13 skipped"；旧句保留但不再作为现行值。

### 10. AGENTS.md:40, 130, 137 + HANDOFF.md:127 — Codex CLI 默认模型仍写 qwen3.8-max-preview
- 原文摘录:
  - AGENTS.md:40: `Default model: qwen3.8-max-preview (direct, Responses API)`
  - AGENTS.md:130: `Token_Plan (direct Responses API) -> qwen3.8-max-preview (default).`
  - AGENTS.md:137: `model = "glm-5.2"  # or qwen3.8-max-preview / deepseek-v4-pro`
  - HANDOFF.md:127: `Default: qwen3.8-max-preview (direct Responses API, xhigh)`
- 矛盾点: 与基准 1 冲突（Loop A 现行为 qwen3.8-max，非 preview；AGENTS.md:275 已更新）。这些段落是操作手册口吻（switch 脚本、config.toml 示例），代理照抄会把 Loop A 切回 preview。
- 建议改法: 在 2026-07-28/07-30 各节加注"默认模型已于 2026-08-03 改为 qwen3.8-max，见 Model Routing 节"，示例行同步更新。

### 11. AGENTS.md:194 — "15 queries, 100% correct"
- 原文摘录: `QA test suite: scripts/m1_rag_qa.py (15 queries, 100% correct)`
- 矛盾点: 与基准 4 冲突（14/15 = 93%）。与第 8 条同节，同为无日期标注的"端点现状"描述。
- 建议改法: 更新为 "15 queries，14/15 = 93%（2026-08-02 库扩容后；门槛 80%）"。

### 12. README.md:15 — 解析能力面仍写 5/5 样本
- 原文摘录: `| 多格式解析 | PDF / TXT / DOCX，含扫描件 OCR | 5/5 = 100% |`
- 矛盾点: 与基准 3 不完全冲突（100% 一致）但口径过期：现行验证面为 scenario1 15 源 30 表（含竖排坐标重建、HTML 邮件正文）。对外展示 5/5 会低估已交付能力。
- 建议改法: 改为 "15 源 / 30 表 = 100%（scenario1）"。

---

## S3 低严重度（历史快照 / 措辞问题 / 待核实）

### 13. AGENTS.md:159-161 — 72B 仍表述为"不替换主力"，实况已删除
- 原文摘录: `72B model NOT replacing主力 (degenerate on structured extraction).`
- 矛盾点: 与基准 6 冲突（72B 已删除，而非保留为候选）。HANDOFF.md:46 "72B model evaluated and rejected" 为带日期的历史记录，可保留。
- 建议改法: 改为 "72B 模型已评估、否决并于 2026-08-03 前删除（结构化抽取退化）"。

### 14. AGENTS.md:225-235 — Test Inventory 表合计 "98+"
- 原文摘录: `| **Total** | **98+** | |`
- 矛盾点: 与基准 7 冲突，但节标题已注明 (2026-08-01)，属可识别的历史快照。
- 建议改法: 表下补一行 "2026-08-03 现行: 227 passed / 13 skipped"，避免被单独引用。

### 15. HANDOFF.md:233 — 多 Agent 自动委派 "NOT verified"（2026-07-28 语境）
- 原文摘录: `OpenCode multi-agent automatic delegation has NOT been verified end-to-end as of 2026-07-28; treat as 'ready to activate', not 'verified'.`
- 矛盾点: 部分过期。显式指示的两跳委派已于 2026-07-29 验证（AGENTS.md:96-101）；中性提示自动委派仍未验证，故该句结论只对了一半。
- 建议改法: 追加一行 "2026-07-29 更新：显式指示两跳委派已验证；中性提示自动委派仍未验证"。

### 16. AGENTS.md:203 — harness 工具模型 qwen3.8-max-preview（待核实，非明确矛盾）
- 原文摘录: `Model: qwen3.8-max-preview, enable_thinking=true, timeout 120s`
- 矛盾点: 基准 1 仅覆盖 Loop A/C 的模型；qwen_harness_tools.py 是独立工具 CLI，可能仍正确使用 preview。列出以防与 Loop 模型混淆。
- 建议改法: 核实脚本现行默认模型；若未变则加一句注释"独立于 Loop A/C 模型路由"。

### 17. 三份 7 月 8 日历史文件 — 无直接矛盾，建议归档
- 涉及文件: `PROJECT_REVIEW_REPORT.md`（review 日期 2026-02-06）、`code_review_prompt.md`、`implementation_guide.md`
- 矛盾点: 未发现与 9 条基准直接冲突的陈述（仅引用单文件测试 `1 passed`、旧 Web 应用 API 面）。风险在于无日期语境地散落在根目录，可能被新 session 当作现行指南。
- 建议改法: 移入 docs/archive/ 或在文件头加"历史快照"标注（本次只读审查未执行移动）。

---

## 覆盖缺口（非陈述矛盾，属整体缺失）

### G1. ZhikunCode v1.2.1+7 在全部根目录文档中零出现
- 现象: 对 AGENTS.md、HANDOFF.md、README*.md 等全文检索 `zhikun` / `8090` 均无命中（OpenCode 相关引用仅涉及 opencode.json/opencode mcp list 配置面）。
- 风险: 基准 2（2026-08-03 升级 ZhikunCode v1.2.1+7，docker，:8090）无任何根目录文档承载，下一 session 无从得知该组件存在，基础设施排障与部署文档（docs/20、docs/21 口径）可能与实况脱节。
- 建议改法: 在 HANDOFF.md 新增 2026-08-03 快照段与 AGENTS.md GB10 节各补一条 ZhikunCode 记录（版本、docker 部署、:8090、升级日期）。

## 范围外观察（供参考，不计入矛盾清单）

- AGENTS.md:53 要求 "Use Python 3.11"，README.md:93 写 Python 3.12，实测 `venv/bin/python --version` = Python 3.12.3。AGENTS.md 该句疑似过期（不在本次 9 条基准内，未列级）。

## 结论

- 共确认矛盾 17 项 + 覆盖缺口 1 项：S1 高严重度 5 项（其中 HANDOFF.md:12-13 的 Loop C 模型与 README.md 的 15/15、164 测试为交付面最大风险）、S2 中严重度 7 项、S3 低严重度 5 项。
- 矛盾集中在三类: ① 2026-08-03 模型切换未回写旧快照段（HANDOFF/AGENTS 多处 glm-5.2、deepseek-v4-flash-0731、preview）；② 客户可见指标未随 8 月冲刺更新（README 测试数与 RAG QA）；③ VLM/72B 终态（关闭/删除）未覆盖"blocked/rejected"中间态表述。
- 修复建议统一原则: 带日期的历史快照保留原文但加"历史快照"标注，现行值集中收敛到 HANDOFF.md 顶部 2026-08-03 段与 AGENTS.md Model Routing / Scenario 1 节，其余段落以指针引用。

END-OF-REPORT
