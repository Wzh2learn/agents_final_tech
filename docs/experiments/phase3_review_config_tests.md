# Phase 3 Code Review — config/ + tests/

- **审查角色**: Loop A (执行层), read-only 代码审查任务 (Loop D 分发)
- **方法论**: skills/requesting-code-review/code-reviewer.md 模板结构
- **日期**: 2026-08-04
- **范围**: `config/` (3 文件) + `tests/` (28 个测试文件 + conftest + fixtures)
- **方法**: 静态分析 (AST 统计 / rg 引用追踪 / schema 冲突程序化检测) + 定向运行确定性测试子集取证。未修改任何代码, 未做任何 git 操作。
- **取证命令**:
  - `pytest tests --collect-only -q` → **240 collected** (与 AGENTS.md 记录的 227 passed / 13 skipped 一致)
  - `pytest tests/test_m1_service.py tests/test_m1_parser.py tests/test_m1_reconcile.py tests/test_m1_schema_api.py -q` → **66 passed** (含 18 个冻结合约测试)
  - `diff config/m1_table_schema.json ~/wzh/m1_samples/m1_table_schema.json` → ~26 处 hunk 漂移

---

## Strengths (先说做得好的)

- **冻结合约测试独立有效**: `tests/test_m1_service.py` (18 tests) 哈希锁定 (frozen_hashes.txt) 且本次独立运行通过; 冻结节点真实可用, 不是摆设。
- **schema API 测试隔离堪称范例**: `tests/test_m1_schema_api.py:49-71` 用 `tmp_path` + `monkeypatch` 把 `LOCAL_SCHEMA` 指到临时目录, 绝不触碰真实 `config/`; admin token 401 路径 (缺 token / 错 token) 有覆盖。
- **解析器匹配算法设计合理**: 四级打分 (标准名精确=4 > 同义词精确=3 > 包含匹配=2 > 编辑距离≤1=1), 贪心一对一占用 (`scripts/m1_statement_parser.py:176-235`); 包含匹配带可疑关键词护栏 (在途/配号/冻结/质押/担保), 编辑距离限定 ≥3 字符, 都是防止短列名错配的实战补丁。
- **归一化健壮**: `normalize_header` 剥离空白/全角/标点 (`scripts/m1_statement_parser.py:60-66`), 因此 `帐  号`、`基金总市值（元）` 这类变体实际可命中; 帐/账变体已覆盖 (基金帐号、股东帐号)。
- **MCP 稳定性测试含脱敏断言**: `tests/test_mcp_opencode_stability.py` 显式验证 `run_once` 只持久化 sanitized status + digest, 不保留原始输出 — 审计友好。
- **fixtures 全合成且标注清晰**: `tests/fixtures/m2_eval_cases_v1.json` 自标 `"classification": "sanitized-bootstrap"`; edge fixtures (编码/空文件/损坏 PDF) 全合成, 无客户数据。
- **任务点名的 5 条业务路径均有测试**: OCR 回退 (9, mock 触发条件齐全)、多轮对话 (20)、跨期对比 (24)、schema API (16)、认证 (5)。
- **内存层补充同义词不进冻结文件**: 交易帐号/交易账号→资产账号 等补充写在 `Schema.load` 代码里 (`scripts/m1_statement_parser.py:139-150`), 治理意识正确。

---

## Issues

### Critical (Must Fix)

1. **真实甲方数据已进入仓库 (违反 AGENTS.md 脱敏红线)**
   - File: `tests/ground_truth_values.json` (git 已跟踪, commit cc6ad5b / 4d3d2f1)
     - 客户编号 `200030028295`、资产账号 `200030028295` (fuxi_hunhe25 样本)
     - 资产账户 `880200001508` + 真实余额 `3508.55` / `401379783.28` / `401383291.83` (jiaxing_minan 样本)
     - 真实市值 `22161557.90`
   - File: `tests/test_m2_multiturn.py:136,141,182,186,330` — 客户名 "嘉兴民安" + 真实总资产 `401383291.83` 作为断言值
   - File: `tests/test_m2_compare.py:25,32,81,226` — "复熙混合25号"、"嘉兴民安" 作为 mock 产品名
   - Why: AGENTS.md 明文规定 "Real client samples ... never committed; reports desensitized"。样本文件本身守住了 (在 ~/wzh/m1_samples/), 但由样本派生的账户号+余额+客户名通过 ground truth 和测试代码泄漏进了 git 历史。公开基金代码 (001522 博时) 不在此列, 问题仅限客户标识与资金数值。
   - Fix: 用合成值替换 (保持数值间的勾稽关系以便测试仍有效); 评估 git 历史清理 (filter-repo) 并知会甲方接口人。建议同时加一条防泄漏回归测试 (见建议清单 #12)。

### Important (Should Fix)

1. **schema 内 8 处同义词冲突, 其中 2 处靠字段顺序碰运气**
   - File: `config/m1_table_schema.json`; 裁决逻辑 `scripts/m1_statement_parser.py:205` (严格 `>`, 同分先声明者胜)
   - 程序化检测出的冲突 (同一源列名 → 多个标准字段, 表内):
     | 表 | 源列名 | 冲突目标 | 实际裁决 |
     |---|---|---|---|
     | 表头信息 | `账号` | 客户编号 vs 资产账号 | 同分平局 → 客户编号 (字段序在前) |
     | 表头信息 | `对账起止日期` | 开始日期 vs 结束日期 | 同分平局 → 只映射开始日期, **结束日期静默丢失** |
     | 证券持仓明细 | `确认份额` | 持仓数量 vs 确认份额 | 标准名精确 (4分) 压同义词 (3分) → 侥幸正确 |
     | 证券持仓明细 | `确认日期` | 交易日期 vs 确认日期 | 同上 |
     | 证券持仓明细 | `手续费` | 手续费 vs 交易规费 | 同上 |
     | 资金资产汇总 | `资产市值`/`证券市值`/`总资产` | 各自 vs 合计金额 | 同上 |
   - Why: 4 处靠打分阶梯侥幸正确, 但声明本身自相矛盾; `账号` 与 `对账起止日期` 是真平局, 结果取决于 JSON 字段书写顺序 — 任何人重排字段顺序都会改变行为。`对账起止日期` 单一表头无法同时喂两个字段, 属于语义缺陷而非纯冲突。
   - Fix: 删除冲突声明之一 (如 `账号` 从资产账号移除, 保留在客户编号), `对账起止日期` 定义明确行为 (范围拆分或指定唯一目标); 并在 CI 中固化冲突检测 (建议清单 #1)。

2. **schema 写 API 不校验同义词冲突 — 冲突集会无声增长**
   - File: `src/web/routers/m1.py:239-281` (`_validate_schema`)
   - Issue: 只校验结构 (tables 存在、table_name/standard 不重复、synonyms 是数组), 不校验 "同一源列名不得出现在多个标准字段下"。PUT /api/m1/schema 与 POST fields 可合法写入新冲突。
   - Fix: 把冲突检测并入 `_validate_schema` (返回 422 + 冲突清单)。

3. **运行时生效的 schema 不在 Loop B 冻结校验范围内**
   - File: `scripts/graph/frozen_hashes.txt` 只哈希 `~/wzh/m1_samples/m1_table_schema.json`; 但 `resolve_schema_path()` (`scripts/m1_statement_parser.py:51-56`) **优先**读 `config/m1_table_schema.json`。
   - 两份文件已漂移 ~26 处 hunk: config/ 是超集 (+约 60 个同义词, 交易对账单新增 持仓数量/摘要 两个字段, header_meta 新增 基金账户/客户名称)。
   - Why: Loop B 每 30 分钟校验的是**运行时不生效**的那份; 若 config/ 被误删, 解析器静默退化到陈旧子集, Loop B 全绿。
   - Fix: Loop D 授权后把 config/m1_table_schema.json 纳入 frozen_hashes.txt, 或让 Loop B 校验 "config ⊇ samples 且冲突数不增" (建议清单 #3)。

4. **`header_meta_fields` JSON 字典是死配置且已漂移 — 单文件两个真相源**
   - File: `config/m1_table_schema.json` 尾部 `header_meta_fields`; 裁决逻辑 `scripts/m1_statement_parser.py:151-158`
   - Issue: 只要存在 kv 布局表 (表头信息), `Schema.load` 就从表字段重建 meta, 永不读这个字典; 字典里独有的 `基金账户`、`客户名称` 运行时**不生效**。手工编辑该字典的人会得到"改了没用"的静默失败。
   - Fix: 删除该字典或在其顶部加 `_comment` 声明 "仅 kv 表缺失时的 fallback"; 推荐删除。

5. **Scenario-1 三个缺口修复零回归测试**
   - `_coordinate_table_reconstruction` (NCAMC 竖排重建, `scripts/m1_statement_parser.py:858`, 100+ 行几何算法) — 无任何测试
   - .msg 邮件 HTML 正文提取 (extract_msg.htmlBody 路径) — 无任何测试
   - XLSX 解析路径 (openpyxl) — 无任何测试
   - DOCX 解析路径 (python-docx) — 无任何测试
   - Why: AGENTS.md 报告这些为 "100% 解析率" 的已交付能力, 但全部依赖手工验证; 任何重构都可能静默破坏甲方场景。这是 tests/ 覆盖图谱中最大的业务空洞。
   - Fix: 见建议清单 #4-#7 (全合成 fixture 即可, 无需真实样本)。

6. **部署制品与 app_config.json 数据库名不一致**
   - File: `config/app_config.json` `database.database: "vector_db"` vs `scripts/run.sh:30` / `docker-compose.yml:9` 的 `POSTGRES_DB=m1_statements`
   - Why: M1/M2 主路径走 DATABASE_URL/PGDATABASE_URL 环境变量不受影响, 但遗留 RAGService (config_loader 路径) 按 app_config 会连一个部署中不存在的库。开发机上可能手工建过 vector_db, 掩盖了该问题。
   - Fix: 统一为 m1_statements, 或在 app_config 注释中声明该节仅适用 Windows 开发环境。

7. **测试门控策略不一致: 无条件跳过 4 个文件, 真集成测试却无护栏**
   - File: `tests/conftest.py:27-52`
   - Issue A: `test_websocket` (1)、`test_web_integration` (7)、`test_core_service` (2)、`test_hmm_memory` (1) 被**无条件**跳过 (共 11 个, 加 e2e_browser 2 个 = 13 skipped)。其中 test_web_integration 是 chat/knowledge 路由**唯一**的覆盖, 跳过后这两个路由器零运行测试。无条件跳过意味着即使有人修好了 fixture, 测试依然静默不跑 — 制造虚假覆盖安全感。
   - Issue B: 反向问题 — `TestMultiTurnIntegration` (`tests/test_m2_multiturn.py:319-326`) 标了 `@pytest.mark.integration` 但**无 skipif 护栏**, PGVector/:8004 不在时是 FAIL 而非 SKIP; pytest.ini 也未设 `addopts -m "not integration"`。基础套件因此不封闭 (hermetic)。
   - Issue C: `_has_server()` (`tests/conftest.py:15-21`) 定义后从未被调用 — 死代码, 正是为解决 Issue B 准备却没接上。
   - Fix: 给集成测试接 `_has_server` 式 skipif 或 pytest.ini 默认排除 integration; 对 4 个被跳文件做出 "修复启用 or 归档 docs/archive" 的明确决定。

### Minor (Nice to Have)

1. **冗余同义词变体**: `基金总市值(元)` 与 `基金总市值（元）` 同时声明 — 归一化已剥离全角括号, 二者重复 (`config/m1_table_schema.json` 交易对账单/证券持仓明细多处)。无害, 但增加维护噪音。
2. **app_config.json 可移植性**: 明文本地开发库密码 (docker 默认值, 低风险)、绝对路径 `/home/testuser/wzh/models/hf/bge-reranker-v2-m3`、`rerank.device: "cuda"` — 单机部署可接受, 建议注释标明 dev-only。
3. **agent_llm_config.json 模型路由陈旧**: 仅遗留 chat 路径消费 (`src/agents/agent.py:45`, `src/biz/agent_service.py:34`), 指向云端 SiliconFlow DeepSeek-V3.2 (需 SILICONFLOW_API_KEY), 与现行本地 :8004 主力栈脱节; 该路径零测试, 无 key 时行为未验证。建议标注 legacy 或改指本地端点。
4. **死常量**: `tests/test_m1_schema_api.py:46` 的 `_LOCAL_SCHEMA_PATH` 指向真实 config 路径但从未使用 (fixture 已正确用 tmp_path), 易误导后来者以为测试会写真实 config。
5. **pytest 标记未用**: pytest.ini 注册了 `e2e`/`slow` 但无任何测试使用; `integration` 被使用但未配套默认排除。
6. **m1 遗留 HTTP 端点**: `/api/m1/sample|extract|review` (`src/web/routers/m1.py:48-63`) 仅服务层有冻结测试覆盖, HTTP 包装层无测试 (低风险, 包装极薄)。

---

## 覆盖图谱与比例 (数据)

**Mock vs 集成比例** (240 collected):
- 真集成 (需 live PG/:5050/:8004/playwright): **7 个 ≈ 3%** — health_embeddings 2, persistence 2, multiturn 1, e2e_browser 2
- 跳过: 13 (11 无条件 + 2 playwright 门控)
- 其余 ~220 为单元/mock/进程内 TestClient; mock 密度最高: test_m2_rag (30 处 mock 引用), test_m1_ocr_fallback (26), test_m2_multiturn (24), test_m2_compare (18)

**无测试的业务路径** (按风险排序):
1. 坐标重建表格解析 (NCAMC 竖排) — 已交付能力, 零测试
2. .msg 邮件正文解析 — 已交付能力, 零测试
3. XLSX / DOCX 解析 — 已交付能力, 零测试
4. knowledge 路由器全部端点 (documents/collections/upload/traceability/rag-settings...) — 唯一覆盖被无条件跳过
5. chat 路由器全部端点 (/chat, sessions CRUD, /reset, /set_role, /suggestions) — 同上
6. collaboration 路由器 + websocket — 跳过
7. cache 路由器 (/stats, /clear) — 零测试
8. LLM 兜底映射的真实调用路径 (仅 unmapped 跟踪有测试, `tests/test_m1_parser.py:113`)
9. BearerAuthMiddleware 真实 app + 带 token 路径 (现仅合成 mini-app 验证, `tests/test_auth.py:36-50`)
10. 运维脚本 vlm_server_8007.py / responses2chat_proxy.py — 零测试 (运维件, 可接受)

---

## Recommendations

**流程/治理:**
- C1 修复前避免将本仓库以任何形式外发 (客户演示环境克隆、截图含 tests/ 等)。
- schema 演进走 "config/ 为唯一真相源 + Loop B 校验 config" 的路线, 冻结清单与运行时真相同步 (需 Loop D 授权改 frozen_hashes.txt)。
- 对 conftest 无条件跳过的 4 个文件做出明示决定 (修复 or 归档), 不要让 "13 skipped" 成为永久状态。

**建议新增测试清单 (只建议, 本次未写):**
1. **schema 冲突哨兵**: 断言任一表内同一源同义词不得映射到两个标准字段; 同一逻辑并入 `_validate_schema` 使 API 写入时拒绝 (422)。当前会报出 8 处存量冲突 → 先修数据再合入哨兵。
2. **`对账起止日期` 语义锁定测试**: 明确期望行为 (拆分为开始/结束 或 唯一目标字段) 并固化。
3. **Loop B 增强**: 校验 config/m1_table_schema.json 哈希, 或校验 config ⊇ samples 超集关系 + 冲突数单调不增。
4. **坐标重建单元测试**: 用 pymupdf 生成含竖排 span 的合成 PDF, 断言 `_coordinate_table_reconstruction` 还原行列 (NCAMC 布局最小复现)。
5. **.msg 解析测试**: mock `extract_msg` 的 htmlBody 返回合成 HTML 表格, 断言表格抽取 (不依赖真实邮件)。
6. **XLSX 解析测试**: openpyxl 内存生成工作簿 → parse → 断言标准字段映射。
7. **DOCX 解析测试**: python-docx 内存生成带表格文档 → parse → 断言。
8. **LLM 兜底映射测试**: mock :8004 响应, 断言 unmapped 列经 LLM 后落入标准字段且 disposition 正确。
9. **真实 app 带 token 认证测试**: M1_API_TOKEN 已设的 main.app 上断言 401/200。
10. **集成护栏**: TestMultiTurnIntegration 加服务可达性 skipif (接 `_has_server`), 或 pytest.ini `addopts = -m "not integration"`。
11. **被跳文件处置**: 修复启用或归档 test_websocket / test_web_integration / test_core_service / test_hmm_memory。
12. **脱敏哨兵**: 回归测试断言 tests/ 下不出现真实样本标识模式 (客户名、`sample_jiaxing|fuxi` 派生值、12 位客户号模式), 防止再次泄漏。

---

## Assessment

**Ready to merge?** With fixes (针对现状存量, 非 PR 审查)

**Reasoning:** 解析器核心确定性良好、冻结合约测试真实有效、任务点名的 5 条业务路径均有覆盖, config/ 三份文件均被代码引用 (app_config=遗留 RAG 栈, agent_llm_config=遗留 chat 栈, m1_table_schema=解析器运行时生效)。但 Critical 级的真实甲方数据入仓必须在任何对外动作前清除; schema 冲突 + 冻结清单与运行时真相脱节属于会在下次 schema 演进时咬人的结构性隐患, 建议优先于 Phase 3 后续开发修复。

END-OF-REPORT
