# PG 池泄漏代码归因（2026-08-23 夜间队列任务 1）

状态: 归因定论 + 修复菜单（明日 :5050 代码窗直接执行） | 更新: 2026-08-23 | 取代/被取代: 无
关联: memory/THREADS.md [08-16 22:20] known_risk 条 / [08-23] PG 池打满事故条 / #HYG-FK-DIAG 同窗排期

## 1. 现象与速率（08-23 窗口实测）
- 修前: pg_stat_activity 100/100 饱和, 最老连接 5-7 天, 零回收。
- 归因普查（窗前 ss + 容器 peer 对账）: 100 连接 = mcp_server.server 45（08-22 14:37 起, ~29h, ≈1.5/h）+ :5050 uvicorn 两 worker 55（08-18 起, ~5d, ≈0.5/h）。Loop B 本体零连接。
- 速率与查询流量吻合: mcp 侧承载 canary + agent 路 knowledge_search（高频）, uvicorn 侧承载直连 ask（低频）。

## 2. 泄漏点定位（代码级坐实）
**主泄漏点: `src/tools/vector_store.py` `get_vector_store()`（L193-238）——engine-per-search。**

```python
# 全局 _vector_store 缓存的是 PGVector 类（L58-68: _vector_store = PGVector）, 不是实例
vector_store = _vector_store(            # 每次调用新建 PGVector 实例
    collection_name=collection_name,
    connection=connection_string,        # → 新 SQLAlchemy engine + 连接池
    embeddings=embeddings, use_jsonb=True,
)
return vector_store                      # 无实例缓存, 无 dispose
```

热路径调用方（每次检索新建一个 engine）:
- `src/biz/rag_service.py` L172（search, 每条 M2 问答）/ L232（add_documents）/ L322·L337（ingest）/ L664
- `src/mcp_server/server.py` knowledge_search 工具 → `get_rag_service_sync()` → 同上
- 三 MCP 进程（mcp_server/vision_mcp_server/tabular_mcp_server）与两 uvicorn worker 各自累计

机制: langchain_postgres.PGVector 构造时按 connection 串创建独立 engine（自带连接池）; 实例随请求丢弃, 池内已开连接永不释放 → idle 连接按请求数线性累积, 直到 PG 重启。

## 3. 排除的嫌疑
- `src/storage/chat_persistence.py`: 模块级 `_conn` 单例（L50 复用未关闭连接）——每进程 1 条长连接, 有界非增长（即 08-16 last_q「chat_sessions 心跳 + ROLLBACK」的来源, 不构成打满）。
- `src/storage/memory/memory_saver.py`: conn 用完 close（L92）, pool 有 close（L40）——卫生。
- `src/storage/collaboration/db.py`: engine 在 __init__ 单例化（非按请求）——不在热路径按请求新建。

## 4. 修复菜单（明日代码窗）
| 项 | 方案 | 改动量 | 风险 | 判定 |
|---|---|---|---|---|
| a | **实例缓存（推荐）**: get_vector_store 内按 (collection_name, connection_string) 缓存实例, threading.Lock 护竞态 | ~15 行单文件 | 低——engine 池本就为并发复用设计; 竞态最坏短暂双实例 | 首选 |
| b | 共享 engine 注入: 模块级单 engine（pool_pre_ping=True）传入 PGVector | 中 | 需验证 langchain-postgres 版本接受 engine 对象 | 备选 |
| c | NullPool: 每请求开关连接, 零闲留 | 小-中 | 每检索 +毫秒级重连开销; 依赖构造器支持 | 备选 |
| d | 不动代码, GUC 10min 兜底（已部署） | 0 | 泄漏继续但有界 | 已生效的底线 |

## 5. 验收与回滚
- 验收: ① `get_vector_store() is get_vector_store()` 同实例断言（新增单测） ② 修复后连跑 canary 3 轮, pg_stat_activity 连接数零增长 ③ pytest 379/13 + eval 16 题零漂移。
- 生效面: 代码改动同时影响 :5050（需重启窗）与三 MCP 进程（sidecar 重启即重生, 08-22 低风险先例在案）。
- 回滚: git revert 单 commit + 原参数重起 :5050 / 重启 sidecar, ~31s 口径。
