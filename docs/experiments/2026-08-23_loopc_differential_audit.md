# Loop C 独立差分审计报告（2026-08-23）

状态: 审计完成（对象1 PASS / 对象2 PASS, 17 findings: 4 LOW + 13 INFO, 无 CRITICAL/HIGH/MEDIUM） | 更新: 2026-08-23 | 取代/被取代: 无

审计基线: 仓库 /home/testuser/wzh/projects/agents_final_tech, HEAD 07a7c16（只读审计, 未改任何代码/配置）。
审计对象:
1. `docs/experiments/2026-08-23_pg_pool_leak_attribution.md`（归因文档 + 已提交修复 `git diff 2f2739f 07a7c16 -- src/tools/vector_store.py`）
2. `docs/experiments/2026-08-23_fk_adapter_fix_draft.md`（菜单 a 草稿 vs 已提交 `git diff 2f2739f 07a7c16 -- src/biz/opencode_adapter.py` + 测试覆盖）

方法: 逐条事实声明对照代码（file:line 证据）; 修复前快照取自 `git show 2f2739f:<file>`; 机制声明对照已安装依赖源码（venv, langchain-postgres==0.0.16）; 测试以 `pytest --collect-only` 验证（只读）。

---

## 一、审计对象 1: PG 池泄漏归因文档 + vector_store 实例缓存修复

### 1.1 文档事实声明核对

**F1 [LOW] §2 行号声明 "L58-68: `_vector_store = PGVector`" 错误, 语义声明正确。**
- 证据: `git show 2f2739f:src/tools/vector_store.py | grep -n` → `15: _vector_store = None`、`136: def __dynamic_import():`、`143: _vector_store = PGVector`; 更早版本 d5e57ec 中该赋值在 L106。任何近期版本均无 L58-68 命中（修复前该处为 SiliconFlowEmbeddings.__init__ 文档串）。
- 语义层面「全局 `_vector_store` 缓存的是 PGVector **类**而非实例」成立: 当前 `src/tools/vector_store.py:151`（`_vector_store = PGVector`）+ L244 每次调用 `vector_store = _vector_store(...)` 实例化。

**F2 [INFO] §2 "`get_vector_store()`（L193-238）" 基本准确, 代码摘录与修前实现语义一致。**
- 证据: `git show 2f2739f:src/tools/vector_store.py` awk 核对: def 在 L193, 函数体 L227-232 每次构造 `_vector_store(collection_name=..., connection=connection_string, embeddings=..., use_jsonb=True)`, L234 `return vector_store`, 无实例缓存、无 dispose（函数体止于 L237, L238 为空行, ±1 容差内）。**engine-per-search 结论成立。**

**F3 [LOW] §2 调用点角色标注两处颠倒（行号本身准确）。**
- 文档称 "`src/biz/rag_service.py` L172（search, 每条 M2 问答）/ L322·L337（ingest）"。
- 实测（`grep -n "def "` 定位所属方法）: L172 属 `ingest_file`（def L104, L172 为「4. 向量化入库」, 见 `src/biz/rag_service.py:160-183`）——是**入库**路径而非 "每条 M2 问答" 的 search; L322·L337 属 `smart_retrieve`（def L240, L332 注释「2.5 OCR 溯源类查询: 补一路 doc_type=ocr_table 的过滤检索」）——是**检索**路径而非 ingest。
- L232（ingest_parsed_blocks 内 add_documents）✓、L664（get_traceability 内, 文档未标角色）✓。
- 影响评估: 不改变归因结论——真正的每条问答检索热路径是 smart_retrieve L322/L337 + get_traceability L664 + hybrid_retriever（见 F4）, 全部"每调用新建实例", 结论方向反而被强化; 但文档把高频负载记在错误行上, 属事实性瑕疵。

**F4 [INFO] 调用点清单不完整（不影响结论与修复完备性）。**
- 文档仅列 rag_service 5 处; 全仓普查另有: `src/biz/rag_service.py:732`（compare_methods）、`src/tools/hybrid_retriever.py:232-233`、`src/storage/memory/episodic_memory.py:22`、`scripts/m1_rag_ingest.py:296`（delete_collection）、`scripts/archive/init_pgvector_db.py:129·234`。
- 关键: 全部生产调用点仅传 `collection_name`（无显式 embeddings）→ 全部走修复后缓存路径（见 F10）。

**F5 [INFO] §3 排除嫌疑三条全部成立, 行号两处精确命中。**
- `src/storage/chat_persistence.py:50` = `if _conn is None or _conn.closed:` 模块级单例复用 ✓（「每进程 1 条长连接, 有界非增长」成立）。
- `src/storage/memory/memory_saver.py:40` = `self._pool.close()` ✓; `:92` = `finally: conn.close()` ✓（两处行号逐行精确）。
- `src/storage/collaboration/db.py:46·53` `create_engine` 位于 `__init__`（def L21）内 ✓（非按请求新建）。

**F6 [INFO] §2 "三 MCP 进程 + 两 uvicorn worker" 声明属实。**
- `src/mcp_server/server.py`、`src/vision_mcp_server/server.py`、`src/tabular_mcp_server/server.py` 均存在（后两者在 src/ 顶层兄弟目录, 非 src/mcp_server/ 内）。
- knowledge_search 链路 ✓: `src/mcp_server/server.py:100-101` `@mcp.tool(name="knowledge_search")` → L9/L39 `get_rag_service_sync()` → rag_service 同一批调用点。
- §1 的连接数分布（45/55）、速率等属窗前运行时观测, 非静态代码可验项, 不作代码层判定。

**F7 [INFO] 泄漏机制经依赖源码实证（langchain-postgres==0.0.16, requirements.txt）。**
- `venv/lib/*/site-packages/langchain_postgres/vectorstores.py:438` `self._engine = create_engine(url=connection, ...)`（字符串连接时）; `:477` 构造期即 `self.create_tables_if_not_exists()`（`:506` `with self._engine.connect()` 实际开连接）。
- 坐实文档 §2 机制描述: 每实例独立 engine+池, 构造即开连接, 实例随请求丢弃后池内连接不释放 → idle 连接线性累积。

### 1.2 已提交修复审查（`git diff 2f2739f 07a7c16 -- src/tools/vector_store.py`, +22 行）

**F8 [INFO] 修复堵住根因, 缓存键语义正确。**
- `src/tools/vector_store.py:232-238` 查缓存 + `:250-253` setdefault 入缓存, `threading.Lock`（L24）护竞态; 缓存键 `(collection_name, connection_string)`（L233）。
- connection_string 在 L228-229 **先解析**（None → `__get_connection_string()`）再参与键计算 → 键语义稳定, 无 None/实值双键问题。
- 键不含 embeddings: embeddings=None 路径经 `get_embeddings()` 模块单例（L196 返回 `_embeddings_client`）, 实例间共享同一 embeddings, 无歧义; `use_jsonb` 恒为 True 不入键亦无歧义。键空间 = 集合数 × 连接串数, 有界不增长。
- 文档 §4 称 "~15 行单文件", 实际 +22 行（含 4 行注释）, 量级相符。

**F9 [LOW] 竞态窗口存在但已声明接受; 一处注释措辞不准。**
- check（L234-238）与 setdefault（L250-253）之间隔着**无锁构造段**（L243-249）: 并发首查双 miss 时会构造两个 PGVector 实例, 败者亦会执行 `create_tables_if_not_exists()`（F7 实证开连接）后被丢弃——败者连接随 CPython 引用计数即时回收。与文档 §4 自评「竞态最坏短暂双实例」一致, 属已接受风险。
- 措辞瑕疵: L252 注释「避免重复 engine」不准——setdefault 只决定哪个实例入缓存, 重复 engine 此时已构造完成, 只是不入缓存/不被使用。

**F10 [INFO] 显式 embeddings 旁路设计正确, 泄漏残留面已查清。**
- `src/tools/vector_store.py:232` `use_cache = embeddings is None`, L231 注释说明理由（避免实例误用）。
- 全仓唯一显式传 embeddings 的调用点: `scripts/archive/init_pgvector_db.py:129`（归档初始化脚本）→ 未修复的泄漏路径仅存于归档场景, 非生产热路径, 属合理取舍。

**F11 [INFO] 文档 §5 验收项 ① 已落地为单测。**
- `tests/test_window_fixes_20260823.py:88-107` `test_vector_store_instance_cache`: 同键 `a is b` + 仅构造 1 次（`len(created) == 1`）+ 异键隔离（`c is not a`）; `pytest --collect-only` 5/5 收集成功。与提交记录 "379→384 (+5)" 一致。

### 对象 1 结论: **PASS**
（归因语义声明、机制、排除项、修复方向全部经代码/依赖源码实证成立; 两处 LOW 为文档行号错引与调用点角色标注颠倒, 一处注释措辞不准, 均不动摇结论; 修复正确堵住根因, 残余竞态为文档自评已接受项。）

---

## 二、审计对象 2: FK adapter 修复草稿 vs 已提交代码

### 2.1 菜单 a diff 逐字逐语义对照（草稿 §1 vs `git diff 2f2739f 07a7c16 -- src/biz/opencode_adapter.py`）

**F12 [INFO] 语义 100% 一致; 记录全部 4 处措辞/位置偏离（均无语义影响）。**
- a) **位置**: 草稿将 `+ completed = False` 置于 `session_id: Optional[str] = None` 行**之前**; 提交代码置于其**后**（`src/biz/opencode_adapter.py:163-164`）。两者均在 `try:` 之前, 语义等价。
- b) **新增注释**: 提交代码在 completed 行追加行内注释 `# [FK 修复·菜单 a 2026-08-23] 仅确认完成的 run 才删 session`（草稿无）。
- c) **keep 分支注释措辞**: 草稿 `# [FK 修复·菜单 a] 超时/异常不删: ... 留给侧车跑完, 水位闸门兜底`; 提交代码（L199-201）追加日期 "2026-08-23"、明确写出 `cleanup_sessions()`、重排换行并加句号。语义相同。
- d) **日志消息措辞**: 草稿 `"opencode session %s kept (run may be in flight)"`; 提交代码（L202）追加后缀 `"; FK-fix menu a"`。
- 其余逐字一致: `completed = True` 插入点（草稿 `_parse_structured` 后 = 提交 L184）、except 分支 `logger.warning("opencode ask failed (%s); fallback", exc)`（= L192）、finally 结构均吻合。

### 2.2 特别核查项

**F13 [INFO] compaction 守卫路径与异常路径都走保留分支 ✓。**
- compaction 守卫: `src/biz/opencode_adapter.py:180-182` 在 `completed = True`（L184）**之前** `return None` → completed 保持 False → finally 走 keep 分支（L198-202）✓。
- 异常路径: L191-193 `except Exception` → return None, completed=False → keep 分支 ✓（`httpx.TimeoutException` 为 Exception 子类）。
- 补充: 未被捕获的 BaseException（KeyboardInterrupt 等）同样经 finally 以 completed=False 走保留分支, 行为更安全; `delete_session`（L59-63）自身吞异常, completed=True 分支不会因删除失败抛入 keep 分支。

**F14 [INFO] finally 内水位闸逻辑逐字不变 ✓。**
- 提交代码 L203-207 ≡ 草稿 §1 上下文行: `try: if len(list_sessions()) > MAX_SESSIONS: cleanup_sessions() except Exception: pass`, 位于 `if session_id:` 内、completed 两分支之外 → 成功/保留两路均触发, 与修前行为一致。

**F15 [INFO] 草稿宣称的残余风险与 `cleanup_sessions` 实现一致 ✓。**
- `src/biz/opencode_adapter.py:71-76`: 按 `_updated_key`（time.updated, 缺省回落 time.created, L66-68）降序排序保留前 `max_keep`=MAX_SESSIONS（L27 缺省 50）个, 删除其余 = **删最旧**, 与草稿 §1 描述吻合。
- 长寿在途 run 的 session 若运行期间 `time.updated` 不刷新, >50 积压时确会被误删 → 后果 = 该 run 重现 FK 失败（即原病灶, 但仅限极端积压）, 与草稿自评「概率低且后果=该 run 的 FK 噪声, 可接受」一致。

**F16 [INFO] 既有边缘情形（非本次修复引入）: session 创建成功但响应缺 "id" 键。**
- L166 `.json()["id"]` KeyError → session_id 保持 None → finally 整体跳过（不删、水位闸也不跑）, 产生孤儿会话。修前行为相同（`delete_session(session_id)` 同样在 `if session_id:` 内）, 水位闸会在后续任一成功 ask 时兜底。记录备查, 不计为本次偏离。

### 2.3 测试覆盖核对（草稿 §3.1 四类场景）

**F17 [LOW] 四类场景全部有对应单测, 但第 4 类断言弱于草稿措辞。**
- ① 成功路径 → delete_session 恰 1 次（monkeypatch httpx）: `tests/test_window_fixes_20260823.py:41-49` `deleted == ["sess-1"]` ✓（`_FakeHttpx` L26-38 即 monkeypatch httpx）。
- ② 超时路径不被删: L52-61, 使用真实 `httpx.TimeoutException` ✓ `deleted == []`。
- ③ compaction 守卫不被删: L64-72（`info={"agent": "compaction"}`）✓ `deleted == []`。
- ④ 水位闸 MAX_SESSIONS+1 → cleanup_sessions 删最旧: L75-85 存在, 但仅断言 `len(deleted) >= 1` 与 `"sess-1" not in deleted`, **未断言被删的恰为最旧会话**（按 fixture 数据应为 `deleted == ["0"]`）。删最旧排序逻辑属既有 `cleanup_sessions` 实现（F15 已核实）, 故不构成正确性缺口, 仅属断言强度低于草稿措辞; 建议补强为 `assert deleted == ["0"]`。
- 计数一致性: 4 场景 5 测试（+对象1 验收测试 1 个）= 提交记录 "379/13 → 384/13 (+5)" ✓; `pytest --collect-only` 5/5 收集通过。

### 对象 2 结论: **PASS**
（提交代码与草稿菜单 a 语义完全一致, 4 处偏离均为位置/注释/日志措辞且已逐条记录; 守卫路径、异常路径、水位闸三项特别核查全部通过; 残余风险声明与实现吻合; 四类单测场景齐备, 仅第 4 类断言强度略低于草稿措辞, 记 LOW。）

---

## 附注
- 本审计为只读: 未改任何代码/配置, 未写除本报告外任何文件（含 dispatch_log）, 未执行任何会落盘变更的命令（测试仅 `--collect-only`）。
- 修复提交另含 ③ M1_B4_LOG_PATH 随重启生效（`scripts/restart_m1_harness.sh` +18）与 logs/memory 文档更新, 不在本次两对象审计范围内, 未作判定。

总体结论: 两审计对象均 PASS——PG 池泄漏归因文档核心结论（类缓存非实例缓存、engine-per-search、排除项、修复菜单 a）经代码与依赖源码双重实证成立且已提交修复正确堵住根因（4 LOW: 行号错引、调用点角色标注颠倒、竞态注释措辞、水位测试断言偏弱, 均不动摇结论）; FK 菜单 a 提交代码与草稿语义零偏离（仅 4 处措辞/位置差异已记录）, 三类特别核查与残余风险声明全部吻合代码实现。
