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
`vision_ocr_extract(image_path, model="paddleocr", max_new_tokens=256)`。它使用
独立视觉解释器启动既有 smoke 脚本，服务启动不加载视觉权重，也不连接数据库。
图片必须位于受控的 `assets/` 或 `data/` 根目录（可通过本地环境变量扩展）；模型键
仅限 `paddleocr`、`minicpm`、`qwen3-vl`，模型目录始终由服务端选择。

全局权限为 `ask`；`m1-extraction` 可调用，`m2-qa` 禁止，`evidence-verifier` 可调用。
协议发现通过只代表实现可启动；真实 OCR 调用、资源数据和效果结论须单独记录为受控
集成验证，且原始识别文本不得进入 Git。

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
