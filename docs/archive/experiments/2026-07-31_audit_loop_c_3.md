# Loop C 审计报告 - 2026-07-31 (Cycle 3)

> 审计对象: commit `185cdf7` "feat(m1): OCR fallback for image-only PDF/DOCX"
> 审计重点: API 是否暴露 `ocr_used`/`ocr_engine`; LU PDF 与新华 DOCX 是否返回 tables>0

## 审计范围
- 审计 commit: `185cdf7` (作者日期 2026-07-31 00:57:23); HEAD = `185cdf7`, 确在交付链中 (ancestor=YES)。
- Loop B 状态: **PASS** (`logs/graph/verify-report.json`, timestamp 2026-07-31T01:15:06, `head_commit`=`4410f98`, overall=PASS, frozen_nodes/pytest/api_anchors 全 PASS)。
- 模型服务: `:8004` (35B, **已加载 mmproj 视觉投影** `mmproj-Qwen3.6-35B-A3B-BF16.gguf`, capabilities 含 `multimodal`)=200; `:8005` (Qwen3-14B)=200。
- M1 harness: `:5050` `/health`=ok, 进程 pid **3478657 启动于 01:16** (在修复 commit 00:57 之后) → **本轮 harness 已重启, live API 实际服务新代码** (上轮 REJECTED 根因已消除)。

### ⚠️ 前置发现 (第三次同类): Loop B 验证对象与交付 commit 又不一致
- Loop B 验证 `4410f98`, 但 `4410f98` **不在 HEAD 链中** (dangling); HEAD 实际为 `185cdf7`。
- `git diff 4410f98 185cdf7` 仅差 1 个 dispatch-log 文档, **代码文件字节级一致** (scripts/src diff = 0 行)。
- 这是连续第 3 轮出现「Loop B PASS 后 amend 已验证 commit」(Cycle1: 7f38c95→6f2f630; Cycle2: 7f38c95 dangling; Cycle3: 4410f98→185cdf7)。代码虽未变, 但验证闭环持续被打破, 已构成系统性流程问题, 须升级 Loop D (见末尾)。

## 代码变更审查

### 变更摘要 (2 文件, +210)
1. **`scripts/m1_statement_parser.py` (+208)** — OCR 兜底主体:
   - `ParsedDoc` 新增 `ocr_used: bool` / `ocr_engine: str`;
   - `_extract_pdf_page_images` (200 DPI 渲染各页 PNG, 含嵌入图 fallback)、`_extract_docx_images` (zipfile 取 word/media/ 图片);
   - **两引擎级联** `_ocr_fallback`: 引擎1 `_try_paddleocr` (调 `~/miniconda3/envs/wzh_vision/bin/python` + `scripts/m1_ocr_fallback.py` manifest, 120s 超时) → 引擎2 `_try_vision_ocr` (base64 图片 → `:8004` `/v1/chat/completions`, 单图 60s 超时);
   - 接入 `parse_pdf`/`parse_docx`: `needs_ocr=true` 时 OCR 文本喂回 `extract_header_meta` + markdown 表格检测。
2. **`src/web/routers/m1.py` (+2)** — 响应新增 `ocr_used` / `ocr_engine` 两字段 (从 result 透传)。

### 是否服务于甲方需求: **PARTIAL → YES (能力层面)**
- 方向正确: 之前 5 份样本中 3 份 (LU/新华/博时-grid) 产出 0 表, 影像件完全无法结构化; 本轮让影像件产出表格, 显著扩大覆盖。✓

### 架构漂移风险: **LOW**
- 纯增量, `needs_ocr=false` 路径不受影响; 失败一律降级为空串 (不污染规则结果); 无新运行时依赖 (PaddleOCR 走子进程, 视觉走标准 HTTP)。

### 不当修改: **无**
- `tests/`、`~/wzh/m1_samples/`、冻结 TAT-DQA 节点均未触及 (stat 仅 scripts+router)。✓ 无调试残留。✓

## 甲方样本端到端验证 (live `:5050`, harness 已重启)

对 5 份真实样本 `POST /api/m1/parse-file`, 重点核对 `ocr_used`/`ocr_engine` 与 `table_count`:

| 样本 | http | 耗时 | ocr_used | ocr_engine | table_count | llm_used | 评分 |
|------|------|------|----------|------------|-------------|----------|------|
| 复熙 TXT | 200 | 0.01s | False ✓ | '' | 2 (100%命中) | False | 95 |
| 嘉兴 PDF | 200 | 0.89s | False | '' | 6 | **True** ✓ | 78 |
| 博时 PDF | 200 | 0.01s | False | '' | 0 | False | 55 |
| LU PDF | 200 | 68.7s | **True** ✓ | **vision-8004** ✓ | **3** ✓ | True | 50 |
| 新华 DOCX | 200 | **267.9s** | **True** ✓ | **vision-8004** ✓ | **5** ✓ | True | 35 |

### 用户三项重点核对结论
1. **`ocr_used`/`ocr_engine` 字段是否在响应中? → YES。** 5 份响应均含两字段; 影像件 (LU/新华) `ocr_used=True`、`ocr_engine='vision-8004'`; 文本/有文本层样本 `ocr_used=False`。✓
2. **LU PDF 是否返回 tables>0? → YES (3 表)。** 上轮 0 表, 本轮 OCR 后 3 表 (匹配 交易对账单)。✓
3. **新华 DOCX 是否返回 tables>0? → YES (5 表)。** 上轮 0 表, 本轮 OCR 后 5 表。✓ 但耗时 268s, 且 5 表 schema 命中率 **0%** (见下)。

### 上轮 CONDITIONAL/REJECTED 项复核
- **Cycle-2 REJECTED (harness 未重启) → 已解除**: 本轮 live API 嘉兴 `llm_used=True`、3 列兜底抽取 (财汇局征费/备注/配号日期 均判「无」, 无幻觉 ✓), `llm_fallback_enabled=True`, `parse_duration_ms` 字段在位; 博时 `header_meta_count=6` (上轮 live 为 2)。→ Cycle-2 的 LLM 接通 + KV(2→6) 修复**已部署生效**。✓

### 质量问题 (影像件)
- **新华 DOCX 5 表 schema 命中率 0%**: 列名为「项目/内容」「阶段/我方工作/厂商工作」「交付物/要求」, 与 交易对账单 schema 8 字段无一命中, 全靠 LLM 兜底填值。这些列名更像**软件项目交付表**而非基金对账单 —— 需 Loop A 核对新华 DOCX 图片的真实内容是否为对账单 (OCR 引擎已确认是多模态实抽, 非文本幻觉, 见下), 若样本本身非对账单则应从甲方样本集剔除或标注。
- **LU PDF 命中率低**: 3 表 hit 率 2/8、3/8、2/7; 列名出现「单位分红每份分红金额(元)①」「现金分红金额①X参与分红份额…」等超长复合列名, OCR 表格切分粗糙。
- **影像件 header_meta=0**: LU/新华 OCR 文本均未恢复表头 KV (header_meta_count 0/1), 头部信息丢失。
- **新华耗时 268s**: 单图 60s × 多图串行, 远超常见 API/网关超时 (30-60s), 作为同步接口实际不可用。

### PaddleOCR「两引擎级联」名不副实
- `:8004` 进程确载 `--mmproj` 且 capabilities 含 `multimodal`, 视觉抽值为真实多模态识别 (非文本模型幻觉)。✓
- 但 **PaddleOCR 引擎1 从未生效**: LU 与新华 `ocr_engine` 均为 `vision-8004`, 无一例 `paddleocr-vl`。诊断: `~/miniconda3/envs/wzh_vision/bin/python` 与 `scripts/m1_ocr_fallback.py` 均存在, 但子进程在窗口内不产出 (手动跑 30s 被 kill, 代码给 120s); `_try_paddleocr` 因 `returncode!=0` 或无 out 文件而 return "" → 永远落到引擎2。级联设计在当前环境无任何冗余收益, 实际只有视觉引擎在工作。

## 判定: **CONDITIONAL**

本轮不驳回: 用户三项重点核对 (ocr 字段在位 / LU>0 / 新华>0) 全部达成, Cycle-2 部署遗漏已修复, OCR 能力真实可用 (多模态已验证), 方向服务于甲方需求。但带条件放行——OCR「能跑」≠「可用」, 以下须 Loop A 闭环:

### 驳回原因
无 (未 REJECTED)。

### 必须修复 (CONDITIONAL 条件)
1. **【性能·高优先】新华 DOCX 同步解析 268s**, 超出任何合理 API 超时。须改为: 多图并发调用 `:8004` (现串行), 或异步任务化 (返回 job_id, 轮询), 或限制单文档最大图片数。否则该端点对甲方不可用。
2. **【正确性·高优先】新华 5 表 schema 命中 0%**: 核对新华 DOCX 图片真实内容; 若确为对账单, 修 OCR→markdown 表格检测/列名归一; 若非对账单, 剔除该样本并在报告标注。不能把 0% 命中的表当作"结构化成功"交付。
3. **【可观测性·中优先】PaddleOCR 引擎1 静默失效**: 级联写成两引擎但引擎1 永不产出, 且无日志暴露失败原因。要么修好 PaddleOCR (查清子进程为何无输出), 要么从代码/文档中移除该级联以免误导; 并在 `ocr_engine` 之外加 `paddle_attempted`/`paddle_error`, 否则"级联"只是装饰。

### 建议改进方向
- LU/新华 `header_meta=0`: OCR 后应优先恢复表头 KV (客户编号/基金名称/基金代码…), 否则即使有明细表, 头部信息仍丢失, 不满足甲方"表头同义词映射 + 结构化"完整需求。
- LU 命中率低 (2/8~): OCR markdown 表格切分需对齐 schema 列名 (复合列名拆分/归一)。
- `parse_duration_ms` 与 `ocr_used` 已在响应, 建议补 `ocr_image_count`/`ocr_per_image_ms`, 便于定位慢点。
- 博时 PDF `table_count=0` 仍未解决 (Cycle2 已提), grid 抽取缺口跨轮未闭合。

## 给 Loop D 的建议
1. **流程纠偏 (升级)**: 连续 3 轮出现「Loop B PASS 后 amend 已验证 commit」(7f38c95→6f2f630、4410f98→185cdf7), 验证对象与交付对象在 git 层面不一致。虽本轮代码与 Loop B 验证对象字节一致可豁免, 但该做法系统性削弱 Loop B 闭环。**建议 Loop D 立规: Loop B PASS 后禁止 amend 已验证 commit; 若必须 amend (如补文档), 须以新 commit hash 重新触发 Loop B 并报备。** 否则后续一旦 amend 误改代码, Loop B 将无法兜住。
2. 本轮 CONDITIONAL, 建议把"新华 268s 性能"与"新华 0% 命中正确性"列为 Loop A 下轮硬性前置; PaddleOCR 静默失效列为可观测性缺陷跟进。在两项高优先修复前, OCR 功能不计入"影像件结构化已交付"。
3. 影像件 OCR 是否纳入 M1 甲方承诺范围, 仍待 Loop D 裁定 (前两轮已提, 本轮未推进); 裁定前不要让 Loop A 盲目扩 OCR 能力。
4. 本轮为 CONDITIONAL (非连续 ACCEPTED), 维持 4-6h 审计频率。
