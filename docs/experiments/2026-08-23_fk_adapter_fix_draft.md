# FK adapter 修复补丁草稿（2026-08-23 夜间队列任务 2 · 只草不应用）

状态: 草稿待窗（明日 :5050 代码窗执行） | 更新: 2026-08-23 | 取代/被取代: 无
关联: memory/THREADS.md #HYG-FK-DIAG（根因定论）/ 2026-08-23_pg_pool_leak_attribution.md（同窗）

## 0. 病灶回顾（诊断坐实, 见 #HYG-FK-DIAG）
`src/biz/opencode_adapter.py` `ask_via_opencode()` finally 块无条件 `delete_session(session_id)`：
超时/异常回落后侧车 run 仍在途, 父 session 被删 → 在途 part/message 插入 FK 失败（累计 2824 条）+ transcript 零持久化。

## 1. 菜单 a —— 超时不删（成功才删, 推荐, 最小改动）

```diff
@@ ask_via_opencode() @@
+    completed = False
     session_id: Optional[str] = None
     try:
         ...
         answer, sources = _parse_structured(_extract_text(payload))
+        completed = True
         return {
             "answer": answer,
             ...
         }
     except Exception as exc:
         logger.warning("opencode ask failed (%s); fallback", exc)
         return None
     finally:
         if session_id:
-            delete_session(session_id)
+            if completed:
+                delete_session(session_id)
+            else:
+                # [FK 修复·菜单 a] 超时/异常不删: 侧车 run 可能在途, 删父 session 致
+                # 在途 part/message FK 失败 + transcript 丢失; 留给侧车跑完, 水位闸门兜底
+                logger.info("opencode session %s kept (run may be in flight)", session_id)
             try:
                 if len(list_sessions()) > MAX_SESSIONS:
                     cleanup_sessions()
             except Exception:
                 pass
```

要点: 成功路径（含结构化解析完成）立即删, 行为不变; 失败/超时/compaction 守卫路径一律不删;
会话水位由既有 `cleanup_sessions()`（>MAX_SESSIONS=50 删最旧）兜底, 无新增后台部件。
残余风险: 水位清理删最旧时可能误删长寿在途 run（>50 会话积压时）, 概率低且后果=该 run 的 FK 噪声, 可接受。

## 2. 菜单 b —— 清理异步化（延迟删, 备选）
失败路径不立即删, 记入延迟队列, 后续调用顺带清过期项（无后台线程）:

```python
_PENDING_DELETE: dict[str, float] = {}
_DELETE_DELAY_S = 180.0  # > 孤儿续跑 p95=133s（L2 实测）, 留余量

def _flush_pending_deletes() -> None:
    now = time.monotonic()
    for sid in [s for s, t in list(_PENDING_DELETE.items()) if now - t >= _DELETE_DELAY_S]:
        if delete_session(sid):
            _PENDING_DELETE.pop(sid, None)
```
finally 失败分支改 `_PENDING_DELETE[session_id] = time.monotonic()`, 函数入口调 `_flush_pending_deletes()`。
比 a 多保「会话终被清」语义, 多一个模块状态与时间参数, 复杂度中。

**推荐序: a 先行（一处条件分支）; a 观察 24h 无会话积压异常即终态, b 留后备不实施。**

## 3. 测试清单（窗口内跑）
1. 单测新增（tests/ 下, 冻结清单允许新增普通测试——T4 门禁先例）:
   - 成功路径 → delete_session 恰被调 1 次（monkeypatch httpx）;
   - 超时路径（httpx.TimeoutException）→ 该 session 不被删;
   - compaction 守卫路径 → 不被删;
   - 水位闸: MAX_SESSIONS+1 个会话 → cleanup_sessions 删最旧。
2. 集成验收（真窗口）: 制造一次超时回落（或用既有超时题）→ GET /session 列表仍含该 id;
   等孤儿跑完 → opencode.db session/part/message 三表行数 >0（「零持久化」代价解除的直接证据）。
3. 回归: pytest 全量 379/13 基线 + canary 4/4 + opencode.log 观察 1h `grep -c 'FOREIGN KEY'` 零新增。

## 4. 回滚口径
git revert 单 commit + :5050 原参数重起（~31s）; sidecar/模型/配置零牵连。
与同窗他项（PG 池泄漏修复 / M1_B4_LOG_PATH / 可能的超时 a）独立可回滚, 逐项记切换点。
