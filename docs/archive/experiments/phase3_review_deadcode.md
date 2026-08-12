# Phase 3 死代码专项审查报告 (Dead Code Audit)

- 日期: 2026-08-04
- 执行: Loop A (执行层), 按 Loop D 专项指令
- 方法论: `skills/requesting-code-review/code-reviewer.md` 模板 (read-only 审查变体)
- 范围: 全仓库死代码排查 (src/tools, src/utils, main.py 路由树可达性, MCP 注册, 资源目录, 根目录残留)
- 约束遵守: 只读分析; 唯一写操作 = 本报告; 未触碰 `tests/test_m1_service.py` 与 `scripts/graph/frozen_hashes.txt`; 未做任何 git 操作; 只建议不执行。

## 审查方法

1. **AST 静态导入闭包**: 用 `ast` 解析 `src/` 全部 79 个 .py 文件, 从入口 `main.py` 计算传递导入闭包 (61 个模块可达, 26 个不可达), 无 importlib/动态导入干扰 (已用 `rg "importlib|__import__"` 验证, 仅 err_trace.py 中路径字符串误报)。
2. **逐模块引用检索**: 对 src/tools 17 个模块、src/utils 11 个模块逐一 `rg` 模块名与导出符号, 范围覆盖 src/tests/scripts/config/docs。
3. **运行配置核对**: opencode.json、docker-compose.yml、deploy/、scripts/start_*.sh、config/*.json。
4. **git 追踪状态核对**: `git ls-files` 区分"已追踪死代码"与"本地未追踪残留"。

## Strengths (现状健康面)

- `src/tools` 17 个模块中 15 个有真实调用链 (biz/rag_service.py、agents/agent.py、web/routers 为三大消费方), 无大面积死区。
- `src/utils` 除 `log/common.py` 外全部活跃; `config_loader.py` 被 14 个文件引用, 是健康的中枢。
- 三个 MCP server 全部在 opencode.json 注册且 `enabled: true`, 配套 start 脚本、契约测试 (tests/test_*_mcp_server.py)、冒烟脚本 (scripts/smoke_test_*.py) 齐全, **无死 MCP**。
- `agents/agent.py` (LangGraph in-app agent) 经 `biz/agent_service.py` 被 main.py 路由树真实触及, 不是死代码。
- `.gitignore` 已覆盖全部工具残留目录 (.omc/.qoder/.ocr_cache/.agent-of-empires/sessions.db/data/), 仓库追踪面干净。

## Issues

### Critical (Must Fix)

无。死代码不构成运行时缺陷; 本次未发现因死代码引发的 bug 或安全风险。

### Important (Should Fix) — 确认零引用的 src 模块

#### 1. `src/tools/knowledge_base.py` (314 行) — 完全孤儿
- 证据: `rg -l "tools\.knowledge_base|from tools import .*knowledge_base|from \.knowledge_base import" src tests scripts` → 0 个外部文件。符号级验证: `rg "KnowledgeBaseTool|search_knowledge_base|get_knowledge_base_stats|AddDocumentInput"` 排除自身后 → 0 命中。不在 main.py AST 闭包内。
- 备注: 其 `add_document_to_knowledge_base`/`delete_documents_from_knowledge_base` 与活跃的 `tools/rag_tools.py` 同名函数重复 (后者经 biz 层 + tools/__init__ 导出, 是现行实现)。本文件是旧直连实现。
- 删除风险: **低**。无 import 方, 不在 tools/__init__.py 导入链, 无测试引用。最后改动 2026-01-04 (0100137)。

#### 2. `src/tools/rag_retriever.py` (142 行) — 完全孤儿
- 证据: `rg -l "tools\.rag_retriever|rag_retrieve_with_rerank" src tests scripts` 排除自身 → 0 命中; AST 闭包不可达。它引用的 reranker_tool/vector_store 均有其他活跃消费方, 删除不影响。
- 删除风险: **低**。最后改动 2026-01-04 (0100137)。

#### 3. `src/web/app_flask_backup.py` (803 行) — 迁移遗留备份
- 证据: `rg -l "app_flask_backup|flask_backup" .` (排除 venv/.git) → 0 命中。AST 闭包不可达。commit e048cb0 (2026-01-19) "统一迁移到 FastAPI 框架" 后遗留。
- 备注: 它是 `utils.cache`/`utils.constants` 的引用方之一, 但这两个 utils 另有活跃引用, 删除无副作用。git 历史已保留完整内容, 备份价值冗余。
- 删除风险: **低**。

#### 4. `src/scripts/sync_dify_kb.py` (63 行) — 依赖缺失目录, 不可运行
- 证据: `rg -l "sync_dify_kb" .` 排除自身 → 0 命中。脚本硬编码 `DIFY_DIR = <repo>/dify`, 而 `dify/` 目录在磁盘上不存在 (仅 .gitignore 有 `dify/` 条目), 脚本运行必报"目录不存在"。
- 删除风险: **低**。若未来重启 Dify 同步可从 git 历史恢复 (dd2e616)。

#### 5. `src/utils/log/common.py` (8 行) — 零引用工具函数
- 证据: `rg "is_prod|get_execute_mode" .` (排除 venv) → 仅 common.py 自身 3 行定义, 无任何调用方。
- 删除风险: **低**。

#### 6. `src/tools/__init__.py` 中 `ALL_TOOLS` 导出块 — 死导出面
- 证据: `rg -n "ALL_TOOLS" .` (排除 venv) → 仅 tools/__init__.py 自身 (L29 定义, L49 `__all__`), 无任何 `from tools import ALL_TOOLS` 消费方。agents/agent.py 直接 import 具体函数, 不走该导出面。
- 注意: **不能删除 `tools/__init__.py` 文件本身** —— Python 语义下任何 `import tools.X` 都会执行它; 仅 `ALL_TOOLS` 列表与 `__all__` 是死代码。其 import 的 5 个模块 (document_processor/qa_agent/feedback_handler/file_writer/rag_tools) 均有独立活跃引用, 精简与否均安全。
- 删除风险: **低** (仅删 ALL_TOOLS 块)。

#### 7. `src/auth/dependencies.py` (29 行) — 导入但从未使用
- 证据: `rg -l "auth\.dependencies|get_current_user" src tests scripts` → 仅 `auth/__init__.py` (re-export) 与自身。所有 router (含 auth/router.py) 均未 `Depends(get_current_user)`。AST 闭包中 main.py 不可达 (仅因 auth/__init__ 被 import 时被动加载)。
- 备注: jwt_handler/users 是活跃的 (auth/router 使用), 唯独 `get_current_user` 这个路由守卫从未接线。这可能是"计划中未完成"而非"废弃" (AGENTS.md 记载 Phase 3 已做 Auth), 需 Loop D 定性。
- 删除风险: **中低**。删文件必须同步修改 `auth/__init__.py` 的 re-export, 否则包导入即崩。若后续计划用 FastAPI 依赖注入保护 /api 端点, 建议保留并接线而非删除。

### Minor (Nice to Have) — 资源文件与根目录残留

#### 8. `assets/*.yml` 5 个 Dify 工作流导出 (共 3854 行)
- 文件: WF_QA_Main.yml (982), WF_DocumentProcessor_v1.yml (1164), WF_Feedback_Handler_v1.yml (947), Master_Router.yml (451), 文档处理.yml (310)。
- 证据: `rg -n "yaml|assets/" src/tools/*.py src/agents/agent.py src/biz/*.py` → 代码仅在 docstring 注释中提及 ("对应 Dify 工作流：…", qa_agent.py 提示词溯源注释), 无任何 yaml.safe_load/open 加载。**运行时零引用, 仅文档溯源价值**。
- 删除风险: **低** (运行无关), 但建议移入 docs/archive/ 保留溯源链, 不建议直接删除。

#### 9. `assets/assets/` 嵌套目录 2 文件 — 零引用测试残留
- 证据: `rg -l "test_write_file" .` → 0 命中; `rg -l "qa_pairs|建账基础问答" .` (排除 assets 自身) → 0 命中。疑似 file_writer 工具早期试跑产物 (file_writer 写入路径相对 assets/)。
- 删除风险: **低**。

#### 10. `assets/test_rule_document.md` (77 行) — 仅 debug 脚本引用
- 证据: 引用方仅 `scripts/debug_split.py`, `scripts/debug_load2.py` (两个一次性调试脚本)。
- 删除风险: **低**; 建议与 debug 脚本同批处置 (见建议 5)。

#### 11. `image/review_evidence/` (13 文件, 1.1MB) — 仅归档文档引用
- 证据: `rg -l "review_evidence" .` → 仅 `docs/archive/code_review_prompt.md` (已归档验收报告) 内嵌引用。
- 删除风险: **低**, 但属验收证据链, 建议保留或整体随归档文档迁移, 不建议删除。

#### 12. 根目录 `sessions.db` (24KB, 未追踪)
- 证据: `git ls-files sessions.db` → 空 (已被 .gitignore `sessions.db`/`*.db` 覆盖)。代码引用在 `storage/collaboration/db.py` L39/42/52 —— 仅当 PGDATABASE_URL 缺失时的 SQLite 回退路径, 文件本身是旧运行产物 (2026-07-09)。
- 删除风险: **低** (可随时再生)。

#### 13. `.coze` (399B, 已追踪但已被 .gitignore 忽略)
- 证据: `rg -l "\.coze" .` 排除自身 → 0 命中; 属历史提交遗留 (先提交后加 ignore)。Coze 平台清单, 本项目无 Coze 集成代码。
- 处置建议: `git rm --cached .coze` 移除追踪 (文件本身可留可删)。风险: **低**。

#### 14. `run.bat` (Windows 启动器) — 被新部署链取代
- 证据: `rg -l "run.bat" .` → 仅 docs/archive/* 归档文档引用。现行部署 = `scripts/run.sh` + docker-compose.yml (docs/20 部署指南); run.bat 内引用的容器名 `pgvector_15432` 与 docker-compose 的 `m1_pgvector` 不一致, 属迁移前遗留。
- 备注: AGENTS.md 仍保留 Windows 开发命令说明, 若团队仍有 Windows 开发场景可暂缓。
- 删除风险: **低**。

#### 15. 根目录工具残留目录 (均未追踪, 已 gitignore)
- `.agent-of-empires/` — AoE harness 配置; AGENTS.md 明确记载 AoE 用于 Loop A 分发 (虽 send 受限), **保留**。
- `.omc/` — 2026-08-04 仍在写入, 为某活跃 CLI 的会话状态, **保留** (勿删活跃工具状态)。
- `.qoder/` — Qoder CLI 侦察配置, AGENTS.md/docs/16/2026-07-29_qoder_recon.md 有档, **保留**。
- `.ocr_cache/` — `scripts/m1_statement_parser.py` 运行时缓存 (活跃), **保留**。
- 任务点名的 `.claude/ .vscode/ .windsurf/` 在仓库根**实际不存在** (已被 .gitignore 覆盖且磁盘无残留), 无需处置。
- 删除风险: 不适用 (建议维持现状)。

#### 16. `scripts/debug_*.py` 5 个一次性调试脚本 (范围外附带发现)
- debug_load.py, debug_load2.py, debug_markdown_splitter.py, debug_split.py, debug_split2.py —— 引用 document_loader/text_splitter/test_rule_document.md, 无测试或文档消费。属 scripts/ 运维区, 不在本次硬性范围内, 仅建议与 #10 同批评估。

## main.py 路由树可达性结论 (任务第 2 项)

AST 闭包不可达的 26 个模块中, 逐一甄别后:

| 模块 | 定性 |
|---|---|
| mcp_server.server | **活** — 独立进程, opencode.json `jinrong-rag` enabled, `bash scripts/start_mcp_server.sh` → `python -m mcp_server.server` |
| vision_mcp_server.server/service | **活** — opencode.json `jinrong-vision` enabled (OCR 主链路, AGENTS.md 记载 vision-8004 兜底) |
| tabular_mcp_server.server/service | **活** — opencode.json `jinrong-tabular` enabled, 有专职 agent (tabular-researcher/tabular-runner) |
| agents.agent | **活** — 经 biz.agent_service 被 main.py 间接触及 (闭包可达) |
| tools.knowledge_base, tools.rag_retriever | **死** (见 Issues #1 #2) |
| utils.log.common | **死** (见 #5) |
| auth.dependencies | **导入未用** (见 #7) |
| web.app_flask_backup | **死** (见 #3) |
| scripts.sync_dify_kb (src/scripts) | **死** (见 #4) |
| 各包 __init__.py | 包初始化, 非死代码 |

**MCP 注册核查结论 (任务第 3 项): 三个 MCP server 全部注册、enabled、有启动脚本与测试, 无死 MCP; 不构成对 AGENTS.md "read-only MCP 边界" 的任何偏离。**

## Recommendations

1. **第一批删除 (低风险, 纯零引用)**: `src/tools/knowledge_base.py`, `src/tools/rag_retriever.py`, `src/utils/log/common.py`, `src/web/app_flask_backup.py`, `src/scripts/sync_dify_kb.py`, `assets/assets/` 整个嵌套目录。合计约 1332 行 src 代码 + 3 个数据文件。删除后跑 `pytest tests` (227 passed 基线) + `python scripts/verify_config.py` 验证。
2. **第二批 (需同步小改)**: `tools/__init__.py` 仅删 `ALL_TOOLS` 块与 `__all__` 行, 保留文件与 5 个 import; `auth/dependencies.py` 由 Loop D 定性 —— 删除需同步改 `auth/__init__.py`, 若计划接线路由守卫则保留并补 `Depends`。
3. **assets/*.yml 归档而非删除**: 移入 `docs/archive/dify_workflows/` 并保持 tools docstring 溯源注释可指向 (注释仅提名字, 不含路径, 迁移零成本)。
4. **`.coze` 移除 git 追踪**: `git rm --cached .coze` (已在 .gitignore, 属历史遗留追踪)。
5. **debug 脚本与 test_rule_document.md 同批评估** (范围外, 建议下一轮 Loop D 决策)。
6. **保留项**: image/review_evidence (验收证据链), sessions.db 可随手删但无需专项处置, 全部工具残留目录维持现状。
7. **流程建议**: 删除类操作不在本审查执行; 建议作为独立 Loop A 任务 (单 commit, `fix(m1): 移除零引用死代码` 形式), 由 Loop B 验证冻结节点不受影响后再合入。

## Assessment

**Ready to merge?** 本报告为只读审查产物, 无代码变更, 不涉及 merge 判定。

**Reasoning:** 仓库死代码总量有限且高度集中 —— src 内确认零引用代码约 1361 行 (占 src 总量 <4%), 主要是 2026-01 Dify→原生工具迁移与 Flask→FastAPI 迁移的遗留物; 现行主干 (biz/rag_service → tools 检索栈、M1/M2 路由、三 MCP server) 引用链完整健康, 无死 MCP、无死路由、无死模板。按上述分批处置可在一个 Loop A 任务内安全清理完毕。

END-OF-REPORT
