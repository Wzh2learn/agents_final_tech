# Phase 3 Code Review — `src/` 全量审查报告

- **审查角色**: Loop A (执行层) read-only 代码审查任务
- **审查方法论**: 按 `skills/requesting-code-review/code-reviewer.md` 模板执行 (Senior Code Reviewer 视角)
- **审查范围**: `src/` 全部 (~16k 行, 85 个 Python 文件), 重点 `web/` / `biz/` / `storage/` 三层
- **审查焦点**: 架构分层违规、错误处理与异常泄露、workers=2 并发一致性、安全 (CORS/认证/路径穿越)、死代码
- **审查方式**: 只读分析 + 机械扫描 (AST unused-import 检测) + 依赖库源码核对 (starlette CORS 行为)
- **日期**: 2026-08-04
- **基线**: HEAD = a91ff74 (未做任何代码修改; 本报告为唯一产出)

---

## Strengths (做得好的地方)

1. **parse-file 上传无文件名穿越**: `src/web/routers/m1.py:91-93` 使用 `tempfile.NamedTemporaryFile` 服务端生成文件名, 仅取用户后缀且白名单校验 (`parser.PARSERS`), 上传路径本身无穿越风险; `finally` 中清理临时文件 (m1.py:104)。
2. **冻结 schema 保护设计正确**: `_write_schema` 只写 `config/m1_table_schema.json` 本地副本, 从不写 `~/wzh/m1_samples/` 冻结文件; `resolve_schema_path()` 本地覆盖优先 (scripts/m1_statement_parser.py:51-55)。
3. **knowledge 上传有完整校验**: `src/utils/file_validator.py` 扩展名 + 10MB 大小 + magic-bytes 三重校验, 且在 `upload_document` 中被调用 (knowledge.py:360)。
4. **chat.py 输入校验扎实**: 消息长度/危险内容过滤、conversation_id 字符集白名单 (chat.py:85-131)、120s 超时 (chat.py:230-239)、`_sanitize_error_message` 脱敏函数 (chat.py:34-48)。
5. **存储层有防腐与容错**: `LocalSyncStorage._resolve_path` 有路径穿越防护 (document_storage.py:22-33); `db.py` 连接池参数有上下界 + `pool_pre_ping` + 20s 重试 (db.py); `chat_persistence` PG 不可用时优雅降级。
6. **MCP 适配器边界干净**: `src/mcp_server/server.py` 等三个适配器确实只读, 入参有边界校验 (top_k 1-20, max_results 1-50), 符合 AGENTS.md 边界。
7. **rag_service DB 会话管理规范**: 所有 `get_session()` 均 try/finally close; 向量/BM25/fallback 三级降级 (rag_service.py:226-340)。
8. **M2 prompt 工程有防幻觉+脱敏指令**, 生成失败时降级返回检索原文 (m2_service.py:406-417 设计意图好, 但泄露异常文本, 见 H-4)。

---

## Issues (按严重度排序)

## Critical (必须修复)

### C-1. 默认部署完全无认证: 认证体系全线 fail-open
- **位置**: `src/web/middleware.py:44-52` (M1_API_TOKEN), `src/web/routers/m1.py:199-234` (M1_ADMIN_TOKEN), `src/auth/jwt_handler.py:41-49`, `src/auth/users.py:14-29`, `docker-compose.yml` (environment 段), `scripts/run.sh:50-58`
- **问题**:
  - `BearerAuthMiddleware`: `M1_API_TOKEN` 未设置时**跳过全部认证** (仅打一条 warning), 所有 API 匿名可访问。
  - `_check_admin`: `M1_ADMIN_TOKEN` 未设置时**直接 return**, schema 写接口 (PUT /api/m1/schema、增删表/字段) 匿名可写。
  - `docker-compose.yml` 与 `scripts/run.sh` **均未设置** M1_API_TOKEN / M1_ADMIN_TOKEN / JWT_SECRET_KEY / DEFAULT_ADMIN_PASSWORD (已核对 compose environment 段与 run.sh export 段) → 文档化的"生产部署"开箱即全裸。
  - 后果: 处理甲方金融对账单的系统, 任何人可上传文件、改写解析规则 (schema)、清空缓存、读取全部解析数据。
- **建议**:
  1. fail-closed: 未设置 token 时拒绝服务 (或至少拒绝写接口), 启动即报错退出;
  2. docker-compose.yml / run.sh 强制从 `${M1_API_TOKEN:?}` 读取, 缺失则启动失败;
  3. 保留现在的 warning 但改为 ERROR + 拒绝启动。

### C-2. `/api/knowledge/upload` 的 collection_name 未校验 → BM25 缓存路径穿越 (任意文件写/删 + pickle 反序列化风险)
- **位置**: `src/web/routers/knowledge.py:349-390` (upload_document), `src/web/routers/knowledge.py:102-110` (_invalidate_kb_cache), `src/tools/bm25_retriever.py:26-32` (_get_cache_path), `src/tools/bm25_retriever.py:97-99` (pickle.load), `src/tools/bm25_retriever.py:388-414` (clear_bm25_cache unlink)
- **问题**:
  - `upload_document` 的 `collection_name: str = Form("knowledge_base")` **未经过 `_validate_collection_name`** (该校验只用于 create/rename collection, 见 knowledge.py:210, 240), 直接透传给 `rag_service.ingest_file` 和 `_invalidate_kb_cache`。
  - `_invalidate_kb_cache` → `clear_bm25_cache` → `cache_dir / f"{collection_name}.pkl"` → `unlink`。攻击者传 `collection_name="../foo"` 即可删除 `/tmp/foo.pkl`; 索引重建路径 (`_build_bm25_index` → `pickle.dump`) 可向穿越路径**写入** pickle 文件。
  - 缓存目录是**可预测的世界可写路径** `/tmp/bm25_cache` (bm25_retriever.py:26), 且加载用 `pickle.load` (bm25_retriever.py:99): 本机任意用户 (或通过上面的写原语) 投放恶意 .pkl 即可在下次检索时**任意代码执行**。
  - 结合 C-1 (默认无认证), 这是远程可达的。
- **建议**:
  1. upload/delete/download/rename 等所有接受 collection_name 的入口统一调用 `_validate_collection_name(strict=True)` (已有正则 `^[\w\-\u4e00-\u9fff]{1,64}$`, knowledge.py:21);
  2. `_get_cache_path` 内对结果做 `os.path.realpath` 前缀校验 (带分隔符);
  3. 缓存目录改为项目内私有目录 (0700), 或改用带校验的序列化格式 (如 joblib 也不安全, 建议 JSON + 重建索引)。

## High (应当修复)

### H-1. workers=2 下进程内状态不一致 (M2 多轮会话为首)
- **位置**: `scripts/run.sh:57` 与 `Dockerfile:24` (`--workers 2`) vs `src/biz/m2_service.py:57-99` (_sessions), `src/biz/rag_service.py:31-50` (runtime RAG settings), `src/web/routers/pages.py:51` (_health_cache), `src/utils/metrics.py` (registry), `src/biz/agent_service.py:28` (_reflection_index)
- **问题**:
  - uvicorn 多 worker = 多进程, 各自独立内存。最严重的是 M2 会话: `_get_session` 只在 session **不在本进程内存时**才从 PG 懒加载 (m2_service.py:77-88); 会话一旦进入某 worker 的 `_sessions`, 后续永不与 PG 对账。两个 worker 各自持有同一 session_id 的不同历史副本, 请求被轮询分发时 → **上下文丢失/错乱**, 而 PG 端被双方重复 append (m2_service.py:92-99), 冷启动重载时历史比任一 worker 看到的都多。
  - 同理: `/api/knowledge/rag-settings` 设置的检索参数只写入处理该请求的 worker 的缓存 (rag_service.py:43-50 + knowledge.py:340-346) → 两个 worker 检索行为不一致, 表现为"同样问题答案时好时坏"。
  - `_health_cache`、Prometheus metrics、agent reflection index 均 per-worker, 指标抓取结果随命中 worker 漂移。
  - 注意 `src/main.py:244` 自带启动器是 workers=1, 与 run.sh/Dockerfile 的 workers=2 不一致, 说明该问题在本地开发中不可见。
- **建议**: 三选一 — (a) 改 workers=1 并以异步并发承载 (当前阻塞问题 H-2 修好后单 worker 足够); (b) 会话/配置状态全部外置 PG/Redis 并每次读取; (c) 负载均衡按 session_id 粘性路由。M2 会话最小修复: `_append_history` 前先与 PG 合并, 或每次都从 PG 读。

### H-2. async 端点内调用阻塞同步代码 → 事件循环卡死, 触发容器健康检查失败
- **位置**: `src/web/routers/m1.py:96-104` (process_sample, OCR 时 74s+), `src/web/routers/m2.py:66-84` → `src/biz/m2_service.py:277-293` (urllib 同步 HTTP, 60s timeout), `src/web/routers/pages.py:55-119` (最多 4 次 urlopen + embedding + 检索 + 重排)
- **问题**:
  - 这些端点都是 `async def`, FastAPI 直接在事件循环里执行 handler。`process_sample` (含 OCR 可达分钟级)、`m2_ask` (两次同步 HTTP 调 :8004)、`health_full` (串行阻塞探测) 会**冻结整个 worker 的事件循环**。
  - workers=2 时两个并发 parse 即全站不可用; Docker healthcheck (`curl /health`, docker-compose.yml:36-40) 虽然打的是轻量 /health, 但 /health 也在同一事件循环上 → 阻塞期间健康检查超时 → 容器被标记 unhealthy/重启 → 解析任务丢失。
  - `/api/health/full` 还免认证 (middleware.py:19), 可被外部反复触发放大阻塞。
- **建议**: 重活全部改 `def` handler (FastAPI 自动放线程池) 或显式 `asyncio.to_thread` / `run_in_executor`; 给 parse-file 加并发信号量; 健康探测改并行 + 更短超时。

### H-3. WebSocket 协作服务在 workers=2 下必然半残
- **位置**: `src/main.py:176-189` (每 worker 执行 startup_event), `src/web/collaboration_service.py:16-29` (start_websocket_thread), `src/web/websocket_server.py:365-414`, `config/app_config.json:203` (`realtime_collaboration: true`)
- **问题**: 每个 worker 进程都会在 startup 时起线程 `asyncio.run` 绑定 :8765 — 后启动的 worker 线程 bind 失败静默死亡; `active_connections` 是进程内 dict, `broadcast_agent_message` 只广播给**本进程**的连接。处理 chat 请求的 worker 若不是持有 WS 服务器的那个, AI 消息广播**静默丢失**。
- **建议**: WS 服务独立进程/容器; 或广播改经 PG/Redis pub-sub; 至少在 bind 失败时记录 ERROR 并让 `broadcast_agent_message` 有失败可观测性。

### H-4. 异常原文系统性泄露给客户端
- **位置**: `src/web/routers/knowledge.py` (23 处 `str(error)` 直接回传, 如 :131, :182, :203, :232, :390, :568, :611), `src/main.py:210-217` (`HTTPException(500, detail=str(e))` 无截断), `src/main.py:286-302` (全局 handler 回传 `str(exc)[:200]`), `src/biz/m2_service.py:416` (兜底答案内嵌 `错误: {type(exc).__name__}: {exc}`), `src/web/routers/pages.py:75,83,93,109` (免认证的 /api/health/full 回传 error detail), `src/web/routers/cache.py:20,31`
- **问题**: SQLAlchemy/psycopg 异常文本常含 DSN、表结构、SQL 片段; urllib 异常含内部端点地址。knowledge.py 的 23 个端点甚至以 HTTP 200 + `{"status":"error","message":str(error)}` 返回, 绕过全局 handler 的截断。`/api/health/full` 免认证, 是稳定的信息探测入口。
- **建议**: 统一走全局 handler; 对外 message 用固定文案 + request_id, 详情只进日志; knowledge.py 改为 raise HTTPException(500) 而非 200 包错; m2 兜底答案不要内嵌异常文本。

### H-5. JWT 硬编码兜底密钥 + 认证模块未接线 + 默认口令 admin123
- **位置**: `src/auth/jwt_handler.py:41-49`, `src/auth/users.py:14-29`, `src/auth/dependencies.py:14-29`, `src/auth/router.py`
- **问题**:
  - `JWT_SECRET_KEY` 未设置时回退硬编码 `"dev-only-insecure-key-do-not-use-in-production"` (仅 warnings.warn) → 任何读过源码的人可伪造 token。
  - 全仓 grep 确认 `get_current_user` **没有任何路由在使用** — JWT/登录体系是"装了但没接"的死安全机制, 容易给后续维护者"已有用户级认证"的错误安全感。
  - 默认管理员 `admin/admin123` (users.py:14), `_save_users` 会把 users.json 写进源码树 `src/auth/` (users.py:40-43), 有随 commit 泄露风险 (.gitignore 未覆盖, `git check-ignore` 验证返回 1)。
- **建议**: 要么完整接线 (所有业务路由 Depends(get_current_user) 并强制 JWT_SECRET_KEY), 要么整体下线 auth 模块避免误导; users.json 路径移出源码树并加 .gitignore; 删除 admin123 兜底。

## Medium (建议修复)

### M-1. CORS 通配 + allow_credentials=True
- **位置**: `src/main.py:137-148`
- **问题**: 默认 `CORS_ORIGINS="*"` 且 `allow_credentials=True`。已核对安装版 starlette 源码 (`middleware/cors.py:155-159`): 请求带 Cookie 时会**反射任意 Origin** 并附 `Access-Control-Allow-Credentials: true`, 等价于对凭据请求开放全域 CORS。当前主认证是 Bearer header 故现实风险中等, 但一旦引入 cookie 会话即被利用。
- **建议**: 生产默认拒绝通配; `CORS_ORIGINS` 未配置时 fail-closed 或仅允许同源; 通配与 credentials 互斥。

### M-2. schema 文件写入非原子、无跨进程锁
- **位置**: `src/web/routers/m1.py:223-229` (_write_schema)
- **问题**: 直接 `open("w") + json.dump`, 两 worker 并发 PUT/增删字段 → 丢失更新; 写入中途崩溃 → schema 文件损坏 (而 parser 每次解析都读它, m1.py:97)。读侧 `_read_schema` 也无锁, 可能读到半截文件。
- **建议**: 写临时文件 + `os.replace` 原子替换; 跨进程用文件锁 (fcntl/flock) 或把 schema 移入 PG。

### M-3. chat_persistence 单连接并发使用 + 历史无限增长
- **位置**: `src/storage/chat_persistence.py:36-58` (单 psycopg 连接, execute 在锁外), `src/storage/chat_persistence.py:93-106` (load_messages 无 LIMIT)
- **问题**: psycopg 连接对象非线程安全, 当前靠"只在事件循环线程调用"侥幸成立; 一旦有线程池调用 (H-2 的修复若用 to_thread 即触发) 就是并发写单连接。另外 PG 端消息永不清理, `load_messages` 全量返回, 冷启动会话可载入远超 `_MAX_TURNS=10` 的历史。
- **建议**: 换连接池 (与 db.py 的 SQLAlchemy engine 复用), load 加 `ORDER BY id DESC LIMIT` + 反转, 定期清理过期 session。

### M-4. parse-file 无上传大小限制
- **位置**: `src/web/routers/m1.py:90` (`content = await file.read()` 无上限)
- **问题**: knowledge 上传有 10MB 限制, 但 M1 parse-file 没有; 超大文件可打爆 worker 内存 (还叠加 H-2 的阻塞)。
- **建议**: 复用 `FileValidator.check_size` 或 FastAPI 层限制; 分块读取并在超限时提前中止。

### M-5. 分层违规: web/biz 经 sys.path hack 反向依赖 scripts/
- **位置**: `src/web/routers/m1.py:31-42` (_get_parser), `src/biz/m2_service.py:117-136` (_load_rag)
- **问题** (对应审查焦点 1):
  - AGENTS.md 定义 `scripts/` 是运维/实验脚本, 现在核心业务路径 (parse-file、M2 问答) 运行时依赖 scripts/m1_statement_parser.py 与 scripts/m1_rag_ingest.py, 通过 `sys.path.insert` 动态导入 — 层级倒挂 (web→scripts), 路径靠 `__file__` 相对推算, 部署目录结构一变即断。
  - `import m1_rag_ingest` 带环境变量副作用 (设置 embedding/PGVector 配置), 导入顺序变成隐式契约。
  - 模块级全局缓存 (`_parser_mod`, `_rag_service`) 无锁, 目前单事件循环线程下侥幸安全。
- **建议**: 将 m1_statement_parser / m1_rag_ingest 的核心逻辑提升为 `src/biz/` 或 `src/tools/` 内的正式模块 (scripts 保留 CLI 薄壳); 这也是解决 C-2/H-2 的前置。若暂不迁移, 至少在 AGENTS.md 中把这两个 scripts 文件升格为"受控依赖"并纳入 Loop B 冻结校验。

### M-6. biz/m2_service 直接查 langchain 内部表 (架构边界)
- **位置**: `src/biz/m2_service.py:146-174` (embedding_count), `src/biz/m2_service.py:446-478` (_query_collection_chunks), `src/biz/m2_service.py:480-497` (list_products)
- **问题** (对应审查焦点 1): AGENTS.md 明令"不得绕过 RAGService 做 ad hoc 数据库查询"。这三处虽自称"只读元数据聚合、非检索", 但直接耦合 `langchain_pg_embedding/langchain_pg_collection` 内部表结构 (cmetadata JSONB 路径查询), langchain 升级即碎, 且确实绕过了 RAGService 抽象。
- **建议**: 在 RAGService 上开正式的元数据聚合接口 (list_products/timeline/counts), m2_service 只调接口; 若保留直查, 需在 AGENTS.md 边界章节显式豁免并固定 langchain 版本。

### M-7. `/api/cache/clear` 无鉴权分级
- **位置**: `src/web/routers/cache.py:24-33`
- **问题**: 任意 API token 持有者 (默认配置下匿名) 可清空全局缓存 — 连带清掉 runtime RAG settings 与 kb_stats 缓存, 是可被利用的扰动点。
- **建议**: 挂 X-Admin-Token 校验 (复用 m1.py 的 _check_admin 模式)。

### M-8. 静默吞异常 (可调试性)
- **位置**: `src/biz/m2_service.py:384-385` (对比路由失败 `except Exception: pass`), `src/biz/m2_service.py:349-350` 附近 (_rewrite_query 失败静默回退), `src/storage/provider.py:68` (裸 `except: pass`)
- **问题**: 对比查询结构化失败时用户无感知地退化为普通 RAG, 日志零痕迹, 线上排障无从下手。
- **建议**: 至少 `logger.warning(..., exc_info=True)`, 并在响应里带 `routing: "fallback"` 字段。

### M-9. `_resolve_path` 前缀比较缺少分隔符边界
- **位置**: `src/storage/document_storage.py:22-33`
- **问题**: `full_path.startswith(abs_root)` 字符串前缀判断: 若 root 为 `/data/docs`, 则 `/data/docs_evil/secret` 也能通过。当前 root_dir 取值下未必可达, 但属于标准错误写法。
- **建议**: 改 `os.path.commonpath([abs_root, full_path]) == abs_root` 或 startswith(abs_root + os.sep)。

## Low (可择机处理)

### L-1. 死代码与未用 import (机械扫描结果)
- `src/web/app_flask_backup.py`: **803 行, 全仓零引用** (grep 验证), 纯死代码, 建议移出 src/ 进 archive 或删除。
- AST 扫描发现 **68 处未用 import**, 重点:
  - `src/main.py:14-15` (get_agent_service_sync, get_rag_service, get_rag_service_sync), `src/main.py:271` (traceback as _tb)
  - `src/biz/rag_service.py:15-16` (classify_question_type, get_retrieval_strategy, get_document_info — 提示 question_classifier 可能整体未用)
  - `src/tools/hybrid_retriever.py:12`, `src/tools/rag_retriever.py:13` (rerank_documents 未用 → reranker 接线可能不完整)
  - `src/web/collaboration_service.py:10` (broadcast_agent_message 导入未用 → 与 H-3 的广播断线相互印证)
  - `src/storage/provider.py:12`, `src/storage/database/document_manager.py:9,10,14`
  - 完整清单可由 `python /tmp/unused_imports.py` (AST 扫描) 复现。

### L-2. 裸 `except:` 5 处
- `src/utils/cache.py:192`, `src/tools/document_loader.py:117,250`, `src/storage/provider.py:68`, `src/web/websocket_server.py:211` — 会吞掉 KeyboardInterrupt/SystemExit, 改 `except Exception`。

### L-3. token 比较非常量时间
- `src/web/middleware.py:61` (`auth_header[7:] == self.token`), `src/web/routers/m1.py:235` (`x_admin_token != _ADMIN_TOKEN`) — 改 `hmac.compare_digest`。实际可利用性低, 属加固项。

### L-4. 中间件顺序: 401 不被请求日志记录
- `src/main.py:151-153` 先加 RequestLogging 后加 BearerAuth → Starlette 逆序应用, BearerAuth 在最外层, 被拒请求不经过日志中间件 → 认证失败无审计痕迹。调换两行顺序即可。

### L-5. `_is_exempt` 细节
- `src/web/middleware.py:31` `path.startswith(prefix + "?")` 是死逻辑 (url.path 不含 query); `/docs` `/redoc` `/openapi.json` 免认证 (middleware.py:19-22) 在开启 token 后仍暴露完整 API schema, 建议生产关闭 docs 或纳入认证。

### L-6. 杂项
- `src/auth/jwt_handler.py:79` `datetime.utcnow()` 已弃用 (3.12 deprecation warning)。
- `src/web/routers/m2.py:21-29` 同一模块三条重复 import, 可合并。
- `src/main.py` `/cancel/{run_id}` 返回 `not_implemented` (约 :110) 是明示 stub, 建议 docs 中标注或移除。
- `src/web/routers/chat.py:168-181` 的"通用问题"正则过宽 (`^怎么.*?$` 等), 路由判断基本恒真, 逻辑价值存疑。
- `src/storage/database/db.py:56-77` 首次建引擎最多阻塞 20s; 若首次触发发生在 async handler 内会卡事件循环, 建议 startup 事件预热。

---

## Recommendations (系统性建议)

1. **先定 worker 模型再做其他修复**: H-1/H-2/H-3 同源 — 建议明确选择 workers=1 + 异步化 (推荐, 改动最小) 或状态全外置, 并把该决定写进 AGENTS.md, 否则后续每个新功能都会重蹈"进程内状态"覆辙。
2. **安全基线清单**: C-1/C-2/H-5/M-1/M-7 合并为一个"生产安全门禁"PR — fail-closed 认证、collection_name 白名单、CORS 收紧、密钥强制化 — 在门禁落地前不应把 :5050 暴露到内网之外。
3. **错误处理统一**: 废弃 knowledge.py 的 `200 + {"status":"error"}` 模式, 全部改走全局 handler + request_id 关联 (现有全局 handler 框架已具备, 只差执行)。
4. **scripts 依赖正名**: M-5 的迁移是 C-2/H-2 修复的前置, 建议作为下一个 Loop A 任务的独立 PR。
5. **Loop B 增补校验项**: 建议把"compose/run.sh 必须定义 M1_API_TOKEN"与"app_flask_backup.py 不得被引用"加入 Loop B 的 30min 校验清单 (需 Loop D 批准, 涉及 frozen_hashes.txt 之外的新规则)。

## Assessment

**Ready to merge? No — 需先修 Critical。**

**Reasoning:** 代码整体工程素养不差 (上传校验、DB 会话管理、MCP 只读边界、输入验证均有亮点), 但默认部署配置 + fail-open 认证 + collection_name 穿越两个 Critical 问题意味着当前形态不满足"处理甲方金融数据"的最低安全要求; workers=2 与进程内状态的矛盾则会在生产负载下以会话错乱和健康检查重启的形式持续发作。建议按 C → H 顺序修复并复跑 Loop B 后再进入客户端演示/交付。

END-OF-REPORT
