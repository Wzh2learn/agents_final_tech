# Loop C 审计报告 - 2026-07-31 (Cycle 6)

> 审计对象: commit `f966cf0` "fix(m1): PaddleOCR-VL 快速失败门控 + 视觉 OCR 并行 (200s->74s)"
> 审计重点: ① 新华 DOCX OCR 耗时下降; ② PaddleOCR 优雅降级; ③ Cycle-5 reconcile disposition 建议

## 审计范围
- 审计 commit: `f966cf0` (作者日期 2026-07-31 03:36:47); **HEAD = `f966cf0`, 在交付链中** (ancestor=YES)。
- Loop B 状态: **PASS** (`logs/graph/verify-report.json`, timestamp 2026-07-31T03:41:02, `head_commit`=`f966cf0`, overall=PASS, 全 PASS)。
- 模型服务: `:8004`=200, `:8005`=200; harness `:5050` `/health`=ok, `uvicorn --workers 2` (pid 3584392 @ 03:40, 在 commit 03:36 之后) → **新代码已部署**。
- 中间演进: `2212244` M2 RAG 集成 (PGVector, 端到端 QA 3/3)、`2342eaf` midpoint (M1 100% parse rate) 等, 非本轮审计对象但说明 M1→M2 闭环推进中。

### 反 amend 规则: **PASS (第 3 轮连续合规)**
`f966cf0` == HEAD == Loop B `head_commit`, 未 amend; `git merge-base --is-ancestor` 在链中。`git fsck` 13 个 dangling 均为历史遗留, 本轮无新增。✓

## 代码变更审查

### 变更摘要 (3 文件, +195/-33)
1. **`scripts/m1_ocr_fallback.py` (+59)** — PaddleOCR 快速失败门控:
   - 新增 `_transformers_incompatibility()`: 仅查版本 (不加载模型), `transformers>=5.0` 即判定不兼容 (PaddleOCR-VL 随包远程代码针对 4.55.0, 5.x 移除了 `ROPE_INIT_FUNCTIONS['default']` / `RotaryEmbedding` mixin / composite `text_config` 三处内部 API);
   - 模型加载前打印稳定标记 `PADDLEOCR_INCOMPATIBLE` 并 `exit 4` (~0.4s, 原需等满 120s 超时); `AutoModelForImageTextToText → AutoModel` (与 config.json auto_map 一致)。
2. **`scripts/m1_statement_parser.py` (+101/-33)** — 调用方降级 + 视觉并行:
   - `_try_paddleocr` 捕获 `PADDLEOCR_INCOMPATIBLE` 标记后锁存全局 `_PADDLEOCR_UNAVAILABLE`, 后续调用**直接跳过子进程** (永久 skip, 不再重复 0.4s 探测);
   - `_try_vision_ocr` 重构: 抽出 `_vision_ocr_one` 单图函数, 改 `ThreadPoolExecutor` 并行 (`M1_OCR_VISION_WORKERS=4`, 匹配 :8004 的 4 slot), `pool.map` 保序; 单图超时由硬编码 60s 改为可配 `M1_OCR_VISION_TIMEOUT=120`。
3. **`docs/experiments/2026-07-31_paddleocr_vl_transformers_compat.md` (+68)** — 兼容性根因文档。

### 是否服务于甲方需求: **YES**
影像件 OCR 耗时与可用性直接关系甲方对账单解析的覆盖与体验; 快速失败门控消除 120s 静默浪费, 并行缩短影像件时延。✓

### 架构漂移风险: **LOW**
- PaddleOCR 门控为纯前置短路, 不改变既有 cascade 语义 (失败仍回落 vision); `_PADDLEOCR_UNAVAILABLE` 为进程级 latch, 合理 (同进程内不兼容状态不变)。
- 视觉并行: `pool.map` 保序保证阅读顺序; workers=4 匹配服务端 slot, 无超额并发。
- 风险点 (轻微): 视觉单图超时从 60s→120s, 慢页不再被丢, 但极端情况单请求最长 ~7×120s/(并行4)≈210s 仍可能偏长; 有 workers=2 + 异步考量兜底, 可接受。

### 不当修改: **无**
仅动 `scripts/` 两文件 + 1 文档; `tests/`、`~/wzh/m1_samples/`、冻结 TAT-DQA 未触。✓ 无调试残留。✓

## 甲方样本端到端验证 (live `:5050`)

| 样本 | 耗时 | ocr_used | ocr_engine | table_count | reconcile | schema 命中率 |
|------|------|----------|------------|-------------|-----------|---------------|
| 复熙 TXT | 0.14s | False | '' | 2 | 4/4 ✓ | 15/15 |
| 嘉兴 PDF | 1.03s | False | '' | 6 | 4/4 ✓ | 58/62 |
| 博时 PDF | 0.60s | False | '' | 1 | 4/4 ✓ | 3/5 |
| LU PDF | 23.2s | True | vision-8004 | 3 | 4/4 ✓ | 7/23 |
| 新华 DOCX | **74.1s** | True | vision-8004 | 5 | 4/4 ✓ | **0/11** |

### 重点核对

**① 新华 DOCX OCR 耗时下降? → YES ✓ (大幅)**
- 实测 **74.1s**, 与 commit 声称的 74s 一致; 较 Cycle-4 的 225s / Cycle-5 的 118s 显著下降 (~2.7x vs 200s 基线)。
- 根因: 视觉引擎并行 (7 图 × 4 worker); 加之 PaddleOCR 快速失败不再拖 120s。LU 同步降至 23s (Cycle-5 为 30s)。✓

**② PaddleOCR 优雅降级? → YES ✓ (实测, 闭合 Cycle 3/4/5 carryover)**
- 直接计时 PaddleOCR 子进程: **exit 4, 耗时 0.41s** (原需等满 120s 超时), 输出稳定标记:
  `PADDLEOCR_INCOMPATIBLE: transformers 5.7.0 >= 5.0 is incompatible with PaddleOCR-VL remote code (requires ~4.55.x; ...)`
- LU/新华 `ocr_engine` 仍为 `vision-8004`, cascade 正确回落视觉引擎, `reconcile 4/4` 不回归。
- `_PADDLEOCR_UNAVAILABLE` latch 生效 (代码审查: 首次探测后同进程后续调用跳过子进程)。
- **Cycle 3/4/5 连续提的 "PaddleOCR 静默失效 + 120s 浪费" carryover 本轮完全闭合**: 不再静默 (有标记+文档)、不再拖时 (0.4s fast-fail)、不再重复探测 (latch)。✓

**③ Cycle-5 reconcile disposition 建议? → NO ✗ (未实施)**
- `grep disposition|real_pass|skipped` 于 `scripts/m1_statement_parser.py` → **无**。Loop A 未采纳 Cycle-5 "加 `disposition: real_pass/skipped/fail` 区分" 的建议。
- 现状仍是: 博时/LU/新华 reconcile "4/4 PASS" 实为 "数据不足跳过" 式名义 PASS (本轮 LU 7/23、新华 0/11, 均无市值数据 → 跳过判 PASS), 对外仍易被误读为"全通过"。
- 该项为 Cycle-5 的"建议改进方向"(非硬性 CONDITIONAL), 不构成驳回, 但既被本轮列为主题③, 须诚实记录: **未做**。

## 判定: **ACCEPTED** (连续 ACCEPTED 计数: 3)

本轮两项硬 carryover (PaddleOCR 静默失效、新华同步时延) 均实质闭合且实测达标, reconcile 无回归 (5/5 仍 4/4), 代码正确/安全/服务需求, 反 amend 第 3 轮合规。Cycle-5 disposition 建议未实施, 但属软建议、不阻塞。**ACCEPTED。**

### 驳回原因
无。

### 建议改进方向 (不阻塞本轮)
1. **【carryover·连续 4 轮未闭合·高】新华 DOCX 仍 0/11 schema 命中**: 并行 OCR 降了时延但未改正确性——5 表列名仍似项目交付表 (项目/内容、阶段/我方工作/厂商工作、交付物/要求), 与 交易对账单 schema 0 命中。Cycle 3/4/5/6 持续未决, **须 Loop D 本轮裁定**: 影像件 OCR 是否属 M1 承诺? 若是, Loop A 须修 OCR→schema 列名归一或剔除该样本; 若否, API 显式标注"影像件暂不支持结构化"。
2. **【Cycle-5 建议重提·中】reconcile disposition 未实施**: 5 样本"4/4 PASS"含水分 (3/5 为跳过式), 仍建议加 `disposition` 区分 real_pass/skipped, 否则"全 PASS"对外易误读。本轮 Loop A 已有两项硬 carryover 优先, 此项可下轮。
3. **【质量·中】LU/博时命中率**: LU 7/23 (~30%)、博时 3/5, OCR/grid 表格切分与列名归一仍偏低; 新华 0% 是其中最差。
4. **【性能·轻微】新华 74s 虽大幅改善, 仍 >60s**: 极端情况 (7 图全慢页) 理论最长约 210s; 有 workers=2 兜底不阻塞他人, 可接受, 但若甲方对同步时延有硬要求, 仍需异步任务化。

## 给 Loop D 的建议
1. **本轮 ACCEPTED, 连续 ACCEPTED 计数=3 → 触发降频阈值**: 按审计频率规则, **可降频至每 12 小时**一次。建议 Loop D 确认降频, 并在出现 REJECTED/CONDITIONAL 时恢复 4-6h。
2. **新华 DOCX 0% 命中已连续 4 轮 (Cycle 3-6) 未闭合**, 此前两轮已强求 Loop D 裁定仍未果。**本轮为最后建议**: 若 Loop D 仍不裁定影像件 OCR 范围, 该项将无限 carryover; 建议要么本轮给出范围裁定, 要么明确"影像件不属 M1, 标注不支持"以关闭该 carryover。
3. PaddleOCR 门控已优雅闭合 (fast-fail + latch + 文档); 长期若要启用引擎1, 需独立 wzh_vision 子环境降级 transformers 至 ~4.55.x (隔离影响), 可作为独立运维任务排期, 不阻塞 M1。
4. 反 amend 规则连续 3 轮合规, 建议固化为成文流程; 历史 13 个 dangling commit 可 `git gc` 清理。
5. M1→M2 闭环 (commit 2212244 等) 推进中, 建议下轮审计关注 M2 RAG/QA 质量, 不止 M1。
