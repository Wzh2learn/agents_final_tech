# Loop C — T1 闭环复核 (c5a8ecf) + T2 Differential Review (4a151dd..HEAD)

- **时间**: 2026-08-07 00:15 (CST)
- **执行**: Loop C (审计层, 独立视角)
- **对象**:
  - Part 1 (T1): `c5a8ecf` 闭环交付逐条复核 → ACCEPTED 转换判定
  - Part 2 (T2): `4a151dd..HEAD` 全量增量 (35 commits, 104 文件, +2578/−218)
- **方法**: git show/diff 全量核验 + HEAD 直读 + **本轮亲跑 pytest** (权限已放开) + **动态探针** (PG 超时实测/变异测试) + 子代理并行外围扫描。不轻信 commit message。
- **基线**: 4a151dd = Phase 3 全量审查报告入库点。

---

## Part 1 — T1 复核: 判定 **ACCEPTED** ✅

### 0. 测试基线 (亲跑, 非采信)

```
PYTHONPATH=src ./venv/bin/python -m pytest -q
→ 266 passed, 13 skipped, 0 failed, 71.41s   (HEAD c5a8ecf)
```

与 c5a8ecf commit message 声明 (266/13/0) 逐字吻合。增量 = 62d21e3 基线 261 + 5 个新闭环测试, 计数自洽。新增 5 测试单独运行亦全绿 (0.09s)。

### 1. 逐条判定

| # | 闭环项 | 判定 | 证据摘要 |
|---|---|---|---|
| F1 | PG 超时加固 | **VERIFIED** | 见 §1.1 |
| F2 | compare 绕过接线测试 | **VERIFIED** (含变异测试证明非桩遮蔽) | 见 §1.2 |
| F3 | trailing-dot strip + echo 负例 | **VERIFIED** | 见 §1.3 |
| F4 | trust_env 断言守卫 + sources:[] 透传 | **VERIFIED** (附 1 项 INFO 残留) | 见 §1.4 |
| F6 | opencode.json 显式 deny | **VERIFIED** (附 1 项 INFO 残留) | 见 §1.5 |

#### 1.1 F1 — PG 超时: VERIFIED (动态实证, 非静态推演)

代码: `src/storage/chat_persistence.py:31-36,53-58`。

- **参数正确性 (psycopg 3.3.0)**: `connect()` 签名 `**kwargs: ConnParam` 透传 libpq 参数; `connect_timeout` (秒) 与 `options="-c statement_timeout=<ms>"` 均为合法 libpq 连接参数。已验证 psycopg 版本 3.3.0。
- **动态实证 ①** (statement_timeout 真实生效且 env 可调): 以 `M2_PG_STATEMENT_TIMEOUT=2000` 起探针, `SHOW statement_timeout` 返回 `2s` (env 覆写成立); `SELECT pg_sleep(5)` 在 **2.0s 被 `QueryCanceled` 取消** — 服务端强制取消路径实测打通。
- **动态实证 ②** (connect_timeout 有界): 对 blackhole 地址连接 2.1s 内异常中止, 无挂起。
- **取值合理性**: connect 5s (memory_saver 先例为 15s, 本处更保守, 合理 — 本机 sidecar 化 PG)、statement 10s — 对 chat 持久化的 INSERT/SELECT 足够宽, 对挂起场景足够紧。
- **env 可调**: `M2_PG_CONNECT_TIMEOUT` / `M2_PG_STATEMENT_TIMEOUT` (import 时求值, 部署侧需在进程启动前设置)。
- **锁内有界性**: `_get_session` (m2_service.py:67-86) 与 `append_turn→_append_history` (L118-119→L94-95) 在 `_sessions_lock` 内的 PG I/O 现最坏 ≈ connect 5s + 每语句 10s, 且 chat_persistence 全部查询函数 try/except 收敛 → 锁持有时间有界。原 "PG 挂起 → :5050 无界挂死" 场景闭合。
- **残留 (INFO, 不阻塞)**: statement_timeout 为服务端强制; 若 TCP 链路静默黑洞 (查询已发出、响应永不到达且无 TCP keepalive), 客户端 recv 仍可超过 10s 阻塞。此残留与 memory_saver 先例同界, 超出本闭环项范围; 如 B 阶段要彻底消除, 可加 `keepalives=1` 系列 libpq 参数。
- **运维注意**: 当前运行的 :5050 进程启动于 22:38:40 (早于 c5a8ecf 23:39), **F1 修复尚未载入生产进程**, 需下次重启生效 (代码正确性不受影响)。

#### 1.2 F2 — compare 绕过接线测试: VERIFIED (变异测试证明)

代码: `tests/test_opencode_adapter.py:220-237` + `src/web/routers/m2.py:86`。

- 测试构造: route=on (setenv) + 加载真实 router 模块 + `mod.detect_compare_intent = lambda q: True` (加载后覆写, 端点按模块全局名解析 → 覆写生效) + 记录型 ask_via_opencode 桩。断言三连: `answer=="direct"` ∧ `state["direct"]==1` ∧ **`called==[]`** (ask_via_opencode 零调用)。
- **关键验证 — 非桩遮蔽**: 本审计亲自做变异测试: 将 `m2.py:86` 的 `and not detect_compare_intent(request.question)` 删除后以同桩驱动 → `called == [1]` (绕过分支消失后 ask_via_opencode 确被调用) → 测试的 `called==[]` 断言必然转红。**该测试不是又一个被 lambda q: False 屏蔽的桩** (旧缺陷: `_load_router_with_stub` 的 detect_compare_intent 硬编码 False 恰屏蔽被测分支; 新测试在加载后覆写, 且决定性断言是调用计数而非仅 answer)。
- 正向对照: `test_router_switch_on_uses_opencode_and_records_history` (L198-209) 证明 compare-intent=False 时路由确实被走 (answer 来自 oc 桩) — 双向钉住。

#### 1.3 F3 — trailing-dot strip + echo 负例: VERIFIED

- strip: `opencode_adapter.py:118` `m.group("sample").rstrip(".")` 落实; 测试 L276-283 断尾点剥离 + **内部点保留** (`sample_a.b` 不被误剥)。
- echo 负例 (L294-315): 两段构造 — ① 完整 JSON 示例回声走结构化分支原样透传 (契约形状本身); ② **散文内嵌 JSON-key 形示例** (`"sample_id": "sample_fuxi_hunhe25"`) → `_extract_cited_sources == []` — 引号隔断使兜底正则不命中。
- **边界完备性核验**: m2-qa system prompt (opencode.json L73) 中含真实 sample_id 的示例仅有 JSON-key 形; 平形 (`样本: sample_xxx`) 在 prompt 中仅以 `<sample_id>` 占位符出现 → 模型无法"逐字回声"出平形真实 ID, 平形提取只会发生在模型真正按契约输出引用时 (即预期行为)。echo 攻击面在 prompt 现状下闭合。

#### 1.4 F4 — trust_env 守卫 + sources:[] 透传: VERIFIED (INFO 残留 1 项)

- 断言守卫: 既有两个 post 桩测试 (L51, L89) 逐调用断 `k.get("trust_env") is False` (覆盖 session-create/message/retry 三个 post 点); 新增 `test_all_httpx_calls_opt_out_of_env_proxy` (L123-138) 对 get/post/delete **三个方法槽位**全量 spy, 所有捕获调用逐一断言。
- sources:[] 透传 (L286-291): 显式拒绝 JSON 走结构化分支原样返回空 sources, 不进兜底 — 契约关键态被钉住 ("兜底不虚构填充": 该输入无引用 token, 即便误入兜底亦产出 [], 但测试钉的是契约形状本身)。
- **残留 (INFO)**: `delete_session` (opencode_adapter.py:61) 与 `list_sessions` (L53) 两个调用点无运行时断言 (spy 测试流程未走到 delete/list); 源码层 6 处调用点已全部直读核验均有 `trust_env=False` 字面量 (L47/53/61/165/170/173)。若未来回归只删 delete 点的 trust_env, 测试不会红 → 建议后续在成功路径测试的 delete 桩补一行断言。

#### 1.5 F6 — opencode.json 权限收紧: VERIFIED (INFO 残留 1 项)

- 四个显式 deny 到位: `opencode.json:65-68` m2-qa permission 含 `read/grep/glob/webfetch: deny` (连同既有 edit/bash deny + jinrong-rag_* allow + vision/tabular deny)。
- JSON 合法性: `python -m json.tool` 通过。
- **残留 (INFO)**: 全局 `"skill": "allow"` (L55) 未被 m2-qa 覆写 → m2-qa 仍继承 skill 权限 (skills/ 目录含 m1-gap-triage 等); `"mode": "all"` 未改。因 bash/edit/read 均 deny, skill 可触发的实际动作面很小, 不构成阻塞; 严格隔离表述需补 `"skill": "deny"`。

### 2. T1 判定

**ACCEPTED**。闭环三项 (F1/F2/F3+F4) 全部 VERIFIED, 其中 F1 有动态实证、F2 有变异测试实证, 超出"静态核验"口径; F6 为超额交付。两项 INFO 残留 (delete/list 断言缺口、skill 继承) 与一项运维注意 (生产进程未重启) 记账, 不阻塞。昨夜 CONDITIONAL 解除。

---

## Part 2 — Differential Review: 4a151dd..HEAD (35 commits)

### 0. 增量盘点与分类

35 commits / 104 文件 / +2578 −218。代码类 16, 文档/台账类 19 (不计深度, 仅扫安全面)。

| 类 | commits |
|---|---|
| opencode 适配层链 | a438f0d (A1) → cf5df3d → a9ddfc4 → 62d21e3 → c5a8ecf |
| embedding 本地化 | 04477ab, 9f3e655, 7da6d6f (部分), dcbe5fb (台账) |
| proxy v3 系列 | 696dcbb (v3), d0056a5 (v3.1), ad56ae2 (v3.2) |
| hook/治理 | cf5df3d (收窄), 100b025 (同步) |
| web/skill/MCP | 201f77f, 6787509, c5fd7c0, 06623d3, 7da6d6f (pages.py) |
| 文档/台账 (不计深度) | 62ff081, c788270, 9cfc434, 6fc24e8, dbd9b09, a1943a9, 5fb8460, dca0bdd, a7f8282, 9a17da4, 1cafb9f, 4a038e5, 0b5f33b, db6572b, fb6a2c4, 5545fde, 6edf3d9, 2daec24 |

**机密扫描**: 全量 diff grep (api_key/secret/password/token + 12+ 位值) 零命中 (.env 未入库, .env.example 仅占位符)。

### 1. opencode 适配层演化链 (a438f0d → c5a8ecf)

**演化轨迹** (每步均已 git show 全量核验):

| commit | 内容 | 核验 |
|---|---|---|
| a438f0d (08-05) | A1 适配层 152 行 + 路由接入 + cleanup 端点/脚本 + 9 测试; 开关默认 off | adapter 全文、cleanup 脚本全文、m2.py 增量 ✓ |
| cf5df3d (01:36) | RLock 1 行修复自死锁 + compare 绕过 1 条件 + L5 hook 收窄入库 + 86 行锁回归测试 | 死锁机理复核成立 (持锁入口 get_history→_get_session 重入); hook 双拷贝逐字节一致 ✓ |
| a9ddfc4 (01:53) | trust_env=False 全 6 处 httpx 调用 (clash socks env 毒化实证) | diff 恰 6 处, 无遗漏 ✓ |
| 62d21e3 (22:28) | sources 遵从度三层加固 (prompt 契约→FORMAT_HINT→保守兜底) + 6 测试 | 昨夜审计已逐条核验 ✓ |
| c5a8ecf (23:39) | 闭环 F1/F2/F3/F4/F6 | Part 1 VERIFIED ✓ |

**会话生命周期/清理**: 一次一抛会话 (create→message→delete in finally, `opencode_adapter.py:163-194`); finally 内 delete 失败被 try/except 吞并返回 False (有界); orphan 上限 50, 超限级联清理 (L190-193, list_sessions 异常亦被捕获); 手动清理双通道 (需 admin token 的 `/api/m2/opencode/cleanup` 端点 + `scripts/opencode_session_cleanup.py`)。**缺陷 (LOW)**: 清理脚本 `--purge-all` 为 `while True` 循环, 若 DELETE 恒返回 2xx 但会话实际未删 (sidecar 病态), 循环无退避无上限 → 理论无限循环; 网络/HTTP 错误会抛异常退出, 实际触发条件苛刻。另 cleanup 脚本用 urllib 默认走 env 代理 (未做 trust_env 等效处理), clash 环境下会失败 — 手动工具, INFO。

**超时回落**: health 3s 前置门 + create 10s + message=ASK_TIMEOUT(env 18/默认 90) + finally delete/list 各 10s; 全异常收敛 return None → 直连, 演示面永不破。最坏前置延迟 ≈ 51s (env 值)。22:33 sidecar 停摆事件为真实故障演练 (dispatch_log #SIDECAR-DOWN)。**残留病态尾巴**: orphan>50 且 finally 阶段失联时级联清理最坏 +500s (有界但长) — 昨夜 F5 已含此项。

**事件循环阻塞模式**: 见 §4 F5 完整评估。

**路由门正确性**: `m2.py:86` route_enabled() ∧ ¬detect_compare_intent(q) → opencode, 成功路径 append_turn 双写历史 (L92-93), None 落直连 (L100 日志 + 直连)。compare 端点 (/compare, /compare/positions) 独立于灰度路由, 规则对比永在进程内 ✓。

### 2. embedding 本地化 (04477ab / 9f3e655 / 7da6d6f)

(子代理深扫 + 本审计对 HIGH/MEDIUM 项逐一直读复核, 复核点均确认)

**机制实况**: tag 写入双路径 — 存量补标 `scripts/m1_rag_tag_doctype.py` (参数化 SQL + jsonb 合并 UPDATE, 幂等, 限定 m1_parsed_statements) 与新入库 `m1_rag_ingest.py:341`; 规则单一信源 `compute_doc_type` (m1_rag_ingest.py:62-84, 确定性规则: table_name 前缀 + sample_id 前缀 + 文本标记词, 非模型推断)。活库实测 137/137 chunk 全部有 tag (statement 62 / reconcile 17 / parse_meta 17 / email_notice 15 / header_meta 15 / ocr_table 11), 与台账一致。消费侧: `smart_retrieve` 2.5 步对含 "ocr" 子串查询追加 `{"doc_type":"ocr_table"}` 过滤召回 (PGVector filter, 签名已验证), 4.5 步 `_apply_doc_type_rescore` 乘数 1.35/1.15/0.70。BM25 融合权重未变 (0.6/0.4), BM25 为既有 stub (缓存空, 实际 combined≈0.6×vector)。

**检索语义影响**: top_k/阈值/权重**零改动** (diff 仅 3 文件, app_config.json 与 m2_service.py 未触碰); 行为变化仅限含 "ocr" 子串的查询 (15 条 QA 基准中仅第 13 条); 召回只增不减, 无 recall 退化。配置面: DEVICE default cpu 裁定已落实 (vector_store.py:172); 回退链 fail-closed (路径不存在 → ValueError → RuntimeError; 未配本地模型 → SiliconFlow, 缺 key 直接抛错), 无静默降级。

**关键问题 (复核确认)**:
- **E1 (HIGH)**: **生产路径 rerank 架空 rescore — 验证配置与生产配置不一致**。生产 M2 走 `use_rerank=True` (m2_service.py:199; app_config.json rerank.enabled=true / force_rerank=true), `_maybe_rerank` 后最终 relevance 取 `rerank_score` (rag_service.py ~L423), doc_type 乘数对生产最终排序基本失效 (真正生效的只是 2.5 步召回扩充); 而 15/15 验证用的是 `use_rerank=False` (m1_rag_qa.py:111)。修复本身非破坏/幂等, 但"OCR meta-query 15/15 修复"的验证口径与生产口径不一致, 需在 B4 验收前以生产配置复验或在文档中降级 rescore 表述。
- **E4 (MEDIUM)**: ingest 与补标脚本判定不对称 — `m1_rag_ingest.py:341` 传 `document=""` 使 email_notice 标记词检查恒 False; 当前 `_list_sample_files` 只收 sample_* 文件故未爆雷, email_* 样本一旦进入 ingest 即产生标签漂移。一行修复 (传 chunk text) 或补测试钉住。
- 其余: "ocr" 裸子串触发器脆弱 (E2)、rescore 可误抬无关 ocr_table/误压合法 notice 查询 (E3, 活库实测 10/11 ocr_table chunk 为证券持仓明细)、`_merge_doc_metadata` 白名单不含 doc_type 键 (E5, BM25 修复后会显形)、.env.example `DATABASE_URL` 与代码 `PGDATABASE_URL` 不一致 (E6, 既有问题)、commit 9f3e655 声称 16 测试实测 **15** (E7, `grep -cE "def test_"` 复核确认, 交付记录失实)。
- 测试质量: 15 例断言中等偏强 (不变路径断精确相等/变路径断因子常量), 无 mock 遮蔽 (直调真实静态方法); 缺口: smart_retrieve 2.5 过滤召回分支零覆盖、ingest/tag 一致性无测试; 测试 import 副作用写全局 env (E8, setdefault 有限风险)。

### 3. hook 治理: L5 pre-commit 收窄

**实况核验** (HEAD):
- `scripts/graph/hooks/pre-commit` 与 `.git/hooks/pre-commit` **逐字节一致** (cmp)。
- 冻结面: `tests/test_m1_service.py` (单文件, 非 ^tests/) + `docs/m1_schema/` + `frozen_hashes.txt` 自身 + manifest 清单路径 (hook L11-21)。
- **自洽性**: frozen_hashes.txt 两条目 (test_m1_service.py faa7565a + m1_table_schema.json 73d4f46e) **md5 逐一复验一致**; manifest 更新需 Loop D 授权 (文件头注明) 且 manifest 自身被 hook 保护 (改动需 --no-verify) — 防篡改链闭合。
- 覆写口: `--no-verify` (Loop D only), 与 dispatch T3 记载一致。

**治理完备性评估**:
- 收窄动机成立: 旧 ^tests/ 冻结把合法新测试 (test_m2_session_lock.py) 也拦在门外, 需 --no-verify 才能入库 (dispatch 01:57 双 case 实测)。收窄后新测试正常入库 ✓。
- **代价 (如实记账)**: tests/test_m1_service.py 之外的所有测试 (含本轮新增的 adapter/lock/doctype 关键测试) 不再受 hash 冻结保护 — 恶意/失控 Loop 可在无 --no-verify 的情况下弱化它们。补偿控制: Loop B verify-report (pytest 全量 + API anchors, 最近一次 head c788270 PASS)、Loop C 差分审计 (本报告)、commit 声明与 dispatch_log 对账。**建议 (非阻塞)**: 将 test_opencode_adapter.py / test_m2_session_lock.py 纳入 frozen_hashes.txt (走 Loop D 授权刷新), 恢复关键回归测试的冻结地位。
- **新测试保护结论**: 新测试本身可被修改 (设计使然), 但其执行被 verify-report pytest 门强制 — 删除/弱化会在计数对账中暴露 (62d21e3→c5a8ecf 的 261→266 计数链即实证)。

### 4. 测试覆盖与设计问题 + F5 完整评估

**增量测试质量 (本区间 +~600 行测试)**:
- 优秀模式: deadline-join 反死锁 (test_m2_session_lock.py, 死锁留活线程即红, 不挂套件); 变异实证有效的接线测试 (F2, 见 Part 1); trust_env 三方法槽 spy; sources 正/负例含 echo 与尾点; doctype rescore 16 例 (见 §2)。
- 桩遮蔽风险排查: 逐一检查新增测试的桩边界 — 除 Part 1 已记的 delete/list trust_env 断言缺口外, 未发现新的桩遮蔽 (compare 绕过经变异测试排除)。
- 既有瑕疵延续: `test_lock_is_reentrant` 的 isinstance 断言带 hasattr 恒真兜底 (昨夜已记), 真实证明力在 nested-acquire deadline 部分 — 不改判。
- **缺口 (新)**: ① `/api/m2/opencode/cleanup` admin 门无测试 (与下文 D-finding 相关); ② cleanup_sessions 级联 (>50) 无故障注入测试; ③ ask_via_opencode 对 session-create 返回缺 "id" 的 None 收敛无显式断言 (spy 测试隐式走到但未断言返回值)。

**F5 完整评估 (async 端点同步阻塞 — B 阶段处理建议)**:

现状: `async def m2_ask_endpoint` 内全部为同步阻塞调用 — get_history/append_turn (锁内 PG I/O)、ask_via_opencode (httpx 同步 ≤18s env)、m2_ask (检索+:8004 生成)。阻塞事件循环最坏 51s (env)/133s (默认), 病态级联 +500s; `--workers 2` 下两个并发慢请求即可让 :5050 全停 (含 /health)。已知放大器: 22:45 实测"争用尾部" (被弃 agent run 占用 :8004, 直连回落排队其后, 单问 42.8s) — 共享 :8004 无隔离无中止。同 router 的 /compare /products /timeline /clear 同为 async+同步阻塞模式。

B 阶段选项与取舍:

| 方案 | 改法 | 优点 | 代价/风险 | 定位 |
|---|---|---|---|---|
| ① 端点转同步 `def` | `async def` → `def` (每端点一词) | FastAPI 自动投线程池 (anyio 默认 40/worker), 事件循环立即解放, /health 永不受牵连; 端点内无 await → 转换平凡安全; diff 最小 | 并发上限=线程池; 阻塞调用不变, 单请求延迟不变 | **推荐先做** (B 阶段第一步, 与 ②③ 正交) |
| ② `asyncio.to_thread` 包阻塞调用 | 保持 async, 对 ask_via_opencode/m2_ask/get_history/append_turn 逐点 to_thread | 更外科, 可按调用点控制 | diff 面更大; 锁/PG 交互等效于 ①; 逐点包裹易漏 (如 append_turn 双写) | ①的等价替代, 无额外收益, 不推荐优先 |
| ③ 独立 worker/队列 (docs/25 路线 B) | 生成侧拆服务/队列, 带取消语义 | 根治争用尾部 (可中止被弃 run)、隔离 :8004、支持排队与背压 | 架构级工程量; 需先验证 DELETE session 是否真中止 run | B 阶段主体目标 |

**建议**: B 阶段先落 ① (一处一词 ×5 端点, 零行为风险, 立即消除"全停含健康检查"这一最坏面), 同时推进 ③ 的决策 (docs/25 路线 B); ② 不单独立项。F1 超时生效后, ① 路径下 PG 挂起占用线程亦有界, 事件循环存活 — 两项修复互补。F5 维持 known_risk 入账状态 (THREADS.md L45), 处置路线即上表。

### 5. 外围增量 (proxy v3 系列 / web / skill / MCP)

(子代理深扫 + 本审计对 MEDIUM 项逐一直读复核, 复核点均确认)

**proxy v3→v3.2 演化** (696dcbb/d0056a5/ad56ae2, `scripts/responses2chat_proxy.py`):
- round-trip 完整性: input 侧 function_call→assistant tool_calls / *_output→role=tool, output 侧 tool_calls→function_call/local_shell_call (含 command 数组归一), usage/instructions/developer 映射正确 — 链路闭合 ✓。
- force non-stream 回归史核实: v2 基线 stream 分支本就强制 `chat["stream"]=False`; v3 重构丢失 → SSE body 进 json.loads 崩; ad56ae2 补回。**HEAD 行为正确**; 客户端要 stream 时收到合法但一次性的 SSE 重放 (TTFT≈完整生成时长), 属设计取舍。
- **P1 (MEDIUM, 复核确认)**: `responses2chat_proxy.py:166` `if name in shell_names or name == "shell"` — 硬编码兜底会把恰名为 `shell` 的**自定义 function tool** 误映射为 local_shell_call → Codex 在本机当命令执行而非回传 function 结果。建议删除 `or name == "shell"`, 仅信 tools 声明收集的 shell_names。
- **P2 (MEDIUM, 复核确认)**: PROXY_DEBUG 日志 — `/tmp/proxy_debug.log` 固定路径 `open(..., "a")` 跟随符号链接 (本机任意用户可预置 symlink → 受控内容追加到任意文件); v3.1 移除 v3.0 的 20000 字总长上限后, `UPSTREAM_RESPONSE` (无 "chat" 键) **全量无截断落盘**, 日志无上界且 /tmp 644 可被本机其他用户读。建议: 移出错路径或 0600 + 恢复总量截断。
- 无 SSRF: PORT/UPSTREAM 均硬编码, 客户端参数不可影响上游 URL ✓。其余 LOW: 无鉴权+单线程 (一次 300s 上游调用阻塞全部路由)、请求体无大小上限/非法 JSON 直接断连、启动打印 API key 前 12 位 (既有)、残破 args 兜底 `bash -c` 执行、round-trip 两处边缘字段 (local_shell 历史项强制 name="shell" / *_output call_id 无兜底)。

**web**: `m1.js:12-15` fallback session id (`Date.now().toString(36)` + `Math.random().toString(36).slice(2,10)`) 非 CSPRNG 且小值退化 — **P9 (LOW)**: 风险不在碰撞而在可猜测性叠加服务端设计: `/api/m2/ask` 接受任意 session_id 且 `_get_session` 从 PG 懒加载历史注入上下文、`/sessions/{id}/clear` 可清任意 id → 猜到 id 即可读上下文/清会话 (randomUUID 可用时不可猜, 单用户本机部署影响有限)。pages.py 增量仅 embedding 健康检查 (env→expanduser→isdir), 无注入, 仅 /health/full 回显本机路径 (INFO)。

**skill sync**: A-list 7 项 + C-list 8 项与 skills/ 实况 13 目录全覆盖自洽, 无孤儿 skill ✓; 两份新 SKILL.md 无危险指令 ✓。**P10 (LOW)**: graph-loop-rules SKILL.md 红线表述 "config/m1_table_schema.json 的冻结 hash" 与实况漂移 — 仓库内 config/m1_table_schema.json **不在**冻结清单 (frozen_hashes.txt 冻结的是仓库外 `~/wzh/m1_samples/m1_table_schema.json`), 与 m1-gap-triage "运行时 schema 非冻结可编辑" 的表述矛盾, 按 graph-loop-rules 执行的 agent 可能误拒合法编辑; 且 manifest 绝对路径条目在 pre-commit (staged 相对路径比对) 下永不命中 (死条目, 实际保护靠 Loop B md5 校验)。另 SKILL.md 内 "pytest 基线 227" 与台账 (242) 漂移。

**MCP 启动脚本**: venv-first 逻辑正确 (显式 env → 项目 venv → conda 兜底 → stderr 报错), PROJECT_ROOT 动态推导无硬编码 ✓。**P3 (MEDIUM, 复核确认)**: 06623d3 宣称的 "stdio hygiene" 修复不完整 — 只改了 bm25_retriever.py:129 与 config_loader.py:68 两处, 但 `bm25_retriever.py:102/116/117/186` 仍是裸 stdout print, 而 MCP stdio 导入链 `mcp_server/server.py:9 → biz.rag_service → tools.bm25_retriever` 在每次 smart_retrieve 都会触达 bm25 (rag_service.py:352) → 缓存 miss/重建时 stdout 污染真实发生在 MCP stdio 请求路径, 可破坏 JSON-RPC 帧。另 start_mcp_server.sh 以 shell source 执行 .env (P11, LOW, 本地可信文件)。

### 6. 其余增量扫描

- `scripts/run_opencode_gb10.sh`: JINRONG_MCP_PYTHON venv-first + conda 回退 — 与 06623d3 声明一致, 无问题。
- `src/tools/bm25_retriever.py` / `src/utils/config_loader.py`: print → stderr (MCP stdio 卫生), 正确; 小瑕疵: `import sys` 置于模块 docstring 之前 (docstring 不再成为 `__doc__`), INFO 级文体问题。
- `scripts/graph/loop_c_audit_prompt.md`: :5000→:5050 端口更正 (漂移修复) ✓。
- `scripts/graph/loop_a_exec_constraints.md`: +1 行 m1-gap-triage skill 登记, 与 skills/ 实况一致 ✓。
- 文档/台账 19 commits 不计深度; 抽查无机密、无与代码实况矛盾的关键声明 (STATE/THREADS/DECISIONS 与本轮代码核验一致)。

---

## Part 2 Findings 汇总 (33 项: HIGH 1 / MEDIUM 8 / LOW 16 / INFO 8)

**HIGH + MEDIUM (需处置)**:

| # | Severity | 位置 | 摘要 | 处置建议 |
|---|---|---|---|---|
| E1 | **HIGH** | `rag_service.py:400-423` + `m2_service.py:199` + `config/app_config.json` + `m1_rag_qa.py:111` | 生产 rerank=True 下 doc_type rescore 乘数被 rerank_score 覆盖 → rescore 对生产最终排序失效; 而 15/15 验证用 rerank=False — 验证口径与生产不一致 | B4 验收前以生产配置复验 OCR meta-query, 或在文档中把 rescore 表述降级为"仅服务召回扩充" |
| E2 | MEDIUM | `rag_service.py:39,335,813` | "ocr" 裸子串触发: 英文词内误触发 (如 docrouter)、中文同义 (光学字符识别) 漏触发 | 词边界化或关键词表 |
| E3 | MEDIUM | `rag_service.py:822-829` | rescore 边界: 含 ocr 查询对全量 ocr_table 加权 — 活库 10/11 ocr_table chunk 为证券持仓明细, 可误抬无关文档; 1.15× 可翻转微弱领先; 合法 notice 查询被 0.70× 误压 | 与 schema-match 条件收紧联动 |
| E4 | MEDIUM | `m1_rag_ingest.py:341` vs `m1_rag_tag_doctype.py:77` | ingest 传 document="" → email_notice 标记词检查恒 False, 与补标脚本不对称; email_* 样本入 ingest 即标签漂移 | 一行修复 (传 chunk text) 或补测试钉住 |
| E5 | MEDIUM | `rag_service.py:860-879` | `_merge_doc_metadata` 白名单不含 doc_type/matched_schema/sample_id → BM25 stub 修复或多集合场景下静默丢 tag | 白名单补键 |
| E6 | MEDIUM | `.env.example:30` vs `vector_store.py:22` | 示例给 `DATABASE_URL` (m1_statements), 代码只认 `PGDATABASE_URL` (vector_db); 照抄新环境静默落默认值 (既有问题, 本期配置面审计范围内发现) | .env.example 补 PGDATABASE_URL |
| P1 | MEDIUM | `responses2chat_proxy.py:166` | `or name == "shell"` 兜底把同名自定义 function tool 误映射为 local_shell_call → 本机执行命令而非回传 function 结果 | 删兜底, 仅信 shell_names |
| P2 | MEDIUM | `responses2chat_proxy.py:20,60,256` | /tmp 固定路径 debug 日志跟随 symlink (受控追加攻击面) + v3.1 移除总长上限后 UPSTREAM_RESPONSE 全量无截断落盘 + 644 可读 | tempfile/0600 或移出错路径, 恢复截断 |
| P3 | MEDIUM | `bm25_retriever.py:102,116-117,186` | 06623d3 宣称的 stdio hygiene 不完整: MCP stdio 链 (server.py→rag_service→bm25) 上仍有裸 stdout print, 缓存 miss/重建时可破坏 JSON-RPC 帧 | 补齐 print→stderr |

**LOW (16)**: D1 `_check_admin` fail-open (M1_ADMIN_TOKEN 全环境未设, .env/scripts/生产进程 env 均无 → cleanup purge_all 在 0.0.0.0:5050 无鉴权; 影响=抛置式会话可被清, 建议 fail-closed) / D2 cleanup 脚本 --purge-all 无退避循环 + urllib 走 env 代理 / E7 commit 9f3e655 声称 16 测试实测 15 (记录失实) / E8 测试 import 副作用写全局 env / E9 过滤召回异常静默吞 + vector_count 虚增 / E10 vector_store.py:106 类签名 device 默认 cuda 残留 (不可达但误导) + health 自检对本地 provider 失实 / E11 非 rerank 路径 relevance_score 被乘数污染并进 M2 prompt / P4 proxy 无鉴权+单线程阻塞 / P5 请求体无大小上限、非法 JSON 断连无 400 / P6 启动打印 API key 前 12 位 (既有) / P7 残破 args 兜底 `bash -c` / P8 round-trip 边缘字段 ×2 / P9 m1.js fallback session id 弱熵 + 服务端任意 session_id 接受 → 跨会话读/清面 / P10 graph-loop-rules 冻结表述漂移 + manifest 绝对路径死条目 / P11 start_mcp_server.sh shell-source .env / P12 opencode.json agent mode 放宽 + prompt 硬编码绝对路径与 /tmp 固定输出。

**INFO (8)**: D3 skill:allow 被 m2-qa 继承 (动作面极小) / D4 delete/list 两调用点无 trust_env 运行时断言 (源码 6 处已核全有) / D5 生产进程未重启, F1 超时未载入 / D6 hook 收窄取舍 — 建议关键新测试纳入 manifest (需 Loop D 授权) / 无 SSRF 确认 (PORT/UPSTREAM 硬编码) / pages.py 仅路径回显 / chat_persistence VARCHAR(36) 容量 + SQL 全参数化 / `import sys` 置于 docstring 前文体瑕疵 ×2。

**判定**: 增量整体 **ACCEPTED** (无 CRITICAL; 1 HIGH 为验证口径问题而非运行期安全/数据风险, 修复非破坏且幂等)。优先处置序: E1 (B4 前复验) → P1/P2/P3 (随手修) → E4/E5 (一行级) → 其余 B 阶段批量。opencode 灰度链经 5 步演化后收敛、可回落、有实证演练; embedding 本地化增量正确非破坏; hook 收窄自洽。

---

## 证据链

- 亲跑: pytest 全量 (266/13/0, 71.41s) + 5 新测试隔离运行
- 动态探针: `SHOW statement_timeout=2s` (env 覆写) + `pg_sleep(5)` 2.0s QueryCanceled + blackhole connect 2.1s 中止; F2 变异测试 (删绕过条件 → called==[1] → 断言必红)
- git show 全量: c5a8ecf / a9ddfc4 / 62d21e3 / cf5df3d / a438f0d + diff 4a151dd..HEAD (m2.py, m2_service.py, hook, constraints, sync_skills, run_opencode_gb10, bm25, vector_store, config_loader, pages.py, m1.js, responses2chat_proxy, MCP 启动脚本)
- HEAD 直读: opencode_adapter.py (195 行全文)、chat_persistence.py 全文、routers/m2.py 全文、m2_service.py L40-149、test_opencode_adapter.py 全文、test_m2_session_lock.py 全文、opencode.json 全文、pre-commit 双拷贝 cmp、frozen_hashes.txt md5 复验、verify-report.json、.env/.env.example、THREADS.md L41-45、responses2chat_proxy.py L15-65/155-190、bm25_retriever.py print 清点、rag_service.py L395-430/890-900、app_config.json rerank 块、m1_rag_qa.py:111、m1_rag_ingest.py:341、test_rag_doctype_rescore.py 计数
- 运行环境探针: uvicorn PID 817423 (lstart 22:38:40, --host 0.0.0.0 --workers 2, env 含 M2_OPENCODE_ROUTE=on / OPENCODE_ASK_TIMEOUT=18 / 无 M1_ADMIN_TOKEN); PG :15432 活库 tag 分布实测 137/137
- 分工披露: embedding 本地化与外围增量 (proxy/web/skill/MCP) 由两个并行子代理深扫, 本审计对其全部 HIGH/MEDIUM 结论逐一直读源码复核 (rerank 配置链、shell 映射、debug 日志截断、bm25 print 链、ingest 不对称、测试计数), 复核点全部成立后才入账; LOW/INFO 按子代理报告收录并抽查关键点
- 限制: 未运行 :5050 端到端黑盒 (sidecar/模型负载原因); E1 的生产配置复验未亲跑 (留 B4)
