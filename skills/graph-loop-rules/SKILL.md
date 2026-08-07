---
name: graph-loop-rules
description: JinRongAgents Graph Loop 红线与运行约束。OpenCode agent 在本仓库执行任何任务（解析、审计、问答、代码修改）前必须遵守；涉及冻结节点、生产后端、API key、72B 模型时触发。
---

# Graph Loop 运行约束（OpenCode agent 适用）

本仓库运行四层 Graph Loop（A 执行 / B 验证 / C 审计 / D 战略，见 docs/17）。任何 agent 任务必须遵守：

## 红线（违反即失败）
1. 冻结节点不可修改：tests/test_m1_service.py、scripts/graph/frozen_hashes.txt、docs/m1_schema/（schema 基线文档）、以及 frozen_hashes.txt 所列全部路径（含仓库外运行时 schema ~/wzh/m1_samples/m1_table_schema.json，commit 钩子 + Loop B 双重 md5 校验）。注意：仓库内 config/m1_table_schema.json 不在冻结清单，可通过 schema API 写入并热加载（见 m1-gap-triage skill）。
2. 不改不重启 :5050 生产后端（甲方演示随时可用）；不切页面后端。
3. 不触碰、不打印、不创建 API key。
4. 不加载 72B 模型（已终判退化并删除）。
5. 归档文档用 git mv，禁止 rm；OpenCode/MCP 交付物三件（archive/09、archive/10、archive/2026-07-19_m2_mcp_verification.md）永不删除。

## 运行纪律
- 每步任务结果追加到 logs/graph/dispatch_log.md（格式：[HH:MM] 任务 → 结果 → commit）。
- 无法判断的问题写 logs/graph/blocked_questions.md 后跳过，不阻塞。
- gap/遗留项台账唯一信源：memory/THREADS.md，其他文档只引用不复述。
- 现状以 memory/STATE.md 为准，不到历史文档里找现状。
- Loop A 执行层完整约束见 scripts/graph/loop_a_exec_constraints.md；Loop C 审计 prompt 见 scripts/graph/loop_c_audit_prompt.md。
- 需要联网检索或数值验证时用 python scripts/qwen_harness_tools.py（web_search / code_interpreter / web_extractor），不滥用。

## 验证要求
交付前必须：远端 ./venv/bin/python -m pytest -q 全绿（基线 275 passed / 13 skipped）；证据先于断言（evidence before assertions）。
