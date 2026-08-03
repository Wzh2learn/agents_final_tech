# Loop C 全库体检报告（review-codebase skill 方法论）

**审计对象**: `agents_final_tech` @ `a91ff74`（2026-08-04）
**方法论**: review-codebase（全库健康/架构/模式，非 diff 审查）；Google 工程原则：分层、单一职责、测试与代码同速增长、避免死代码
**前置门禁**: Loop B verify-report.json — `PASS`（2026-08-04T00:05，frozen_nodes 0 违规 / pytest exit 0 / api_anchors 0 失败）→ 审计放行
**只读合规**: 未修改任何文件、未做任何 git 写操作；冻结文件 `tests/test_m1_service.py` 与 `scripts/graph/frozen_hashes.txt` 仅读取核验（Loop B 已验证哈希一致），未触碰

## 全库度量基线

| 区域 | 文件数 | Python LOC | 备注 |
|---|---|---|---|
| src/ | 85 | 15,961 | web 13 文件 / biz 5 / storage 18 / tools 18 |
| scripts/ | 94（55 py + 20 sh + 16 md + 3 其他） | 10,267 | 扁平目录，无子分类（graph/ 除外） |
| tests/ | 29 | 4,185 | 225 个 `def test_`（含 parametrize 展开 = 227 收集数），13 skipped |
| config/ | 3 | 991 | m1_table_schema.json 占 16.5KB |

测试/代码 LOC 比 ≈ 16%，量级及格；但分布严重倾斜（见 H5）。

---

## Findings

### Critical

无。构建与测试链健康（227 passed / 0 failed），冻结节点完整，未发现数据丢失或已被利用级别的安全缺陷。

### High

**H1 架构倒挂：核心业务引擎住在 scripts/，src 靠 sys.path 黑科技引用**
- `src/web/routers/m1.py:34-39`、`src/biz/m2_service.py:127-132` — 两处用 `os.path.join(__file__, "..", "..", "..", "scripts")` + `sys.path.insert` 引入生产逻辑
- 甲方北极星 M1 解析引擎 `scripts/m1_statement_parser.py`（1917 LOC）与 M2 RAG 引导 `scripts/m1_rag_ingest.py`（402 LOC）都在 src/ 分层体系之外；而 `m1_rag_ingest.py:49` 又反向 `from biz.rag_service import RAGService`，形成 **scripts↔src 包级循环依赖**
- 后果：最核心的客户价值代码不受 src/ 的分层约束与测试惯例保护；部署依赖脆弱的相对路径；AGENTS.md 宣称的 web/biz/storage 分层对真正的引擎无效
- 建议：将两个文件提升为 `src/biz/m1_parser/` 包（按 parse/ocr/reconcile/mapping 拆模块），scripts/ 只留瘦 CLI 入口；这也顺势消解 M1 的巨型文件问题

**H2 knowledge.py 跨层直取存储 + 胖路由，双重违反成文边界**
- `src/web/routers/knowledge.py` 共 **24 处** `from storage...` 函数内直连（:120-121, :144-145, :208-209, :236-237, :275-278, :394-396, :431-432, :479-480, :540-542, :578-579…）
- `src/web/routers/knowledge.py:277-298` 直接查询 `LangchainPgEmbedding`/`func.count(...)` — 违反 AGENTS.md 明文禁令 "*Do not … bypass RAGService with ad hoc database queries*"
- 685 LOC、约 24 个端点，路由内做集合管理/文档 CRUD/chunk 编辑等业务逻辑，违反 AGENTS.md "*Keep route handlers thin and business logic in src/biz/*"
- 建议：新建 `biz/knowledge_service.py` 承接全部业务逻辑，embedding 统计走 RAGService/storage 门面；该文件是本次审计最集中的分层违规点

**H3 Schema 写接口 fail-open：未设 M1_ADMIN_TOKEN 时完全裸奔**
- `src/web/routers/m1.py:199-202, 231-236` — `_ADMIN_TOKEN` 未设置时 `_check_admin()` 直接 `return`（:233-234 "unprotected mode"），仅在启动日志打一条 warning；PUT /api/m1/schema、表/字段增删 4 个写端点对任何请求开放
- schema 是解析正确性的根（Loop D 授权的准冻结资产），被未授权篡改会静默污染全部下游解析与勾稽
- 建议：改为 fail-closed — 未配置 token 时写端点返回 503/403 或启动即拒；至少要求显式 `M1_ALLOW_UNPROTECTED_SCHEMA=1` 才开放

**H4 默认凭据 fail-soft：警告但照跑**
- `src/auth/users.py:14` — 默认管理员 `admin/admin123`（getenv 兜底），只发 RuntimeWarning
- `src/auth/jwt_handler.py:20` — `JWT_SECRET_KEY` 缺失时回退硬编码 `"dev-only-insecure-key-do-not-use-in-production"`，令牌可被任何读过源码的人伪造
- 二者在"忘记配环境变量"的部署中同时失效 = 完整认证链失守；docs/20 部署指南未把这两项列为硬门槛
- 建议：提供 `PRODUCTION_MODE` 开关，生产模式下缺任一环境变量即拒绝启动；部署文档加启动前检查清单

**H5 测试分布失衡：最大的一层（tools/）几乎裸奔**
- src/tools/ 约 4.1k LOC、18 个模块，是最大的层；`hybrid_retriever.py`(527)、`bm25_retriever.py`(420)、`qa_agent.py`(409)、`document_hierarchy.py`(411)、`text_splitter.py`(343)、`knowledge_base.py`(314)、`question_classifier.py`、`reranker_tool.py` 等在 tests/ 中**零单元引用**（仅 5 个需活服务的 integration/e2e 测试间接覆盖检索路径）
- 225 个测试函数中 test_m1_*+test_m2_* ≈ 147 个（65%）；`knowledge.py` 24 个端点无测试；storage 内部（document_manager 553 / s3_storage 424 / document_storage 334）仅 4 个相关测试
- 检索质量是 M2 的生命线（93% QA 正确率靠它），但检索代码本身没有回归网
- 建议：优先给 hybrid/bm25/rerank/splitter 补确定性单元测试（纯函数居多，成本低）；knowledge 路由补 httpx/TestClient 契约测试

### Medium

**M1 复杂度热点：1917 行单文件 + 185 行单函数**
- `scripts/m1_statement_parser.py`（1917 LOC）：`reconcile()` :1279 ≈185 行、`_coordinate_table_reconstruction()` :858 ≈123 行、`_text_lines_to_tables()` :745 ≈113 行、`process_sample()` :1606 ≈108 行（按相邻 def 间距估算）
- 单文件承担：格式解析×5 + OCR 回退×3 + 表头映射 + 勾稽 + 脱敏 + LLM 兜底，6 类职责
- 建议：与 H1 合并处理 — 提升为包时按职责拆 4-5 个模块，每模块 <400 行

**M2 rag_service.smart_retrieve 167 行，7 件事一个函数**
- `src/biz/rag_service.py:226-393` ≈167 行：集合选择+向量检索+BM25+去重+本地兜底+重排+合并；`_maybe_rerank` :813-903 ≈90 行
- 建议：抽 retriever 策略对象（vector/bm25/hybrid 各自独立），smart_retrieve 只做编排

**M3 Web 层胖函数**
- `src/web/routers/chat.py:145-288` `chat()` ≈143 行（SSE 编排内联在路由）、`get_suggestions` :329-413 ≈84 行
- `src/web/websocket_server.py:84-225` `handle_connection` ≈141 行
- 建议：SSE/WS 生命周期逻辑下沉 biz/agent_service 或独立 stream 模块

**M4 遗留代码：整套 Flask 备份应用 + 6 个 debug 脚本住在生产树**
- `src/web/app_flask_backup.py`（803 LOC）— 完整旧 Flask 表面仍在 src/web/ 内；docs/CLAUDE.md 明令 "*Do not introduce Flask response patterns*"，requirements.txt 却仍为它钉着 Flask+Werkzeug
- `scripts/debug_load.py`/`debug_load2.py`/`debug_split.py`/`debug_split2.py`/`ingest_debug.py`/`ingest_debug2.py` — 无 docstring、无用途说明的调试遗留（loop_c_audit_prompt Step 4 明确要查这一项）
- 建议：app_flask_backup.py `git mv` 进 docs/archive 同级或删（git 历史可找回）并同步摘掉 Flask 依赖；debug 脚本归档或删除

**M5 scripts/ 可维护性：94 个文件扁平堆放，身份混乱**
- 3 个 `test_*.py`（`scripts/test_db_conn.py`、`test_non_thinking_mode.py`、`test_web_ui.py`）因 `pytest.ini testpaths=tests` **永远不会被 pytest 收集** — 长得像测试，实际是 CI 盲区
- 重复/权属不明：`responses2chat_proxy.py` vs `responses2chat_proxy_v2.py`（AGENTS.md:42 引用 v1，v2 自称 "Clean … v2"，无人说明哪个是现役）；debug_load/debug_load2、debug_split/debug_split2、ingest_debug/ingest_debug2 三对孪生
- 54 个 .py 中仅 17 个提及 usage（≈2/3 无使用说明）；16 个 `loop_*.md`/`overnight_*.md` 已消费 prompt 存档与可执行工具混居
- 建议：分子目录（parse/ eval/ ops/ proxy/ graph/ archive/）；`test_*.py` 改名 `check_*.py` 或移入 tests/ 标 integration；README_scripts.md 增加"现役/存档"两栏清单，明确 proxy v1/v2 归属

**M6 文档幽灵引用：INDEX.md 指向不存在的 memory/ 权威层**
- `docs/INDEX.md:4`（"现状以 memory/ 为准"）、:16（"根 memory/ 蒸馏记忆层: CORE / DECISIONS / STATE / THREADS"）、:46（"现状快照一律写 memory/STATE.md"）— 但仓库根目录**没有 memory/ 目录**
- 新会话按 INDEX 指引去找现状会落空，被迫回退到 AGENTS.md/HANDOFF.md — 与 INDEX 自己的规则矛盾
- 建议：要么建立 memory/ 并落 STATE.md，要么修订 INDEX.md 把权威现状指回 AGENTS.md + HANDOFF.md 顶部快照

**M7 文档治理自相矛盾**
- `docs/INDEX.md:46` 宣布 "HANDOFF.md 冻结于 2026-08-03 快照，不再更新"，但 `HANDOFF.md:3` 赫然写着 "Snapshot — 2026-08-04 (current)" — 冻结声明与实际维护行为冲突（二者必有一个是错的）
- `docs/experiments/phase3_loop_c_review_codebase.md` 等 4 个 phase3 报告文件为空占位但已出现在 git status 未跟踪列表
- 建议：Loop D 明确 HANDOFF 定位（活文档 or 冻结）并统一 INDEX 措辞；空占位文件要么填充要么移除

### Low

**L1** `config/app_config.json:8-13` — 明文 `postgres/postgres` 本地开发库凭据。localhost 场景可接受，但建议改为 env 优先、配置文件兜底，避免未来误带上真实环境。

**L2** `src/scripts/sync_dify_kb.py`（63 行）— 一次性运维脚本误入 src/ 包，应移入 scripts/。

**L3** `src/tools/file_writer.py:19` — `secret_key=""` 空占位配置，模板残留，建议改为从 provider 读取。

**L4** `src/auth/users.py:10,40-43` — 运行时把 users.json 写进**源码目录** src/auth/，建议落 data/ 并加入 .gitignore。

**L5** AGENTS.md:224-236 — 2026-08-01 测试清单表（98+）与当前 227 并存，虽已注明是快照，但表格与脚注相邻易误读；建议把旧表整体折叠进历史小节。

**L6** `logs/graph/pytest_latest.txt` 仅记录冻结子集 18 tests 的运行输出；全量证据在 verify-report.json（exit 0）中，证据链完整但建议日志文件注明"仅冻结子集"以免误读。

## 值得肯定的健康项（审计证据）

- **下行分层基本干净**：biz→web、storage→biz/web 的上行违规 = 0；web→biz 全部走正规导入
- **冻结体系真正在运转**：frozen_hashes.txt + Loop B 30 分钟巡检 + git pre-commit 拦截，今日 00:05 全 PASS
- 依赖 100% 钉版本（requirements.txt 127 项全 `==`）；`.env` 未入库、.gitignore 覆盖全面
- TODO/FIXME 仅 8 处且多为 docstring 占位符 — 无积压技术债标记
- 文档纪律突出：INDEX.md 治理规则、archive 只进不删、experiments 按日期只追加、codebase_map.md 与实测 LOC 偏差 <15%；README/HANDOFF/AGENTS 三方数字（227 tests、100% 解析率、14/15 QA）完全一致

---

## 整体健康评级：**B**

流程纪律（四层 Loop、冻结节点、文档治理、测试全绿）达到 A 水准；但**核心引擎游离于分层体系之外（H1）、最大路由跨层直取存储（H2）、两处 fail-open/soft 认证（H3/H4）、最大模块层零单测（H5）**这四类结构性问题压住了上限。属于"运行健康、架构欠账"的典型 B 级。

## Top-5 改进建议

1. **引擎归位**（对应 H1+M1）：`m1_statement_parser.py` + `m1_rag_ingest.py` 提升为 `src/biz/m1_parser/` 包并按职责拆模块，scripts/ 留瘦 CLI；消除两处 sys.path 黑科技与包级循环依赖。这是单项收益最大的重构。
2. **knowledge.py 瘦身**（对应 H2）：业务逻辑迁入 `biz/knowledge_service.py`，删除对 `LangchainPgEmbedding` 的 ad-hoc 查询，恢复 AGENTS.md 明文边界。
3. **认证 fail-closed**（对应 H3+H4）：schema 写接口无 token 即拒绝；增加 `PRODUCTION_MODE` 启动门禁，缺 `JWT_SECRET_KEY`/`DEFAULT_ADMIN_PASSWORD`/`M1_ADMIN_TOKEN` 任一即不启动，并写入 docs/20 部署清单。
4. **给检索层补回归网**（对应 H5+M2）：优先为 hybrid/bm25/rerank/splitter 补确定性单元测试 + knowledge 路由契约测试，把 65% 集中于 m1/m2 服务的测试分布拉平；smart_retrieve 同步拆策略对象。
5. **scripts/ 大扫除**（对应 M4+M5）：分子目录归档 loop_*.md 与 debug 脚本，裁定 proxy v1/v2 权属，`test_*.py` 改名或移入 tests/，README_scripts.md 增加现役/存档清单；顺带清退 app_flask_backup.py 与 Flask 依赖。

*本报告为只读审计产物，未修改任何代码；修复执行归 Loop A，冻结红线不变。*

END-OF-REPORT
