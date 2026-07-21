# OpenCode 开发机运行说明

截至 **2026-07-21**，当前状态与优先级以根目录 [HANDOFF.md](../HANDOFF.md) 和
[阶段收尾与对外汇报](12_阶段收尾与对外汇报.md) 为准。

## 已验证的只读链路

- MCP：`knowledge_search`、`knowledge_list_collections`、`knowledge_get_source`；
- OpenCode：本地 `gb10/qwen3-14b` provider 与只读 MCP 工具调用；
- Qwen3-14B：以 16K 上下文完成过服务验证；
- 正式只读 OpenCode/MCP 稳定性验收：**20/20 通过**；进程生命周期问题已修复。

这些是历史验证结论，不表示模型、数据库或 MCP 服务当前正在运行。M1 OCR/规则
抽取、正式 M2 业务指标和完整多 Agent 工作流均未完成。

## Vision MCP（已实现，独立验证）

`jinrong-vision` 是与 `jinrong-rag` 分离的只读 stdio MCP，当前仅公开
`vision_ocr_extract(image_path, model="paddleocr", max_new_tokens=256)`。MCP 服务使用
`JINRONG_MCP_PYTHON`（默认 `~/miniconda3/envs/wzh_vllm/bin/python`）启动；只有它启动的重型推理子进程使用
`JINRONG_VISION_PYTHON`（默认 `~/miniconda3/envs/wzh_vision/bin/python`）启动既有 smoke 脚本。服务启动不加载视觉权重，也不连接数据库。
图片必须位于受控的 `assets/` 或 `data/` 根目录（可通过本地环境变量扩展）；模型键
仅限 `paddleocr`、`minicpm`、`qwen3-vl`，模型目录始终由服务端选择。

全局权限为 `ask`；`m1-extraction` 可调用，`m2-qa` 禁止，`evidence-verifier` 可调用。
协议发现通过只代表实现可启动；真实 OCR 调用、资源数据和效果结论须单独记录为受控
集成验证，且原始识别文本不得进入 Git。

## Tabular MCP（已实现，独立验证）

`jinrong-tabular` 与知识、Vision MCP 分离，仅公开
`tabular_classify(feature_names, train_rows, labels, predict_rows, model="tabpfn", model_version="v2")`。
调用仅接受小型、矩形、有限数值的内存数据；不接收文件、路径、代码或调用者指定的模型 ID。
MCP 进程使用 `JINRONG_MCP_PYTHON`（默认 `~/miniconda3/envs/wzh_vllm/bin/python`），启动时不导入
TabPFN/TabFM；单次推理子进程使用 `JINRONG_TABULAR_PYTHON`（默认
`~/miniconda3/envs/wzh_tabular/bin/python`）。TabFM checkpoint 是服务端固定映射，可仅由本地
`JINRONG_TABFM_CHECKPOINT_PATH` 覆盖，且输出不含路径或环境细节。

```bash
python scripts/smoke_test_tabular_mcp_server.py
python scripts/smoke_test_tabular_mcp_server.py --run-synthetic --model tabpfn
python scripts/smoke_test_tabular_mcp_server.py --run-synthetic --model tabfm
```

第一条只做协议发现；后两条运行既有脱敏合成分类链路，并只打印状态、模型、行数、耗时和输出维度。
2026-07-21 的 TabPFN v2 与 TabFM 调用均通过（各 8 条训练、3 条预测、3×2 输出；推理分别为 0.912 秒
和 0.616 秒）。这些调用不构成业务效果或正式 M1/M2 指标。全局调用为 `ask`；`m2-qa` 与
`evidence-verifier` 禁止，`m1-extraction` 保持 `ask`，专用 `tabular-researcher` 仅可调用该 MCP 工具。

同日 `opencode mcp list` 显示知识、Vision、Tabular 三个 MCP 均已连接。调优后的
`tabular-runner` 是供 CLI 演示使用的专用 primary agent：只启动 Tabular MCP、无需数据库变量，
使用低温度、两步上限和严格数组 Schema。脱敏合成 TabPFN 调用约 26 秒完成整条 OpenCode 链路，
其中模型推理为 1.013 秒；不记录预测内容。原先超过 3 分钟的现象是 SSH 等待继承的输出描述符，
不是模型或 MCP 未执行。协调器自动委派 `tabular-researcher` 子 Agent 仍需后续单独验证。

```bash
bash scripts/run_opencode_tabular.sh run \
  --agent tabular-runner --title tabular-demo \
  'Call tabular_classify once with the supplied numeric training and prediction rows.'
```

## 续接前检查

在开发机交互终端中先执行只读检查：

```bash
cd ~/wzh/projects/agents_final_tech
git status --short
git pull --ff-only origin main
tmux list-windows -t coding-jinrong
```

按本机安全配置提供所需环境变量，不显示其值。之后仅在任务确有需要时执行
`opencode mcp list`、协议 smoke test 或服务健康检查。一次只运行一个大模型；
不要因为文档中的历史验证而假定或重启服务。

## 当前优先事项

1. 取得负责人批准的 M2 合成标签—稳定来源映射和人工答案质量标注；
2. 再运行已有评测器，形成正式 M2 指标；
3. 建立批准的 M1 OCR/规则抽取标注集与数值基线；
4. 最后交接给工程同学实施完整编排、权限、状态和系统集成。

日志、原始模型/工具输出、来源映射和私有业务材料均留在受控本地环境，不进入 Git。
