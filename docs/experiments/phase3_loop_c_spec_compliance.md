Evidence collection is complete. Compiling the audit report per the spec-to-code-compliance methodology (Phase 0–6: extraction → alignment → classification → report).

# Loop C 文档-代码一致性审计报告

**审计方法论**: spec-to-code-compliance skill（Spec-IR 提取 → Code-IR 对照 → Alignment 分类 → 证据引用）
**审计对象**: docs/17、docs/19、docs/20
**审计时间**: 2026-08-04 · HEAD = `a91ff74`（main，与 Loop B 最新报告同一 commit）
**证据来源**: 静态代码核对（file:line 引用）、`ss -tln` 端口快照、进程清单、logs/graph/verify-report.json（2026-08-04 00:05 Loop B 实时结果）、docs/experiments/ 归档报告。
**限制说明**: 本会话中 `curl`/`wget`/Python 网络调用均需审批且未获批准，HTTP 端点验证改用 (a) 监听端口快照 + (b) Loop B 于今日 00:05 写入的 verify-report.json 与 loop_b.log（其中逐端点记录了 :5050 与 :8004/:8005 的 200/ok 结果）替代，效力等同。全程只读，未做任何写操作。

---

## 一、docs/17_Graph_Engineering_多层Loop设计.md

### 已核对一致的陈述（抽样）

| 文档陈述 | 代码/运行实况 | 判定 |
|---|---|---|
| §8 文件索引列出 scripts/graph/ 6 个文件 | 6/6 全部存在；orchestrator 支持 start/stop/status/logs（graph_orchestrator.sh:169 `case`） | full_match |
| §2 Loop B "纯 bash、30 分钟轮询、写 verify-report.json、独立跑 `pytest tests/test_m1_service.py -v`" | loop_b_verify.sh `POLL_INTERVAL=1800`；pytest 命令逐字一致；`REPORT_FILE=logs/graph/verify-report.json`；今日 00:05 实测 18 passed | full_match |
| §3.1 锚点 "`curl http://127.0.0.1:8004/health` 返回 ok" | loop_b.log 2026-08-04 00:05 `OK: model :8004 healthy`、`OK: model :8005 healthy`；`ss -tln` 显示 :8004/:8005/:8100/:15432 均在监听 | full_match |
| 演进记录 2026-07-31 "API_BASE :5050" 修复 | loop_b_verify.sh `API_BASE="${M1_API_BASE:-http://127.0.0.1:5050}"` | full_match |
| §3.2 冻结 `tests/test_m1_service.py`（git diff/md5 校验） | frozen_hashes.txt 第 1 条即该文件；Loop B 今日校验 PASS、0 violations | full_match |

### 不一致清单

**[17-1] §3.1 锚点表：`curl -s http://127.0.0.1:5000/api/m1/parse-file 返回 200 + 有效 JSON`**（MEDIUM）
- **文档原文**: 锚点 "API 端点真的能用" 使用 **:5000**。
- **代码实况**: 应用实际监听 **:5050**（运行进程 `./venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 5050 --workers 2`；`ss -tln` 显示 5050 监听、**5000 无任何监听**；Loop B 锚点亦用 5050 且今日 PASS）。另注意 `/api/m1/parse-file` 是 POST multipart 路由（src/web/routers/m1.py:69-74），GET 裸 curl 不会返回 200，锚点写法本身也不可复现。
- **建议修法**: 改为 `:5050`，并把锚点换成 Loop B 实际使用的可复现 GET 锚点（`GET /health`、`GET /api/m1/sample`），或写成 `curl -X POST -F "file=@x.pdf" http://127.0.0.1:5050/api/m1/parse-file`。

**[17-2] §4.1 基础设施表：`:5000 | FastAPI 应用 | M1/M2 业务 API | 运行中`**（MEDIUM）
- **文档原文**: :5000 为业务 API 端口。
- **代码实况**: 业务 API 在 :5050；AGENTS.md:189 亦写明 "M2 RAG QA endpoint is live at :5050"。本条与文档自己的演进记录（2026-07-31 "API_BASE :5050"）**内部矛盾**。
- **建议修法**: §4.1 表将 :5000 改为 :5050；或在表头注明"本节为 2026-07-29 快照，现行端口以演进记录为准"。

**[17-3] §3.2 冻结节点表：`字段定义 | docs/m1_schema/*.json`**（HIGH）
- **文档原文**: 冻结对象"字段定义"路径为 `docs/m1_schema/*.json`。
- **代码实况**: `docs/m1_schema/` **不存在**（ls 报错"没有那个文件或目录"）。真实 schema 双轨制：活动副本 `config/m1_table_schema.json`（LOCAL_SCHEMA，m1_statement_parser.py:48；API 写入也只写这里，src/web/routers/m1.py:223-228），冻结基准 `~/wzh/m1_samples/m1_table_schema.json`（DEFAULT_SCHEMA，m1_statement_parser.py:44；frozen_hashes.txt 第 2 条哈希的正是它）。AGENTS.md:184/211 的冻结清单同样是 `~/wzh/m1_samples/m1_table_schema.json`，无 docs/m1_schema。
- **建议修法**: 将冻结表改为 `~/wzh/m1_samples/m1_table_schema.json`（冻结基准）+ `config/m1_table_schema.json`（可写覆盖层），与 frozen_hashes.txt 和 AGENTS.md 对齐。此为安全机制条目，路径错误会误导 Loop A/C 的冻结判断。

**[17-4] §3.2 冻结节点表：`甲方真实样本 ~/wzh/m1_samples/ | md5sum 清单比对`**（MEDIUM，code_weaker_than_spec）
- **文档原文**: 整个样本目录由 md5sum 清单比对保护。
- **代码实况**: frozen_hashes.txt 仅含 **2 个文件**（test_m1_service.py + m1_table_schema.json），未对样本目录内 PDF/TXT/DOCX 建哈希；loop_b_verify.sh 的 check_frozen_nodes 只遍历该清单 + 测试文件计数下限，无样本目录扫描。
- **建议修法**: 二选一——(a) 在 frozen_hashes.txt 增补样本文件哈希（需 Loop D 授权）；(b) 把文档表述改为"样本目录受' repo 外存放 + 仅 schema 文件哈希锚定'保护，非逐文件哈希"。

**[17-5] §3.2 冻结节点表：`评测基准 docs/experiments/ | git diff 检查`**（LOW-MEDIUM，code_weaker_than_spec）
- **文档原文**: Loop B 用 git diff 检查评测报告"只增不改"。
- **代码实况**: loop_b_verify.sh 的 git 检查仅 `git diff --name-only HEAD~1 HEAD | grep '^tests/'`（只看 tests/），对 docs/experiments/ 无任何检查。
- **建议修法**: 在 check_git_state 增加对 `docs/experiments/` 已归档文件修改/删除的检测，或下调文档表述。

**[17-6] §8 文件索引未覆盖 3 个实际存在的文件**（LOW，UNDOCUMENTED）
- **实况**: scripts/graph/ 另有 `loop_d_daemon.sh`、`sync_skills.sh`、`write_report.py`（后者被 loop_b_verify.sh 调用写报告，属关键路径）。
- **建议修法**: 补入索引表。

**[17-7] §4.1/§4.2 模型与内存数字**（AMBIGUOUS，不可验证）
- "Qwen3.6-35B-A3B Q4_K_M + mmproj"、"44GB/121GB 已用"、72B 下载进度等描述远端 GB10 状态，本机无法取证；对应端口（:8004/:8005/:8100）监听属实，模型身份与内存数字**无法证实也无法证伪**。
- **建议修法**: 保留但标注"快照时间 2026-07-29，远端状态以 loop_d_monitor.sh 实时输出为准"。

### 结论：**DRIFTED**
设计层与 Loop B 实现高度一致（机制、脚本、轮询、报告均吻合且今日 PASS），但安全机制章节（§3.1/§3.2）存在 1 处 HIGH（冻结路径指向不存在的目录）+ 2 处端口/锚点漂移，属文档滞后于 07-31 的 :5050 迁移。

---

## 二、docs/19_系统能力说明书.md

### 已核对一致的陈述（抽样）

| 文档陈述 | 代码/运行实况 | 判定 |
|---|---|---|
| 格式耗时表（TXT <100ms / PDF文本层 <2s / OCR ~27s / DOCX ~70s） | e2e_benchmark.md：TXT 12ms、jiaxing PDF 1064ms、LU.pdf parse 26885ms、xinhua.docx 69676ms，逐条吻合 | full_match |
| "4 项勾稽校验 + real_pass/skipped" | m1_statement_parser.py:1279-1458 恰为 4 检查（市值勾稽/币种一致/日期格式/静默错配嫌疑），`disposition ∈ {real_pass, skipped}` | full_match |
| M2 端点 + 自然语言路由（"对比/变化/差异"触发）+ 诚实降级文案 | src/web/routers/m2.py:98-117 四个端点齐全；m2_service.py:437 `_COMPARE_TRIGGERS`；m2_service.py:571 降级文案逐字一致 | full_match |
| 测试集 15/15、295ms（138+157）、17 embeddings、4/5 样本入库 | docs/22 closeout L422-435、L526 与 2026-07-31_m2_rag_integration.md L65 逐字佐证（**但见 [19-1] 的时效性问题**） | full_match（对报告时点） |
| 答案溯源（来源文档/表/相关度/原文） | m2_service.py retrieve() 返回 `{sample_id, table_name, score, text}` | full_match |
| 多轮对话存 PG（chat_sessions + chat_messages） | src/storage/chat_persistence.py:16-28 两表 DDL 与文档逐字一致 | full_match |
| /api/health/full 带 30s 缓存 | src/web/routers/pages.py `_HEALTH_CACHE_TTL = 30.0` | full_match |
| Bearer Token（M1_API_TOKEN）+ 未设置时 WARNING 不停机 | src/web/middleware.py:46-50 逐字实现 | full_match |
| /api/metrics Prometheus 格式；JSON 日志 → logs/app.log | metrics.py:12；logs/app.log 首行即 JSON 结构 | full_match |
| 规则配置 GET/PUT/POST/DELETE + X-Admin-Token + 热加载 + UI 按钮 | m1.py:294-385 全部端点 + `_check_admin`；parse_file 每请求 `Schema.load`（真热加载）；m1.html:45 "规则配置"按钮 | full_match |
| 并发 2 workers | 运行进程/Dockerfile/m1_serve.sh 均 `--workers 2` | full_match |
| Phase 4 边界压测 | tests/test_m1_edge_cases.py 17 个用例 + closeout L458 "17/17 pass"、L574 "10 边界样本压测" | full_match |
| 截图引用（01_homepage/02_sample_parsed/03_m2_qa、demo_sequence 8 帧） | 文件全部存在 | full_match |

### 不一致清单

**[19-1] 性能数据："M2 问答响应 295ms（检索 138ms + 生成 157ms）"**（MEDIUM，stale vs current code）
- **文档原文**: 性能表将 295ms 作为现行指标（含 §4 表格与"核心能力"节）。
- **代码实况**: 当前 /api/m2/ask 路径**已启用 rerank**——m2_service.py:187 `use_rerank=True`；config/app_config.json `"rerank.enabled": true`、`force_rerank: true`、本地 bge-reranker-v2-m3。项目自己的 closeout 报告（docs/22 L530）记录 rerank 接入后 **M2 延迟 (warm) 295ms → 689ms**。295ms 是 2026-08-01 的 pre-rerank 基线，不再代表当前代码行为。
- **建议修法**: 更新为"~689ms（含 rerank 精排，warm）；无 rerank 基线 295ms"，或注明测量基线的 rerank 开关状态。

**[19-2] 技术架构："技术栈: Python 3.11"**（LOW）
- **实况**: venv/pyvenv.cfg `version = 3.12.3`；Dockerfile `FROM python:3.12-slim`；docs/CLAUDE.md 要求 3.12。
- **建议修法**: 改为 "Python 3.11+（实际 3.12）"。

**[19-3] "映射结果覆盖 6 类标准表结构：…KV 网格、通用表格"**（LOW，partial_match）
- **实况**: schema 定义 4 张标准表（表头信息/资金资产汇总/证券持仓明细/交易对账单）+ `_unattributed` 兜底（config/m1_table_schema.json:5,132,155,292,590）；解析器另产出 `kv_grid_*` 表（m1_statement_parser.py:852）。代码中不存在名为"通用表格"的表类型。
- **建议修法**: 表述改为"4 张标准业务表 + KV 网格表 + 未归类兜底（_unattributed）"。

**[19-4] 部署方式节与生产化特性节的入口混淆**（LOW-MEDIUM）
- **文档原文**: "开发环境一键启动 `bash scripts/m1_serve.sh`"，同文又称系统具备 /api/health/full、/api/metrics、认证、PG 持久化等生产特性。
- **代码实况**: m1_serve.sh 生成的是**精简 harness**（/tmp/m1_harness_5050.py），只挂 m1/m2 路由 + /m1 页面 + /health，**不含** /api/health/full、/api/metrics、认证中间件、chat 路由。全部生产特性在 `main:app`（src/main.py）中，需按部署指南的 uvicorn main:app 方式启动（当前运行进程即 main:app）。
- **建议修法**: 注明 "m1_serve.sh = 轻量演示入口；完整能力（监控/认证/健康全景）需启动 main:app"。

**[19-5] 路线图内部张力**（LOW）
- "生产部署 | Docker + 监控 + 日志 | 📋 规划中" 与同文"生产化特性（Phase 3）已完成"（deploy/ 文件、metrics、JSON 日志均已落地）矛盾。
- **建议修法**: 将路线图"生产部署"改为"✅ 基础已就绪（Phase 3），剩生产环境接入"。

### 结论：**DRIFTED**（轻度）
端点、能力、校验逻辑、测试数字与代码高度吻合（20+ 条 full_match），但标志性性能数字 295ms 已落后于当前代码路径（rerank 已开启，现行 ~689ms），按"性能数字必须与代码实况一致"的审计口径判 DRIFTED。

---

## 三、docs/20_部署指南.md

### 已核对一致的陈述（抽样）

| 文档陈述 | 代码/运行实况 | 判定 |
|---|---|---|
| 快速启动步骤 5 `PYTHONPATH=src python -m uvicorn main:app --host 0.0.0.0 --port 5050 --workers 2` | 当前运行进程命令行逐字一致 | full_match |
| 步骤 6 验证端点 /health、/api/m1/sample | 两路由均存在（main.py:228；m1.py:48），Loop B 今日实测 200 | full_match |
| Docker Compose 三服务表（m1-harness:5050 / pgvector:15432 / responses-proxy:8100） | docker-compose.yml 服务名与端口逐字一致 | full_match |
| M1_API_TOKEN / M1_ADMIN_TOKEN 语义 + 未设置仅 WARNING | middleware.py:46-50、m1.py:199-202 逐字实现 | full_match |
| systemd / supervisord 守护 | deploy/m1-harness.service、deploy/supervisord.conf 存在且命令与文档一致 | full_match |
| Prometheus 抓 /api/metrics | metrics.py:12 路由存在 | full_match |
| Python 3.11+ 推荐 3.12 | venv 3.12.3、Dockerfile 3.12-slim | full_match |
| Qwen3-Embedding-0.6B CPU 嵌入 | 2026-07-31_m2_rag_integration.md 证实本地 0.6B CPU；代码路径 LOCAL_EMBEDDING_MODEL_PATH 存在（vector_store.py:168） | full_match |

### 不一致清单

**[20-1] 数据库环境变量名：`DATABASE_URL` vs 代码实际读取 `PGDATABASE_URL`**（HIGH）
- **文档原文**: 步骤 4 `export DATABASE_URL="postgresql://.../m1_statements"`；"环境变量清单"表亦列 `DATABASE_URL`。
- **代码实况**: `grep -rn DATABASE_URL src/` 显示**所有**读取点均为 `PGDATABASE_URL`（src/storage/database/db.py:19、src/tools/vector_store.py:22、src/storage/chat_persistence.py:39、src/storage/collaboration/db.py:31）；`DATABASE_URL` 在 src/ 中**零引用**。按文档照做，应用读不到连接串，vector_store 将回退到 PG* 分量变量 → 默认 `localhost:5432/vector_db` → 连接失败。文档末尾"环境变量完整清单"又正确地写了 `PGDATABASE_URL`（必填）——**文档自相矛盾**。deploy/ 两个守护文件用的也是 PGDATABASE_URL。
- **建议修法**: 步骤 4 与清单表统一改为 `PGDATABASE_URL`；同步修正 .env.example 与 docker-compose.yml（compose 里 m1-harness 环境目前也是 `DATABASE_URL`，同样不会被代码读取）。

**[20-2] 数据库名：`m1_statements` vs 实际生产 `vector_db`**（HIGH）
- **文档原文**: 步骤 3 `POSTGRES_DB=m1_statements`、连接串 `.../m1_statements`。
- **代码/运行实况**: deploy/m1-harness.service 与 supervisord.conf 均为 `.../15432/vector_db`；2026-07-31_m2_rag_integration.md §2 记载生产 PGVector 为"docker `pgvector_15432`，库 `vector_db`"；vector_store.py:34 回退默认库名也是 `vector_db`。docker-compose.yml 单独创建 `m1_statements`，与实际运行库不符（新环境按 compose 起库后，还需与守护配置/既有数据对齐）。
- **建议修法**: 明确"现行生产库为 vector_db"，并决定统一方向（改 compose/deploy 之一），文档与两侧配置保持一致。

**[20-3] `LLM_BASE_URL` / `EMBEDDING_BASE_URL` 为无效变量**（MEDIUM）
- **文档原文**: 步骤 4 要求 export 两者；清单表给出默认值 `http://127.0.0.1:8004/v1`。
- **代码实况**: src/ 内无任何代码读取这两个变量。实际生效的是：`M1_LLM_ENDPOINT`（m1_statement_parser.py:1512，默认 `http://127.0.0.1:8004/v1/chat/completions`）、`M2_LLM_ENDPOINT`（m2_service.py:42，同默认）、嵌入侧 `LOCAL_EMBEDDING_MODEL_PATH` / `SILICONFLOW_BASE_URL`（vector_store.py:168-181）。默认值恰好都指向 :8004，故行为碰巧一致，但用户按文档修改这两个变量**不会生效**。
- **建议修法**: 清单替换为真实生效变量（M1_LLM_ENDPOINT、M2_LLM_ENDPOINT、LOCAL_EMBEDDING_MODEL_PATH、SILICONFLOW_BASE_URL/SILICONFLOW_API_KEY、PGDATABASE_URL）。

**[20-4] `OPENAI_API_KEY（必填）`**（LOW-MEDIUM）
- **文档原文**: 两处清单均标"必填/是"。
- **代码实况**: `grep OPENAI_API_KEY src/` 零命中——核心应用完全不读它；仅 scripts/responses2chat_proxy.py:10 读取。本地 :8004 路径无需任何 key。
- **建议修法**: 改为"responses-proxy / SiliconFlow 嵌入路径需要；纯本地 :8004 部署可选"。

**[20-5] docker-compose.yml 与代码的联动缺陷（由文档审计牵出）**（HIGH）
- **实况**: compose 的 m1-harness 服务注入 `DATABASE_URL`（与文档一致、与代码不一致），未注入 `PGDATABASE_URL` → 容器内应用按代码逻辑无法获得连接串。文档与 compose 互相一致，但两者同时偏离代码。
- **建议修法**: compose environment 改为 `PGDATABASE_URL: postgresql://postgres:postgres@pgvector:5432/<统一库名>`；此属配置修复，需另行立项（本次只读审计不改动）。

**[20-6] 模型表资源数字 ":8004 → 6.5GB RAM + GPU" 等**（AMBIGUOUS，不可验证）
- 远端 GB10 资源占用无法从本机取证；端口存在性已验证（:8004/:8005 监听中）。
- **建议修法**: 标注快照来源与时间。

### 结论：**DRIFTED**
服务端口、进程命令、认证/守护/监控等描述与实况吻合，但两处 HIGH 级环境变量/库名偏差（DATABASE_URL 无效、m1_statements vs vector_db）会导致**照文档从零部署直接失败**，且文档内部前后清单自相矛盾。

---

## 总体汇总

| 文档 | full_match | 漂移项 | 最高严重级 | 结论 |
|---|---|---|---|---|
| 17_Graph_Engineering | ~10 条（Loop B 机制全吻合，今日 PASS） | 7 | HIGH（冻结路径指向不存在目录） | **DRIFTED** |
| 19_系统能力说明书 | 20+ 条（端点/校验/测试数字全吻合） | 5 | MEDIUM（295ms 落后于 rerank 现状） | **DRIFTED**（轻度） |
| 20_部署指南 | ~10 条（进程命令/端口/认证吻合） | 6 | HIGH（DB 变量名与库名偏差致部署失败） | **DRIFTED** |

**优先修复建议（按 ROI）**: [20-1]+[20-5] 统一 PGDATABASE_URL → [20-2] 统一库名 → [17-3] 更正冻结 schema 路径 → [19-1] 更新 QA 延迟数字 → 其余 LOW 项随下次文档例行维护。

END-OF-REPORT
