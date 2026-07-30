# Loop C 审计报告 - 2026-07-31

## 审计范围
- 审计 commit 范围: `df96aa0..3e83d5e` (重点功能变更: `d209514` feat(m1-parser): add LLM fallback for unmapped columns)
- Loop B 状态: **PASS** (`logs/graph/verify-report.json` timestamp 2026-07-30T23:56:53, overall=PASS, frozen_nodes/pytest/api_anchors 全 PASS, action="Loop A may continue")
- 模型服务健康: `:8004`(35B 主力)=200, `:8005`(Qwen3-14B 推理)=200
- M1 harness: `:5050`(`/m1`=200, `/api/m1/parse-file` POST=200) 运行中; 注: `:5000` 是另一个应用(建账规则助手), 非 M1。

## 代码变更审查

### 变更摘要
本轮唯一功能性 `src`/`scripts` 变更是 `d209514` (`scripts/m1_statement_parser.py`, +135/-2), 新增 LLM 兜底:
- 对规则映射后仍 unmapped 的源列, 调本地 35B 模型抽值;
- prompt 要求三态输出 (真实值 / "无"表头无数据 / ""列名缺失);
- 通过 `chat_template_kwargs.enable_thinking=false` + `temperature=0` 关思考;
- 幻觉护栏: 构建全文表头词表, 若 LLM 输出值落在表头词集合内则丢弃、保持 unmapped;
- 默认 `llm_fallback=False`; 仅 CLI `main()` 据 `--no-llm` / `M1_LLM_FALLBACK` 环境变量开启。

最近 3 个 commit (`488afe1`, `3f44302`, `3e83d5e`) 均为 docs / `.gitignore`, 无代码改动。

### 是否服务于甲方需求: **PARTIAL**
- 方向正确: 甲方需求 = 表头同义词映射 + 结构化提取, LLM 兜底正是补齐规则映射漏掉的列 (如「财汇局征费」「配号日期」), 服务于需求。✓
- **但交付路径未接通 (见下) → 甲方实际通过 API 调用时拿不到该能力。**

### 架构漂移风险: **LOW**
- 改动集中在单文件、纯增量 (新函数 + `process_sample` 可选参数), 不破坏纯规则行为; 失败一律降级 `{}`, 不污染规则结果。
- 无引入新依赖 (用标准库 `urllib.request`), 无架构层改动。

### 不当修改: **无**
- `tests/` 最近 5 commit 未被 d209514 触及 (上次改动在 `0ed4437`)。✓
- `~/wzh/m1_samples/` 未进 git, 未被任何 commit 触及, 真实样本只读完好。✓
- 冻结的 TAT-DQA 节点: d209514 仅动 `scripts/m1_statement_parser.py`, 未碰 TAT-DQA。✓
- 无 `breakpoint()/pdb/DEBUG print` 等调试残留。✓

## 甲方样本端到端验证

通过交付 API (`POST http://127.0.0.1:5050/api/m1/parse-file`) 解析 5 份真实样本:

| 样本 | 解析状态 | 字段覆盖率 | 质量评分 | 备注 |
|------|----------|------------|----------|------|
| sample_fuxi_hunhe25_20231101.txt (复熙混合25) | success | 100% (2表: 资金资产汇总5/5, 证券持仓明细10/10, 无unmapped) | **95** | 规则映射完整, 勾稽通过。文本样本最优。 |
| sample_jiaxing_minan_20231031.pdf (嘉兴民安) | success | ~93% (5表; 其中3表各有1列unmapped: 财汇局征费/备注/配号日期) | **70** | unmapped 列经 CLI 验证可被 LLM 兜底正确判为「无」(表头无数据), **但 API 路径未开启 LLM 兜底, `llm_extracted` 全空**。市值勾稽: 静默错配嫌疑 FAIL (4项嫌疑, 含 在途数量/配号 等同名列)。 |
| sample_boshi_chuantong.pdf (博时传统) | success | **0% 表格** (table_count=0, 仅 header_meta 2字段: 基金名称/基金代码) | **35** | `needs_ocr=false`(有文本层)却提取出 0 张表 → **PDF grid 抽取失败**, 非 OCR 问题。严重覆盖缺口。 |
| sample_20260506_233222LU.pdf | success | **0% 表格** (image-only PDF, needs_ocr=true) | **20** | 纯图片 PDF, 无文本层, OCR/vision 未实现 → 完全无法结构化。已知能力空白。 |
| sample_xinhua.docx (新华) | success | **0% 表格** (image-only DOCX, 7 embedded images, needs_ocr=true) | **20** | 纯图片 DOCX, OCR/vision 未实现 → 完全无法结构化。已知能力空白。 |

**端到端小结**: 5 份甲方样本中, 仅 1 份 (复熙 TXT) 完整解析; 1 份 (嘉兴 PDF) 部分解析但有未映射列且 API 未启用兜底; **3 份 (博时/LU/新华) 产出 0 表格**。甲方样本整体解析成功率 1/5 = 20% (按"完整结构化"计)。

## 判定: **CONDITIONAL**

不驳回 (代码本身正确、安全、方向服务于需求, 符合"不能因不够优雅而驳回"原则), 但**带条件放行**, 以下两项须 Loop A 修复后方可视为本轮交付达标:

### 驳回原因 (条件未达成项)
无 (未 REJECTED)。

### 必须修复 (CONDITIONAL 条件)
1. **【交付路径断裂·高优先】LLM 兜底未接通 API。** `src/web/routers/m1.py:76` 调用 `parser.process_sample(tmp_path, schema)` 时未传 `llm_fallback=True`, 导致 d209514 的能力仅 CLI 可用, 甲方通过 `/api/m1/parse-file` 调用时 `llm_extracted` 恒为空 (嘉兴样本 3 列 unmapped 即为例证)。功能已开发但未交付。
2. **【覆盖缺口·中优先】3/5 真实样本产出 0 表格。** 其中博时 PDF 有文本层 (`needs_ocr=false`) 却抽不出任何表, 属 grid 抽取缺陷而非 OCR 缺陷, 应优先排查; LU/新华为纯图片, OCR/vision 未实现, 需明确是否纳入 M1 范围 (若纳入则排期, 若不纳入则在 API 响应中显式标注"暂不支持影像件"而非静默返回空表)。

### 建议改进方向
- API 路径启用 LLM 兜底时, 应在响应中带 `llm_used: true/false` 与调用耗时, 便于审计与降级监控。
- 嘉兴样本"静默错配嫌疑 FAIL (4项)": 同名列(在途数量/配号/持仓数量)被映射到不同标准列, 建议Loop A 复核这些映射是否真为语义等价还是误配。
- `opencode.json` 无 `agents` 键 (解析为 None), 若期望多 agent 配置需补全; 当前不影响 M1 运行。

## 给 Loop D 的建议 (如有)
1. 本轮判定 **CONDITIONAL**, 建议不冻结工作流, 但将上述两项修复列为 Loop A 下一轮硬性前置条件; 在 Loop A 提交"API 接通 LLM 兜底"前, 该功能不计入交付完成度。
2. 影像件 (LU/新华) 的 OCR 能力是否属于 M1 甲方承诺范围, 需 Loop D 裁定边界 (纳入排期 / 明确不支持的对外说明); 在裁定前, 不要让 Loop A 盲目投入 OCR 开发。
3. 连续 ACCEPTED 降频规则不适用本轮 (本轮为 CONDITIONAL), 维持 4-6h 审计频率。
