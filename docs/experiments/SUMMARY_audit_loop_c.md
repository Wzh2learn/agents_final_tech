# SUMMARY — Loop C 审计报告归并 (2026-07-31 ~ 2026-08-03)

> 只读归并任务产物。除本文件外未写入/修改任何文件，未执行 git 写操作，未读取 `~/wzh/m1_samples/`。
> 归并日期: 2026-08-03。建议落实状态以 `git log`、`docs/18_overnight_loopD_neat_closeout.md`、
> `AGENTS.md` 及 HEAD 代码 grep 为证据交叉核对。

## 来源与口径

**归并的 9 份 Loop C 审计报告** (docs/experiments/):

| # | 文件 | 轮次 | 审计执行模型 |
|---|------|------|--------------|
| 1 | 2026-07-31_audit_loop_c.md | Cycle 1 | Claude Code + glm-5.2 (报告未注明，据 AGENTS.md「Graph Engineering Running Mode」注册口径) |
| 2 | 2026-07-31_audit_loop_c_2.md | Cycle 2 | 同上 |
| 3 | 2026-07-31_audit_loop_c_3.md | Cycle 3 | 同上 |
| 4 | 2026-07-31_audit_loop_c_4.md | Cycle 4 | 同上 |
| 5 | 2026-07-31_audit_loop_c_5.md | Cycle 5 | 同上 |
| 6 | 2026-07-31_audit_loop_c_6.md | Cycle 6 | 同上 |
| 7 | 2026-07-31_audit_loop_c_r7.md | Cycle 7 (R7) | 同上 (首次使用 qwen_harness_tools web_search 辅助审计) |
| 8 | 2026-08-02_audit_loop_c_deepseek.md | 模型轮换轮 | deepseek-v4-flash-0731 (首次, 经 Claude Code, tool_use/code_interpreter 验证通过) |
| 9 | 2026-08-02_audit_loop_c_qwen38.md | 模型轮换轮 | qwen3.8-max-preview (经 Claude Code Anthropic 兼容端点, 自动审计失败→人工完成) |

**总览**:

| 轮次 | 日期/时间 | 审计对象 (commit) | 判定 | 连续 ACCEPTED |
|------|-----------|-------------------|------|---------------|
| C1 | 07-31 ~00:40 | df96aa0..3e83d5e (重点 d209514 LLM 兜底) | CONDITIONAL | 0 |
| C2 | 07-31 ~00:53 | 7f38c95 (LLM 接通 API + KV 修复) | **REJECTED** | 0 |
| C3 | 07-31 ~01:38 | 185cdf7 (OCR 兜底) | CONDITIONAL | 0 |
| C4 | 07-31 ~02:18 | ca0f3a0 (无边框表格 + workers=2) | ACCEPTED | 1 |
| C5 | 07-31 ~02:58 | 037e5a2 (+中间 f08ef31) 市值勾稽修复 | ACCEPTED | 2 |
| C6 | 07-31 ~03:44 | f966cf0 (PaddleOCR 门控 + OCR 并行) | ACCEPTED | 3 → 触发 12h 降频 |
| C7 | 07-31 22:30 | 6b9deaa..264f30a (harness 工具 + docs/15) | ACCEPTED | 4 |
| DS | 08-02 22:40 | de7336b..97b8b9e (schema 同义词 + OCR prompt) | ACCEPTED | (降频后首轮, deepseek) |
| QW | 08-02/03 | d7049b5..9ea3754 (scenario1 gap 修复) | ACCEPTED (manual) | (qwen3.8-max-preview 兼容事故轮) |

> ⚠️ 口径勘误: docs/18 §12「Loop C 审计演进」表记 C2=CONDITIONAL、C3=ACCEPTED，与报告原文不符
> (报告原文: C2=REJECTED、C3=CONDITIONAL、C4 起才是首个 ACCEPTED)。以本报告文件为准；
> 「连续 4 次 ACCEPTED (C4-C7)」与 AGENTS.md「4x consecutive ACCEPTED」一致。

---

## Cycle 1 — 2026-07-31 ~00:40 · CONDITIONAL

- **审计对象**: `df96aa0..3e83d5e`，重点 `d209514` feat(m1-parser): add LLM fallback for unmapped columns
- **模型**: Claude Code + glm-5.2 (按注册口径)
- **判定**: **CONDITIONAL** — 代码正确、安全、方向服务甲方需求，但交付路径未接通，带条件放行
- **关键发现**:
  1. LLM 兜底 (35B, 三态输出, 幻觉护栏) 仅 CLI 可用: `src/web/routers/m1.py:76` 未传 `llm_fallback=True`，API 侧 `llm_extracted` 恒空 (嘉兴 3 列 unmapped 为例证)。
  2. 5 份甲方样本端到端: 仅复熙 TXT 完整解析 (1/5=20%)；博时 PDF 有文本层却 0 表 (grid 抽取缺陷)；LU/新华纯影像件无 OCR 能力 (0 表)。
  3. 嘉兴市值勾稽 FAIL + 静默错配嫌疑 4 项 (同名列映射存疑)。
  4. `opencode.json` 无 `agents` 键。
- **当时建议的落实情况**:
  - 【条件1】LLM 兜底接通 API → **已落实**: `6f2f630` (C2 审计对象) 加 `llm_fallback` 参数 + `llm_used`/`llm_fallback_enabled`/`parse_duration_ms` 字段；C3 live 复测确认生效 (嘉兴 `llm_used=True`、3 列兜底判「无」)。
  - 【条件2】3/5 样本 0 表 → **已落实**: OCR 兜底 `185cdf7` (C3: LU 0→3 表、新华 0→5 表) + 无边框/KV-grid 抽取 `ca0f3a0` (C4: 博时 0→1 表)；C4 起 5/5 样本 table_count≥1。
  - 响应带 `llm_used` 字段 → **已落实** (6f2f630)。
  - 嘉兴静默错配复核 → **已落实**: `f08ef31` 修复误报，C5 实测「无可疑映射」。
  - `opencode.json` agents 键 → **已落实** (后续多 agent 配置就位；见 07-29 two-hop 验证与 AGENTS.md「ready to activate」口径)。
  - 影像件 OCR 是否纳入 M1 承诺 → 当时未裁定，**最终于 07-31 午间由 Loop D 裁定** (见 C3/C6/C7 跟踪)。

## Cycle 2 — 2026-07-31 ~00:53 · REJECTED

- **审计对象**: `7f38c95` fix(m1): wire LLM fallback into API + fix KV extraction (回应 C1 条件)
- **模型**: Claude Code + glm-5.2
- **判定**: **REJECTED** — 驳回理由不在代码 (磁盘代码 CLI 直跑全部正确)，而在交付未生效
- **关键发现**:
  1. 【致命】live API (`:5050`) 5/5 样本响应均无 `llm_used` 等新字段，三项 sub-fix 全部缺失。根因: harness 进程 pid 2957102 启动于 07-30 08:45 (修复前 ~16h)，从未重启，Python 模块缓存旧代码 →「代码已改、服务未更」静默漂移。
  2. 【流程】Loop B 验证对象 `7f38c95` 被 amend 为 `6f2f630` (追加 1 docs 文件)，验证对象与交付 commit 在 git 层不一致 (代码字节级相同)。
- **当时建议的落实情况**:
  - 重启 harness + Loop C 复测 → **已落实**: 01:16 重启 (pid 3478657)，C3 live 复测三项修复全部生效，REJECTED 解除。
  - 「Loop B PASS 后不得 amend」立规 → **已落实**: `ed2ddc4` "anti-amend rule (Loop D directive)"，C4-C7 连续 4 轮合规。
  - harness `/health` 暴露所载代码 commit/mtime → **未落实** (HEAD grep 无实现)。
  - 暴露 `llm_call_attempted`/`llm_error` 区分「未触发/触发失败」→ **未落实** (HEAD grep 无实现)。
  - 博时 grid 缺口跟进 → **已落实** (C4 `ca0f3a0` 闭合)。

## Cycle 3 — 2026-07-31 ~01:38 · CONDITIONAL

- **审计对象**: `185cdf7` feat(m1): OCR fallback for image-only PDF/DOCX
- **模型**: Claude Code + glm-5.2
- **判定**: **CONDITIONAL** — 用户三项重点 (ocr 字段在位 / LU>0 / 新华>0) 全部达成、C2 部署问题已消除，但 OCR「能跑≠可用」
- **关键发现**:
  1. 影像件 OCR 真实可用: LU 3 表 (68.7s)、新华 5 表 (267.9s)，`ocr_engine=vision-8004` (:8004 已载 mmproj 多模态)。
  2. 新华 5 表 schema 命中率 **0%**，列名似「软件项目交付表」而非对账单 → 样本真实性存疑。
  3. 新华 268s 同步耗时远超网关超时，实际不可用。
  4. PaddleOCR「两引擎级联」名不副实: 引擎1 从不产出 (子进程无输出)，永远回落 vision-8004，且无日志。
  5. 前置发现: 连续第 3 轮 Loop B 验证对象被 amend (4410f98→185cdf7 dangling)，升级为系统性流程问题。
- **当时建议的落实情况**:
  - 【条件1】新华性能 (多图并发/异步) → **已落实**: `f966cf0` 视觉 OCR ThreadPoolExecutor 并行 (workers=4) + PaddleOCR fast-fail，200s→74s；C6 实测 74.1s。
  - 【条件2】新华 0% 命中 (核对内容/修归一/剔除) → **已落实 (裁定路径)**: Loop A #9 验证 OCR chunks 污染 RAG (8/10→5/10) 后 REVERT (`fcce4a4`→`212f53c`)；Loop D 裁定「新华 DOCX 是操作流程文档而非金融对账单」(docs/18 §14 决策2)，D4 入库过滤 `531bcc0`；`c701e14` 记录 xinhua CLOSED；AGENTS.md「xinhua 0/11 schema hit: CLOSED」。连续 5 轮 (C3-C7) 的 carryover 以**样本剔除裁定**关闭，非列名归一修复。
  - 【条件3】PaddleOCR 可观测性 → **已落实**: `f966cf0` 快速失败门控 (`PADDLEOCR_INCOMPATIBLE` 标记、exit 4、0.41s、进程级 latch) + 根因文档；C6 实测确认闭合。引擎本身仍不可用 (transformers 5.7.0 与 PaddleOCR-VL 需 ~4.55 不兼容 + aarch64 SIGSEGV)，后被宣布永久不可用、vision-8004 为永久引擎。
  - 反 amend 立规升级 → **已落实** (`ed2ddc4`，C3 审计后 ~23 分钟提交)。
  - OCR 样本 header_meta 恢复 / `ocr_image_count` 字段 → **未落实** (影像件 header_meta 仍为 0，无该字段)。
  - LU 列名归一 → **部分**: OCR prompt 增强 `97b8b9e` 改善表格检出 (华泰 0→1、TraFax 0→3 表)，但 LU 命中率仍低 (deepseek 轮 60.9% 口径)。

## Cycle 4 — 2026-07-31 ~02:18 · ACCEPTED (连续计数 1)

- **审计对象**: `ca0f3a0` fix(m1): borderless PDF table extraction + uvicorn workers=2
- **模型**: Claude Code + glm-5.2
- **判定**: **ACCEPTED** — 四项重点全部达成，无新增缺陷
- **关键发现**:
  1. 博时 table_count 0→1 (kv_grid 透视兜底，3/5 hits)，C3 grid 缺口闭合。
  2. workers=2 实测有效: 新华 OCR (225s) 期间 4/4 次 `/health` 探测毫秒级 200。
  3. 5/5 样本 table_count≥1 (字面覆盖 100%)，但报告明确警示「覆盖≠达标」(新华 0%、LU ~30%)，建议以字段命中率而非表数作为对外完成度指标。
  4. 反 amend 规则首次合规 (HEAD==Loop B head_commit)；父 commit 即 `ed2ddc4` 立规。
- **当时建议的落实情况** (均为不阻塞 carryover):
  - 新华 0% 命中 (连续 2 轮) → 后由 Loop D 裁定关闭 (见 C3 跟踪)。✅
  - 新华 225s 同步 → `f966cf0` 并行降至 74s。✅
  - LU/博时命中率 → 部分改善 (见 C3 跟踪)。⚠️
  - PaddleOCR 引擎1 排期修复 → 改为 fast-fail 门控 + 宣布永久不可用 (方向性关闭)。✅(决策)
  - 博时 grid 质量 3/5 → 后续 `cc6ad5b` 修正博时 ground truth 循环论证；deepseek 轮复测博时 hit 60%。⚠️ 部分

## Cycle 5 — 2026-07-31 ~02:58 · ACCEPTED (连续计数 2)

- **审计对象**: `037e5a2` fix(m1): 市值勾稽去除明细合计行重复计数 (+中间 commit `f08ef31` 静默错配误报修复 + PaddleOCR trust_remote_code)
- **模型**: Claude Code + glm-5.2
- **判定**: **ACCEPTED** — 嘉兴 reconcile 3/4→4/4 实质性达成，5 样本 reconcile 全 PASS
- **关键发现**:
  1. 根因诊断准确: 明细表「合计:」行被重复计入市值求和 → 4 亿假差异；`_is_total_row()` 过滤 + 改比市值类总量后嘉兴 diff=0.00。
  2. 诚实区分: 5/5「4/4 PASS」中博时/LU/新华为「数据不足跳过」式名义 PASS，对外易误读。
  3. 反 amend 第 2 轮连续合规；`git fsck` 13 个 dangling 均为历史遗留。
- **当时建议的落实情况**:
  - reconcile 加 `disposition: real_pass/skipped/fail` → **已落实**: `c8d7195` (07-31 03:45，C6 审计结束后 9 分钟)；AGENTS.md「disposition field added」确认。(C6 审计时点尚未实施，C6 报告如实记录「未做」，随后即补上。)
  - PaddleOCR `trust_remote_code` 不足、需升级 transformers → 被 C6 fast-fail 方案替代；引擎永久不可用结论见 07-31 ARM64 调查。✅(决策关闭)
  - 新华 DOCX 连续 3 轮未闭合，强请 Loop D 裁定 → 07-31 午间裁定 (docs/18 §14)。✅
  - LU/博时命中率 → 部分 (同前)。⚠️
  - dangling commit `git gc` 清理 → **部分/未见显式动作**: 当前 `git fsck` 仍有 3 个 dangling commit (较当时 13 个减少，无专门 gc commit 记录，属自然衰减)。

## Cycle 6 — 2026-07-31 ~03:44 · ACCEPTED (连续计数 3 → 触发 12h 降频)

- **审计对象**: `f966cf0` fix(m1): PaddleOCR-VL 快速失败门控 + 视觉 OCR 并行 (200s→74s)
- **模型**: Claude Code + glm-5.2
- **判定**: **ACCEPTED** — 两项硬 carryover (PaddleOCR 静默失效、新华时延) 实质闭合，reconcile 无回归
- **关键发现**:
  1. 新华 74.1s (vs C4 225s / C5 118s，~2.7x)，LU 23s；PaddleOCR exit 4 / 0.41s 优雅降级，latch 生效。
  2. Cycle-5 的 disposition 建议**未实施** (grep 无) — 报告如实记录「未做」(软建议不阻塞)。
  3. 新华 0/11 连续 4 轮未闭合，报告称本轮为对 Loop D 的「最后建议」。
- **当时建议的落实情况**:
  - 降频至 12h → **已落实** (AGENTS.md「Loop C: 12h freq」；docs/18 §12 守护模式)。
  - 新华裁定 (最后建议) → **已落实**: 07-31 午间 Loop D 裁定关闭 (见 C3 跟踪)。
  - disposition 重提 → **已落实** (`c8d7195`，本轮审计后 9 分钟)。
  - PaddleOCR 独立子环境降级 transformers → **未执行，决策性放弃**: ARM64 调查 (4a937fe) 确认 PaddlePaddle 3.2.2 aarch64 SIGSEGV 不可用，vision-8004 定为永久引擎。✅(决策关闭)
  - LU/博时命中率、新华 74s 仍>60s 的异步化 → 未专项处理 (OCR 缓存 `b4b9b58` 后使重复扫描 30s→<100ms，间接缓解)。⚠️

## Cycle 7 (R7) — 2026-07-31 22:30 · ACCEPTED (连续计数 4)

- **审计对象**: `6b9deaa..264f30a`，重点 `87d8da4` (Qwen harness tools CLI) + `264f30a` (docs/18 §15)；无 src/ 改动
- **模型**: Claude Code + glm-5.2 (本轮首次用被审计的 `qwen_harness_tools.py web_search` 做审计辅助)
- **判定**: **ACCEPTED** — 清洁增量，M1 合约 18/18 PASS，5 样本无回归
- **关键发现**:
  1. Loop B 滞后 HEAD 2 commit (最后验证 `6b9deaa`，未覆盖两个重点 commit)；Loop C 自跑合约测试补偿。
  2. `web_extractor` 子命令为坏路: Qwen API 要求其必须与 web_search 同请求，独立调用必 400。
  3. `TIMEOUT=60` 对 web_search+enable_thinking 偏紧 (首次调用即撞超时)。
  4. 新华 0/11 连续 5 轮未闭合 (最后一次建议性重提)。
  5. pytest 全量 12 failed 均为 async/playwright 环境性失败，非本轮引入。
- **当时建议的落实情况**:
  - web_extractor 修复 → **已落实**: `631f376` (22:29，与审计报告提交几乎同刻) "web_extractor requires web_search in same request"；AGENTS.md 亦注明该约束。
  - TIMEOUT 60→120s → **已落实** (同 commit；AGENTS.md「timeout 120s」)。
  - Loop B 重跑覆盖 HEAD → **已落实**: 后续 Loop B 追上 (08-02 deepseek 审计时 Loop B head=`97b8b9e` PASS)。
  - 新华裁定 → **已落实** (`c701e14` 23:03 "xinhua CLOSED"，距本轮 ~40 分钟)。
  - disposition 重提 → 已落实 (`c8d7195`)。
  - 审计重心转向 M2 RAG/QA → **已体现**: 后续 8h 交付循环、E2E 基准、deepseek 轮均覆盖 M2。

## deepseek 轮换轮 — 2026-08-02 22:40 · ACCEPTED

- **审计对象**: `de7336b` (嘉合 schema +38 同义词) .. `97b8b9e` (OCR prompt markdown 表格示例)
- **模型**: **deepseek-v4-flash-0731** (Loop C 首次换模审计，经 Claude Code；tool_use/code_interpreter 验证通过)
- **判定**: **ACCEPTED** — 两 commit 正确、聚焦、通过冻结门禁；全库 223 passed / 15 skipped
- **关键发现**:
  1. 嘉合命中率 31.2%→93.8% 经 code_interpreter 独立复算确认**完全可复现** (15/16 列；表1「基金份额+可用份额」同映射「持仓数量」，8 来源列命中 7 标准字段)。
  2. 8 份真实样本 unmapped=0，无字段回归；`.msg` 非注册解析类型 (预存行为非回归)。
  3. 新华 hit_rate 0.0 系 hits 计数不含 LLM-fallback 分配 (11 列实际已映射)，指标口径问题。
- **当时建议的落实情况**:
  - hit_rate 双口径 (`cols`/`distinct_mapped`) → **未落实** (HEAD grep 无)。
  - metrics 增加 `llm_mapped` 计数 → **未落实** (HEAD grep 无)。
  - `.msg` 层明确报错/处理 → **已落实 (间接)**: 未注册类型显式报错逻辑早在 `d4dc801` (07-29) 已存在于 router；`.msg` 实际处理由 scenario1 预处理流 (解附件 + HTML 正文解析) 完成 — docs/18 §20 (9 个 .msg → 13 附件 + 3 邮件正文)、`d7049b5` (邮件正文 HTML 表 0→9 表)、AGENTS.md「Gap 3 (email body) solved」。

## qwen3.8-max-preview 轮换轮 — 2026-08-02 · ACCEPTED (manual)

- **审计对象**: `d7049b5..9ea3754` (scenario1 三 gap: NCAMC 坐标重建、VLM 路由、HTML 邮件正文)
- **模型**: **qwen3.8-max-preview** 经 Anthropic 兼容端点 (Claude Code)
- **判定**: **ACCEPTED (manual)** — 模型未能执行自动审计，人工完成全部检查
- **关键发现**:
  1. **兼容性事故**: Claude Code 多步审计 prompt 下，qwen3.8-max-preview 回应「看不到具体任务」——无法正确处理 Claude Code system prompt + user message 格式 (经 Anthropic proxy)。
  2. 人工审计结果: 冻结测试 0 改动 PASS；schema 纯增量；parser 3 个新函数均为 fallback；pytest 225 passed / 0 failed；既有解析路径无回归 (嘉合 93.8%、嘉兴/复熙 100%)。
  3. 建议: Loop C 审计改用 deepseek-v4-flash-0731 或 glm-5.2；qwen3.8-max-preview 更适合 Codex CLI (Loop A)。
- **当时建议的落实情况**:
  - Loop C 换用 deepseek/glm → **已落实且后续超越**: 深seek 轮验证后继续作为 Loop C 模型 (HANDOFF.md 记录)；至 2026-08-03，**qwen3.8-max (非 preview)** 经 Anthropic 兼容端点 tool_use 验证通过，重新接回 Loop C (AGENTS.md「Model Routing (updated 2026-08-03)」)——原「preview 专属不兼容」结论被固化进 AGENTS.md。

---

## 跨轮观察 (归并结论)

1. **9 轮判定分布**: 1 REJECTED (C2, 部署未生效) + 2 CONDITIONAL (C1, C3) + 6 ACCEPTED (C4-C7 + 两轮模型轮换)。唯一 REJECTED 的根因是 harness 未重启而非代码错误，一次重启即解除。
2. **amend 漂移 → 反 amend 规则**: C1-C3 连续 3 轮出现「Loop B PASS 后 amend 已验证 commit」，C3 升级为 Loop D 立规 (`ed2ddc4`)，此后 C4-C7 连续 4 轮合规。
3. **新华 DOCX carryover 是全程最长未决项** (C3-C7 连续 5 轮重提): 最终以「样本属操作流程文档而非金融对账单」的 Loop D 裁定关闭 (REVERT + 入库过滤 + CLOSED 记录)，属裁定关闭而非技术修复。
4. **审计建议的落实速度总体很快**: LLM 接通、重启复测、OCR 并行、disposition、web_extractor/TIMEOUT、反 amend 规则均在 1-2 轮内 (常常数分钟至数小时内) 落地。
5. **至今未落实的建议** (3 项，均为软建议/可观测性):
   - C2: harness `/health` 暴露所载代码 commit/文件 mtime；
   - C2: `llm_call_attempted`/`llm_error` 区分「未触发/触发但失败」；
   - deepseek 轮: hit_rate 双口径 (`cols`/`distinct_mapped`) 与 `llm_mapped` 计数。
6. **docs/18 §12 的审计演进表与报告原文存在判定口径偏差** (C2/C3 误记)，归并时以报告文件为准。

---

## 任务二：其余实验文件清单 (非 Loop C 审计, 27 文件 + 3 目录)

现状标注: **仍相关** = 结论/资产当前仍有效或被 AGENTS.md/docs 引用; **已过期** = 结论已被后续工作取代; **可归档** = 纯历史快照/证据，可移档保存。

| 文件 | 主题 | 现状 | 依据 |
|------|------|------|------|
| 2026-07-10_model_services.md | GB10 开发机模型服务初始盘点 (路径/端口/模型库) | 可归档 | 已被 docs/21 基础设施盘点 + AGENTS.md「Model Routing」取代 |
| 2026-07-10_tabular_smoke_test.md | TabPFN/TabFM 表格基础模型冒烟 (wzh_tabular 环境) | 可归档 | TAT-DQA/tabular 线已冻结；tabular_classify 协议检查结论已并入 AGENTS.md |
| 2026-07-14_vision_smoke_test.md | 视觉模型冒烟 (wzh_vision, transformers 5.7.0, GB10) | 仍相关 | transformers 5.7.0 版本事实是 PaddleOCR-VL 不兼容根因的环境依据 |
| 2026-07-23_tat_dqa_m2_upper_bound.md | TAT-DQA M2 parsed-JSON 上限基线 (EM 上界) | 仍相关 | TAT-DQA 冻结 (FROZEN 非删除)，本文件即保留的研究基线 |
| 2026-07-28_chunking_and_integration.md | G 策略集成 + 分块粒度 (top_k=10+rerank→top-5, EM 0.28) | 仍相关 | AGENTS.md: 该 G 策略是 live M2 检索默认 (与甲方 M1 分开报告) |
| 2026-07-28_m1_baseline.md | M1 确定性规则基线 (src/biz/m1_service.py, TAT-DQA dev) | 仍相关 | m1_service 展示工作台为冻结节点 (18 测试)，本文件为其基线记录 |
| 2026-07-28_m1_llm_batch.md | TAT-DQA 全 dev LLM 批量抽取 (Qwen3-14B, 190/274 文档) | 已过期 | TAT-DQA 冻结 + 方法被规则优先 parser + LLM 兜底取代 |
| 2026-07-28_m1_llm_extraction.md | TAT-DQA zero-shot LLM 抽取原型 (5 文档) | 已过期 | 同上，原型路线被 scripts/m1_statement_parser.py 取代 |
| 2026-07-28_m1_statement_parser.md | 甲方对账单 parser 原型诞生报告 (纯规则, 5 样本) | 已过期 | 主线起点文档；20% 解析率等结论已被 100% 终态取代，保留作演进档案 |
| 2026-07-28_rerank_experiment.md | bge-reranker-v2-m3 cross-encoder 实验 | 仍相关 | reranker 于 33c8a82 在生产 M2 启用；本文件为其选型依据 |
| 2026-07-28_retrieval_ablation.md | 检索策略单变量对照 (TAT-DQA) | 仍相关 | live G 检索默认的对照实验依据 (冻结研究基线) |
| 2026-07-29_m1_compact_and_patch.md | parser 紧凑摘要 + schema C 补丁回写 | 已过期 | schema 已演进至 config/m1_table_schema.json (+38 嘉合 +23 HTML 同义词) |
| 2026-07-29_m1_header_mapping_llm.md | 未知表头 LLM 冷启动建议 + 勾稽把关 (不自动写回) | 已过期 | 「人审」原则保留，但 schema 演进被自助配置 CRUD (1d7406b) 与同义词机制取代 |
| 2026-07-29_m1_multiagent_delegation.md | 多 agent 委派: 单跳可用, 双跳 BLOCKED (16K 上下文) | 已过期 | 双跳 BLOCKED 结论当晚被 64K 上下文推翻 (见 m1_verify_and_mcp) |
| 2026-07-29_m1_next_iteration.md | Schema 扩展 + parser 升级 + 工作台三面板改造 | 已过期 | 迭代记录，能力被后续 8 轮 Loop A 全面超越 |
| 2026-07-29_m1_ocr_fallback.md | PaddleOCR-VL 首次纯图样本 OCR 闭环 (用完即停) | 已过期 | OCR 被 185cdf7 集成化；PaddleOCR-VL 被宣布永久不可用 |
| 2026-07-29_m1_schema_reconcile.md | 扩 schema + 勾稽校验 (救回 KV 报告体) | 已过期 | schema/reconcile 均已大幅演进 (disposition, 合计行过滤等) |
| 2026-07-29_m1_verify_and_mcp.md | 双跳委派验证 (64K, exit 0/58s) + MCP 集成, 三 Phase PASS | 仍相关 | AGENTS.md 显式引用；「explicitly-instructed two-hop IS verified」的证据源 |
| 2026-07-29_qoder_recon.md | Qoder CLI 1.1.7 侦察 + 协议分析 (BLOCKED-auth) | 仍相关 | 迁移决策仍 pending (等用户 PAT + Phase 2 实测)，AGENTS.md 保留专节 |
| 2026-07-30_72b_vs_35b_summary.md | 72B vs 35B v3 抽取对比摘要 (enable_thinking=false) | 可归档 | 结论 (72B 退化不替换主力) 已固化进 AGENTS.md 与 docs/18 |
| 2026-07-31_72b_reevaluation.md | 72B RAG QA 复评 (退化确认, 14x 慢, 46GB) | 可归档 | 终判「72B 不适合任何角色」已写入 docs/18 §16；模型文件建议删除 |
| 2026-07-31_e2e_benchmark.md | E2E 性能基准 5 样本×3 (OCR 占 93.7%, QA 295ms) | 仍相关 | 仍是当前唯一的端到端性能基线，无后续基准取代 |
| 2026-07-31_m2_rag_integration.md | M1→PGVector 入库 + M2 QA 3/3 (Loop A #6) | 仍相关 | live M2 端点 (:5050/api/m2/ask, m1_parsed_statements) 的起源记录；集合规模后扩至 137 embeddings |
| 2026-07-31_paddleocr_arm64_investigation.md | PaddleOCR ARM64 SIGSEGV 调查 → vision-8004 永久引擎 | 仍相关 | 「PaddleOCR-VL remains broken」现行结论的依据 |
| 2026-07-31_paddleocr_vl_transformers_compat.md | PaddleOCR-VL transformers 不兼容诊断 + OCR 并行化 | 仍相关 | fast-fail 门控 (f966cf0) 的根因文档，机制仍在服役 |
| 2026-07-31_ui_screenshots/ (目录, 6 PNG) | M1/M2 UI + ZhikunCode 浏览器实测截图 | 可归档 | 证据快照，已被 docs/18 §16 引用；更新版见 08-01 demo_sequence |
| 2026-07-31_zhikuncode_ui_screenshot.png | ZhikunCode Web UI 单张截图 (D2) | 可归档 | docs/18 §16 已引用的单次证据 |
| 2026-08-01_demo_sequence/ (目录, 11 PNG) | 一键 demo 全流程截图序列 | 仍相关 | AGENTS.md「Demo screenshot sequence」显式引用，甲方演示物料 |
| 2026-08-01_field_accuracy.json | 字段值准确率评测结果 (21 checks, 100%) | 仍相关 | 现行精度评测产物 (对应 4d3d2f1 ground-truth 修正后 100%) |
| results/ (目录, 2026-07-19 MCP 稳定性运行原始记录) | OpenCode/MCP 20-call 只读稳定性运行原始日志 | 可归档 | 结论已固化入 docs/2026-07-19_m2_mcp_verification.md 与 AGENTS.md，原始日志留档即可 |

END-OF-REPORT
