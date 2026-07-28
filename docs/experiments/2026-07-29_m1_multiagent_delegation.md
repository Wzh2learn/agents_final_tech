# M1 多 Agent 自动委派端到端验证

- 日期: 2026-07-29
- 执行: Codex CLI on GB10（模型服务 Qwen3-14B-Q4 @ :8004，16K context；OpenCode 1.18.3）
- 状态: **Step1 机制可用但自动触发不可靠；Step2 单跳委派已验证可用且结果正确，双跳（含 evidence-verifier）BLOCKED（上下文溢出 + 超时）**
- 约束遵守: 样本未入库（`~/wzh/m1_samples` 只读）；报告脱敏（样本以 Sample-* 代称，数值不展开）；未下载模型；未改 `m1_service.py`；未碰 TAT-DQA/tests/CUDA；未 push；OpenCode 单任务 180s 超时；未常驻额外模型。

## TL;DR

1. **委派机制本身可用**：主协调 agent（内置 `build`，`task:true`）能通过 `task` 工具拉起子 agent 会话并执行工具，链路 `primary -> task -> subagent -> tool -> 返回` 在基础设施层面跑通。
2. **"自动"委派不可靠**：中性 prompt 下，主 agent 倾向**直接调用**自己有权限的工具，而不委派子 agent（tabular 与 m1 均复现）。委派需要 prompt 明确指示才稳定触发。
3. **子 agent 空结果缺陷**：`tabular-researcher`（`steps:2`）跑完工具后不产出最终文本，父 agent 收到空 `task_result` 后重试至 180s 超时。给子 agent 加"必须输出最终文本摘要"的 prompt 后（m1-extraction）该缺陷消失。
4. **Step2 单跳已验证**：`coordinator -> task -> m1-extraction -> bash 跑 parser -> /tmp/opencode/m1_extract.json -> 文本摘要` 端到端成功，结果与直接跑 parser **完全一致**（6 样本、表数 1/0/0/2/7/0、唯一样本市值勾稽 FAIL）。
5. **Step2 双跳 BLOCKED**：`evidence-verifier` 读取 215KB 解析 JSON（~26090 tokens）**超出 Qwen3-14B 16384 context**，触发 compaction 后仍溢出，返回空结果；整体双跳 >180s 超时。

## 环境

- OpenCode 二进制: `~/.opencode/bin/opencode`（v1.18.3，非 PATH，需手动加入）
- 模型: `gb10/qwen3-14b` -> `http://127.0.0.1:8004/v1`（llama-server，16K context，健康）
- MCP: jinrong-rag / jinrong-vision / jinrong-tabular（opencode.json 定义；本轮 tabular 链路真实调用成功）
- PostgreSQL/PGVector: `:15432` 容器在运行（本轮未使用）
- 子 agent 定义: m2-qa / m1-extraction / evidence-verifier / tabular-researcher（subagent），tabular-runner（primary）
- 运行方式: `opencode run "<prompt>" --auto --format json`，`timeout 180`

## Step 1 — 委派机制验证（tabular 链路）

### 1.1 中性 prompt（不指示委派）→ 未自动委派

给主 agent 一个明确应委派给 `tabular-researcher` 的表格分类请求（含显式 feature_names/train_rows/labels/predict_rows，合成脱敏数据）。

- 结果: 主 agent **直接**调用 `jinrong-tabular_tabular_classify`，未出现任何 `task`/subagent 调用。
- trace（脱敏）: 6 个事件，唯一工具调用为
  `TOOL tool=jinrong-tabular_tabular_classify status=completed`，输出 `success / tabpfn v2 / train_count=8 / predict_count=3`。
  全文 `task`/`subagent`/`tabular-researcher`/`delegate` 关键字计数均为 0。
- 原因: `build` 主 agent 对 `jinrong-tabular_*` 有 allow 权限，模型选择直接调用工具的捷径，而非委派。

### 1.2 机制可用性确认

`opencode debug agent build` 显示主 agent `tools` 含 `"task": true`，且 4 个自定义子 agent 均已注册（`opencode debug config` agents 列表确认）。**委派能力已接线。**

### 1.3 指示委派（强制走 task）→ 机制跑通，但子 agent 返回空

prompt 明确要求"必须用 task 工具委派给 tabular-researcher，不要自己调用"。

- 主 agent 两次调用 `task`，`input_keys=['description','prompt','subagent_type']`，`subagent_type=tabular-researcher`，`state=completed`。
- 子 agent 会话（导出验证）内部: `reasoning -> TOOL jinrong-tabular_tabular_classify status=completed`（success, tabpfn v2, 3 预测）-> `step-finish reason=tool-calls` -> 下一步 `step-finish reason=stop` **但无 text part**。
- 父 agent 收到 `<task_result></task_result>`（空），遂重试委派，第 3 步时 **180s 超时（exit 124）**。
- 根因: `tabular-researcher` 配置 `steps:2`，工具调用耗尽步数后未产出最终文本摘要；`task` 工具以子 agent 最终文本作为 `task_result`，故为空。

### Step1 结论

**机制工作（基础设施层面），但有两个缺陷：**
- (a) 中性 prompt 下**不自动触发**委派（主 agent 直接调用工具）；
- (b) 子 agent（`steps:2` 的 tabular-researcher）**返回空结果**，导致父 agent 重试至超时。

证据: 1.1 直接调用 trace（无 task）；1.3 `task subagent_type=tabular-researcher state=completed` + 子会话内 `tabular_classify completed` + 空 `task_result` + exit 124。

## Step 2 — m1 解析接入委派

### 2.0 直接跑 parser 建立基线（ground truth）

`./venv/bin/python scripts/m1_statement_parser.py --samples-dir ~/wzh/m1_samples --json /tmp/.../parser_baseline.json`
（venv 含 fitz/openpyxl/docx；系统 python3 缺 openpyxl，wzh_vllm env 三者全缺 → 子 agent 必须用项目 venv 绝对路径）。

脱敏基线（样本以代号表示）:

| 样本代号 | 类型 | 表数 | 勾稽结果 |
|---|---|---|---|
| Sample-XLSX | xlsx | 1 | PASS |
| Sample-PDF-1 | pdf | 0 | PASS（需 OCR） |
| Sample-PDF-2 | pdf | 0 | PASS |
| Sample-TXT | txt | 2 | PASS |
| Sample-PDF-3 | pdf | 7 | **FAIL（市值勾稽 + 静默错配嫌疑）** |
| Sample-DOCX | docx | 0 | PASS（image-only，需 OCR） |

### 2.1 首次委派尝试 → BLOCKED（权限）

指示主 agent 委派 m1-extraction 跑 parser（输出 `/tmp/m1_delegation/`）。`opencode run --auto`，180s。

- 日志确认委派已发生: `evaluated permission=task pattern=m1-extraction action=allow` -> 创建子会话 `agent=m1-extraction`。
- 子 agent 决定跑 bash: `evaluated permission=bash pattern="<parser 命令>" action=ask` -> `asking`；
  紧接 `permission=external_directory pattern=/tmp/m1_delegation/* action=ask` -> `asking`。
- 之后无任何事件，子 agent **卡在权限等待**直到 180s 超时（仅 1 个 step_start，304 字节）。
- **精确 BLOCKED 原因**: `--auto` **未自动批准子 agent 的 `bash`/`external_directory` ask 权限**，headless 下无人应答 -> 挂起超时。

### 2.2 最小接入修复（已提交）

按任务授权（"m1-extraction agent 的 permission 允许 bash，prompt 指示它"）改 `opencode.json` 的 m1-extraction：

1. `permission.bash`: `"ask"` -> `"allow"`（消除 bash 权限挂起）。
2. 新增 `prompt`: 指示用项目 venv 绝对路径跑 parser，输出写到**已允许目录** `/tmp/opencode/m1_extract.json`（规避 external_directory ask），读回并返回简洁文本摘要，**且必须以最终文本摘要结束**（修复 1.3 的空结果缺陷）。

`opencode debug agent m1-extraction` 确认 `bash ... action=allow` 生效、`has prompt: True`。

### 2.3 修复后单跳委派 → 成功且结果正确

指示主 agent 委派 m1-extraction 解析 `~/wzh/m1_samples`。`opencode run --auto`，**exit 0（未超时，约 128s）**。

- 主 agent `task subagent_type=m1-extraction state=completed`，`task_result` **非空**:
  > Parsed 6 samples, found 10 tables. Reconcile results: Sample-XLSX PASS; Sample-PDF-1 PASS(needs OCR); Sample-PDF-2 PASS; Sample-TXT PASS; **Sample-PDF-3 FAIL(市值勾稽, 静默错配嫌疑)**; Sample-DOCX PASS(data insufficient)
- 子 agent 真实产出 `/tmp/opencode/m1_extract.json`（215,516 字节）。
- 主 agent 将摘要逐字作为最终 TEXT 回答。
- **正确性校验**: 委派产出与直接基线逐样本表数一致（1/0/0/2/7/0），唯一 FAIL 样本及其两个失败勾稽项完全吻合。

**单跳委派链 `coordinator -> m1-extraction -> parser -> 勾稽摘要` 端到端验证通过，结果正确。**

### 2.4 双跳尝试（+ evidence-verifier）→ BLOCKED（上下文溢出 + 超时）

指示主 agent 先委派 m1-extraction 解析，再委派 evidence-verifier 读 `/tmp/opencode/m1_extract.json` 独立复核勾稽。180s。

- 主 agent 对两个子 agent 都发起了 `task` 委派（`subagent_type` 出现 2 次）：
  - m1-extraction 返回**正确**摘要（同 2.3）。
  - evidence-verifier 返回**空** `task_result`。
- evidence-verifier 子会话导出 + 日志显示精确原因：
  - `TOOL read filePath=/tmp/opencode/m1_extract.json status=completed`（read 成功，无权限阻塞）。
  - `ERROR AI_APICallError: request (26090 tokens) exceeds the available context size (16384 tokens)` —— 215KB 解析 JSON 注入后**超出 Qwen3-14B 16K context**。
  - 触发 `agent=compaction` 压缩后重试，再次 `ERROR Context size has been exceeded`，始终未产出复核结论 -> 空结果。
- 主 agent 额外步骤叠加，整体 **180s 超时（exit 124）**。
- **精确 BLOCKED 原因**: (1) 解析全量 JSON 体积超模型上下文，verifier 无法整文件复核；(2) Qwen3-14B 单步 ~30s，双跳 + compaction 重试超 180s 预算。

## 可行性判断：多 Agent 确保解析正确

- **可行（已部分验证）**：单跳 `coordinator -> m1-extraction` 能稳定产出与确定性 parser 一致、带勾稽结论的标准化结果。把 parser 作为子 agent 的 bash 工具接入是成立的。
- **"多 Agent 独立复核保正确"目前不成立**，受三点制约：
  1. 自动委派不可靠（需 prompt 显式指示，否则主 agent 自己干）；
  2. verifier 上下文溢出（全量解析 JSON > 16K tokens）；
  3. 双跳延迟超 180s（Qwen3-14B）。
- 诚实表述：当前应记为 **"单跳委派已验证；自动委派与双跳复核 ready-to-activate，未验证"**，不得表述为"多 Agent 自动委派已验证"。

## 下一步最小可行集成路径

1. **parser 输出瘦身供复核**：让 parser 额外产出一份**紧凑勾稽摘要 JSON**（每样本: 代号/表数/各勾稽项 PASS-FAIL+关键数字），体积 << 16K tokens；verifier 只读这份摘要而非 215KB 全量。这是解锁双跳的最小改动（不改 m1_service.py，只扩 parser 的 `--json` 旁路输出）。
2. **修复空结果缺陷**：给所有子 agent（含 tabular-researcher）加"必须以最终文本摘要结束"的 prompt；复核 `steps:2` 是否过小。
3. **提升自动委派率**（三选一/组合）：(a) 收回主 agent 对应工具的直接权限，逼其委派；(b) 协调器换更强模型；(c) 接受"显式指示委派"为运行模式。
4. **放宽多跳时延预算**：双跳在 Qwen3-14B 上 >180s，需提高单任务超时或换更快协调模型。
5. **权限**：headless `--auto` 不会批准子 agent 的 ask 权限；接入新子 agent 时按需把 bash/external_directory 显式设为 allow 并限定输出到已允许目录（如 `/tmp/opencode/`）。

## 附录：配置变更（已提交，未 push）

`opencode.json` 的 `m1-extraction`：
- `permission.bash`: `ask` -> `allow`
- 新增 `prompt`（约 590 字符）：venv 绝对路径跑 parser -> 输出 `/tmp/opencode/m1_extract.json` -> 读回返回简洁勾稽摘要 -> 必须以最终文本结束。

（脱敏说明：样本真实名称/数值不出现在本报告；Sample-* 与类型对应关系仅用于内部追溯。）
