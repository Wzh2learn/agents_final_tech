# Phase 3 代码审查报告 — scripts/ 目录全量盘点

> 审查类型: 目录级 read-only 审查（按 `skills/requesting-code-review/code-reviewer.md` 模板结构调整）
> 审查日期: 2026-08-04 | 审查者: Loop A (read-only 分析, 未改任何代码, 未做任何 git 操作)
> 范围: `scripts/` 全部 94 个文件（55 py / 20 sh / 16 md / 1 json / 1 ps1 / 1 txt；codebase_map 口径"92 个脚本"不含 README 与 frozen_hashes.txt 等附属文件）
> 方法: 全库引用图谱（docs / dispatch_log / 跨脚本 import / src / tests）、git 末次提交时间、运行时实测（端口监听、curl、schema 内容比对）、逐文件 docstring 审读

---

## Strengths（先说做得好的）

- **核心链路脚本质量高、边界自觉**: `m1_statement_parser.py` / `m1_rag_ingest.py` / `m1_rag_qa.py` 均在 docstring 明确"不另建向量库、不绕过 RAGService、样本不落盘、输出脱敏"，且确实如此实现；`m1_statement_parser` 的 LLM/OCR 端点全部走环境变量（`M1_LLM_ENDPOINT`、`M1_OCR_VISION_ENDPOINT`），是硬编码治理的样板。
- **Loop B 验证层扎实**: `graph/loop_b_verify.sh` 纯 bash、无 AI、日志与返回值严格分流（stdout 只传数值），冻结哈希校验 + 独立 pytest + API 锚点三段式与 docs/17 §2 设计一致；`write_report.py` 输出结构与 verify-report.json 实测吻合（2026-08-03 PASS, e86ff07）。
- **loop_*.md / overnight_*.md 任务提示词按 AGENTS.md 政策作为审计档案保留**，形成"任务 → 提示词 → 实验报告"的可追溯链。
- **`.gitignore` 有效**: `scripts/__pycache__/*.pyc` 均未入库（git ls-files 验证为 0）。
- **qwen_harness_tools.py 健康度好**: 单文件 stdlib、错误路径返回 `ERROR:` 前缀且 exit 1、web_extractor 自动附带 web_search（遵守千问 API 约束）、STUB 工具显式声明，与 AGENTS.md 描述完全一致。

---

## Issues（按严重度排序）

### Critical (Must Fix)

1. **`scripts/graph/graph_orchestrator.sh` 的 Loop A / Loop C 启动方式与现行有效模式冲突，在 GB10 上大概率不可用**
   - File: scripts/graph/graph_orchestrator.sh:36-60
   - Issue: Loop A/C 用 `$CODEX_BIN --full-auto -q '...'` 启动。但 (a) AGENTS.md 与 docs/17 演进记录（2026-07-31）已确立 Loop A 派活方式为 tmux 直启 `cat loop_a_exec_constraints.md /tmp/task.md | codex exec --dangerously-bypass-approvals-and-sandbox`；(b) GB10 无 bubblewrap user namespaces，不带 `--dangerously-bypass-approvals-and-sandbox` 的 Codex CLI 无法执行命令。Loop C 同样已被替换为 Claude Code + qwen3.8-max（2026-08-03），orchestrator 仍按 Codex CLI 启动。
   - Why: docs/17 §8 "快速启动"明确指引 `bash scripts/graph/graph_orchestrator.sh start`。新接手的 Loop D 照做会得到"看似启动、实际空转"的 Loop A/C，破坏 Graph 的监督闭环。
   - Fix: 将 start_loop_a/start_loop_c 改为现行 tmux 直启模式（或标记 orchestrator 仅管理 Loop B + status），并在 docs/17 §8 注明 Loop A/C 的真实派活方式。

### Important (Should Fix)

2. **应用端口漂移 :5000 → :5050，Loop D 视图与 orchestrator 仍探 :5000**
   - File: scripts/graph/loop_d_monitor.sh:28, scripts/graph/graph_orchestrator.sh:96, docs/17 §3.1/§4.1
   - Evidence: 实测 `ss -ltnp` 仅 :5050 在监听（uvicorn, health 200）；`:5000/health` 返回 000。Loop B 已修正（`API_BASE=http://127.0.0.1:5050`），但 Loop D 监控与 orchestrator status 永远报 "FastAPI DOWN"，误导战略层判断。
   - Fix: 两处改为 `${M1_API_BASE:-http://127.0.0.1:5050}`（与 loop_b_verify.sh 对齐），同步修订 docs/17 §3.1 锚点示例与 §4.1 端口表。

3. **Loop C 载体描述全面过时（prompt 头部 + docs/17）**
   - File: scripts/graph/loop_c_audit_prompt.md:3-5, docs/17 §2/§6
   - Issue: prompt 头部仍写"Codex CLI system prompt / 推理引擎 :8005 (Qwen3-14B)"，但该文件 2026-08-03 已追加 Claude Code 的 Skill 武库节；AGENTS.md 与 codebase_map 均记载 Loop C = Claude Code + qwen3.8-max。头部与正文自相矛盾。
   - Fix: 更新 prompt 头部为 Claude Code 载体；docs/17 §2 框图与 §6 Loop C 启动提示同步。

4. **docs/17 冻结节点表指向不存在的路径**
   - File: docs/17 §3.2、§6 Loop A 启动提示
   - Issue: 写"字段定义 `docs/m1_schema/*.json`"，但 `docs/m1_schema/` 不存在（实测 ls 失败）；真实冻结的字段定义是 `~/wzh/m1_samples/m1_table_schema.json`（frozen_hashes.txt 与 AGENTS.md 为准）。
   - Why: 新 Loop A/C 读 docs/17 会保护一个不存在的路径、忽略真实 schema。
   - Fix: docs/17 §3.2/§6 改为与 frozen_hashes.txt 一致的清单。

5. **`responses2chat_proxy_v2.py` 是严格过时的重复副本，应删除**
   - File: scripts/responses2chat_proxy_v2.py（全库 0 引用）
   - Evidence: `diff` 显示 v1 = v2 + developer-role 映射 + Responses→Chat tools 转换 + /health 端点；git 史：17ca43b 同时重写两文件后，3b5dfea 只给 v1 加了 /health。AGENTS.md、switch_codex_model.sh、deploy_proxy_gb10.sh、docker-compose.yml 全部引用 v1。v2 若被误启动会丢失 tools 转换（Claude Code tool_use 依赖此路径）。
   - Fix: 删除 v2（或按治理规则标 DEPRECATED 头部注明"以 v1 为准"）。

6. **docs/17 §8 实现文件索引缺 3 个文件，§4.2 快照过时**
   - File: docs/17 §8（缺 `loop_d_daemon.sh`、`write_report.py`、`sync_skills.sh`）；§4.2 仍写 72B "下载中"
   - Evidence: 72B 已于 2026-07-31 评估、拒绝并删除（AGENTS.md），但 graph_orchestrator.sh:116-124 的 status 仍在探测 72B 下载文件。
   - Fix: 补齐索引；§4 加快照日期标注或删除 72B 小节；orchestrator 移除 72B 探测段。

7. **`scripts/README_scripts.md` 严重过时，作为 scripts/ 唯一索引文档在误导读者**
   - File: scripts/README_scripts.md（2026-07-21 快照）
   - Evidence: 描述 8 个"建议后续生成"的脚本（check_gpu.sh、setup_env.sh、start_vllm.sh 等）全部不存在（实测 MISSING）；未覆盖 7 月下旬以来全部 m1_*、graph/*、run.sh、demo.sh；"20/20 OpenCode 稳定性"口径已被 M1/M2 现状取代。
   - Fix: 重写为现状索引（或降级归档，改由 codebase_map.md 承担索引职责——后者已是较新的权威图谱）。

8. **三个 LLM 原型脚本的模型假设已过时，直接复跑会产生误导性结果**
   - File: scripts/m1_llm_extract_prototype.py:33-46, scripts/m1_llm_batch_extract.py:32-45, scripts/m1_header_mapping_llm.py:44-45
   - Issue: 均硬编码 `DEFAULT_MODEL/LLM_MODEL = "Qwen3-14B-Q4_K_M.gguf"` + `/no_think` 前缀，假设 :8004 是 Qwen3-14B。但 :8004 自 2026-07-30 起运行为 Qwen3.6-35B-A3B（实测 ss 显示 llama-server；m1_statement_parser.py:1513 的现行默认即 35B-A3B 且不用 /no_think）。llama-server 会忽略 model 字段，但 `/no_think` 对 35B-A3B 的行为未验证——复跑前必须重新校验，否则结果不可信。
   - Fix: 若保留（见建议清单），在文件头加"冻结研究基线 / 模型假设已过时，复跑前先验证"横幅；header_mapping_llm 若作为未来冷启动工具复用，应把模型常量改为环境变量。

### Minor (Nice to Have)

9. **`deploy_qoder_gb10.sh` 从 `/tmp/qoder_settings_template.json` 拷贝而非仓库内模板**
   - File: scripts/deploy_qoder_gb10.sh:19 — 仓库里就有 `scripts/qoder_settings_template.json`，脚本却依赖 /tmp 预置，直接运行必失败。Fix: 改为相对脚本目录定位模板。

10. **`supervisor_m1.sh` 与 `supervisor_qoder.sh` 文件头带 UTF-8 BOM**（实测 `efbbbf` 在 shebang 之前）— `./xxx.sh` 直接执行时内核无法识别 shebang；`bash xxx.sh` 不受影响。Fix: 去 BOM。

11. **硬编码集中在冻结/死脚本，活跃脚本治理良好** — 详见专项问题 3 的候选表；活跃链路无需立即动作。

12. **`loop_b_verify.sh` 的 API 锚点是旧文本规则端点**（/api/m1/sample、/api/m1/extract），与 docs/17 §3.1 写的 /api/m1/parse-file 不一致。两者都"对"（锚点 = 冻结的 test_m1_service 契约对应的端点），但文档与脚本各说一边，应在 docs/17 注明锚点的真实清单。另注意 Loop B 只跑 18 条冻结契约测试（设计如此），不等于全量 227 条回归。

---

## 专项问题 1：原型/重复脚本是否已被 m1_statement_parser 的 LLM 兜底取代？

**结论：三个脚本分两种情况，"被取代"的说法只对了一半。**

| 脚本 | 定位 | 与 parser LLM 兜底的关系 | 现状 |
|------|------|--------------------------|------|
| `m1_llm_extract_prototype.py` | TAT-DQA dev 5 文档 zero-shot 抽取原型 | **不同血统，不存在取代关系**。它读 `/home/testuser/wzh/datasets/tat-dqa` 英文语料、抽通用金融字段；parser 的 `llm_fallback_unmapped` 服务甲方中文对账单的未映射列值抽取。属已冻结的 TAT-DQA 研究线 | 冻结研究基线，保留并标注（见 Issue 8） |
| `m1_llm_batch_extract.py` | 上述原型的 274 文档批量化（checkpoint/resume） | 同上，TAT-DQA 研究线 | 同上 |
| `m1_header_mapping_llm.py` | 甲方 M1 未知表头冷启动：LLM 建议 synonym + 勾稽把关 + 人审回写 | **互补而非重复**：parser 的 llm_fallback 是运行时抽值；本脚本是离线 schema 冷启动建议器。其 2026-07-29 产出的建议（交易日期/代理费用/印花税/基金净值/最新单价/成交数量/币种/资产账户 等）经逐条比对**已全部进入现行冻结 schema**（unmapped 39→23→5→0 的演进在 AGENTS.md 有载）。import 的 P.PARSERS / P.Schema / P.SchemaField / P.process_sample 四个符号在现行 parser 中均存在，**无 API 漂移** | 一次性使命已完成；保留为未来新交易对手冷启动工具，建议模型常量改 env |

另：`m1_ocr_render.py`（纯图样本渲染 PNG）与 `m1_ocr_map.py`（OCR 文本映射命中率评测）是 2026-07-29 OCR 兜底实验的 Phase 0-3 一次性脚本；其能力已被 `m1_ocr_fallback.py`（parser 直接 import）+ parser 内置图片抽取吸收，仅实验报告引用它们 → 建议归档或删除。

## 专项问题 2：死脚本（孤儿）清单

判定标准：全库（docs/、dispatch_log.md、其他脚本、src/、tests/）零引用，且非政策保留档案。dispatch_log.md 实测仅记载过 vlm_server_8007.py / m1_rag_qa.py / sync_skills.sh / demo.sh 四个脚本名。

**A. 建议删除（一次性调试残留，零引用，git 史可回溯）**：
- `debug_load.py`、`debug_load2.py`、`debug_split.py`、`debug_split2.py`、`debug_markdown_splitter.py`（2026-07-16 加载器调试）
- `ingest_debug.py`、`ingest_debug2.py`（2026-07-16 入库调试）
- `check_kb.py`（查 langchain_pg_embedding 旧表口径，现行集合管理走 RAGService / m1_rag_ingest verify）
- `init_pgvector_ext.py`（530 字节，init_knowledge_backend.py 已覆盖建表建集合）
- `_verify_m1_local.py`（M1 页面无 DB 冒烟，已被 tests/test_m1_edge_cases.py 等 227 条测试覆盖）
- `responses2chat_proxy_v2.py`（见 Issue 5）

**B. 建议归档或标注"已应用的一次性部署"（零引用但承载环境重建知识）**：
- `deploy_proxy_gb10.sh`、`setup_codex_gb10.sh`（GB10 已按此部署完毕；重装机时有用）
- `deploy_qoder_gb10.sh` + `qoder_settings_template.json` + `supervisor_qoder.sh`（Qoder 迁移待 PAT 决策中，docs/16 未关闭前保留）
- `graph/loop_d_daemon.sh`（无上游引用但功能有效，补进 docs/17 §8 索引即可）

**C. 仅 docs/archive 引用的遗留脚本（2026-01 ~ 03 前 M1 时代）**：
- `init_collaboration_db.py`、`init_pgvector_db.py`、`migrate_sessions.py`、`test_db_conn.py`、`test_web_ui.py`、`test_non_thinking_mode.py`、`populate_knowledge_base.py`、`setup_claude_env.ps1`
- 建议：与 docs/archive 同批归档（移出 scripts/ 或加 DEPRECATED 头），避免新会话误用旧表结构。

**D. 政策保留（非死脚本）**：`loop_*.md`、`overnight_*.md` 共 16 个任务提示词 = AGENTS.md 明确的"consumed remote-loop task prompts, kept as audit archive"；`supervisor_m1.sh` 为已消费的 7 月末 loop 链编排，同档案性质。

## 专项问题 3：硬编码散落情况

活跃脚本治理良好（env 覆盖齐全）；硬编码集中在冻结研究线与死脚本。**建议集中到 env/config 的候选项**：

| 硬编码 | 位置 | 建议 |
|--------|------|------|
| `Qwen3-14B-Q4_K_M.gguf` + `:8004` | m1_llm_extract_prototype / m1_llm_batch_extract / m1_header_mapping_llm / run_rerank_eval / run_retrieval_ablation / run_tat_dqa_m2_upper_bound / run_m2_rag_eval | 冻结线不强制；header_mapping_llm 若复用则必须 env 化 |
| `/home/testuser/wzh/datasets/tat-dqa` | tat_dqa_data.py:28、两个 LLM 原型 | 冻结线，保持原样（改动触碰冻结边界无收益） |
| `MODEL = "qwen3.8-max-preview"`、API_BASE | qwen_harness_tools.py:27-28 | 低风险（AGENTS.md 锁定该模型）；可加 `QWEN_HARNESS_MODEL` env 覆盖 |
| `MODEL_PATH = ~/wzh/models/hf/qwen3-vl-8b-instruct` | vlm_server_8007.py:22 | BLOCKED 状态，解冻时再 env 化 |
| `:5000` | loop_d_monitor.sh:28、graph_orchestrator.sh:96 | **应修**（见 Issue 2），统一 `${M1_API_BASE:-:5050}` |
| `/tmp/qoder_settings_template.json` | deploy_qoder_gb10.sh:19 | 改为仓库内路径（Issue 9） |

## 专项问题 4：graph/ 子目录与 docs/17 的一致性

| 检查项 | 结论 |
|--------|------|
| Loop B（30min 周期、纯 bash、冻结哈希、独立 pytest、API 锚点、verify-report.json） | **一致**（脚本 = 设计；端口已修正 :5050） |
| Loop A 启动方式 | **不一致**（Issue 1：orchestrator 用 --full-auto，现行为 tmux 直启 codex exec） |
| Loop C 载体 | **不一致**（Issue 3：prompt 头部/docs/17 说 Codex CLI+:8005，实际 Claude Code+qwen3.8-max） |
| 冻结节点清单 | **不一致**（Issue 4：docs/17 写 docs/m1_schema/*.json，实际是 ~/wzh/m1_samples/m1_table_schema.json） |
| §8 文件索引 | 缺 loop_d_daemon.sh / write_report.py / sync_skills.sh（Issue 6） |
| §4 基础设施快照 | 过时（72B 已删除；端口表无 :5050）（Issue 6） |
| skill 分发（sync_skills.sh） | 与 AGENTS.md Skill 武库注册表一致（A 4 件 / C 6 件清单吻合） |

## 专项问题 5：qwen_harness_tools / responses2chat_proxy(_v2) 健康度

- **qwen_harness_tools.py: 健康**。实现与 AGENTS.md 契约完全一致（qwen3.8-max-preview、enable_thinking、120s 超时、web_extractor 需伴生 web_search、ERROR 前缀 + exit 1）。被 loop_a_exec_constraints.md 与 loop_c_audit_prompt.md 正确引用。仅 Minor：模型/端点无 env 覆盖。
- **responses2chat_proxy.py (v1): 健康且为现役**（:8100 实测监听中；含 developer-role 映射、tools 转换、/health；AGENTS.md 记载 glm-5.2 端到端验证通过；docker-compose.yml 引用）。
- **responses2chat_proxy_v2.py: 死代码**，v1 的严格子集，零引用，建议删除（Issue 5）。

---

## 建议清单（只建议，不执行）

**删除（12）**：debug_load.py、debug_load2.py、debug_split.py、debug_split2.py、debug_markdown_splitter.py、ingest_debug.py、ingest_debug2.py、check_kb.py、init_pgvector_ext.py、_verify_m1_local.py、responses2chat_proxy_v2.py、m1_ocr_map.py*（*或随实验报告归档）*

**归档/标注（11）**：m1_ocr_render.py、init_collaboration_db.py、init_pgvector_db.py、migrate_sessions.py、test_db_conn.py、test_web_ui.py、test_non_thinking_mode.py、populate_knowledge_base.py、setup_claude_env.ps1、deploy_proxy_gb10.sh、setup_codex_gb10.sh

**合并候选（2）**：openai_smoke_test.py → 并入 smoke_test_retrieval_model.py 或保留为通用冒烟入口；README_scripts.md 索引职责 → 并入 docs/architecture/codebase_map.md

**保留-冻结研究基线（8，禁改，加过时模型横幅）**：tat_dqa_data.py、prepare_tat_dqa_joint_v1.py、run_tat_dqa_m2_upper_bound.py、run_retrieval_ablation.py、run_rerank_eval.py、run_chunk_ablation.py、m1_llm_extract_prototype.py、m1_llm_batch_extract.py

**保留-活跃核心（其余约 61 个）**：m1_statement_parser / m1_ocr_fallback / m1_rag_ingest / m1_rag_qa / m1_benchmark / m1_accuracy_eval / m1_header_mapping_llm（env 化后）/ graph 全套 / run.sh / m1_serve.sh / demo.sh / qwen_harness_tools / responses2chat_proxy / verify_config / init_knowledge_backend / MCP 三件套（start_* + smoke_test_*）/ run_opencode_* / run_mcp_opencode_stability / run_tabular_inference / vlm_server_8007（BLOCKED 保留）/ switch_codex_model / download_hf_model / download_model_from_catalog（model_catalog.json 存在，配套保留）/ benchmark_openai_models / run_m2_rag_eval（历史 M2 合成夹具评测，若确认被 m1_rag_qa 完全覆盖可转删除）/ Qoder 三件（决策未关闭）/ loop_*.md 与 overnight_*.md（审计档案政策）

---

## Assessment

**Ready to merge?** N/A（read-only 审查，无代码变更）

**结论**: scripts/ 核心活跃链路（M1 解析 → RAG 入库 → QA → Graph 验证）质量与边界纪律都好；主要债务集中在两类：
(1) **Graph 编排层文档/脚本滞后于 7/30-8/3 的运营演进**（端口、Loop A/C 启动方式、Loop C 载体、冻结路径 4 处漂移），其中 orchestrator 启动方式属 Critical——它是 docs/17 指引的官方入口却在 GB10 上不可用；
(2) **前 M1 时代与实验期的一次性脚本未清退**（约 12 个可直接删除、11 个应归档），README_scripts.md 作为唯一 scripts 索引已失真。

所有建议均为只读结论，未执行任何删除/修改/git 操作；执行需 Loop D 批准（涉及冻结线标注时注意不得触碰 frozen_hashes.txt 所列文件本体）。

END-OF-REPORT
