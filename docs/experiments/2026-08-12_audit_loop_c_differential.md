# Loop C Differential 审计报告 — 2026-08-12

> **判定: CONDITIONAL（ACCEPTED with conditions）**
> 审计范围: `git diff 5535bdf..504810c`（3 commits / 12 files / +168 −131）
> 前序审计: `2026-08-10_audit_loop_c_differential.md`（CONDITIONAL, F1–F20）
> 审计者: Loop C（只读；未改 src/、tests/、config/、docs/23、冻结节点；未重启服务）
> 实测: quick 门禁 @HEAD 复跑 PASS（12 pass/0 warn/0 fail/3 skip）；冻结 md5 双复核 ✓

---

## 判定摘要

| 维度 | 结论 |
|---|---|
| 范围内变更（schema +2 同义词落地 / 基线 rebuild / docs 台账） | **可接受**；红线全过；仅 1 处 diff 引入的潜伏映射冲突（FC-1）需在下批 apply 前修复 |
| 重点① 近义词映射冲突 | 发现 1 处**本次新引入**的表内碰撞（交易账号），根因=陈旧建议+merge 无碰撞检测；基金资产总额 无碰撞 |
| 重点② baseline rebuild 口径 | **一致**（同 parser/同 schema 解析/容差未动/14 案精确复现）；但 100.0 基线使门禁进入零容差粒度区（FC-3） |
| 重点③ docs/23 注记流程 | **合规**（表下加注 2 行、表体零改动、docx 同 commit 重生成、数字有基线背书） |
| 重点④ known risks 复评 | **双双复评为 HIGH 暴露（均为存量、非本 diff 引入、已台账延期）**：fail-open auth 为在产实况；F5 async 阻塞 route=on 在跑 |

解除条件（按优先级）：
1. **FC-1（MEDIUM，diff 引入）**: 删除 `config/m1_table_schema.json:501` 中 资产账号 下的 `交易账号` 同义词，或在 merge 侧加表内碰撞检测（见 FC-1 修复建议）+ 复跑 quick 门禁。
2. **FC-4（HIGH，存量）**: fail-open auth 保持 B 阶段最高优先；在 token 落地前**不得扩大 :5050 暴露面**；`.env.example` 补 `M1_API_TOKEN` 条目。
3. **FC-5（HIGH 可用性，存量）**: 延迟修复 a+b 在下一重启窗口落地；落地前评估临时将 `M2_OPENCODE_ROUTE` 置 off（用户裁定项）。
4. FC-2/FC-3/FC-6 为 LOW/INFO 级台账与门禁健壮性改进，并入下一迭代即可。

---

## 红线核查（全部通过）

- 冻结节点在 5535bdf..504810c **零改动**（`git diff --name-only` 对下列路径为空）:
  - `tests/test_m1_service.py` ✓（现值 md5 `faa7565a2b83b5b593389000b7ed72d7` 与 `scripts/graph/frozen_hashes.txt` 一致，本次实测）
  - `scripts/graph/frozen_hashes.txt` ✓
  - 冻结运行时 schema `~/wzh/m1_samples/m1_table_schema.json` ✓（现值 md5 `73d4f46e20e8eeb03532f4b4a8e55c0d` 与清单一致，本次实测）
  - 注: 任务书所称 `docs/m1_schema/frozen_hashes` 在仓库中不存在，冻结哈希清单实际位于 `scripts/graph/frozen_hashes.txt`（已按实物核查）。
- 审计期间**未重启任何服务**（:5050 PID 4086502 持续未动；仅以 `--quick` 只读跑门禁，其自写 report 属工具自身行为）。
- **docs/23 未被审计者改动**；审计者唯一写入为本报告。
- `~/wzh/m1_samples/` 样本目录在 diff 中无改动。
- 危险模式扫描（diff 内 shell/密钥/eval）: 本 diff 仅 JSON+md+docx，无代码面，零命中。

---

## 范围内变更清单（5535bdf..504810c）

| commit | 内容 |
|---|---|
| `270c686` | walkthrough 验收原子提交: apply 5 建议（实增 2 同义词）/ reject 14 / hold 6；schema +交易账号/+基金资产总额；基线 WaveFax 85.7→100（--rebuild）；quick 门禁 12 pass/3 skip |
| `3bc093a` | neat: 战绩入活文档（18/26/27/28/INDEX/STATE/THREADS） |
| `504810c` | docs/23 表下加注（表体不动）+ docx 重生成 |

文件面: `config/m1_table_schema.json`（+2 同义词）、`config/schema_suggestions.json`（applied/rejected/pending 重排）、`tests/baselines/scenario1_baseline.json`（WaveFax + created）、docs×7（INDEX/STATE/THREADS/18/26/27/28）、docs/23 md+docx。**无 src/、tests/ 代码改动** → 安全面变化全部来自配置数据与文档。

---

## Findings（按严重度排序）

### FC-4 [HIGH｜known risk 复评｜存量，非本 diff] fail-open auth 已是**在产实况**: 全接口无 token、绑 0.0.0.0、本次 apply 即无 token 执行

- **证据（代码）**:
  - `src/web/middleware.py:48-54` — `M1_API_TOKEN` 未设 → `dispatch` 直接放行全部请求（仅启动 warning `:50`）。
  - `src/web/routers/m1.py:201-204` 读取 token，`m1.py:233-238` `_check_admin` 在 token 未设时**直接 return**；同模式 `src/web/routers/m2.py:40-48`。
  - 无保护写端点清单: `PUT /api/m1/schema`（m1.py:306）、`POST /schema/tables`（:321）、`POST .../fields`（:339）、`DELETE field`（:355）、`DELETE table`（:372）、`POST /schema-suggestions/apply`（:442）、`reject`（:529）、`POST /api/m2/opencode/cleanup`（m2.py:126）。
- **证据（在产实况，本次实测）**:
  - `/proc/4086502/environ` 中 `M1_API_TOKEN`/`M1_ADMIN_TOKEN` **零命中**；`ss -tlnp`: `0.0.0.0:5050`；`ps`: `uvicorn main:app --host 0.0.0.0 --port 5050 --workers 2`。
  - 本次 schema apply（`config/schema_suggestions.json` applied_at=`2026-08-11 23:30`）即在无 `M1_ADMIN_TOKEN` 下经 Web 端点执行（`memory/THREADS.md:117` 遗留② 自认）。
- **影响**: 任何可达 5050 端口者可匿名**重写解析规则**（注入错误同义词 → 污染下游 M2 RAG 答案）、删表/删字段、批量 reject 关闭自学习闭环。与 CORS 默认 `*`（`src/main.py:137-140`）叠加仅属次生面（主向量是直连）。
- **既有缓解（不足以替代认证）**: F1 冻结守卫（m1.py:448-451）、写前结构校验（:314-316）、门禁失败字节级回滚（:477,:502-509）、single-flight（:452-455）。
- **处置状态**: 用户已裁定为 B 阶段延期项（THREADS.md:117）。**复评结论: 维持台账，严重度由前序 MEDIUM 级表述上调为 HIGH 暴露**——因部署面为 0.0.0.0 且本次真实写操作已在无 token 状态发生。条件 2 要求 token 落地前不得扩大暴露面。

### FC-5 [HIGH-可用性｜known risk 复评｜存量，非本 diff] F5: `m2_ask_endpoint` 在 async 端点内全同步调用 sidecar，单请求阻塞事件循环最长约 51s；route=on 在跑 + 无鉴权 = 匿名低成本 DoS

- **证据（代码）**:
  - `src/web/routers/m2.py:83-99` — `async def m2_ask_endpoint` 直接调用**同步** `opencode_adapter.ask_via_opencode`。
  - `src/biz/opencode_adapter.py` 阻塞链（全部同步 httpx，运行在事件循环线程）: `sidecar_health` 3s（:160,:45-47）→ 建会话 10s（:165）→ 发消息 `timeout_s`（:170，失败重试一次再 18s :171-173）→ `delete_session` 10s（:189,:59-61）→ `list_sessions` 10s（:191,:52-53）→ 可能触发 `cleanup_sessions`（:192）。worst ≈ 3+10+18+10+10 ≈ **51s/请求**（live timeout=18）。
  - 对照: 同模式在 apply 端点为 subprocess ≤300s（`src/web/routers/m1.py:491-496`，已有 single-flight 缓解）；m2 ask 路**无任何并发限制**。
- **证据（在产实况）**: `/proc/4086502/environ`: `M2_OPENCODE_ROUTE=on`、`OPENCODE_ASK_TIMEOUT=18`；`memory/STATE.md` route=on；延迟诊断（`docs/experiments/2026-08-11_agent_latency_diagnosis.md`）实测 warm ≈22.8s > 18s 超时 → 几乎每问都先吃满大部分超时再回落直连。
- **影响**: workers=2 的 :5050，**2 个并发非对比类 ask 即可使全站（health/M1 解析/metrics）停摆数十秒**；无 token 即可触发（FC-4）→ 匿名 DoS。
- **处置状态**: 延迟修复 a(warm-up)+b(禁 thinking) 已批、等 :5050 重启窗口（STATE.md）。**复评结论: 风险未消除且 route=on 使其处于激活态**；建议窗口落地前评估临时 `M2_OPENCODE_ROUTE=off`（牺牲 agent 路体验换可用性，用户裁定）。

### FC-1 [MEDIUM｜本 diff 引入] `交易账号` 在 证券持仓明细 内成为双字段同义词（表内碰撞）；根因=陈旧建议 + merge 无碰撞检测

- **证据**:
  - `config/m1_table_schema.json:498-502` 将 `交易账号` 加入 `资产账号` 的 synonyms；而同表 field[35] 存在**标准字段** `交易账号`（synonyms `交易账号/交易帐号`，旧版已有，git show 5535bdf 证实）。全仓扫描确认此为**本次新增的唯一表内碰撞**（旧版 证券持仓明细 仅 3 处既有碰撞: 确认份额/确认日期/手续费）。
  - 根因时间线: 建议 harvest 于 `2026-08-09 01:21`（schema_suggestions.json applied 条目 first_seen）；**5 分钟后** commit `6c2fd02`（08-09 01:26）才补入 +8 账号上下文字段（含专用 `交易账号` 字段）。建议产生时该列确实 unmapped，apply 时（08-11）已陈旧。
  - 机制缺口: `scripts/m1_apply_schema_suggestions.py:69-74` merge 仅检查 `raw in 目标字段 syns`，**不检查 raw 是否已是同表其他字段的 synonym/standard**；门禁只看命中率，语义错配不可见（前序 F12 已确立该局限）。
- **影响界定（潜伏、当前无实测损害）**:
  - 精确表头 `交易账号` 不受影响: standard 精确匹配 score 4 > synonym 精确 score 3（`scripts/m1_statement_parser.py:182-185`），仍落入 `交易账号` 字段。
  - 暴露面在**包含匹配变体**（如 `交易账号(户)`，score 2 平手）: 平手时严格 `>` 比较保留先遍历字段（`m1_statement_parser.py:205-207`），而 资产账号=field[22] 先于 交易账号=field[35] → 变体会**改判到 资产账号**（diff 前判 交易账号）。两字段同属账号族，属"错字段"而非"乱映射"，但会污染 M2 检索语义。
  - 基线无回退: 华泰紫金 100.0 前后不变；quick 门禁本次复跑 PASS（12/3 skip）——该同义词在回归集内**零收益、仅增碰撞风险**（真正收益来自 基金资产总额，见 FC-6）。
- **修复建议（≤5 行）**: 从 `config/m1_table_schema.json:501` 移除该同义词；并在 `merge_into_schema` 增加碰撞检查（raw 已是同表其他字段 synonym/standard → skip 并记原因）；可加一条"表内 synonym→≤1 standard"的回归断言防再犯。

### FC-3 [LOW｜本 diff 引入] 基线 rebuild 至 100.0 后，WaveFax 门禁进入零容差粒度区（OCR 非确定性下误 FAIL 风险上升）

- **证据**:
  - `tests/baselines/scenario1_baseline.json:137-139` WaveFax `hit_rates=[100.0]`；`tolerance.ocr_hit_rate_pp=10.0`（:6-9，未改动 ✓）。
  - 该样本单表 7 列（85.7%=6/7 反推）: 任一列失配 → 85.7% = −14.3pp > 10pp → **FAIL**（`scripts/m1_scenario1_regression.py:86-91`）。基线 100.0 意味着门禁对 WaveFax 只有"恰好 100"一种 PASS 态；vision 输出非确定性（baseline `_comment` 自认）下，误 FAIL 概率结构性抬升。
  - 既有（非本 diff）同族弱点: OCR 案 table_count 容差内减少时，逐表比较取 `min(len)`（`m1_scenario1_regression.py:86`）——OCR 产出 0 表仅 WARN 不 FAIL（:80-85）。登记为存量观察项。
- **建议**: 对小列表（≤10 列）OCR 样本改用"按列数容差"（如允 1 列）或基线封顶 95；或在门禁报告中标注"100.0 基线 + 小表 = 零容差"提示。

### FC-2 [LOW｜本 diff 引入] apply 台账把"被 skip 的建议"记为 applied；"+5 近义词"表述与实增 2 不符

- **证据**:
  - `config/schema_suggestions.json` applied[] 含 `分红方式→分红方式`（applied_at 2026-08-11 23:30），但 merge 实际 skip 原因为**目标字段不存在**（交易对账单 无 `分红方式` 标准字段，`memory/THREADS.md:116` 遗留① 自认）；`销售机构`、`产品总值①x②` 两条在旧 schema 已存在（git show 5535bdf 证实）→ "已存在" no-op。**净新增同义词 = 2**（交易账号、基金资产总额），与 commit message "+5 近义词" 不符（+5 为"应用建议数"口径）。
  - 机制: `src/web/routers/m1.py:513-519` 将全部 chosen 移入 applied，skip 原因仅存于响应 `skips` 字段、**不落盘**。
- **影响**: 台账语义失真（"applied" ≠ "merged"），后续审计/复盘需穿透比对；无安全影响；THREADS 已诚实补记，故 LOW。
- **建议**: applied 条目落 `merge_result: merged|already_exists|skipped:<reason>`；commit message 口径改"apply 5 建议/实增 2 同义词"。

### FC-6 [INFO｜重点①结论] `基金资产总额 → 市值`（证券持仓明细）: 无表内碰撞、跨表共享为既有模式、收益真实

- `config/m1_table_schema.json:371-375` 将 `基金资产总额` 加入 证券持仓明细.市值 synonyms: 表内碰撞扫描**零命中**；跨表共享（表头信息/交易对账单.合计金额/资金资产汇总.资产总值）在旧版已存在（3 处），本次为第 4 处，属既有模式延续；grid 匹配按表独立进行（`best_schema_match`，`m1_statement_parser.py:243-256`），不引入新串扰。
- 语义: 基金持仓行的"基金资产总额"=份额×净值=持仓市值，映射到 `市值` 成立。
- 收益: WaveFax 85.7→100.0（6/7→7/7）与该同义词一一对应，为本次 diff 唯一 measurable 收益。

### FC-7 [INFO｜重点②结论] baseline rebuild 与回归口径**一致**，无基线操纵迹象

- 口径一致性: rebuild 与门禁同走 `scripts/m1_statement_parser.py` + `resolve_schema_path()`（config/ 优先，`m1_statement_parser.py:52-56`，与 :5050 生产同源）、同 `--no-llm` 确定性口径（`m1_scenario1_regression.py:56`）；`created=2026-08-11` 与 `do_rebuild` 的 `time.strftime`（:183）吻合；tolerance 未动。
- 无放宽迹象: diff 中基线**仅** WaveFax 85.7→100.0 与 created 两处变化；其余 14 案数值逐条未动——rebuild 以新 schema 全量重跑而 14 案精确复现，反证新同义词对确定性样本零扰动（含 嘉合×8/NCAMC/HTML×3 精确匹配案）。
- 时序正确: schema 变更与 rebuild 同 commit（270c686），基线反映变更后实况；rebuild 输出即证据，非"先改基线后凑数"。
- skip 逻辑与文档一致（`--quick` 跳 3 个 ocr_expected 样本，`m1_scenario1_regression.py:116,132-135`）；apply 端点的 F3 盲区提示（`m1.py:521-524`）对本次两条 OCR 来源建议**按设计触发**，事后以 rebuild 人工复核闭环——流程合规，唯改善证据为单次 OCR 实跑（FC-3 已述风险）。
- 审计者独立复跑: `scripts/m1_scenario1_regression.py --quick` @HEAD → **PASS: 12 pass / 0 warn / 0 fail / 3 skip**（0.9s），与 commit message 口径一致。

### FC-8 [INFO｜重点③结论] docs/23 注记流程**合规**

- `docs/23_甲方阶段汇报.md:45` 表下加注，diff 实证为纯插入（hunk `@@ -42,6 +42,8 @@`，无任何 `-` 行）: 二轮战绩表表体零改动，注位于表末与既有"二轮提升的意义"引文之间。
- 注文"WaveFax 经同义词沉淀升至 100%"有基线背书（`scenario1_baseline.json:138` = 100.0 ✓）；"以系统实况为准"表述诚实。
- docx 同 commit（504810c）重生成（470184→470247 bytes，7 图内嵌）；`scripts/build_doc23_docx.py` 为纯本地转换（前序审计已核）。
- 治理面: STATE/THREADS 明示"等用户人工复审后亲发、不擅自改"，与冻结文档纪律一致；前序 F18 的 4 处数字漂移已在本范围之前修正于表体（35.7%/31 张/样本级均值/国金 70→90，现文核对 ✓）。
- 小疵（不碍合规）: 表体二轮列仍为 85.7%，读者需将注与该行关联；建议发送版排版时确认注的指向无歧义。

### FC-9 [INFO｜整改连续性] 前序审计（2026-08-10）CONDITIONAL 解除条件已**全部落地**（本范围前完成，本次逐项复核）

| 前序 finding | 落地证据 |
|---|---|
| F1 冻结守卫（HIGH） | `src/web/routers/m1.py:448-451`（注释自标 "F1 (audit 2026-08-10)"） |
| F2 reject 门禁 | `m1.py:533` `_check_admin` 已加 |
| F3 quick 盲区提示 | `m1.py:521-524`（本次 apply 实际触发） |
| F4 single-flight | `m1.py:452-455,:549` |
| F5 字节级备份 | `m1.py:477`（rb 读/ wb 回滚） |
| F10 无样本 --force 门禁 | `scripts/m1_apply_schema_suggestions.py:156-160` |
| F11 退出码 2 | `scripts/m1_scenario1_regression.py:160,:208` |
| F18 docs/23 数字 | 表体已按工件修正（见 FC-8） |

---

## 范围外观察（登记不深审）

1. 审计提交后仓库继续前移: HEAD=`60f5d4e`（台账 commit，仅 STATE/THREADS 各 1 行）；工作区存在**未提交** `M config/schema_suggestions.json` 与未跟踪 `scripts/t1_client_experience_audit.py`、`docs/experiments/2026-08-12_client_experience_audit/`（并行 loop 活动）。本审计范围严格止于 504810c，上述不入判定。
2. `.env.example:70` 仅登记 `M1_ADMIN_TOKEN`（注释态）；`M1_API_TOKEN` 条目仍缺（前序建议只落地一半）。
3. CORS 默认 `*`（`src/main.py:137`）+ `allow_credentials=True`（:144）: 在无认证前提下非主向量，但 token 落地时应同步收紧 `CORS_ORIGINS`。
4. 任务书 frozen 节点名 `docs/m1_schema/frozen_hashes` 与仓库实物（`scripts/graph/frozen_hashes.txt`）不一致，建议台账统一表述。

---

## 附录: 审计方法

- 角色: Loop C 只读审计（红线: 不改代码/不碰冻结节点/不重启服务/不改 docs/23）。
- 范围: `git diff 5535bdf..504810c`（3 commits, 12 files）+ 关联代码静态核查（parser 匹配语义、apply 端点、auth 中间件、adapter）+ 在产实况取证（/proc environ、ss、ps）。
- 实测项: 全 schema 同义词碰撞扫描（表内/跨表，新旧版对比）；冻结 md5×2 复核；quick 门禁 @HEAD 复跑；旧 schema 逐条核对 5 条 applied 建议落点；6c2fd02 时间线溯源。
- 未做（诚实声明）: OCR 全量门禁复跑（需 vision 实算且非确定性，超出只读快审预算；rebuild 单次实跑已由块 A 完成并入账）；:5050 进程未做任何探测性请求（避免扰动在产服务）。
