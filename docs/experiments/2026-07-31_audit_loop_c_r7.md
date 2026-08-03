# Loop C 审计报告 - 2026-07-31 22:30 (Cycle 7)

> 完整 5 步审计; 重点 commit: `87d8da4` (Qwen harness tools CLI) + `264f30a` (docs section 15)
> 辅助: 本轮首次使用 `scripts/qwen_harness_tools.py web_search` 验证被审计工具自身

## 审计范围
- 审计 commit 范围: `6b9deaa..264f30a` (HEAD~2..HEAD; 重点 `87d8da4` + `264f30a`)
- HEAD = `264f30a`, 在交付链中 (ancestor=YES)。
- **Loop B 状态: PASS, 但存在覆盖缺口 (见下)** —— `logs/graph/verify-report.json` timestamp 2026-07-31T22:03:51, `head_commit`=`6b9deaa`, overall=PASS (frozen_nodes/pytest/api_anchors 全 PASS)。**但 `87d8da4`(22:11) 与 `264f30a`(22:17) 均在 Loop B 运行(22:03)之后提交**, 即 Loop B 未覆盖本轮两个重点 commit。非 amend (6b9deaa 仍是 HEAD 祖先, 未被改写), 属正常向前开发, 但验证门已滞后 HEAD 2 个 commit。Loop C 已自跑 M1 合约测试补偿 (见 Step 4)。
- 模型服务: `:8004`=200, `:8005`=200; harness `:5050` `/health`=ok, `uvicorn --workers 2` (pid 3593282) 运行中 (87d8da4 为独立 CLI 工具, 不被 harness 导入, 无需重启)。

## Step 1 — Loop B 验证报告
如上: PASS (head=`6b9deaa`), 但未覆盖重点 commit。本轮不据此跳过审计, 改由 Loop C 自跑 M1 合约 (`tests/test_m1_service.py`) 与 5 样本端到端补偿验证。

## Step 2 — 代码变更审查

### 变更摘要 (HEAD~3..HEAD, +326/-1, **无 src/ 改动**)
- `scripts/qwen_harness_tools.py` (+136, 新文件, commit `87d8da4`): Qwen Responses API (`/compatible-mode/v1/responses`) 的 CLI 包装, 暴露 `web_search` / `code_interpreter` / `web_extractor` 三工具 + `t2i_search`/`i2i_search` 两 stub。模型 `qwen3.8-max-preview`, `enable_thinking=True`, 硬编码 `TIMEOUT=60`。
- `scripts/graph/loop_c_audit_prompt.md` (+14, `87d8da4`): 新增"千问平台工具(审计辅助)"节, 授权 Loop C 用 `web_search`/`web_extractor` 联网。
- `scripts/graph/loop_a_exec_constraints.md` (+16, `87d8da4`): 加 harness tools 使用约束节。
- `docs/experiments/2026-07-31_72b_reevaluation.md` (+127, `6b9deaa`): 72B 复评报告 (退化确认)。
- `docs/22_overnight_loopD_neat_closeout.md` (+34, `264f30a`): section 15, 4 项决策 + harness tools 集成 + Loop A demo。
- `git diff HEAD~3..HEAD -- src/` = **空** (无 src/ 代码改动)。

### 是否服务于甲方需求: **PARTIAL (间接)**
- `87d8da4` 是 loop 体系自身的工具/审计基础设施 (含 Loop C 自身的联网能力), **非 M1 对账单解析功能**; 不直接推进甲方"表头同义词映射 + 结构化提取", 但增强审计/验证闭环。`264f30a` 纯文档。无 M1 解析逻辑变更, 亦无回归 (Step 3/4 证实)。

### 架构漂移风险: **LOW**
- 独立 CLI 脚本, 标准库 `urllib`, 不导入/不改 harness 与 parser; 无新依赖注入 M1 路径。`enable_thinking=True` + 60s 超时对审计辅助场景可接受。

### 不当修改: **无**
- `tests/`、`~/wzh/m1_samples/`、冻结 TAT-DQA 节点均未触及 (`git diff --stat` 无 tests/tat/dqa/samples 命中)。✓
- 无 `breakpoint/pdb/TODO/FIXME` 调试残留。✓
- 安全性 (代码审查 `qwen_harness_tools.py`): 用环境变量取 `OPENAI_API_KEY` (无硬编码密钥), `urllib.request` 构造请求 (无 shell 调用/无注入面), 错误体截断 500 字防日志爆量, `STUB_TOOLS` 诚实标注未实现。✓

## Step 3 — 甲方样本端到端验证 (live `:5050`)

| 样本 | http | 耗时 | ocr_used | table_count | reconcile | schema 命中率 | 评分 |
|------|------|------|----------|-------------|-----------|--------------|------|
| 复熙 TXT | 200 | 0.05s | False | 2 | 4/4 ✓ | 15/15 | 95 |
| 嘉兴 PDF | 200 | 1.27s | False | 6 | 4/4 ✓ | 58/62 | 82 |
| 博时 PDF | 200 | 1.59s | False | 1 | 4/4 ✓ | 3/5 | 62 |
| LU PDF | 200 | 28.0s | True (vision-8004) | 3 | 4/4 ✓ | 7/23 | 50 |
| 新华 DOCX | 200 | 79.0s | True (vision-8004) | 5 | 4/4 ✓ | **0/11** | 45 |

**与 Cycle 6 一致, 无回归。** 5 样本 reconcile 仍 4/4, 字段覆盖率与命中率不变。新华 0/11 已连续 5 轮 (Cycle 3-7) 未闭合。

### 重点 commit `87d8da4` 工具实测 (审计被审计物本身)
- **web_search**: 首次调用 `TimeoutError` (撞 60s 硬编码超时, `enable_thinking=True` + 联网首调用偏慢); 换短 query 重试 **成功** (返回"Today is Friday, July 31, 2026", rc=0)。→ 工具可用, 但 `TIMEOUT=60` 对 web_search+思考偏紧。
- **web_extractor**: **HTTP 400 失败** —— Qwen API 报 `The web_extractor tool must be executed with web_search tool`。即 web_extractor 不能单独调用, 须与 web_search 同请求。当前 CLI 把它暴露为独立子命令, **必然 400**。commit 声称"web_search + code_interpreter working"未含 web_extractor, 不算虚假, 但该子命令实为坏路。
- code_interpreter: 未本轮实测 (非审计判断所需, 避免不必要的工具调用)。

## Step 4 — 架构一致性
- `:8004/:8005` 健康; `:5050` workers=2, `/health` ok; harness 自 03:51 运行 (f966cf0 时代代码, 因 87d8da4 不影响 harness, 无需重启)。
- **M1 合约测试** (`tests/test_m1_service.py`, Loop C 自跑补偿 Loop B 滞后): **18/18 PASS** (0.02s)。冻结合约未变。✓
- `pytest tests/` 全量 12 failed / 75 passed —— 失败均为 `test_core_service`/`test_websocket`/`test_e2e_browser`/`test_hmm_memory` 等 **async/websocket/playwright 环境性失败** (asyncio 配置缺失、playwright 未装), 非 M1、非本轮 commit 引入 (HEAD~3..HEAD 未触 tests/src)。Loop B 的 "pytest PASS" 指 M1 合约, 与本轮 18/18 一致。
- opencode.json: `agents` 键为 None (无 agent 配置); `mcp` 配 3 server (start_mcp_server.sh / start_vision_mcp_server.sh / start_tabular_mcp_server.sh), 脚本均存在 (各 14 行)。本轮未逐一启动验证 (非 M1 路径)。
- 反 amend: `264f30a`==HEAD, `6b9deaa` 为祖先 (非 dangling); `git fsck` 10 个 dangling 均为历史遗留, 本轮无新增。✓ (连续合规延续)

## Step 5 — 判定

### 判定: **ACCEPTED** (连续 ACCEPTED 计数: 4)

本轮重点两 commit 为清洁增量: 无 src/tests/samples/frozen 改动, M1 合约 18/18 PASS, 5 样本无回归, 反 amend 合规, 新工具代码安全、web_search 可用。`web_extractor` 坏路与 `TIMEOUT=60` 偏紧为非阻塞质量问题 (辅助工具, 非 M1)。**ACCEPTED。**

### 驳回原因
无。

### 建议改进方向 (不阻塞本轮)
1. **【中·正确性】`web_extractor` 子命令坏路**: Qwen API 要求 web_extractor 必须与 web_search 同请求执行, 当前 CLI 独立调用必 400。建议要么改为 `web_extractor <url>` 内部自动并 web_search, 要么在 `--help` 标注"须配合 web_search"并退出, 免得用户误用。commit `87d8da4` 的"verified"声称应补注 web_extractor 未验。
2. **【低·健壮性】`TIMEOUT=60` 对 web_search+`enable_thinking=True` 偏紧** (本轮首次调用即撞超时); 建议 web_search 路径单独放宽至 90-120s, 或可配 `M1_TOOL_TIMEOUT`。
3. **【carryover·连续 5 轮·高】新华 DOCX 仍 0/11 schema 命中** (Cycle 3-7): OCR 能跑 (79s) 但 5 表仍似项目交付表, 与对账单 schema 0 命中。**第 5 次重提, 强烈建议 Loop D 本轮必须裁定**影像件 OCR 是否属 M1 承诺 (含→修正确性; 不含→API 标注"暂不支持"以关闭 carryover)。
4. **【carryover·中】reconcile disposition 未实施** (Cycle 5 起): 5 样本"4/4 PASS"含 3/5 跳过式水分, 仍建议加 `real_pass/skipped/fail`。
5. **【流程·中】Loop B 滞后 HEAD 2 commit**: Loop B 最后验证 `6b9deaa`, 未覆盖 `87d8da4`/`264f30a`。虽本轮 Loop C 已补偿验证无回归, 但验证门应跟上 HEAD。

## 给 Loop D 的建议
1. **本轮 ACCEPTED, 连续 ACCEPTED=4 (已超 3 次阈值), 维持 12h 降频审计。** 出现 REJECTED/CONDITIONAL 时恢复 4-6h。
2. **建议 Loop D 促 Loop B 重跑覆盖 `264f30a` (当前 HEAD)**, 消除"验证门滞后"的流程缺口; 在 Loop B 复盖 HEAD 前, 本轮结论由 Loop C 补偿测试背书 (M1 合约 18/18 + 5 样本无回归)。
3. **新华 0/11 已连续 5 轮未闭合** —— 本轮为最后一次建议性重提: 若 Loop D 仍不裁定, 该 carryover 将无限延续; 建议要么裁定范围, 要么显式"影像件不属 M1"关闭之。
4. `87d8da4` 工具纳入审计闭环是正向一步 (Loop C 已据此联网验证); 但 `web_extractor` 坏路应让 Loop A 下轮修, 否则该子命令是"半成品"。
5. M1 解析面连续多轮稳定无回归 (Cycle 4-7), 建议后续审计重心可转向 M2 RAG/QA 质量 (commit `2212244` 等), 不止 M1。
