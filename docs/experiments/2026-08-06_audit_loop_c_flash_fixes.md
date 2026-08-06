# Loop C 审计 — flash 首任务 + 死锁/代理隔离修复 + A2 灰度配置

- **审计时间**: 2026-08-06 22:52 (CST)
- **审计执行**: Loop C (qwen3.8-max 槽位, Claude Code, reasoning xhigh)
- **审计对象**:
  1. `62d21e3` fix(m2-qa): sources 遵从度加固 (flash 首任务, DECISIONS.md「切换后首任务重点审计」条款触发)
  2. `cf5df3d` fix(m2): RLock 自死锁 + compare-intent 绕过灰度 + L5 hook 收窄
  3. `a9ddfc4` fix(opencode_adapter): trust_env=False 代理隔离
  4. A2 灰度配置面: `.env` / `src/web/routers/m2.py` / `opencode.json` / `src/biz/opencode_adapter.py`
- **方法**: 独立 git show 全量 diff 核验 + HEAD 文件直读 + 历史溯源 (git log/follow) + 静态正则推演; 未轻信任务描述。
- **执行限制 (如实披露)**: 本会话 pytest 执行被权限系统拦截 (未获批), 未能亲跑测试套件; 测试结论采信 HEAD `62d21e3` 处的 Loop B 独立验证报告 (`logs/graph/verify-report.json`, pytest exit_code=0 PASS) + dispatch_log 22:33 记录 (261 passed/13 skipped/0 failed)。静态核验范围内未发现记录与代码矛盾。

---

## 判定: **CONDITIONAL**

三个修复本身均正确、范围收敛、声明与 diff 逐条吻合, 且回落路径有真实故障实证 (22:33 sidecar 停摆事件静默降级, 演示无损)。不给 ACCEPTED 的原因: ① cf5df3d 的 commit message 声称 "regression tests", 但 compare-intent 绕过这一行为变更**没有**接线级回归测试 (只有锁回归); ② 问题 (a) 所指的锁内 PG 阻塞 I/O 且**无任何超时**的风险确实存在, RLock 只是解了自死锁并使该路径在灰度下更易触达, 需闭环 (加固或显式入账)。两项闭环完成后可转 ACCEPTED, 不阻塞当前灰度运行。

---

## 一、逐 commit 核验

### 1. `62d21e3` — m2-qa sources 遵从度 (flash 首任务) ✅ 描述属实

| commit message 声明 | 独立核验 | 结论 |
|---|---|---|
| opencode.json m2-qa.prompt 内嵌 JSON 契约 + 完整示例 | diff 证实; HEAD opencode.json 为合法 JSON, 契约含 `{answer, sources[{sample_id,table_name,field}]}` 结构示例 + "sources 非空" + 显式拒绝条款 (sources:[]) | ✓ |
| `_FORMAT_HINT` 禁 markdown 围栏/列表, 要求 sources 非空 | `opencode_adapter.py:30-37` 证实 | ✓ |
| `_extract_cited_sources` 保守兜底, "never fabricate" | `opencode_adapter.py:93-141`; 静态推演见 findings F3 (字面义成立, 有窄边界残留) | ✓ (附 F3) |
| 6 新单测, 共 15 | diff 新增恰 6 个 test 函数; 文件现存 15 个 test (9 旧 + 6 新) | ✓ |
| 261 passed/13 skipped, 基线 255/13 | 采信 verify-report.json (RC=0); 254/14→261/13 的差异 = 6 新测试 + 1 个环境依赖 skip 转 pass (PG/:5050 在跑时 skipif 解除), 无异常 | ✓ (F8) |

### 2. `cf5df3d` — RLock + compare 绕过 + hook 收窄 ⚠️ 修复正确, 测试声明过宽

- **RLock**: `m2_service.py:55` `threading.Lock()→RLock()`。死锁机理复核成立: `get_history` (L112 持锁) → `_get_session` (L67 再取同锁), 非重入锁必死锁; 直连路径 `m2_ask→_get_session` (L382) 不带外层锁所以此前幸存, opencode 路由是首个从持锁入口调 `_get_session` 的路径 → 与 "opencode route froze workers" 的事故面吻合 (dispatch 02:00 记载 Loop B 01:36 FAIL 正是死锁期报警)。修复为最小正确修复。
- **compare 绕过**: `routers/m2.py:86` `route_enabled() and not detect_compare_intent(q)`; `_COMPARE_TRIGGERS` 8 个触发词 (L449); `detect_compare_intent` 单测在 `test_m2_compare.py` 有 7 例 ✓, 但**接线级测试缺失** → F2。
- **L5 hook 收窄**: `scripts/graph/hooks/pre-commit` 与 `.git/hooks/pre-commit` **逐字节一致** (diff 验证); 冻结清单 `frozen_hashes.txt` 含 `test_m1_service.py` (faa7565a) + schema json; 收窄口径 (单文件而非 ^tests/) 与 dispatch T3 记载一致。
- **锁回归测试** 4 个, deadline-join 策略有效; 小瑕疵: `test_lock_is_reentrant` 的 isinstance 断言带 `hasattr` 兜底恒真, 真实证明力在 nested-acquire deadline 部分。

### 3. `a9ddfc4` — trust_env=False ✅ 完整

- `opencode_adapter.py` 全部 6 处 httpx 调用逐一核验, **无遗漏** (grep httpx 排除 trust_env=False 后为空)。
- 动机成立: clash `all_proxy=socks*` 类环境变量会让 httpx 走环境代理解析, 对 `http://127.0.0.1:4096` 的 socks 代理解析可抛 ValueError → 健康检查恒 False → sidecar 被误判不健康, 灰度静默失效。trust_env=False 是正解。
- 测试侧仅把 mock 放宽为 `**k` 接收, **没有**任何断言锁定 trust_env 传参 → F4。

---

## 二、A2 灰度配置审查

| 项 | 实况 | 结论 |
|---|---|---|
| `.env` 开关 | `M2_OPENCODE_ROUTE=on`; **`OPENCODE_ASK_TIMEOUT=18`** (注意: 非任务书所写的 90; 90 是代码默认, 部署值 18) | ⚠️ F7 |
| `.env` 加载链 | `src/utils/config_loader.py` dotenv 载入; `.env` 未入 git (仅 `.env.example` 入库) → 18s 调整不受版本控制 | INFO |
| 路由门 | `m2_ask_endpoint` (async def) 内: 开关 + compare 绕过 → opencode, 返回 None 落直连; 成功路径 `append_turn` 双写历史 | ✓ (附 F5) |
| opencode.json m2-qa 权限 | `edit/bash deny, jinrong-rag_* allow, vision/tabular deny` ✓; 但 "仅 jinrong-rag allow" 表述过强: read/grep/glob/webfetch 未显式 deny, 全局 `skill: allow` 被继承, `mode: all` | ⚠️ F6 |
| adapter 超时/回落 | health 3s / create 10s / message=ASK_TIMEOUT / delete 10s / list 10s, 全部有界; 异常一律 return None → 直连; finally 删会话 + orphan>50 时级联清理 | ✓ (附 F5) |

---

## 三、重点问题回答

### a) RLock 后锁内阻塞 I/O 隐患? — **存在, MEDIUM**

`_get_session` 在 `_sessions_lock` 内调 `pg_load_messages` + `persist_session_create` (`m2_service.py:79-83`); `append_turn→_append_history→persist_message` 同样在锁内 (L118-119 + L94-95)。嵌套锁序为 `_sessions_lock → _conn_lock` (chat_persistence), 未发现反向, 无锁序死锁; 但 `chat_persistence.py` 的 `psycopg.connect(url, autocommit=True)` **无 connect_timeout、无查询超时** — 对照同仓 `memory_saver.py:60` 已有 `connect_timeout=DB_CONNECTION_TIMEOUT` 先例, 此处遗漏。PG 挂起 (非宕机) 时, 首个触达线程无限期阻塞并持有全局锁 → 两 worker 依次触雷后 :5050 整体 (含 /health) 无界挂死。宕机/拒连场景则快速异常优雅降级。此为 Phase 3 (`1a105bf`) 遗留, 非本次引入; RLock 使其在灰度路径下更易触达。**闭环项 ①**。

### b) `_extract_cited_sources` 会虚构来源吗? — 正则本身不会, 有窄边界残留, LOW

静态推演: ① 必须有 `样本[:：]/sample_id[:：]/样本=` 前缀 + `sample_` 字面量才命中, 裸 `sample_xxx` 不提取 (有对应负例测试 ✓); ② JSON 键语法 `"sample_id": "sample_x"` 因引号隔断不会被误匹配; ③ 显式拒绝 JSON (sources:[]) 走 JSON 分支不进兜底 ✓。残留: **echo 场景** — 模型在非 JSON 文本里复述 system prompt 的契约示例 (恰含真实 `sample_fuxi_hunhe25`) 时, 兜底会把示例样本当来源提取 ("never fabricate" 在 "不出文本所写" 的字面义上成立, 但文本本身可以是鹦鹉学舌的幻觉); 另有 trailing-dot 捕获 (`样本: sample_abc.` → `sample_abc.` 带点)。无测试覆盖 echo 负例。**闭环项 ③ 的一部分**。

### c) sidecar 故障模式下直连回落无损吗? 有无挂死单点? — 回落无损且有实证; 挂死风险不在 sidecar 侧而在 PG 侧

- adapter 所有 httpx 调用均有显式 timeout → **adapter 内无无界挂死**。sidecar down (拒连) / 健康超时 / create 超时 / message 超时 / 400 重试, 全部收敛到 return None → 直连, 最坏前置延迟 ≈ 3+10+18 (env 值; 默认 90 则 ~133s) + finally delete/list 20s ≈ **51s (env)**。
- **实证**: 22:33 `#SIDECAR-DOWN` 记录 — opencode serve 停摆 (defunct, :4096 无监听) 期间 :5050 按设计静默降级直连, 演示无损; 2s 重建恢复。这是回落路径的真实故障演练, 非仅测试桩。
- 病态尾巴: orphan>50 且 sidecar 恰在 finally 阶段失联时, 级联清理最坏 50×10s ≈ +500s (有界但长)。
- **放大器**: 端点是 `async def` 而 adapter/直连 LLM 均为同步阻塞调用 (该模式自端点诞生即存在, 非本次回归), 上述秒数会阻塞事件循环; `--workers 2` 下两个并发卡住即可让 :5050 全停 (含健康检查) 相应时长。→ F5。
- 真正的**无界**挂死单点是 (a) 的 PG-stall 模式 (psycopg 无超时), 不是 sidecar 模式。

### d) 测试覆盖充分吗? — 主路径充分, 4 个缺口

已覆盖 (有效断言): 兜底提取正/负例 ×5、JSON 优先于兜底、FORMAT_HINT 契约钉住、锁死锁回归 ×4 (deadline 策略)、路由开/关/回落 ×3、trust_env 后 mock 兼容。
缺口:
1. **compare 绕过接线** (F2, MEDIUM-LOW): 无 "route=on + 对比类问题 → 走直连且不调 opencode" 的测试; 路由测试桩把 `detect_compare_intent` 硬编码为 `lambda q: False`, 恰把被测分支屏蔽了。
2. **trust_env 无守卫** (F4): mock 收 `**k` 不校验, 回退 trust_env 不会红。建议任一 post mock 断言 `k.get("trust_env") is False`。
3. **显式拒绝 JSON (sources:[]) 透传**无独立测试 (代码路径正确, 但这是契约关键态)。
4. **echo 虚构负例** (F3) 无测试。
hook 收窄无自动化测试, 但 T3 drill (dispatch 01:57) 双 case 实测 + 本次文件一致性 diff 补足, 可接受。

### e) flash 首任务代码质量 (相对其历史水位)? — 无退化迹象, 判 PASS

以可核查口径评估: ① diff 收敛 (+120/−3, 3 文件), 零越界 (未触冻结节点, verify-report frozen_nodes PASS); ② commit message 逐条声明均与 diff/HEAD 实物吻合, 无虚报; ③ 修复分层合理 — prompt 契约 (最便宜可逆) → FORMAT_HINT → 确定性兜底 (最后防线), 优先级排序是工程判断而非堆料; ④ 测试断言具体 (断提取值而非不崩溃); ⑤ 817s RC=0, 一次通过。相对 flash 级模型的预期水位属上佳; DECISIONS.md 回滚标准三条件 (连续失败/冻结异常/成本不降) 无一触发, **支持保留 flash 于 Loop A 槽位**。

---

## 四、Findings 汇总

| # | Severity | 位置 | 摘要 |
|---|---|---|---|
| F1 | **MEDIUM** | `m2_service.py:79-83,94-95,118-119` + `chat_persistence.py:46` | 全局锁内 PG I/O 且 psycopg 无任何超时 (对照 memory_saver.py:60 有先例); PG 挂起 → :5050 无界挂死。Phase 3 遗留, 灰度放大暴露面 |
| F2 | MEDIUM-LOW | `routers/m2.py:86` / tests | compare-intent 绕过无接线级回归测试; commit message "regression tests" 声明过宽 (仅锁回归) |
| F3 | LOW | `opencode_adapter.py:93-127` | echo 提示词示例 → 兜底提取示例样本; trailing-dot 捕获; 均无负例测试 |
| F4 | LOW | tests/test_opencode_adapter.py | trust_env=False 无断言守卫, mock `**k` 吞掉回归 |
| F5 | LOW | `routers/m2.py:83-99` (async def + 同步调用) | 最坏 51s (env) ~133s (默认) 阻塞事件循环, 病态清理级联 +500s; workers=2 仅部分缓解。既有模式, 非本次回归 |
| F6 | INFO | `opencode.json` m2-qa | 隔离表述 "仅 jinrong-rag allow" 过强: read/grep/glob/webfetch 未显式 deny, skill 全局 allow 被继承; 建议严格化或改台账表述 |
| F7 | INFO | `.env` (未入库) | 部署值 `OPENCODE_ASK_TIMEOUT=18` < 实测 agent 多步时延 70s (STATE.md L6) → 慢问题必超时回落, 灰度对复杂问题实质失效; 需确认 18 是否有意, 无意则回调 |
| F8 | INFO | 测试计数 | 254/14→261/13 差异可由 6 新测试 + 1 个环境依赖 skip 解除解释, 无异常 |

---

## 五、闭环项 (CONDITIONAL 条件)

1. **F1**: `chat_persistence` 增加 `connect_timeout` + 查询级超时 (对齐 memory_saver 先例), 或将 PG I/O 移出 `_sessions_lock`; 若决定不修, 须在 STATE/THREADS 显式入账为 known_risk 并注明触发条件与影响面。
2. **F2**: 补接线级测试 — route=on + `detect_compare_intent→True` 桩 → 断言走直连且 `ask_via_opencode` 未被调用。
3. **F3+F4**: 补 trust_env 断言 + 显式拒绝 JSON (sources:[]) 透传测试 + echo 负例; 顺手 strip sample_id 尾部 `.`。

> 建议执行方: 闭环项体量小 (预计 <30min), 可仍由 flash 执行, 完成后 Loop C 复核转 ACCEPTED。
> 不阻塞项: 当前灰度 (route=on) 可继续运行; F7 请 Loop D/运维确认 18s 意图。

---

## 六、证据链

- `git show` 全量 diff: 62d21e3 / cf5df3d / a9ddfc4; 溯源 a438f0d (A1 基线, async 端点既存)、1a105bf (Phase 3 persistence 基线)
- HEAD 直读: `src/biz/opencode_adapter.py` (195 行全文)、`src/web/routers/m2.py` (全文)、`src/biz/m2_service.py` (L26-135, L449, L695-729)、`src/storage/chat_persistence.py` (全文)、`opencode.json` (全文)、`.env`、`scripts/run.sh` (workers=2)、`scripts/graph/hooks/pre-commit` + `.git/hooks/pre-commit` (diff 一致)、`scripts/graph/frozen_hashes.txt`
- 旁证: `logs/graph/verify-report.json` (Loop B, head 62d21e3, PASS)、`logs/graph/dispatch_log.md` (01:55 灰度验证 / 01:58 回滚演练 23s / 02:00 hook drill / 22:33 flash PASS + SIDECAR-DOWN 实证降级)、`memory/STATE.md` L6、`memory/DECISIONS.md` L105-110 (flash 切换 + 回滚标准 + 本审计授权)
- 限制: 未亲跑 pytest (权限拦截); 未运行 python 动态探针 (权限拦截), b/c 的推演为静态分析
