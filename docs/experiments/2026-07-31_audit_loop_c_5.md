# Loop C 审计报告 - 2026-07-31 (Cycle 5)

> 审计对象: commit `037e5a2` "fix(m1): 市值勾稽去除明细合计行重复计数 + 对比市值类总量"
> 审计重点: 嘉兴 reconcile 4/4 PASS (was 3/4); 5 样本 reconcile 全检

## 审计范围
- 审计 commit: `037e5a2` (作者日期 2026-07-31 02:48:32); **HEAD = `037e5a2`, 在交付链中** (ancestor=YES)。
- Loop B 状态: **PASS** (`logs/graph/verify-report.json`, timestamp 2026-07-31T02:53:38, `head_commit`=`037e5a2`, overall=PASS, 全 PASS)。
- 模型服务: `:8004`=200, `:8005`=200; harness `:5050` `/health`=ok, `uvicorn ... --workers 2` (pid 3548465 @ 02:53, 在 commit 02:48 之后) → **新代码已部署**。
- 中间 commit `f08ef31` (02:25) "修复静默错配嫌疑误报 + PaddleOCR trust_remote_code" —— 回应 Cycle-1/3/4 的 carryover (嘉兴静默错配误报 + PaddleOCR 修复), 本轮一并复核。

### 反 amend 规则: **PASS (第 2 轮连续合规)**
`037e5a2` == HEAD == Loop B `head_commit`, 未 amend; `git merge-base --is-ancestor` 在链中。`git fsck` 检出 13 个 dangling commit 均为 Cycle 1-3 amend 历史遗留, 本轮无新增。规则持续执行。✓

## 代码变更审查

### 变更摘要 (1 文件, +22/-2) — `scripts/m1_statement_parser.py`
根因诊断准确: 明细表(证券持仓明细)常含「合计:」汇总行, 旧 reconcile 把汇总行与数据行一起对「市值」求和 → 重复计数 → sum 翻倍 → 与汇总表形成 4 亿假差异 → 误报 FAIL。PDF 数据本身一致。

修复 (reconcile 函数内):
1. **`_is_total_row()`**: 任一字段值含「合计/小计/总计」判为汇总行; 市值求和前过滤, 只对数据行求和。
2. **市值勾稽对比字段调整**: 优先对比市值类总量「资产市值/证券市值」, 其次「合计金额/资产总值/总资产」。理由: 总资产=市值+资金余额, 含现金会引入偏差; 改用市值类字段使嘉兴精确匹配 (diff=0.00)。

### 是否服务于甲方需求: **YES**
对账单解析的核心交付之一是勾稽校验正确性; 修复误报直接提升对账可信度。✓

### 架构漂移风险: **LOW**
纯函数内增量, 阈值/字段优先级调整, 不影响其他检查项; `_is_total_row` 仅作用于市值求和分支。无新依赖。

### 不当修改: **无**
仅动 `scripts/m1_statement_parser.py` (stat 单文件); `tests/`、`~/wzh/m1_samples/`、冻结 TAT-DQA 未触。✓ 无调试残留。✓

## 甲方样本端到端验证 (live `:5050`)

### reconcile 全检 (5 样本 × 4 检查项)

| 样本 | 耗时 | reconcile | 市值勾稽 actual | 备注 |
|------|------|-----------|-----------------|------|
| 复熙 TXT | 0.02s | **4/4 PASS** ✓ | sum(市值)=22,161,557.90, **diff=0.00** (tol=110,807) | **实质性 PASS** (有真实市值数据) |
| 嘉兴 PDF | 0.98s | **4/4 PASS** ✓ | sum(市值)=401,379,783.28, **diff=0.00** (tol=2,006,898) | **实质性 PASS** (重点项, 详见下) |
| 博时 PDF | 0.79s | 4/4 PASS | 明细市值=无, 汇总=无 → 数据不足跳过 | 名义 PASS (无市值数据) |
| LU PDF | 30.5s | 4/4 PASS | 数据不足跳过 | 名义 PASS (OCR 表无市值) |
| 新华 DOCX | 118.0s | 4/4 PASS | 数据不足跳过 | 名义 PASS (OCR 表无市值) |

### 重点核对: 嘉兴 reconcile 4/4 PASS (was 3/4)? → **YES ✓**
两处真实 FAIL 均已修复:
- **市值勾稽 FAIL→PASS** (本 commit `037e5a2`): 过滤合计行后 sum(市值)=401,379,783.28, 与资产市值 diff=0.00。Cycle-1 的 4 亿假差异消除。
- **静默错配嫌疑 FAIL→PASS** (中间 commit `f08ef31`): actual="无可疑映射"。Cycle-1 的「在途数量/配号/持仓数量」4 项嫌疑误报消除 (contains-match 嫌疑关键词跳过 + 移除市值勾稽级联嫌疑)。
- 币种一致 / 日期格式 维持 PASS。

→ 嘉兴从 3/4 → **4/4**, 重点项达成。✓

### 5 样本 reconcile 全 PASS? → **YES ✓ (5/5)**
全部 4/4。**但需诚实区分**: 仅复熙、嘉兴有**实质性市值勾稽** (diff=0.00); 博时/LU/新华为「数据不足跳过」式 PASS (无市值数据, 程序标注"数据不足，跳过"判 PASS)。这是诚实跳过而非假通过, 不构成缺陷, 但对外不宜宣称"5 样本勾稽全通过"而不加限定。

## 判定: **ACCEPTED** (连续 ACCEPTED 计数: 2)

本轮重点 (嘉兴 4/4) 达成且为实质性修复, 5 样本 reconcile 全 PASS, 代码正确/安全/服务需求, 反 amend 第 2 轮合规, 静默错配误报 carryover 已闭合 (f08ef31)。无新增缺陷, 无回归 (复熙仍实质性 PASS, 其余维持跳过式 PASS)。**ACCEPTED。**

### 驳回原因
无。

### 建议改进方向 (不阻塞本轮)
1. **【可观测性·中】 reconcile "数据不足跳过" 应可区分**: 博时/LU/新华 4/4 PASS 实为 vacuous (无市值数据即跳过判 PASS)。建议 reconcile 结果加 `disposition: real_pass/skipped/fail`, 否则"4/4"掩盖了"3/5 样本无勾稽数据"的事实, 对外易误读为全通过。
2. **【carryover·中】 PaddleOCR 仍未生效**: `f08ef31` 加了 `trust_remote_code=True`, 但 LU/新华 `ocr_engine` 仍为 `vision-8004`, 无一例 `paddleocr-vl`。根因 (Cycle-4 诊断的 `PaddleOCRVLConfig has no attribute text_config` transformers 不兼容) 未解, `trust_remote_code` 单独不够。视觉引擎仍独自承担所有 OCR (LU 30s/新华 118s)。
3. **【carryover·高·连续 3 轮未闭合】 新华 DOCX**: 仍 5 表 0% schema 命中 (项目交付类内容), 同步 118s (较 Cycle-4 的 225s 改善, 但仍慢)。Cycle-3/4 已提, 待 Loop D 裁定影像件 OCR 范围。
4. **【carryover·中】 LU/博时命中率**: LU 2/8~3/8, 博时 3/5, OCR/grid 表格切分质量仍偏低。

## 给 Loop D 的建议
1. **本轮 ACCEPTED, 连续 ACCEPTED 计数=2。** 再有 1 轮 ACCEPTED 即达"连续 3 次"降频阈值 (→ 12h 审计)。
2. reconcile 加 disposition 区分 real_pass/skipped —— 建议列为 Loop A 下轮轻量改进, 避免"5/4 全 PASS"的对外误读。
3. 新华 DOCX "0% 命中 + 118s" 连续 3 轮 (Cycle 3/4/5) 未闭合, 仍待 Loop D 裁定影像件 OCR 是否纳入 M1 承诺。**强烈建议 Loop D 本轮给出裁定**, 避免无限 carryover。
4. PaddleOCR 修复 (`trust_remote_code` 不足, 需升级 transformers 或 patch config) 建议排期, 以启用引擎1、为视觉引擎减负。
5. 反 amend 规则连续 2 轮合规, 建议固化; 历史 13 个 dangling commit 可择期 `git gc` 清理。
