# 基础设施盘点与 Gap 解决规划

> 状态: 活跃（规划已全部执行） | 更新: 2026-08-05 | 取代/被取代: 无

> 日期: 2026-08-02 | 状态: 已执行（3 项 gap 全部 CLOSED，台账见 memory/THREADS.md） | 作者: Loop D 战略层

---

## 一、基础设施盘点

### 1.1 本地模型服务

| 端口 | 模型 | 格式 | 状态 | 用途 | 备注 |
|------|------|------|------|------|------|
| :8004 | Qwen3.6-35B-A3B + mmproj | GGUF Q4_K_M | **运行中** | 生成 + 视觉 OCR + 嵌入 | MoE 3B active, 64K ctx, CUDA |
| :8005 | Qwen3-14B | GGUF Q4_K_M | **运行中** | 辅助生成 | 32K ctx, 20 层 GPU offload |
| :8006 | — | — | **已停止** | (72B 已删除) | 47GB 磁盘已释放 |
| :8100 | responses2chat 代理 | Python | **运行中** | Chat-only 模型适配 | upstream = token-plan |

### 1.2 已下载但未服务的模型

| 模型 | 路径 | 格式 | 大小 | 登记任务 | 当前状态 |
|------|------|------|------|----------|----------|
| Qwen3-4B | gguf/qwen3-4b | GGUF | ~2.5GB | m1_rule_extract, m2_rag_qa | **未服务** |
| Qwen3-8B | gguf/qwen3-8b | GGUF | ~5GB | m1_rule_extract, m2_rag_qa | **未服务** |
| Qwen3-14B | gguf/qwen3-14b | GGUF | ~8GB | m1_rule_extract, m2_rag_qa | 已服务 (:8005) |
| MiniCPM5-1B | hf/minicpm5-1b | safetensors | ~2GB | m1_rule_extract, tool_use | **未使用** |
| **Qwen3-VL-8B-Instruct** | hf/qwen3-vl-8b-instruct | safetensors (4 shards) | ~16GB | vision_language, ocr, document_qa | **未使用** ⭐ |
| **MiniCPM-V-4.6** | hf/minicpm-v-4.6 | safetensors | ~4GB | vision_language, ocr, document_qa | **未使用** ⭐ |
| PaddleOCR-VL-1.6 | hf/paddleocr-vl-1.6 | safetensors | ~3GB | ocr, document_parsing | **SIGSEGV on ARM64** ❌ |
| BGE-M3 | hf/bge-m3 | safetensors + onnx | ~2GB | embedding, m2_retrieval | **未使用** (用 qwen3-emb 替代) |
| BGE-Reranker-v2-m3 | hf/bge-reranker-v2-m3 | safetensors | ~2GB | rerank | **已使用** (M2 rerank) |
| Qwen3-Embedding-0.6B | hf/qwen3-embedding-0.6b | safetensors | ~1GB | embedding | **已使用** (RAG 嵌入) |
| Qwen3-Reranker-0.6B | hf/qwen3-reranker-0.6b | safetensors | ~1GB | rerank | **未使用** (用 bge-reranker 替代) |
| TabPFN-3 | hf/tabpfn_3 | pytorch | ~100MB | tabular_classification | **未使用** |
| TabFM-1.0 | hf/tabfm-1.0.0-pytorch | pytorch | ~200MB | tabular_classification/regression | **未使用** |

**⭐ 关键发现**: Qwen3-VL-8B 和 MiniCPM-V-4.6 是两个已下载但完全未使用的视觉语言模型。
它们可以直接用于 OCR + 表格结构识别, 可能解决 NCAMC 垂直布局和华泰 OCR 纯文本问题。

### 1.3 MCP Server

| Server | 暴露工具 | 配置 | 运行状态 | 阻塞原因 |
|--------|----------|------|----------|----------|
| jinrong-rag | `knowledge_search`, `knowledge_list_collections`, `knowledge_get_source` | opencode.json enabled=true | **未运行** | 需要 `wzh_vllm` conda env (start 脚本硬编码) |
| jinrong-vision | `vision_ocr_extract` | opencode.json enabled=true | **未运行** | 同上 + 需要 PaddleOCR-VL (SIGSEGV) |
| jinrong-tabular | `tabular_classify` | opencode.json enabled=true | **未运行** | 需要 `wzh_vllm` env + TabPFN 独立 env |

**MCP 工具能力**:
- `knowledge_search`: 向量+BM25 混合检索, 支持 collection 过滤
- `vision_ocr_extract`: 对图片跑 PaddleOCR-VL 或 MiniCPM-V 推理 (subprocess 隔离)
- `tabular_classify`: 对数值表格跑 TabPFN/TabFM 分类 (subprocess 隔离)

**阻塞分析**: 3 个 MCP server 的 start 脚本都硬编码 `JINRONG_MCP_PYTHON=$HOME/miniconda3/envs/wzh_vllm/bin/python`。
这个 conda env 在 GB10 上可能不存在或已损坏。需要:
1. 检查 `~/miniconda3/envs/wzh_vllm/` 是否存在
2. 如果不存在, 改用 venv 的 python (但需安装 mcp 包)
3. vision_mcp 还需要解决 PaddleOCR-VL SIGSEGV (或切换到 MiniCPM-V / Qwen3-VL)

### 1.4 OpenCode 多 Agent 配置

| Agent | 模式 | 模型 | 权限 | 当前状态 |
|-------|------|------|------|----------|
| m2-qa | subagent | gb10/qwen3.6-35b-a3b | RAG only | **配置完整, 未运行** |
| m1-extraction | subagent | gb10/qwen3.6-35b-a3b | bash + RAG | **配置完整, 未运行** |
| evidence-verifier | subagent | gb10/qwen3.6-35b-a3b | bash + RAG | **配置完整, 未运行** |
| tabular-researcher | subagent | gb10/qwen3.6-35b-a3b | tabular only | **配置完整, 未运行** |
| tabular-runner | primary | gb10/qwen3.6-35b-a3b | tabular only | **配置完整, 未运行** |

**编排关系** (设计意图):
```
coordinator (primary, 用户交互)
  +-- m1-extraction (解析对账单)
  |     +-- evidence-verifier (校验解析结果)
  +-- m2-qa (RAG 问答)
  +-- tabular-researcher (表格 ML 实验)
```

**未运行原因**: OpenCode 框架本身没有在 GB10 上启动。opencode.json 是配置文件,
但需要 `opencode` CLI 或 API 来驱动 agent 编排。当前所有 agent 都是"纸面配置"。

### 1.5 千问 Harness 工具

| 工具 | 使用次数 | 使用场景 | 状态 |
|------|----------|----------|------|
| web_search | 6 次 | Loop C 审计查规范, 验证工具自身 | **可用** |
| code_interpreter | 3 次 | Loop C 审计数值验证, 勾稽校验 | **可用** |
| web_extractor | 1 次 | 修复后验证 (需配合 web_search) | **可用但少用** |

### 1.6 Parser 表格检测逻辑

当前 parser 有 **3 层表格检测**, 按优先级:

1. **pymupdf find_tables()** -- 检测有网格线/边框的表格
   - 策略: 先默认策略, 失败后 `strategy="text"` 重试
   - 适用: 标准 PDF 表格 (嘉兴/博时/复熙)
   - 不适用: 无边框表格, 扫描件, 垂直布局

2. **_text_lines_to_tables()** -- 正则回退, 两种策略:
   - 策略 1: 多空格分隔列检测 (连续行 2+ 空格分割, 列数一致 >= 2)
   - 策略 2: 重复 KV 块检测 (key:value 行分组, pivot 成表格)
   - 适用: 无网格线但有空格对齐的文本表格
   - 不适用: 垂直布局 (NCAMC), 单空格分隔 (华泰 OCR)

3. **_parse_markdown_tables()** -- Markdown pipe 表格解析
   - 检测 `| header |` + `|---|` 模式
   - 适用: OCR 输出为 markdown 格式时 (S1 增强后)
   - 不适用: OCR 输出为纯文本时

---

## 二、3 个 Known Gap 解决路径

### Gap 1: NCAMC 垂直布局 (0 表)

**问题本质**: pymupdf `get_text()` 按阅读顺序提取, 表格的列名和数据值变成垂直单列。
原始 PDF 有表格结构, 但文本提取丢失了列关系。

| 路径 | 方法 | 工作量 | 预期效果 | 推荐度 |
|------|------|--------|----------|--------|
| A | pymupdf `get_text("dict")` 坐标重建列 | 中 (2-3h) | 高 -- 直接利用 PDF 坐标信息 | ⭐⭐⭐⭐ |
| B | Qwen3-VL-8B 直接看图识别表格 | 中 (1-2h 部署 + 测试) | 高 -- VLM 天然理解表格布局 | ⭐⭐⭐⭐⭐ |
| C | MiniCPM-V-4.6 看图识别 | 低 (模型更小, 部署快) | 中 -- 轻量 VLM, 表格能力待验证 | ⭐⭐⭐ |
| D | vision_mcp_server 的 vision_ocr_extract | 高 (需修 MCP env) | 中 -- 底层仍是 PaddleOCR-VL (SIGSEGV) | ⭐⭐ |
| E | 多 agent: vision agent 提区域 -> table agent 结构化 | 高 (需启用 OpenCode) | 高 -- 但依赖整个 agent 体系 | ⭐⭐ |

**推荐**: **路径 B** (Qwen3-VL-8B) 作为主力, **路径 A** (坐标重建) 作为无 GPU 时的回退。

路径 B 的理由:
- 模型已下载 (16GB safetensors), 不需要额外下载
- Qwen3-VL-8B 是专门的视觉语言模型, 表格理解能力强
- 可以用 vLLM 或 transformers 部署为 API, 替换或补充 :8004 的 mmproj OCR
- 对 NCAMC 这类"有文本层但布局非标准"的 PDF, VLM 可以直接看页面截图理解表格结构

路径 A 的理由:
- 不需要额外模型, 纯代码方案
- pymupdf 的 `get_text("dict")` 返回每个文本块的 bbox 坐标
- 按 y 坐标分行, 按 x 坐标分列, 可以重建表格结构
- 对 NCAMC 这种"列名在上, 数据在下"的垂直布局特别有效

### Gap 2: 华泰/OCR 纯文本无表格线 (S1 已部分解决)

**问题本质**: OCR 输出的文本是空格分隔的, 没有 markdown 表格标记。
S1 通过增强 prompt 让模型输出 markdown 格式, 已解决华泰 (0->1 表) 和 TraFax (0->3 表)。

| 路径 | 方法 | 工作量 | 预期效果 | 推荐度 |
|------|------|--------|----------|--------|
| A | ~~改 OCR prompt 要求 markdown~~ | **已完成** | 华泰 0->1, TraFax 0->3 | ✅ done |
| B | 后处理: 空格分隔表格检测 | 低 (1h) | 中 -- 作为 markdown 解析的回退 | ⭐⭐⭐ |
| C | tabular_mcp_server 的 classify | 高 (需修 MCP env) | 低 -- classify 不做表格检测 | ⭐ |
| D | Qwen3-VL-8B 替代 vision-8004 做 OCR | 中 (部署 VLM) | 高 -- VLM 可直接输出结构化表格 | ⭐⭐⭐⭐ |
| E | 多 agent: OCR -> table agent | 高 | 高 -- 但依赖 agent 体系 | ⭐⭐ |

**推荐**: **路径 D** (与 Gap 1 共用 Qwen3-VL-8B 部署)。
VLM 做 OCR 时可以直接输出 markdown 表格, 一步到位, 不需要"OCR -> 后处理 -> 表格检测"的多步 pipeline。

**路径 B 作为快速补充**: 在 `_text_lines_to_tables` 的策略 1 中, 当前要求 2+ 空格分隔。
华泰 OCR 输出是单空格分隔, 所以没命中。可以加一个"单空格 + 列数一致"的宽松策略。

### Gap 3: Email Body 格式 (0 表)

**问题本质**: 邮件正文中的对账单是 HTML 表格被 extract-msg 提取为纯文本,
列名和值交替排列 (垂直 KV 模式), 不是 parser 能处理的格式。

| 路径 | 方法 | 工作量 | 预期效果 | 推荐度 |
|------|------|--------|----------|--------|
| A | 写 parse_email_body 专用解析器 | 中 (3-4h) | 中 -- 只解决这 3 封邮件的格式 | ⭐⭐ |
| B | LLM 把 email body 转成标准格式再喂 parser | 低 (1-2h) | 高 -- 通用, 不依赖特定格式 | ⭐⭐⭐⭐ |
| C | 多 agent: email agent 提取+格式化 | 高 | 高 -- 但依赖 agent 体系 | ⭐⭐ |
| D | 用 extract-msg 的 HTML body 而非纯文本 | 低 (0.5h) | 高 -- HTML 表格可以直接用 BeautifulSoup 解析 | ⭐⭐⭐⭐⭐ |

**推荐**: **路径 D** 优先, **路径 B** 作为回退。

路径 D 的理由:
- extract-msg 库可以获取 HTML 格式的 body (`msg.htmlBody`)
- HTML 中的 `<table>` 标签可以直接用 BeautifulSoup 或 pandas.read_html 解析
- 这比纯文本解析可靠得多, 因为 HTML 保留了表格结构
- 工作量极小: 在预处理脚本里加一步 HTML 提取 + 表格解析

路径 B 的理由:
- 如果 HTML body 不可用 (某些 .msg 只有纯文本), 用 LLM 做格式转换
- 把 email body 发给 :8004, prompt: "把以下对账单文本转换为 markdown 表格"
- 然后把 markdown 输出喂给 _parse_markdown_tables

---

## 三、多 Agent 体系可行性评估

### 3.1 当前配置完整性

opencode.json 配置了 5 个 agent, 权限隔离清晰, prompt 详细。
但存在以下问题:

1. **OpenCode CLI 未安装/未启动**: 配置文件存在但没有运行时
2. **MCP Server 未运行**: 3 个 MCP server 的 start 脚本依赖 `wzh_vllm` conda env
3. **模型路由**: agent 配置指向 `gb10/qwen3.6-35b-a3b` (:8004), 这个在跑
4. **缺少 coordinator agent**: 配置了 4 个 subagent + 1 个 primary, 但没有显式的 coordinator 编排逻辑

### 3.2 启用多 Agent 的前置条件

| 条件 | 状态 | 工作量 |
|------|------|--------|
| OpenCode CLI 安装 | 未确认 | 0.5h (npm install -g opencode) |
| MCP Server Python env | 需修复 | 1-2h (改 start 脚本用 venv 或创建 conda env) |
| PaddleOCR-VL SIGSEGV | 阻塞 vision_mcp | 需切换到 MiniCPM-V 或 Qwen3-VL |
| TabPFN 独立 env | 阻塞 tabular_mcp | 1h (创建独立 venv) |
| 端到端测试 | 未做 | 2-3h |

### 3.3 框架选择

| 框架 | 优势 | 劣势 | 适合场景 |
|------|------|------|----------|
| **OpenCode** | 已有配置, MCP 集成好, 权限隔离 | 需要 CLI 运行时, MCP env 问题 | 交互式多 agent 协作 |
| **LangGraph** | 已有依赖, 状态机编排灵活 | 需要写编排代码, 无 MCP 集成 | 自动化 pipeline |
| **Python 脚本** | 最简单, 无依赖 | 无 agent 能力, 无 tool use | 固定流程批处理 |

**推荐**: 当前阶段用 **Python 脚本编排** 做 gap 修复 (快速验证),
验证成功后再迁移到 **LangGraph** (自动化 pipeline),
最终在需要交互式协作时启用 **OpenCode**。

理由: OpenCode 的 MCP 依赖链太长 (conda env + PaddleOCR SIGSEGV + TabPFN env),
在当前"先解决 gap 再优化架构"的阶段, 投入产出比不高。

### 3.4 多 Agent 能解决哪些 Gap

| Gap | 多 Agent 方案 | 是否比单脚本更好 |
|-----|--------------|-----------------|
| NCAMC 垂直布局 | vision agent (VLM 看图) -> table agent (结构化) | 略好 -- 但单脚本调 VLM API 也能做 |
| 华泰 OCR 纯文本 | OCR agent (VLM) -> table agent (markdown 解析) | 否 -- S1 prompt 增强已解决 |
| Email body | email agent (HTML 提取) -> format agent (LLM 转换) -> parser | 略好 -- 但 BeautifulSoup 一行代码也能做 |

**结论**: 多 agent 体系在当前阶段不是 gap 解决的关键路径。
gap 的核心瓶颈是"模型能力" (VLM 表格理解) 和"数据格式" (HTML vs 纯文本),
不是"编排能力"。

---

## 四、推荐执行顺序

### Phase 1: 快速修复 (1-2h, 无需新模型)

1. **Gap 3 路径 D**: extract-msg 提取 HTML body -> BeautifulSoup 解析表格
   - 改 preprocess_msg.py, 加 `msg.htmlBody` 提取
   - 用 `pandas.read_html()` 或 `BeautifulSoup` 解析 `<table>` 标签
   - 预期: 国金/南华/财通 3 封邮件从 0 表变有表

2. **Gap 2 路径 B**: _text_lines_to_tables 加单空格宽松策略
   - 在策略 1 后面加策略 1.5: 单空格分隔 + 列数一致 >= 3
   - 预期: 作为 markdown 解析的回退, 提高鲁棒性

### Phase 2: VLM 部署 (2-3h, 需要 GPU 内存)

3. **部署 Qwen3-VL-8B-Instruct** 为独立 API (:8007)
   - 用 transformers + vLLM 或 llama.cpp (如果有 GGUF 版本)
   - 测试: 对 NCAMC PDF 页面截图, 看能否输出 markdown 表格
   - 如果成功: 替换 _try_vision_ocr 中的 :8004 mmproj 调用

4. **Gap 1 路径 A 作为回退**: pymupdf 坐标重建
   - 如果 VLM 部署失败或太慢, 用坐标方案
   - `get_text("dict")` -> 按 bbox 聚类 -> 重建表格

### Phase 3: MCP 修复 (2-3h, 可选)

5. **修复 MCP start 脚本**: 改用 venv python + 安装 mcp 包
6. **vision_mcp 切换模型**: 从 PaddleOCR-VL 切到 MiniCPM-V 或 Qwen3-VL
7. **端到端测试**: 启动 OpenCode, 跑一次 m1-extraction agent

### Phase 4: 多 Agent 启用 (3-4h, 可选)

8. **安装 OpenCode CLI**
9. **编写 coordinator 编排逻辑** (或用 LangGraph 替代)
10. **端到端 pipeline 测试**: 上传 .msg -> 预处理 -> 解析 -> 校验 -> 入库 -> 问答

---

## 五、资源利用率总结

### 已打出的牌

| 资源 | 利用率 | 评价 |
|------|--------|------|
| :8004 35B + mmproj | 90% | 核心引擎, 生成+OCR+嵌入 |
| :8005 14B | 30% | 辅助, 大部分场景被 35B 覆盖 |
| bge-reranker-v2-m3 | 80% | M2 rerank 在用 |
| qwen3-embedding-0.6b | 90% | RAG 嵌入在用 |
| Harness tools | 40% | Loop C 用过, Loop A 少用 |
| config/m1_table_schema.json | 70% | 嘉合 synonyms 补全后提升明显 |

### 发了但没打的牌

| 资源 | 潜在价值 | 为什么没打 |
|------|----------|-----------|
| **Qwen3-VL-8B** | ⭐⭐⭐⭐⭐ 解决 NCAMC + 华泰 OCR | 没有部署计划, 一直在用 :8004 mmproj |
| **MiniCPM-V-4.6** | ⭐⭐⭐⭐ 轻量 VLM 替代 | 同上 |
| **MCP Server x3** | ⭐⭐⭐ 工具化能力 | start 脚本 env 问题, 从未成功启动 |
| **OpenCode Agents x5** | ⭐⭐⭐ 多 agent 编排 | 框架未安装, 配置是纸面的 |
| **TabPFN + TabFM** | ⭐⭐ 表格 ML | 与当前 gap 无关, 研究性质 |
| **Qwen3-4B / 8B** | ⭐⭐ 轻量替代 | 35B 够用, 没动力切换 |
| **BGE-M3** | ⭐⭐ 多向量检索 | qwen3-emb 够用 |
| **Qwen3-Reranker-0.6B** | ⭐⭐ 轻量 rerank | bge-reranker 够用 |

### 组合打法 (未尝试)

1. **VLM + Parser Pipeline**: Qwen3-VL-8B 看页面截图 -> 输出 markdown -> _parse_markdown_tables
   - 一步解决 Gap 1 + Gap 2
   - 比当前 "mmproj OCR -> 纯文本 -> 表格检测" 的 pipeline 更直接

2. **HTML + LLM Fallback**: extract-msg HTML body -> BeautifulSoup 表格 -> 失败时 LLM 格式转换
   - 解决 Gap 3, 且通用性强

3. **坐标重建 + VLM 验证**: pymupdf 坐标重建表格 -> VLM 看截图验证/修正
   - 双重保障, 适合高价值对账单

4. **MCP + OpenCode 全链路**: 修复 MCP env -> 启动 OpenCode -> m1-extraction agent 自动编排
   - 最终形态, 但前置条件多

---

## 六、决策点 (需要确认)

| # | 决策 | 选项 | 影响 |
|---|------|------|------|
| D1 | Qwen3-VL-8B 部署方式 | A: vLLM / B: transformers / C: 找 GGUF 用 llama.cpp | GPU 内存占用不同 |
| D2 | Gap 3 优先路径 | A: HTML body 提取 / B: LLM 格式转换 / C: 两个都做 | 工作量 0.5h vs 2h vs 2.5h |
| D3 | MCP 修复是否值得投入 | A: 修 / B: 跳过, 直接用 Python 脚本调模型 | 3h vs 0h |
| D4 | OpenCode 是否启用 | A: 现在启用 / B: gap 解决后再说 / C: 用 LangGraph 替代 | 架构方向 |
| D5 | :8005 14B 是否还需要 | A: 保留 / B: 停掉释放内存 | 8GB RAM |
---

## 七、执行结果 (2026-08-02 实际)

### Gap 解决状态

| Gap | 规划推荐路径 | 实际执行路径 | 结果 |
|-----|-------------|-------------|------|
| NCAMC 垂直布局 | B (Qwen3-VL-8B) | **A (pymupdf 坐标重建)** | **SOLVED** 75% hit |
| 华泰 OCR 纯文本 | D (VLM 替代) | **A (OCR prompt 增强)** | **SOLVED** 0→1 table |
| Email body | D (HTML body) | **D (HTML body + BS4)** | **SOLVED** 0→9 tables |

### VLM 部署结果

| 步骤 | 结果 | 备注 |
|------|------|------|
| GGUF 搜索 | HF API timeout | 同 P4 网络问题 |
| safetensors 加载 | OK (105s, bf16, 130GB VRAM) | Qwen3VLForConditionalGeneration |
| 推理 | **FAIL** | Triton JIT 编译失败 (ARM64 gcc) |
| 尝试 eager/sdpa | 均失败 | Triton 在 attention 外也被使用 |
| 服务器代码 | 已提交 | scripts/vlm_server_8007.py |

**结论**: VLM 路径 (B/D) 在 ARM64 GB10 上被 Triton 阻塞。
坐标重建 (路径 A) 作为替代方案成功解决 NCAMC gap，无需 VLM。

### 坐标重建技术细节

`_coordinate_table_reconstruction()` 工作原理:
1. `page.get_text("dict")` 获取每个文本 span 的 bbox 坐标
2. 按 y 坐标聚类成行 (5pt 容差)
3. 用已知 schema 字段名匹配 header 行 (>=3 匹配)
4. 按 x 坐标重叠分配数据 span 到列
5. 集成到 `parse_pdf()`: find_tables → text_lines → **coordinates** → OCR

Junk 检测: find_tables() 对 NCAMC 返回 35 行 x 16 列的垃圾表
(水印文本, 15/16 header 为 None)。通过 "non-empty header <= 2" 启发式识别。

### 最终 Scenario 1 数据

| 指标 | 改进前 | 改进后 |
|------|--------|--------|
| 总表数 | ~17 | **30** |
| 总行数 | ~30 | **74** |
| NCAMC | 0 表 | **1 表 (75%)** |
| 华泰 | 0 表 | **1 表 (35.7%)** |
| TraFax | 0 表 | **3 表 (65.1%)** |
| Email body | 0 表 | **9 表 (24-70%)** |
| 嘉合 | 31.2% | **93.8%** |
| RAG chunks | 88 | **132** (+44 HTML) |

### 推荐执行顺序 (更新)

Phase 1 (HTML + synonyms): **DONE** (d7049b5)
Phase 2a (VLM): **BLOCKED** - 等 Triton 修复或 GGUF 可用
Phase 2b (VLM 集成): **DONE** - 代码就绪, 优雅回退 (701eae2)
Phase 2c (MCP 路由): **DONE** (9abf67b)
Phase 2-alt (坐标重建): **DONE** - 替代 VLM 解决 NCAMC (b927efe)
Phase 3 (MCP 修复): 跳过 (用户决策 D3=B)
Phase 4 (OpenCode): 跳过 (用户决策 D4=B)

### 未打出的牌 (更新)

| 资源 | 状态变化 |
|------|----------|
| Qwen3-VL-8B | 部署失败 (Triton), 代码就绪 |
| MiniCPM-V-4.6 | 仍未使用 (VLM 路径阻塞) |
| MCP Server x3 | vision_mcp 路由已更新, 但 env 问题未修 |
| 坐标重建 | **NEW: 已打出, 解决 NCAMC** |
| HTML body 提取 | **NEW: 已打出, 解决 email gap** |


## 八、2026-08-09 更新（沉淀专项）

- **VLM 降采样实验（Gap 1/2 后续）**: `_vlm_downsample` 送图前缩至 ≤1600px（`M1_VLM_MAX_PX`），延迟从 3-8min 降至 9.6-22.9s/文件（达标）；但 TraFax 命中率 [50,81.8,81.8]→[0,0,100] 显著劣化（8B Q4 对乱版传真输出退化表格）→ **:8007 维持 VERIFIED-CLOSED**，下采样代码保留为未来更强 VLM 的复用资产。
- **BM25**: 原 stub 已实现为真 BM25（PG 全量取 137 chunks + rank_bm25 + /tmp 缓存），flag `M2_ENABLE_BM25` 默认 false；A/B 16 题 hit@10 持平（15/16=15/16，排名零变化）→ 决策不修，留 flag 备语料扩大。
- **rg**: GB10 已装 ripgrep 15.1.0（pip ripgrep → ~/bin/rg，无 sudo；GitHub 直链不可达）。
- **工具链新增**: scripts/restart_opencode_sidecar.sh（sidecar 不热加载配置，改 opencode.json/skills 后必须重启）、scripts/graph/check_skill_sync.sh（skill 分发漂移检查）。
