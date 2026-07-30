# Loop C 审计报告 - 2026-07-31 (Cycle 2)

> 审计对象: commit `7f38c95` "fix(m1): wire LLM fallback into API + fix KV extraction"
> 审计重点: API 路径是否正确接通 LLM 兜底 (响应是否含 `llm_used` 字段)

## 审计范围
- 审计 commit: `7f38c95` (作者日期 2026-07-31 00:33:57)
- Loop B 状态: **PASS** (`logs/graph/verify-report.json`, timestamp 2026-07-31T00:40:58, `head_commit`=7f38c95, overall=PASS, frozen_nodes/pytest/api_anchors 全 PASS)
- 模型服务: `:8004`(35B)=200, `:8005`(Qwen3-14B)=200
- M1 harness: `:5050` `/m1`=200 `/health`=200 (进程 pid 2957102, 启动于 7月30 08:45:22)

### ⚠️ 重要前置发现: commit 被 amend, Loop B 验证对象与交付分支不一致
- Loop B 验证的 `7f38c95` **不在当前 HEAD 链中** (`git merge-base --is-ancestor 7f38c95 HEAD` → NOT ancestor), 处于 dangling 状态。
- 交付分支实际承载该修复的 commit 是 `6f2f630` (HEAD~1 的父辈链上)。
- `git diff 7f38c95 6f2f630` 显示两者**仅差 1 个 docs md 文件** (+29 行), **代码文件 (scripts/m1_statement_parser.py, src/web/routers/m1.py) 字节级一致**。
- 含义: Loop B 验证后, 该 commit 被 amend 追加了 1 个文档文件, 改写了历史。代码本身未变, 但**审计对象与交付对象在 git 层面已非同一 commit**, 属流程瑕疵, 需 Loop D 知悉 (见末尾建议)。

## 代码变更审查

### 变更摘要 (2 文件, +73/-9)
1. **`src/web/routers/m1.py` (+38/-5)** — 直接回应上一轮 CONDITIONAL 第 1 项:
   - `/parse-file` 增加 `llm_fallback: Optional[bool]` Query 参数 (默认跟随 `M1_LLM_FALLBACK` 环境变量, 默认 on, 与 CLI 一致);
   - 调用 `process_sample(tmp_path, schema, llm_fallback=use_llm)` 接通兜底;
   - 响应新增 `llm_used` / `llm_fallback_enabled` / `parse_duration_ms` 三字段;
   - `llm_used` 由 `any(t.get("llm_extracted") for t in tables_out)` 推导 (诚实反映是否真触发);
   - 影像件 (needs_ocr 且 0 表) 追加显式 note "暂不支持影像件（纯图片 PDF/DOCX），需 OCR 能力后方可结构化"。
2. **`scripts/m1_statement_parser.py` (+44/-4)** — 回应第 2 项 + 兜底可用性:
   - `Schema.load`: 内存层为「资产账号」补同义词「交易帐号/交易账号」;
   - `extract_header_meta` / `scan_unattributed_kv`: 支持「键在行尾、值在下一行」(向下看 ≤2 行, 且排除下一行为另一键的情况); 正则容忍「为」前缀冒号 (如「基金资产总额为：」)。
   - `process_sample(..., llm_fallback=False)` 签名保持向后兼容。

### 是否服务于甲方需求: **YES (代码层面)**
- 三处改动全部命中甲方需求 (同义词映射 + 结构化提取) 与上一轮 CONDITIONAL 条件, 无无关重构。

### 架构漂移风险: **LOW**
- 纯增量、向后兼容 (`llm_fallback` 默认 False 不影响直接调用方); 无新依赖; `llm_used` 推导基于既有 `llm_extracted` 字段, 无副作用。

### 不当修改: **无**
- `tests/`、`~/wzh/m1_samples/`、冻结的 TAT-DQA 节点均未触及。✓
- 无调试代码残留。✓

## 甲方样本端到端验证

### A. 交付 API (live `:5050`) 实测 — **本轮核心结论**

对 5 份真实样本 `POST http://127.0.0.1:5050/api/m1/parse-file`:

| 样本 | http | 响应是否含 `llm_used` | `llm_fallback_enabled` | `parse_duration_ms` | 评分 |
|------|------|----------------------|----------------------|---------------------|------|
| 复熙 TXT | 200 | **❌ MISSING** | MISSING | MISSING | 95* |
| 嘉兴 PDF | 200 | **❌ MISSING** | MISSING | MISSING | 60 |
| 博时 PDF | 200 | **❌ MISSING** | MISSING | MISSING | 35 |
| LU PDF | 200 | **❌ MISSING** | MISSING | MISSING | 20 |
| 新华 DOCX | 200 | **❌ MISSING** | MISSING | MISSING | 20 |

\* 复熙本身无需 LLM (规则已 100% 命中), 95 分基于其规则解析质量, 与字段缺失无关。

**live API 五份响应均不含 `llm_used` / `llm_fallback_enabled` / `parse_duration_ms`** — 响应 schema 仍是修复前的旧结构。佐证:
- 嘉兴样本仍带 3 个 unmapped 列 (财汇局征费/备注/配号日期) 且 `llm_extracted` 全空 → LLM 兜底未触发;
- 博时样本 `header_meta_count` 仍为 **2** (修复后应为 6) → KV 修复未生效;
- 影像件 note 仍为旧措辞 ("image-only PDF ... -> needs OCR/vision"), 全量 grep "暂不支持影像件" 在 live 响应中 **命中 0 次** → 影像件 note 修复未生效。

**三项 sub-fix 在 live API 上全部缺失。**

### B. on-disk 代码 CLI 直跑 — 验证修复逻辑本身正确

为区分「修复逻辑错误」与「未部署」, 直接用磁盘新代码跑 CLI (`M1_LLM_FALLBACK=1`, 只读, 未重启服务):

| 验证项 | CLI 结果 | 判定 |
|--------|----------|------|
| 博时 KV 提取 (期望 2→6) | `表头区KV数: 6` (客户姓名/资产账号/基金名称/基金代码/基金份额净值/基金资产总额) | **修复有效** ✓ |
| 嘉兴 LLM 兜底 | 3 列抽取: 财汇局征费→"无", 备注→"无", 配号日期→"无"; 幻觉护栏未失效 | **修复有效** ✓ |
| 影像件 note | router 侧逻辑 (CLI 不打印该 note) — 见 live API 缺失 | 代码存在但未部署 |

结论: **磁盘代码的修复逻辑全部正确**, 问题纯粹在「未部署」。

### C. 根因定位: harness 进程未重启
- harness 进程 pid 2957102 启动于 **7月30 08:45:22**;
- 修复 commit `7f38c95` 作者日期 **7月31 00:33:57**; 磁盘 router 文件 mtime **7月31 00:42:04**;
- 进程在修复前 ~16 小时已启动, Python 已将旧 `web.routers.m1` 模块缓存于内存, 此后从未 reload/重启 → live API 持续服务旧代码。

## 判定: **REJECTED**

> 驳回理由不在代码 (代码正确且服务于需求), 而在交付: 本轮审计的核心问题——"API 路径是否正确接通 LLM 兜底"——**实测答案为否**。`llm_used` 字段在 5/5 份样本的 live 响应中均缺失, LLM 兜底在 API 上完全未生效。修复仅存在于 git 与磁盘, 未到达运行中的交付服务。

### 驳回原因
1. **【交付未生效·致命】** commit `7f38c95` 的三项修复 (LLM 接通 / KV 2→6 / 影像件 note) 在 live API (`:5050`) 上全部缺失。根因: harness 进程自 7月30 08:45 启动后未重启, 未加载新代码。**甲方通过 API 调用拿不到本轮任何修复。**
2. **【流程·中】** Loop B 验证对象 `7f38c95` 已被 amend 为 `6f2f630` (追加 1 docs 文件), Loop B 验证的 commit 与交付分支实际 commit 不一致。代码虽未变, 但验证闭环被打破。

### 必须修复 (REJECTED 解除条件)
1. **重启 harness 进程** 使 `7f38c95`/`6f2f630` 的代码生效, 重启后 Loop C 需重测: 5 份样本 live 响应须出现 `llm_used` 字段, 嘉兴须出现非空 `llm_extracted`, 博时 `header_meta_count` 须为 6。在 Loop C 复测通过前, 本轮交付不计入完成度。
2. 若历史 amend 无必要, 建议此后避免在 Loop B 验证后改写已验证 commit; 如必须 amend, 须触发 Loop B 重验并以新 hash 报备。

### 建议改进方向
- harness 应增加「启动时记录所载代码 commit / 文件 mtime」并在 `/health` 暴露, 便于 Loop C 一眼判断「服务跑的是哪个版本」, 避免此类「代码已改、服务未更」的静默漂移再次发生。
- `llm_used` 推导依赖 `llm_extracted` 非空; 当 LLM 调用异常降级为 `{}` 时 `llm_used` 会是 False——建议额外暴露 `llm_call_attempted` 或 `llm_error`, 否则"未触发"与"触发但失败"无法区分, 不利于排障。
- 博时 PDF 即使 KV 修到 6, `table_count` 仍为 0 (无 grid 表), 上一轮的 grid 抽取缺口未闭合, 建议下轮跟进。

## 给 Loop D 的建议
1. **本轮 REJECTED, 建议冻结 Loop A 新功能开发**直至「重启 harness + Loop C 复测 live API 含 `llm_used`」通过。根因是部署遗漏而非代码错误, 修复成本极低 (一次重启 + 复测), 但不修则本轮交付为零。
2. Loop B 验证后 amend commit 的做法已造成验证对象漂移; 建议 Loop D 在流程上明确: 「Loop B PASS 后不得 amend 已验证 commit, 否则需重新触发 Loop B」。本轮代码未变可豁免, 但需立规矩。
3. 影像件 (LU/新华) OCR 是否纳入 M1 仍未裁定 (上轮已提), 本轮未推进, 维持待 Loop D 裁定。
4. 本轮为 REJECTED, 不适用降频, 维持 4-6h 审计; 重启后复测若 PASS 可与下一轮合并计为连续 ACCEPTED。
