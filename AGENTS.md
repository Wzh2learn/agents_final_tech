# Repository Guidelines

## Project Structure

`src/` uses a layered FastAPI architecture: `web/` contains routes, templates, and static assets; `biz/` owns application services; `agents/` contains the in-app LangGraph agent; `tools/` implements retrieval and document functions; `storage/` manages PostgreSQL/PGVector, memory, and files. Read-only OpenCode adapters live in `src/mcp_server/`, `src/vision_mcp_server/`, and `src/tabular_mcp_server/`. Put tests in `tests/`, operational and experiment commands in `scripts/`, model manifests in `models/`, and plans/results in `docs/`.

Read `memory/STATE.md` for the current GB10 state and immediate work, and `docs/13_M1_M2联合数据闭环计划.md` for the approved public dataset and split policy (frozen research line), before starting a new Codex CLI session.

## Current Architecture Boundary

The existing Web application and `RAGService` remain the source of truth for documents, collections, retrieval, and traceability. `opencode.json` connects the GB10 OpenAI-compatible Qwen3.6-35B-A3B service (gb10/qwen3.6-35b-a3b) to three isolated local MCP servers. The implemented surface is read-only:

- `knowledge_search`
- `knowledge_list_collections`
- `knowledge_get_source`
- `vision_ocr_extract`
- `tabular_classify`

Qwen3-14B has been service-validated on this path, and the formal read-only
20-call OpenCode/MCP stability run passed. This does not imply a service is
currently running. Formal M2 business metrics remain blocked on an
owner-approved label-to-source mapping and human annotations. Vision and
tabular protocol/synthetic chain checks have passed, but M1 OCR quality,
tabular business metrics, and full multi-agent orchestration remain unfinished.
Do not create a second vector store or bypass `RAGService` with ad hoc database
queries.

As of 2026-07-28, the M1 display workbench is **complete and verified**:
`src/biz/m1_service.py`, `src/web/routers/m1.py`, `src/web/templates/m1.html`,
`src/web/static/m1.css`, `src/web/static/m1.js`, and `tests/test_m1_service.py`
(18 tests passing on both Windows and Linux aarch64). It is a deterministic
text-rule baseline for demonstrating the M1 -> M2 handoff flow, not an
OCR/VLM result or a production API. The GB10 dev machine has pulled this code
and verified tests pass.

## GB10 Dev Machine (2026-07-28)

Codex CLI 0.145.0 is configured with Token Plan:
- Default model: `qwen3.8-max-preview` (direct, Responses API)
- Chat-only models (`glm-5.2`, `deepseek-v4-pro`) via local proxy on `:8100`
  (`scripts/responses2chat_proxy.py`)
- tmux sessions for autonomous experiment loops
- venv at `~/wzh/projects/agents_final_tech/venv` (pytest + pydantic)
- PostgreSQL/PGVector Docker container on `:15432`
- Qwen3.6-35B-A3B llama-server on `:8004` (64K context, MoE 3B active)

Use `--dangerously-bypass-approvals-and-sandbox` for Codex CLI exec on GB10
(bubblewrap user namespaces unavailable).

## Development Commands

Use Python 3.12 and install `requirements.txt`. On Windows:

```powershell
.\venv\Scripts\python.exe scripts\verify_config.py
.\venv\Scripts\python.exe src\main.py -m http -p 5000
$env:PYTHONPATH="src"; .\venv\Scripts\python.exe -m pytest tests -v
```

On the GB10 Linux machine, provide the required local environment variables
without recording their values, then initialize and test the MCP path with:

```bash
python scripts/init_knowledge_backend.py
python scripts/smoke_test_mcp_server.py
opencode mcp list
```

## Style and Testing

Follow PEP 8, four-space indentation, type annotations, and `snake_case`/`PascalCase` naming. Keep route handlers thin and business logic in `src/biz/`. Tests use `pytest`; name files `test_*.py` and add focused coverage for service, retrieval, MCP contract, and API changes. Commands requiring live PostgreSQL, GB10 models, or cloud credentials must be identified as integration tests.

## Changes and Security

Use short, imperative commits scoped to one concern. PRs should state behavior, verification commands, configuration impact, and screenshots for UI changes. Never commit `.env`, credentials, server addresses, model weights, generated datasets, logs, or local databases. Preserve the read-only MCP boundary unless a reviewed task explicitly introduces a write operation.
## Current Work Mainline & Frozen Items (2026-07-28, user-confirmed)

These are boundaries the next agent must respect or it will redo frozen work or
mis-report status:

- **Mainline / north star = client counterparty-statement M1** (table parse +
  header synonym mapping + arithmetic reconciliation + statement workbench +
  OpenCode skill multi-agent). New work and remote Codex loops prioritize this.
- **TAT-DQA experiments are FROZEN** (paused, not deleted; numbers kept as a
  research baseline). Do NOT open new TAT-DQA retrieval / ablation / llm-batch
  loops or pile on volume. Resume the general methodology only in a later
  research phase, after the client-facing M1 is solid.
- The integrated G retrieval strategy (top_k=10 + bge-reranker-v2-m3 -> top-5,
  TAT-DQA EM 0.28) is the live M2 retrieval default, but it is orthogonal to the
  client M1; report the two separately, never conflate.
- **Multi-agent automatic delegation is NOT verified end-to-end.** Config +
  samples + engine are present (opencode.json agents/permissions), but no
  OpenCode auto-delegation run has completed; docs and reports must say
  "ready to activate", never "verified".
  - 2026-07-29 update: with the model on 64K context, **explicitly-instructed
    two-hop delegation IS verified** (`coordinator -> m1-extraction ->
    evidence-verifier`, exit 0 / 58s; verifier verdict matches the deterministic
    parser ground truth). See docs/experiments/2026-07-29_m1_verify_and_mcp.md.
    This does NOT cover neutral-prompt auto-delegation, which stays unverified.
- Real client samples live in `~/wzh/m1_samples/` on GB10 (outside the repo,
  never committed; reports desensitized). `scripts/loop_*.md` are consumed
  remote-loop task prompts, kept as audit archive.
- Remote Codex CLI exec needs `--dangerously-bypass-approvals-and-sandbox`
  (bubblewrap user namespaces unavailable on GB10).


## Qoder CLI Recon (2026-07-29, recon only, no switch)

Qoder CLI 1.1.7 isolated-installed at `~/.local/qoder` on GB10. Protocol analysis
confirms full OpenAI chat-completions compatibility with llama-server :8004 (direct,
no proxy needed) and responses2chat :8100 (forward path). Config via
`~/.qoder/settings.json` providers field (reverse-engineered from bundle).

**Hard gate**: Qoder requires account auth (PAT or browser OAuth) even for external
providers. Phase 2 connectivity test BLOCKED-auth. User must register + provide PAT
before any Qoder loop can execute.

Coexistence with Codex CLI: zero conflict (separate binaries, config dirs, auth).
All existing assets (AGENTS.md, SKILL.md, loop prompts, supervisors, proxy) are
tool-agnostic and reusable under Qoder with only the invocation shell changed
(`codex exec` -> `qodercli -p --dangerously-skip-permissions`).

Migration decision: pending user PAT + Phase 2实测. See docs/16 and
docs/experiments/2026-07-29_qoder_recon.md for full report.

## Codex CLI model switching on GB10 (2026-07-30)

Codex CLI on GB10 reads ~/.codex/config.toml with two Token Plan providers:
- Token_Plan (direct Responses API) -> qwen3.8-max-preview (default).
- Token_Plan_Chat (local responses2chat proxy :8100, Responses->Chat) -> glm-5.2, deepseek-v4-pro.
  glm/deepseek only speak Chat Completions on Qwen Token Plan; the proxy translates.
Switch helper: bash scripts/switch_codex_model.sh [qwen|glm|deepseek]
For glm/deepseek it also ensures the :8100 proxy is up. Verified 2026-07-30:
codex exec end-to-end with glm-5.2 via the proxy returns a valid response.
Manual equivalent (edit the two top-level lines of ~/.codex/config.toml):
  model = "glm-5.2"                  # or qwen3.8-max-preview / deepseek-v4-pro
  model_provider = "Token_Plan_Chat" # or Token_Plan for qwen
then ensure the proxy is running for the *_Chat provider:
  bash ~/start_proxy.sh   # fallback: nohup python3 ~/.local/bin/responses2chat_proxy.py &

## M1 Parser Terminal State (2026-07-31, 8h autonomous loop)

The M1 counterparty-statement parser (`scripts/m1_statement_parser.py`) achieved
**100% parse rate** on all 5 real client samples after 8 rounds of Loop A:

| Capability | Status |
|------------|--------|
| Text statement parse (TXT/XLSX) | 100% (rule mapping) |
| Text-layer PDF parse | 100% (grid + borderless fallback) |
| Image-only PDF/DOCX parse | 100% (OCR fallback, vision-8004 parallel) |
| LLM fallback (unmapped cols) | Connected, jiaxing unmapped 0 |
| Silent mismatch detection | Fixed, disposition field added |
| Market-value reconciliation | All PASS |
| RAG ingest + QA | 3/3 correct (PGVector m1_parsed_statements) |
| Reconcile disposition | real_pass / skipped / fail |
| OCR parallelization | 200s -> 74s (2.7x) |

PaddleOCR-VL remains broken (transformers version incompatibility); vision-8004
fallback handles all OCR needs. 72B model evaluated, rejected and deleted (degenerate on structured extraction; files removed, 47GB freed).

## Graph Engineering Running Mode (2026-07-31)

Four-layer loop architecture per `docs/17_Graph_Engineering_多层Loop设计.md`:

| Layer | Role | Tool | Status |
|-------|------|------|--------|
| Loop D | Strategic oversight | Local Codex desktop | Active |
| Loop A | Execution | Remote Codex CLI via tmux | Standby (dispatched per task) |
| Loop B | Independent verification | graph-loop-b tmux daemon, 30min cycle | Running |
| Loop C | Quality audit | Claude Code + qwen3.8-max | 12h freq (after 3x ACCEPTED) |

**AoE session management note**: AoE `send` does not work with `codex exec`
(one-shot binary; respawn re-runs original command). Loop A tasks are dispatched
via tmux direct launch:
```bash
tmux new-session -d -s loop-a-taskN "cd $PROJ && source ~/.bashrc && \
  cat scripts/graph/loop_a_exec_constraints.md /tmp/task.md | \
  codex exec --dangerously-bypass-approvals-and-sandbox 2>&1 | \
  tee -a logs/graph/loop_a.log"
```

Frozen nodes (Loop B verifies every 30min): `tests/test_m1_service.py`,
`~/wzh/m1_samples/m1_table_schema.json`, `scripts/graph/frozen_hashes.txt`.
L5 git pre-commit hook blocks commits touching frozen paths.

## M2 RAG QA Endpoint (2026-07-31)

The M2 RAG QA endpoint is live at :5050/api/m2/ask:
- POST { question: ..., top_k: 3} -> {answer: ..., sources: [...], model: ...}
- Uses PGVector collection m1_parsed_statements (137 embeddings, scenario1 included)
- Embedding + generation via :8004 (Qwen3.6-35B-A3B)
- QA test suite: scripts/m1_rag_qa.py (15 queries, 14/15 = 93% after 2026-08-02 collection expansion; gate 80%)
- UI panel integrated into :5050/m1 page

## Qwen Harness Tools (2026-07-31)

scripts/qwen_harness_tools.py provides CLI access to Qwen platform tools:
- web_search: internet search via Responses API
- code_interpreter: cloud sandbox code execution
- web_extractor: web page content extraction (requires web_search in same request)
- Model: qwen3.8-max-preview, enable_thinking=true, timeout 120s (independent of Loop A/C routing; preview supports all 5 harness tools)
- Used by Loop A (execution) and Loop C (audit) for external verification

## Graph Engineering Loop Status (2026-07-31)

- Loop B: daemon running (30min cycle, all PASS)
- Loop C: 12h frequency (4x consecutive ACCEPTED), Claude Code + qwen3.8-max (switched from glm-5.2 on 2026-08-03)
- Loop A: standby (tmux direct launch per task)
- Loop D: strategic layer (user + main thread)
- Frozen nodes: tests/test_m1_service.py, ~/wzh/m1_samples/, scripts/graph/frozen_hashes.txt
- xinhua 0/11 schema hit: CLOSED (operational doc, not financial statement)

## 8h Delivery Loop (2026-08-01)

System upgraded from  runnable to deliverable:
- docs/19: Client-facing capability document (business perspective)
- docs/20: Deployment guide with Docker Compose
- Multi-turn M2 conversation (session_id + chat UI + context injection)
- 98+ tests (18 frozen + 17 edge + 20 multiturn + 53 unit)
- Demo screenshot sequence: docs/experiments/2026-08-01_demo_sequence/ (11 images)
- Docker: docker-compose.yml + Dockerfile + scripts/run.sh

### Test Inventory (2026-08-01)
| File | Count | Status |
|------|-------|--------|
| test_m1_service.py (frozen) | 18 | PASS |
| test_m1_edge_cases.py | 17 | PASS |
| test_m2_multiturn.py | 20 | PASS |
| test_m1_parser.py | ~15 | PASS |
| test_m1_reconcile.py | ~12 | PASS |
| test_m1_ocr_fallback.py | ~8 | PASS |
| test_m2_rag.py | ~8 | PASS |
| **Total** | **98+** | |

2026-08-04 current: 227 passed / 13 skipped (table above is the 2026-08-01 snapshot). 2026-08-07 current: 266 passed / 13 skipped.

## 8h Production Sprint (2026-08-01)

System upgraded from "deliverable" to "production-ready":
- Phase 1: Cross-document comparison (4 APIs + NL routing)
- Phase 2: Schema self-service config (CRUD + UI modal + admin token)
- Phase 3: Auth + persistence + metrics + logging + deploy files
- Phase 4: Edge case hardening (10 fixtures) + UI polish
- Tests: 225 passed (was 164), 13 skipped, 0 failed
- Ground truth: independence check found + fixed circular reasoning in boshi

### New Endpoints (2026-08-01)
| Endpoint | Method | Purpose |
|----------|--------|---------|
| /api/m2/products | GET | Product list |
| /api/m2/products/{name}/timeline | GET | Date snapshots |
| /api/m2/compare | POST | Cross-date diff |
| /api/m2/compare/positions | POST | Position ranking |
| /api/m1/schema | GET/PUT | Schema CRUD |
| /api/m1/schema/tables | POST | Add table |
| /api/m1/schema/tables/{n}/fields | POST/DELETE | Field CRUD |
| /api/metrics | GET | Prometheus metrics |

## Scenario 1 Gap Resolution (2026-08-02)

All 3 known gaps solved:
- Gap 1 (NCAMC vertical layout): `_coordinate_table_reconstruction()` in parser
  Uses pymupdf bbox coordinates to rebuild tables from vertical text layout.
  Integrated as fallback: find_tables -> text_lines -> coordinates -> OCR.
- Gap 2 (OCR pure text): Enhanced OCR prompt with markdown table format example.
 华泰 0->1 table, TraFax 0->3 tables.
- Gap 3 (email body): HTML body extraction via extract_msg.htmlBody + BeautifulSoup.
  3 email-body .msg files: 0 -> 9 tables.

Schema: +23 HTML-specific synonyms (基金市值, 基金份额, 份额净值, etc.)
Parser: +3 new functions/strategies (coordinate reconstruction, VLM table, single-space loose)
VLM: scripts/vlm_server_8007.py ready but BLOCKED (Triton ARM64 JIT compilation)

### Model Routing (updated 2026-08-07)
- Codex CLI (Loop A): deepseek-v4-flash-0731 via Token_Plan_Chat (:8100 responses2chat proxy v3.2; since 2026-08-06)
  - Boundary: flash = code execution / bounded tasks only; long-read / doc-study sub-agent tasks use qwen3.8-max or the main thread (memory/DECISIONS.md 2026-08-06/08-07, rollback commands included)
- Claude Code (Loop C): qwen3.8-max via Anthropic-compatible endpoint, all slots
  (tool_use verified 2026-08-03; claude -p dispatch needs --dangerously-skip-permissions, 2026-08-06 lesson)
- Loop D sub-agents: deepseek-v4-flash-0731 default; integration review / multimodal stay qwen3.8-max

### ZhikunCode (GB10)
- v1.2.1+7 (upgraded 2026-08-03), docker container `zhikuncode`, port :8090
- Self-hosted Multi-Agent platform; source-built via docker compose (~/wzh/tools/zhikuncode)
- :8004: Qwen3.6-35B-A3B + mmproj (generation + OCR + embedding)
- :8005: RETIRED (Qwen3-14B 退位 2026-08-17; Loop B 断言 down)
- :8007: free probe port (VLM/Triton 线已关闭)
- :8006/:8008: Qwen3.8-27B-FP8 (vLLM GB10 镜像) — M2 agent 验证链 / judge / 深度问答; thinking 经 reasoning_effort low/medium/xhigh（生产 m2-qa thinking 现为 OFF, proxy 默认; judge xhigh）
- :4096: opencode 侧车 (M2 agent 路交付链; 启动器 scripts/sidecar_launch.sh)

### RAG Collection
137 embeddings (was 88). Includes scenario1 HTML + NCAMC coordinate tables.
RAG QA: eval 基线定稿 2026-08-09（08-22 生产复验: 确定性 16/16 + NF 0/9 + judge 四维 5.0, 经 :5050） = 确定性 16/16 + AI judge 四维全 5.0（15/15 为一轮口径, OCR meta-query fixed 08-05, 生产复验 08-07/08-09）; pytest 379 passed / 13 skipped (08-22); scenario1 回归门禁 15/15（华泰 100%, 嘉合 93.8%）。

## Skill 武库注册表 (Phase 0, 2026-08-03)

**Source of truth**: 仓库 `skills/` 目录；`scripts/graph/sync_skills.sh` 幂等分发到各 harness。

**三层分发架构**:
- 仓库 `skills/` (版本化 source of truth) → sync_skills.sh → 各 harness skill 目录
- Loop A (Codex CLI): `~/.codex/skills/` — 执行层武库 (+ 既有 neat-freak)
- Loop C (Claude Code): `~/.claude/skills/` — 审计层武库
- Loop B 为纯 bash 验证层, 无 AI, 不配 skill; Loop D (指挥层) 使用本地全套 skill

**配属注册表**:

| Loop | Harness | skill | 用途 |
|---|---|---|---|
| A | Codex CLI | systematic-debugging | bug 卡住时根因追溯 |
| A | Codex CLI | executing-plans | 多步计划按 checkpoint 执行 |
| A | Codex CLI | subagent-driven-development | 独立子任务并行分发 |
| A | Codex CLI | verification-before-completion | 交付前证据验证（**DEPRECATED 2026-08-25: 被 verify-before-done 取代**, 目录保留, 治理规则 4） ── **日期口径已核定（09-12 批 #3, 只增不改; 上方原文逐字保留作轨迹）**: 本行的 **2026-08-25 是正确的弃用日**, **不改**; 弃用件本体 `skills/verification-before-completion/SKILL.md:6` 所写的 **2026-08-26 是「弃用横幅的写入日」而非「弃用生效日」**。**git 历史为证** = `AGENTS.md` 的该 DEPRECATED 标注由 **`735813b`** 引入（commit 日期 **2026-08-25**, message 明写「AGENTS.md 注册表 (verification-before-completion 标 DEPRECATED 被 verify-before-done 取代)」）; 而 `SKILL.md:6` 的横幅由 **`0cbced5`** 引入（commit 日期 **08-26**, message 明写「verification-before-completion DEPRECATED **双注记**」）⇒ **注册表先标（08-25）, 本体横幅次日补写（08-26）**, 故 1 天之差属**补写日与生效日之别, 不是转录误差**。**⇒ 与开工卡建议相反, 按证据改判**: 开工卡建议「以 SKILL.md 本体为准, 把 AGENTS.md:311 更正为转录误差」, 并明示「若核 git 历史后发现相反证据（例如弃用标记确于 08-25 落而 SKILL.md 是 08-26 补写）, 按证据改判并在汇报说明, 不要照抄本条建议」——**核出的正是该相反证据**, 故本行日期**不动**, 权威口径 = **弃用生效日 2026-08-25（注册表）**。**为何不改 `SKILL.md:6` 本体**: 该件在 `scripts/graph/sync_skills.sh` 的 `A_SKILLS` 分发列表内, 改仓库副本而不改两端安装区会使 `sync_skills.sh --check` 的 `diff -rq` 内容比对报 **DRIFT**, 而 `docs_lint [4]` 的漂移是 **FAIL 级**（批 #1 的 BOM 修复已实证过这条链）; 而本批 §四.6 明令**不动 `~/.codex` 与 `~/.claude` 任何文件** ⇒ 无法同步安装区 ⇒ **改本体必然弄红权威 lint 门**。故本批只在**不被分发的** `AGENTS.md` 与派发路径件上更正, 并把「SKILL.md:6 横幅日期口径」**留给 A19 脚本级批次**（那一批会跑原子分发, 可安全改 skill 文件并同步两端）。 |
| A | Codex CLI | m2-rag-playbook | M2 RAG 问答失败模式契约（m2-qa agent 经 skill 工具加载）|
| C | Claude Code | review-codebase | 全库体检 |
| C | Claude Code | differential-review | 增量 diff 审查 |
| C | Claude Code | spec-to-code-compliance | 文档-代码一致性 |
| C | Claude Code | requesting-code-review | 结构化审查请求 |
| C | Claude Code | receiving-code-review | 反馈的技术性验证 |
| C | Claude Code | security-best-practices | 安全专项 (按需) |
| C | Claude Code | m2-rag-playbook | 审计 M2 问答行为的对照基线 |
| A | Codex CLI | agent-prompt-contracts | 编写/修改 agent prompt 与输出契约时必读 |
| C | Claude Code | agent-prompt-contracts | 审计 prompt 类改动的契约遵从基线 |
| A | Codex CLI | m1-gap-triage | M1 解析失败分诊：0 表/高 unmapped → 读原文诊断 → 补 synonyms → 重跑 → 报 delta（嘉合 playbook） |
| A | Codex CLI | graph-loop-rules | Graph Loop 红线与运行约束（冻结节点/生产后端/API key/72B），OpenCode agent 通用 |
| A | Codex CLI | jinrong-docs-sync | 文档四层结构治理 + INDEX.md 单一入口维护 (Phase 4 自定义, 2026-08-04) |
| C | Claude Code | jinrong-docs-sync | 审计后文档时效/一致性复核的同套规则基线 |
| A | Codex CLI | research-writing-skill | 科研线 (docs/30): 论文正文/摘要/回复审稿人写作与润色, 中文优先 |
| A | Codex CLI | office-academic-skill | 科研线 (docs/30): 学术 Word/PPT 生成 (文献报告/组会/答辩 PPT) |
| A | Codex CLI | scientific-toolkit-skill | 科研线 (docs/30): 科研计算/统计/配图 (含 paper-lookup 与 citation-management 子技能) |
| A | Codex CLI | verify-before-done | 完成申报前双重验收: 11 条"假完成"捷径清单 + 本轮实跑完成门（取代 verification-before-completion; 源 skills-loop-engineering@7ffbe44） |
| C | Claude Code | verify-before-done | 审计层验收完成申报的同套门 |
| C | Claude Code | self-eval-bias | 同上下文自评偏倚检测（侧线抽验机制的理论依据） |
| A | Codex CLI | shift-notes | 会话交接笔记格式; handoff 与 git 冲突时信 git |
| A | Codex CLI | context-budget | 上下文预算纪律（长会话/大文件/精度塌方; 与 L2 context 瘦身杠杆同源） |
| A | Codex CLI | tool-restraint | 工具克制: 过多 MCP/工具 = 认知负载悬崖（对应 sidecar 元数据装载病灶） |
| A | Codex CLI | spec-first | 行动前写 goal spec 到盘（目标/完成条件/禁触/停止条件） |
| A | Codex CLI | sprint-contract | 写码前定义 done（谓词化验收 + 运行路径 + 范围外清单） |
| A | Codex CLI | broken-window-check | 冒烟已声明完成的功能（配合 shift-notes） |
| A | Codex CLI | eval-harness | eval 骨架（grader 隔离/judge 可见 prompt/基线入 git） |
| A | Codex CLI | evaluator-calibration | LLM 评审校准: rubric 锚定/禁读生成者推理/引用式判据/定期重提示（08-25 judge 事故对症） |
| C | Claude Code | evaluator-calibration | 审计层评估校准基线 |
| C | Claude Code | repo-audit | 对抗式治理审计 + hook 升级判断 + 项目结构梳理 |
| C | Claude Code | readme-audit | 索引/文档入口审计（INDEX 治理） |
| A | Codex CLI | experiment-autopsy | 实验尸检四步法（解剖/诊断/交叉验证/行动）+ tradeoff 前沿共线检验 |
| A | Codex CLI | decision-record | ADR 式决策记录（对应 docs/32 DECISIONS） |
| A | Codex CLI | paper-polish-and-audit | 投稿前论文审计清单（科研线, 论文章 4 前置） |
| A | Codex CLI | recsys-toolkit | RecSys career/defense 双模式工具包（科研线） |
| A | Codex CLI | paper-review-check | 科研线: 投稿前攻击面自查/对抗审查（每章草稿过一轮; 审稿人视角五问） |
| C | Claude Code | paper-review-check | 审计层论文草稿审查协议（Loop C 审计范围扩至论文, 2026-08-29） |
| A | Codex CLI | paper-writing-zh | 科研线: 中英文学术写作纪律（claims↔证据对齐, 禁 overclaim, limitations 不藏） |
| A | Codex CLI | algorithm-description | 科研线: 代码→论文算法描述（伪代码/复杂度/变量对位, G(τ,ε) 方法节用） |
| A | Codex CLI | neat-freak | 治理线: 知识收口/声明-实况对账/漂移清场（触发: /neat、洁癖、收尾同步意图） |
| A | Codex CLI | code-cleanup-helper | 治理线: 技术债四扫 + repo audit（Mode A/B, release 一致性/交叉引用） |
| A | Codex CLI | skill-doctor | 治理线: skill metadata 与 doc-link 体检（每次 neat 收尾跑, 治理规则 2） |
| A | Codex CLI | skill-map | 治理线: skill 安装/交叉引用地图（依赖发现与重复检测） |
| A | Codex CLI | agent-rules | 通用: AGENTS.md/agent 规则文件编写规范 |
| A | Codex CLI | codebase-map | 通用: 代码库结构总览与依赖图 |
| A | Codex CLI | dispatching-parallel-agents | 通用: 独立子任务并行分发模式 |
| A | Codex CLI | writing-plans | 通用: 多步任务实施计划编写 |
| A | Codex CLI | jupyter-notebook | 通用: notebook 脚手架与实验记录 |
| A | Codex CLI | pdf | 通用: PDF 读取/生成/处理工具链 |
| A | Codex CLI | playwright | 通用: 浏览器自动化（终端驱动, walkthrough/录制复用） |
| A | Codex CLI | playwright-interactive | 通用: 持久浏览器/Electron 交互式调试 |
| A | Codex CLI | security-threat-model | 通用: 仓库威胁建模（显式触发） |
| A | Codex CLI | cloudflare-deploy | 通用: Cloudflare 部署（未启用, 备用） |
| A | Codex CLI | vercel-deploy | 通用: Vercel 部署（未启用, 备用） |
| A | Codex CLI | figma | 通用: Figma 上下文获取/设计转代码（未启用, 备用） |
| A | Codex CLI | figma-use | 通用: Figma 写操作前置（未启用, 备用） |
| A | Codex CLI | figma-implement-design | 通用: 设计稿 1:1 实现（未启用, 备用） |
| A | Codex CLI | figma-generate-design | 通用: 代码→Figma 画布（未启用, 备用） |
| A | Codex CLI | figma-generate-library | 通用: 设计系统对齐（未启用, 备用） |
| A | Codex CLI | figma-code-connect-components | 通用: Code Connect 组件映射（未启用, 备用） |
| A | Codex CLI | skills-best-practices | 治理线: 自定义 skill 规范（治理规则 3 依据） |
| A | Codex CLI | experiment-analysis | Standardized analysis framework for ML experiment results. Follows a 5-step process (dat |
| A | Codex CLI | experiment-observer | 自动检查实验日志，提取关键指标（HR/NDCG/sHR/proto cos/ort_loss/group 诊断/τ 退火）、趋势分析和健康度判断。当用户需要分析实验结果、定时  |
| A | Codex CLI | research-driven-design | 从论文出发的训练策略设计引擎。 核心流程：论文机制提取 → 核心原理归纳 → 框架映射 → 适配性分析 → 训练信号设计 → 实验验证方案。 参数耦合适配分析（Step 4.5 |
| A | Codex CLI | offline-eval-playbook | Offline evaluation judgment playbook: multi-slice evaluation (full/covered/intersection) |
| A | Codex CLI | code-pathology | 代码全路径病理检查：沿数据流从输入到输出逐层审查，找确定性 Bug 和高价值优化方向。 核心理念：不做泛泛 review，而是沿着一条具体的训练路径（如主特征路径 full-m |
| A | Codex CLI | organize-logs | Organize experiment logs into a structured, searchable directory with per-dataset groupi |
| A | Codex CLI | train-monitor | Monitor running training jobs — check GPU utilization, training progress, loss curves, a |
| A | Codex CLI | gpu-env | Activate GPU training environment, check GPU/driver status, verify torch/accelerate/deep |
| A | Codex CLI | data-sync | Download data or model checkpoints from object storage to local training server. Checks  |
| A | Codex CLI | write-failing-test-first | Before fixing any bug, write a test that reproduces it and watch it fail. Use for every  |
| A | Codex CLI | flaky-hunter | Diagnose and fix tests that pass sometimes and fail other times. Use when CI is red inte |
| A | Codex CLI | bisect-regression | Find the exact commit that introduced a bug. Use when something worked before and broke, |
| A | Codex CLI | coverage-gaps | Find the untested code paths that actually matter, not just the coverage percentage. Use |
| A | Codex CLI | contract-test | Test the boundary between two systems by the contract, not the implementation. Use for A |
| A | Codex CLI | kill-dead-code | Find and remove unreachable/unused code safely. Use during cleanup or before a refactor. |
| A | Codex CLI | reduce-nesting | Flatten deeply nested conditionals into readable, early-return code. Use on any function |
| A | Codex CLI | simplify | Reduce a change to the minimum that solves the problem. Use when code is over-engineered |
| A | Codex CLI | revert-surgical | Undo a bad change without nuking unrelated work. Use when a specific commit or change br |
| A | Codex CLI | rebase-safely | Rebase, squash, or rewrite history without losing work or breaking shared branches. Use  |
| A | Codex CLI | clean-commits | Turn messy WIP into clean, atomic commits with messages that explain why. Use before ope |
| A | Codex CLI | changelog-from-diff | Turn a set of commits or a diff into a clean, user-facing changelog entry. Use before a  |
| A | Codex CLI | pr-from-diff | Write a PR description a reviewer can approve fast. Use when opening any pull request. |
| A | Codex CLI | dependency-audit | Decide whether to add, keep, or remove a dependency. Use before adding any package. |
| A | Codex CLI | authz-check | Verify that an endpoint checks ownership, not just authentication. Use on any handler th |
| A | Codex CLI | input-validation | Validate and constrain untrusted input at the boundary. Use on any handler that accepts  |
| A | Codex CLI | secret-scan | Catch hardcoded secrets, keys, and tokens before they get committed. Use before any comm |
| A | Codex CLI | migration-writer | Write safe, reversible database migrations for this repo's conventions. Use for any sche |
| A | Codex CLI | schema-diff | Compare two schema states and surface the risky changes. Use before applying migrations  |
| A | Codex CLI | design-system | Make frontend output look intentional, not AI-generated. Use for any UI work — component |
| A | Codex CLI | a11y-pass | Catch the accessibility failures that ship in almost every AI-built UI. Use after buildi |
| A | Codex CLI | loading-empty-error-states | Design the three states every data UI forgets. Use for any component that fetches or lis |
| A | Codex CLI | init-script-contract | Author idempotent init.sh under 120s plus sibling test.sh, stop.sh, reset.sh, serve.sh w |
| A | Codex CLI | progress-reading-protocol | Run the fixed 6-step session-opening sequence — pwd, read progress, git log, count remai |
| A | Codex CLI | harness-stripping | Systematically remove one harness component at a time and measure impact, killing scaffo |
| A | Codex CLI | structured-output | Get JSON out of the model reliably. Prefer tool_use with a schema over prompted-JSON, va |
| A | Codex CLI | prompt-caching | Cache the parts of the prompt that don't change so a long-running loop stops paying full |
| A | Codex CLI | pdf-ingestion | Get a PDF into the model without blowing the context window or losing structure. Native  |
| A | Codex CLI | planner-spec-expand | Expand a 1-4 sentence product brief into a full spec with a design language, acceptance  |
| A | Codex CLI | skill-merger | "分析并合并功能重叠的 Skill。当用户觉得 skill 太多太杂、想整理/精简/瘦身 skill 库、发现多个 skill 职责重复、说「合并重复的 skill」「帮我整理 |
| A | Codex CLI | skill-hook-trigger | "用 Hook 机制为 Skill 加确定性触发提示。当用户抱怨「skill 老是不触发/该用的时候没用上」、想「用 hook 保证 skill 触发」「给 skill 加触发 |
| A | Codex CLI | socrates | "Socratic learning coach for any technical paper or complex topic. Use when the user say |
| A | Codex CLI | dream-engine | 认知梦境引擎。模拟人类做梦过程，从用户的研究笔记中发现远距离联想，产出研究 idea。 触发词：做梦、联想、灵感、论文idea、研究方向、记忆整理、创意发散。 示例：帮我做个梦 |
| C | Claude Code | audit-cycle | Standard audit cycle distilled from five real audits run in one week (external expert re |
| C | Claude Code | owasp-review | Security-review a diff against the OWASP Top 10. Use before merging anything that touche |
| C | Claude Code | sql-review | Review SQL and ORM queries for correctness, safety, and performance before they ship. |
| C | Claude Code | feature-list-json | Enumerate every end-to-end feature as strict JSON entries with passes:false, editable-pa |
| C | Claude Code | subagent-fanout | Parallelize independent sub-jobs across fresh-context subagents instead of one bloated c |
| C | Claude Code | using-loopkit | Use when starting any conversation in a loopkit-enabled project - establishes how to fin |
| A | Codex CLI | exp-lifecycle | 实验生命周期五阶段闭环编排器（判读→设计→工程→审计→治理, 带反馈环; 编排层, 各阶段复用域内既有 skill） |

**治理规则**:
1. 仅 Loop D 可安装新 skill: 搜索 → 克隆审计 → 安装 → 注册本表与 skills/ → sync_skills.sh 分发。
2. skill-doctor / skill-map 定期体检 (每次 neat 收尾时), 核对 metadata 与交叉引用一致性。
3. 自定义 skill 按 skills-best-practices 规范放仓库 skills/ (SKILL.md frontmatter + 附属文件), 不放个人目录。
4. 弃用只标记不删除: 注册表标 DEPRECATED 并在 SKILL.md 头部注明, 目录保留审计痕迹。
5. 修复失败的 prompt 改动必须同 commit 在 skills/agent-prompt-contracts/ 补录/更新对应契约 (失败模式 → 对策 → 验证方式 + 证据链接); 无契约补录的 prompt 修复合并前须说明理由。
6. 其余 49 件 skills-loop-engineering 库存（code-quality/security/git-ops/frontend/data/dream-engine 等）不入仓, 留源仓库按需取; 引入需走本表流程。

## 机械强制层 (pre-commit hook 链, 2026-08-25)

仓库 `scripts/graph/hooks/` 是机械强制层; `.git/hooks/pre-commit` 为链式入口
(安装器 `scripts/graph/hooks/install_hooks.sh`, 本地与 GB10 通用):

1. `pre-commit` — L5 冻结节点守卫 (2026-08-06 既有, 链首不可移除; 覆盖仅 --no-verify, Loop D 专用)
2. `cjk-byte-check.precommit.sh` — staged .md 的 U+FFFD 乱码扫描（源仓库 3 次实证; 本项目 CRLF/编码麻烦同族）
3. `index-guard.precommit.sh` — 新增 scripts/**/*.py|sh 必须已索引于 docs/INDEX.md（源仓库 7 次"打地鼠"实证）
4. `large-file-guard.precommit.sh` — >5MB / 权重/视频/数据类型禁入库（对应"视频文件不入 git"既有纪律）
5. `summary-recompute-guard.precommit.sh` — 摘要收据重读复算守卫（2026-08-30; Hook Escalation 第 3 次触发: "声明摘要 ≠ 存储工件"三连实证 f1bf00b/36ab25f/d4e749a → 上机械强制; 核心 `scripts/graph/hooks/summary_recompute_guard.py`: 收据块 gen/check, sha raw+LF 双口径, 数值容差 5e-5, 失配阻断; python 缺失降级警告放行）

**Hook Escalation Ladder**（源 docs/governance/reference/HOOK_AUTHORING_GUIDE.md）:
同一错误第 1 次 = 记教训; 第 2 次 = 入教训台账; 第 3 次及以上 = 上机械强制。
编写标准 (何时写/何时不写/正反例测试/降级原则 = 环境异常警告放行不无声 fail-open) 同文档。
移植自 git@github.com:Wzh2learn/skills-loop-engineering.git @ 7ffbe44 (2026-08-25, 用户授权)。

### 守卫验证与台账证据纪律（2026-09-12 立法, 决策 31 批; 三条均来自 RW-1 / RW-2 / RW-4 三批实测事故）

**选点理由**: 落在本节（机械强制层）而非 `templates/task_card_template.md §8`。三条红线的约束对象是
**守卫的操作者与复验者**（主线程 / 侧线 / Loop A 都适用）, 而 `AGENTS.md` 是每个 agent 会话起始即读的
**唯一全局规则件**; 模板 §8 只在**拟任务卡**时被读到, 且其既有内容是「执行-报告阶段分离 / 检查点持久化 /
usage 记账」这类**分析工作**纪律, 把守卫验证纪律放进去会互相稀释、且拟卡人看不到执行期的事故教训。
第 3 条同时约束台账写作, 但其**成因**是守卫的标记匹配, 故三条作为一组留在本节最易被一起读到。

1. **凡断言「某守卫未生效 / 已生效」, 必须同时记下当次命令的环境变量前置**（至少 `PYTHONUTF8` /
   `PYTHONIOENCODING` / `LC_ALL` / `LANG`）。理由 = RW-2 的失效是「**按环境变量偶然生效**」的:
   同一台机器、同一个钩子、同一份文件, 设 `PYTHONUTF8=1` 时守卫真跑并拦下提交, 不设时守卫静默不跑并放行。
   不记环境变量, 「守卫拦住了」与「守卫根本没跑」在事后不可区分（本仓已因此产生过一次错误的历史归因,
   见 `memory/THREADS.md` 的 `#BATCH1-BLOCK-ATTRIBUTION-CORRECTED` 与其结案条）。
2. **反例结果必须同时记 `rc` 与守卫是否出声**（`guard_lines_emitted`）。只记 rc 不足以判定:
   「rc=1 因为被拦」与「rc=1 因为 harness 自己坏了 / 守卫崩溃 / 守卫根本没跑」在 rc 上完全同形。
   本仓已三次踩到 = 侧线 SC-1（稀疏检出锥外 `git add` 静默失效致 4 个假 PASS）、主线程 RW-4
   （CJK 仓库路径致守卫崩溃, 四例全 rc=1 的假 BLOCKED）、以及 `cmd | tail; echo $?` 取到管道下游 rc
   的同族口径错。**配套硬要求**: 任何反例集**必须先跑正例对照并确认其 rc=0 且守卫出声**,
   正例不过则整批结果判 **INVALID**（结果无意义, 不等于通过）。
3. **凡写关于标记 / 正则 / 哨兵串的台账, 写完必须机械扫一遍自己有没有把哨兵串写进去。**
   本仓已因此堵了两批台账: `b52675f` 在 `memory/THREADS.md` 里逐字写出收据块起始标记以说明「真块合计 0」,
   使该文件此后无法提交; 批 #2 写 `#LEDGER-COMMIT-BLOCKED…` 条时又逐字写出两次（opener 计数 1→3）。
   **描述一个由字面文本触发的缺陷, 这件事本身就会触发该缺陷。** 指代哨兵串一律用占位（如「〔起始标记〕」）
   或拼接写法; **每次编辑 `memory/THREADS.md` 后须跑一次 opener 计数作为提交前自查**。

## 记忆系统协议 (Phase 5 L1, 2026-08-04)

仓库 `memory/` 是蒸馏记忆层；`logs/graph/dispatch_log.md` 是原始事件流。两轨并行，不互替。

**文件结构**:
- `memory/CORE.md` — 永久事实（<100 行，始终加载）：系统拓扑（端口/服务/模型路由）、目录约定、冻结红线、分发通道命令。
- `memory/DECISIONS.md` — 只追加决策日志（ADR 风格）：日期 + 决策 + 理由，不删改。
- `memory/STATE.md` — 当前快照（覆写式）：各 Loop 状态、进行中任务、下一步、阻塞项。
- `memory/THREADS.md` — 未决线索：blocked_questions 蒸馏 + 甲方待确认项。
- `memory/archive/` — 快照式归档（`STATE_<date>_<suffix>.md`，按日期命名）+ 滚动式历史件 `THREADS_history.md`（已结案条目轨迹；常规会话不读）。

**单一信源规则**: 现役台账唯一存放于 `memory/THREADS.md`；**已结案的历史轨迹在 `memory/archive/THREADS_history.md`（滚动件，只增不改）**。其他文档（CORE/STATE/docs 等）只引用不复述，更新只改对应台账件。

**读取协议（新会话/新 Loop）**: `memory/CORE.md` → `STATE.md` → `THREADS.md`（**读取协议不含 `memory/archive/`——常规会话不读已结案历史件**；替代读 HANDOFF.md 全文，HANDOFF.md 为冻结历史文档）。

**写入职责**:
- Loop A: 任务交付后更新 `STATE.md` 任务进度段。
- Loop B: 验证 PASS/FAIL 写入 `STATE.md` 验证段。
- Loop C: 审计判定与关键发现写入 `DECISIONS.md`。
- Loop D: 每次 neat/收尾覆写 `STATE.md`（旧版移入 `memory/archive/`）；从 dispatch_log 提炼重要决策进 `DECISIONS.md`。

L2 语义记忆层（mem0 自托管 + pgvector :15432 + MCP）见 docs/18 第 10 节，排在 OpenCode 交付链路打通后执行，今晚不装。

## 文档治理（docs_lint）

**neat 收尾必跑 `scripts/docs_lint.py`**（退出码 0 才可收口）。五项机器检查：INDEX 覆盖率+死链、存活文档状态头时效、**台账防漂移**（gap/遗留关键词只允许出现在 memory/THREADS.md，其他文档只引用不复述——08-11 漂移案的固化；已结案轨迹见 `memory/archive/THREADS_history.md`，该处不在关键词扫描域内）、skill 注册表 vs 两端安装 diff（`scripts/graph/sync_skills.sh --check`）、**配属注册表 vs 分发列表 diff**（AGENTS.md 注册表与 sync_skills.sh A/C_SKILLS 双向对账，治理体检 2026-08-12 新增）。

## 执行节奏治理 (2026-08-25, 用户批准)

- **主线程禁用 >5min 阻塞 sleep**: 一切里程碑等待 = GB10 cron one-shot + 文件工件 + 结 turn;
  watcher session / sleep 链模式作废。三害: 阻塞期间用户插不进话 / 上下文压缩 / ssh 长连接脆弱。
  等待不是工作, 工件才是。先例: 池×GUC 修复窗 (08-25 凌晨) 12min 闲置门禁转 cron 工件。
- **收集与判定分离**: 数据收集保留夜间 cron (机器时间, 流量干净); 需用户拍板的判定一律移至白天——
  主线程每日上午产出《判定一页纸》(分段数据 + 选项 + 推荐 + 红线核对), 用户白天圈选。
  任务卡不得把人类决策排在 22:00 后; 夜间窗口只执行已批准的确定性动作。
- **cron one-shot 三件套**: 跑完自删条目 + abort/rollback 分支写死在脚本 (不依赖在线判断) + 工件路径显式声明。
  同步固化于 templates/task_card_template.md §8。
- **cron 闸语义 (2026-08-25)**: 闸不达标 = 改期（至多 N 次）, 禁止 SKIP; 耗尽 = BLOCKED 标记, 不静默。
  工具 scripts/graph/cron_gate_helper.sh。案例: W4 闸 SKIP 致 W5 连环 abort (08-25 凌晨)。
- **UTF-8 字节截断必须字符安全 (2026-08-25)**: 引用 LLM 回答/中文文本做 `head -c N` 字节截断时, 必须接 `| iconv -f utf-8 -t utf-8 -c`
  （或改字符级截断）; 下游读文件默认 errors="replace", 判定类读取必须有第二数据源兜底。
  案例: 08-25 gate=UNKNOWN 误报——gate 脚本 head -c 400 在 position 657 腰斩"资产市"后字符 (invalid continuation byte),
  汇编器 rd() 吞 UnicodeDecodeError 返回空串。回归用例 = 08-25 当晚 gate PASS。
- **pending 卡交接必须 cron one-shot 触发 (2026-08-25)**: "稍后执行"类任务卡入账必须同批装触发 cron;
  禁止依赖"硬停后会话仍活"。案例: 晨间序列卡入账后零执行 (08-25)。

## Skill 路由（2026-08-29 立法）

装载决策依 **docs/SKILL_ROUTING.md**（五线总表 + 仲裁规则: 红线永载/领域优先/单任务≤5/新旧降级
+ 冗余裁决表 + 钩链矩阵）。任务卡必须含"skill 装载清单"行（模板已加）。路由表修订需用户批。

## 敏感文件纪律（2026-08-29 立法）

`~/.claude/settings.json`、`~/.codex/auth.json` 及各 harness 凭证文件 = **明文 token 载体,
永不 cat / 永不入 commit / 永不出现在任何工件或日志中**（只能 stat/chmod/路径引用）。
权限基线 600（08-29 已对 ~/.claude/settings.json 执行）。违反 = 红线事故级。

## 收口清单（2026-08-29 制度化）

每次收口 commit 前必须执行: `venv/bin/python scripts/graph/governance_drift_scan.py`
（状态词扫荡: 待批/待执行/待发送/待勾选 + 活文档日期超期）。命中 = 漂移候选自动登记
docs/29 backlog "漂移扫描待核"节（幂等去重）, 收口汇报附扫描结果行; 夜间 03:30 cron
轻扫（--cron 只报告不登记）。审计层（Loop C）范围含治理件。
