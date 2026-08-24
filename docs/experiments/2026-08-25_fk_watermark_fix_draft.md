# FK 水位闸边界修复草稿（只草不改码, 2026-08-25 夜间队列 W6.1）

> 状态: 草稿待批 | 更新: 2026-08-25 | 实施挂下个 :5050 窗口（推荐与池修复观察期后合并）
> 根因台账: THREADS "FK 竞争"条（08-11 起）+ 08-24 窗口卡; 最新事件 08-25 08:14 新增 1 条（日均 1 条级边角）

## 1. 根因（代码级, 已核当前码）

`src/biz/opencode_adapter.py`:
- L201-205（菜单 a 超时不删路径的 finally）: 超时/异常会话保留（侧车 run 可能在途）, 随后 `if len(list_sessions()) > MAX_SESSIONS(50): cleanup_sessions()`
- L71-76 `cleanup_sessions(max_keep=50)`: 按 `time.updated` 排序, 删除第 50 名之后**全部**, 无在途/新近保护
- 冲突: 第 51+ 名恰为在途会话时, 删父 session → 侧车在途 part/message INSERT 触发 FK 失败 + transcript 丢失

## 2. 修复菜单

### 菜单 a（推荐）: 新近活跃豁免
cleanup_sessions 增加 `min_idle_s` 豁免: 只删 updated 距今 ≥120s 的超编会话（120s = 45s 超时 + 侧车收尾余量, env 可调）。
```diff
--- a/src/biz/opencode_adapter.py
+++ b/src/biz/opencode_adapter.py
@@
 MAX_SESSIONS = int(os.environ.get("OPENCODE_MAX_SESSIONS", "50"))
+CLEANUP_MIN_IDLE_S = float(os.environ.get("OPENCODE_CLEANUP_MIN_IDLE_S", "120"))
@@
-def cleanup_sessions(max_keep: int = MAX_SESSIONS, purge_all: bool = False) -> dict[str, int]:
-    """Delete every session (purge_all) or the oldest ones beyond max_keep."""
-    sessions = list_sessions()
-    doomed = sessions if purge_all else sorted(sessions, key=_updated_key, reverse=True)[max_keep:]
-    deleted = sum(1 for s in doomed if delete_session(str(s.get("id", ""))))
-    return {"before": len(sessions), "deleted": deleted, "kept": len(sessions) - len(doomed)}
+def cleanup_sessions(max_keep: int = MAX_SESSIONS, purge_all: bool = False,
+                     min_idle_s: float = CLEANUP_MIN_IDLE_S) -> dict[str, int]:
+    """Delete every session (purge_all) or the oldest ones beyond max_keep.
+    [FK 边界修复 2026-08-25] 超编删除跳过近 min_idle_s 内活跃过的会话,
+    防止删掉侧车在途 run 的父 session (FK 失败 + transcript 丢失)。"""
+    sessions = list_sessions()
+    if purge_all:
+        doomed = sessions
+        skipped_recent = 0
+    else:
+        now = time.time()
+        over = sorted(sessions, key=_updated_key, reverse=True)[max_keep:]
+        doomed = [s for s in over if now - _updated_key(s) >= min_idle_s]
+        skipped_recent = len(over) - len(doomed)
+    deleted = sum(1 for s in doomed if delete_session(str(s.get("id", ""))))
+    return {"before": len(sessions), "deleted": deleted,
+            "kept": len(sessions) - len(doomed), "skipped_recent": skipped_recent}
```
（需确认文件已 `import time`; web/routers/m2.py L169 管理端点签名兼容, 新参有默认值。）

- 收益: 在途会话不再被水位闸误删; 超编仍被治理（只豁免新近, 下一轮自然回收）。
- 风险: 高并发下会话数短时超过 50+豁免数（无上限风险低: 侧车并发 ≤2-3, 豁免窗口 120s）。

### 菜单 b（备选, 可与 a 叠加）: 高低水位滞回
触发线 50→60, 清理目标 40（一次删够, 降频 50%+）。改 L204 阈值 + cleanup 删到 low_water。
- 收益: 清理频率降; 风险: 峰值会话数更高（60）, 单独不解决在途误删 → **不单独采用**。

## 3. 测试清单
1. 单测（新增）: mock list_sessions 55 条, 2 条 updated=now-10s → cleanup 后 deleted=3, skipped_recent=2, 新近 2 条仍在
2. 回归: `pytest tests/ -k "cleanup or opencode" -q` 全绿
3. 全量: `pytest tests/ -q` 384 passed 基线不破
4. 手工（窗口内）: 构造 51+ 会话（脚本灌假 session 或等自然积累）触发清理, opencode.log 观察 24h 零新 FK 行
5. 管理端点: /api/m2/cleanup（m2.py L169）带默认参调用一次, 返回含 skipped_recent 字段

## 4. 回滚口径
`git checkout src/biz/opencode_adapter.py` + `bash scripts/restart_m1_harness.sh`（~31s, env 45/on 不变, 无配置变更）; 单文件改动, 回滚零残留。

## 5. 验收（实施窗口用）
- [ ] diff 与本草稿逐字一致（或差异已记账）
- [ ] 测试清单 1-3 过
- [ ] 验收清单模板三列贴实测
- [ ] dispatch 一行 + THREADS FK 条转"修复已上线, 观察 48h"
