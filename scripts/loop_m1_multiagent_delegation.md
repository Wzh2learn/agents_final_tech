# 任务：M1 多 Agent 自动委派端到端验证

## 背景
HANDOFF/AGENTS 明确：OpenCode 多 Agent 自动委派**从未端到端验证**；opencode.json
已定义 m1-extraction / m2-qa / evidence-verifier / tabular-researcher 及权限。本轮分
两步验证，诚实记录，不硬凑"已验证"。样本 `~/wzh/m1_samples/`。主模型用 GB10 默认
（Token Plan qwen3.8-max-preview 或 :8004，按 opencode.json provider）。

## 约束
- 样本不入库、报告脱敏；不下载模型；不改 m1_service.py；不 push；不碰 TAT-DQA/test；
  不动 CUDA/驱动。
- OpenCode 单任务超时 180s；不常驻额外模型。

## Step 1 委派机制验证（低风险，必做）
证明"主 agent 自动委派子 agent"机制本身工作：
- 复用 tabular 链路：HANDOFF 记录 tabular-runner 端到端 ~26s 成功，但"协调器自动委派
  tabular-researcher 子 agent 仍未验证"——本轮正验证这个自动委派。
- 让主协调 agent 收到一个应委派给 tabular-researcher 的请求，检查 OpenCode 的
  trace/log（stdout json、或 ~/.local/share/opencode、或项目 .opencode 日志）是否出现
  subagent 调用记录。
- 结论：机制工作 / 不工作 + 证据（trace 摘录脱敏）。

## Step 2 m1 解析接入委派（集成，可能 BLOCKED）
若 Step1 机制工作，尝试把 m1_statement_parser 接入：
- 最简包装：m1-extraction agent 的 permission 允许 bash，prompt 指示它
  `python3 scripts/m1_statement_parser.py --samples-dir ~/wzh/m1_samples --json /tmp/...`
  解析指定样本；或注册为 MCP 工具（若已有 mcp 框架）。
- 跑一份真实样本：主协调→委派 m1-extraction 解析→委派 evidence-verifier 对解析结果做
  勾稽校验（读 parser 的 reconcile 输出）→返回标准化+校验结论。
- 检查委派链是否自动发生 + 最终结果是否正确（与直接跑 parser 对比）。
- 若跑不通：记录 BLOCKED 精确原因（工具未注册？权限 deny？模型路由？子 agent 没被自动
  选中？），给最小修复建议；**不得**把"配置存在"或"手动跑通单 agent"表述为"自动委派
  已验证"。

## 报告
`docs/experiments/$(date +%F)_m1_multiagent_delegation.md`：
- Step1 结论 + trace 证据
- Step2 结论 或 BLOCKED 原因 + 修复建议
- 对"多 Agent 确保解析正确"的可行性判断 + 下一步最小可行集成路径。脱敏。

## 提交（不 push）
commit 报告 + 任何为接入而加的最小工具包装脚本；注明 Step2 验证状态。

## 停止条件
OpenCode 不可用 / Step1 机制不工作→Step2 跳过，报告 Step1 结论+BLOCKED；单任务超时→
记 TIMEOUT；全完成→正常。不 push、不碰 TAT-DQA、不常驻模型。
