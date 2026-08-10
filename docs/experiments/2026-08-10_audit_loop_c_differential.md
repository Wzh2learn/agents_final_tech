# Loop C Differential 审计报告 — 2026-08-10

> 状态: 活跃 | 审计范围: `git diff a7f8282..HEAD`（56 commits, e715dc5 为 HEAD）
> 基线: 2026-08-06 审计基线之后全部变更 | 前序审计: `2026-08-06_differential_phase3_to_head.md`（33 findings）
> Loop B 状态: **PASS**（`logs/graph/verify-report.json`, 2026-08-10T23:38, head=e715dc5, frozen_nodes/pytest/api_anchors 全过）
> 审计者: Loop C（只读审计；未修改 src/、tests/、samples/ 任何文件）

---

## 统计汇总

| 严重度 | 数量 | 编号 |
|---|---|---|
| CRITICAL | **0** | — |
| HIGH | **1** | F1（条件性，当前不可达） |
| MEDIUM | **6** | F2, F3, F4, F10, F13, F18 |
| LOW | **8** | F5, F6, F7, F8, F11, F14, F15, F19 |
| INFO | **5** | F9, F12, F16, F17, F20 |

**一句话结论**: T4 建议映射端点核心机制（fail-closed 回滚、无 shell 注入、无路径穿越、测试 10/10 绿）是健全的；但存在 1 条条件性冻结节点写入通路（F1）、门禁覆盖盲区（F3/F10）、reject 未设防（F2），以及甲方可见文档 docs/23 的 4 处数字漂移（F18）。**判定: CONDITIONAL**（见文末）。

**红线核查（全部通过）**:
- 冻结节点在 a7f8282..HEAD 范围内**零改动**: `tests/test_m1_service.py`、`docs/m1_schema/`、`scripts/graph/frozen_hashes.txt`（`git diff --name-only` 为空）。
- 冻结哈希现值复核: `tests/test_m1_service.py` = `faa7565a…` ✓、`~/wzh/m1_samples/m1_table_schema.json` = `73d4f46e…` ✓，与清单逐项一致。
- `~/wzh/m1_samples/` 样本目录在 diff 中无改动（唯一命中是 docs/ 下的截图文件名）。
- tests/ 变更均为**新增**测试文件 + `conftest.py` 一处改动（将 legacy `test_e2e_browser` 从"无 playwright 才跳过"改为"一律跳过"，理由: 该测试面向旧 :5000 UI、headless=False、非 M1/M2 范围，commit 02b768e 有说明）。未见篡改既有断言以规避失败的行为；冻结测试文件本体未动。

**实测证据**:
- `pytest tests/test_m1_schema_suggestions.py tests/test_bm25_stdio_hygiene.py tests/test_m1_cli_robustness.py tests/test_m1_ingest_doc_type.py tests/test_rag_doctype_rescore.py` → **36 passed**。
- `scripts/m1_scenario1_regression.py --quick` @HEAD → **PASS: 12 pass / 0 warn / 0 fail / 3 skip(OCR)**, 0.9s。
- 全 diff 危险模式扫描（shell=True / os.system / eval / 硬编码密钥）→ **零命中**。

---

## P1 — T4 schema-suggestion 端点（src/web/routers/m1.py + tests/test_m1_schema_suggestions.py）

### F1 [HIGH，条件性] Web apply 端点缺少冻结 schema 守卫，config 缺失时可写穿冻结运行时 schema

- **证据**:
  - `src/web/routers/m1.py:460` `schema_path = _get_schema_path()` → `parser.resolve_schema_path()`；`scripts/m1_statement_parser.py:52-56` 解析顺序为 config/ 优先、**否则回退 `~/wzh/m1_samples/m1_table_schema.json`（冻结运行时 schema）**。
  - `m1.py:471-473` 将 merged schema 直接写回 `schema_path`；`m1.py:487-488` 回滚时同样写回。
  - 对照: CLI 脚本对同一目标有显式守卫（`scripts/m1_apply_schema_suggestions.py:124-128` `--allow-frozen` 拦截），**Web 端点路径无等价检查**。
  - 附加效应: 回滚写回使用 `json.dumps(json.load(...))` 紧凑序列化（`m1.py:461-462`），即使内容语义不变也会**改变冻结文件字节 → md5 漂移 → Loop B frozen_nodes 告警**；且 `_suggestions_path()`（`m1.py:389-391`）会在 `~/wzh/m1_samples/` 内创建 suggestions 文件（该目录为只读红线区）。
- **当前可达性**: **不可达**——`config/m1_table_schema.json` 现存（已验证），`resolve_schema_path()` 恒返回 config 路径；且不存在可覆盖 schema 路径的环境变量（parser 仅有 `M1_SCHEMA_SUGGESTIONS`，无 `M1_SCHEMA_PATH`）。触发前提 = config 文件被删除/未部署。
- **风险**: 一旦前提成立（部署漏配、误清理），一次 apply（甚至随后的"回滚"）即构成对冻结节点的写入，违反 frozen_hashes 治理红线。
- **建议**: apply 端点在写入前断言 `os.path.abspath(schema_path) == os.path.abspath(parser.LOCAL_SCHEMA)`，否则 403 拒绝；或复用 CLI 的 frozen 判定逻辑。成本低（3 行），属红线防御，建议本轮必修。

### F2 [MEDIUM] reject 端点无 admin 门禁（与 apply 不一致）

- **证据**: `m1.py:509-523` `reject_schema_suggestions` 未调用 `_check_admin`；对照 apply 端点 `m1.py:446` 有调用。前端对两者都发送 token（`src/web/static/m1.js:880-884`），后端只对 apply 校验。
- **影响**: reject 虽不改 schema，但会把建议永久移入 `rejected`（"不再重复推荐"，`m1.py:517-521`）。在默认无 token 部署下（`.env.example` 未登记 `M1_ADMIN_TOKEN`，启动仅 warning，`m1.py:200-203`），任何客户端可批量拒绝建议，**静默关闭自学习闭环**——属状态破坏而非只读。
- **建议**: reject 与 apply 同样过 `_check_admin`；测试补一条 reject 401 用例（现 TestAdminGate 只覆盖 apply，`tests/test_m1_schema_suggestions.py:237-250`）。

### F3 [MEDIUM] apply 门禁（--quick）对 57% 的待确认建议是盲区

- **证据**:
  - 端点门禁固定 `--quick`（`m1.py:475-478`）；quick 跳过全部 3 个 OCR 样本（`scripts/m1_scenario1_regression.py:116,132-135`，本次实跑 3 skip 复现）。
  - 当前 21 条 pending 建议的来源分布（`config/schema_suggestions.json` 实数）: OCR 样本来源 **11 条**（华泰紫金 8/TraFax 2/WaveFax 1）+ 上传临时文件来源 **1 条**（`tmp2np272vj.pdf`，样本不存在）+ 常规样本 9 条。**12/21（57%）建议对应的样本从不被 quick 门禁验证，其中 4 条为 high confidence**。
  - 这些建议涉及的恰是 schema 的 `证券持仓明细`/`交易对账单` 字段（ Counter: 交易对账单 12 / 证券持仓明细 9），apply 后门禁仍显示 PASS——**门禁给予的是虚假信心，而非对变更的验证**。
- **缓解事实**: quick 仍覆盖 12 个确定性源，能拦住全局性 parser/schema 破坏；单样本同义词合并的局部劣化（尤其 OCR 源）确实漏检。
- **建议**: 短期在 apply 响应 `hint` 中如实注明"OCR 来源建议未经门禁验证"；中期按建议的 `sample` 字段做定向 before/after（复用 `m1_apply_schema_suggestions.py` 的 summarize 比对），或对含 OCR 来源建议的 apply 强制全量门禁并在 UI 提示耗时。

### F4 [MEDIUM] async 端点内同步 subprocess（≤300s 阻塞事件循环）+ 默认无鉴权可触发

- **证据**: `m1.py:475-480` `subprocess.run([...], timeout=300)` 位于 `async def` 内；默认部署无 `M1_ADMIN_TOKEN`（见 F2），任何客户端可反复触发 apply。
- **影响**: workers=2 的 :5050 服务可被 2-4 个并发 apply 请求完全阻塞（每请求最长 300s）。与既有 **F5 known_risk**（memory/THREADS.md:48，2026-08-06 用户裁定"async 端点同步阻塞"归 B 阶段处理）同一模式——本条是该已知风险在新端点上的又一实例，且触发成本更低（无需真实问答流量）。
- **建议**: 若 B 阶段前不动结构，至少在端点入口做单飞（single-flight）锁/信号量，防并发重复门禁；并把本条并入 known_risk 台账。

### F5 [LOW] 回滚非字节级 + BOM 边界

- **证据**: 回滚备份为 `json.dumps(..., ensure_ascii=False)` 紧凑格式（`m1.py:461-462`），而生产 schema 文件为 indent=2（`config/m1_table_schema.json` 实测）——回滚后**格式漂移**（语义不变）。测试 `tests/test_m1_schema_suggestions.py:190-191` 断言"byte-for-byte 恢复"之所以通过，仅因 fixture 本身是紧凑写入（:93-94）。
- BOM: `_read_schema` 用 `utf-8-sig`（`m1.py:220`，容忍 BOM），但 apply 备份读取用 `utf-8`（`m1.py:461`）——带 BOM 的 schema 会在备份行抛 JSONDecodeError（500，merge 之前，无副作用）。当前文件无 BOM（xxd 实测），为潜伏问题。
- **建议**: 备份改为 `open(..., "rb").read()` 原样字节备份、回滚原样写回；测试 fixture 改用 indent=2 以对齐生产。

### F6 [LOW] retarget 匹配按 (raw_column, table) 首命中，重复条目语义脆弱

- **证据**: `_match_key` 忽略 `standard_field`（`m1.py:424-429`，docstring 说明是有意支持 UI retarget）；apply 取首命中即 break（`m1.py:449-455`），但移除阶段删除**所有**同键条目（`m1.py:501-502`）。harvest 侧去重键是三元组 `(table, raw_column, standard_field)`（`scripts/m1_statement_parser.py:1658,1663`），**结构上允许同 (raw, table) 出现多个不同 standard_field 的条目**——届时 apply 只落第一条、却清掉全部。
- **现状**: 当前 21 条 pending 中 (raw_column, table) 重复数为 **0**（实测），暂无实际损害。
- **建议**: harvest 或写入侧对同 (raw, table) 多目标情形做显式策略（保留最高置信/合并 reason），或 apply 按三元组精确匹配、retarget 单独传 `original_standard_field`。

### F7 [LOW] 建议文件路径双轨：M1_SCHEMA_SUGGESTIONS 覆盖只对 harvest 生效

- **证据**: parser 侧建议路径可被 `M1_SCHEMA_SUGGESTIONS` 覆盖（`scripts/m1_statement_parser.py:1591-1595`），Web 端点侧固定取 `dirname(schema_path)/schema_suggestions.json`（`m1.py:389-391`）。若有人设置该环境变量，harvest 写 A 文件、UI 读写 B 文件，静默分叉。
- **建议**: 端点侧同样尊重该环境变量，或在文档中声明该 env 仅 CLI 用途。

### F8 [LOW] 上传路径产生的建议以临时文件名为 sample 溯源，永远无法复验

- **证据**: `/parse-file` 用 `NamedTemporaryFile` 处理上传（`m1.py:92-105`），parser 将 `result["file"]`（临时 basename）写入建议的 `sample` 字段——现存实例: `tmp2np272vj.pdf`（`config/schema_suggestions.json` 中 1 条 high confidence），该文件在任何样本目录均不存在（实测）。CLI 复验对其只能 warn 跳过；门禁亦不覆盖（见 F3）。
- **建议**: harvest 时若 sample 名匹配 `tmp*` 模式，要么不落 sample 字段，要么在 UI 标注"不可复验来源"。

### F9 [INFO] 安全面核查通过项

- **admin gate 绕过**: 未发现其他绕过路径。PUT/POST/DELETE schema CRUD 与 apply 均过 `_check_admin`；GET 类（`/schema`、`/schema-suggestions`）按 Phase 2 既有设计公开。token 比较为 `!=`（`m1.py:236`）非常量时间，对此类内部 token 实际风险可忽略。
- **路径穿越**: 所有文件路径均由服务端配置推导（`resolve_schema_path`/`LOCAL_SCHEMA`），**无任何请求参数进入路径拼接**，不存在穿越向量。
- **subprocess**: 列表参数、无 shell、脚本路径与 cwd 均由服务端推导（`m1.py:475-480`），无注入面。
- **回滚正确性（常规路径）**: 备份先于 merge 获取；门禁 FAIL/异常 → 恢复备份 + 清理 `.merged` + 建议保持 pending（`m1.py:486-493`，测试 `test_apply_gate_fail_rolls_back` 覆盖）；门禁子进程崩溃无 PASS 标记 → 判失败，**fail-closed** ✓。
- **热加载声明属实**: `parse-file` 每请求重新 `Schema.load`（`m1.py:98`），apply 成功后无需重启 ✓。
- **前端 XSS**: 建议面板所有插值均经 `esc()`（`src/web/static/m1.js:838-861`）✓；retarget 下拉仅含该表真实字段 ✓。
- **测试质量**: 10 用例覆盖 GET/apply 成功/retarget/无匹配/门禁失败回滚/零合并/reject/admin，且 mock 了 subprocess 与 merge 模块、不触碰真实 config/（`tests/test_m1_schema_suggestions.py:53-106`）——本轮全部通过。

---

## P2 — 回归门禁与 schema 自学习脚本

### F10 [MEDIUM] CLI 复验默认样本目录错位 + 无样本时不拦截写回

- **证据**:
  - `scripts/m1_apply_schema_suggestions.py:112-113` 默认 `--samples-dir ~/wzh/m1_samples`（扁平目录），但 21 条建议中 4 个来源样本位于 `~/wzh/m1_samples/scenario1/attachments/`（华泰紫金/TraFax/WaveFax/233222LU 中 3 个转发件）。实测: 默认目录下仅 `sample_20260506_233222LU.pdf` 存在，其余 4 个来源均 MISSING → 触发 `:138-142` 的 warn 跳过。
  - **默认参数下 CLI 只能复验 5 个来源样本中的 1 个（9/21 条建议）**；若剩余建议全部来自缺失样本，则落入 `:156-161` 分支: "[warn] 无可复验样本，仅合并 schema（不验证）"，此时 `--apply` **直接写回，无门禁**。
  - 该脚本同时是端点 apply 的 merge 提供方（仅用 `merge_into_schema`，验证走端点自己的 quick 门禁），故端点不受此条直接影响；风险在手工 CLI 使用。
- **建议**: 默认 samples-dir 改为（或追加扫描）`scenario1/attachments`；"无可复验样本"时 `--apply` 应要求显式 `--force` 才写回。

### F11 [LOW] 退出码契约与实现不符

- **证据**: `scripts/m1_scenario1_regression.py:20` 文档声称"退出码: 0=PASS 1=FAIL 2=环境/文件缺失"；实测 `--baseline /nonexistent.json` → 未捕获 `FileNotFoundError` traceback，**rc=1**（复现于本次审计）。
- **影响**: 对端点门禁无碍（看 stdout PASS 标记，fail-closed ✓）；对 Loop B/CI 挂载场景，"环境缺失"与"真 FAIL"被混同为 1，排障口径失真。
- **建议**: main 内捕获文件缺失类异常 → exit 2，与文档对齐。

### F12 [INFO] 判定口径评估

- **方向感知合理**: 确定性样本命中率提升 → WARN 不 FAIL（`:99-107`）；OCR 样本 ±10pp/±1 表容差（`:77-98`，与 baseline `tolerance` 一致）；无结果判 FAIL（`:138-141`）——fail-closed 方向正确，与 commit 6c2fd02 "回归门控方向感知" 声明一致。
- **口径局限（固有，非缺陷）**: 门禁只比 `table_count` + 逐表 `hit_rate`，不验证勾稽、不验证字段语义——同义词错配到"同样能命中"的错误字段时，命中率不变、门禁放行。语义正确性的控制点是人工在 UI 下拉选择（retarget），门禁职责是稳定性而非语义，此分工可接受，但应在 docs/26 的 walkthrough 中写明"门禁不保语义"以免误信。
- `--rebuild` 直接覆写基线无二次确认（`:153-183`，docstring 已注"慎用"）；`--force` 绕过回归拦截（`:183-185`，docstring 已注）——均为显式 opt-in，INFO 记录。

---

## P3 — RAG 侧变更（doc_type / BM25 / eval）

### F13 [MEDIUM] judge "不见期望答案防泄漏" 声明与实现不符

- **证据**:
  - `scripts/m2_eval_judge.py:5` docstring: "faithfulness 忠实度：答案只使用检索到的内容（**judge 不看期望答案，防泄漏**）"。
  - 实际 `JUDGE_PROMPT` 含 `[参考期望]` 段且 `{expected}` 被真实注入（`scripts/m2_eval_judge.py:63-64,100`）；隔离仅靠 prompt 指令"仅 numeric_correctness 可用；忠实度判断禁止参考"（`:63`）。
  - 同一声明在 `docs/experiments/2026-08-08_eval_baseline.md:42`（资产清单）重复出现。
- **影响**: 这是**指令级隔离而非结构级隔离**——judge 完全能看到期望答案，faithfulness/citation 维度存在被期望答案锚定的可能。docs/23 对外声称的"AI 评审四维均分 5.0/5.0"的 evidential strength 因此打折（叠加 F20 的 rubric 放宽史）。
- **建议**: 要么修 docstring/eval 文档为"期望答案注入但限 numeric 维度使用（指令级隔离）"，要么把 faithfulness/citation 的 judge 调用改为结构性剔除 expected 字段（双 prompt 方案，成本小）。

### F14 [LOW] doc_type 打标脚本默认即写库，且覆盖手工标签；"非破坏性"表述需限定

- **证据**: `scripts/m1_rag_tag_doctype.py:51-53` 唯一 flag 是 `--dry-run`（默认 False → **默认写**）；`:81-83` 凡 `doc_type != new_type` 一律入变更计划（**不是只补空值**，手工改过的标签会被规则覆盖）。
- **核实**: commit 04477ab 的"non-destructive"声明对 `document`/`embedding` 列**属实**（UPDATE 仅 `cmetadata` jsonb 合并，`:96-105`，无 DELETE/INSERT，幂等 ✓）；但 argparse description "非破坏性标记"（`:50`）对 metadata 本身是夸大。
- **建议**: 保持默认写可以（一次性迁移工具），但把 description 改为"按规则重算 doc_type（会覆盖既有值）"，并在 docstring 标注"手工修改的 doc_type 会被下次运行覆盖"。

### F15 [LOW] M2_ENABLE_BM25 未登记 .env.example；ingest docstring 仍称"混合检索"

- **证据**: `src/biz/rag_service.py:351` `M2_ENABLE_BM25` 默认 `"false"`（与 commit 13a37b8 "零增益→flag 默认关" 声明一致 ✓），但 `.env.example` 无该条目（grep 零命中）；`scripts/m1_rag_ingest.py:8` docstring 仍写"检索走 RAGService.smart_retrieve（**向量 + BM25 混合**）"——默认路径现为纯向量，docstring 过时。
- **补充事实**: BM25 从"无条件调用恒空 stub"变为"flag 控制真实现"，默认检索结果与旧行为等价（旧 stub 恒返回空）✓；stdio 卫生已修（`src/tools/bm25_retriever.py:102,108,117,120,199` 全部 `file=sys.stderr`，静态扫描测试守门 `tests/test_bm25_stdio_hygiene.py:18-24`）✓。
- **建议**: `.env.example` 登记 `M2_ENABLE_BM25=false`（含"零增益、实验用"注释）；更新 ingest docstring。

### F16 [INFO] P3 声明核对通过项

- **rescore 默认行为**: doc_type rescore 无 flag、默认启用，但由查询内容门控（query 含 "ocr" 子串，`src/biz/rag_service.py:39,814-815`）；非 OCR 查询零影响、无 doc_type 的 chunk（knowledge_base）跳过不改分（`tests/test_rag_doctype_rescore.py:77-87,109-114` 覆盖）——"对既有检索非破坏"声明在排序层面属实 ✓。小代价: OCR 类查询对每个集合多发一次 filter 向量查询（`rag_service.py:335-338`）。
- **E4 修复核实**: 前序审计 E4（`m1_rag_ingest.py` 传 `document=""` 致 email_notice 恒 False）已修——现为真实 chunk 文本（`scripts/m1_rag_ingest.py:332-334,344`），测试钉住（`tests/test_m1_ingest_doc_type.py:61-70`）✓。
- **eval 三层口径**: 确定性 16 题全过才 PASS（`scripts/m2_eval_deterministic.py:126,181`）；judge 不阻塞（`m2_eval_judge.py:210` 恒 return 0；`run_eval.sh:77` 仅按 M1/M2 RC 决定退出）✓ 与声明一致。
- ingest 无新增 CLI flag，doc_type 为每 chunk 无条件附带的**新增 metadata 字段**，不改既有数据 ✓（非 opt-in 但仅加法）。

### F17 [INFO] 测试计数口径再现（commit 9f3e655: "16 unit tests" 实为 15）

- **证据**: `tests/test_rag_doctype_rescore.py` 实际 15 个 `def test_`（实测），commit message 声称 16。
- **处置**: 该漂移已在前序台账登记（memory/THREADS.md E7 "记录漂移更正"），无需重复动作，仅在本报告留痕。

---

## P4 — 文档数字漂移（docs/23 vs 基线/原始工件）

### F18 [MEDIUM] docs/23（甲方发送版）战绩表 4 处数字与原始工件/现行基线不符

逐项证据（一轮原始 = `~/wzh/m1_samples/scenario1/final_results.json` 2026-08-03；二轮基线 = `tests/baselines/scenario1_baseline.json` + `docs/experiments/2026-08-08_eval_baseline.md:60`；本次审计独立复算）:

| # | docs/23 位置 | 文档值 | 实测/基线值 | 性质 |
|---|---|---|---|---|
| 1 | `docs/23_甲方阶段汇报.md:38,107` | 华泰紫金一轮 **42.9%** | 一轮原始 **[35.7]**（final_results.json，本次复算 ✓；docs/archive/22:600,647 同）；42.9 实为另一样本 233222LU 的数字（memory/STATE.md:25），疑为样本张冠李戴 | 不一致/无依据 |
| 2 | `docs/23_甲方阶段汇报.md:41` | 国金一轮 **80%** | 一轮原始 **[70.0]**（复算 ✓） | 不一致 |
| 3 | `docs/23_甲方阶段汇报.md:39` | TraFax "63.6% → 81.8%" | 逐表 [50, 81.8, 63.6] → [50, 81.8, 81.8]，**样本均值 65.1 → 71.2**；50% 的表两轮从未改善 | 挑选最优单表值代表整份（误导） |
| 4 | `docs/23_甲方阶段汇报.md:27` | "结构化产出 **30** 张标准表" | 现行基线 table_count 合计 **31**（NCAMC 0→1 表）；30 仅对一轮原始成立 | 口径过时（一轮数 vs 2026-08-09 基线） |

- **加重情节**: `23_甲方阶段汇报_发送版.docx` 已按该 .md 重新生成（commit c05d3aa，`scripts/build_doc23_docx.py`）——漂移数字已进入可分发载体；且该数字正在继续扩散（审计期间观测到 Loop A 并发写入 `memory/DECISIONS.md` 的 2026-08-10 条目仍引用"华泰 42.9%→100%"）——建议本轮一并校正。
- **方向说明**: #1/#2 是高估一轮基线（改善幅度被**低估**），#3 是高估二轮现状，性质混合，非单向粉饰；但对外文档必须以工件为准。
- **建议**: 按 final_results.json + baseline 修正 4 处；TraFax 改逐表表述或注明"样本级均值"；修正后重跑 `build_doc23_docx.py` 重新生成发送版。

### F19 [LOW] docs/23 附录 B 与叙事层的依据缺失/时序错位

- **证据**:
  - `docs/23_甲方阶段汇报.md:95-102` 附录 B 全部耗时数字引用的 `experiments/2026-08-04_rehearsal/demo_rehearsal.log` **不存在**（该目录实测仅 7 PNG + 1 样例 PDF）。注意 `docs/INDEX.md` 对该目录的描述（"彩排截图 7 张 + demo 日志"）同样与事实不符（日志不存在），已在本次审计中一并更正。
  - `:29,49` "扫描件单份 27-78 秒": 一轮实测 OCR parse_ms 16.4-28.7s，07-31 基准 27.5/70.9s，**"78" 全仓无出处**。
  - `:30` "一轮 15/15=100%": 08-03/08-04 时点口径为 **14/15**（OCR 元查询未修），15/15 是 08-05 修复后状态（memory/THREADS.md:13,35）——归属时点错位；且一轮 15 题题集不在仓库（fixture 仅 v1=20 cases / v3=16 题）。
  - `:30` "扩充至 16/16（新增 4 道对抗题）": 15+4≠16，实为 v3=12 基础+4 对抗（净增 1 题），表述失真。
  - `:100` "08-05 修复" vs eval_baseline.md:17 / fixture:3 注释"08-07 修复 case"——跨文档日期口径不一（实为 08-05 修复、08-07 生产口径复验）。
- **建议**: 附录 B 要么补回日志工件、要么改为引用现存的 `2026-08-05_rehearsal_post_embedding/rehearsal_report.json` 口径；其余按实测改写。

### F20 [INFO] 口径提示（数字本身一致）

- **"四维均分 5.0/5.0"**: 与最新复测一致（`logs/graph/eval/m2_judge_report.json` 实测四维 mean=5.0, n=16；eval_baseline.md "2026-08-09 二次复测" 节），但经历 rubric 放宽（拒答 citation 豁免，commit 7fafeb7）后才达成，且叠加 F13 的期望答案注入——引用时建议注明口径演化。
- **"直连路约 2 秒/轮"**（doc23:32）: eval_baseline.md:16 实测直连 ~3s（且该轮多数请求为 18s 超时回落）——轻度漂移，建议改 ~3s 或注明口径。
- **核对无漂移项**: 9 封 .msg / 674 行映射表（234 代码对）/ 15 源 / 嘉合 93.8%（= [87.5,100] 平均）/ WaveFax 71.4→85.7 / 华泰二轮 100% / 8 字段沉淀 / 16/16（fixture 实数 16 ✓）/ agent 路 15-20s / M1 15/15 与 quick 12/12 / tolerance ±10pp±1 表 / eval:60 基线行逐项吻合。

---

## 范围外观察（未深审，仅危险模式扫描）

- `src/biz/opencode_adapter.py`（+194）、`scripts/responses2chat_proxy.py`（+338/-104）、`scripts/preprocess_msg.py` 等由前序 2026-08-06/08-07 审计覆盖大部分；本轮全 diff grep（shell 注入/密钥）**零命中**。
- `tests/conftest.py` 改动（legacy e2e 一律跳过）理由成立且范围最小化，但该文件属 tests/ 基础设施，按 Loop C 红线规则**登记为已观察项**: 无篡改既有断言行为，未发现为规避失败而改测试的迹象。
- `scripts/build_doc23_docx.py` 为纯本地 md→docx 转换，无外部调用 ✓。
- 文档治理: `2026-08-08_eval_baseline.md` 与 `2026-08-09_demo_script.md` 一直未登记进 `docs/INDEX.md` experiments 表（本次审计已补登，连同本报告条目）；`2026-08-09_demo_video/` 目录仍未登记，建议 Loop A 下轮补齐。

---

## 判定

**CONDITIONAL**（非驳回；红线未破，核心机制健全）

解除条件（建议在下一轮发送版 docx 分发前完成 ①②）:
1. **F1（HIGH）**: apply 端点增加冻结 schema 守卫（断言写入目标 == LOCAL_SCHEMA），或等价防护 + 回归测试。
2. **F18（MEDIUM）**: docs/23 四处数字按工件修正并重新生成发送版 docx。
3. **F2/F3/F4（MEDIUM）**: reject 加 admin 门禁；apply 响应/文档如实标注 quick 门禁盲区；并发 single-flight。可并入下一迭代，但 F2 建议与 F1 同批（均为端点一行级改动）。
4. **F10/F13（MEDIUM）**: CLI 无样本写回需显式 --force；judge 防泄漏声明修正或结构性隔离。

### 给 Loop D 的建议

- F1 属冻结红线防御，建议列为 Loop A 最高优先（改动 ≤3 行 + 1 测试）。
- F18/F19 涉及甲方可见物，建议走"修文档 → Loop C 复核数字 → 重生成 docx"闭环，勿与代码改动混 commit。
- F4 与既有 F5 known_risk 同源（async 阻塞），若 B 阶段（网关化）排期仍远，建议先批 single-flight 补丁。
- 建议把 `M2_ENABLE_BM25`、`M1_ADMIN_TOKEN` 补进 `.env.example`，并在 docs/20 部署指南标注"生产部署必须设置 M1_ADMIN_TOKEN"（当前默认无保护）。

---

## 附录：审计方法

- 角色与权限: `scripts/graph/loop_c_audit_prompt.md`（只读；不改 src/tests/samples）。
- diff 范围: `git diff a7f8282..HEAD`（56 commits, 101 files, +6486/-272）。
- 并行事实核查子代理 ×3（parser 语义 / RAG 变更 / 文档数字），关键 MEDIUM+ 发现均由主审计独立复核（frozen md5、quick 门禁实跑、final_results.json 复算、judge prompt、tag 脚本默认值、测试计数）。
- 实跑: pytest 36 项 ✓；scenario1 --quick @HEAD PASS ✓；冻结哈希比对 ✓；危险模式/密钥全 diff 扫描 ✓。
