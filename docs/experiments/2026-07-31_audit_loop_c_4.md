# Loop C 审计报告 - 2026-07-31 (Cycle 4)

> 审计对象: commit `ca0f3a0` "fix(m1): borderless PDF table extraction + uvicorn workers=2"
> 审计重点: ① boshi table_count 0→1; ② workers=2 防 /health 阻塞; ③ 5 样本全覆盖; ④ 反 amend 规则合规

## 审计范围
- 审计 commit: `ca0f3a0` (作者日期 2026-07-31 01:54:32); **HEAD = `ca0f3a0`, 且在交付链中** (ancestor=YES)。
- Loop B 状态: **PASS** (`logs/graph/verify-report.json`, timestamp 2026-07-31T02:08:19, `head_commit`=`ca0f3a0`, overall=PASS, frozen_nodes/pytest/api_anchors 全 PASS)。
- 模型服务: `:8004` (35B + mmproj 视觉)=200, `:8005` (Qwen3-14B)=200。
- M1 harness: `:5050` `/health`=ok, 进程 `uvicorn m1_harness_5050:app --workers 2` (pid 3510217 启动于 02:03, 在 commit 01:54 之后) → **本轮 harness 已重启, 新代码已部署**。

## 代码变更审查

### 变更摘要 (2 文件, +93/-8)
1. **`scripts/m1_statement_parser.py` (+85)** — 无边框 PDF 表格抽取:
   - `parse_pdf`: 默认 `find_tables()` 返 0 表但有文本层时, 增加 `find_tables(strategy="text")` 兜底 (a);
   - 新增 `_text_lines_to_tables()` 正则兜底 (b): 策略1 多空格列检测 (≥2 列、≥3 行成表); 策略2 重复 KV 块透视成 grid (锚键重复即分块, 取公共键为表头);
   - 兜底产出的表 `extend` 进 `doc.tables`, 不影响 `needs_ocr` 判定。
2. **`scripts/m1_serve.sh` (+16/-8)** — uvicorn workers=2:
   - 由 `uvicorn.run(app)` 改为 CLI `uvicorn m1_harness_${PORT}:app --workers 2`;
   - heredoc 改用绝对 `${PROJECT_ROOT}` 路径 (避免 worker 进程 cwd 不定); `PYTHONPATH` 加 `/tmp` 以便 import 生成的 harness 模块。

### 是否服务于甲方需求: **YES**
- 无边框 PDF 表格抽取直接补齐 boshi 类样本的结构化缺口; workers=2 解决长 OCR 期间服务不可用 → 均服务于甲方"结构化提取"需求。✓

### 架构漂移风险: **LOW**
- `_text_lines_to_tables` 纯增量、有阈值保护 (≥3 行/≥4 KV 对才成表), 不污染既有 `find_tables` 路径; workers 调整属部署配置, 无架构改动; 绝对路径改造降低 cwd 依赖, 合理。

### 不当修改: **无**
- `tests/`、`~/wzh/m1_samples/`、冻结 TAT-DQA 节点均未触及 (stat 仅 scripts 两文件)。✓ 无调试残留。✓

## 甲方样本端到端验证 (live `:5050`, workers=2)

| 样本 | http | 耗时 | ocr_used | table_count | llm_used | 命中率 | 评分 |
|------|------|------|----------|-------------|----------|--------|------|
| 复熙 TXT | 200 | 0.18s | False | **2** ✓ | False | 100% | 95 |
| 嘉兴 PDF | 200 | 0.88s | False | **6** ✓ | True | 高(14/15,13/14,8/9) | 80 |
| 博时 PDF | 200 | 0.61s | False | **1** ✓ | True | 3/5 | 62 |
| LU PDF | 200 | 80.8s | True (vision-8004) | **3** ✓ | True | 2/8~3/8 (低) | 50 |
| 新华 DOCX | 200 | 225.0s | True (vision-8004) | **5** ✓ | True | **0/11 (0%)** | 35 |

### 用户四项重点核对结论

**① boshi PDF table_count=1 (was 0)? → YES ✓**
kv_grid 兜底 (策略2) 成表, 匹配 证券持仓明细, 3/5 hits; `header_meta_count=6` (KV 修复保持); llm 兜底抽 2 列。Cycle-3 "博时 grid=0" 缺口**闭合**。

**② workers=2 防止 /health 阻塞? → YES ✓ (实测)**
在 xinhua OCR (225s) 运行期间连续探测 `/health` 4 次:

| 探测 # | 时点(OCR 进行中) | 延迟 | 状态 |
|--------|------------------|------|------|
| 1 | +12s | 1.6ms | 200 |
| 2 | +18s | 1.1ms | 200 |
| 3 | +24s | 1.6ms | 200 |
| 4 | +30s | 2.9ms | 200 |

4/4 命中, 均毫秒级 → workers=2 确保长 OCR 占用 1 worker 时, 另一 worker 仍可服务健康检查/其他请求。Cycle-3 "新华 OCR 期间服务阻塞" 风险**已消除**。

**③ 5 样本全覆盖 (table_count>0)? → YES ✓**
复熙2 / 嘉兴6 / 博时1 / LU3 / 新华5, 全部 ≥1。从 Cycle-1 的 1/5 完整解析 → 本轮 5/5 产出表格。**字面"覆盖率"100%。**

**④ 反 amend 规则合规? → YES ✓ (本轮)**
- `ca0f3a0` == HEAD == Loop B `head_commit`, 未被 amend; `git merge-base --is-ancestor` 确认在交付链中。
- 父 commit 为 `ed2ddc4` "docs: Loop C audit #3 + anti-amend rule (Loop D directive)" → Loop D 已采纳 Cycle-3 升级建议并立规, Loop A 本轮停止 amend, **验证闭环闭合**。
- 注: `git fsck` 仍检出多个 dangling commit (4410f98 / 74520ef / 33f34af …), 系 Cycle 1-3 amend 历史遗留, 不在交付链、不影响本轮; 本轮无新增 dangling。

## 判定: **ACCEPTED**

本轮四项重点全部达成, 代码正确/安全/服务于需求, 反 amend 规则首次合规, PaddleOCR 失效已诚实诊断 (transformers 不兼容 + 缺 `trust_remote_code`, 见 commit Fix 3, 回应 Cycle-3 可观测性反馈)。无新增缺陷。**本轮 ACCEPTED。** (连续 ACCEPTED 计数: 1)

### 驳回原因
无。

### 建议改进方向 (不阻塞本轮)
1. **【carryover·正确性·高】新华 DOCX 仍 0/11 schema 命中**: 5 表列名为「项目/内容」「阶段/我方工作/厂商工作」「交付物/要求」, 仍似项目交付表而非基金对账单。Cycle-3 已提, 本轮未推进。须 Loop A 核对新华图片真实内容并裁定 (剔除样本 / 修 OCR→schema 列名归一), 否则"5 表"是假性覆盖。
2. **【carryover·性能·中】新华同步解析仍 225s**: workers=2 解决了"阻塞他人", 但发起方自身仍等 225s (7 图 × ~32s 串行)。真正解法仍是多图并发调 `:8004` 或异步任务化, 本轮未做。
3. **【质量·中】LU/博时命中率偏低**: LU 2/8~3/8 (OCR 表格切分粗糙、超长复合列名); 博时 3/5 且 llm 抽出的列含片段化值 (如「元（单位」疑似「元（单位：人民币）」截断)。建议 KV-grid 透视后做列名清洗/截断修复。
4. **【carryover·中】PaddleOCR 引擎1 仍不工作**: 本轮已诚实诊断根因 (transformers 版本不兼容 PaddleOCRVLConfig), 建议排期更新 transformers 或 patch config, 以启用引擎1、为 vision-8004 减负 (新华 7 图目前全压在视觉引擎)。
5. 博时 grid 抽取虽闭合 (0→1), 但 hit 仅 3/5, 跨轮 "grid 抽取质量" 仍可提升。

## 给 Loop D 的建议
1. **本轮 ACCEPTED, 连续 ACCEPTED 计数=1。** 未达"连续 3 次"降频阈值, 维持 4-6h 审计。
2. 反 amend 规则本轮首次合规, 建议 Loop D 固化该规则到流程文档 (ed2ddc4 已立), 持续执行; 历史 dangling commit 可择期 `git gc` 清理, 不影响交付。
3. 新华 DOCX 的"0% schema 命中 + 225s"是连续 2 轮 (Cycle3/4) 未闭合的 carryover, 建议Loop D 裁定: 是否将影像件 OCR 列入 M1 甲方承诺范围? 若是, 须给 Loop A 排期修正确性 (列名归一) 与性能 (多图并发); 若否, 在 API 显式标注"影像件暂不支持结构化"而非返回 0% 命中的假表。
4. 至此 5 份甲方样本均产出表格 (字面全覆盖), 但真实结构化质量参差 (新华 0%、LU ~30%), "覆盖"≠"达标", 建议Loop D 以"字段命中率"而非"表数"作为对外完成度指标。
