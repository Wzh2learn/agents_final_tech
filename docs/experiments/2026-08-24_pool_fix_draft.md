# 池×GUC 修复补丁草稿（2026-08-24, 只草不应用, 待 :5050 窗口批准）

> 状态: 草稿 | 更新: 2026-08-24 | 取代/被取代: 无
> 依据: 2026-08-24_segment_d_q06_attribution.md 修复菜单 F1/F2; langchain-postgres 0.0.16 内部实查（`__init__` 支持 `engine_args` 透传 create_engine, L438; 引擎句柄 `._engine`）

## F1 · pre_ping + recycle（src/tools/vector_store.py, ~2 行）

```python
# get_vector_store 内构造处:
        vector_store = _vector_store(
            collection_name=collection_name,
            connection=connection_string,
            embeddings=embeddings,
            use_jsonb=True,
            # [池×GUC 修复 2026-08-24] GUC idle_session_timeout=10min 会杀长驻池 idle 连接,
            # 无 pre_ping 时首查抛 IdleSessionTimeout 被吞 → 兜底冒充检索 (归因报告)。
            # pre_ping: 检出即探活, 死连接透明重建; recycle=300s 先于 GUC 600s 主动回收。
            engine_args={"pool_pre_ping": True, "pool_recycle": 300},
        )
```

影响面: 所有经 get_vector_store 的消费方（:5050 两 worker / MCP 三进程 / eval 脚本）同参生效; 每 (collection, conn) 实例缓存不变, 每实例一个引擎池, 连接总数不变。
风险: 低（SQLAlchemy 标准参数）; 回滚 = 去掉 engine_args 重启。

## F2 · 异常不吞 + 重试一次 + 兜底显式（src/biz/rag_service.py smart_retrieve, ~20 行）

```python
# 原 (L321-330):
            try:
                vector_store = get_vector_store(collection_name=collection_name)
                results = vector_store.similarity_search_with_score(query, k=top_k)
                ...
            except Exception as e:
                logger.warning(f"Vector retrieve failed on {collection_name}: {e}")

# 改为:
            vector_store = get_vector_store(collection_name=collection_name)
            vector_failed = False
            try:
                results = vector_store.similarity_search_with_score(query, k=top_k)
                ...
            except Exception as e:
                logger.error(f"Vector retrieve failed on {collection_name}: {e}")  # WARNING→ERROR
                # 连接类故障: 弃池重试一次 (死连接 invalidate 后重建)
                try:
                    engine = getattr(vector_store, "_engine", None)
                    if engine is not None:
                        engine.dispose()
                    results = vector_store.similarity_search_with_score(query, k=top_k)
                    ...（同上收 doc）
                    logger.info(f"Vector retrieve recovered after dispose+retry on {collection_name}")
                except Exception as e2:
                    vector_failed = True
                    logger.error(f"Vector retrieve retry failed on {collection_name}: {e2}")
# 兜底段 (原 L367-375) 加标记:
            if vector_count == 0 and bm25_count == 0:
                fallback_docs = self._local_fallback_docs(...)
                for doc in fallback_docs:
                    doc.metadata["collection"] = collection_name
                    doc.metadata["fallback"] = True
                    if vector_failed:
                        doc.metadata["fallback_reason"] = "vector_retrieve_error"  # 兜底原因显式
                    all_docs.append(doc)
                if vector_failed and fallback_docs:
                    logger.error(f"Serving {len(fallback_docs)} FALLBACK docs as retrieval on {collection_name} (vector path broken)")
```

测试清单: ① 单测: mock similarity_search 抛 IdleSessionTimeout → 断言 dispose+重试调用 + fallback_reason 标记 ② 集成（窗口内）: 静置 >10min 后首问 = 正确命中（pre_ping 生效, 不再走兜底）③ 对照: 拔 PG 网线/停容器 → ERROR 级响亮失败不静默 ④ pytest 全绿。
回滚口径: git checkout 两文件 + 重启。

## 窗口执行序（批准后）

1 窗前存档（PID/env/inspect 级）→ 2 改两文件 → 3 :5050 重启（restart_m1_harness.sh SOP）→ 4 侧车重启（MCP 重生载修复）→ 5 验证: /api/health/full + 静置 12min 后 q06 直问（预期 0.7889 命中, 零新 WARNING）+ canary 一轮 + pg_stat_activity 贴底 → 6 B4 分段点"池修复后段"标记 + 恢复每日 eval 节奏（干净段开始攒数, 供超时 (a) 判定）
