# M1 验证轮：UI 端到端 + OpenCode 多 Agent 双跳 + MCP 集成

- 日期: 2026-07-29
- 执行: Codex CLI on GB10（模型服务 Qwen3.6-35B-A3B-Q4 @ :8004，**64K context**，MoE 3B active；OpenCode 1.18.3）
- 状态: **Phase 1 / 2 / 3 全部 PASS**。UI parse-file 三样本成功；多 Agent 双跳委派由 BLOCKED 转为**已验证**（exit 0，58s）；jinrong-rag / jinrong-vision MCP 均可被 agent 调用并返回正确结果。
- 约束遵守: 样本未入库（`~/wzh/m1_samples` 只读）；报告脱敏（仅指标，不展开原始金额/账号）；未改 `src/biz/m1_service.py`；未碰 TAT-DQA；未下载模型；未常驻额外模型（视觉/向量模型均为临时子进程，跑完即退）；未 push。

## TL;DR

1. **Phase 1（UI 端到端）**: `/api/m1/parse-file` 对 TXT/PDF/XLSX 三类样本全部 `status=success`，tables 非空、metrics 含 hit_rate。三样本合计 **unmapped=5**（达成 39→5 目标）。TXT/XLSX 勾稽全 PASS；PDF 正确报出唯一真实 FAIL（市值勾稽 + 静默错配嫌疑）。
2. **Phase 2（多 Agent）**: 双跳委派 `coordinator -> m1-extraction -> evidence-verifier` **端到端验证通过**（exit 0，58s；verifier 结论与确定性 parser 地面真值逐样本一致）。解锁主因是模型升级 16K→64K + compact summary（1.1KB 替代 215KB 全量 JSON），但升级后还暴露并修复了 **2 个配置 bug**（悬空顶层 model 引用；external_directory 权限挂起 + 子 agent 过度探查）。任务预案 A/B/C **均无需启用**。
3. **Phase 3（MCP）**: `knowledge_search` / `knowledge_list_collections` / `vision_ocr_extract` 均可被 agent 调用并返回 `success`。`knowledge_base` 集合为空（0 chunks），故 M1 域查询返回 0 条（**符合预期**，与 M1 正式指标受阻于 owner 审批标签映射一致）；检索链路在已入库的 tat-dqa 集合（627 chunks）上验证可用（2 条可溯源结果）。视觉 paddleocr-vl-1.6 对 M1 规则表截图 OCR 准确（~67–73s，峰值显存 1.94GiB）。
4. **配置变更（已提交，未 push）**: `opencode.json` 三处修复，见附录。

---

## Phase 1 — UI 端到端

### 方法

- `:5000` 返回 Internal Server Error、`:5050` 已被既有 m1-standalone harness 占用；为确定性地验证**当前代码**且不干扰既有会话，按任务 harness 模式新起独立 FastAPI 于 `:5051`（tmux 常驻，挂载 `/static` + `/api/m1` 路由）。
- 用 `curl -F file=@<sample>` 打 `/api/m1/parse-file`，落盘完整 JSON 后提取指标。

### 结果（脱敏，仅指标）

| 样本（仓库内拼音代称） | kind | needs_ocr | tables | hit_rate | unmapped | KV | reconcile |
|---|---|---|---|---|---|---|---|
| fuxi_hunhe25（TXT） | txt | False | 2 | 93.3% | 1 | 7 | **4/4 PASS** |
| jiaxing_minan（PDF） | pdf | False | 7 | 86.8% | 4 | 5 | 2/4（市值勾稽 + 静默错配嫌疑 FAIL） |
| xinxizha（XLSX） | xlsx | False | 1 | 100% | 0 | 0 | 4/4（多为数据不足 SKIP） |

- 三样本 unmapped 合计 **5**（TXT 1 + PDF 4 + XLSX 0），与本轮目标「39→5」一致（parser 侧旁路统计为 23 出现次/18 唯一列 → 5 出现次/5 唯一列）。
- **PDF 的 FAIL 是真实勾稽捕获**：市值勾稽 sum(市值) 与总资产差异超容差；静默错配嫌疑命中 4 项（在途数量/配号/持仓数量映射可疑 + 市值勾稽失败）。这正是工作台需要人工复核的场景，属预期行为而非缺陷。
- XLSX 单 sheet（A1:F674）解析出 673 条记录、6 列全映射（hit_rate 100%）。
- 三个样本 `needs_ocr=False`（均为文本层 PDF/纯文本/表格，无需 OCR）；6 样本全量解析中另有 2 个纯图样本（20260506 pdf、xinhua docx）标记 `needs_ocr=True`，对应 Phase 3 视觉链路。

---

## Phase 2 — OpenCode 多 Agent context 问题

### 前提已变（关键）

任务预案基于「Qwen3-14B 16K context 装不下 MCP 工具定义 + agent prompts」。但当前环境已切换模型（commit `6022191`）：llama-server 以 `-c 65536`（64K）运行 Qwen3.6-35B-A3B。且 parser 已产出 **compact summary**（`--compact-summary`，1103 bytes）供 verifier 读取，替代上一轮溢出的 215KB 全量 JSON。因此先验证「原生双跳现状是否已通」，再决定是否启用 A/B/C。

### 排障与根因（按发现顺序）

1. **悬空顶层 model 引用（启动即挂，1s exit 1）**：commit `6022191` 把 provider 的模型键从 `qwen3-14b` 改名为 `qwen3.6-35b-a3b`，但顶层 `"model": "gb10/qwen3-14b"` 未同步，导致 `opencode run` 无法解析默认模型，server error。用 `-m gb10/qwen3.6-35b-a3b` 探针（9s 返回 OK）定位后，修正顶层引用。
2. **external_directory 权限挂起（hop 1 卡死）**：35B 模型比 14B 更「谨慎」，m1-extraction 子 agent 先用 glob/read 探查 `~/wzh/m1_samples`（项目外目录），触发 `external_directory` ask；headless `--auto` 未放行该 ask，子 agent 挂起至超时（parser 始终未执行，输出文件未刷新）。修复：给 m1-extraction 加 `external_directory: allow`，并把 prompt 改为「首个动作必须直接跑 parser bash，不得先探查目录」。
3. **evidence-verifier 过度探查（hop 2 卡死）**：verifier 读到 compact summary 后仍深挖（step 14+，自写分析脚本、试图读原始样本），再次撞 external_directory ask。修复：verifier 加 `external_directory: allow` + `steps: 4`，prompt 收紧为「唯一数据源 = compact summary，不得打开任何其他文件/不得写分析脚本」。

### 双跳验证结果

- `opencode run --auto --format json`，显式指示走 `task` 委派（自动委派在上一轮已确认不可靠，需显式指示）。
- **exit 0，elapsed 58s**（对比上一轮 14B/16K >360s 超时）。
- 事件链：`task -> m1-extraction`（completed，真实跑 parser，输出 23:09:24 刷新）→ `task -> evidence-verifier`（completed，仅读 compact summary，无外部文件访问）→ 主 agent 汇总 TEXT。
- verifier 结论与地面真值一致：唯一 FAIL 样本 = jiaxing_minan PDF（market_value=FAIL、silent_mismatch=FAIL、4 unmapped），其余 5 样本可接受。
- 子 agent 时延：m1-extraction 19.3s，evidence-verifier 18.5s。

### context 占用分布（任务 D）

| 组成 | tokens（实测/估算） |
|---|---|
| 固定开销（system prompt + 工具定义含 5 个 MCP 工具 + 内置工具 + agent 注册表） | ~10.2K（cache-read 基线） |
| 每跳 task_result 注入 | +~0.75K |
| 主协调器峰值 | ~12K |
| compact summary | ~0.3K（1103 bytes） |
| 旧全量 JSON（上一轮溢出元凶） | ~26K（215KB，已弃用） |

结论：64K 下峰值 ~12K，约 5× 余量；即便旧 26K 全量 JSON 现在也能装下，但 compact summary 仍是最小化最佳实践。**工具定义（含全部 3 个 MCP server 的 5 个工具）在 64K 下完全可承载，无需精简** → 预案 A（裁剪 MCP 工具）/B（缩短 description）/C（串行模拟）**均无需启用**。

---

## Phase 3 — MCP 集成验证

### 前置条件（本机实测）

| 项 | 状态 |
|---|---|
| PostgreSQL/PGVector `:15432`（容器 `pgvector_15432`） | 运行中 |
| 本地 reranker `bge-reranker-v2-m3`（CUDA） | 模型在位，按需加载 |
| 本地 embedding `qwen3-embedding-0.6b`（1024 维，CUDA） | 模型在位；**需项目 venv（transformers 5.14.1）**，conda `wzh_vllm`（transformers 4.45.2）无法识别 `qwen3` 架构 |
| SiliconFlow 云端 embedding key | **未提供** → 用 `LOCAL_EMBEDDING_MODEL_PATH` 本地替代 |
| 视觉模型 paddleocr-vl-1.6 / minicpm-v-4.6 / qwen3-vl-8b | 均在位；推理走 `wzh_vision` env（transformers 5.7.0）子进程 |

MCP server 由 opencode 启动时的环境变量决定行为，关键变量：`PGDATABASE_URL`、`JINRONG_MCP_PYTHON`（指向项目 venv）、`LOCAL_EMBEDDING_MODEL_PATH`、`JINRONG_VISION_PYTHON`、`JINRONG_VISION_ALLOWED_ROOTS`（需覆盖 `~/wzh/m1_samples`，默认仅 `assets/`、`data/`）。

### 3.1 jinrong-rag（knowledge_search / knowledge_list_collections）

- **agent 可调用（已验证）**：agent 依次调用 `knowledge_search(query="对账单 表头 字段映射", top_k=5)` 与 `knowledge_list_collections`，两者均 `status=completed/success`（整轮 exit 0，31s）。
- `knowledge_list_collections` 返回 2 个集合：`knowledge_base`、`tat-dqa-joint-v1-validation`；时延 0.05s。
- `knowledge_search` 对 M1 域查询返回 **0 条**，根因是 **`knowledge_base` 集合为空（0 chunks）**——M1/金融知识尚未入库，与「M1 正式业务指标受阻于 owner 审批的 label-to-source 映射 + 人工标注」现状一致，属预期而非故障。
- **检索链路可用性旁证**：对已入库的 `tat-dqa-joint-v1-validation`（627 chunks）查询返回 2 条可溯源结果（含 source id），端到端 14.2s（含一次性 embedding + reranker 加载）。链路 = 本地 qwen3 embedding → PGVector 向量检索 → 本地 bge reranker，全程本地、无需云 key。

### 3.2 jinrong-vision（vision_ocr_extract）

- **agent 可调用（已验证）**：agent 调用 `vision_ocr_extract(image_path=<ui_parse_rule_table.png>, model="paddleocr")`，`status=completed`，返回非空文本（整轮 exit 0，88s）。
- 直连子进程基线：paddleocr-vl-1.6 @ CUDA，**elapsed 67.3s，峰值显存 1.94GiB**；agent 路径 73.3s。
- **结果质量高**：对 1511×755 的 M1「解析表规则（表/表字段近义词）」配置截图，准确 OCR 出表名（交易对账单）、表头显示名与近义词列表（产品名称/管理人/对账日期/券商/托管行/合计金额/单位净值 及各自近义词），结构与中文均正确。
- 配置说明：`m1-extraction` 子 agent 按冻结配置 `jinrong-vision_*: deny`，故视觉经 primary build agent（`--auto` 放行 ask）验证；若要在 M1 流程内用视觉兜底纯图对账单，需给相应子 agent 开通 vision 权限或由 primary 路由。

### 3.3 时延汇总

| 调用 | 时延 | 备注 |
|---|---|---|
| knowledge_list_collections | 0.05s | 仅 DB |
| knowledge_search（空集合） | ~7s | 含一次性 embedding 加载 |
| knowledge_search（627 chunks 集合） | 14.2s | embedding + reranker 加载，2 结果 |
| vision_ocr_extract（paddleocr，1511×755） | 67–73s | VLM 加载 + 推理，1.94GiB |

---

## 对甲方 M1 主线的完成度评估

- **确定性 parser + 工作台 API：扎实**。三类文件（TXT/PDF/XLSX）稳定解析，hit_rate 86.8–100%，unmapped 降至 5，勾稽能捕获真实错配（PDF FAIL）并给出可复核线索。
- **多 Agent 独立复核：由「ready-to-activate」升级为「显式指示下单跳 + 双跳委派均已验证」**。verifier 结论与 parser 地面真值一致，双跳 58s 可接受。**仍保留的限制**：自动委派（中性 prompt）不可靠，需显式指示；这是运行模式约束，非链路缺陷。
- **MCP 集成：rag/vision 可被 agent 调用**。但 `knowledge_base` 空 → M1 域知识检索暂无数据（受阻于标签映射 + 人工标注，非技术问题）；视觉 OCR 可用作纯图对账单兜底（6 样本中 2 个需 OCR），已在 UI 截图上验证质量，**但尚未在真实纯图对账单扫描件上正式测 OCR 质量**。
- **剩余缺口（非本轮范围）**: (1) M1 域知识入库（填 `knowledge_base`）；(2) owner 审批的 label-to-source 映射 + 人工标注 → 解锁正式业务指标；(3) 纯图对账单 OCR 质量正式评测；(4) 自动委派可靠性（可选：收回主 agent 直接工具权限逼其委派，或换更强协调模型）。

---

## 附录：配置变更（`opencode.json`，已提交未 push）

1. 顶层 `"model"`: `gb10/qwen3-14b` → `gb10/qwen3.6-35b-a3b`（修复 commit `6022191` 遗留的悬空引用，否则 `opencode run` 启动即挂）。
2. `m1-extraction`: 加 `external_directory: allow`；prompt 收紧为「首动作直接跑 parser bash，不得先探查目录」，并改读 compact summary 而非 215KB 全量 JSON。
3. `evidence-verifier`: 加 `external_directory: allow` + `steps: 4`；prompt 收紧为「唯一数据源 = compact summary，不得打开其他文件/不得写分析脚本」。

（脱敏说明：样本以仓库内拼音代称指代，原始金额/账号/客户全称等不出现在本报告；数值仅保留命中率/列数/勾稽 PASS-FAIL 等聚合指标。）
